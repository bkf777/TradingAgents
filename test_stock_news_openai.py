"""
测试 get_stock_news_openai 函数的独立测试文件
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.config import get_config, set_config
from tradingagents.default_config import DEFAULT_CONFIG
from openai import OpenAI

# 尝试导入 MCP 相关包，如果失败则提供替代方案
try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langgraph.prebuilt import create_react_agent
    from langchain_openai import ChatOpenAI
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"MCP 包导入失败: {e}")
    print("请安装 langchain-mcp-adapters 包: pip install langchain-mcp-adapters")
    MCP_AVAILABLE = False


async def get_stock_news_openai_fixed(ticker, curr_date):
    """
    修复后的 get_stock_news_openai 函数
    """
    # 获取配置
    config = get_config()
    
    # 创建 MCP 客户端（移除了不必要的 OpenAI 客户端创建）
    client = MultiServerMCPClient({
        "tavily-mcp": {
            "command": "npx",
            "args": ["-y", "tavily-mcp@0.1.2"],
            "env": {
                "TAVILY_API_KEY": "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"
            }
        }
    })
    
    try:
        # 获取工具
        tools = await client.get_tools()
        print(f"可用工具数量: {len(tools)}")
        
        # 创建 LLM 实例
        llm = ChatOpenAI(
            model=config["quick_think_llm"],
            base_url=config["backend_url"],
            api_key=config["openai_api_key"]
        )
        
        # 创建 React 代理
        agent = create_react_agent(llm, tools)
        
        # 构建查询消息
        query = f"Can you search Social Media for {ticker} from 7 days before {curr_date} to {curr_date}? Make sure you only get the data posted during that period."
        
        print(f"查询: {query}")
        
        # 调用代理
        response = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
        
        print("响应:")
        print(response)
        
        # 返回响应内容
        if hasattr(response, 'choices') and response.choices:
            return response.choices[0].message.content
        elif isinstance(response, dict) and 'messages' in response:
            # LangGraph 返回的格式
            messages = response['messages']
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                elif isinstance(last_message, dict) and 'content' in last_message:
                    return last_message['content']
        
        return str(response)
        
    except Exception as e:
        print(f"错误: {e}")
        return f"错误: {str(e)}"
    
    finally:
        # 清理资源
        try:
            await client.close()
        except:
            pass


async def test_function():
    """
    测试函数
    """
    # 设置配置
    config = DEFAULT_CONFIG.copy()
    config["backend_url"] = "https://api.nuwaapi.com/v1"
    config["quick_think_llm"] = "gpt-4o-mini"
    set_config(config)
    
    print("开始测试 get_stock_news_openai 函数...")
    print(f"配置: {config}")
    
    # 测试参数
    ticker = "NVDA"
    curr_date = "2024-06-10"
    
    print(f"测试参数: ticker={ticker}, curr_date={curr_date}")
    
    try:
        # 调用函数
        result = await get_stock_news_openai_fixed(ticker, curr_date)
        
        print("\n=== 测试结果 ===")
        print(result)
        print("=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_function())
