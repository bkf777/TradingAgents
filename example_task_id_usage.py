#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
task_id 参数使用示例
展示如何在 API 请求中使用 task_id 参数进行任务管理
"""

import requests
import json
import time
from datetime import datetime


def example_basic_usage():
    """基本使用示例：不提供 task_id，让系统自动生成"""
    print("📝 示例1：基本使用（自动生成 task_id）")
    print("-" * 50)
    
    data = {
        "symbol": "AAPL",
        "date": "2025-01-01"
    }
    
    try:
        response = requests.post(
            "http://localhost:5000/analyze",
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功")
            print(f"📊 返回信息:")
            print(f"   - 股票代码: {result.get('symbol')}")
            print(f"   - 分析日期: {result.get('analysis_date')}")
            print(f"   - 会话ID: {result.get('conversation_id')}")
            print(f"   - 任务ID: {result.get('task_id')}")  # 系统自动生成
            print(f"   - 成功状态: {result.get('success')}")
            return result.get('task_id')
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"❌ 错误信息: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器，请确保服务器正在运行")
        return None
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None


def example_custom_task_id():
    """自定义 task_id 示例"""
    print("\n📝 示例2：使用自定义 task_id")
    print("-" * 50)
    
    # 生成自定义的 task_id
    custom_task_id = f"user_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    data = {
        "symbol": "NVDA",
        "date": "2025-01-01",
        "task_id": custom_task_id,  # 自定义 task_id
        "conversation_id": f"conv_{datetime.now().strftime('%H%M%S')}"
    }
    
    print(f"🎯 使用自定义 task_id: {custom_task_id}")
    
    try:
        response = requests.post(
            "http://localhost:5000/analyze",
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功")
            print(f"📊 返回信息:")
            print(f"   - 股票代码: {result.get('symbol')}")
            print(f"   - 任务ID: {result.get('task_id')}")
            print(f"   - 会话ID: {result.get('conversation_id')}")
            
            # 验证返回的 task_id 是否与发送的一致
            if result.get('task_id') == custom_task_id:
                print(f"✅ task_id 匹配成功")
            else:
                print(f"❌ task_id 不匹配")
                print(f"   发送: {custom_task_id}")
                print(f"   返回: {result.get('task_id')}")
            
            return result.get('task_id')
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None


def example_batch_analysis():
    """批量分析示例：使用相同的 task_id 进行多次分析"""
    print("\n📝 示例3：批量分析（共享 task_id）")
    print("-" * 50)
    
    # 使用相同的 task_id 进行多个股票的分析
    batch_task_id = f"batch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    symbols = ["AAPL", "GOOGL", "MSFT"]
    
    print(f"🎯 批量任务ID: {batch_task_id}")
    print(f"📈 分析股票: {', '.join(symbols)}")
    
    results = []
    
    for i, symbol in enumerate(symbols):
        print(f"\n🔍 分析 {i+1}/{len(symbols)}: {symbol}")
        
        data = {
            "symbol": symbol,
            "date": "2025-01-01",
            "task_id": batch_task_id,  # 使用相同的 task_id
            "conversation_id": f"batch_conv_{datetime.now().strftime('%H%M%S')}"
        }
        
        try:
            response = requests.post(
                "http://localhost:5000/analyze",
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                results.append({
                    "symbol": symbol,
                    "task_id": result.get('task_id'),
                    "success": result.get('success'),
                    "ai_messages_count": len(result.get('ai_messages', []))
                })
                print(f"   ✅ {symbol} 分析完成")
            else:
                print(f"   ❌ {symbol} 分析失败: {response.status_code}")
                results.append({
                    "symbol": symbol,
                    "task_id": None,
                    "success": False,
                    "error": response.text
                })
                
        except Exception as e:
            print(f"   ❌ {symbol} 分析异常: {e}")
            results.append({
                "symbol": symbol,
                "task_id": None,
                "success": False,
                "error": str(e)
            })
        
        # 避免请求过于频繁
        if i < len(symbols) - 1:
            time.sleep(1)
    
    # 汇总结果
    print(f"\n📊 批量分析结果:")
    successful = 0
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['symbol']}: task_id={result.get('task_id', 'N/A')}")
        if result['success']:
            successful += 1
    
    print(f"\n📈 成功率: {successful}/{len(symbols)} ({successful/len(symbols)*100:.1f}%)")
    return batch_task_id


def example_task_tracking():
    """任务跟踪示例：展示如何通过 task_id 跟踪任务状态"""
    print("\n📝 示例4：任务跟踪")
    print("-" * 50)
    
    # 创建一个可跟踪的任务
    tracking_task_id = f"trackable_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"🎯 创建可跟踪任务: {tracking_task_id}")
    
    data = {
        "symbol": "TSLA",
        "date": "2025-01-01",
        "task_id": tracking_task_id,
        "conversation_id": f"track_conv_{datetime.now().strftime('%H%M%S')}"
    }
    
    try:
        # 发起分析请求
        print(f"🚀 发起分析请求...")
        response = requests.post(
            "http://localhost:5000/analyze",
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 分析请求成功")
            print(f"📊 任务信息:")
            print(f"   - 任务ID: {result.get('task_id')}")
            print(f"   - 股票代码: {result.get('symbol')}")
            print(f"   - 分析日期: {result.get('analysis_date')}")
            print(f"   - AI消息数量: {len(result.get('ai_messages', []))}")
            
            # 在实际应用中，这里可以：
            # 1. 将 task_id 保存到本地数据库
            # 2. 定期查询任务状态
            # 3. 通过 task_id 关联相关的后续操作
            
            print(f"\n💡 任务跟踪建议:")
            print(f"   1. 保存 task_id: {result.get('task_id')}")
            print(f"   2. 可通过数据库查询该任务的所有消息")
            print(f"   3. 可将多个相关操作关联到同一个 task_id")
            
            return result.get('task_id')
        else:
            print(f"❌ 分析请求失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None


def main():
    """主函数：运行所有示例"""
    print("🚀 task_id 参数使用示例")
    print("=" * 60)
    
    # 检查API服务器是否可用
    try:
        health_response = requests.get("http://localhost:5000/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ API服务器运行正常")
        else:
            print("⚠️ API服务器状态异常")
    except:
        print("❌ 无法连接到API服务器")
        print("💡 请先启动API服务器: python api_server_simple.py")
        return
    
    # 运行示例
    task_ids = []
    
    # 示例1：基本使用
    task_id1 = example_basic_usage()
    if task_id1:
        task_ids.append(task_id1)
    
    # 示例2：自定义 task_id
    task_id2 = example_custom_task_id()
    if task_id2:
        task_ids.append(task_id2)
    
    # 示例3：批量分析
    task_id3 = example_batch_analysis()
    if task_id3:
        task_ids.append(task_id3)
    
    # 示例4：任务跟踪
    task_id4 = example_task_tracking()
    if task_id4:
        task_ids.append(task_id4)
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 示例运行总结:")
    print(f"✅ 成功创建了 {len(task_ids)} 个任务")
    
    if task_ids:
        print(f"📝 任务ID列表:")
        for i, task_id in enumerate(task_ids, 1):
            print(f"   {i}. {task_id}")
        
        print(f"\n💡 后续可以通过这些 task_id 在数据库中查询相关消息:")
        print(f"   SELECT * FROM messages WHERE task_id IN ({', '.join(['%s'] * len(task_ids))});")
        print(f"   SELECT * FROM tasks WHERE task_id IN ({', '.join(['%s'] * len(task_ids))});")
    
    print(f"\n🎯 task_id 参数的主要优势:")
    print(f"   1. 任务管理：可以将多个相关操作关联到同一个任务")
    print(f"   2. 数据追踪：通过 task_id 可以查询任务的所有相关消息")
    print(f"   3. 批量处理：多个分析请求可以共享同一个 task_id")
    print(f"   4. 灵活性：支持自定义 task_id 或自动生成")
    print(f"   5. 兼容性：如果不提供 task_id，系统会自动生成")


if __name__ == "__main__":
    main()
