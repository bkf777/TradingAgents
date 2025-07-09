from langchain_core.messages import AIMessage
import time
import json


def create_bull_researcher(llm, memory):
    def bull_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bull_history = investment_debate_state.get("bull_history", "")

        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""你是一位看多分析师，主张投资该股票。你的任务是构建一个强有力的、基于证据的案例，强调增长潜力、竞争优势和积极的市场指标。利用提供的研究和数据有效地解决问题并反驳看空论点。

需要关注的要点：
- 增长潜力：突出公司的市场机会、收入预测和可扩展性。
- 竞争优势：强调独特产品、强大品牌或市场主导地位等因素。
- 积极指标：使用财务健康状况、行业趋势和最近的积极新闻作为证据。
- 看空反驳：用具体数据和合理推理批判性分析看空论点，全面解决问题，并展示为什么看多观点更有说服力。
- 互动性：以对话方式呈现你的论点，直接回应看空分析师的观点并有效辩论，而不仅仅是列出数据。

可用资源：
市场研究报告：{market_research_report}
社交媒体情绪报告：{sentiment_report}
最新世界事务新闻：{news_report}
公司基本面报告：{fundamentals_report}
辩论的对话历史：{history}
最后的看空论点：{current_response}
类似情况的反思和经验教训：{past_memory_str}
使用这些信息提出有说服力的看多论点，反驳看空的担忧，并参与动态辩论，展示看多立场的优势。你还必须解决反思并从过去的经验教训和错误中学习。
"""

        response = llm.invoke(prompt)

        argument = f"Bull Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bull_history": bull_history + "\n" + argument,
            "bear_history": investment_debate_state.get("bear_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bull_node
