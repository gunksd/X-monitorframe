# X-monitorframe

基于 Twitter API → FastAPI → 企业微信 Webhook 的推特监控框架

## 功能特性

- 🐦 **高频实时监控**：20秒间隔监控多个 Twitter 账号的推文
- 📱 **智能消息推送**：自动推送通知到企业微信群聊，清晰显示用户名
- 🖼️ **完整媒体支持**：转发图片、视频预览和动图链接
- 🗄️ **数据持久存储**：SQLite 数据库存储推文记录和监控状态
- 🚀 **现代Web框架**：FastAPI + 实时管理面板
- ⚙️ **灵活配置管理**：可配置监控间隔、用户列表和通知格式
- 🛡️ **智能速率控制**：自动处理Twitter API限制，避免阻塞
- 📊 **详细数据统计**：推文互动数据（点赞、转发、回复数）
- 🎛️ **可视化管理**：Web管理界面，实时监控状态和日志

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

# 监控的用户名列表（逗号分隔）
TWITTER_USERNAMES=user1,user2,user3

# 检查间隔（秒）- 推荐20秒实现准实时监控
CHECK_INTERVAL_SECONDS=20

# 自动启动监控
AUTO_START_MONITORING=false
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

## Web 管理面板

访问 `http://localhost:8000` 打开可视化管理面板：

- 📊 **实时状态监控**：监控服务状态、速率限制状态
- 🎛️ **一键控制**：启动/停止监控、测试消息推送
- 👥 **用户管理**：查看监控用户列表和状态
- 📋 **实时日志**：查看系统运行日志和错误信息
- ⚠️ **智能提醒**：Twitter API限制状态和重置时间

## API 接口

### 基础接口

- `GET /` - Web管理面板
- `GET /api` - API服务状态
- `GET /health` - 健康检查
- `GET /monitor/status` - 详细监控状态（包含速率限制信息）

### 监控控制

- `POST /monitor/start` - 启动监控
- `POST /monitor/stop` - 停止监控
- `GET /monitor/users` - 获取监控用户列表
- `GET /monitor/logs` - 获取系统日志

### 通知测试

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
2. **高频检查**：每20秒检查一次用户的新推文
3. **智能过滤**：只处理未通知过的新推文，避免重复
4. **媒体解析**：自动解析推文中的图片、视频和动图
5. **格式化通知**：生成包含媒体链接的企业微信消息
6. **发送推送**：推送到企业微信群聊，清晰显示用户名
7. **数据存储**：将推文信息和媒体数据存储到数据库
8. **速率控制**：自动处理Twitter API限制，确保服务稳定

## 消息格式示例

当检测到新推文时，企业微信会收到如下格式的消息：

```markdown
## 🐦 @username 发布了新推文

**内容**: 这是一条包含图片的推文内容...

**媒体内容**:
- 🖼️ [图片1](https://pbs.twimg.com/media/xxx.jpg)
- 🎥 [视频1预览](https://pbs.twimg.com/ext_tw_video_thumb/xxx.jpg)

**数据**:
- 👍 点赞: 1,234
- 🔄 转推: 567
- 💬 回复: 89

[查看原推文](https://twitter.com/username/status/123456789)
```

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

## 安全注意事项

⚠️ **重要安全提醒**：

1. **配置文件安全**：`.env` 文件包含敏感信息，已被 `.gitignore` 保护
2. **Token 保护**：Twitter Bearer Token 和企业微信 Webhook URL 绝不能提交到版本控制
3. **数据库隐私**：`*.db` 文件包含推文数据，已自动排除跟踪
4. **生产部署**：部署时使用环境变量或安全的配置管理工具

## 故障排除

### 常见问题

1. **Twitter API 限制**：检查 Bearer Token 是否有效，注意 API 速率限制
2. **企业微信通知失败**：验证 Webhook URL 格式和权限
3. **数据库问题**：检查文件权限，确保数据目录可写
4. **速率限制频繁**：考虑增加 `CHECK_INTERVAL_SECONDS` 间隔时间

### 日志查看

```bash
# 查看应用日志
docker-compose logs twitter-monitor

# 实时日志
docker-compose logs -f twitter-monitor
```

## 许可证

Apache License 2.0 License
