#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API连接
检查OpenAI API连接是否正常
"""

import sys
import os
import requests
import ssl
import socket
from urllib.parse import urlparse

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_connectivity():
    """测试基本网络连接"""
    print("=" * 50)
    print("测试基本网络连接")
    print("=" * 50)
    
    test_urls = [
        "https://www.google.com",
        "https://api.openai.com",
        "https://api.nuwaapi.com"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            print(f"✅ {url}: {response.status_code}")
        except Exception as e:
            print(f"❌ {url}: {str(e)}")

def test_ssl_connection():
    """测试SSL连接"""
    print("\n" + "=" * 50)
    print("测试SSL连接")
    print("=" * 50)
    
    test_hosts = [
        ("api.openai.com", 443),
        ("api.nuwaapi.com", 443)
    ]
    
    for host, port in test_hosts:
        try:
            # 创建SSL上下文
            context = ssl.create_default_context()
            
            # 创建socket连接
            with socket.create_connection((host, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    print(f"✅ {host}:{port} SSL连接成功")
                    print(f"   SSL版本: {ssock.version()}")
                    print(f"   证书主题: {ssock.getpeercert()['subject']}")
        except Exception as e:
            print(f"❌ {host}:{port} SSL连接失败: {str(e)}")

def test_openai_api():
    """测试OpenAI API调用"""
    print("\n" + "=" * 50)
    print("测试OpenAI API调用")
    print("=" * 50)
    
    try:
        from openai import OpenAI
        
        # 使用您的配置
        client = OpenAI(
            api_key="sk-yOXwTRVHIub4m6WjEWin68sqvdYypExLyBbChOc38SX4PnpW",
            base_url="https://api.nuwaapi.com/v1"
        )
        
        print("尝试调用OpenAI API...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Hello, this is a test message."}
            ],
            max_tokens=50,
            timeout=30
        )
        
        print("✅ OpenAI API调用成功")
        print(f"响应: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ OpenAI API调用失败: {str(e)}")
        print(f"错误类型: {type(e).__name__}")

def test_with_different_settings():
    """测试不同的连接设置"""
    print("\n" + "=" * 50)
    print("测试不同的连接设置")
    print("=" * 50)
    
    try:
        from openai import OpenAI
        import httpx
        
        # 创建自定义HTTP客户端，增加超时和重试
        http_client = httpx.Client(
            timeout=60.0,  # 增加超时时间
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            verify=True  # 验证SSL证书
        )
        
        client = OpenAI(
            api_key="sk-yOXwTRVHIub4m6WjEWin68sqvdYypExLyBbChOc38SX4PnpW",
            base_url="https://api.nuwaapi.com/v1",
            http_client=http_client
        )
        
        print("使用自定义HTTP客户端测试...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "测试消息"}
            ],
            max_tokens=30
        )
        
        print("✅ 自定义设置API调用成功")
        print(f"响应: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ 自定义设置API调用失败: {str(e)}")

def test_alternative_endpoints():
    """测试备用端点"""
    print("\n" + "=" * 50)
    print("测试备用端点")
    print("=" * 50)
    
    endpoints = [
        "https://api.openai.com/v1",  # 官方端点
        "https://api.nuwaapi.com/v1",  # 您当前使用的端点
    ]
    
    for endpoint in endpoints:
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key="sk-yOXwTRVHIub4m6WjEWin68sqvdYypExLyBbChOc38SX4PnpW",
                base_url=endpoint
            )
            
            print(f"测试端点: {endpoint}")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "Hello"}
                ],
                max_tokens=20,
                timeout=30
            )
            
            print(f"✅ {endpoint} 调用成功")
            
        except Exception as e:
            print(f"❌ {endpoint} 调用失败: {str(e)}")

def main():
    """主测试函数"""
    print("开始API连接测试...")
    
    test_basic_connectivity()
    test_ssl_connection()
    test_openai_api()
    test_with_different_settings()
    test_alternative_endpoints()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
    
    print("\n建议的解决方案:")
    print("1. 如果SSL连接失败，可能是网络或防火墙问题")
    print("2. 如果API调用失败，可能是API密钥或端点问题")
    print("3. 可以尝试使用官方OpenAI端点: https://api.openai.com/v1")
    print("4. 检查是否需要配置代理设置")
    print("5. 确保API密钥有效且有足够的配额")

if __name__ == "__main__":
    main()
