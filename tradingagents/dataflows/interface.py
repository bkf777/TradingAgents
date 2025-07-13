from typing import Annotated, Dict
from .reddit_utils import fetch_top_from_category
from .yfin_utils import *
from .stockstats_utils import *
from .googlenews_utils import *
from .finnhub_utils import get_data_in_range
from .akshare_utils import (
    akshare_utils,
    get_akshare_stock_data,
    get_akshare_stock_info,
    get_akshare_balance_sheet,
    get_akshare_income_statement,
    get_akshare_cash_flow,
    get_akshare_news,
    get_akshare_global_news,
)
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import os
import pandas as pd
from tqdm import tqdm
import yfinance as yf
from openai import OpenAI
from .config import get_config, set_config, DATA_DIR
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent


async def _create_tavily_mcp_agent(config):
    """
    创建 Tavily MCP 代理的通用函数
    """
    # 创建 MCP 客户端
    client = MultiServerMCPClient(
        {
            "tavily-mcp": {
                "command": "npx",
                "args": ["-y", "tavily-mcp@0.1.2"],
                "env": {"TAVILY_API_KEY": "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"},
                "transport": "stdio",
            }
        }
    )

    # 获取工具
    tools = await client.get_tools()

    # 创建 LLM 实例
    from langchain_openai import ChatOpenAI

    # 对于 MCP 环境中的 LangChain ChatOpenAI，需要使用基础 URL（不包含 /chat/completions）
    backend_url = config["backend_url"]
    if backend_url.endswith("/chat/completions"):
        backend_url = backend_url.replace("/chat/completions", "")

    llm = ChatOpenAI(
        model=config["quick_think_llm"],
        base_url=backend_url,
        api_key=config["openai_api_key"],
    )

    # 创建 React 代理
    agent = create_react_agent(llm, tools)

    return client, agent


async def _execute_mcp_query(query, description="MCP查询"):
    """
    执行 MCP 查询的通用函数
    """
    config = get_config()

    try:
        client, agent = await _create_tavily_mcp_agent(config)

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
        try:
            await client.close()
        except:
            pass


def get_finnhub_news(
    ticker: Annotated[
        str,
        "Search query of a company's, e.g. 'AAPL, TSM, etc.",
    ],
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
):
    """
    使用AKShare获取股票新闻，替代Finnhub
    """
    try:
        print(f"使用AKShare获取股票新闻: {ticker} (回看 {look_back_days} 天)")

        start_date = datetime.strptime(curr_date, "%Y-%m-%d")
        before = start_date - relativedelta(days=look_back_days)
        before = before.strftime("%Y-%m-%d")

        # 使用AKShare获取新闻
        news_result = get_akshare_news(ticker, before, curr_date)

        if news_result:
            return news_result

        # 备用方案：使用原始Finnhub方法
        print(f"AKShare未找到新闻，尝试使用原始Finnhub方法")
        try:
            result = get_data_in_range(ticker, before, curr_date, "news_data", DATA_DIR)

            if len(result) == 0:
                return ""

            combined_result = ""
            for day, data in result.items():
                if len(data) == 0:
                    continue
                for entry in data:
                    current_news = (
                        "### "
                        + entry["headline"]
                        + f" ({day})"
                        + "\n"
                        + entry["summary"]
                    )
                    combined_result += current_news + "\n\n"

            return f"## {ticker} News, from {before} to {curr_date}:\n" + str(
                combined_result
            )
        except Exception as finnhub_error:
            print(f"Finnhub备用方案也失败: {str(finnhub_error)}")
            return ""

    except Exception as e:
        print(f"获取股票新闻时出错: {str(e)}")
        return ""


