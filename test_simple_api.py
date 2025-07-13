#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试简化版API服务器
"""

import requests
import json
import time
from datetime import datetime

# API服务器地址
BASE_URL = "http://localhost:5000"


def test_health_check():
    """测试健康检查接口"""
    print("=" * 50)
    print("测试健康检查接口")
    print("=" * 50)

    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 健康检查失败: {str(e)}")
        return False


def test_root_endpoint():
    """测试根路径"""
    print("\n" + "=" * 50)
    print("测试根路径")
    print("=" * 50)

    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 根路径测试失败: {str(e)}")
        return False


def test_analyze_endpoint():
    """测试分析接口"""
    print("\n" + "=" * 50)
    print("测试分析接口")
    print("=" * 50)

    # 测试数据
    test_data = {
        "symbol": "NVDA",
        "date": "2025-01-01",
        "conversation_id": "test_conversation_001",
        "config": {"max_debate_rounds": 1, "online_tools": True},
    }

    try:
        print(f"发送请求: {json.dumps(test_data, indent=2, ensure_ascii=False)}")

        # 发送POST请求
        response = requests.post(
            f"{BASE_URL}/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=300,  # 5分钟超时
        )

        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ 分析成功!")
            print(f"股票代码: {result.get('symbol')}")
            print(f"分析日期: {result.get('analysis_date')}")
            print(f"会话ID: {result.get('conversation_id')}")
            print(f"决策: {result.get('decision')}")
            print(f"AI消息数量: {len(result.get('ai_messages', []))}")

            # 显示前几条AI消息
            ai_messages = result.get("ai_messages", [])
            if ai_messages:
                print("\n前3条AI消息:")
                for i, msg in enumerate(ai_messages[:3]):
                    print(f"  {i+1}. [{msg['type']}] {msg['content'][:100]}...")

            return True
        else:
            print(f"❌ 分析失败: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 分析接口测试失败: {str(e)}")
        return False


def test_analyze_with_invalid_data():
    """测试分析接口的错误处理"""
    print("\n" + "=" * 50)
    print("测试分析接口错误处理")
    print("=" * 50)

    # 测试缺少必要参数
    invalid_data = {
        "symbol": "NVDA"
        # 缺少 date 参数
    }

    try:
        response = requests.post(
            f"{BASE_URL}/analyze",
            json=invalid_data,
            headers={"Content-Type": "application/json"},
        )

        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

        # 应该返回400错误
        return response.status_code == 400

    except Exception as e:
        print(f"❌ 错误处理测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("开始测试简化版API服务器...")
    print(f"测试时间: {datetime.now()}")
    print(f"API地址: {BASE_URL}")

    # 等待服务器启动
    print("\n等待服务器启动...")
    time.sleep(2)

    results = []

    # 运行所有测试
    results.append(("健康检查", test_health_check()))
    results.append(("根路径", test_root_endpoint()))
    results.append(("错误处理", test_analyze_with_invalid_data()))
    # results.append(("分析接口", test_analyze_endpoint()))  # 注释掉以避免长时间运行

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
        print("🎉 所有测试都通过了！")
    else:
        print("⚠️ 部分测试失败。")

    print("\n使用说明:")
    print("1. 启动服务器: python api_server_simple.py")
    print("2. 查看API文档: http://localhost:5000/docs/")
    print("3. 健康检查: http://localhost:5000/health")
    print("4. 分析接口: POST http://localhost:5000/analyze")
    print("\n分析接口示例:")
    print(
        json.dumps(
            {
                "symbol": "NVDA",
                "date": "2025-01-01",
                "conversation_id": "my_conversation_001",
                "config": {"max_debate_rounds": 1, "online_tools": True},
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
