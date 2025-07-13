#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API客户端工具
提供更稳定的OpenAI API连接
"""

import time
import logging
from typing import Any, Dict, Optional
from openai import OpenAI
import httpx
from functools import wraps

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RobustOpenAIClient:
    """更稳定的OpenAI客户端"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.nuwaapi.com/v1",
        max_retries: int = 3,
        timeout: float = 60.0,
    ):
        """
        初始化客户端

        Args:
            api_key: API密钥
            base_url: API基础URL
            max_retries: 最大重试次数
            timeout: 超时时间（秒）
        """
        self.api_key = api_key
        self.base_url = base_url
        self.max_retries = max_retries
        self.timeout = timeout

        # 创建自定义HTTP客户端
        self.http_client = httpx.Client(
            timeout=timeout,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            verify=True,
            # 添加重试配置
            transport=httpx.HTTPTransport(retries=2),
        )

        # 创建OpenAI客户端
        self.client = OpenAI(
            api_key=api_key, base_url=base_url, http_client=self.http_client
        )

    def _retry_on_connection_error(self, func):
        """连接错误重试装饰器"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(self.max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_msg = str(e).lower()

                    # 检查是否是连接相关错误
                    connection_errors = [
                        "connection error",
                        "ssl",
                        "timeout",
                        "eof occurred",
                        "connection reset",
                        "connection refused",
                    ]

                    is_connection_error = any(
                        err in error_msg for err in connection_errors
                    )

                    if is_connection_error and attempt < self.max_retries - 1:
                        wait_time = (2**attempt) + 1  # 指数退避: 2, 5, 9秒
                        logger.warning(
                            f"API连接错误 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}"
                        )
                        logger.info(f"等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        # 非连接错误或最后一次尝试，直接抛出异常
                        break

            # 所有重试都失败了
            logger.error(f"API调用最终失败: {str(last_exception)}")
            raise last_exception

        return wrapper

    def chat_completions_create(self, **kwargs) -> Any:
        """创建聊天完成，带重试机制"""
        return self._retry_on_connection_error(self.client.chat.completions.create)(
            **kwargs
        )

    def close(self):
        """关闭客户端"""
        if hasattr(self.http_client, "close"):
            self.http_client.close()


# 全局客户端实例
_global_client: Optional[RobustOpenAIClient] = None


def get_robust_openai_client(
    api_key: str = "sk-yOXwTRVHIub4m6WjEWin68sqvdYypExLyBbChOc38SX4PnpW",
    base_url: str = "https://api.nuwaapi.com/v1",
) -> RobustOpenAIClient:
    """获取全局的稳定OpenAI客户端"""
    global _global_client

    if _global_client is None:
        _global_client = RobustOpenAIClient(
            api_key=api_key, base_url=base_url, max_retries=3, timeout=60.0
        )

    return _global_client


def create_robust_openai_instance(
    api_key: str = "sk-yOXwTRVHIub4m6WjEWin68sqvdYypExLyBbChOc38SX4PnpW",
    base_url: str = "https://api.nuwaapi.com/v1",
) -> OpenAI:
    """
    创建一个更稳定的OpenAI实例
    这个函数返回标准的OpenAI客户端，但配置了更好的连接参数
    """
    # 创建自定义HTTP客户端
    http_client = httpx.Client(
        timeout=60.0,
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        verify=True,
        transport=httpx.HTTPTransport(retries=2),
    )

    return OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)


def safe_api_call(func, *args, max_retries=3, **kwargs):
    """
    安全的API调用包装器

    Args:
        func: 要调用的函数
        max_retries: 最大重试次数
        *args, **kwargs: 传递给函数的参数

    Returns:
        函数的返回值，或在失败时返回错误信息
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            error_msg = str(e).lower()

            # 检查是否是连接相关错误
            connection_errors = [
                "connection error",
                "ssl",
                "timeout",
                "eof occurred",
                "connection reset",
                "connection refused",
            ]

            is_connection_error = any(err in error_msg for err in connection_errors)

            if is_connection_error and attempt < max_retries - 1:
                wait_time = (2**attempt) + 1
                logger.warning(
                    f"API调用失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
                )
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                continue
            else:
                break

    # 所有重试都失败了
    logger.error(f"API调用最终失败: {str(last_exception)}")
    return f"API调用失败: {str(last_exception)}"
