#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试消息去重逻辑
模拟LangGraph的trace结构来验证我们的去重算法
"""

import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '.')

# 模拟LangChain消息对象
class MockMessage:
    def __init__(self, msg_type, content):
        self.type = msg_type
        self.content = content

def simulate_langgraph_trace():
    """模拟LangGraph的trace结构，展示消息累积的问题"""
    
    # 模拟LangGraph的trace，每个步骤包含累积的消息
    trace = [
        # 第1步：初始消息
        {
            "messages": [
                MockMessage("human", "分析AAPL股票"),
            ]
        },
        # 第2步：累积了前面的消息 + 新消息
        {
            "messages": [
                MockMessage("human", "分析AAPL股票"),  # 重复
                MockMessage("ai", "我来分析AAPL的市场数据..."),
            ]
        },
        # 第3步：累积了前面的消息 + 新消息
        {
            "messages": [
                MockMessage("human", "分析AAPL股票"),  # 重复
                MockMessage("ai", "我来分析AAPL的市场数据..."),  # 重复
                MockMessage("ai", "根据技术分析，AAPL显示出..."),
            ]
        },
        # 第4步：累积了前面的消息 + 新消息
        {
            "messages": [
                MockMessage("human", "分析AAPL股票"),  # 重复
                MockMessage("ai", "我来分析AAPL的市场数据..."),  # 重复
                MockMessage("ai", "根据技术分析，AAPL显示出..."),  # 重复
                MockMessage("ai", "综合考虑各项因素，建议..."),
            ]
        },
    ]
    
    return trace

def extract_messages_old_way(trace):
    """旧的提取方式（会产生重复）"""
    ai_messages = []
    
    for step_idx, step in enumerate(trace):
        if "messages" in step and step["messages"]:
            for msg_idx, msg in enumerate(step["messages"]):
                if hasattr(msg, "content") and hasattr(msg, "type"):
                    ai_messages.append(
                        {
                            "type": msg.type,
                            "content": str(msg.content),
                            "step_index": step_idx,
                            "message_index": msg_idx,
                        }
                    )
    
    return ai_messages

def extract_messages_new_way(trace):
    """新的提取方式（避免重复）"""
    ai_messages = []
    processed_messages = set()
    
    for step_idx, step in enumerate(trace):
        if "messages" in step and step["messages"]:
            current_messages = step["messages"]
            
            # 如果是第一步，所有消息都是新的
            if step_idx == 0:
                new_messages = current_messages
            else:
                # 获取上一步的消息数量
                prev_step = trace[step_idx - 1]
                prev_msg_count = len(prev_step.get("messages", []))
                # 只取新增的消息
                new_messages = current_messages[prev_msg_count:]
            
            # 处理新增的消息
            for msg_idx, msg in enumerate(new_messages):
                if hasattr(msg, "content") and hasattr(msg, "type"):
                    # 创建消息的唯一标识符
                    msg_id = f"{step_idx}_{len(current_messages) - len(new_messages) + msg_idx}_{hash(str(msg.content))}"
                    
                    if msg_id not in processed_messages:
                        processed_messages.add(msg_id)
                        ai_messages.append(
                            {
                                "type": msg.type,
                                "content": str(msg.content),
                                "step_index": step_idx,
                                "message_index": len(current_messages) - len(new_messages) + msg_idx,
                            }
                        )
    
    return ai_messages

def analyze_messages(messages, method_name):
    """分析消息列表，检查重复情况"""
    print(f"\n📊 {method_name} 结果分析:")
    print(f"  - 总消息数量: {len(messages)}")
    
    # 按内容分组，检查重复
    content_counts = {}
    for msg in messages:
        content = msg["content"]
        content_counts[content] = content_counts.get(content, 0) + 1
    
    # 统计重复情况
    unique_contents = len(content_counts)
    duplicate_contents = [content for content, count in content_counts.items() if count > 1]
    
    print(f"  - 唯一内容数量: {unique_contents}")
    print(f"  - 重复内容数量: {len(duplicate_contents)}")
    
    if duplicate_contents:
        print(f"  ⚠️ 重复的内容:")
        for content in duplicate_contents:
            count = content_counts[content]
            print(f"    - \"{content[:50]}...\" (出现{count}次)")
    else:
        print(f"  ✅ 没有重复内容")
    
    # 显示消息详情
    print(f"  📝 消息详情:")
    for i, msg in enumerate(messages, 1):
        print(f"    {i}. 步骤{msg['step_index']}, 索引{msg['message_index']}: [{msg['type']}] {msg['content'][:50]}...")
    
    return len(duplicate_contents) == 0

def test_deduplication_logic():
    """测试去重逻辑"""
    print("🧪 测试消息去重逻辑")
    print("=" * 60)
    
    # 生成模拟trace
    trace = simulate_langgraph_trace()
    print(f"📋 模拟trace结构 (共{len(trace)}个步骤):")
    for i, step in enumerate(trace):
        msg_count = len(step["messages"])
        print(f"  步骤{i}: {msg_count}条消息")
    
    # 测试旧方法
    print("\n" + "=" * 60)
    old_messages = extract_messages_old_way(trace)
    old_success = analyze_messages(old_messages, "旧方法（会产生重复）")
    
    # 测试新方法
    print("\n" + "=" * 60)
    new_messages = extract_messages_new_way(trace)
    new_success = analyze_messages(new_messages, "新方法（去重优化）")
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 对比总结:")
    print(f"  - 旧方法: {len(old_messages)}条消息, {'✅无重复' if old_success else '❌有重复'}")
    print(f"  - 新方法: {len(new_messages)}条消息, {'✅无重复' if new_success else '❌有重复'}")
    
    if new_success and not old_success:
        print("\n🎉 去重逻辑修复成功！新方法有效消除了重复消息。")
        return True
    elif new_success and old_success:
        print("\n🤔 两种方法都没有重复，可能测试用例不够复杂。")
        return True
    else:
        print("\n❌ 去重逻辑仍有问题，需要进一步优化。")
        return False

if __name__ == "__main__":
    success = test_deduplication_logic()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 去重逻辑测试通过！")
    else:
        print("❌ 去重逻辑测试失败。")
