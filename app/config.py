from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    TWITTER_BEARER_TOKEN: str
    WECHAT_WEBHOOK_URL: str
    
    TWITTER_USERNAMES: List[str] = []
    CHECK_INTERVAL_SECONDS: int = 300  # 5分钟检查一次
    AUTO_START_MONITORING: bool = False
    
    DATABASE_URL: Optional[str] = "sqlite:///./twitter_monitor.db"
    
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()