def get_finnhub_company_insider_sentiment(
    ticker: Annotated[str, "ticker symbol for the company"],
    curr_date: Annotated[
        str,
        "current date of you are trading at, yyyy-mm-dd",
    ],
    look_back_days: Annotated[int, "number of days to look back"],
):
    """
    Retrieve insider sentiment about a company (retrieved from public SEC information) for the past 15 days
    Args:
        ticker (str): ticker symbol of the company
        curr_date (str): current date you are trading on, yyyy-mm-dd
    Returns:
        str: a report of the sentiment in the past 15 days starting at curr_date
    """

    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
    before = date_obj - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    data = get_data_in_range(ticker, before, curr_date, "insider_senti", DATA_DIR)

    if len(data) == 0:
        return ""

    result_str = ""
    seen_dicts = []
    for date, senti_list in data.items():
        for entry in senti_list:
            if entry not in seen_dicts:
                result_str += f"### {entry['year']}-{entry['month']}:\nChange: {entry['change']}\nMonthly Share Purchase Ratio: {entry['mspr']}\n\n"
                seen_dicts.append(entry)

    return (
        f"## {ticker} Insider Sentiment Data for {before} to {curr_date}:\n"
        + result_str
        + "The change field refers to the net buying/selling from all insiders' transactions. The mspr field refers to monthly share purchase ratio."
    )


def get_finnhub_company_insider_transactions(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[
        str,
        "current date you are trading at, yyyy-mm-dd",
    ],
    look_back_days: Annotated[int, "how many days to look back"],
):
    """
    Retrieve insider transcaction information about a company (retrieved from public SEC information) for the past 15 days
    Args:
        ticker (str): ticker symbol of the company
        curr_date (str): current date you are trading at, yyyy-mm-dd
    Returns:
        str: a report of the company's insider transaction/trading informtaion in the past 15 days
    """

    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
    before = date_obj - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    data = get_data_in_range(ticker, before, curr_date, "insider_trans", DATA_DIR)

    if len(data) == 0:
        return ""

    result_str = ""

    seen_dicts = []
    for date, senti_list in data.items():
        for entry in senti_list:
            if entry not in seen_dicts:
                result_str += f"### Filing Date: {entry['filingDate']}, {entry['name']}:\nChange:{entry['change']}\nShares: {entry['share']}\nTransaction Price: {entry['transactionPrice']}\nTransaction Code: {entry['transactionCode']}\n\n"
                seen_dicts.append(entry)

    return (
        f"## {ticker} insider transactions from {before} to {curr_date}:\n"
        + result_str
        + "The change field reflects the variation in share count—here a negative number indicates a reduction in holdings—while share specifies the total number of shares involved. The transactionPrice denotes the per-share price at which the trade was executed, and transactionDate marks when the transaction occurred. The name field identifies the insider making the trade, and transactionCode (e.g., S for sale) clarifies the nature of the transaction. FilingDate records when the transaction was officially reported, and the unique id links to the specific SEC filing, as indicated by the source. Additionally, the symbol ties the transaction to a particular company, isDerivative flags whether the trade involves derivative securities, and currency notes the currency context of the transaction."
    )


