from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from typing import List
from typing import Annotated
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import RemoveMessage
from langchain_core.tools import tool
from datetime import date, timedelta, datetime
import functools
import pandas as pd
import os
from dateutil.relativedelta import relativedelta
from langchain_openai import ChatOpenAI
import tradingagents.dataflows.interface as interface
from tradingagents.default_config import DEFAULT_CONFIG
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
import asyncio
import threading


def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]

        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages]

        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")

        return {"messages": removal_operations + [placeholder]}

    return delete_messages


class Toolkit:
    _config = DEFAULT_CONFIG.copy()

    @classmethod
    def update_config(cls, config):
        """Update the class-level configuration."""
        cls._config.update(config)

    @property
    def config(self):
        """Access the configuration."""
        return self._config

    def __init__(self, config=None):
        if config:
            self.update_config(config)

    @staticmethod
    @tool
    def get_reddit_news(
        curr_date: Annotated[str, "Date you want to get news for in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve global news from Reddit within a specified time frame.
        Args:
            curr_date (str): Date you want to get news for in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the latest global news from Reddit in the specified time frame.
        """

        global_news_result = interface.get_reddit_global_news(curr_date, 7, 5)

        return global_news_result

    @staticmethod
    @tool
    def get_finnhub_news(
        ticker: Annotated[
            str,
            "Search query of a company, e.g. 'AAPL, TSM, etc.",
        ],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news about a given stock from Finnhub within a date range
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing news about the company within the date range from start_date to end_date
        """

        end_date_str = end_date

        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        look_back_days = (end_date - start_date).days

        finnhub_news_result = interface.get_finnhub_news(
            ticker, end_date_str, look_back_days
        )

        return finnhub_news_result

    @staticmethod
    @tool
    def get_reddit_stock_info(
        ticker: Annotated[
            str,
            "Ticker of a company. e.g. AAPL, TSM",
        ],
        curr_date: Annotated[str, "Current date you want to get news for"],
    ) -> str:
        """
        Retrieve the latest news about a given stock from Reddit, given the current date.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): current date in yyyy-mm-dd format to get news for
        Returns:
            str: A formatted dataframe containing the latest news about the company on the given date
        """

        stock_news_results = interface.get_reddit_company_news(ticker, curr_date, 7, 5)

        return stock_news_results

    @staticmethod
    @tool
    def get_YFin_data(
        symbol: Annotated[str, "ticker symbol of the company"],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve the stock price data for a given ticker symbol from Yahoo Finance.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
        """

        result_data = interface.get_YFin_data(symbol, start_date, end_date)

        return result_data

    @staticmethod
    @tool
    def get_YFin_data_online(
        symbol: Annotated[str, "ticker symbol of the company"],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve the stock price data for a given ticker symbol from Yahoo Finance.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
        """

        result_data = interface.get_YFin_data_online(symbol, start_date, end_date)

        return result_data

    @staticmethod
    @tool
    def get_stockstats_indicators_report(
        symbol: Annotated[str, "ticker symbol of the company"],
        indicator: Annotated[
            str, "technical indicator to get the analysis and report of"
        ],
        curr_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
        look_back_days: Annotated[int, "how many days to look back"] = 30,
    ) -> str:
        """
        Retrieve stock stats indicators for a given ticker symbol and indicator.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            indicator (str): Technical indicator to get the analysis and report of
            curr_date (str): The current trading date you are trading on, YYYY-mm-dd
            look_back_days (int): How many days to look back, default is 30
        Returns:
            str: A formatted dataframe containing the stock stats indicators for the specified ticker symbol and indicator.
        """

        result_stockstats = interface.get_stock_stats_indicators_window(
            symbol, indicator, curr_date, look_back_days, False
        )

        return result_stockstats

    @staticmethod
    @tool
    def get_stockstats_indicators_report_online(
        symbol: Annotated[str, "ticker symbol of the company"],
        indicator: Annotated[
            str, "technical indicator to get the analysis and report of"
        ],
        curr_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
        look_back_days: Annotated[int, "how many days to look back"] = 30,
    ) -> str:
        """
        Retrieve stock stats indicators for a given ticker symbol and indicator.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            indicator (str): Technical indicator to get the analysis and report of
            curr_date (str): The current trading date you are trading on, YYYY-mm-dd
            look_back_days (int): How many days to look back, default is 30
        Returns:
            str: A formatted dataframe containing the stock stats indicators for the specified ticker symbol and indicator.
        """

        result_stockstats = interface.get_stock_stats_indicators_window(
            symbol, indicator, curr_date, look_back_days, True
        )

        return result_stockstats

    @staticmethod
    @tool
    def get_finnhub_company_insider_sentiment(
        ticker: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[
            str,
            "current date of you are trading at, yyyy-mm-dd",
        ],
    ):
        """
        Retrieve insider sentiment information about a company (retrieved from public SEC information) for the past 30 days
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the sentiment in the past 30 days starting at curr_date
        """

        data_sentiment = interface.get_finnhub_company_insider_sentiment(
            ticker, curr_date, 30
        )

        return data_sentiment

    @staticmethod
    @tool
    def get_finnhub_company_insider_transactions(
        ticker: Annotated[str, "ticker symbol"],
        curr_date: Annotated[
            str,
            "current date you are trading at, yyyy-mm-dd",
        ],
    ):
        """
        Retrieve insider transaction information about a company (retrieved from public SEC information) for the past 30 days
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the company's insider transactions/trading information in the past 30 days
        """

        data_trans = interface.get_finnhub_company_insider_transactions(
            ticker, curr_date, 30
        )

        return data_trans

    @staticmethod
    @tool
    def get_simfin_balance_sheet(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent balance sheet of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the company's most recent balance sheet
        """

        data_balance_sheet = interface.get_simfin_balance_sheet(ticker, freq, curr_date)

        return data_balance_sheet

    @staticmethod
    @tool
    def get_simfin_cashflow(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent cash flow statement of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
                str: a report of the company's most recent cash flow statement
        """

        data_cashflow = interface.get_simfin_cashflow(ticker, freq, curr_date)

        return data_cashflow

    @staticmethod
    @tool
    def get_simfin_income_stmt(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent income statement of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
                str: a report of the company's most recent income statement
        """

        data_income_stmt = interface.get_simfin_income_statements(
            ticker, freq, curr_date
        )

        return data_income_stmt

    @staticmethod
    @tool
    def get_google_news(
        query: Annotated[str, "Query to search with"],
        curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news from Google News based on a query and date range.
        Args:
            query (str): Query to search with
            curr_date (str): Current date in yyyy-mm-dd format
            look_back_days (int): How many days to look back
        Returns:
            str: A formatted string containing the latest news from Google News based on the query and date range.
        """

        google_news_results = interface.get_google_news(query, curr_date, 7)

        return google_news_results

    @staticmethod
    @tool
    def get_stock_news_openai(
        ticker: Annotated[str, "the company's ticker"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news about a given stock by using Tavily MCP to get real-time data.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest news about the company on the given date.
        """
        import asyncio
        import threading

        def run_async_in_thread():
            """在新线程中运行异步函数"""
            try:
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        interface.get_stock_news_openai(ticker, curr_date)
                    )
                finally:
                    loop.close()
            except Exception as e:
                return f"错误: {str(e)}"

        # 在新线程中运行异步函数
        try:
            result_container = []
            exception_container = []

            def thread_target():
                try:
                    result = run_async_in_thread()
                    result_container.append(result)
                except Exception as e:
                    exception_container.append(e)

            thread = threading.Thread(target=thread_target)
            thread.start()
            thread.join(timeout=120)  # 2分钟超时

            if thread.is_alive():
                return "错误: 请求超时"

            if exception_container:
                return f"错误: {str(exception_container[0])}"

            if result_container:
                return result_container[0]

            return "错误: 未知错误"

        except Exception as e:
            return f"错误: {str(e)}"

    @staticmethod
    @tool
    def get_global_news_openai(
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest macroeconomics news using Tavily MCP to get real-time data.
        Args:
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest macroeconomic news on the given date.
        """
        import asyncio
        import threading

        def run_async_in_thread():
            """在新线程中运行异步函数"""
            try:
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        interface.get_global_news_openai(curr_date)
                    )
                finally:
                    loop.close()
            except Exception as e:
                return f"错误: {str(e)}"

        # 在新线程中运行异步函数
        try:
            result_container = []
            exception_container = []

            def thread_target():
                try:
                    result = run_async_in_thread()
                    result_container.append(result)
                except Exception as e:
                    exception_container.append(e)

            thread = threading.Thread(target=thread_target)
            thread.start()
            thread.join(timeout=120)  # 2分钟超时

            if thread.is_alive():
                return "错误: 请求超时"

            if exception_container:
                return f"错误: {str(exception_container[0])}"

            if result_container:
                return result_container[0]

            return "错误: 未知错误"

        except Exception as e:
            return f"错误: {str(e)}"

    @staticmethod
    @tool
    def get_fundamentals_openai(
        ticker: Annotated[str, "the company's ticker"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest fundamental information about a given stock using Tavily MCP to get real-time data.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest fundamental information about the company on the given date.
        """
        import asyncio
        import threading

        def run_async_in_thread():
            """在新线程中运行异步函数"""
            try:
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        interface.get_fundamentals_openai(ticker, curr_date)
                    )
                finally:
                    loop.close()
            except Exception as e:
                return f"错误: {str(e)}"

        # 在新线程中运行异步函数
        try:
            result_container = []
            exception_container = []

            def thread_target():
                try:
                    result = run_async_in_thread()
                    result_container.append(result)
                except Exception as e:
                    exception_container.append(e)

            thread = threading.Thread(target=thread_target)
            thread.start()
            thread.join(timeout=120)  # 2分钟超时

            if thread.is_alive():
                return "错误: 请求超时"

            if exception_container:
                return f"错误: {str(exception_container[0])}"

            if result_container:
                return result_container[0]

            return "错误: 未知错误"

        except Exception as e:
            return f"错误: {str(e)}"

    # MCP (Model Context Protocol) 相关方法
    @classmethod
    def create_mcp_client(cls, server_configs):
        """
        创建 MCP 客户端
        Args:
            server_configs (dict): MCP 服务器配置字典
        Returns:
            MultiServerMCPClient: MCP 客户端实例
        """
        return MultiServerMCPClient(server_configs)

    @classmethod
    async def create_mcp_agent(cls, server_configs, llm_config=None):
        """
        创建 MCP 代理
        Args:
            server_configs (dict): MCP 服务器配置字典
            llm_config (dict): LLM 配置，如果为 None 则使用默认配置
        Returns:
            tuple: (client, agent) MCP 客户端和代理实例
        """
        # 创建 MCP 客户端
        client = cls.create_mcp_client(server_configs)

        # 获取工具
        tools = await client.get_tools()

        # 使用提供的 LLM 配置或默认配置
        if llm_config is None:
            llm_config = cls._config

        # 创建 LLM 实例
        llm = ChatOpenAI(
            model=llm_config.get("quick_think_llm", "gpt-4o-mini"),
            base_url=llm_config.get("backend_url", "https://api.nuwaapi.com/v1"),
            api_key=llm_config.get("openai_api_key", ""),
        )

        # 创建代理
        agent = create_react_agent(llm, tools)

        return client, agent

    @classmethod
    async def execute_mcp_query(
        cls, query, server_configs, description="MCP查询", llm_config=None
    ):
        """
        执行 MCP 查询的通用方法
        Args:
            query (str): 查询内容
            server_configs (dict): MCP 服务器配置字典
            description (str): 查询描述
            llm_config (dict): LLM 配置，如果为 None 则使用默认配置
        Returns:
            str: 查询结果
        """
        client = None
        try:
            client, agent = await cls.create_mcp_agent(server_configs, llm_config)

            print(f"执行{description}: {query}")

            # 调用代理
            response = await agent.ainvoke(
                {"messages": [{"role": "user", "content": query}]}
            )

            # 返回响应内容
            if isinstance(response, dict) and "messages" in response:
                messages = response["messages"]
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, "content"):
                        return last_message.content
                    elif isinstance(last_message, dict) and "content" in last_message:
                        return last_message["content"]

            return str(response)

        except Exception as e:
            print(f"{description}错误: {e}")
            return f"错误: {str(e)}"
        finally:
            # 清理资源
            if client:
                try:
                    await client.close()
                except:
                    pass

    @classmethod
    def run_mcp_query_sync(
        cls, query, server_configs, description="MCP查询", llm_config=None
    ):
        """
        同步执行 MCP 查询的方法（在新线程中运行异步函数）
        Args:
            query (str): 查询内容
            server_configs (dict): MCP 服务器配置字典
            description (str): 查询描述
            llm_config (dict): LLM 配置，如果为 None 则使用默认配置
        Returns:
            str: 查询结果
        """

        def run_async_in_thread():
            """在新线程中运行异步函数"""
            try:
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        cls.execute_mcp_query(
                            query, server_configs, description, llm_config
                        )
                    )
                finally:
                    loop.close()
            except Exception as e:
                return f"错误: {str(e)}"

        # 在新线程中运行异步函数
        try:
            result_container = []
            exception_container = []

            def thread_target():
                try:
                    result = run_async_in_thread()
                    result_container.append(result)
                except Exception as e:
                    exception_container.append(e)

            thread = threading.Thread(target=thread_target)
            thread.start()
            thread.join(timeout=120)  # 2分钟超时

            if thread.is_alive():
                return "错误: 请求超时"

            if exception_container:
                return f"错误: {str(exception_container[0])}"

            if result_container:
                return result_container[0]

            return "错误: 未知错误"

        except Exception as e:
            return f"错误: {str(e)}"

    # 预定义的 MCP 服务器配置
    @classmethod
    def get_tavily_mcp_config(cls, api_key="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"):
        """
        获取 Tavily MCP 服务器配置
        Args:
            api_key (str): Tavily API 密钥
        Returns:
            dict: Tavily MCP 服务器配置
        """
        return {
            "tavily-mcp": {
                "command": "npx",
                "args": ["-y", "tavily-mcp@0.1.2"],
                "env": {"TAVILY_API_KEY": api_key},
                "transport": "stdio",
            }
        }

    @classmethod
    def get_filesystem_mcp_config(cls, allowed_directories=None):
        """
        获取文件系统 MCP 服务器配置
        Args:
            allowed_directories (list): 允许访问的目录列表
        Returns:
            dict: 文件系统 MCP 服务器配置
        """
        config = {
            "filesystem-mcp": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                "transport": "stdio",
            }
        }

        if allowed_directories:
            config["filesystem-mcp"]["args"].extend(allowed_directories)

        return config

    @classmethod
    def get_web_search_mcp_config(cls):
        """
        获取网络搜索 MCP 服务器配置
        Returns:
            dict: 网络搜索 MCP 服务器配置
        """
        return {
            "web-search-mcp": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-web-search"],
                "transport": "stdio",
            }
        }

    # 便捷的 MCP 工具方法
    @staticmethod
    @tool
    def search_web_with_mcp(
        query: Annotated[str, "搜索查询内容"],
        max_results: Annotated[int, "最大结果数量"] = 5,
    ):
        """
        使用 Tavily MCP 进行网络搜索
        Args:
            query (str): 搜索查询内容
            max_results (int): 最大结果数量，默认为 5
        Returns:
            str: 搜索结果
        """
        tavily_config = Toolkit.get_tavily_mcp_config()
        search_query = f"Search for: {query}. Limit results to {max_results} items."

        return Toolkit.run_mcp_query_sync(
            search_query, tavily_config, f"网络搜索: {query}"
        )

    @staticmethod
    @tool
    def get_financial_news_mcp(
        topic: Annotated[str, "财经新闻主题"],
        date_range: Annotated[str, "日期范围，例如 'last 7 days'"] = "last 7 days",
    ):
        """
        使用 MCP 获取财经新闻
        Args:
            topic (str): 财经新闻主题
            date_range (str): 日期范围，默认为 "last 7 days"
        Returns:
            str: 财经新闻结果
        """
        tavily_config = Toolkit.get_tavily_mcp_config()
        search_query = f"Search for financial news about {topic} from {date_range}. Focus on market impact, earnings, and economic indicators."

        return Toolkit.run_mcp_query_sync(
            search_query, tavily_config, f"财经新闻搜索: {topic}"
        )

    @staticmethod
    @tool
    def analyze_market_sentiment_mcp(
        ticker: Annotated[str, "股票代码"],
        analysis_period: Annotated[str, "分析周期"] = "last 30 days",
    ):
        """
        使用 MCP 分析市场情绪
        Args:
            ticker (str): 股票代码
            analysis_period (str): 分析周期，默认为 "last 30 days"
        Returns:
            str: 市场情绪分析结果
        """
        tavily_config = Toolkit.get_tavily_mcp_config()
        search_query = f"Search for market sentiment analysis and investor opinions about {ticker} stock over {analysis_period}. Include social media sentiment, analyst opinions, and market commentary."

        return Toolkit.run_mcp_query_sync(
            search_query, tavily_config, f"市场情绪分析: {ticker}"
        )

    @staticmethod
    @tool
    def get_competitor_analysis_mcp(
        company: Annotated[str, "公司名称或股票代码"],
        industry: Annotated[str, "行业类别"] = "",
    ):
        """
        使用 MCP 进行竞争对手分析
        Args:
            company (str): 公司名称或股票代码
            industry (str): 行业类别，可选
        Returns:
            str: 竞争对手分析结果
        """
        tavily_config = Toolkit.get_tavily_mcp_config()
        industry_filter = f" in {industry} industry" if industry else ""
        search_query = f"Search for competitor analysis and market positioning of {company}{industry_filter}. Include market share, competitive advantages, and recent competitive developments."

        return Toolkit.run_mcp_query_sync(
            search_query, tavily_config, f"竞争对手分析: {company}"
        )

    @classmethod
    def create_custom_mcp_tool(
        cls, tool_name, description, server_configs, query_template
    ):
        """
        创建自定义 MCP 工具
        Args:
            tool_name (str): 工具名称
            description (str): 工具描述
            server_configs (dict): MCP 服务器配置
            query_template (str): 查询模板，使用 {param_name} 作为参数占位符
        Returns:
            function: 装饰后的工具函数
        """

        def tool_function(**kwargs):
            """动态生成的 MCP 工具函数"""
            try:
                # 使用参数填充查询模板
                query = query_template.format(**kwargs)

                return cls.run_mcp_query_sync(
                    query, server_configs, f"{tool_name}: {kwargs}"
                )
            except KeyError as e:
                return f"错误: 查询模板中缺少参数 {e}"
            except Exception as e:
                return f"错误: {str(e)}"

        # 设置函数名称和文档字符串
        tool_function.__name__ = tool_name
        tool_function.__doc__ = description

        # 应用 @tool 装饰器并设置名称
        structured_tool = tool(tool_function)
        structured_tool.name = tool_name
        structured_tool.description = description

        return structured_tool

    @classmethod
    def create_tavily_search_tool(cls, tool_name, search_template, description=None):
        """
        创建基于 Tavily 的搜索工具
        Args:
            tool_name (str): 工具名称
            search_template (str): 搜索模板，使用 {param_name} 作为参数占位符
            description (str): 工具描述，如果为 None 则自动生成
        Returns:
            function: 装饰后的工具函数
        """
        if description is None:
            description = f"使用 Tavily MCP 进行搜索: {tool_name}"

        tavily_config = cls.get_tavily_mcp_config()

        return cls.create_custom_mcp_tool(
            tool_name=tool_name,
            description=description,
            server_configs=tavily_config,
            query_template=search_template,
        )

    # 示例：创建一些专门的搜索工具
    @classmethod
    def get_earnings_analysis_tool(cls):
        """获取财报分析工具"""
        return cls.create_tavily_search_tool(
            tool_name="get_earnings_analysis",
            search_template="Search for earnings analysis and financial performance of {ticker} for {quarter} {year}. Include revenue, profit margins, guidance, and analyst reactions.",
            description="获取指定公司的财报分析和财务表现",
        )

    @classmethod
    def get_regulatory_news_tool(cls):
        """获取监管新闻工具"""
        return cls.create_tavily_search_tool(
            tool_name="get_regulatory_news",
            search_template="Search for regulatory news and policy changes affecting {industry} sector in {region} from {date_range}. Focus on compliance requirements and market impact.",
            description="获取影响特定行业的监管新闻和政策变化",
        )

    @classmethod
    def get_merger_acquisition_tool(cls):
        """获取并购新闻工具"""
        return cls.create_tavily_search_tool(
            tool_name="get_merger_acquisition_news",
            search_template="Search for merger and acquisition news involving {company} or {industry} sector from {date_range}. Include deal values, strategic rationale, and market reactions.",
            description="获取并购相关新闻和市场反应",
        )

    # 工具注册方法
    @classmethod
    def register_mcp_tools(cls, tool_list=None):
        """
        注册 MCP 工具到工具列表
        Args:
            tool_list (list): 要注册的工具列表，如果为 None 则注册所有默认工具
        Returns:
            list: 注册的工具列表
        """
        if tool_list is None:
            # 默认工具列表
            tool_list = [
                cls.search_web_with_mcp,
                cls.get_financial_news_mcp,
                cls.analyze_market_sentiment_mcp,
                cls.get_competitor_analysis_mcp,
            ]

        return tool_list

    @classmethod
    def get_all_mcp_tools(cls):
        """
        获取所有可用的 MCP 工具
        Returns:
            dict: 工具名称到工具函数的映射
        """
        return {
            "search_web_with_mcp": cls.search_web_with_mcp,
            "get_financial_news_mcp": cls.get_financial_news_mcp,
            "analyze_market_sentiment_mcp": cls.analyze_market_sentiment_mcp,
            "get_competitor_analysis_mcp": cls.get_competitor_analysis_mcp,
            "get_earnings_analysis_tool": cls.get_earnings_analysis_tool(),
            "get_regulatory_news_tool": cls.get_regulatory_news_tool(),
            "get_merger_acquisition_tool": cls.get_merger_acquisition_tool(),
        }
