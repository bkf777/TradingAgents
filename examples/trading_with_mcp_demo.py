"""
使用 MCP 功能进行交易分析的演示
演示如何将 MCP 工具集成到交易决策流程中
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.default_config import DEFAULT_CONFIG


class MCPTradingAnalyzer:
    """使用 MCP 功能的交易分析器"""
    
    def __init__(self):
        self.toolkit = Toolkit()
        
    def analyze_stock_comprehensive(self, ticker, analysis_date="2024-12-01"):
        """
        对股票进行综合分析
        Args:
            ticker (str): 股票代码
            analysis_date (str): 分析日期
        Returns:
            dict: 综合分析结果
        """
        print(f"🔍 开始对 {ticker} 进行综合分析...")
        
        analysis_results = {
            "ticker": ticker,
            "analysis_date": analysis_date,
            "news_analysis": None,
            "sentiment_analysis": None,
            "competitor_analysis": None,
            "market_trends": None,
            "recommendation": None
        }
        
        # 1. 获取最新财经新闻
        print(f"\n📰 步骤 1: 获取 {ticker} 的最新新闻...")
        try:
            news_result = Toolkit.get_financial_news_mcp.invoke({
                "topic": f"{ticker} stock earnings financial results",
                "date_range": "last 14 days"
            })
            analysis_results["news_analysis"] = news_result[:500] + "..." if len(news_result) > 500 else news_result
            print("✅ 新闻分析完成")
        except Exception as e:
            print(f"❌ 新闻分析失败: {e}")
            analysis_results["news_analysis"] = f"错误: {str(e)}"

        # 2. 分析市场情绪
        print(f"\n💭 步骤 2: 分析 {ticker} 的市场情绪...")
        try:
            sentiment_result = Toolkit.analyze_market_sentiment_mcp.invoke({
                "ticker": ticker,
                "analysis_period": "last 30 days"
            })
            analysis_results["sentiment_analysis"] = sentiment_result[:500] + "..." if len(sentiment_result) > 500 else sentiment_result
            print("✅ 情绪分析完成")
        except Exception as e:
            print(f"❌ 情绪分析失败: {e}")
            analysis_results["sentiment_analysis"] = f"错误: {str(e)}"

        # 3. 竞争对手分析
        print(f"\n🏢 步骤 3: 分析 {ticker} 的竞争环境...")
        try:
            # 根据不同股票确定行业
            industry_map = {
                "AAPL": "technology smartphone",
                "TSLA": "electric vehicle automotive",
                "NVDA": "semiconductor AI chips",
                "MSFT": "technology cloud computing",
                "GOOGL": "technology search advertising",
                "AMZN": "e-commerce cloud computing"
            }
            industry = industry_map.get(ticker, "technology")

            competitor_result = Toolkit.get_competitor_analysis_mcp.invoke({
                "company": ticker,
                "industry": industry
            })
            analysis_results["competitor_analysis"] = competitor_result[:500] + "..." if len(competitor_result) > 500 else competitor_result
            print("✅ 竞争分析完成")
        except Exception as e:
            print(f"❌ 竞争分析失败: {e}")
            analysis_results["competitor_analysis"] = f"错误: {str(e)}"

        # 4. 市场趋势分析
        print(f"\n📈 步骤 4: 分析相关市场趋势...")
        try:
            trends_result = Toolkit.search_web_with_mcp.invoke({
                "query": f"market trends analysis {ticker} sector outlook 2024",
                "max_results": 3
            })
            analysis_results["market_trends"] = trends_result[:500] + "..." if len(trends_result) > 500 else trends_result
            print("✅ 趋势分析完成")
        except Exception as e:
            print(f"❌ 趋势分析失败: {e}")
            analysis_results["market_trends"] = f"错误: {str(e)}"
        
        # 5. 生成投资建议
        print(f"\n🎯 步骤 5: 生成投资建议...")
        analysis_results["recommendation"] = self._generate_recommendation(analysis_results)
        
        return analysis_results
    
    def _generate_recommendation(self, analysis_results):
        """
        基于分析结果生成投资建议
        Args:
            analysis_results (dict): 分析结果
        Returns:
            str: 投资建议
        """
        # 简单的规则基础建议生成
        positive_indicators = 0
        negative_indicators = 0
        
        # 检查各项分析结果中的关键词
        positive_keywords = ["growth", "increase", "positive", "bullish", "strong", "beat", "exceed"]
        negative_keywords = ["decline", "decrease", "negative", "bearish", "weak", "miss", "below"]
        
        for key, value in analysis_results.items():
            if key in ["news_analysis", "sentiment_analysis", "competitor_analysis", "market_trends"] and value:
                value_lower = str(value).lower()
                for keyword in positive_keywords:
                    if keyword in value_lower:
                        positive_indicators += 1
                        break
                for keyword in negative_keywords:
                    if keyword in value_lower:
                        negative_indicators += 1
                        break
        
        # 生成建议
        if positive_indicators > negative_indicators:
            recommendation = "🟢 建议: 看涨 - 基于当前分析，该股票显示出积极信号"
        elif negative_indicators > positive_indicators:
            recommendation = "🔴 建议: 看跌 - 基于当前分析，该股票显示出消极信号"
        else:
            recommendation = "🟡 建议: 中性 - 需要更多信息进行决策"
        
        recommendation += f"\n积极指标: {positive_indicators}, 消极指标: {negative_indicators}"
        
        return recommendation
    
    def create_custom_analysis_tool(self, analysis_type, search_template):
        """
        创建自定义分析工具
        Args:
            analysis_type (str): 分析类型
            search_template (str): 搜索模板
        Returns:
            function: 自定义分析工具
        """
        return Toolkit.create_tavily_search_tool(
            tool_name=f"analyze_{analysis_type}",
            search_template=search_template,
            description=f"分析 {analysis_type} 相关信息"
        )
    
    def demonstrate_custom_tools(self):
        """演示自定义工具创建和使用"""
        print("\n🛠️ 演示自定义 MCP 工具创建...")
        
        # 1. 创建ESG分析工具
        esg_tool = self.create_custom_analysis_tool(
            "esg_performance",
            "Search for ESG (Environmental, Social, Governance) analysis and sustainability reports for {company}. Include ESG scores and environmental impact."
        )
        print(f"✅ 创建ESG分析工具: {esg_tool.name}")
        
        # 2. 创建技术分析工具
        technical_tool = self.create_custom_analysis_tool(
            "technical_indicators",
            "Search for technical analysis and chart patterns for {ticker} stock. Include moving averages, RSI, MACD, and support/resistance levels."
        )
        print(f"✅ 创建技术分析工具: {technical_tool.name}")
        
        # 3. 创建宏观经济分析工具
        macro_tool = self.create_custom_analysis_tool(
            "macro_economic_impact",
            "Search for macroeconomic factors affecting {sector} sector including interest rates, inflation, GDP growth, and policy changes."
        )
        print(f"✅ 创建宏观经济分析工具: {macro_tool.name}")
        
        return {
            "esg_tool": esg_tool,
            "technical_tool": technical_tool,
            "macro_tool": macro_tool
        }


def main():
    """主演示函数"""
    print("🚀 MCP 交易分析演示")
    print("=" * 60)
    
    # 创建分析器
    analyzer = MCPTradingAnalyzer()
    
    # 演示股票列表
    demo_stocks = ["AAPL", "TSLA", "NVDA"]
    
    print(f"📊 将对以下股票进行分析: {', '.join(demo_stocks)}")
    print("\n注意: 这是演示模式，实际的网络请求可能需要有效的API密钥")
    
    # 对每只股票进行分析
    for ticker in demo_stocks:
        print(f"\n{'='*60}")
        print(f"📈 分析股票: {ticker}")
        print(f"{'='*60}")
        
        try:
            # 进行综合分析
            results = analyzer.analyze_stock_comprehensive(ticker)
            
            # 显示结果摘要
            print(f"\n📋 {ticker} 分析结果摘要:")
            print(f"股票代码: {results['ticker']}")
            print(f"分析日期: {results['analysis_date']}")
            print(f"投资建议: {results['recommendation']}")
            
            # 显示各项分析的状态
            analysis_items = [
                ("新闻分析", results['news_analysis']),
                ("情绪分析", results['sentiment_analysis']),
                ("竞争分析", results['competitor_analysis']),
                ("趋势分析", results['market_trends'])
            ]
            
            for item_name, item_result in analysis_items:
                if item_result and not item_result.startswith("错误:"):
                    print(f"✅ {item_name}: 完成")
                else:
                    print(f"❌ {item_name}: 失败或跳过")
            
        except Exception as e:
            print(f"❌ 分析 {ticker} 时发生错误: {e}")
        
        # 添加分隔符
        if ticker != demo_stocks[-1]:
            print("\n" + "-" * 40)
    
    # 演示自定义工具创建
    print(f"\n{'='*60}")
    print("🛠️ 自定义工具演示")
    print(f"{'='*60}")
    
    custom_tools = analyzer.demonstrate_custom_tools()
    
    print(f"\n✅ 成功创建 {len(custom_tools)} 个自定义工具")
    print("这些工具可以在实际交易分析中使用")
    
    # 总结
    print(f"\n{'='*60}")
    print("📝 演示总结")
    print(f"{'='*60}")
    print("✅ MCP 功能已成功集成到 TradingAgents 中")
    print("✅ 可以创建自定义分析工具")
    print("✅ 支持多种数据源和分析类型")
    print("✅ 提供了完整的交易决策支持框架")
    
    print(f"\n📖 下一步:")
    print("1. 配置有效的 API 密钥以启用实际网络请求")
    print("2. 根据具体需求创建更多自定义工具")
    print("3. 将 MCP 工具集成到现有的交易策略中")
    print("4. 查看 docs/MCP_USAGE.md 了解更多使用方法")


if __name__ == "__main__":
    main()
