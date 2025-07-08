"""
MCP (Model Context Protocol) 使用示例
演示如何在 TradingAgents 中使用 MCP 功能
"""

import sys
import os
import asyncio

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.default_config import DEFAULT_CONFIG


def example_basic_mcp_usage():
    """基本 MCP 使用示例"""
    print("=== 基本 MCP 使用示例 ===")
    
    # 1. 使用预定义的网络搜索工具
    print("\n1. 网络搜索示例:")
    result = Toolkit.search_web_with_mcp(
        query="NVIDIA Q4 2024 earnings results",
        max_results=3
    )
    print(f"搜索结果: {result[:500]}...")
    
    # 2. 获取财经新闻
    print("\n2. 财经新闻示例:")
    news_result = Toolkit.get_financial_news_mcp(
        topic="Federal Reserve interest rate decision",
        date_range="last 14 days"
    )
    print(f"新闻结果: {news_result[:500]}...")
    
    # 3. 市场情绪分析
    print("\n3. 市场情绪分析示例:")
    sentiment_result = Toolkit.analyze_market_sentiment_mcp(
        ticker="TSLA",
        analysis_period="last 7 days"
    )
    print(f"情绪分析结果: {sentiment_result[:500]}...")


def example_custom_mcp_tools():
    """自定义 MCP 工具示例"""
    print("\n=== 自定义 MCP 工具示例 ===")
    
    # 1. 创建自定义的行业分析工具
    industry_analysis_tool = Toolkit.create_tavily_search_tool(
        tool_name="analyze_industry_trends",
        search_template="Search for industry trends and market analysis for {industry} sector in {year}. Include growth projections, key challenges, and emerging opportunities.",
        description="分析特定行业的趋势和市场前景"
    )
    
    print("\n1. 行业趋势分析:")
    # 注意：由于这是动态创建的工具，需要直接调用
    # 在实际使用中，你可能需要将其注册到代理的工具列表中
    
    # 2. 创建ESG分析工具
    esg_analysis_tool = Toolkit.create_tavily_search_tool(
        tool_name="get_esg_analysis",
        search_template="Search for ESG (Environmental, Social, Governance) analysis and sustainability reports for {company}. Include ESG scores, sustainability initiatives, and environmental impact.",
        description="获取公司的ESG分析和可持续发展报告"
    )
    
    print("2. 创建了ESG分析工具")
    
    # 3. 获取预定义的专业工具
    earnings_tool = Toolkit.get_earnings_analysis_tool()
    regulatory_tool = Toolkit.get_regulatory_news_tool()
    ma_tool = Toolkit.get_merger_acquisition_tool()
    
    print("3. 获取了预定义的专业分析工具")


async def example_advanced_mcp_usage():
    """高级 MCP 使用示例"""
    print("\n=== 高级 MCP 使用示例 ===")
    
    # 1. 直接使用 MCP 客户端和代理
    print("\n1. 直接使用 MCP 代理:")
    
    # 配置 Tavily MCP 服务器
    tavily_config = Toolkit.get_tavily_mcp_config()
    
    try:
        # 创建 MCP 代理
        client, agent = await Toolkit.create_mcp_agent(tavily_config)
        
        # 执行复杂查询
        complex_query = """
        Search for comprehensive analysis of Apple Inc (AAPL) including:
        1. Recent financial performance and earnings
        2. Product launch updates and market reception
        3. Competitive position in smartphone and services markets
        4. Analyst price targets and recommendations
        Provide a summary suitable for investment decision making.
        """
        
        response = await agent.ainvoke({
            "messages": [{"role": "user", "content": complex_query}]
        })
        
        print(f"复杂查询结果: {str(response)[:500]}...")
        
        # 清理资源
        await client.close()
        
    except Exception as e:
        print(f"高级 MCP 使用错误: {e}")
    
    # 2. 使用多个 MCP 服务器
    print("\n2. 多服务器配置示例:")
    
    # 组合多个 MCP 服务器配置
    multi_server_config = {}
    multi_server_config.update(Toolkit.get_tavily_mcp_config())
    multi_server_config.update(Toolkit.get_web_search_mcp_config())
    
    print(f"配置了 {len(multi_server_config)} 个 MCP 服务器")


def example_mcp_integration_with_trading():
    """MCP 与交易系统集成示例"""
    print("\n=== MCP 与交易系统集成示例 ===")
    
    # 1. 获取所有可用的 MCP 工具
    mcp_tools = Toolkit.get_all_mcp_tools()
    print(f"\n1. 可用的 MCP 工具: {list(mcp_tools.keys())}")
    
    # 2. 注册 MCP 工具
    registered_tools = Toolkit.register_mcp_tools()
    print(f"2. 注册了 {len(registered_tools)} 个 MCP 工具")
    
    # 3. 模拟交易决策流程中使用 MCP 工具
    print("\n3. 交易决策流程示例:")
    
    ticker = "NVDA"
    
    # 步骤1: 获取最新新闻
    print(f"   步骤1: 获取 {ticker} 的最新新闻...")
    news = Toolkit.get_financial_news_mcp(
        topic=f"{ticker} stock news earnings",
        date_range="last 7 days"
    )
    print(f"   新闻摘要: {news[:200]}...")
    
    # 步骤2: 分析市场情绪
    print(f"   步骤2: 分析 {ticker} 的市场情绪...")
    sentiment = Toolkit.analyze_market_sentiment_mcp(
        ticker=ticker,
        analysis_period="last 14 days"
    )
    print(f"   情绪分析: {sentiment[:200]}...")
    
    # 步骤3: 竞争对手分析
    print(f"   步骤3: 分析 {ticker} 的竞争环境...")
    competition = Toolkit.get_competitor_analysis_mcp(
        company=ticker,
        industry="semiconductor"
    )
    print(f"   竞争分析: {competition[:200]}...")


def main():
    """主函数"""
    print("TradingAgents MCP 功能演示")
    print("=" * 50)
    
    # 基本使用示例
    example_basic_mcp_usage()
    
    # 自定义工具示例
    example_custom_mcp_tools()
    
    # 高级使用示例（异步）
    print("\n运行高级异步示例...")
    asyncio.run(example_advanced_mcp_usage())
    
    # 与交易系统集成示例
    example_mcp_integration_with_trading()
    
    print("\n" + "=" * 50)
    print("MCP 功能演示完成！")


if __name__ == "__main__":
    main()
