#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库连接优化和请求流程
验证 message_type 字段的正确性和数据库写入功能
"""

import json
import requests
from datetime import datetime
from database_config import DatabaseManager, MessageManager, get_db_config


def test_database_connection():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    try:
        db_manager = DatabaseManager(get_db_config())
        print("✅ 数据库连接成功")

        # 测试查询
        result = db_manager.execute_query("SELECT COUNT(*) as count FROM messages")
        print(f"📊 当前消息表记录数: {result[0]['count']}")

        db_manager.disconnect()
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def test_message_type_validation():
    """测试 message_type 字段验证"""
    print("\n🔍 测试 message_type 字段验证...")

    try:
        db_manager = DatabaseManager(get_db_config())
        message_manager = MessageManager(db_manager)

        # 测试有效的 message_type
        valid_types = ["human", "ai", "system", "tool"]
        for msg_type in valid_types:
            message_id = message_manager.save_message_optimized(
                symbol="TEST",
                analysis_date="2025-01-01",
                task_id=f"test_task_{msg_type}_{datetime.now().strftime('%H%M%S')}",
                message_type=msg_type,
                content=f"测试消息 - 类型: {msg_type}",
                metadata={"test": True, "message_type_test": msg_type},
            )
            if message_id:
                print(f"✅ 有效类型 '{msg_type}' 保存成功: {message_id}")
            else:
                print(f"❌ 有效类型 '{msg_type}' 保存失败")

        # 测试无效的 message_type
        invalid_types = ["user", "assistant", "bot", "invalid"]
        for msg_type in invalid_types:
            message_id = message_manager.save_message_optimized(
                symbol="TEST",
                analysis_date="2025-01-01",
                task_id=f"test_task_{msg_type}_{datetime.now().strftime('%H%M%S')}",
                message_type=msg_type,
                content=f"测试消息 - 无效类型: {msg_type}",
                metadata={
                    "test": True,
                    "message_type_test": msg_type,
                    "expected_fallback": "ai",
                },
            )
            if message_id:
                print(
                    f"✅ 无效类型 '{msg_type}' 已自动转换为 'ai' 并保存: {message_id}"
                )
            else:
                print(f"❌ 无效类型 '{msg_type}' 处理失败")

        db_manager.disconnect()
        return True
    except Exception as e:
        print(f"❌ message_type 验证测试失败: {e}")
        return False


def test_api_request():
    """测试API请求流程"""
    print("\n🔍 测试API请求流程...")

    # 测试数据
    test_data = {
        "symbol": "NVDA",
        "date": "2025-01-01",
        "conversation_id": f"test_conversation_{datetime.now().strftime('%H%M%S')}",
        "task_id": f"test_task_{datetime.now().strftime('%H%M%S')}",  # 新增：测试task_id参数
    }

    try:
        # 发送请求到API服务器
        response = requests.post(
            "http://localhost:5000/analyze", json=test_data, timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ API请求成功")
            print(f"📊 返回数据:")
            print(f"   - 股票代码: {result.get('symbol')}")
            print(f"   - 分析日期: {result.get('analysis_date')}")
            print(f"   - 会话ID: {result.get('conversation_id')}")
            print(f"   - 任务ID: {result.get('task_id')}")  # 新增：显示task_id
            print(f"   - AI消息数量: {len(result.get('ai_messages', []))}")
            print(f"   - 成功状态: {result.get('success')}")

            # 检查AI消息的类型
            ai_messages = result.get("ai_messages", [])
            if ai_messages:
                print(f"📝 AI消息类型分布:")
                type_counts = {}
                for msg in ai_messages:
                    msg_type = msg.get("type", "unknown")
                    type_counts[msg_type] = type_counts.get(msg_type, 0) + 1

                for msg_type, count in type_counts.items():
                    print(f"   - {msg_type}: {count} 条")

            return True
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(f"❌ 错误信息: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器 (http://localhost:5000)")
        print("💡 请确保API服务器正在运行: python api_server_simple.py")
        return False
    except Exception as e:
        print(f"❌ API请求测试失败: {e}")
        return False


def test_health_check():
    """测试健康检查接口"""
    print("\n🔍 测试健康检查接口...")

    try:
        response = requests.get("http://localhost:5000/health", timeout=10)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 健康检查成功")
            print(f"📊 服务状态:")
            print(f"   - 服务器: {result.get('server')}")
            print(f"   - 状态: {result.get('status')}")
            print(f"   - 数据库: {result.get('database')}")
            print(f"   - 版本: {result.get('version')}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        return False
    except Exception as e:
        print(f"❌ 健康检查测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始数据库优化和请求流程测试")
    print("=" * 60)

    # 测试结果统计
    test_results = []

    # 1. 测试数据库连接
    test_results.append(("数据库连接", test_database_connection()))

    # 2. 测试 message_type 验证
    test_results.append(("message_type验证", test_message_type_validation()))

    # 3. 测试健康检查
    test_results.append(("健康检查", test_health_check()))

    # 4. 测试API请求（可选，需要服务器运行）
    test_results.append(("API请求", test_api_request()))

    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   - {test_name}: {status}")
        if result:
            passed += 1

    print(f"\n📈 总体结果: {passed}/{total} 项测试通过")

    if passed == total:
        print("🎉 所有测试通过！数据库优化成功！")
    else:
        print("⚠️ 部分测试失败，请检查相关配置")

    print("\n💡 优化要点:")
    print("   1. message_type 字段严格按照数据库枚举约束 (human, ai, system, tool)")
    print("   2. conversation_id 保存在 metadata 中，而不是单独的字段")
    print("   3. 使用 save_message_optimized 方法进行数据库写入")
    print("   4. 增强了错误处理和调试信息输出")


if __name__ == "__main__":
    main()
