from fastapi import FastAPI, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
import asyncio
import logging
from app.config import settings
from app.services.twitter_service import TwitterService
from app.services.wechat_service import WeChatService
from app.services.monitor_service import MonitorService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

monitor_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global monitor_service
    
    twitter_service = TwitterService()
    wechat_service = WeChatService()
    monitor_service = MonitorService(twitter_service, wechat_service)
    
    if settings.AUTO_START_MONITORING:
        asyncio.create_task(monitor_service.start_monitoring())
        logger.info("Auto-started monitoring service")
    
    yield
    
    if monitor_service:
        await monitor_service.stop_monitoring()
        logger.info("Stopped monitoring service")

app = FastAPI(
    title="Twitter Monitor Framework",
    description="Monitor Twitter posts and send notifications to WeChat Work",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"message": "Twitter Monitor Framework", "status": "running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "monitoring_active": monitor_service.is_monitoring if monitor_service else False
    }

@app.post("/monitor/start")
async def start_monitoring():
    if not monitor_service:
        raise HTTPException(status_code=500, detail="Monitor service not initialized")
    
    if monitor_service.is_monitoring:
        return {"message": "Monitoring already active"}
    
    asyncio.create_task(monitor_service.start_monitoring())
    return {"message": "Monitoring started"}

@app.post("/monitor/stop")
async def stop_monitoring():
    if not monitor_service:
        raise HTTPException(status_code=500, detail="Monitor service not initialized")
    
    if not monitor_service.is_monitoring:
        return {"message": "Monitoring not active"}
    
    await monitor_service.stop_monitoring()
    return {"message": "Monitoring stopped"}

@app.get("/monitor/status")
async def monitor_status():
    if not monitor_service:
        raise HTTPException(status_code=500, detail="Monitor service not initialized")
    
    return {
        "is_monitoring": monitor_service.is_monitoring,
        "monitored_users": len(settings.TWITTER_USERNAMES),
        "check_interval": settings.CHECK_INTERVAL_SECONDS
    }

@app.post("/webhook/test")
async def test_webhook():
    wechat_service = WeChatService()
    success = await wechat_service.send_message("测试消息：Twitter 监控框架运行正常")
    
    if success:
        return {"message": "Test message sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test message")