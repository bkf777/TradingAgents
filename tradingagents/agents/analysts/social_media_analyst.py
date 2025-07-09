from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json


def create_social_media_analyst(llm, toolkit):
    def social_media_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        if toolkit.config["online_tools"]:
            tools = [toolkit.get_stock_news_openai]
        else:
            tools = [
                toolkit.get_reddit_stock_info,
            ]

        system_message = (
            "你是一位社交媒体和公司特定新闻研究员/分析师，负责分析过去一周特定公司的社交媒体帖子、最新公司新闻和公众情绪。你将获得一个公司的名称，你的目标是撰写一份全面详细的长篇报告，详述你的分析、见解以及对交易者和投资者的影响，内容基于查看社交媒体和人们对该公司的评论，分析人们每天对该公司的情感数据，以及查看最近的公司新闻。尝试查看所有可能的来源，从社交媒体到情感再到新闻。不要简单地表述趋势是混合的，提供详细和精细的分析和见解，这可能有助于交易者做出决策。"
            + """ 确保在报告末尾附加一个Markdown表格，以组织报告中的要点，使其条理清晰且易于阅读。""",
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
            "sentiment_report": report,
        }

    return social_media_analyst_node
