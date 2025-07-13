# TradingAgents 简化版 API 服务器

这是一个简化版的 TradingAgents API 服务器，只提供股票分析功能。

## 功能特点

- ✅ **单一分析接口** - 只保留 `/analyze` 接口
- ✅ **简化配置** - 减少不必要的复杂性
- ✅ **错误处理** - 完善的错误处理和日志记录
- ✅ **数据库支持** - 可选的 MySQL 数据库集成
- ✅ **API 文档** - 自动生成的 Swagger 文档
- ✅ **健康检查** - 服务器状态监控

## 安装和启动

### 1. 启动服务器

```bash
python api_server_simple.py
```

服务器将在 `http://localhost:5000` 启动

### 2. 查看 API 文档

访问 `http://localhost:5000/docs/` 查看完整的 API 文档

### 3. 健康检查

访问 `http://localhost:5000/health` 检查服务器状态

## API 接口

### 分析接口

**POST** `/analyze`

执行股票分析并返回结果。

#### 请求参数

```json
{
  "symbol": "NVDA",
  "date": "2025-01-01",
  "conversation_id": "my_conversation_001",
  "config": {
    "max_debate_rounds": 1,
    "online_tools": true
  }
}
```

#### 参数说明

- `symbol` (必需): 股票代码，如 "NVDA", "AAPL", "000001"
- `date` (必需): 分析日期，格式 "YYYY-MM-DD"
- `conversation_id` (可选): 会话 ID，用于数据库存储和会话管理。如果不提供，系统会自动生成
- `config` (可选): 自定义配置参数

#### 响应示例

```json
{
  "success": true,
  "symbol": "NVDA",
  "analysis_date": "2025-01-01",
  "conversation_id": "my_conversation_001",
  "decision": "买入建议...",
  "ai_messages": [
    {
      "type": "ai",
      "content": "分析消息内容...",
      "timestamp": "2025-01-01T12:00:00",
      "step_index": 0,
      "message_index": 0
    }
  ],
  "final_state": {},
  "timestamp": "2025-01-01T12:00:00"
}
```

### 健康检查接口

**GET** `/health`

检查服务器状态。

#### 响应示例

```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00",
  "database": "connected"
}
```

### 根路径

**GET** `/`

获取 API 服务器信息。

## 配置说明

### 默认配置

```python
DEFAULT_API_CONFIG = {
    "llm_provider": "openai",
    "backend_url": "https://api.nuwaapi.com/v1",
    "deep_think_llm": "o3-mini-high",
    "quick_think_llm": "o3-mini-high",
    "max_debate_rounds": 1,
    "online_tools": True,
    "reset_memory_collections": False,
}
```

### 自定义配置

可以通过请求的 `config` 参数覆盖默认配置：

```json
{
  "symbol": "NVDA",
  "date": "2025-01-01",
  "conversation_id": "custom_conversation_002",
  "config": {
    "max_debate_rounds": 2,
    "online_tools": false,
    "deep_think_llm": "gpt-4o-mini"
  }
}
```

## 数据库集成

服务器支持可选的 MySQL 数据库集成，用于保存 AI 交互消息。

### 数据库配置

确保 `database_config.py` 文件存在并配置正确：

```python
def get_db_config():
    return {
        "host": "localhost",
        "port": 13306,
        "database": "trading_analysis",
        "user": "root",
        "password": "12345678"
    }
```

### 数据库表结构

AI 消息将保存到数据库中，包含以下字段：

- `symbol`: 股票代码
- `analysis_date`: 分析日期
- `message_type`: 消息类型
- `content`: 消息内容
- `step_index`: 步骤索引
- `message_index`: 消息索引
- `timestamp`: 时间戳

## 测试

### 运行测试脚本

```bash
python test_simple_api.py
```

### 手动测试

使用 curl 命令测试：

```bash
# 健康检查
curl http://localhost:5000/health

# 股票分析
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NVDA",
    "date": "2025-01-01",
    "config": {
      "max_debate_rounds": 1,
      "online_tools": true
    }
  }'
```

## 错误处理

服务器提供完善的错误处理：

### 参数错误 (400)

```json
{
  "success": false,
  "message": "缺少必要参数: symbol 和 date"
}
```

### 服务器错误 (500)

```json
{
  "success": false,
  "message": "操作失败: 具体错误信息",
  "error_type": "ErrorType",
  "timestamp": "2025-01-01T12:00:00"
}
```

## 日志记录

服务器会记录详细的日志信息：

- 控制台输出：实时显示操作状态
- 日志文件：`api_server.log` 保存详细日志
- 错误追踪：完整的错误堆栈信息

## 性能优化建议

1. **连接池配置**：使用连接池优化数据库连接
2. **缓存机制**：对频繁请求的数据进行缓存
3. **异步处理**：对于长时间运行的分析任务使用异步处理
4. **负载均衡**：在生产环境中使用负载均衡器

## 部署建议

### 开发环境

```bash
python api_server_simple.py
```

### 生产环境

使用 WSGI 服务器如 Gunicorn：

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api_server_simple:app
```

## 故障排除

### 常见问题

1. **数据库连接失败**

   - 检查数据库配置
   - 确保数据库服务正在运行

2. **API 调用超时**

   - 增加请求超时时间
   - 检查网络连接

3. **内存不足**
   - 监控服务器内存使用
   - 考虑增加服务器资源

### 日志查看

```bash
# 查看实时日志
tail -f api_server.log

# 查看错误日志
grep "ERROR" api_server.log
```

## 联系支持

如有问题，请查看：

1. API 文档：`http://localhost:5000/docs/`
2. 健康检查：`http://localhost:5000/health`
3. 日志文件：`api_server.log`
