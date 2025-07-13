#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingAgents 简化版 API 服务器
只提供股票分析功能的REST API接口
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import traceback
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# 导入TradingAgents相关模块
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# 导入数据库相关模块
db_manager = None
message_manager = None

# 连接MySQL数据库
try:
    from database_config import DatabaseManager, MessageManager, get_db_config

    db_manager = DatabaseManager(get_db_config())
    message_manager = MessageManager(db_manager)
    print("✅ MySQL数据库连接成功")
except Exception as e:
    print(f"❌ MySQL数据库连接失败: {e}")
    print("⚠️ 分析结果将不会保存到数据库")
    db_manager = None
    message_manager = None


def make_json_serializable(obj):
    """
    将包含LangChain消息对象的数据结构转换为JSON可序列化的格式

    Args:
        obj: 需要序列化的对象

    Returns:
        JSON可序列化的对象
    """
    if obj is None:
        return None

    # 处理字典类型
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            result[key] = make_json_serializable(value)
        return result

    # 处理列表类型
    elif isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]

    # 处理LangChain消息对象
    elif hasattr(obj, "content") and hasattr(obj, "type"):
        return {
            "type": obj.type,
            "content": str(obj.content),
            "timestamp": datetime.now().isoformat(),
        }

    # 处理其他有__dict__属性的对象
    elif hasattr(obj, "__dict__"):
        return make_json_serializable(obj.__dict__)

    # 处理基本数据类型
    elif isinstance(obj, (str, int, float, bool)):
        return obj

    # 处理datetime对象
    elif isinstance(obj, datetime):
        return obj.isoformat()

    # 其他情况转换为字符串
    else:
        return str(obj)


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("api_server.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 启用跨域支持


# 参数格式化函数
def format_task_parameters_for_analysis(
    task_data: Dict[str, Any], provided_date: str = None
) -> tuple:
    """
    将数据库中的task数据格式化为TradingAgentsGraph.propagate()方法需要的参数格式

    Args:
        task_data: 从数据库获取的task数据字典
        provided_date: 用户提供的具体分析日期（可选）

    Returns:
        tuple: (symbol, analysis_date) 格式化后的参数
    """
    try:
        # 获取股票代码（ticker字段）
        symbol = task_data.get("ticker", "").upper()
        if not symbol:
            raise ValueError("task数据中缺少ticker字段")

        # 处理分析日期
        analysis_date = None

        # 1. 如果用户提供了具体日期，优先使用
        if provided_date:
            analysis_date = provided_date
            print(f"📅 使用用户提供的分析日期: {analysis_date}")
        else:
            # 2. 如果没有提供日期，根据analysis_period生成合适的日期
            analysis_period = task_data.get("analysis_period", "1m")

            # 根据分析周期计算合适的分析日期
            # 对于股票分析，通常使用最近的交易日
            today = datetime.now()

            # 简单处理：使用今天的日期，格式为YYYY-MM-DD
            # 在实际应用中，可能需要考虑交易日历，排除周末和节假日
            analysis_date = today.strftime("%Y-%m-%d")

            print(f"📅 根据分析周期 '{analysis_period}' 生成分析日期: {analysis_date}")

        # 验证参数
        if not symbol or not analysis_date:
            raise ValueError(
                f"参数格式化失败: symbol='{symbol}', analysis_date='{analysis_date}'"
            )

        print(f"✅ 参数格式化成功: symbol='{symbol}', analysis_date='{analysis_date}'")
        return symbol, analysis_date

    except Exception as e:
        error_msg = f"参数格式化失败: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"❌ task_data: {task_data}")
        raise ValueError(error_msg)


def validate_task_data_for_analysis(task_data: Dict[str, Any]) -> bool:
    """
    验证task数据是否包含分析所需的必要字段

    Args:
        task_data: 从数据库获取的task数据字典

    Returns:
        bool: 验证是否通过
    """
    try:
        required_fields = ["ticker", "task_id"]
        missing_fields = []

        for field in required_fields:
            if field not in task_data or not task_data[field]:
                missing_fields.append(field)

        if missing_fields:
            print(f"❌ task数据验证失败，缺少必要字段: {missing_fields}")
            return False

        # 验证ticker格式（基本验证）
        ticker = task_data["ticker"].strip()
        if len(ticker) == 0:
            print(f"❌ ticker字段为空")
            return False

        print(
            f"✅ task数据验证通过: ticker='{ticker}', task_id='{task_data['task_id']}'"
        )
        return True

    except Exception as e:
        print(f"❌ task数据验证异常: {str(e)}")
        return False


# 错误处理函数
def handle_error(error: Exception, operation: str, **kwargs) -> tuple:
    """统一错误处理函数"""
    error_msg = str(error)
    error_trace = traceback.format_exc()

    # 记录错误日志
    logger.error(f"操作失败: {operation}")
    logger.error(f"错误信息: {error_msg}")
    logger.error(f"错误详情: {error_trace}")

    # 打印错误信息到控制台
    print(f"\n{'='*50}")
    print(f"❌ 错误发生时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"❌ 操作: {operation}")
    print(f"❌ 错误类型: {type(error).__name__}")
    print(f"❌ 错误信息: {error_msg}")

    if kwargs:
        print(f"❌ 上下文信息:")
        for key, value in kwargs.items():
            print(f"   - {key}: {value}")

    print(f"❌ 错误堆栈:")
    for line in error_trace.split("\n"):
        if line.strip():
            print(f"   {line}")
    print(f"{'='*50}\n")

    return {
        "success": False,
        "message": f"操作失败: {error_msg}",
        "error_type": type(error).__name__,
        "timestamp": datetime.now().isoformat(),
    }, 500


# 全局配置
DEFAULT_API_CONFIG = DEFAULT_CONFIG.copy()
DEFAULT_API_CONFIG.update(
    {
        "llm_provider": "openai",
        "backend_url": "https://api.nuwaapi.com/v1",
        "deep_think_llm": "o3-mini-high",
        "quick_think_llm": "o3-mini-high",
        "max_debate_rounds": 1,
        "online_tools": True,
        "reset_memory_collections": False,
    }
)


@app.route("/analyze", methods=["POST"])
def analyze():
    """执行股票分析 - 支持两种模式：
    1. 直接提供symbol和date参数
    2. 提供task_id，从数据库获取task数据并格式化参数
    """
    symbol = None
    analysis_date = None
    conversation_id = None
    task_id = None
    custom_config = {}
    task_data = None

    try:
        data = request.get_json()

        # 获取基本参数
        provided_symbol = data.get("symbol")
        provided_date = data.get("date")
        conversation_id = data.get("conversation_id")
        task_id = data.get("task_id")
        custom_config = data.get("config", {})

        print(f"🔍 收到分析请求:")
        print(f"   - 提供的symbol: {provided_symbol}")
        print(f"   - 提供的date: {provided_date}")
        print(f"   - 会话ID: {conversation_id}")
        print(f"   - 任务ID: {task_id}")

        # 参数处理逻辑：支持两种模式
        if task_id and db_manager:
            # 模式1: 从数据库获取task数据
            print(f"📋 模式1: 从数据库获取task数据 (task_id: {task_id})")

            try:
                # 从数据库获取task数据
                task_query = "SELECT * FROM tasks WHERE task_id = %s"
                task_results = db_manager.execute_query(task_query, (task_id,))

                if not task_results:
                    error_msg = f"未找到task_id为 '{task_id}' 的任务"
                    print(f"❌ {error_msg}")
                    return jsonify({"success": False, "message": error_msg}), 404

                task_data = task_results[0]
                print(
                    f"✅ 成功获取task数据: {task_data['ticker']} - {task_data['title']}"
                )

                # 验证task数据
                if not validate_task_data_for_analysis(task_data):
                    error_msg = f"task数据验证失败，无法进行分析"
                    print(f"❌ {error_msg}")
                    return jsonify({"success": False, "message": error_msg}), 400

                # 格式化参数
                symbol, analysis_date = format_task_parameters_for_analysis(
                    task_data, provided_date
                )

                # 如果没有提供task_id，使用数据库中的task_id
                if not task_id:
                    task_id = task_data["task_id"]

            except Exception as db_error:
                error_msg = f"从数据库获取task数据失败: {str(db_error)}"
                print(f"❌ {error_msg}")
                return jsonify({"success": False, "message": error_msg}), 500

        elif provided_symbol and provided_date:
            # 模式2: 直接使用提供的参数
            print(f"📋 模式2: 使用直接提供的参数")
            symbol = provided_symbol
            analysis_date = provided_date

        else:
            # 参数不足
            error_msg = "参数不足: 请提供 (symbol + date) 或 task_id"
            print(f"❌ {error_msg}")
            return jsonify({"success": False, "message": error_msg}), 400

        # 验证最终参数
        if not symbol or not analysis_date:
            error_msg = (
                f"参数处理失败: symbol='{symbol}', analysis_date='{analysis_date}'"
            )
            print(f"❌ {error_msg}")
            return jsonify({"success": False, "message": error_msg}), 400

        print(
            f"✅ 最终分析参数: symbol='{symbol}', analysis_date='{analysis_date}', task_id='{task_id}'"
        )

        logger.info(
            f"执行股票分析: symbol={symbol}, analysis_date={analysis_date}, conversation_id={conversation_id}, task_id={task_id}, custom_config={custom_config}"
        )

        # 如果没有提供conversation_id，生成一个默认的
        if not conversation_id:
            conversation_id = (
                f"analysis_{symbol}_{analysis_date}_{datetime.now().strftime('%H%M%S')}"
            )
            print(f"📝 生成会话ID: {conversation_id}")

        # 如果没有提供task_id，生成一个默认的
        if not task_id:
            task_id = (
                f"task_{symbol}_{analysis_date}_{datetime.now().strftime('%H%M%S')}"
            )
            print(f"📝 生成任务ID: {task_id}")
        else:
            print(f"📝 使用提供的任务ID: {task_id}")

        # 创建配置
        config = DEFAULT_API_CONFIG.copy()
        config.update(custom_config)
        print(
            f"📋 使用配置: LLM={config['llm_provider']}, 模型={config['quick_think_llm']}"
        )

        # 初始化TradingAgentsGraph
        print(f"🚀 初始化TradingAgentsGraph...")
        ta = TradingAgentsGraph(debug=True, config=config)

        # 执行分析
        print(f"⚡ 开始执行分析...")
        final_state, decision = ta.propagate(symbol, analysis_date)

        # 获取AI交互消息
        ai_messages = []

        # 从trace中获取所有AI交互消息
        if hasattr(ta, "trace") and ta.trace:
            print(f"🔍 从trace中提取AI消息，共 {len(ta.trace)} 个步骤")

            for step_idx, step in enumerate(ta.trace):
                if "messages" in step and step["messages"]:
                    for msg_idx, msg in enumerate(step["messages"]):
                        if hasattr(msg, "content") and hasattr(msg, "type"):
                            ai_messages.append(
                                {
                                    "type": msg.type,
                                    "content": str(msg.content),
                                    "timestamp": datetime.now().isoformat(),
                                    "step_index": step_idx,
                                    "message_index": msg_idx,
                                }
                            )
                            print(
                                f"  📝 步骤 {step_idx}, 消息 {msg_idx}: [{msg.type}] {str(msg.content)[:100]}..."
                            )

        # 如果trace为空，尝试从curr_state获取
        elif (
            hasattr(ta, "curr_state") and ta.curr_state and "messages" in ta.curr_state
        ):
            print(f"🔍 从curr_state中提取AI消息")
            for msg in ta.curr_state["messages"]:
                if hasattr(msg, "content") and hasattr(msg, "type"):
                    ai_messages.append(
                        {
                            "type": msg.type,
                            "content": str(msg.content),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        print(f"📝 总共捕获到 {len(ai_messages)} 条AI交互消息")

        result = {
            "symbol": symbol,
            "analysis_date": analysis_date,
            "conversation_id": conversation_id,
            "task_id": task_id,
            "decision": decision,
            "ai_messages": ai_messages,
            "final_state": make_json_serializable(final_state) if final_state else {},
            "timestamp": datetime.now().isoformat(),
            "success": True,
        }

        # 如果有task数据，添加到结果中
        if task_data:
            result["task_data"] = {
                "ticker": task_data.get("ticker"),
                "title": task_data.get("title"),
                "description": task_data.get("description"),
                "status": task_data.get("status"),
                "research_depth": task_data.get("research_depth"),
                "analysis_period": task_data.get("analysis_period"),
                "config": task_data.get("config"),
                "created_by": task_data.get("created_by"),
                "created_at": task_data.get("created_at"),
            }
            print(f"📋 添加task数据到返回结果: {task_data.get('title')}")

        # 保存到数据库
        if message_manager:
            try:
                # 只保存AI交互消息到数据库
                saved_count = 0
                for msg in ai_messages:
                    # 验证并标准化 message_type
                    msg_type = msg["type"].lower()
                    # 确保 message_type 符合数据库枚举约束
                    if msg_type not in ["human", "ai", "system", "tool"]:
                        print(f"⚠️ 无效的消息类型 '{msg_type}'，使用默认值 'ai'")
                        msg_type = "ai"

                    # 使用优化的保存方法，使用接收到的task_id参数
                    message_id = message_manager.save_message_optimized(
                        symbol=symbol,
                        analysis_date=analysis_date,
                        task_id=task_id,  # 使用接收到的task_id参数
                        message_type=msg_type,
                        content=msg["content"],
                        metadata={
                            "symbol": symbol,
                            "analysis_date": analysis_date,
                            "conversation_id": conversation_id,  # 保存在metadata中
                            "task_id": task_id,  # 也在metadata中保存task_id
                            "step_index": msg.get("step_index"),
                            "message_index": msg.get("message_index"),
                            "timestamp": msg.get(
                                "timestamp", datetime.now().isoformat()
                            ),
                        },
                    )

                    if message_id:
                        saved_count += 1
                        print(
                            f"💾 保存消息 {saved_count}/{len(ai_messages)}: {message_id} (类型: {msg_type})"
                        )
                    else:
                        print(f"⚠️ 消息 {saved_count + 1} 保存失败")

                print(f"💾 成功保存 {saved_count}/{len(ai_messages)} 条消息到数据库")
            except Exception as db_error:
                print(f"❌ 保存到数据库失败: {str(db_error)}")
                logger.error(f"数据库保存失败: {str(db_error)}")
                # 打印详细错误信息用于调试
                import traceback

                print(f"❌ 详细错误信息: {traceback.format_exc()}")

        print(f"✅ 分析完成: {symbol}")
        return jsonify(result)

    except Exception as e:
        error_response, status_code = handle_error(
            e,
            "股票分析",
            symbol=symbol,
            analysis_date=analysis_date,
            conversation_id=conversation_id,
            task_id=task_id,
            custom_config=custom_config,
        )
        return jsonify(error_response), status_code


@app.route("/health")
def health_check():
    """健康检查接口"""
    return jsonify(
        {
            "server": "TradingAgents API",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "database": "connected" if db_manager else "disconnected",
        }
    )


@app.route("/")
def index():
    """根路径重定向到API文档"""
    return jsonify(
        {
            "message": "TradingAgents API Server",
            "health": "/health",
            "analyze": "/analyze",
            "timestamp": datetime.now().isoformat(),
        }
    )


if __name__ == "__main__":
    print("🚀 启动TradingAgents API服务器...")
    print(f"📖 API文档: http://localhost:5000/docs/")
    print(f"🔍 分析接口: http://localhost:5000/analyze")
    print(f"❤️ 健康检查: http://localhost:5000/health")

    app.run(host="0.0.0.0", port=5000, debug=True)
