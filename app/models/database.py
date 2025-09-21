import aiosqlite
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

class TweetRecord:
    def __init__(self, tweet_id: str, username: str, content: str, 
                 tweet_url: str, created_at: str, metrics: str):
        self.tweet_id = tweet_id
        self.username = username
        self.content = content
        self.tweet_url = tweet_url
        self.created_at = created_at
        self.metrics = metrics

async def init_db():
    try:
        db_path = settings.DATABASE_URL.replace('sqlite:///', '')
        
        async with aiosqlite.connect(db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS tweet_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tweet_id TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tweet_url TEXT NOT NULL,
                    metrics TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_username_created 
                ON tweet_records(username, created_at DESC)
            ''')
            
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_tweet_id
                ON tweet_records(tweet_id)
            ''')

            # 添加速率限制状态表
            await db.execute('''
                CREATE TABLE IF NOT EXISTS rate_limit_status (
                    id INTEGER PRIMARY KEY,
                    rate_limited_until REAL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await db.commit()
            logger.info("Database initialized successfully")
            
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

@asynccontextmanager
async def get_db():
    db_path = settings.DATABASE_URL.replace('sqlite:///', '')
    db = None
    try:
        db = await aiosqlite.connect(db_path)
        yield db
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise
    finally:
        if db:
            await db.close()