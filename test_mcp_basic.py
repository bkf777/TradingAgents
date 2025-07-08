"""
基本 MCP 功能测试脚本
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from tradingagents.agents.utils.agent_utils import Toolkit
    print("✅ 成功导入 Toolkit")
except ImportError as e:
    print(f"❌ 导入 Toolkit 失败: {e}")
    sys.exit(1)

def test_mcp_config_creation():
    """测试 MCP 配置创建"""
    print("\n🔧 测试 MCP 配置创建...")
    
    try:
        # 测试 Tavily 配置
        tavily_config = Toolkit.get_tavily_mcp_config()
        print(f"✅ Tavily 配置创建成功: {list(tavily_config.keys())}")
        
        # 测试文件系统配置
        fs_config = Toolkit.get_filesystem_mcp_config()
        print(f"✅ 文件系统配置创建成功: {list(fs_config.keys())}")
        
        # 测试网络搜索配置
        web_config = Toolkit.get_web_search_mcp_config()
        print(f"✅ 网络搜索配置创建成功: {list(web_config.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ 配置创建失败: {e}")
        return False

def test_custom_tool_creation():
    """测试自定义工具创建"""
    print("\n🛠️ 测试自定义工具创建...")
    
    try:
        # 创建自定义 Tavily 搜索工具
        custom_tool = Toolkit.create_tavily_search_tool(
            tool_name="test_search_tool",
            search_template="Search for {query} in {domain}",
            description="测试搜索工具"
        )
        
        print(f"✅ 自定义 Tavily 工具创建成功: {getattr(custom_tool, 'name', 'unknown')}")

        # 创建完全自定义的工具
        custom_mcp_tool = Toolkit.create_custom_mcp_tool(
            tool_name="test_custom_tool",
            description="测试自定义 MCP 工具",
            server_configs=Toolkit.get_tavily_mcp_config(),
            query_template="Test query with {param1} and {param2}"
        )

        print(f"✅ 自定义 MCP 工具创建成功: {getattr(custom_mcp_tool, 'name', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ 自定义工具创建失败: {e}")
        return False

def test_predefined_tools():
    """测试预定义工具"""
    print("\n📊 测试预定义工具创建...")
    
    try:
        # 测试财报分析工具
        earnings_tool = Toolkit.get_earnings_analysis_tool()
        print(f"✅ 财报分析工具创建成功: {getattr(earnings_tool, 'name', 'unknown')}")

        # 测试监管新闻工具
        regulatory_tool = Toolkit.get_regulatory_news_tool()
        print(f"✅ 监管新闻工具创建成功: {getattr(regulatory_tool, 'name', 'unknown')}")

        # 测试并购工具
        ma_tool = Toolkit.get_merger_acquisition_tool()
        print(f"✅ 并购分析工具创建成功: {getattr(ma_tool, 'name', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ 预定义工具创建失败: {e}")
        return False

def test_tool_registration():
    """测试工具注册"""
    print("\n📝 测试工具注册...")
    
    try:
        # 获取所有 MCP 工具
        all_tools = Toolkit.get_all_mcp_tools()
        print(f"✅ 获取到 {len(all_tools)} 个 MCP 工具: {list(all_tools.keys())}")
        
        # 注册默认工具
        registered_tools = Toolkit.register_mcp_tools()
        print(f"✅ 注册了 {len(registered_tools)} 个工具")
        
        return True
    except Exception as e:
        print(f"❌ 工具注册失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能（不需要网络连接）"""
    print("\n⚙️ 测试基本功能...")
    
    try:
        # 测试工具方法是否存在
        methods_to_check = [
            'create_mcp_client',
            'create_mcp_agent', 
            'execute_mcp_query',
            'run_mcp_query_sync',
            'search_web_with_mcp',
            'get_financial_news_mcp',
            'analyze_market_sentiment_mcp',
            'get_competitor_analysis_mcp'
        ]
        
        for method_name in methods_to_check:
            if hasattr(Toolkit, method_name):
                print(f"✅ 方法 {method_name} 存在")
            else:
                print(f"❌ 方法 {method_name} 不存在")
                return False
        
        return True
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始 MCP 基本功能测试")
    print("=" * 50)
    
    tests = [
        test_mcp_config_creation,
        test_custom_tool_creation,
        test_predefined_tools,
        test_tool_registration,
        test_basic_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ 测试 {test_func.__name__} 失败")
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有基本测试通过！MCP 功能已成功集成到 Toolkit 类中。")
        print("\n📖 使用说明:")
        print("1. 查看 docs/MCP_USAGE.md 了解详细使用方法")
        print("2. 运行 examples/mcp_usage_example.py 查看完整示例")
        print("3. 设置环境变量 ENABLE_MCP_NETWORK_TESTS=1 来运行网络测试")
        return True
    else:
        print("❌ 部分测试失败，请检查错误信息")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