def get_simfin_balance_sheet(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency of the company's financial history: annual / quarterly",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    """
    使用AKShare获取资产负债表数据，替代SimFin
    """
    try:
        print(f"使用AKShare获取资产负债表: {ticker} ({freq})")

        # 映射频率参数
        period_mapping = {"annual": "年报", "quarterly": "季报"}
        period = period_mapping.get(freq, "年报")

        # 使用AKShare获取数据
        data = get_akshare_balance_sheet(ticker, period)

        if data.empty:
            print(f"AKShare未找到数据，尝试使用原始SimFin方法")
            # 备用方案：使用原始SimFin方法
            try:
                data_path = os.path.join(
                    DATA_DIR,
                    "fundamental_data",
                    "simfin_data_all",
                    "balance_sheet",
                    "companies",
                    "us",
                    f"us-balance-{freq}.csv",
                )
                df = pd.read_csv(data_path, sep=";")

                # Convert date strings to datetime objects and remove any time components
                df["Report Date"] = pd.to_datetime(
                    df["Report Date"], utc=True
                ).dt.normalize()
                df["Publish Date"] = pd.to_datetime(
                    df["Publish Date"], utc=True
                ).dt.normalize()

                # Convert the current date to datetime and normalize
                curr_date_dt = pd.to_datetime(curr_date, utc=True).normalize()

                # Filter the DataFrame for the given ticker and for reports that were published on or before the current date
                filtered_df = df[
                    (df["Ticker"] == ticker) & (df["Publish Date"] <= curr_date_dt)
                ]

                # Check if there are any available reports; if not, return a notification
                if filtered_df.empty:
                    print("No balance sheet available before the given current date.")
                    return ""

                # Get the most recent balance sheet by selecting the row with the latest Publish Date
                latest_balance_sheet = filtered_df.loc[
                    filtered_df["Publish Date"].idxmax()
                ]

                # drop the SimFinID column
                if "SimFinId" in latest_balance_sheet.index:
                    latest_balance_sheet = latest_balance_sheet.drop("SimFinId")

                return (
                    f"## {freq} balance sheet for {ticker} released on {str(latest_balance_sheet['Publish Date'])[0:10]}: \n"
                    + str(latest_balance_sheet)
                    + "\n\nThis includes metadata like reporting dates and currency, share details, and a breakdown of assets, liabilities, and equity. Assets are grouped as current (liquid items like cash and receivables) and noncurrent (long-term investments and property). Liabilities are split between short-term obligations and long-term debts, while equity reflects shareholder funds such as paid-in capital and retained earnings. Together, these components ensure that total assets equal the sum of liabilities and equity."
                )
            except Exception as simfin_error:
                print(f"SimFin备用方案也失败: {str(simfin_error)}")
                return ""

        # 格式化AKShare数据
        if not data.empty:
            # 获取最新的报告日期
            report_date = datetime.now().strftime("%Y-%m-%d")
            if "报告期" in data.columns:
                report_date = str(data["报告期"].iloc[0])[:10]

            return (
                f"## {freq} balance sheet for {ticker} (AKShare data): \n"
                + str(data.to_string())
                + f"\n\nData source: AKShare. Report date: {report_date}. "
                + "This includes metadata like reporting dates and currency, share details, and a breakdown of assets, liabilities, and equity. Assets are grouped as current (liquid items like cash and receivables) and noncurrent (long-term investments and property). Liabilities are split between short-term obligations and long-term debts, while equity reflects shareholder funds such as paid-in capital and retained earnings. Together, these components ensure that total assets equal the sum of liabilities and equity."
            )
        else:
            return ""

    except Exception as e:
        print(f"获取资产负债表时出错: {str(e)}")
        return ""


def get_simfin_cashflow(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency of the company's financial history: annual / quarterly",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    """
    使用AKShare获取现金流量表数据，替代SimFin
    """
    try:
        print(f"使用AKShare获取现金流量表: {ticker} ({freq})")

        # 映射频率参数
        period_mapping = {"annual": "年报", "quarterly": "季报"}
        period = period_mapping.get(freq, "年报")

        # 使用AKShare获取数据
        data = get_akshare_cash_flow(ticker, period)

        if data.empty:
            print(f"AKShare未找到数据，尝试使用原始SimFin方法")
            # 备用方案：使用原始SimFin方法
            try:
                data_path = os.path.join(
                    DATA_DIR,
                    "fundamental_data",
                    "simfin_data_all",
                    "cash_flow",
                    "companies",
                    "us",
                    f"us-cashflow-{freq}.csv",
                )
                df = pd.read_csv(data_path, sep=";")

                # Convert date strings to datetime objects and remove any time components
                df["Report Date"] = pd.to_datetime(
                    df["Report Date"], utc=True
                ).dt.normalize()
                df["Publish Date"] = pd.to_datetime(
                    df["Publish Date"], utc=True
                ).dt.normalize()

                # Convert the current date to datetime and normalize
                curr_date_dt = pd.to_datetime(curr_date, utc=True).normalize()

                # Filter the DataFrame for the given ticker and for reports that were published on or before the current date
                filtered_df = df[
                    (df["Ticker"] == ticker) & (df["Publish Date"] <= curr_date_dt)
                ]

                # Check if there are any available reports; if not, return a notification
                if filtered_df.empty:
                    print(
                        "No cash flow statement available before the given current date."
                    )
                    return ""

                # Get the most recent cash flow statement by selecting the row with the latest Publish Date
                latest_cash_flow = filtered_df.loc[filtered_df["Publish Date"].idxmax()]

                # drop the SimFinID column
                if "SimFinId" in latest_cash_flow.index:
                    latest_cash_flow = latest_cash_flow.drop("SimFinId")

                return (
                    f"## {freq} cash flow statement for {ticker} released on {str(latest_cash_flow['Publish Date'])[0:10]}: \n"
                    + str(latest_cash_flow)
                    + "\n\nThis includes metadata like reporting dates and currency, share details, and a breakdown of cash movements. Operating activities show cash generated from core business operations, including net income adjustments for non-cash items and working capital changes. Investing activities cover asset acquisitions/disposals and investments. Financing activities include debt transactions, equity issuances/repurchases, and dividend payments. The net change in cash represents the overall increase or decrease in the company's cash position during the reporting period."
                )
            except Exception as simfin_error:
                print(f"SimFin备用方案也失败: {str(simfin_error)}")
                return ""

        # 格式化AKShare数据
        if not data.empty:
            # 获取最新的报告日期
            report_date = datetime.now().strftime("%Y-%m-%d")
            if "报告期" in data.columns:
                report_date = str(data["报告期"].iloc[0])[:10]

            return (
                f"## {freq} cash flow statement for {ticker} (AKShare data): \n"
                + str(data.to_string())
                + f"\n\nData source: AKShare. Report date: {report_date}. "
                + "This includes metadata like reporting dates and currency, share details, and a breakdown of cash movements. Operating activities show cash generated from core business operations, including net income adjustments for non-cash items and working capital changes. Investing activities cover asset acquisitions/disposals and investments. Financing activities include debt transactions, equity issuances/repurchases, and dividend payments. The net change in cash represents the overall increase or decrease in the company's cash position during the reporting period."
            )
        else:
            return ""

    except Exception as e:
        print(f"获取现金流量表时出错: {str(e)}")
        return ""


def get_simfin_income_statements(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency of the company's financial history: annual / quarterly",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    data_path = os.path.join(
        DATA_DIR,
        "fundamental_data",
        "simfin_data_all",
        "income_statements",
        "companies",
        "us",
        f"us-income-{freq}.csv",
    )
    df = pd.read_csv(data_path, sep=";")

    # Convert date strings to datetime objects and remove any time components
    df["Report Date"] = pd.to_datetime(df["Report Date"], utc=True).dt.normalize()
    df["Publish Date"] = pd.to_datetime(df["Publish Date"], utc=True).dt.normalize()

    # Convert the current date to datetime and normalize
    curr_date_dt = pd.to_datetime(curr_date, utc=True).normalize()

    # Filter the DataFrame for the given ticker and for reports that were published on or before the current date
    filtered_df = df[(df["Ticker"] == ticker) & (df["Publish Date"] <= curr_date_dt)]

    # Check if there are any available reports; if not, return a notification
    if filtered_df.empty:
        print("No income statement available before the given current date.")
        return ""

    # Get the most recent income statement by selecting the row with the latest Publish Date
    latest_income = filtered_df.loc[filtered_df["Publish Date"].idxmax()]

    # drop the SimFinID column
    latest_income = latest_income.drop("SimFinId")

    return (
        f"## {freq} income statement for {ticker} released on {str(latest_income['Publish Date'])[0:10]}: \n"
        + str(latest_income)
        + "\n\nThis includes metadata like reporting dates and currency, share details, and a comprehensive breakdown of the company's financial performance. Starting with Revenue, it shows Cost of Revenue and resulting Gross Profit. Operating Expenses are detailed, including SG&A, R&D, and Depreciation. The statement then shows Operating Income, followed by non-operating items and Interest Expense, leading to Pretax Income. After accounting for Income Tax and any Extraordinary items, it concludes with Net Income, representing the company's bottom-line profit or loss for the period."
    )


def get_google_news(
    query: Annotated[str, "Query to search with"],
    curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    query = query.replace(" ", "+")

    start_date = datetime.strptime(curr_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    news_results = getNewsData(query, before, curr_date)

    news_str = ""

    for news in news_results:
        news_str += (
            f"### {news['title']} (source: {news['source']}) \n\n{news['snippet']}\n\n"
        )

    if len(news_results) == 0:
        return ""

    return f"## {query} Google News, from {before} to {curr_date}:\n\n{news_str}"


def get_reddit_global_news(
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
    max_limit_per_day: Annotated[int, "Maximum number of news per day"],
) -> str:
    """
    Retrieve the latest top reddit news
    Args:
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
    Returns:
        str: A formatted dataframe containing the latest news articles posts on reddit and meta information in these columns: "created_utc", "id", "title", "selftext", "score", "num_comments", "url"
    """

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    posts = []
    # iterate from start_date to end_date
    curr_date = datetime.strptime(before, "%Y-%m-%d")

    total_iterations = (start_date - curr_date).days + 1
    pbar = tqdm(desc=f"Getting Global News on {start_date}", total=total_iterations)

    while curr_date <= start_date:
        curr_date_str = curr_date.strftime("%Y-%m-%d")
        fetch_result = fetch_top_from_category(
            "global_news",
            curr_date_str,
            max_limit_per_day,
            data_path=os.path.join(DATA_DIR, "reddit_data"),
        )
        posts.extend(fetch_result)
        curr_date += relativedelta(days=1)
        pbar.update(1)

    pbar.close()

    if len(posts) == 0:
        return ""

    news_str = ""
    for post in posts:
        if post["content"] == "":
            news_str += f"### {post['title']}\n\n"
        else:
            news_str += f"### {post['title']}\n\n{post['content']}\n\n"

    return f"## Global News Reddit, from {before} to {curr_date}:\n{news_str}"


def get_reddit_company_news(
    ticker: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
    max_limit_per_day: Annotated[int, "Maximum number of news per day"],
) -> str:
    """
    Retrieve the latest top reddit news
    Args:
        ticker: ticker symbol of the company
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
    Returns:
        str: A formatted dataframe containing the latest news articles posts on reddit and meta information in these columns: "created_utc", "id", "title", "selftext", "score", "num_comments", "url"
    """

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    posts = []
    # iterate from start_date to end_date
    curr_date = datetime.strptime(before, "%Y-%m-%d")

    total_iterations = (start_date - curr_date).days + 1
    pbar = tqdm(
        desc=f"Getting Company News for {ticker} on {start_date}",
        total=total_iterations,
    )

    while curr_date <= start_date:
        curr_date_str = curr_date.strftime("%Y-%m-%d")
        fetch_result = fetch_top_from_category(
            "company_news",
            curr_date_str,
            max_limit_per_day,
            ticker,
            data_path=os.path.join(DATA_DIR, "reddit_data"),
        )
        posts.extend(fetch_result)
        curr_date += relativedelta(days=1)

        pbar.update(1)

    pbar.close()

    if len(posts) == 0:
        return ""

    news_str = ""
    for post in posts:
        if post["content"] == "":
            news_str += f"### {post['title']}\n\n"
        else:
            news_str += f"### {post['title']}\n\n{post['content']}\n\n"

    return f"##{ticker} News Reddit, from {before} to {curr_date}:\n\n{news_str}"


def get_stock_stats_indicators_window(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[
        str, "The current trading date you are trading on, YYYY-mm-dd"
    ],
    look_back_days: Annotated[int, "how many days to look back"],
    online: Annotated[bool, "to fetch data online or offline"],
) -> str:

    best_ind_params = {
        # Moving Averages
        "close_50_sma": (
            "50 SMA: A medium-term trend indicator. "
            "Usage: Identify trend direction and serve as dynamic support/resistance. "
            "Tips: It lags price; combine with faster indicators for timely signals."
        ),
        "close_200_sma": (
            "200 SMA: A long-term trend benchmark. "
            "Usage: Confirm overall market trend and identify golden/death cross setups. "
            "Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries."
        ),
        "close_10_ema": (
            "10 EMA: A responsive short-term average. "
            "Usage: Capture quick shifts in momentum and potential entry points. "
            "Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals."
        ),
        # MACD Related
        "macd": (
            "MACD: Computes momentum via differences of EMAs. "
            "Usage: Look for crossovers and divergence as signals of trend changes. "
            "Tips: Confirm with other indicators in low-volatility or sideways markets."
        ),
        "macds": (
            "MACD Signal: An EMA smoothing of the MACD line. "
            "Usage: Use crossovers with the MACD line to trigger trades. "
            "Tips: Should be part of a broader strategy to avoid false positives."
        ),
        "macdh": (
            "MACD Histogram: Shows the gap between the MACD line and its signal. "
            "Usage: Visualize momentum strength and spot divergence early. "
            "Tips: Can be volatile; complement with additional filters in fast-moving markets."
        ),
        # Momentum Indicators
        "rsi": (
            "RSI: Measures momentum to flag overbought/oversold conditions. "
            "Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. "
            "Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis."
        ),
        # Volatility Indicators
        "boll": (
            "Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. "
            "Usage: Acts as a dynamic benchmark for price movement. "
            "Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals."
        ),
        "boll_ub": (
            "Bollinger Upper Band: Typically 2 standard deviations above the middle line. "
            "Usage: Signals potential overbought conditions and breakout zones. "
            "Tips: Confirm signals with other tools; prices may ride the band in strong trends."
        ),
        "boll_lb": (
            "Bollinger Lower Band: Typically 2 standard deviations below the middle line. "
            "Usage: Indicates potential oversold conditions. "
            "Tips: Use additional analysis to avoid false reversal signals."
        ),
        "atr": (
            "ATR: Averages true range to measure volatility. "
            "Usage: Set stop-loss levels and adjust position sizes based on current market volatility. "
            "Tips: It's a reactive measure, so use it as part of a broader risk management strategy."
        ),
        # Volume-Based Indicators
        "vwma": (
            "VWMA: A moving average weighted by volume. "
            "Usage: Confirm trends by integrating price action with volume data. "
            "Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses."
        ),
        "mfi": (
            "MFI: The Money Flow Index is a momentum indicator that uses both price and volume to measure buying and selling pressure. "
            "Usage: Identify overbought (>80) or oversold (<20) conditions and confirm the strength of trends or reversals. "
            "Tips: Use alongside RSI or MACD to confirm signals; divergence between price and MFI can indicate potential reversals."
        ),
    }

    if indicator not in best_ind_params:
        raise ValueError(
            f"Indicator {indicator} is not supported. Please choose from: {list(best_ind_params.keys())}"
        )

    end_date = curr_date
    curr_date = datetime.strptime(curr_date, "%Y-%m-%d")
    before = curr_date - relativedelta(days=look_back_days)

    if not online:
        # read from YFin data
        data = pd.read_csv(
            os.path.join(
                DATA_DIR,
                f"market_data/price_data/{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
            )
        )
        data["Date"] = pd.to_datetime(data["Date"], utc=True)
        dates_in_df = data["Date"].astype(str).str[:10]

        ind_string = ""
        while curr_date >= before:
            # only do the trading dates
            if curr_date.strftime("%Y-%m-%d") in dates_in_df.values:
                indicator_value = get_stockstats_indicator(
                    symbol, indicator, curr_date.strftime("%Y-%m-%d"), online
                )

                ind_string += f"{curr_date.strftime('%Y-%m-%d')}: {indicator_value}\n"

            curr_date = curr_date - relativedelta(days=1)
    else:
        # online gathering
        ind_string = ""
        while curr_date >= before:
            indicator_value = get_stockstats_indicator(
                symbol, indicator, curr_date.strftime("%Y-%m-%d"), online
            )

            ind_string += f"{curr_date.strftime('%Y-%m-%d')}: {indicator_value}\n"

            curr_date = curr_date - relativedelta(days=1)

    result_str = (
        f"## {indicator} values from {before.strftime('%Y-%m-%d')} to {end_date}:\n\n"
        + ind_string
        + "\n\n"
        + best_ind_params.get(indicator, "No description available.")
    )

    return result_str


def get_stockstats_indicator(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[
        str, "The current trading date you are trading on, YYYY-mm-dd"
    ],
    online: Annotated[bool, "to fetch data online or offline"],
) -> str:

    curr_date = datetime.strptime(curr_date, "%Y-%m-%d")
    curr_date = curr_date.strftime("%Y-%m-%d")

    try:
        indicator_value = StockstatsUtils.get_stock_stats(
            symbol,
            indicator,
            curr_date,
            os.path.join(DATA_DIR, "market_data", "price_data"),
            online=online,
        )
    except Exception as e:
        print(
            f"Error getting stockstats indicator data for indicator {indicator} on {curr_date}: {e}"
        )
        return ""

    return str(indicator_value)


def get_YFin_data_window(
    symbol: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    # calculate past days
    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
    before = date_obj - relativedelta(days=look_back_days)
    start_date = before.strftime("%Y-%m-%d")

    # read in data
    data = pd.read_csv(
        os.path.join(
            DATA_DIR,
            f"market_data/price_data/{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
        )
    )

    # Extract just the date part for comparison
    data["DateOnly"] = data["Date"].str[:10]

    # Filter data between the start and end dates (inclusive)
    filtered_data = data[
        (data["DateOnly"] >= start_date) & (data["DateOnly"] <= curr_date)
    ]

    # Drop the temporary column we created
    filtered_data = filtered_data.drop("DateOnly", axis=1)

    # Set pandas display options to show the full DataFrame
    with pd.option_context(
        "display.max_rows", None, "display.max_columns", None, "display.width", None
    ):
        df_string = filtered_data.to_string()

    return (
        f"## Raw Market Data for {symbol} from {start_date} to {curr_date}:\n\n"
        + df_string
    )


def get_YFin_data_online(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
):
    """
    使用AKShare获取股票历史数据，替代YFinance
    """
    try:
        print(f"使用AKShare获取股票数据: {symbol} from {start_date} to {end_date}")

        # 验证日期格式
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")

        # 使用AKShare获取数据
        data = get_akshare_stock_data(symbol, start_date, end_date)

        # 检查数据是否为空
        if data.empty:
            print(f"AKShare未找到数据，尝试使用YFinance作为备用")
            # 备用方案：使用YFinance
            ticker = yf.Ticker(symbol.upper())
            data = ticker.history(start=start_date, end=end_date)

            if data.empty:
                return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

        # 确保数据格式一致
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)

        # 标准化列名以保持兼容性
        column_mapping = {
            "Open": "Open",
            "High": "High",
            "Low": "Low",
            "Close": "Close",
            "Volume": "Volume",
        }

        # 如果没有Adj Close列，使用Close列
        if "Adj Close" not in data.columns and "Close" in data.columns:
            data["Adj Close"] = data["Close"]

        # 四舍五入数值
        numeric_columns = ["Open", "High", "Low", "Close", "Adj Close"]
        for col in numeric_columns:
            if col in data.columns:
                data[col] = data[col].round(2)

        # 转换为CSV字符串
        csv_string = data.to_csv()

        # 添加头部信息
        header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
        header += f"# Total records: {len(data)}\n"
        header += (
            f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        header += f"# Data source: AKShare\n\n"

        return header + csv_string

    except Exception as e:
        print(f"获取股票数据时出错: {str(e)}")
        # 如果AKShare失败，尝试使用原始的YFinance方法
        try:
            ticker = yf.Ticker(symbol.upper())
            data = ticker.history(start=start_date, end=end_date)

            if data.empty:
                return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

            if data.index.tz is not None:
                data.index = data.index.tz_localize(None)

            numeric_columns = ["Open", "High", "Low", "Close", "Adj Close"]
            for col in numeric_columns:
                if col in data.columns:
                    data[col] = data[col].round(2)

            csv_string = data.to_csv()
            header = (
                f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
            )
            header += f"# Total records: {len(data)}\n"
            header += (
                f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            header += f"# Data source: YFinance (fallback)\n\n"

            return header + csv_string

        except Exception as fallback_error:
            return f"Error retrieving data for symbol '{symbol}': {str(fallback_error)}"


def get_YFin_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    # read in data
    data = pd.read_csv(
        os.path.join(
            DATA_DIR,
            f"market_data/price_data/{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
        )
    )

    if end_date > "2025-03-25":
        raise Exception(
            f"Get_YFin_Data: {end_date} is outside of the data range of 2015-01-01 to 2025-03-25"
        )

    # Extract just the date part for comparison
    data["DateOnly"] = data["Date"].str[:10]

    # Filter data between the start and end dates (inclusive)
    filtered_data = data[
        (data["DateOnly"] >= start_date) & (data["DateOnly"] <= end_date)
    ]

    # Drop the temporary column we created
    filtered_data = filtered_data.drop("DateOnly", axis=1)

    # remove the index from the dataframe
    filtered_data = filtered_data.reset_index(drop=True)

    return filtered_data


async def get_stock_news_openai(ticker, curr_date):
    """
    获取股票社交媒体新闻，使用 Tavily MCP 获取实时数据
    """
    query = f"你可以搜索从{curr_date}前7天到{curr_date}期间的社交媒体上关于{ticker}的内容吗？请确保仅获取该时间段内发布的数据。"
    return await _execute_mcp_query(query, f"股票{ticker}社交媒体新闻查询")


async def get_global_news_openai(curr_date):
    """
    获取全球宏观经济新闻，使用 Tavily MCP 获取实时数据
    """
    query = f"请搜索从 ​​{curr_date} 前7天​​ 到 ​​{curr_date}​​ 期间对交易有参考价值的全球宏观经济新闻。重点关注以下内容：,​央行决策​​（利率决议、货币政策声明等）,​​经济指标​​（PMI、零售销售、工业产出等）,​​通胀数据​​（CPI、PPI等）,​​GDP报告​​（季度或年度经济增长数据）,​​就业数据​​（非农就业、失业率等）,​​重大经济政策公告​​（财政刺激、贸易政策等）"
    return await _execute_mcp_query(query, "全球宏观经济新闻查询")


async def get_fundamentals_openai(ticker, curr_date):
    """
    获取股票基本面分析数据，使用 Tavily MCP 获取实时数据
    """
    query = f"搜索{ticker}从{curr_date}前一个月到{curr_date}的基本面分析和财务数据。包括财报、财务报表、分析师评级、市盈率(PE)、市销率(PS)、现金流数据、营收增长、利润率等关键财务指标"
    return await _execute_mcp_query(query, f"股票{ticker}基本面分析查询")
