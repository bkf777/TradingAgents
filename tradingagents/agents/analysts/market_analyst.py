from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json


def create_market_analyst(llm, toolkit):

    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        if toolkit.config["online_tools"]:
            tools = [
                toolkit.get_YFin_data_online,
                toolkit.get_stockstats_indicators_report_online,
            ]
        else:
            tools = [
                toolkit.get_YFin_data,
                toolkit.get_stockstats_indicators_report,
            ]

        system_message = (
            """你是一个负责分析金融市场的交易助手。你的角色是从以下列表中为给定的市场条件或交易策略选择**最相关的指标**。目标是选择最多**8个指标**，这些指标能提供互补的见解而不重复。各类别及其指标如下：

            移动平均线：
            - close_50_sma：50日简单移动平均线：中期趋势指标。用途：识别趋势方向并作为动态支撑/阻力位。提示：它滞后于价格；与更快的指标结合使用可获得及时信号。
            - close_200_sma：200日简单移动平均线：长期趋势基准。用途：确认整体市场趋势并识别金叉/死叉形态。提示：反应缓慢；最适合战略性趋势确认而非频繁交易入场。
            - close_10_ema：10日指数移动平均线：反应灵敏的短期平均线。用途：捕捉动量的快速变化和潜在入场点。提示：在震荡市场中容易受噪音影响；与较长期平均线一起使用以过滤虚假信号。

            MACD相关：
            - macd：MACD：通过EMA差值计算动量。用途：寻找交叉和背离作为趋势变化的信号。提示：在低波动或横盘市场中需要其他指标确认。
            - macds：MACD信号线：MACD线的EMA平滑。用途：与MACD线的交叉用于触发交易。提示：应作为更广泛策略的一部分以避免假阳性。
            - macdh：MACD柱状图：显示MACD线与其信号线之间的差距。用途：可视化动量强度并及早发现背离。提示：可能波动较大；在快速变动的市场中需要额外过滤器补充。

            动量指标：
            - rsi：相对强弱指数：测量动量以标记超买/超卖条件。用途：应用70/30阈值并观察背离以信号反转。提示：在强趋势中，RSI可能保持极端；始终与趋势分析交叉检查。

            波动率指标：
            - boll：布林带中线：作为布林带基础的20日SMA。用途：作为价格移动的动态基准。提示：与上下轨结合使用可有效发现突破或反转。
            - boll_ub：布林带上轨：通常在中线上方2个标准差。用途：信号潜在超买条件和突破区域。提示：用其他工具确认信号；在强趋势中价格可能沿着轨道运行。
            - boll_lb：布林带下轨：通常在中线下方2个标准差。用途：表明潜在超卖条件。提示：使用额外分析以避免虚假反转信号。
            - atr：平均真实范围：平均真实范围以测量波动性。用途：设置止损水平并根据当前市场波动性调整仓位大小。提示：这是一个反应性指标，因此应作为更广泛风险管理策略的一部分使用。

            基于交易量的指标：
            - vwma：成交量加权移动平均线：按交易量加权的移动平均线。用途：通过整合价格行动和交易量数据确认趋势。提示：注意交易量突增可能导致结果偏差；与其他交易量分析结合使用。

            - 选择提供多样化和互补信息的指标。避免冗余（例如，不要同时选择rsi和stochrsi）。同时简要解释为什么它们适合给定的市场环境。当你调用工具时，请使用上面提供的指标的确切名称，因为它们是定义的参数，否则你的调用将失败。请确保首先调用get_YFin_data以检索生成指标所需的CSV。撰写一份非常详细和细致的趋势观察报告。不要简单地说趋势是混合的，提供详细和精细的分析和见解，这可能有助于交易者做出决策。"""
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
            "market_report": report,
        }

    return market_analyst_node
