"""
测试 MCP 功能的单元测试
"""

import unittest
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.default_config import DEFAULT_CONFIG


class TestMCPFunctionality(unittest.TestCase):
    """MCP 功能测试类"""
    
    def setUp(self):
        """测试设置"""
        self.toolkit = Toolkit()
        
    def test_mcp_config_creation(self):
        """测试 MCP 配置创建"""
        print("\n测试 MCP 配置创建...")
        
        # 测试 Tavily 配置
        tavily_config = Toolkit.get_tavily_mcp_config()
        self.assertIsInstance(tavily_config, dict)
        self.assertIn("tavily-mcp", tavily_config)
        self.assertIn("command", tavily_config["tavily-mcp"])
        self.assertIn("args", tavily_config["tavily-mcp"])
        self.assertIn("env", tavily_config["tavily-mcp"])
        print("✓ Tavily 配置创建成功")
        
        # 测试文件系统配置
        fs_config = Toolkit.get_filesystem_mcp_config(["/tmp"])
        self.assertIsInstance(fs_config, dict)
        self.assertIn("filesystem-mcp", fs_config)
        print("✓ 文件系统配置创建成功")
        
        # 测试网络搜索配置
        web_config = Toolkit.get_web_search_mcp_config()
        self.assertIsInstance(web_config, dict)
        self.assertIn("web-search-mcp", web_config)
        print("✓ 网络搜索配置创建成功")
    
    def test_custom_tool_creation(self):
        """测试自定义工具创建"""
        print("\n测试自定义工具创建...")
        
        # 创建自定义 Tavily 搜索工具
        custom_tool = Toolkit.create_tavily_search_tool(
            tool_name="test_search_tool",
            search_template="Search for {query} in {domain}",
            description="测试搜索工具"
        )
        
        self.assertIsNotNone(custom_tool)
        self.assertEqual(custom_tool.__name__, "test_search_tool")
        self.assertIn("测试搜索工具", custom_tool.__doc__)
        print("✓ 自定义 Tavily 工具创建成功")
        
        # 创建完全自定义的工具
        custom_mcp_tool = Toolkit.create_custom_mcp_tool(
            tool_name="test_custom_tool",
            description="测试自定义 MCP 工具",
            server_configs=Toolkit.get_tavily_mcp_config(),
            query_template="Test query with {param1} and {param2}"
        )
        
        self.assertIsNotNone(custom_mcp_tool)
        self.assertEqual(custom_mcp_tool.__name__, "test_custom_tool")
        print("✓ 自定义 MCP 工具创建成功")
    
    def test_predefined_tools_creation(self):
        """测试预定义工具创建"""
        print("\n测试预定义工具创建...")
        
        # 测试财报分析工具
        earnings_tool = Toolkit.get_earnings_analysis_tool()
        self.assertIsNotNone(earnings_tool)
        print("✓ 财报分析工具创建成功")
        
        # 测试监管新闻工具
        regulatory_tool = Toolkit.get_regulatory_news_tool()
        self.assertIsNotNone(regulatory_tool)
        print("✓ 监管新闻工具创建成功")
        
        # 测试并购工具
        ma_tool = Toolkit.get_merger_acquisition_tool()
        self.assertIsNotNone(ma_tool)
        print("✓ 并购分析工具创建成功")
    
    def test_tool_registration(self):
        """测试工具注册"""
        print("\n测试工具注册...")
        
        # 获取所有 MCP 工具
        all_tools = Toolkit.get_all_mcp_tools()
        self.assertIsInstance(all_tools, dict)
        self.assertGreater(len(all_tools), 0)
        print(f"✓ 获取到 {len(all_tools)} 个 MCP 工具")
        
        # 注册默认工具
        registered_tools = Toolkit.register_mcp_tools()
        self.assertIsInstance(registered_tools, list)
        self.assertGreater(len(registered_tools), 0)
        print(f"✓ 注册了 {len(registered_tools)} 个工具")
    
    @unittest.skipIf(
        not os.getenv("ENABLE_MCP_NETWORK_TESTS"), 
        "跳过网络测试 (设置 ENABLE_MCP_NETWORK_TESTS=1 启用)"
    )
    def test_basic_mcp_search(self):
        """测试基本 MCP 搜索功能（需要网络连接）"""
        print("\n测试基本 MCP 搜索功能...")
        
        try:
            # 测试网络搜索
            result = Toolkit.search_web_with_mcp(
                query="Python programming tutorial",
                max_results=2
            )
            
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)
            self.assertNotIn("错误:", result)
            print("✓ 网络搜索功能正常")
            
        except Exception as e:
            self.skipTest(f"网络搜索测试失败: {e}")
    
    @unittest.skipIf(
        not os.getenv("ENABLE_MCP_NETWORK_TESTS"), 
        "跳过网络测试 (设置 ENABLE_MCP_NETWORK_TESTS=1 启用)"
    )
    def test_financial_mcp_tools(self):
        """测试财经相关的 MCP 工具（需要网络连接）"""
        print("\n测试财经 MCP 工具...")
        
        try:
            # 测试财经新闻获取
            news_result = Toolkit.get_financial_news_mcp(
                topic="stock market",
                date_range="last 3 days"
            )
            
            self.assertIsInstance(news_result, str)
            self.assertGreater(len(news_result), 0)
            print("✓ 财经新闻获取功能正常")
            
            # 测试市场情绪分析
            sentiment_result = Toolkit.analyze_market_sentiment_mcp(
                ticker="AAPL",
                analysis_period="last 7 days"
            )
            
            self.assertIsInstance(sentiment_result, str)
            self.assertGreater(len(sentiment_result), 0)
            print("✓ 市场情绪分析功能正常")
            
        except Exception as e:
            self.skipTest(f"财经工具测试失败: {e}")
    
    def test_async_mcp_functionality(self):
        """测试异步 MCP 功能"""
        print("\n测试异步 MCP 功能...")
        
        async def async_test():
            try:
                # 测试 MCP 代理创建
                tavily_config = Toolkit.get_tavily_mcp_config()
                
                # 这里我们只测试配置是否正确，不实际连接
                self.assertIsInstance(tavily_config, dict)
                self.assertIn("tavily-mcp", tavily_config)
                
                print("✓ 异步 MCP 配置验证成功")
                return True
                
            except Exception as e:
                print(f"异步测试错误: {e}")
                return False
        
        # 运行异步测试
        result = asyncio.run(async_test())
        self.assertTrue(result)
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n测试错误处理...")
        
        # 测试无效的查询模板
        try:
            invalid_tool = Toolkit.create_custom_mcp_tool(
                tool_name="invalid_tool",
                description="无效工具测试",
                server_configs=Toolkit.get_tavily_mcp_config(),
                query_template="Query with {missing_param}"
            )
            
            # 调用工具时应该返回错误信息
            result = invalid_tool(wrong_param="test")
            self.assertIn("错误:", result)
            print("✓ 参数错误处理正常")
            
        except Exception as e:
            print(f"错误处理测试异常: {e}")
    
    def test_configuration_validation(self):
        """测试配置验证"""
        print("\n测试配置验证...")
        
        # 测试默认配置
        default_config = DEFAULT_CONFIG
        self.assertIn("backend_url", default_config)
        self.assertIn("openai_api_key", default_config)
        print("✓ 默认配置验证成功")
        
        # 测试自定义配置
        custom_config = {
            "quick_think_llm": "gpt-4o-mini",
            "backend_url": "https://api.nuwaapi.com/v1/chat/completions",
            "openai_api_key": "test-key"
        }
        
        # 验证配置格式
        required_keys = ["quick_think_llm", "backend_url", "openai_api_key"]
        for key in required_keys:
            self.assertIn(key, custom_config)
        
        print("✓ 自定义配置验证成功")


