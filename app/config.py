from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    TWITTER_BEARER_TOKEN: str
    WECHAT_WEBHOOK_URL: str
    
    TWITTER_USERNAMES: str = ""  # 改为字符串类型，稍后解析
    CHECK_INTERVAL_SECONDS: int = 20  # 20秒检查一次，实现准实时监控
    AUTO_START_MONITORING: bool = False
    
    DATABASE_URL: Optional[str] = "sqlite:///./twitter_monitor.db"
    
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def twitter_usernames_list(self) -> List[str]:
        """将逗号分隔的用户名字符串转换为列表"""
        if not self.TWITTER_USERNAMES:
            return []
        return [username.strip() for username in self.TWITTER_USERNAMES.split(',') if username.strip()]

settings = Settings()