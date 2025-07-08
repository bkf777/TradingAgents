# MCP (Model Context Protocol) 使用指南

本文档介绍如何在 TradingAgents 中使用 MCP 功能来扩展系统的数据获取和分析能力。

## 概述

MCP (Model Context Protocol) 是一个开放标准，允许 AI 应用程序与外部数据源和工具进行安全、标准化的集成。在 TradingAgents 中，我们已经集成了 MCP 支持，特别是通过 `langchain-mcp-adapters` 包。

## 安装依赖

确保已安装必要的依赖：

```bash
pip install langchain-mcp-adapters
```

或者使用项目的 requirements.txt：

```bash
pip install -r requirements.txt
```

## 基本使用

### 1. 预定义的 MCP 工具

TradingAgents 提供了几个预定义的 MCP 工具：

```python
from tradingagents.agents.utils.agent_utils import Toolkit

# 网络搜索
result = Toolkit.search_web_with_mcp(
    query="NVIDIA Q4 2024 earnings",
    max_results=5
)

# 财经新闻获取
news = Toolkit.get_financial_news_mcp(
    topic="Federal Reserve interest rate",
    date_range="last 7 days"
)

# 市场情绪分析
sentiment = Toolkit.analyze_market_sentiment_mcp(
    ticker="AAPL",
    analysis_period="last 30 days"
)

# 竞争对手分析
competition = Toolkit.get_competitor_analysis_mcp(
    company="Tesla",
    industry="electric vehicle"
)
```

### 2. MCP 服务器配置

#### Tavily 搜索配置
```python
tavily_config = Toolkit.get_tavily_mcp_config(
    api_key="your-tavily-api-key"
)
```

#### 文件系统配置
```python
filesystem_config = Toolkit.get_filesystem_mcp_config(
    allowed_directories=["/path/to/data", "/path/to/reports"]
)
```

#### 网络搜索配置
```python
web_search_config = Toolkit.get_web_search_mcp_config()
```

## 高级使用

### 1. 创建自定义 MCP 工具

```python
# 创建基于 Tavily 的自定义搜索工具
custom_tool = Toolkit.create_tavily_search_tool(
    tool_name="analyze_crypto_trends",
    search_template="Search for cryptocurrency market trends for {crypto} in {timeframe}. Include price analysis, market sentiment, and regulatory news.",
    description="分析加密货币市场趋势"
)

# 创建完全自定义的 MCP 工具
earnings_tool = Toolkit.create_custom_mcp_tool(
    tool_name="get_earnings_calendar",
    description="获取财报日历信息",
    server_configs=Toolkit.get_tavily_mcp_config(),
    query_template="Search for earnings calendar and upcoming earnings announcements for {sector} companies in {month} {year}"
)
```

### 2. 直接使用 MCP 客户端

```python
import asyncio

async def advanced_mcp_usage():
    # 创建 MCP 代理
    client, agent = await Toolkit.create_mcp_agent(
        server_configs=Toolkit.get_tavily_mcp_config()
    )
    
    try:
        # 执行复杂查询
        response = await agent.ainvoke({
            "messages": [{"role": "user", "content": "Analyze Apple's competitive position"}]
        })
        
        print(response)
    finally:
        await client.close()

# 运行异步函数
asyncio.run(advanced_mcp_usage())
```

### 3. 同步执行 MCP 查询

```python
# 使用同步包装器
result = Toolkit.run_mcp_query_sync(
    query="Search for Tesla's latest autopilot developments",
    server_configs=Toolkit.get_tavily_mcp_config(),
    description="Tesla 自动驾驶技术搜索"
)
```

## 专业分析工具

### 1. 财报分析工具
```python
earnings_tool = Toolkit.get_earnings_analysis_tool()
# 使用方式：分析特定公司的财报表现
```

### 2. 监管新闻工具
```python
regulatory_tool = Toolkit.get_regulatory_news_tool()
# 使用方式：获取影响特定行业的监管变化
```

### 3. 并购分析工具
```python
ma_tool = Toolkit.get_merger_acquisition_tool()
# 使用方式：分析并购活动和市场影响
```

## 与交易系统集成

### 1. 注册 MCP 工具到代理

```python
# 获取所有 MCP 工具
mcp_tools = Toolkit.get_all_mcp_tools()

# 注册到工具列表
registered_tools = Toolkit.register_mcp_tools()

# 在创建代理时使用
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4")
agent = create_react_agent(llm, registered_tools)
```

### 2. 在交易决策流程中使用

```python
def trading_decision_with_mcp(ticker, date):
    """使用 MCP 工具进行交易决策"""
    
    # 1. 获取最新新闻
    news = Toolkit.get_financial_news_mcp(
        topic=f"{ticker} earnings news",
        date_range="last 7 days"
    )
    
    # 2. 分析市场情绪
    sentiment = Toolkit.analyze_market_sentiment_mcp(
        ticker=ticker,
        analysis_period="last 14 days"
    )
    
    # 3. 竞争对手分析
    competition = Toolkit.get_competitor_analysis_mcp(
        company=ticker,
        industry="technology"
    )
    
    # 4. 综合分析并做出决策
    # ... 决策逻辑
    
    return {
        "news": news,
        "sentiment": sentiment,
        "competition": competition
    }
```

## 配置和自定义

### 1. 自定义 LLM 配置

```python
custom_llm_config = {
    "quick_think_llm": "gpt-4o-mini",
    "backend_url": "https://api.nuwaapi.com/v1/chat/completions",
    "openai_api_key": "your-api-key"
}

# 使用自定义配置执行查询
result = Toolkit.run_mcp_query_sync(
    query="Search for market analysis",
    server_configs=Toolkit.get_tavily_mcp_config(),
    llm_config=custom_llm_config
)
```

### 2. 多服务器配置

```python
# 组合多个 MCP 服务器
multi_config = {}
multi_config.update(Toolkit.get_tavily_mcp_config())
multi_config.update(Toolkit.get_web_search_mcp_config())

# 使用多服务器配置
client, agent = await Toolkit.create_mcp_agent(multi_config)
```

## 最佳实践

1. **错误处理**: 始终包含适当的错误处理，特别是在网络请求中
2. **资源清理**: 使用 `try/finally` 块确保 MCP 客户端正确关闭
3. **超时设置**: 为长时间运行的查询设置合理的超时时间
4. **API 密钥管理**: 安全地管理 API 密钥，避免硬编码
5. **查询优化**: 编写清晰、具体的查询以获得更好的结果

## 故障排除

### 常见问题

1. **MCP 包导入失败**: 确保安装了 `langchain-mcp-adapters`
2. **超时错误**: 增加超时时间或优化查询
3. **API 密钥错误**: 检查 API 密钥是否正确配置
4. **网络连接问题**: 确保网络连接正常

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 测试 MCP 连接
try:
    result = Toolkit.search_web_with_mcp("test query")
    print("MCP 连接正常")
except Exception as e:
    print(f"MCP 连接失败: {e}")
```

## 示例代码

完整的使用示例请参考 `examples/mcp_usage_example.py` 文件。

## 参考资源

- [langchain-mcp-adapters 文档](https://github.com/langchain-ai/langchain-mcp-adapters)
- [Model Context Protocol 规范](https://modelcontextprotocol.io/)
- [Tavily API 文档](https://tavily.com/)
