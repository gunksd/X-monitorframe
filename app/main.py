from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
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
templates = Jinja2Templates(directory="app/templates")

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

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api")
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

    # 获取速率限制信息
    twitter_service = monitor_service.twitter_service
    is_rate_limited = await twitter_service.is_rate_limited()
    reset_time = twitter_service.get_rate_limit_reset_time()

    return {
        "is_monitoring": monitor_service.is_monitoring,
        "monitored_users": len(settings.twitter_usernames_list),
        "check_interval": settings.CHECK_INTERVAL_SECONDS,
        "rate_limited": is_rate_limited,
        "rate_limit_reset_seconds": reset_time
    }

@app.get("/monitor/users")
async def get_monitored_users():
    """获取监控用户列表及状态"""
    users_data = []
    for username in settings.twitter_usernames_list:
        users_data.append({
            "username": username,
            "last_check": "刚刚",  # 实际应该从数据库获取
            "status": "正常"
        })

    return {
        "users": users_data,
        "total_count": len(users_data)
    }

@app.get("/monitor/logs")
async def get_logs():
    """获取系统日志"""
    import datetime
    now = datetime.datetime.now().strftime("%H:%M:%S")

    # 构建更详细的日志信息
    logs = []

    # 系统状态信息
    if monitor_service:
        if monitor_service.is_monitoring:
            logs.append(f"[{now}] INFO: ✅ 监控服务正在运行")
            logs.append(f"[{now}] INFO: 📊 监控用户数: {len(settings.twitter_usernames_list)}")
            logs.append(f"[{now}] INFO: ⏰ 检查间隔: {settings.CHECK_INTERVAL_SECONDS}秒")
            logs.append(f"[{now}] WARNING: ⚠️  Twitter API 速率限制生效中")
            logs.append(f"[{now}] INFO: 💤 等待速率限制重置...")
        else:
            logs.append(f"[{now}] INFO: ⏹️  监控服务已停止")
    else:
        logs.append(f"[{now}] ERROR: ❌ 监控服务未初始化")

    # 用户列表
    logs.append(f"[{now}] INFO: 👥 监控用户列表:")
    for username in settings.twitter_usernames_list:
        logs.append(f"[{now}] INFO:   - @{username}")

    return {
        "logs": logs,
        "timestamp": now
    }

@app.post("/webhook/test")
async def test_webhook():
    wechat_service = WeChatService()
    success = await wechat_service.send_message("测试消息：Twitter 监控框架运行正常")

    if success:
        return {"message": "Test message sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test message")

@app.post("/monitor/clear-rate-limit")
async def clear_rate_limit():
    """手动清除Twitter API速率限制状态"""
    if not monitor_service:
        raise HTTPException(status_code=500, detail="Monitor service not initialized")

    try:
        twitter_service = monitor_service.twitter_service
        twitter_service.rate_limited_until = None
        await twitter_service._clear_rate_limit_in_db()

        return {"message": "Rate limit status cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing rate limit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear rate limit: {str(e)}")