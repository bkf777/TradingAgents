#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试make_json_serializable函数
模拟包含LangChain消息对象的数据结构
"""

import json
import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '.')

# 导入我们的序列化函数
from api_server_simple import make_json_serializable

# 模拟LangChain消息对象
class MockHumanMessage:
    def __init__(self, content):
        self.type = "human"
        self.content = content

class MockAIMessage:
    def __init__(self, content):
        self.type = "ai"
        self.content = content

def test_serialization():
    """测试序列化函数"""
    
    print("🧪 测试make_json_serializable函数")
    print("=" * 50)
    
    # 创建包含LangChain消息对象的测试数据
    test_data = {
        "symbol": "688111",
        "analysis_date": "2025-01-13",
        "messages": [
            MockHumanMessage("分析688111股票"),
            MockAIMessage("好的，我来分析688111股票的情况..."),
        ],
        "final_state": {
            "messages": [
                MockHumanMessage("请提供投资建议"),
                MockAIMessage("基于分析，建议..."),
            ],
            "decision": "买入",
            "confidence": 0.8,
            "timestamp": datetime.now()
        },
        "nested_data": {
            "level1": {
                "level2": {
                    "message": MockAIMessage("嵌套消息测试")
                }
            }
        }
    }
    
    print("📋 原始数据结构:")
    print(f"  - messages数量: {len(test_data['messages'])}")
    print(f"  - final_state.messages数量: {len(test_data['final_state']['messages'])}")
    print(f"  - 嵌套消息类型: {type(test_data['nested_data']['level1']['level2']['message'])}")
    
    try:
        # 使用我们的序列化函数
        print("\n🔄 执行序列化...")
        serialized_data = make_json_serializable(test_data)
        
        print("✅ 序列化成功！")
        
        # 尝试JSON序列化
        print("\n🔄 执行JSON序列化...")
        json_string = json.dumps(serialized_data, indent=2, ensure_ascii=False)
        
        print("✅ JSON序列化成功！")
        
        # 验证反序列化
        print("\n🔄 执行JSON反序列化...")
        parsed_data = json.loads(json_string)
        
        print("✅ JSON反序列化成功！")
        
        # 检查序列化后的数据结构
        print("\n📋 序列化后的数据结构:")
        print(f"  - messages数量: {len(parsed_data['messages'])}")
        print(f"  - 第一条消息类型: {parsed_data['messages'][0]['type']}")
        print(f"  - 第一条消息内容: {parsed_data['messages'][0]['content'][:50]}...")
        print(f"  - final_state.messages数量: {len(parsed_data['final_state']['messages'])}")
        print(f"  - 嵌套消息类型: {parsed_data['nested_data']['level1']['level2']['message']['type']}")
        
        # 显示JSON字符串的一部分
        print(f"\n📄 JSON字符串 (前300字符):")
        print(json_string[:300] + "...")
        
        print("\n🎉 所有测试通过！make_json_serializable函数工作正常。")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"📄 错误详情: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_serialization()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 序列化函数测试通过！JSON序列化问题已修复。")
    else:
        print("❌ 序列化函数测试失败。")
