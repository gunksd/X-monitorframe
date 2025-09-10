# X-monitorframe

基于 Twitter API → FastAPI → 企业微信 Webhook 的推特监控框架

## 功能特性

- 🐦 实时监控多个 Twitter 账号的推文
- 📱 自动推送通知到企业微信群聊
- 🗄️ SQLite 数据库存储推文记录
- 🚀 FastAPI Web 框架，提供 REST API
- ⚙️ 可配置的监控间隔和用户列表
- 🐳 Docker 容器化部署
- 📊 推文数据统计（点赞、转发、回复数）

## 快速开始

### 1. 环境配置

复制环境配置文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入必要的配置：
```env
# Twitter API Bearer Token
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here

# 企业微信 Webhook URL
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your_webhook_key_here

# 监控的用户名列表
TWITTER_USERNAMES=["elonmusk", "openai", "tesla"]

# 检查间隔（秒）
CHECK_INTERVAL_SECONDS=300

# 自动启动监控
AUTO_START_MONITORING=true
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行应用

```bash
python run.py
```

或使用 uvicorn：
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Docker 部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## API 接口

### 基础接口

- `GET /` - 服务状态
- `GET /health` - 健康检查
- `GET /monitor/status` - 监控状态

### 监控控制

- `POST /monitor/start` - 启动监控
- `POST /monitor/stop` - 停止监控
- `POST /webhook/test` - 测试企业微信通知

### 示例请求

```bash
# 启动监控
curl -X POST "http://localhost:8000/monitor/start"

# 获取监控状态
curl "http://localhost:8000/monitor/status"

# 测试企业微信通知
curl -X POST "http://localhost:8000/webhook/test"
```

## 配置说明

### Twitter API 配置

1. 访问 [Twitter Developer Portal](https://developer.twitter.com/)
2. 创建应用并获取 Bearer Token
3. 将 Token 填入 `TWITTER_BEARER_TOKEN` 配置项

### 企业微信 Webhook 配置

1. 在企业微信群聊中添加群机器人
2. 获取 Webhook URL
3. 将 URL 填入 `WECHAT_WEBHOOK_URL` 配置项

### 监控用户配置

在 `TWITTER_USERNAMES` 中配置要监控的 Twitter 用户名：
```env
TWITTER_USERNAMES=["user1", "user2", "user3"]
```

## 项目结构

```
X-monitorframe/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 主应用
│   ├── config.py            # 配置管理
│   ├── models/
│   │   ├── __init__.py
│   │   └── database.py      # 数据库模型
│   └── services/
│       ├── __init__.py
│       ├── twitter_service.py    # Twitter API 服务
│       ├── wechat_service.py     # 企业微信服务
│       └── monitor_service.py    # 监控服务
├── .env.example             # 环境配置模板
├── requirements.txt         # Python 依赖
├── run.py                   # 启动脚本
├── Dockerfile              # Docker 镜像配置
├── docker-compose.yml      # Docker Compose 配置
└── README.md               # 项目文档
```

## 监控流程

1. **初始化**：系统启动时初始化数据库和服务
2. **定期检查**：按配置间隔检查用户的新推文
3. **消息过滤**：只处理未通知过的新推文
4. **发送通知**：格式化推文内容并发送到企业微信
5. **记录存储**：将推文信息存储到数据库

## 扩展功能

### 自定义通知格式

修改 `app/services/wechat_service.py` 中的 `_format_tweet_message` 方法：

```python
def _format_tweet_message(self, tweet_data: Dict[str, Any]) -> str:
    # 自定义消息格式
    return f"新推文来自 @{tweet_data['author']}: {tweet_data['text']}"
```

### 添加关键词过滤

在 `MonitorService` 中添加关键词检查逻辑：

```python
def _should_notify(self, tweet_text: str) -> bool:
    keywords = ["关键词1", "关键词2"]
    return any(keyword in tweet_text for keyword in keywords)
```

### 多通道通知

扩展 `WeChatService`，支持多个企业微信群或其他通知渠道。

## 故障排除

### 常见问题

1. **Twitter API 限制**：检查 Bearer Token 是否有效，注意 API 速率限制
2. **企业微信通知失败**：验证 Webhook URL 格式和权限
3. **数据库问题**：检查文件权限，确保数据目录可写

### 日志查看

```bash
# 查看应用日志
docker-compose logs twitter-monitor

# 实时日志
docker-compose logs -f twitter-monitor
```

## 许可证

MIT License
