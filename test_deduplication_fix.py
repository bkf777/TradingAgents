#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试消息去重修复的脚本
使用较小的时间范围和简化配置来快速验证修复效果
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_message_deduplication():
    """测试消息去重功能"""
    
    # 使用较小的时间范围和简化配置
    test_data = {
        "symbol": "AAPL",  # 使用AAPL，数据更稳定
        "date": "2025-01-10",  # 使用稍早的日期
        "conversation_id": f"dedup_test_{int(time.time())}",
        "config": {
            "analysisType": "basic",  # 基础分析，更快
            "includeRisk": False,     # 不包含风险分析
            "includeSentiment": False, # 不包含情感分析
            "researchDepth": "shallow", # 浅层研究
            "analysisPeriod": "1d"    # 只分析1天，最小时间范围
        }
    }
    
    print("🧪 测试消息去重修复")
    print("=" * 50)
    print(f"📊 测试股票: {test_data['symbol']}")
    print(f"📅 分析日期: {test_data['date']}")
    print(f"⏱️ 分析周期: {test_data['config']['analysisPeriod']}")
    print(f"🔍 研究深度: {test_data['config']['researchDepth']}")
    print(f"🆔 会话ID: {test_data['conversation_id']}")
    
    try:
        print("\n📡 发送分析请求...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:5000/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=180  # 3分钟超时，应该足够了
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"📈 响应状态码: {response.status_code}")
        print(f"⏱️ 请求耗时: {duration:.2f}秒")
        
        if response.status_code == 200:
            print("✅ 请求成功！")
            
            try:
                result = response.json()
                print("✅ JSON解析成功！")
                
                # 分析消息去重效果
                ai_messages = result.get('ai_messages', [])
                print(f"\n📊 消息分析结果:")
                print(f"  - 总消息数量: {len(ai_messages)}")
                
                if ai_messages:
                    # 按步骤分组统计
                    step_counts = {}
                    message_types = {}
                    content_hashes = set()
                    duplicate_contents = []
                    
                    for msg in ai_messages:
                        step_idx = msg.get('step_index', 'unknown')
                        msg_type = msg.get('type', 'unknown')
                        content = msg.get('content', '')
                        
                        # 统计每个步骤的消息数量
                        step_counts[step_idx] = step_counts.get(step_idx, 0) + 1
                        
                        # 统计消息类型
                        message_types[msg_type] = message_types.get(msg_type, 0) + 1
                        
                        # 检查内容重复
                        content_hash = hash(content)
                        if content_hash in content_hashes:
                            duplicate_contents.append(content[:100] + "...")
                        else:
                            content_hashes.add(content_hash)
                    
                    print(f"  - 步骤分布: {dict(sorted(step_counts.items()))}")
                    print(f"  - 消息类型分布: {message_types}")
                    print(f"  - 唯一内容数量: {len(content_hashes)}")
                    print(f"  - 重复内容数量: {len(duplicate_contents)}")
                    
                    if duplicate_contents:
                        print(f"  ⚠️ 发现重复内容:")
                        for i, dup in enumerate(duplicate_contents[:3], 1):  # 只显示前3个
                            print(f"    {i}. {dup}")
                        if len(duplicate_contents) > 3:
                            print(f"    ... 还有 {len(duplicate_contents) - 3} 个重复内容")
                    else:
                        print(f"  ✅ 没有发现重复内容！")
                    
                    # 显示前几条消息的详细信息
                    print(f"\n📝 前3条消息详情:")
                    for i, msg in enumerate(ai_messages[:3], 1):
                        print(f"  {i}. 步骤{msg.get('step_index', '?')}, 类型: {msg.get('type', '?')}")
                        print(f"     内容: {msg.get('content', '')[:80]}...")
                        print(f"     消息索引: {msg.get('message_index', '?')}")
                
                # 检查其他字段
                print(f"\n📋 其他信息:")
                print(f"  - symbol: {result.get('symbol')}")
                print(f"  - analysis_date: {result.get('analysis_date')}")
                print(f"  - success: {result.get('success')}")
                print(f"  - final_state类型: {type(result.get('final_state'))}")
                
                # 判断修复是否成功
                if len(duplicate_contents) == 0:
                    print(f"\n🎉 消息去重修复成功！没有发现重复消息。")
                    return True
                else:
                    print(f"\n⚠️ 仍然存在 {len(duplicate_contents)} 个重复消息，需要进一步优化。")
                    return False
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                print(f"📄 响应内容 (前300字符): {response.text[:300]}")
                return False
                
        else:
            print(f"❌ 请求失败: {response.status_code}")
            try:
                error_info = response.json()
                print(f"📄 错误信息: {error_info}")
            except:
                print(f"📄 原始错误: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时（3分钟）")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_health_first():
    """先测试健康检查"""
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API服务器运行正常")
            return True
        else:
            print(f"❌ API服务器异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接API服务器: {e}")
        return False

if __name__ == "__main__":
    print("🔧 消息去重修复测试")
    print("=" * 50)
    
    # 先检查服务器状态
    if not test_health_first():
        print("❌ 请先启动API服务器")
        exit(1)
    
    print("\n" + "=" * 50)
    
    # 执行主要测试
    success = test_message_deduplication()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 测试通过！消息去重功能正常工作。")
    else:
        print("❌ 测试未完全通过，可能需要进一步优化。")
