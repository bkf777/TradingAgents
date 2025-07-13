#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的JSON序列化修复测试
使用已存在的task_id进行测试
"""

import requests
import json
import time

def test_with_task_id():
    """使用task_id测试分析API"""
    
    # 使用已存在的task_id
    task_id = "250a21f1-14d9-46e3-93af-91f9a49dac0b"
    
    test_data = {
        "task_id": task_id
    }
    
    print(f"🧪 测试JSON序列化修复 (使用task_id: {task_id})")
    
    try:
        print("📡 发送分析请求...")
        response = requests.post(
            "http://localhost:5000/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2分钟超时
        )
        
        print(f"📈 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 请求成功！")
            
            # 尝试解析JSON响应
            try:
                result = response.json()
                print("✅ JSON解析成功！修复有效！")
                
                # 显示基本信息
                print(f"  - success: {result.get('success')}")
                print(f"  - symbol: {result.get('symbol')}")
                print(f"  - ai_messages数量: {len(result.get('ai_messages', []))}")
                print(f"  - final_state类型: {type(result.get('final_state'))}")
                
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                print(f"📄 响应内容 (前200字符): {response.text[:200]}")
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
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

if __name__ == "__main__":
    print("🔧 简单JSON序列化修复测试")
    print("=" * 50)
    
    success = test_with_task_id()
    
    print("=" * 50)
    if success:
        print("🎉 测试通过！JSON序列化问题已修复。")
    else:
        print("❌ 测试失败。")
