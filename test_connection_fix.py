#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试连接修复
验证新闻分析师的连接问题是否已解决
"""

import sys
import os
import asyncio
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_news_analyst_with_retry():
    """测试带重试机制的新闻分析师"""
    print("=" * 50)
    print("测试新闻分析师（带重试机制）")
    print("=" * 50)

    try:
        from tradingagents.agents.analysts.news_analyst import create_news_analyst
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.agents.utils.agent_utils import Toolkit
        from langchain_core.messages import HumanMessage

        # 创建配置
        config = DEFAULT_CONFIG.copy()

        # 创建工具包
        toolkit = Toolkit(config=config)

        # 创建新闻分析师
        news_analyst = create_news_analyst(toolkit)

        # 创建测试状态
        test_state = {
            "messages": [HumanMessage(content="请分析NVDA的最新新闻")],
            "ticker": "NVDA",
            "current_date": datetime.now().strftime("%Y-%m-%d"),
        }

        print("调用新闻分析师...")
        result = news_analyst(test_state)

        print("✅ 新闻分析师调用成功")
        print(f"返回消息数量: {len(result.get('messages', []))}")
        if result.get("news_report"):
            print(f"新闻报告长度: {len(result['news_report'])} 字符")

        return True

    except Exception as e:
        print(f"❌ 新闻分析师调用失败: {str(e)}")
        return False


def test_trading_graph_initialization():
    """测试交易图初始化"""
    print("\n" + "=" * 50)
    print("测试交易图初始化")
    print("=" * 50)

    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG

        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "openai"
        config["backend_url"] = "https://api.nuwaapi.com/v1"

        print("初始化交易图...")
        ta = TradingAgentsGraph(debug=True, config=config)

        print("✅ 交易图初始化成功")
        print(f"LLM提供商: {config['llm_provider']}")
        print(f"后端URL: {config['backend_url']}")

        return True

    except Exception as e:
        print(f"❌ 交易图初始化失败: {str(e)}")
        return False


def test_simple_analysis():
    """测试简单的股票分析"""
    print("\n" + "=" * 50)
    print("测试简单股票分析")
    print("=" * 50)

    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG

        # 创建配置
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "openai"
        config["backend_url"] = "https://api.nuwaapi.com/v1"
        config["max_debate_rounds"] = 1  # 减少轮次以快速测试

        print("初始化交易图...")
        ta = TradingAgentsGraph(debug=True, config=config)

        print("开始分析 NVDA...")
        final_state, decision = ta.propagate("NVDA", "2025-01-01")

        print("✅ 股票分析完成")
        print(f"决策: {decision}")

        return True

    except Exception as e:
        print(f"❌ 股票分析失败: {str(e)}")
        print(f"错误类型: {type(e).__name__}")

        # 检查是否是连接错误
        error_msg = str(e).lower()
        connection_errors = [
            "connection error",
            "ssl",
            "timeout",
            "eof occurred",
            "connection reset",
        ]

        is_connection_error = any(err in error_msg for err in connection_errors)
        if is_connection_error:
            print("🔍 这是一个连接错误，重试机制应该会处理")

        return False


def test_robust_client():
    """测试稳定的客户端"""
    print("\n" + "=" * 50)
    print("测试稳定的API客户端")
    print("=" * 50)

    try:
        from tradingagents.utils.api_client import get_robust_openai_client

        print("创建稳定的OpenAI客户端...")
        client = get_robust_openai_client()

        print("测试API调用...")
        response = client.chat_completions_create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello, this is a connection test."}],
            max_tokens=50,
        )

        print("✅ 稳定客户端调用成功")
        print(f"响应: {response.choices[0].message.content}")

        return True

    except Exception as e:
        print(f"❌ 稳定客户端调用失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("开始连接修复测试...")
    print(f"测试时间: {datetime.now()}")

    results = []

    # 运行所有测试
    results.append(("稳定客户端测试", test_robust_client()))
    results.append(("交易图初始化测试", test_trading_graph_initialization()))
    results.append(("新闻分析师测试", test_news_analyst_with_retry()))
    # results.append(("简单分析测试", test_simple_analysis()))  # 注释掉以避免长时间运行

    # 显示结果
    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("🎉 所有测试都通过了！连接问题已修复。")
    else:
        print("⚠️ 部分测试失败，可能仍存在连接问题。")

    print("\n建议:")
    print("1. 如果测试仍然失败，可能需要检查网络环境")
    print("2. 可以尝试增加重试次数或超时时间")
    print("3. 考虑使用不同的API端点")


if __name__ == "__main__":
    main()
