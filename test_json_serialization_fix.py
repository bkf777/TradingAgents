#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试JSON序列化修复的脚本
用于验证API服务器是否能正确处理包含LangChain消息对象的响应
"""

import requests
import json
import time
from datetime import datetime

def test_analyze_api():
    """测试分析API接口"""
    
    # API服务器地址
    base_url = "http://localhost:5000"
    
    # 测试数据
    test_data = {
        "symbol": "688111",  # 金山办公
        "date": "2025-01-13",
        "conversation_id": f"test_fix_{int(time.time())}",
        "config": {
            "analysisType": "comprehensive",
            "includeRisk": True,
            "includeSentiment": True,
            "researchDepth": "shallow",
            "analysisPeriod": "1w"
        }
    }
    
    print("🧪 开始测试JSON序列化修复...")
    print(f"📊 测试股票: {test_data['symbol']}")
    print(f"📅 分析日期: {test_data['date']}")
    print(f"🆔 会话ID: {test_data['conversation_id']}")
    
    try:
        # 发送请求
        print("\n📡 发送分析请求...")
        response = requests.post(
            f"{base_url}/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5分钟超时
        )
        
        print(f"📈 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 请求成功！")
            
            # 尝试解析JSON响应
            try:
                result = response.json()
                print("✅ JSON解析成功！")
                
                # 检查响应结构
                print("\n📋 响应结构检查:")
                print(f"  - success: {result.get('success', 'N/A')}")
                print(f"  - symbol: {result.get('symbol', 'N/A')}")
                print(f"  - analysis_date: {result.get('analysis_date', 'N/A')}")
                print(f"  - conversation_id: {result.get('conversation_id', 'N/A')}")
                print(f"  - ai_messages数量: {len(result.get('ai_messages', []))}")
                print(f"  - final_state类型: {type(result.get('final_state', {}))}")
                print(f"  - timestamp: {result.get('timestamp', 'N/A')}")
                
                # 检查final_state是否包含可序列化的数据
                final_state = result.get('final_state', {})
                if final_state:
                    print(f"  - final_state键数量: {len(final_state.keys()) if isinstance(final_state, dict) else 'N/A'}")
                    if isinstance(final_state, dict):
                        print(f"  - final_state键: {list(final_state.keys())[:5]}...")  # 只显示前5个键
                
                # 检查ai_messages结构
                ai_messages = result.get('ai_messages', [])
                if ai_messages:
                    print(f"\n📝 AI消息示例 (第1条):")
                    first_msg = ai_messages[0]
                    print(f"  - type: {first_msg.get('type', 'N/A')}")
                    print(f"  - content长度: {len(str(first_msg.get('content', '')))}")
                    print(f"  - timestamp: {first_msg.get('timestamp', 'N/A')}")
                
                print("\n🎉 JSON序列化修复测试成功！")
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                print(f"📄 原始响应内容 (前500字符): {response.text[:500]}")
                return False
                
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"📄 错误响应: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保API服务器正在运行")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

def test_health_check():
    """测试健康检查接口"""
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 健康检查通过")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

if __name__ == "__main__":
    print("🔧 JSON序列化修复测试")
    print("=" * 50)
    
    # 首先检查服务器是否运行
    print("🏥 检查API服务器状态...")
    if not test_health_check():
        print("❌ API服务器未运行，请先启动服务器")
        exit(1)
    
    print("\n" + "=" * 50)
    
    # 执行主要测试
    success = test_analyze_api()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 所有测试通过！JSON序列化问题已修复。")
    else:
        print("❌ 测试失败，需要进一步调试。")
