import asyncio
import logging
from typing import Dict, Optional, Set
from datetime import datetime
from app.services.twitter_service import TwitterService
from app.services.wechat_service import WeChatService
from app.models.database import TweetRecord, init_db, get_db
from app.config import settings

logger = logging.getLogger(__name__)

class MonitorService:
    def __init__(self, twitter_service: TwitterService, wechat_service: WeChatService):
        self.twitter_service = twitter_service
        self.wechat_service = wechat_service
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.last_tweet_ids: Dict[str, str] = {}
        
    async def start_monitoring(self):
        if self.is_monitoring:
            logger.warning("监控已经在运行中")
            return

        await init_db()
        await self._load_last_tweet_ids()

        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        usernames = ', '.join([f'@{u}' for u in settings.twitter_usernames_list])
        logger.info(f"🚀 开始监控 Twitter 用户: {usernames}")
        
    async def stop_monitoring(self):
        if not self.is_monitoring:
            logger.warning("监控未在运行")
            return

        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ 已停止 Twitter 监控")
    
    async def _monitoring_loop(self):
        try:
            while self.is_monitoring:
                await self._check_tweets()
                await asyncio.sleep(settings.CHECK_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {str(e)}")
            self.is_monitoring = False
    
    async def _check_tweets(self):
        usernames = settings.twitter_usernames_list
        if not usernames:
            logger.warning("No Twitter usernames configured for monitoring")
            return
            
        try:
            all_tweets = await self.twitter_service.get_multiple_users_tweets(
                usernames,
                self.last_tweet_ids
            )
            
            for username, tweets in all_tweets.items():
                if tweets:
                    new_tweets = await self._filter_new_tweets(username, tweets)
                    
                    for tweet in new_tweets:
                        await self._process_new_tweet(tweet)
                        
                    if new_tweets:
                        self.last_tweet_ids[username] = tweets[0]['id']
                        await self._save_last_tweet_id(username, tweets[0]['id'])
                        
        except Exception as e:
            logger.error(f"Error checking tweets: {str(e)}")
    
    async def _filter_new_tweets(self, username: str, tweets: list) -> list:
        if not tweets:
            return []
            
        last_id = self.last_tweet_ids.get(username)
        if not last_id:
            return [tweets[0]]  # Only return the latest tweet if no history
            
        new_tweets = []
        for tweet in tweets:
            if int(tweet['id']) > int(last_id):
                new_tweets.append(tweet)
            else:
                break
                
        return new_tweets
    
    async def _process_new_tweet(self, tweet_data: dict):
        try:
            tweet_id = tweet_data['id']
            author = tweet_data['author']
            tweet_text = tweet_data['text'][:50] + '...' if len(tweet_data['text']) > 50 else tweet_data['text']

            logger.info(f"🐦 检测到新推文: @{author} - {tweet_text}")

            # Save to database
            await self._save_tweet_record(tweet_data)

            # Send notification
            success = await self.wechat_service.send_tweet_notification(tweet_data)

            if success:
                logger.info(f"✅ 成功转发推文到企业微信: @{author} ({tweet_id})")
            else:
                logger.error(f"❌ 转发推文失败: @{author} ({tweet_id})")

        except Exception as e:
            logger.error(f"❌ 处理推文时发生错误 {tweet_data.get('id', 'unknown')}: {str(e)}")
    
    async def _load_last_tweet_ids(self):
        try:
            async with get_db() as db:
                for username in settings.twitter_usernames_list:
                    result = await db.execute(
                        "SELECT tweet_id FROM tweet_records WHERE username = ? ORDER BY created_at DESC LIMIT 1",
                        (username,)
                    )
                    row = await result.fetchone()
                    if row:
                        self.last_tweet_ids[username] = row[0]
                        
        except Exception as e:
            logger.error(f"Error loading last tweet IDs: {str(e)}")
    
    async def _save_last_tweet_id(self, username: str, tweet_id: str):
        try:
            async with get_db() as db:
                await db.execute(
                    """UPDATE tweet_records 
                       SET updated_at = ? 
                       WHERE username = ? AND tweet_id = ?""",
                    (datetime.utcnow().isoformat(), username, tweet_id)
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Error saving last tweet ID: {str(e)}")
    
    async def _save_tweet_record(self, tweet_data: dict):
        try:
            async with get_db() as db:
                await db.execute(
                    """INSERT OR IGNORE INTO tweet_records 
                       (tweet_id, username, content, tweet_url, created_at, metrics)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        tweet_data['id'],
                        tweet_data['author'],
                        tweet_data['text'],
                        tweet_data['url'],
                        tweet_data['created_at'],
                        str(tweet_data['metrics'])
                    )
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Error saving tweet record: {str(e)}")