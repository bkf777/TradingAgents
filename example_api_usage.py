#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingAgents API 使用示例
演示如何调用简化版API进行股票分析
"""

import requests
import json
import time
from datetime import datetime

# API服务器地址
API_BASE_URL = "http://localhost:5000"


def analyze_stock(symbol, date, conversation_id=None, config=None):
    """
    调用股票分析API

    Args:
        symbol (str): 股票代码
        date (str): 分析日期 (YYYY-MM-DD)
        conversation_id (str): 可选的会话ID
        config (dict): 可选的自定义配置

    Returns:
        dict: 分析结果
    """
    url = f"{API_BASE_URL}/analyze"

    # 准备请求数据
    data = {"symbol": symbol, "date": date}

    if conversation_id:
        data["conversation_id"] = conversation_id

    if config:
        data["config"] = config

    print(f"🔍 开始分析股票: {symbol}")
    print(f"📅 分析日期: {date}")
    print(f"📋 请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

    try:
        # 发送POST请求
        response = requests.post(
            url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=300,  # 5分钟超时
        )

        print(f"📊 响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ 分析成功!")
            return result
        else:
            print(f"❌ 分析失败: {response.text}")
            return None

    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return None
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        return None


def check_server_health():
    """检查服务器健康状态"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            health_data = response.json()
            print("✅ 服务器状态正常")
            print(f"   数据库状态: {health_data.get('database', 'unknown')}")
            print(f"   服务器版本: {health_data.get('version', 'unknown')}")
            return True
        else:
            print(f"❌ 服务器状态异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务器: {str(e)}")
        return False


def main():
    """主函数 - 演示API使用"""
    print("=" * 60)
    print("TradingAgents API 使用示例")
    print("=" * 60)

    # 1. 检查服务器健康状态
    print("\n1. 检查服务器状态...")
    if not check_server_health():
        print("请确保API服务器正在运行: python api_server_simple.py")
        return

    # 2. 基本股票分析示例
    print("\n2. 基本股票分析示例...")
    result = analyze_stock(
        symbol="NVDA", date="2025-01-01", conversation_id="demo_conversation_001"
    )

    if result:
        print(f"\n📈 分析结果:")
        print(f"   股票代码: {result.get('symbol')}")
        print(f"   分析日期: {result.get('analysis_date')}")
        print(f"   会话ID: {result.get('conversation_id')}")
        print(f"   决策建议: {result.get('decision', '无')[:100]}...")
        print(f"   AI消息数量: {len(result.get('ai_messages', []))}")

        # 显示前几条AI消息
        ai_messages = result.get("ai_messages", [])
        if ai_messages:
            print(f"\n📝 AI分析摘要 (前3条):")
            for i, msg in enumerate(ai_messages[:3]):
                print(f"   {i+1}. [{msg['type']}] {msg['content'][:80]}...")

    # 3. 自定义配置示例
    print("\n3. 自定义配置分析示例...")
    custom_config = {
        "max_debate_rounds": 2,  # 增加辩论轮次
        "online_tools": True,  # 使用在线工具
        "quick_think_llm": "gpt-4o-mini",  # 指定模型
    }

    result = analyze_stock(symbol="AAPL", date="2025-01-01", config=custom_config)

    if result:
        print(f"\n📈 自定义配置分析结果:")
        print(f"   股票代码: {result.get('symbol')}")
        print(f"   决策建议: {result.get('decision', '无')[:100]}...")

    # 4. 错误处理示例
    print("\n4. 错误处理示例...")
    result = analyze_stock(symbol="", date="2025-01-01")  # 空的股票代码

    print("\n=" * 60)
    print("示例完成!")
    print("=" * 60)

    print("\n💡 使用提示:")
    print("1. 确保API服务器正在运行")
    print("2. 股票代码支持美股 (如 NVDA, AAPL) 和A股 (如 000001)")
    print("3. 分析可能需要几分钟时间，请耐心等待")
    print("4. 可以通过config参数自定义分析配置")

    print("\n🔗 相关链接:")
    print(f"   API服务器: {API_BASE_URL}")
    print(f"   健康检查: {API_BASE_URL}/health")
    print(f"   分析接口: {API_BASE_URL}/analyze")


if __name__ == "__main__":
    main()
