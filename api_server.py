#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingAgents Web API 服务器
提供股票数据获取和分析功能的REST API接口
"""

from flask import Flask, request
from flask_cors import CORS
from flask_restx import Api, Resource, fields, Namespace
import asyncio
import json
import traceback
import logging
import sys
from datetime import datetime, date
import pandas as pd
from typing import Dict, Any, Optional

# 导入TradingAgents相关模块
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows import (
    get_YFin_data,
    get_YFin_data_window,
    get_stockstats_indicator,
    get_finnhub_news,
    get_stock_news_openai,
    get_global_news_openai,
)

# 导入数据库相关模块
# 初始化数据库连接
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


# 错误处理函数
def handle_error(error: Exception, operation: str, **kwargs) -> tuple:
    """
    统一错误处理函数

    Args:
        error: 异常对象
        operation: 操作描述
        **kwargs: 额外的上下文信息

    Returns:
        tuple: (错误响应字典, HTTP状态码)
    """
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

    # 打印额外的上下文信息
    if kwargs:
        print(f"❌ 上下文信息:")
        for key, value in kwargs.items():
            print(f"   - {key}: {value}")

    print(f"❌ 错误堆栈:")
    print(error_trace)
    print(f"{'='*50}\n")

    # 根据错误类型确定HTTP状态码
    if isinstance(error, ValueError):
        status_code = 400
    elif isinstance(error, KeyError):
        status_code = 400
    elif isinstance(error, FileNotFoundError):
        status_code = 404
    elif isinstance(error, ConnectionError):
        status_code = 503
    elif isinstance(error, TimeoutError):
        status_code = 504
    else:
        status_code = 500

    return {
        "success": False,
        "message": f"{operation}失败: {error_msg}",
        "error": {
            "type": type(error).__name__,
            "message": error_msg,
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "context": kwargs,
        },
    }, status_code


# 请求日志中间件
@app.before_request
def log_request():
    """记录请求信息"""
    logger.info(f"收到请求: {request.method} {request.url}")
    if request.is_json:
        try:
            json_data = request.get_json()
            logger.info(f"请求数据: {json_data}")
        except Exception as e:
            logger.warning(f"无法解析JSON数据: {str(e)}")
    print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] {request.method} {request.url}")


@app.after_request
def log_response(response):
    """记录响应信息"""
    logger.info(f"响应状态: {response.status_code}")
    print(
        f"✅ [{datetime.now().strftime('%H:%M:%S')}] 响应状态: {response.status_code}"
    )
    return response


# 创建API文档
api = Api(
    app,
    version="1.0",
    title="TradingAgents API",
    description="股票数据获取和智能分析API",
    doc="/docs/",
)

# 创建命名空间
data_ns = Namespace("data", description="数据获取相关API")
analysis_ns = Namespace("analysis", description="分析相关API")

api.add_namespace(data_ns, path="/api/data")
api.add_namespace(analysis_ns, path="/api/analysis")

# 定义API模型
stock_data_model = api.model(
    "StockData",
    {
        "symbol": fields.String(required=True, description="股票代码", example="NVDA"),
        "start_date": fields.String(
            required=True, description="开始日期 (YYYY-MM-DD)", example="2024-01-01"
        ),
        "end_date": fields.String(
            required=True, description="结束日期 (YYYY-MM-DD)", example="2024-12-31"
        ),
    },
)

analysis_model = api.model(
    "Analysis",
    {
        "symbol": fields.String(required=True, description="股票代码", example="NVDA"),
        "date": fields.String(
            required=True, description="分析日期 (YYYY-MM-DD)", example="2025-06-10"
        ),
        "config": fields.Raw(description="自定义配置参数"),
    },
)

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
        "reset_memory_collections": False,  # 是否重置内存集合
    }
)


@data_ns.route("/stock/<string:symbol>")
class StockDataResource(Resource):
    @data_ns.doc("get_stock_data")
    @data_ns.param("symbol", "股票代码")
    @data_ns.param("start_date", "开始日期 (YYYY-MM-DD)", default="2024-01-01")
    @data_ns.param("end_date", "结束日期 (YYYY-MM-DD)", default="2024-12-31")
    def get(self, symbol):
        """获取股票历史数据"""
        try:
            start_date = request.args.get("start_date", "2024-01-01")
            end_date = request.args.get("end_date", "2024-12-31")

            print(f"📊 开始获取股票数据: {symbol} ({start_date} 到 {end_date})")
            logger.info(
                f"获取股票数据: symbol={symbol}, start_date={start_date}, end_date={end_date}"
            )

            # 获取股票数据
            stock_data = get_YFin_data(symbol, start_date, end_date)

            # 转换为JSON格式
            if isinstance(stock_data, pd.DataFrame):
                result = {
                    "symbol": symbol,
                    "start_date": start_date,
                    "end_date": end_date,
                    "data": stock_data.reset_index().to_dict("records"),
                }
                print(f"✅ 成功获取 {symbol} 的股票数据，共 {len(stock_data)} 条记录")
            else:
                result = {
                    "symbol": symbol,
                    "start_date": start_date,
                    "end_date": end_date,
                    "data": stock_data,
                }
                print(f"✅ 成功获取 {symbol} 的股票数据")

            return {
                "success": True,
                "message": f"成功获取 {symbol} 的股票数据",
                "result": result,
            }

        except Exception as e:
            return handle_error(
                e,
                f"获取股票数据",
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )


@data_ns.route("/stock/<string:symbol>/window")
class StockDataWindowResource(Resource):
    @data_ns.doc("get_stock_data_window")
    @data_ns.param("symbol", "股票代码")
    @data_ns.param("date", "目标日期 (YYYY-MM-DD)", default="2024-12-31")
    @data_ns.param("window_size", "时间窗口大小（天）", default=30)
    def get(self, symbol):
        """获取指定时间窗口的股票数据"""
        try:
            target_date = request.args.get("date", "2024-12-31")
            window_size = int(request.args.get("window_size", 30))

            print(
                f"📊 开始获取时间窗口数据: {symbol} (日期: {target_date}, 窗口: {window_size}天)"
            )
            logger.info(
                f"获取时间窗口数据: symbol={symbol}, target_date={target_date}, window_size={window_size}"
            )

            # 获取时间窗口数据
            stock_data = get_YFin_data_window(symbol, target_date, window_size)

            # 转换为JSON格式
            if isinstance(stock_data, pd.DataFrame):
                result = {
                    "symbol": symbol,
                    "target_date": target_date,
                    "window_size": window_size,
                    "data": stock_data.reset_index().to_dict("records"),
                }
                print(
                    f"✅ 成功获取 {symbol} 的时间窗口数据，共 {len(stock_data)} 条记录"
                )
            else:
                result = {
                    "symbol": symbol,
                    "target_date": target_date,
                    "window_size": window_size,
                    "data": stock_data,
                }
                print(f"✅ 成功获取 {symbol} 的时间窗口数据")

            return {
                "success": True,
                "message": f"成功获取 {symbol} 的时间窗口数据",
                "result": result,
            }

        except Exception as e:
            return handle_error(
                e,
                f"获取时间窗口数据",
                symbol=symbol,
                target_date=target_date,
                window_size=window_size,
            )


@data_ns.route("/stock/<string:symbol>/indicator")
class StockIndicatorResource(Resource):
    @data_ns.doc("get_stock_indicator")
    @data_ns.param("symbol", "股票代码")
    @data_ns.param("indicator", "技术指标名称", default="rsi_14")
    @data_ns.param("date", "目标日期 (YYYY-MM-DD)", default="2024-12-31")
    def get(self, symbol):
        """获取股票技术指标"""
        try:
            indicator = request.args.get("indicator", "rsi_14")
            target_date = request.args.get("date", "2024-12-31")

            print(f"📈 开始获取技术指标: {symbol} - {indicator} (日期: {target_date})")
            logger.info(
                f"获取技术指标: symbol={symbol}, indicator={indicator}, target_date={target_date}"
            )

            # 获取技术指标
            indicator_value = get_stockstats_indicator(symbol, indicator, target_date)

            result = {
                "symbol": symbol,
                "indicator": indicator,
                "date": target_date,
                "value": indicator_value,
            }

            print(f"✅ 成功获取 {symbol} 的 {indicator} 指标，值为: {indicator_value}")

            return {
                "success": True,
                "message": f"成功获取 {symbol} 的 {indicator} 指标",
                "result": result,
            }

        except Exception as e:
            return handle_error(
                e,
                f"获取技术指标",
                symbol=symbol,
                indicator=indicator,
                target_date=target_date,
            )


@data_ns.route("/news/<string:symbol>")
class StockNewsResource(Resource):
    @data_ns.doc("get_stock_news")
    @data_ns.param("symbol", "股票代码")
    @data_ns.param("start_date", "开始日期 (YYYY-MM-DD)")
    @data_ns.param("end_date", "结束日期 (YYYY-MM-DD)")
    def get(self, symbol):
        """获取股票相关新闻"""
        try:
            start_date = request.args.get("start_date")
            end_date = request.args.get("end_date")

            if start_date and end_date:
                print(
                    f"📰 开始获取股票新闻: {symbol} ({start_date} 到 {end_date}) - 使用Finnhub"
                )
                logger.info(
                    f"获取股票新闻(Finnhub): symbol={symbol}, start_date={start_date}, end_date={end_date}"
                )
                news_data = get_finnhub_news(symbol, start_date, end_date)
            else:
                print(f"📰 开始获取股票新闻: {symbol} - 使用OpenAI实时数据")
                logger.info(f"获取股票新闻(OpenAI): symbol={symbol}")
                news_data = get_stock_news_openai(symbol)

            result = {
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "news": news_data,
            }

            news_count = len(news_data) if isinstance(news_data, list) else "未知"
            print(f"✅ 成功获取 {symbol} 的新闻数据，共 {news_count} 条")

            return {
                "success": True,
                "message": f"成功获取 {symbol} 的新闻数据",
                "result": result,
            }

        except Exception as e:
            return handle_error(
                e,
                f"获取新闻数据",
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )


@data_ns.route("/news/global")
class GlobalNewsResource(Resource):
    @data_ns.doc("get_global_news")
    @data_ns.param("topic", "新闻主题", default="financial markets")
    def get(self):
        """获取全球财经新闻"""
        try:
            topic = request.args.get("topic", "financial markets")

            print(f"🌍 开始获取全球新闻: {topic}")
            logger.info(f"获取全球新闻: topic={topic}")

            # 获取全球新闻
            news_data = get_global_news_openai(topic)

            result = {"topic": topic, "news": news_data}

            news_count = len(news_data) if isinstance(news_data, list) else "未知"
            print(f"✅ 成功获取关于 {topic} 的全球新闻，共 {news_count} 条")

            return {
                "success": True,
                "message": f"成功获取关于 {topic} 的全球新闻",
                "result": result,
            }

        except Exception as e:
            return handle_error(e, f"获取全球新闻", topic=topic)


@data_ns.route("/batch/stocks")
class BatchStockDataResource(Resource):
    @data_ns.doc("get_batch_stock_data")
    @data_ns.expect(
        api.model(
            "BatchStockRequest",
            {
                "symbols": fields.List(
                    fields.String, required=True, description="股票代码列表"
                ),
                "start_date": fields.String(required=True, description="开始日期"),
                "end_date": fields.String(required=True, description="结束日期"),
            },
        )
    )
    def post(self):
        """批量获取多只股票的数据"""
        symbols = []
        start_date = None
        end_date = None

        try:
            data = request.get_json()
            symbols = data.get("symbols", [])
            start_date = data.get("start_date")
            end_date = data.get("end_date")

            print(f"📊 开始批量获取股票数据: {symbols} ({start_date} 到 {end_date})")
            logger.info(
                f"批量获取股票数据: symbols={symbols}, start_date={start_date}, end_date={end_date}"
            )

            if not symbols or not start_date or not end_date:
                error_msg = "缺少必要参数: symbols, start_date, end_date"
                print(f"❌ 参数错误: {error_msg}")
                return (
                    {
                        "success": False,
                        "message": error_msg,
                    },
                    400,
                )

            results = {}
            errors = {}

            for i, symbol in enumerate(symbols, 1):
                try:
                    print(f"📈 处理股票 {i}/{len(symbols)}: {symbol}")
                    stock_data = get_YFin_data(symbol, start_date, end_date)
                    if isinstance(stock_data, pd.DataFrame):
                        results[symbol] = stock_data.reset_index().to_dict("records")
                        print(f"✅ {symbol}: 成功获取 {len(stock_data)} 条记录")
                    else:
                        results[symbol] = stock_data
                        print(f"✅ {symbol}: 成功获取数据")
                except Exception as e:
                    errors[symbol] = str(e)
                    print(f"❌ {symbol}: 获取失败 - {str(e)}")

            print(f"✅ 批量获取完成，成功: {len(results)}, 失败: {len(errors)}")

            return {
                "success": True,
                "message": f"批量获取完成，成功: {len(results)}, 失败: {len(errors)}",
                "result": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "data": results,
                    "errors": errors,
                },
            }

        except Exception as e:
            return handle_error(
                e,
                f"批量获取股票数据",
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
            )


@analysis_ns.route("/analyze")
class AnalysisResource(Resource):
    @analysis_ns.doc("run_analysis")
    @analysis_ns.expect(analysis_model)
    def post(self):
        """执行股票分析"""
        symbol = None
        analysis_date = None
        custom_config = {}

        try:
            data = request.get_json()
            symbol = data.get("symbol")
            analysis_date = data.get("date")
            custom_config = data.get("config", {})

            print(f"🔍 开始股票分析: {symbol} (日期: {analysis_date})")
            logger.info(
                f"执行股票分析: symbol={symbol}, analysis_date={analysis_date}, custom_config={custom_config}"
            )

            if not symbol or not analysis_date:
                error_msg = "缺少必要参数: symbol 和 date"
                print(f"❌ 参数错误: {error_msg}")
                return (
                    {"success": False, "message": error_msg},
                    400,
                )

            # 创建配置
            config = DEFAULT_API_CONFIG.copy()
            config.update(custom_config)
            print(f"📋 使用配置: {config}")

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
                hasattr(ta, "curr_state")
                and ta.curr_state
                and "messages" in ta.curr_state
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
                "decision": decision,
                "config_used": config,
            }

            # 保存AI交互消息到数据库
            message_ids = []
            if message_manager and ai_messages:
                try:
                    print(f"💾 开始保存 {len(ai_messages)} 条AI交互消息到数据库...")

                    for i, ai_msg in enumerate(ai_messages):
                        # 为每条AI消息创建一个数据库记录
                        message_content = f"[{ai_msg['type']}] {ai_msg['content']}"

                        message_id = message_manager.save_analysis_message(
                            symbol=symbol,
                            analysis_date=analysis_date,
                            message=message_content,
                            decision_data=(
                                decision if i == len(ai_messages) - 1 else None
                            ),  # 只在最后一条消息中保存决策数据
                            metadata={
                                "config_used": config,
                                "message_type": ai_msg["type"],
                                "message_index": i,
                                "total_messages": len(ai_messages),
                                "ai_timestamp": ai_msg["timestamp"],
                            },
                        )

                        if message_id:
                            message_ids.append(message_id)
                            print(
                                f"💾 保存AI消息 {i+1}/{len(ai_messages)}: {message_id}"
                            )
                        else:
                            print(f"⚠️ AI消息 {i+1} 保存失败")

                    print(f"✅ 成功保存 {len(message_ids)} 条AI交互消息到数据库")

                except Exception as e:
                    print(f"⚠️ 数据库保存异常: {str(e)}")
                    logger.error(f"数据库保存异常: {str(e)}")
            elif message_manager and not ai_messages:
                # 如果没有捕获到AI消息，保存一个简单的完成消息
                try:
                    fallback_message = f"完成 {symbol} 的分析（未捕获到详细AI交互）"
                    message_id = message_manager.save_analysis_message(
                        symbol=symbol,
                        analysis_date=analysis_date,
                        message=fallback_message,
                        decision_data=decision,
                        metadata={"config_used": config, "fallback": True},
                    )
                    if message_id:
                        message_ids.append(message_id)
                        print(f"💾 保存备用消息到数据库: {message_id}")
                except Exception as e:
                    print(f"⚠️ 备用消息保存异常: {str(e)}")

            print(f"✅ 成功完成 {symbol} 的分析")

            # 在返回结果中包含消息ID列表（如果保存成功）
            if message_ids:
                result["message_ids"] = message_ids
                result["saved_messages_count"] = len(message_ids)

            return {
                "success": True,
                "message": f"成功完成 {symbol} 的分析，保存了 {len(message_ids)} 条AI交互消息",
                "result": result,
            }

        except Exception as e:
            return handle_error(
                e,
                f"执行股票分析",
                symbol=symbol,
                analysis_date=analysis_date,
                custom_config=custom_config,
            )


@analysis_ns.route("/batch/analyze")
class BatchAnalysisResource(Resource):
    @analysis_ns.doc("run_batch_analysis")
    @analysis_ns.expect(
        api.model(
            "BatchAnalysisRequest",
            {
                "symbols": fields.List(
                    fields.String, required=True, description="股票代码列表"
                ),
                "date": fields.String(required=True, description="分析日期"),
                "config": fields.Raw(description="自定义配置参数"),
            },
        )
    )
    def post(self):
        """批量执行多只股票的分析"""
        symbols = []
        analysis_date = None
        custom_config = {}

        try:
            data = request.get_json()
            symbols = data.get("symbols", [])
            analysis_date = data.get("date")
            custom_config = data.get("config", {})

            print(f"🔍 开始批量股票分析: {symbols} (日期: {analysis_date})")
            logger.info(
                f"批量股票分析: symbols={symbols}, analysis_date={analysis_date}, custom_config={custom_config}"
            )

            if not symbols or not analysis_date:
                error_msg = "缺少必要参数: symbols 和 date"
                print(f"❌ 参数错误: {error_msg}")
                return (
                    {"success": False, "message": error_msg},
                    400,
                )

            # 创建配置
            config = DEFAULT_API_CONFIG.copy()
            config.update(custom_config)
            print(f"📋 使用配置: {config}")

            results = {}
            errors = {}

            for i, symbol in enumerate(symbols, 1):
                try:
                    print(f"🔍 分析股票 {i}/{len(symbols)}: {symbol}")
                    # 为每个股票创建独立的分析实例
                    ta = TradingAgentsGraph(debug=True, config=config)
                    _, decision = ta.propagate(symbol, analysis_date)

                    results[symbol] = {
                        "symbol": symbol,
                        "analysis_date": analysis_date,
                        "decision": decision,
                    }
                    print(f"✅ {symbol}: 分析完成")
                except Exception as e:
                    errors[symbol] = str(e)
                    print(f"❌ {symbol}: 分析失败 - {str(e)}")

            print(f"✅ 批量分析完成，成功: {len(results)}, 失败: {len(errors)}")

            return {
                "success": True,
                "message": f"批量分析完成，成功: {len(results)}, 失败: {len(errors)}",
                "result": {
                    "analysis_date": analysis_date,
                    "results": results,
                    "errors": errors,
                    "config_used": config,
                },
            }

        except Exception as e:
            return handle_error(
                e,
                f"批量股票分析",
                symbols=symbols,
                analysis_date=analysis_date,
                custom_config=custom_config,
            )


@analysis_ns.route("/quick/<string:symbol>")
class QuickAnalysisResource(Resource):
    @analysis_ns.doc("run_quick_analysis")
    @analysis_ns.param("symbol", "股票代码")
    @analysis_ns.param("date", "分析日期 (YYYY-MM-DD)", default="2025-06-10")
    def get(self, symbol):
        """快速分析（使用默认配置）"""
        try:
            analysis_date = request.args.get("date", "2025-06-10")

            print(f"⚡ 开始快速分析: {symbol} (日期: {analysis_date})")
            logger.info(f"快速分析: symbol={symbol}, analysis_date={analysis_date}")

            # 使用轻量级配置进行快速分析
            quick_config = DEFAULT_API_CONFIG.copy()
            quick_config.update(
                {
                    "max_debate_rounds": 1,
                    "max_risk_discuss_rounds": 1,
                    "quick_think_llm": "gpt-4o-mini",  # 使用更快的模型
                }
            )
            print(f"📋 使用快速配置: {quick_config}")

            # 初始化TradingAgentsGraph
            print(f"🚀 初始化TradingAgentsGraph (快速模式)...")
            ta = TradingAgentsGraph(debug=False, config=quick_config)

            # 执行分析
            print(f"⚡ 开始执行快速分析...")
            _, decision = ta.propagate(symbol, analysis_date)

            result = {
                "symbol": symbol,
                "analysis_date": analysis_date,
                "decision": decision,
                "analysis_type": "quick",
            }

            print(f"✅ 成功完成 {symbol} 的快速分析")

            return {
                "success": True,
                "message": f"成功完成 {symbol} 的快速分析",
                "result": result,
            }

        except Exception as e:
            return handle_error(
                e, f"快速分析", symbol=symbol, analysis_date=analysis_date
            )


@app.route("/health")
def health_check():
    """健康检查端点"""
    try:
        print(f"💓 健康检查请求")
        logger.info("健康检查请求")

        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "server": "TradingAgents API",
        }

        print(f"✅ 健康检查通过")
        return health_status

    except Exception as e:
        print(f"❌ 健康检查失败: {str(e)}")
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }, 500


@app.route("/reset-memory", methods=["POST"])
def reset_memory():
    """重置内存集合端点"""
    try:
        print(f"🗑️ 重置内存集合请求")
        logger.info("重置内存集合请求")

        # 创建一个临时配置来重置内存
        reset_config = DEFAULT_API_CONFIG.copy()
        reset_config["reset_memory_collections"] = True

        # 初始化一个临时的TradingAgentsGraph来重置内存
        temp_ta = TradingAgentsGraph(debug=False, config=reset_config)

        result = {
            "success": True,
            "message": "内存集合已重置",
            "timestamp": datetime.now().isoformat(),
            "collections_reset": [
                "bull_memory",
                "bear_memory",
                "trader_memory",
                "invest_judge_memory",
                "risk_manager_memory",
            ],
        }

        print(f"✅ 内存集合重置完成")
        return result

    except Exception as e:
        return handle_error(e, "重置内存集合")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 启动 TradingAgents API 服务器...")
    print("=" * 60)
    print(f"📚 API 文档地址: http://localhost:5000/docs/")
    print(f"💓 健康检查: http://localhost:5000/health")
    print(f"🗑️ 重置内存: http://localhost:5000/reset-memory (POST)")
    print(f"📝 日志文件: api_server.log")
    if db_manager:
        print("💾 MySQL数据库: 已连接，分析结果将自动保存")
    else:
        print("⚠️ MySQL数据库: 未连接，分析结果不会保存")
    print("=" * 60)

    logger.info("TradingAgents API 服务器启动")

    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        print(f"❌ 服务器启动失败: {str(e)}")
        logger.error(f"服务器启动失败: {str(e)}")
        raise
