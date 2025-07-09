from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json


def create_news_analyst(llm, toolkit):
    def news_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        if toolkit.config["online_tools"]:
            tools = [toolkit.get_global_news_openai, toolkit.get_google_news]
        else:
            tools = [
                toolkit.get_finnhub_news,
                toolkit.get_reddit_news,
                toolkit.get_google_news,
            ]

        system_message = (
            "你是一位新闻研究员，负责分析过去一周的最新新闻和趋势。请撰写一份关于与交易和宏观经济相关的当前世界状况的综合报告。查看来自EODHD和Finnhub的新闻以确保全面性。不要简单地表述趋势是混合的，提供详细和精细的分析和见解，这可能有助于交易者做出决策。"
            + """ 确保在报告末尾附加一个Markdown表格，以组织报告中的要点，使其条理清晰且易于阅读。"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                       "system",
                        "你是一个乐于助人的AI助手，与其他助手协作完成任务。"
                        " 使用提供的工具逐步解答问题。"
                        " 如果无法完全解答，没关系；其他具备不同工具的助手会接手未完成的部分。"
                        " 尽可能执行操作以推动进展。"
                        " 如果你或其他助手得出最终交易建议：**买入/持有/卖出** 或可交付成果，"
                        " 请在回复前加上 FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** 以便团队知晓停止讨论。"
                        " 你可使用的工具包括：{tool_names}。\n{system_message}"
                        "当前日期为 {current_date}，我们关注的公司是 {ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "news_report": report,
        }

    return news_analyst_node