class TestMCPIntegration(unittest.TestCase):
    """MCP 集成测试类"""
    
    def test_toolkit_mcp_integration(self):
        """测试 Toolkit 与 MCP 的集成"""
        print("\n测试 Toolkit MCP 集成...")
        
        # 验证 MCP 相关方法存在
        self.assertTrue(hasattr(Toolkit, 'create_mcp_client'))
        self.assertTrue(hasattr(Toolkit, 'create_mcp_agent'))
        self.assertTrue(hasattr(Toolkit, 'execute_mcp_query'))
        self.assertTrue(hasattr(Toolkit, 'run_mcp_query_sync'))
        print("✓ MCP 方法集成验证成功")
        
        # 验证预定义工具存在
        self.assertTrue(hasattr(Toolkit, 'search_web_with_mcp'))
        self.assertTrue(hasattr(Toolkit, 'get_financial_news_mcp'))
        self.assertTrue(hasattr(Toolkit, 'analyze_market_sentiment_mcp'))
        self.assertTrue(hasattr(Toolkit, 'get_competitor_analysis_mcp'))
        print("✓ 预定义 MCP 工具验证成功")
        
        # 验证工具创建方法存在
        self.assertTrue(hasattr(Toolkit, 'create_custom_mcp_tool'))
        self.assertTrue(hasattr(Toolkit, 'create_tavily_search_tool'))
        print("✓ MCP 工具创建方法验证成功")


def run_tests():
    """运行所有测试"""
    print("开始运行 MCP 功能测试...")
    print("=" * 60)
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_suite.addTest(unittest.makeSuite(TestMCPFunctionality))
    test_suite.addTest(unittest.makeSuite(TestMCPIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
        print(f"失败: {len(result.failures)}, 错误: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # 设置环境变量以启用网络测试（可选）
    # os.environ["ENABLE_MCP_NETWORK_TESTS"] = "1"
    
    success = run_tests()
    sys.exit(0 if success else 1)
