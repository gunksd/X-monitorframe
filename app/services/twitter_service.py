import tweepy
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
from app.config import settings

logger = logging.getLogger(__name__)

class TwitterService:
    def __init__(self):
        self.client = tweepy.Client(
            bearer_token=settings.TWITTER_BEARER_TOKEN,
            wait_on_rate_limit=True
        )
        
    async def get_user_tweets(self, username: str, since_id: Optional[str] = None) -> List[Dict]:
        try:
            user = self.client.get_user(username=username)
            if not user.data:
                logger.error(f"User {username} not found")
                return []
            
            user_id = user.data.id
            
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=10,
                since_id=since_id,
                tweet_fields=['created_at', 'text', 'public_metrics', 'context_annotations'],
                exclude=['retweets', 'replies']
            )
            
            if not tweets.data:
                return []
            
            tweet_list = []
            for tweet in tweets.data:
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat(),
                    'author': username,
                    'url': f"https://twitter.com/{username}/status/{tweet.id}",
                    'metrics': {
                        'retweets': tweet.public_metrics['retweet_count'],
                        'likes': tweet.public_metrics['like_count'],
                        'replies': tweet.public_metrics['reply_count'],
                        'quotes': tweet.public_metrics['quote_count']
                    }
                }
                tweet_list.append(tweet_data)
            
            return tweet_list
            
        except Exception as e:
            logger.error(f"Error fetching tweets for {username}: {str(e)}")
            return []
    
    async def get_multiple_users_tweets(self, usernames: List[str], since_ids: Optional[Dict[str, str]] = None) -> Dict[str, List[Dict]]:
        results = {}
        
        for username in usernames:
            since_id = since_ids.get(username) if since_ids else None
            tweets = await self.get_user_tweets(username, since_id)
            results[username] = tweets
            
        return results
    
    def validate_credentials(self) -> bool:
        try:
            me = self.client.get_me()
            return me.data is not None
        except Exception as e:
            logger.error(f"Twitter credentials validation failed: {str(e)}")
            return False