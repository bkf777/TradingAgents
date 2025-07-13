"""
AKShare数据获取工具类
提供股票数据、财务数据、新闻数据等获取功能
"""

import akshare as ak
import pandas as pd
from typing import Annotated, Optional, Dict, Any
from datetime import datetime, timedelta
import warnings
import time
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 忽略警告
warnings.filterwarnings("ignore")


class AKShareUtils:
    """AKShare数据获取工具类"""

    def __init__(self):
        """初始化AKShare工具类"""
        self.cache = {}  # 简单的内存缓存

    def _get_cache_key(self, func_name: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [func_name]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        return "_".join(key_parts)

    def _cache_get(self, key: str, expire_minutes: int = 30):
        """从缓存获取数据"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(minutes=expire_minutes):
                return data
            else:
                del self.cache[key]
        return None

    def _cache_set(self, key: str, data: Any):
        """设置缓存数据"""
        self.cache[key] = (data, datetime.now())

    def _safe_request(self, func, *args, **kwargs):
        """安全的API请求，包含重试机制"""
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                result = func(*args, **kwargs)
                if result is not None and not (
                    isinstance(result, pd.DataFrame) and result.empty
                ):
                    return result
                else:
                    logger.warning(f"API返回空数据，尝试 {attempt + 1}/{max_retries}")
            except Exception as e:
                logger.warning(
                    f"API请求失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"API请求最终失败: {str(e)}")
                    raise e

        return None

    def get_stock_realtime_data(
        self, symbol: Annotated[str, "股票代码，如 '000001' 或 'sh000001'"]
    ) -> Optional[pd.DataFrame]:
        """
        获取股票实时行情数据

        Args:
            symbol: 股票代码

        Returns:
            包含实时行情数据的DataFrame
        """
        try:
            # 标准化股票代码
            if symbol.startswith(("sh", "sz")):
                symbol = symbol[2:]

            cache_key = self._get_cache_key("realtime", symbol=symbol)
            cached_data = self._cache_get(
                cache_key, expire_minutes=1
            )  # 实时数据缓存1分钟
            if cached_data is not None:
                return cached_data

            # 获取A股实时行情
            data = self._safe_request(ak.stock_zh_a_spot_em)

            if data is not None and not data.empty:
                # 筛选指定股票
                stock_data = data[data["代码"] == symbol]
                if not stock_data.empty:
                    self._cache_set(cache_key, stock_data)
                    return stock_data

            logger.warning(f"未找到股票 {symbol} 的实时数据")
            return None

        except Exception as e:
            logger.error(f"获取股票 {symbol} 实时数据失败: {str(e)}")
            return None

    def get_stock_historical_data(
        self,
        symbol: Annotated[str, "股票代码"],
        start_date: Annotated[str, "开始日期，格式：YYYY-MM-DD"],
        end_date: Annotated[str, "结束日期，格式：YYYY-MM-DD"],
        period: Annotated[str, "数据周期"] = "daily",
        adjust: Annotated[str, "复权类型"] = "qfq",
    ) -> Optional[pd.DataFrame]:
        """
        获取股票历史行情数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 数据周期 (daily, weekly, monthly)
            adjust: 复权类型 (qfq前复权, hfq后复权, 空字符串不复权)

        Returns:
            包含历史行情数据的DataFrame
        """
        try:
            # 标准化股票代码
            if symbol.startswith(("sh", "sz")):
                symbol = symbol[2:]

            cache_key = self._get_cache_key(
                "historical",
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                period=period,
                adjust=adjust,
            )
            cached_data = self._cache_get(
                cache_key, expire_minutes=60
            )  # 历史数据缓存1小时
            if cached_data is not None:
                return cached_data

            # 获取历史行情数据
            data = self._safe_request(
                ak.stock_zh_a_hist,
                symbol=symbol,
                period=period,
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust=adjust,
            )

            if data is not None and not data.empty:
                # 标准化列名
                data = data.rename(
                    columns={
                        "日期": "Date",
                        "开盘": "Open",
                        "收盘": "Close",
                        "最高": "High",
                        "最低": "Low",
                        "成交量": "Volume",
                        "成交额": "Amount",
                        "振幅": "Amplitude",
                        "涨跌幅": "Change_Pct",
                        "涨跌额": "Change",
                        "换手率": "Turnover",
                    }
                )

                # 确保日期格式正确
                if "Date" in data.columns:
                    data["Date"] = pd.to_datetime(data["Date"])
                    data = data.set_index("Date")

                self._cache_set(cache_key, data)
                return data

            logger.warning(
                f"未找到股票 {symbol} 在 {start_date} 到 {end_date} 的历史数据"
            )
            return None

        except Exception as e:
            logger.error(f"获取股票 {symbol} 历史数据失败: {str(e)}")
            return None

    def get_stock_info(
        self, symbol: Annotated[str, "股票代码"]
    ) -> Optional[Dict[str, Any]]:
        """
        获取股票基本信息

        Args:
            symbol: 股票代码

        Returns:
            包含股票基本信息的字典
        """
        try:
            # 标准化股票代码
            if symbol.startswith(("sh", "sz")):
                symbol = symbol[2:]

            cache_key = self._get_cache_key("stock_info", symbol=symbol)
            cached_data = self._cache_get(cache_key, expire_minutes=60)
            if cached_data is not None:
                return cached_data

            # 获取股票基本信息
            data = self._safe_request(ak.stock_individual_info_em, symbol=symbol)

            if data is not None and not data.empty:
                # 转换为字典格式
                info_dict = {}
                for _, row in data.iterrows():
                    info_dict[row["item"]] = row["value"]

                self._cache_set(cache_key, info_dict)
                return info_dict

            logger.warning(f"未找到股票 {symbol} 的基本信息")
            return None

        except Exception as e:
            logger.error(f"获取股票 {symbol} 基本信息失败: {str(e)}")
            return None

    def get_stock_news(
        self,
        symbol: Annotated[str, "股票代码"],
        start_date: Annotated[str, "开始日期，格式：YYYY-MM-DD"],
        end_date: Annotated[str, "结束日期，格式：YYYY-MM-DD"],
    ) -> Optional[str]:
        """
        获取股票新闻数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            格式化的新闻字符串
        """
        try:
            # 标准化股票代码
            if symbol.startswith(("sh", "sz")):
                symbol = symbol[2:]

            cache_key = self._get_cache_key(
                "news", symbol=symbol, start_date=start_date, end_date=end_date
            )
            cached_data = self._cache_get(cache_key, expire_minutes=30)
            if cached_data is not None:
                return cached_data

            # 获取个股新闻
            data = self._safe_request(ak.stock_news_em, symbol=symbol)

            if data is not None and not data.empty:
                # 过滤日期范围内的新闻
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")

                filtered_news = []
                for _, row in data.iterrows():
                    try:
                        # 尝试不同的列名
                        title_col = None
                        time_col = None
                        content_col = None

                        # 查找标题列
                        for col in ["标题", "title", "新闻标题", "消息标题"]:
                            if col in row.index:
                                title_col = col
                                break

                        # 查找时间列
                        for col in ["发布时间", "time", "时间", "发布日期", "日期"]:
                            if col in row.index:
                                time_col = col
                                break

                        # 查找内容列
                        for col in ["内容", "content", "新闻内容", "摘要", "summary"]:
                            if col in row.index:
                                content_col = col
                                break

                        if title_col and time_col:
                            time_str = str(row[time_col])
                            if len(time_str) >= 10:
                                news_date = datetime.strptime(time_str[:10], "%Y-%m-%d")
                                if start_dt <= news_date <= end_dt:
                                    filtered_news.append(
                                        {
                                            "title": row[title_col],
                                            "time": time_str,
                                            "content": (
                                                row[content_col]
                                                if content_col
                                                and pd.notna(row[content_col])
                                                else "无详细内容"
                                            ),
                                        }
                                    )
                    except Exception as e:
                        logger.debug(f"处理新闻条目时出错: {str(e)}")
                        continue

                if filtered_news:
                    news_text = f"## {symbol} 新闻，从 {start_date} 到 {end_date}:\n\n"
                    for news in filtered_news:
                        news_text += f"### {news['title']} ({news['time']})\n"
                        news_text += f"{news['content']}\n\n"

                    self._cache_set(cache_key, news_text)
                    return news_text

            logger.warning(f"未找到股票 {symbol} 在 {start_date} 到 {end_date} 的新闻")
            return ""

        except Exception as e:
            logger.error(f"获取股票 {symbol} 新闻失败: {str(e)}")
            return ""

    def get_financial_balance_sheet(
        self,
        symbol: Annotated[str, "股票代码"],
        period: Annotated[str, "报告期类型"] = "年报",
    ) -> Optional[pd.DataFrame]:
        """
        获取资产负债表数据

        Args:
            symbol: 股票代码
            period: 报告期类型 (年报, 中报, 一季报, 三季报)

        Returns:
            包含资产负债表数据的DataFrame
        """
        try:
            # 标准化股票代码
            if symbol.startswith(("sh", "sz")):
                symbol = symbol[2:]

            cache_key = self._get_cache_key(
                "balance_sheet", symbol=symbol, period=period
            )
            cached_data = self._cache_get(
                cache_key, expire_minutes=120
            )  # 财务数据缓存2小时
            if cached_data is not None:
                return cached_data

            # 获取资产负债表
            data = self._safe_request(
                ak.stock_balance_sheet_by_report_em, symbol=symbol
            )

            if data is not None and not data.empty:
                # 根据期间筛选最新数据
                if period in data.columns:
                    latest_data = data[data[period].notna()].head(1)
                    if not latest_data.empty:
                        self._cache_set(cache_key, latest_data)
                        return latest_data
                else:
                    # 如果没有指定期间列，返回最新的数据
                    self._cache_set(cache_key, data.head(1))
                    return data.head(1)

            logger.warning(f"未找到股票 {symbol} 的资产负债表数据")
            return None

        except Exception as e:
            logger.error(f"获取股票 {symbol} 资产负债表失败: {str(e)}")
            return None

    def get_financial_income_statement(
        self,
        symbol: Annotated[str, "股票代码"],
        period: Annotated[str, "报告期类型"] = "年报",
    ) -> Optional[pd.DataFrame]:
        """
        获取利润表数据

        Args:
            symbol: 股票代码
            period: 报告期类型 (年报, 中报, 一季报, 三季报)

        Returns:
            包含利润表数据的DataFrame
        """
        try:
            # 标准化股票代码
            if symbol.startswith(("sh", "sz")):
                symbol = symbol[2:]

            cache_key = self._get_cache_key(
                "income_statement", symbol=symbol, period=period
            )
            cached_data = self._cache_get(cache_key, expire_minutes=120)
            if cached_data is not None:
                return cached_data

            # 获取利润表
            data = self._safe_request(ak.stock_profit_sheet_by_report_em, symbol=symbol)

            if data is not None and not data.empty:
                # 根据期间筛选最新数据
                if period in data.columns:
                    latest_data = data[data[period].notna()].head(1)
                    if not latest_data.empty:
                        self._cache_set(cache_key, latest_data)
                        return latest_data
                else:
                    self._cache_set(cache_key, data.head(1))
                    return data.head(1)

            logger.warning(f"未找到股票 {symbol} 的利润表数据")
            return None

        except Exception as e:
            logger.error(f"获取股票 {symbol} 利润表失败: {str(e)}")
            return None

    def get_financial_cash_flow(
        self,
        symbol: Annotated[str, "股票代码"],
        period: Annotated[str, "报告期类型"] = "年报",
    ) -> Optional[pd.DataFrame]:
        """
        获取现金流量表数据

        Args:
            symbol: 股票代码
            period: 报告期类型 (年报, 中报, 一季报, 三季报)

        Returns:
            包含现金流量表数据的DataFrame
        """
        try:
            # 标准化股票代码
            if symbol.startswith(("sh", "sz")):
                symbol = symbol[2:]

            cache_key = self._get_cache_key("cash_flow", symbol=symbol, period=period)
            cached_data = self._cache_get(cache_key, expire_minutes=120)
            if cached_data is not None:
                return cached_data

            # 获取现金流量表
            data = self._safe_request(
                ak.stock_cash_flow_sheet_by_report_em, symbol=symbol
            )

            if data is not None and not data.empty:
                # 根据期间筛选最新数据
                if period in data.columns:
                    latest_data = data[data[period].notna()].head(1)
                    if not latest_data.empty:
                        self._cache_set(cache_key, latest_data)
                        return latest_data
                else:
                    self._cache_set(cache_key, data.head(1))
                    return data.head(1)

            logger.warning(f"未找到股票 {symbol} 的现金流量表数据")
            return None

        except Exception as e:
            logger.error(f"获取股票 {symbol} 现金流量表失败: {str(e)}")
            return None

    def get_global_news(
        self,
        start_date: Annotated[str, "开始日期，格式：YYYY-MM-DD"],
        end_date: Annotated[str, "结束日期，格式：YYYY-MM-DD"],
    ) -> Optional[str]:
        """
        获取全球财经新闻

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            格式化的新闻字符串
        """
        try:
            cache_key = self._get_cache_key(
                "global_news", start_date=start_date, end_date=end_date
            )
            cached_data = self._cache_get(cache_key, expire_minutes=30)
            if cached_data is not None:
                return cached_data

            # 获取财经快讯
            data = self._safe_request(ak.stock_info_global_em)

            if data is not None and not data.empty:
                # 过滤日期范围内的新闻
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")

                filtered_news = []
                for _, row in data.iterrows():
                    try:
                        # 假设时间列名为'时间'
                        if "时间" in row:
                            news_date = datetime.strptime(row["时间"][:10], "%Y-%m-%d")
                            if start_dt <= news_date <= end_dt:
                                filtered_news.append(row)
                    except:
                        continue

                if filtered_news:
                    news_text = f"## 全球财经新闻，从 {start_date} 到 {end_date}:\n\n"
                    for news in filtered_news:
                        news_text += f"### {news.get('标题', '无标题')} ({news.get('时间', '无时间')})\n"
                        if "内容" in news and pd.notna(news["内容"]):
                            news_text += f"{news['内容']}\n\n"
                        else:
                            news_text += "无详细内容\n\n"

                    self._cache_set(cache_key, news_text)
                    return news_text

            logger.warning(f"未找到 {start_date} 到 {end_date} 的全球财经新闻")
            return ""

        except Exception as e:
            logger.error(f"获取全球财经新闻失败: {str(e)}")
            return ""


# 创建全局实例
akshare_utils = AKShareUtils()


# 兼容性函数，保持与现有接口一致
def get_akshare_stock_data(
    symbol: Annotated[str, "股票代码"],
    start_date: Annotated[str, "开始日期，格式：YYYY-MM-DD"],
    end_date: Annotated[str, "结束日期，格式：YYYY-MM-DD"],
) -> pd.DataFrame:
    """
    获取股票历史数据，兼容YFinance格式

    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        DataFrame格式的股票数据
    """
    data = akshare_utils.get_stock_historical_data(symbol, start_date, end_date)
    if data is not None:
        return data
    else:
        return pd.DataFrame()


def get_akshare_stock_info(symbol: Annotated[str, "股票代码"]) -> Dict[str, Any]:
    """
    获取股票基本信息，兼容YFinance格式

    Args:
        symbol: 股票代码

    Returns:
        包含股票信息的字典
    """
    info = akshare_utils.get_stock_info(symbol)
    if info is not None:
        return info
    else:
        return {}


def get_akshare_balance_sheet(
    symbol: Annotated[str, "股票代码"], period: Annotated[str, "报告期类型"] = "年报"
) -> pd.DataFrame:
    """
    获取资产负债表，兼容SimFin格式

    Args:
        symbol: 股票代码
        period: 报告期类型

    Returns:
        DataFrame格式的资产负债表
    """
    data = akshare_utils.get_financial_balance_sheet(symbol, period)
    if data is not None:
        return data
    else:
        return pd.DataFrame()


def get_akshare_income_statement(
    symbol: Annotated[str, "股票代码"], period: Annotated[str, "报告期类型"] = "年报"
) -> pd.DataFrame:
    """
    获取利润表，兼容SimFin格式

    Args:
        symbol: 股票代码
        period: 报告期类型

    Returns:
        DataFrame格式的利润表
    """
    data = akshare_utils.get_financial_income_statement(symbol, period)
    if data is not None:
        return data
    else:
        return pd.DataFrame()


def get_akshare_cash_flow(
    symbol: Annotated[str, "股票代码"], period: Annotated[str, "报告期类型"] = "年报"
) -> pd.DataFrame:
    """
    获取现金流量表，兼容SimFin格式

    Args:
        symbol: 股票代码
        period: 报告期类型

    Returns:
        DataFrame格式的现金流量表
    """
    data = akshare_utils.get_financial_cash_flow(symbol, period)
    if data is not None:
        return data
    else:
        return pd.DataFrame()


def get_akshare_news(
    symbol: Annotated[str, "股票代码"],
    start_date: Annotated[str, "开始日期，格式：YYYY-MM-DD"],
    end_date: Annotated[str, "结束日期，格式：YYYY-MM-DD"],
) -> str:
    """
    获取股票新闻，兼容Finnhub格式

    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        格式化的新闻字符串
    """
    news = akshare_utils.get_stock_news(symbol, start_date, end_date)
    if news:
        return news
    else:
        return ""


def get_akshare_global_news(
    start_date: Annotated[str, "开始日期，格式：YYYY-MM-DD"],
    end_date: Annotated[str, "结束日期，格式：YYYY-MM-DD"],
) -> str:
    """
    获取全球财经新闻

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        格式化的新闻字符串
    """
    news = akshare_utils.get_global_news(start_date, end_date)
    if news:
        return news
    else:
        return ""
