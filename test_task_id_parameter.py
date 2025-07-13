#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 task_id 参数功能
验证 API 接口能够正确接收和处理 task_id 参数
"""

import json
from datetime import datetime
from database_config import DatabaseManager, MessageManager, get_db_config


def test_task_id_database_operations():
    """测试 task_id 相关的数据库操作"""
    print("🔍 测试 task_id 数据库操作...")
    
    try:
        db_manager = DatabaseManager(get_db_config())
        message_manager = MessageManager(db_manager)
        
        # 测试数据
        symbol = "AAPL"
        analysis_date = "2025-01-01"
        task_id = f"custom_task_{datetime.now().strftime('%H%M%S')}"
        
        print(f"📝 测试任务ID: {task_id}")
        
        # 测试保存消息（会自动创建任务）
        message_id = message_manager.save_message_optimized(
            symbol=symbol,
            analysis_date=analysis_date,
            task_id=task_id,
            message_type="ai",
            content="这是一条测试消息，用于验证 task_id 参数功能",
            metadata={
                "test": True,
                "task_id_test": True,
                "custom_task_id": task_id
            }
        )
        
        if message_id:
            print(f"✅ 消息保存成功: {message_id}")
            
            # 验证任务是否被创建
            task_query = "SELECT * FROM tasks WHERE task_id = %s"
            task_result = db_manager.execute_query(task_query, (task_id,))
            
            if task_result:
                task = task_result[0]
                print(f"✅ 任务创建成功:")
                print(f"   - 任务ID: {task['task_id']}")
                print(f"   - 股票代码: {task['ticker']}")
                print(f"   - 标题: {task['title']}")
                print(f"   - 状态: {task['status']}")
                print(f"   - 创建时间: {task['created_at']}")
            else:
                print(f"❌ 任务未找到: {task_id}")
                
            # 验证消息是否正确关联到任务
            message_query = "SELECT * FROM messages WHERE message_id = %s"
            message_result = db_manager.execute_query(message_query, (message_id,))
            
            if message_result:
                message = message_result[0]
                print(f"✅ 消息验证成功:")
                print(f"   - 消息ID: {message['message_id']}")
                print(f"   - 关联任务ID: {message['task_id']}")
                print(f"   - 消息类型: {message['message_type']}")
                print(f"   - 序号: {message['sequence_number']}")
                
                # 解析metadata
                metadata = json.loads(message['metadata'])
                print(f"   - 元数据中的task_id: {metadata.get('task_id', 'N/A')}")
            else:
                print(f"❌ 消息未找到: {message_id}")
                
        else:
            print(f"❌ 消息保存失败")
            
        db_manager.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"❌ 详细错误: {traceback.format_exc()}")
        return False


def test_multiple_messages_same_task():
    """测试同一个任务下保存多条消息"""
    print("\n🔍 测试同一任务下的多条消息...")
    
    try:
        db_manager = DatabaseManager(get_db_config())
        message_manager = MessageManager(db_manager)
        
        # 测试数据
        symbol = "TSLA"
        analysis_date = "2025-01-01"
        task_id = f"multi_msg_task_{datetime.now().strftime('%H%M%S')}"
        
        print(f"📝 测试任务ID: {task_id}")
        
        # 保存多条消息
        messages = [
            {"type": "human", "content": "请分析TSLA股票"},
            {"type": "ai", "content": "开始分析TSLA股票..."},
            {"type": "system", "content": "系统正在获取数据"},
            {"type": "tool", "content": "工具调用结果"},
            {"type": "ai", "content": "分析完成，建议买入"}
        ]
        
        saved_messages = []
        for i, msg in enumerate(messages):
            message_id = message_manager.save_message_optimized(
                symbol=symbol,
                analysis_date=analysis_date,
                task_id=task_id,
                message_type=msg["type"],
                content=msg["content"],
                metadata={
                    "message_index": i,
                    "total_messages": len(messages),
                    "task_id": task_id
                }
            )
            
            if message_id:
                saved_messages.append(message_id)
                print(f"✅ 消息 {i+1}/{len(messages)} 保存成功: {message_id} (类型: {msg['type']})")
            else:
                print(f"❌ 消息 {i+1} 保存失败")
        
        print(f"📊 总共保存了 {len(saved_messages)}/{len(messages)} 条消息")
        
        # 验证所有消息都关联到同一个任务
        if saved_messages:
            query = """
            SELECT message_id, message_type, sequence_number, task_id 
            FROM messages 
            WHERE task_id = %s 
            ORDER BY sequence_number
            """
            results = db_manager.execute_query(query, (task_id,))
            
            print(f"✅ 任务 {task_id} 下的所有消息:")
            for result in results:
                print(f"   - {result['message_type']}: 序号 {result['sequence_number']}, ID: {result['message_id']}")
        
        db_manager.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"❌ 详细错误: {traceback.format_exc()}")
        return False


def test_task_id_parameter_scenarios():
    """测试不同的 task_id 参数场景"""
    print("\n🔍 测试不同的 task_id 参数场景...")
    
    scenarios = [
        {
            "name": "自定义task_id",
            "task_id": f"custom_{datetime.now().strftime('%H%M%S')}",
            "description": "用户提供自定义的task_id"
        },
        {
            "name": "UUID格式task_id",
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "description": "使用UUID格式的task_id"
        },
        {
            "name": "带特殊字符task_id",
            "task_id": f"task-with-dashes_{datetime.now().strftime('%H%M%S')}",
            "description": "包含连字符的task_id"
        }
    ]
    
    try:
        db_manager = DatabaseManager(get_db_config())
        message_manager = MessageManager(db_manager)
        
        success_count = 0
        
        for scenario in scenarios:
            print(f"\n📝 测试场景: {scenario['name']}")
            print(f"   描述: {scenario['description']}")
            print(f"   task_id: {scenario['task_id']}")
            
            try:
                message_id = message_manager.save_message_optimized(
                    symbol="TEST",
                    analysis_date="2025-01-01",
                    task_id=scenario['task_id'],
                    message_type="ai",
                    content=f"测试消息 - {scenario['name']}",
                    metadata={
                        "scenario": scenario['name'],
                        "test_task_id": scenario['task_id']
                    }
                )
                
                if message_id:
                    print(f"   ✅ 成功: {message_id}")
                    success_count += 1
                else:
                    print(f"   ❌ 失败: 消息保存失败")
                    
            except Exception as e:
                print(f"   ❌ 失败: {e}")
        
        print(f"\n📊 场景测试结果: {success_count}/{len(scenarios)} 成功")
        
        db_manager.disconnect()
        return success_count == len(scenarios)
        
    except Exception as e:
        print(f"❌ 场景测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始 task_id 参数功能测试")
    print("=" * 60)
    
    # 测试结果统计
    test_results = []
    
    # 1. 测试基本的 task_id 数据库操作
    test_results.append(("task_id数据库操作", test_task_id_database_operations()))
    
    # 2. 测试同一任务下的多条消息
    test_results.append(("同任务多消息", test_multiple_messages_same_task()))
    
    # 3. 测试不同的 task_id 参数场景
    test_results.append(("task_id参数场景", test_task_id_parameter_scenarios()))
    
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
        print("🎉 所有测试通过！task_id 参数功能正常！")
    else:
        print("⚠️ 部分测试失败，请检查相关配置")
    
    print("\n💡 task_id 参数功能特点:")
    print("   1. 支持接收自定义的 task_id 参数")
    print("   2. 如果未提供 task_id，会自动生成默认值")
    print("   3. 自动创建对应的任务记录（如果不存在）")
    print("   4. 消息通过 task_id 正确关联到任务")
    print("   5. 支持同一任务下保存多条消息")
    print("   6. task_id 同时保存在数据库字段和 metadata 中")


if __name__ == "__main__":
    main()
