#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真实的analyze API接口调用
验证从数据库获取task数据并进行实际分析的完整流程
"""

import requests
import json
import sys
import os
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入数据库相关模块
try:
    from database_config import DatabaseManager, get_db_config
    print("✅ 成功导入数据库模块")
except ImportError as e:
    print(f"❌ 导入数据库模块失败: {e}")
    sys.exit(1)

# API配置
API_BASE_URL = "http://localhost:5000"
ANALYZE_ENDPOINT = f"{API_BASE_URL}/analyze"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"


def check_api_server():
    """检查API服务器是否运行"""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ API服务器运行正常")
            print(f"   - 服务器: {health_data.get('server', 'Unknown')}")
            print(f"   - 状态: {health_data.get('status', 'Unknown')}")
            print(f"   - 数据库: {health_data.get('database', 'Unknown')}")
            return True
        else:
            print(f"❌ API服务器响应异常: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到API服务器: {e}")
        print(f"请确保API服务器在 {API_BASE_URL} 运行")
        return False


def test_analyze_with_task_id():
    """测试使用task_id进行分析"""
    print("\n" + "="*60)
    print("🧪 测试使用task_id进行真实分析")
    print("="*60)
    
    try:
        # 连接数据库获取一个有效的task_id
        db_manager = DatabaseManager(get_db_config())
        
        query = "SELECT * FROM tasks WHERE status = 'pending' LIMIT 1"
        tasks = db_manager.execute_query(query)
        
        if not tasks:
            print("❌ 数据库中没有pending状态的task数据")
            # 尝试获取任意task
            query = "SELECT * FROM tasks LIMIT 1"
            tasks = db_manager.execute_query(query)
            
            if not tasks:
                print("❌ 数据库中没有任何task数据")
                db_manager.disconnect()
                return False
        
        task = tasks[0]
        task_id = task['task_id']
        
        print(f"📋 使用task进行分析:")
        print(f"   - task_id: {task_id}")
        print(f"   - ticker: {task['ticker']}")
        print(f"   - title: {task['title']}")
        print(f"   - status: {task['status']}")
        print(f"   - analysis_period: {task['analysis_period']}")
        
        # 准备请求数据
        request_data = {
            "task_id": task_id,
            "date": "2025-01-15",  # 提供一个具体的分析日期
            "conversation_id": f"test_real_api_{int(time.time())}",
            "config": {
                "max_debate_rounds": 1,  # 减少轮次以加快测试
                "online_tools": False,   # 使用离线模式
                "quick_think_llm": "o3-mini-high",
                "deep_think_llm": "o3-mini-high"
            }
        }
        
        print(f"\n📤 发送分析请求...")
        print(f"请求数据: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
        
        # 发送请求
        start_time = time.time()
        response = requests.post(
            ANALYZE_ENDPOINT, 
            json=request_data,
            timeout=300  # 5分钟超时
        )
        end_time = time.time()
        
        print(f"\n📥 收到响应 (耗时: {end_time - start_time:.2f}秒)")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ 分析成功完成!")
            print(f"   - symbol: {result.get('symbol')}")
            print(f"   - analysis_date: {result.get('analysis_date')}")
            print(f"   - task_id: {result.get('task_id')}")
            print(f"   - conversation_id: {result.get('conversation_id')}")
            print(f"   - AI消息数量: {len(result.get('ai_messages', []))}")
            
            # 显示决策结果
            decision = result.get('decision')
            if decision:
                print(f"   - 投资决策: {decision}")
            
            # 显示task数据信息
            task_data = result.get('task_data')
            if task_data:
                print(f"   - 使用的task数据:")
                print(f"     * ticker: {task_data.get('ticker')}")
                print(f"     * title: {task_data.get('title')}")
                print(f"     * research_depth: {task_data.get('research_depth')}")
                print(f"     * analysis_period: {task_data.get('analysis_period')}")
            
            # 验证数据库中是否保存了消息
            print(f"\n🔍 验证数据库中的消息保存...")
            message_query = """
            SELECT COUNT(*) as message_count 
            FROM messages 
            WHERE task_id = %s
            """
            message_result = db_manager.execute_query(message_query, (task_id,))
            if message_result:
                message_count = message_result[0]['message_count']
                print(f"✅ 数据库中保存了 {message_count} 条消息")
            
            db_manager.disconnect()
            return True
            
        else:
            print(f"❌ 分析失败")
            try:
                error_data = response.json()
                print(f"错误信息: {error_data.get('message', '未知错误')}")
            except:
                print(f"响应内容: {response.text}")
            
            db_manager.disconnect()
            return False
        
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"❌ 详细错误: {traceback.format_exc()}")
        return False


def test_analyze_with_direct_params():
    """测试使用直接参数进行分析"""
    print("\n" + "="*60)
    print("🧪 测试使用直接参数进行分析")
    print("="*60)
    
    try:
        # 准备请求数据
        request_data = {
            "symbol": "AAPL",
            "date": "2025-01-15",
            "conversation_id": f"test_direct_api_{int(time.time())}",
            "config": {
                "max_debate_rounds": 1,  # 减少轮次以加快测试
                "online_tools": False,   # 使用离线模式
                "quick_think_llm": "o3-mini-high",
                "deep_think_llm": "o3-mini-high"
            }
        }
        
        print(f"📤 发送分析请求...")
        print(f"请求数据: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
        
        # 发送请求
        start_time = time.time()
        response = requests.post(
            ANALYZE_ENDPOINT, 
            json=request_data,
            timeout=300  # 5分钟超时
        )
        end_time = time.time()
        
        print(f"\n📥 收到响应 (耗时: {end_time - start_time:.2f}秒)")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ 分析成功完成!")
            print(f"   - symbol: {result.get('symbol')}")
            print(f"   - analysis_date: {result.get('analysis_date')}")
            print(f"   - task_id: {result.get('task_id')}")
            print(f"   - conversation_id: {result.get('conversation_id')}")
            print(f"   - AI消息数量: {len(result.get('ai_messages', []))}")
            
            # 显示决策结果
            decision = result.get('decision')
            if decision:
                print(f"   - 投资决策: {decision}")
            
            return True
            
        else:
            print(f"❌ 分析失败")
            try:
                error_data = response.json()
                print(f"错误信息: {error_data.get('message', '未知错误')}")
            except:
                print(f"响应内容: {response.text}")
            
            return False
        
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试真实的analyze API接口...")
    
    # 检查API服务器
    if not check_api_server():
        print("❌ API服务器未运行，无法进行测试")
        return
    
    print(f"\n⚠️ 注意: 这将进行真实的股票分析，可能需要几分钟时间")
    print(f"如果您只想测试参数处理逻辑，请运行 test_analyze_api_modes.py")
    
    # 询问用户是否继续
    try:
        user_input = input("\n是否继续进行真实分析测试? (y/N): ").strip().lower()
        if user_input not in ['y', 'yes']:
            print("测试已取消")
            return
    except KeyboardInterrupt:
        print("\n测试已取消")
        return
    
    # 运行测试
    print(f"\n开始测试...")
    
    # 测试task_id模式
    test1_result = test_analyze_with_task_id()
    
    # 如果第一个测试成功，询问是否继续第二个测试
    if test1_result:
        try:
            user_input = input("\n第一个测试成功，是否继续测试直接参数模式? (y/N): ").strip().lower()
            if user_input in ['y', 'yes']:
                test2_result = test_analyze_with_direct_params()
            else:
                test2_result = None
        except KeyboardInterrupt:
            print("\n测试已取消")
            test2_result = None
    else:
        test2_result = None
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    print(f"task_id模式测试: {'✅ 通过' if test1_result else '❌ 失败'}")
    if test2_result is not None:
        print(f"直接参数模式测试: {'✅ 通过' if test2_result else '❌ 失败'}")
    else:
        print(f"直接参数模式测试: ⏭️ 跳过")
    
    if test1_result:
        print(f"\n🎉 task参数格式化功能正常工作！")
        print(f"✅ 可以从数据库获取task数据并正确传递给TradingAgentsGraph进行分析")
    else:
        print(f"\n⚠️ 测试失败，请检查相关功能")


if __name__ == "__main__":
    main()
