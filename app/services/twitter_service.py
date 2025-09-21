import tweepy
import asyncio
import logging
import time
from typing import List, Dict, Optional
from datetime import datetime, timezone
from app.config import settings
from app.models.database import get_db

logger = logging.getLogger(__name__)

class TwitterService:
    def __init__(self):
        self.client = tweepy.Client(
            bearer_token=settings.TWITTER_BEARER_TOKEN,
            wait_on_rate_limit=False  # 不要阻塞等待，而是抛出异常
        )
        self.rate_limited_until = None
        self.user_id_cache = {}  # 缓存用户ID，避免重复API调用
        self.api_call_count = 0  # API调用计数器
        self.last_api_reset = time.time()  # 最后一次重置计数器的时间
        # 初始化时从数据库加载速率限制状态
        asyncio.create_task(self._load_rate_limit_from_db())
        
    async def _load_rate_limit_from_db(self):
        """从数据库加载速率限制状态"""
        try:
            async with get_db() as db:
                cursor = await db.execute(
                    "SELECT rate_limited_until FROM rate_limit_status ORDER BY id DESC LIMIT 1"
                )
                row = await cursor.fetchone()
                if row and row[0]:
                    current_time = time.time()
                    if row[0] > current_time:
                        self.rate_limited_until = row[0]
                        logger.info(f"Loaded rate limit state: {int(row[0] - current_time)}s remaining")
                    else:
                        # 清理过期的速率限制记录
                        await self._clear_rate_limit_in_db()
        except Exception as e:
            logger.error(f"Error loading rate limit from database: {e}")

    async def _save_rate_limit_to_db(self, rate_limited_until: float):
        """保存速率限制状态到数据库"""
        try:
            async with get_db() as db:
                # 先清理旧记录
                await db.execute("DELETE FROM rate_limit_status")
                # 插入新记录
                await db.execute(
                    "INSERT INTO rate_limit_status (rate_limited_until) VALUES (?)",
                    (rate_limited_until,)
                )
                await db.commit()
                logger.info(f"Rate limit state saved to database")
        except Exception as e:
            logger.error(f"Error saving rate limit to database: {e}")

    async def _clear_rate_limit_in_db(self):
        """清理数据库中的速率限制状态"""
        try:
            async with get_db() as db:
                await db.execute("DELETE FROM rate_limit_status")
                await db.commit()
                logger.info("Rate limit state cleared from database")
        except Exception as e:
            logger.error(f"Error clearing rate limit from database: {e}")

    async def _check_rate_limit(self):
        """检查是否处于速率限制状态"""
        if self.rate_limited_until:
            if time.time() < self.rate_limited_until:
                return True
            else:
                self.rate_limited_until = None
                await self._clear_rate_limit_in_db()
        return False

    async def is_rate_limited(self) -> bool:
        """检查是否处于速率限制状态（供外部调用）"""
        return await self._check_rate_limit()

    def get_rate_limit_reset_time(self) -> Optional[int]:
        """获取速率限制重置时间（秒）"""
        if self.rate_limited_until:
            import time
            remaining = max(0, int(self.rate_limited_until - time.time()))
            return remaining
        return None

    def _track_api_call(self):
        """跟踪API调用数量"""
        current_time = time.time()
        # 每15分钟重置计数器
        if current_time - self.last_api_reset > 900:  # 15分钟
            self.api_call_count = 0
            self.last_api_reset = current_time

        self.api_call_count += 1
        logger.info(f"API调用计数: {self.api_call_count} (Free Tier: 1次/15分钟限制)")

    async def get_user_tweets(self, username: str, since_id: Optional[str] = None) -> List[Dict]:
        # 如果处于速率限制状态，直接返回空列表
        if await self._check_rate_limit():
            logger.warning(f"Rate limited, skipping request for {username}")
            return []

        try:
            # 直接通过用户名获取推文，减少API调用
            # 先获取用户信息和推文（但只在必要时获取用户ID）
            user_id = self.user_id_cache.get(username)
            if not user_id:
                # 只在缓存中没有时才调用获取用户API
                self._track_api_call()  # 跟踪API调用
                user = self.client.get_user(username=username)
                if not user.data:
                    logger.error(f"User {username} not found")
                    return []
                user_id = user.data.id
                self.user_id_cache[username] = user_id
                logger.info(f"Cached user ID for {username}: {user_id}")
                # 在用户ID获取后增加延迟
                await asyncio.sleep(8)

            # 获取用户推文
            self._track_api_call()  # 跟踪API调用
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=5,  # 减少每次获取的推文数量
                since_id=since_id,
                tweet_fields=['created_at', 'text', 'public_metrics', 'attachments'],
                expansions=['attachments.media_keys'],
                media_fields=['type', 'url', 'preview_image_url', 'alt_text'],
                exclude=['retweets', 'replies']
            )

            # 在推文获取后增加延迟，避免连续API请求
            await asyncio.sleep(5)

            if not tweets.data:
                return []
            
            # 处理媒体数据
            media_dict = {}
            if tweets.includes and 'media' in tweets.includes:
                for media in tweets.includes['media']:
                    media_dict[media.media_key] = {
                        'type': media.type,
                        'url': getattr(media, 'url', None),
                        'preview_image_url': getattr(media, 'preview_image_url', None),
                        'alt_text': getattr(media, 'alt_text', None)
                    }

            tweet_list = []
            for tweet in tweets.data:
                # 处理附件媒体
                media_attachments = []
                if hasattr(tweet, 'attachments') and tweet.attachments and 'media_keys' in tweet.attachments:
                    for media_key in tweet.attachments['media_keys']:
                        if media_key in media_dict:
                            media_attachments.append(media_dict[media_key])

                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat(),
                    'author': username,
                    'url': f"https://twitter.com/{username}/status/{tweet.id}",
                    'media': media_attachments,
                    'metrics': {
                        'retweets': tweet.public_metrics['retweet_count'],
                        'likes': tweet.public_metrics['like_count'],
                        'replies': tweet.public_metrics['reply_count'],
                        'quotes': tweet.public_metrics['quote_count']
                    }
                }
                tweet_list.append(tweet_data)
            
            return tweet_list
            
        except tweepy.TooManyRequests as e:
            logger.warning(f"Rate limit exceeded for user {username} - API调用过于频繁")
            # 设置速率限制状态（等待API重置后重试）
            self.rate_limited_until = time.time() + 15 * 60
            await self._save_rate_limit_to_db(self.rate_limited_until)
            return []
        except tweepy.Forbidden as e:
            logger.error(f"Access forbidden for user {username}: {str(e)}")
            return []
        except tweepy.NotFound as e:
            logger.error(f"User {username} not found: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching tweets for {username}: {str(e)}")
            return []
    
    async def get_multiple_users_tweets(self, usernames: List[str], since_ids: Optional[Dict[str, str]] = None) -> Dict[str, List[Dict]]:
        results = {}
        
        for username in usernames:
            try:
                since_id = since_ids.get(username) if since_ids else None
                tweets = await self.get_user_tweets(username, since_id)
                results[username] = tweets
                
                # 在用户之间添加延迟避免过快请求
                if len(usernames) > 1:
                    await asyncio.sleep(5)  # 增加到5秒延迟
                    
            except Exception as e:
                logger.error(f"Error processing user {username}: {str(e)}")
                results[username] = []
                
        return results
    
    def validate_credentials(self) -> bool:
        try:
            self._track_api_call()  # 跟踪API调用
            me = self.client.get_me()
            return me.data is not None
        except Exception as e:
            logger.error(f"Twitter credentials validation failed: {str(e)}")
            return False