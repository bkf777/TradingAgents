"""
测试 OpenAI 相关函数的独立测试文件
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.config import get_config, set_config
from tradingagents.default_config import DEFAULT_CONFIG

# 直接从 interface 模块导入函数
from tradingagents.dataflows.interface import get_stock_news_openai, get_global_news_openai, get_fundamentals_openai


async def test_get_stock_news_openai():
    """
    测试 get_stock_news_openai 函数
    """
    print("\n=== 测试 get_stock_news_openai ===")
    
    ticker = "NVDA"
    curr_date = "2025-06-10"
    
    print(f"参数: ticker={ticker}, curr_date={curr_date}")
    
    try:
        result = await get_stock_news_openai(ticker, curr_date)
        print("结果:")
        print(result)
        return result
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return f"错误: {str(e)}"


async def test_get_global_news_openai():
    """
    测试 get_global_news_openai 函数
    """
    print("\n=== 测试 get_global_news_openai ===")

    curr_date = "2025-06-10"

    print(f"参数: curr_date={curr_date}")

    try:
        result = await get_global_news_openai(curr_date)
        print("结果:")
        print(result)
        return result
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return f"错误: {str(e)}"


async def test_get_fundamentals_openai():
    """
    测试 get_fundamentals_openai 函数
    """
    print("\n=== 测试 get_fundamentals_openai ===")

    ticker = "NVDA"
    curr_date = "2025-06-10"

    print(f"参数: ticker={ticker}, curr_date={curr_date}")

    try:
        result = await get_fundamentals_openai(ticker, curr_date)
        print("结果:")
        print(result)
        return result
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return f"错误: {str(e)}"


async def main():
    """
    主测试函数
    """
    # 设置配置
    config = DEFAULT_CONFIG.copy()
    # 使用正确的完整端点 URL（这个 API 需要完整路径）
    config["backend_url"] = "https://api.nuwaapi.com/v1"
    config["quick_think_llm"] = "gpt-4o-mini"
    set_config(config)
    
    print("开始测试 OpenAI 相关函数...")
    print(f"配置: backend_url={config['backend_url']}")
    print(f"模型: {config['quick_think_llm']}")
    
    # 测试所有函数
    results = {}
    
    # 测试 get_stock_news_openai (异步)
    results['stock_news'] = await test_get_stock_news_openai()
    
    # 测试 get_global_news_openai (现在是异步)
    results['global_news'] = await test_get_global_news_openai()

    # 测试 get_fundamentals_openai (现在是异步)
    results['fundamentals'] = await test_get_fundamentals_openai()
    
    print("\n=== 所有测试完成 ===")
    print("测试结果摘要:")
    for test_name, result in results.items():
        status = "成功" if not result.startswith("错误:") else "失败"
        print(f"- {test_name}: {status}")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
