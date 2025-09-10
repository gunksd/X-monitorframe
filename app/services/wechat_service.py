import aiohttp
import json
import logging
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class WeChatService:
    def __init__(self):
        self.webhook_url = settings.WECHAT_WEBHOOK_URL
        
    async def send_message(self, content: str, mentioned_list: Optional[list] = None) -> bool:
        try:
            payload = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
            
            if mentioned_list:
                payload["text"]["mentioned_list"] = mentioned_list
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200 and result.get('errcode') == 0:
                        logger.info("WeChat message sent successfully")
                        return True
                    else:
                        logger.error(f"WeChat message failed: {result}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending WeChat message: {str(e)}")
            return False
    
    async def send_markdown(self, content: str) -> bool:
        try:
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "content": content
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200 and result.get('errcode') == 0:
                        logger.info("WeChat markdown sent successfully")
                        return True
                    else:
                        logger.error(f"WeChat markdown failed: {result}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending WeChat markdown: {str(e)}")
            return False
    
    async def send_tweet_notification(self, tweet_data: Dict[str, Any]) -> bool:
        content = self._format_tweet_message(tweet_data)
        return await self.send_markdown(content)
    
    def _format_tweet_message(self, tweet_data: Dict[str, Any]) -> str:
        username = tweet_data.get('author', 'Unknown')
        text = tweet_data.get('text', '')
        url = tweet_data.get('url', '')
        metrics = tweet_data.get('metrics', {})
        
        formatted_text = text[:200] + "..." if len(text) > 200 else text
        
        message = f"""## 🐦 新推文监控提醒

**用户**: @{username}
**内容**: {formatted_text}

**数据**:
- 👍 点赞: {metrics.get('likes', 0)}
- 🔄 转推: {metrics.get('retweets', 0)}
- 💬 回复: {metrics.get('replies', 0)}

[查看推文]({url})"""
        
        return message
    
    def validate_webhook(self) -> bool:
        return bool(self.webhook_url and self.webhook_url.startswith('https://'))