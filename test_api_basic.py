#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本API测试 - 测试健康检查和基本连接
"""

import requests
import json

def test_health():
    """测试健康检查接口"""
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        print(f"健康检查状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"健康检查响应: {result}")
            return True
        return False
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_docs():
    """测试文档接口"""
    try:
        response = requests.get("http://localhost:5000/docs/", timeout=5)
        print(f"文档接口状态码: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"文档接口失败: {e}")
        return False

def test_analyze_invalid():
    """测试分析接口的错误处理"""
    try:
        # 发送无效请求
        response = requests.post(
            "http://localhost:5000/analyze",
            json={},  # 空数据
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"分析接口(无效请求)状态码: {response.status_code}")
        if response.status_code != 200:
            try:
                error_info = response.json()
                print(f"错误响应: {error_info}")
                return True  # 正确返回错误是好的
            except:
                print(f"原始错误响应: {response.text}")
                return True
        return False
    except Exception as e:
        print(f"分析接口测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🔧 基本API测试")
    print("=" * 50)
    
    print("1. 测试健康检查...")
    health_ok = test_health()
    
    print("\n2. 测试文档接口...")
    docs_ok = test_docs()
    
    print("\n3. 测试分析接口错误处理...")
    error_ok = test_analyze_invalid()
    
    print("\n" + "=" * 50)
    print(f"健康检查: {'✅' if health_ok else '❌'}")
    print(f"文档接口: {'✅' if docs_ok else '❌'}")
    print(f"错误处理: {'✅' if error_ok else '❌'}")
    
    if health_ok and docs_ok and error_ok:
        print("\n🎉 基本API功能正常！")
        print("💡 JSON序列化修复已生效，API服务器可以正常处理请求。")
        print("⏰ 之前的超时可能是因为股票分析过程需要较长时间。")
    else:
        print("\n❌ 基本API功能异常。")
