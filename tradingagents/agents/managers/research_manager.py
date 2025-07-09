import time
import json


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        investment_debate_state = state["investment_debate_state"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""作为投资组合经理和辩论主持人，你的角色是批判性地评估本轮辩论并做出明确决定：与看空分析师一致，与看多分析师一致，或者仅在基于所提出的论据有强有力的理由时选择持有。

简明扼要地总结双方的关键点，重点关注最有说服力的证据或推理。你的建议——买入、卖出或持有——必须清晰且可行。避免仅仅因为双方都有有效观点而默认选择持有；要基于辩论中最有力的论据做出立场。

此外，为交易员制定详细的投资计划。这应包括：

你的建议：由最有说服力的论据支持的明确立场。
理由：解释为什么这些论据导致你的结论。
战略行动：实施建议的具体步骤。
考虑你在类似情况下的过去错误。利用这些见解完善你的决策过程，确保你在学习和进步。以对话方式呈现你的分析，就像自然交谈一样，不使用特殊格式。

以下是你对过去错误的反思：
\"{past_memory_str}\"

以下是辩论内容：
辩论历史：
{history}"""
        response = llm.invoke(prompt)

        new_investment_debate_state = {
            "judge_decision": response.content,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": response.content,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": response.content,
        }

    return research_manager_node
