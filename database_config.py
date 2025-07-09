#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置和连接管理
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import mysql.connector
from mysql.connector import Error
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化数据库连接

        Args:
            config: 数据库配置字典
        """
        self.config = config
        self.connection = None
        self.connect()

    def connect(self):
        """建立数据库连接"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 13306),
                database=self.config.get("database", "trading_analysis"),
                user=self.config.get("user", "root"),
                password=self.config.get("password", "12345678"),
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci",
                autocommit=True,
            )
            print(
                f"✅ 数据库连接成功: {self.config.get('host')}:{self.config.get('port')}/{self.config.get('database')}"
            )
            logger.info("数据库连接成功")
        except Error as e:
            print(f"❌ 数据库连接失败: {e}")
            logger.error(f"数据库连接失败: {e}")
            raise

    def disconnect(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("数据库连接已关闭")

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """执行查询并返回结果"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Error as e:
            logger.error(f"查询执行失败: {e}")
            print(f"❌ 查询执行失败: {e}")
            raise

    def execute_update(self, query: str, params: tuple = None) -> int:
        """执行更新操作并返回影响的行数"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows
        except Error as e:
            logger.error(f"更新执行失败: {e}")
            print(f"❌ 更新执行失败: {e}")
            raise


class MessageManager:
    """消息管理器"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def save_analysis_message(
        self,
        symbol: str,
        analysis_date: str,
        message: str,
        decision_data: Dict = None,
        metadata: Dict = None,
    ) -> str:
        """
        保存分析消息到数据库

        Args:
            symbol: 股票代码
            analysis_date: 分析日期
            message: 分析消息
            decision_data: 决策数据
            metadata: 元数据

        Returns:
            str: 新创建的消息ID，失败返回None
        """
        try:
            message_id = str(uuid.uuid4())
            conversation_id = f"analysis_{symbol}_{analysis_date}"
            task_id = (
                f"task_{symbol}_{analysis_date}_{datetime.now().strftime('%H%M%S')}"
            )

            # 注释掉外键依赖，直接插入消息
            # self._ensure_conversation_exists(conversation_id, symbol, analysis_date)
            # self._ensure_task_exists(task_id, conversation_id, symbol, analysis_date)

            # 准备元数据
            full_metadata = {
                "symbol": symbol,
                "analysis_date": analysis_date,
                "decision_data": decision_data,
                "timestamp": datetime.now().isoformat(),
            }
            if metadata:
                full_metadata.update(metadata)

            query = """
            INSERT INTO messages (
                message_id, conversation_id, task_id, message_type,
                content, metadata, sequence_number
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            params = (
                message_id,
                conversation_id,
                task_id,
                "ai",  # 分析结果是AI消息
                message,
                json.dumps(full_metadata),
                1,  # 简化序号处理
            )

            affected_rows = self.db.execute_update(query, params)

            if affected_rows > 0:
                logger.info(f"保存分析消息成功: {message_id} for {symbol}")
                print(f"💾 数据库写入成功: {symbol} -> {message_id}")
                return message_id
            else:
                logger.warning(f"保存分析消息失败: 没有行被影响")
                print(f"⚠️ 数据库写入失败: 没有行被影响")
                return None

        except Exception as e:
            logger.error(f"保存分析消息失败: {e}")
            print(f"❌ 数据库写入异常: {e}")
            return None

    def _ensure_conversation_exists(
        self, conversation_id: str, symbol: str, analysis_date: str
    ):
        """确保会话存在"""
        try:
            # 检查会话是否存在
            check_query = (
                "SELECT conversation_id FROM conversations WHERE conversation_id = %s"
            )
            result = self.db.execute_query(check_query, (conversation_id,))

            if not result:
                # 创建会话
                insert_query = """
                INSERT INTO conversations (conversation_id, title, description, status)
                VALUES (%s, %s, %s, %s)
                """
                params = (
                    conversation_id,
                    f"{symbol} 股票分析",
                    f"{symbol} 在 {analysis_date} 的分析会话",
                    "active",
                )
                self.db.execute_update(insert_query, params)
                print(f"✅ 创建会话: {conversation_id}")
        except Exception as e:
            logger.warning(f"确保会话存在失败: {e}")

    def _ensure_task_exists(
        self, task_id: str, conversation_id: str, symbol: str, analysis_date: str
    ):
        """确保任务存在"""
        try:
            # 检查任务是否存在
            check_query = "SELECT task_id FROM tasks WHERE task_id = %s"
            result = self.db.execute_query(check_query, (task_id,))

            if not result:
                # 创建任务
                insert_query = """
                INSERT INTO tasks (task_id, conversation_id, task_type, title, description, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                params = (
                    task_id,
                    conversation_id,
                    "analysis",
                    f"{symbol} 分析任务",
                    f"{symbol} 在 {analysis_date} 的分析任务",
                    "completed",
                )
                self.db.execute_update(insert_query, params)
                print(f"✅ 创建任务: {task_id}")
        except Exception as e:
            logger.warning(f"确保任务存在失败: {e}")

    def get_analysis_history(self, symbol: str, limit: int = 10) -> List[Dict]:
        """获取股票的分析历史"""
        try:
            query = """
            SELECT message_id, content, metadata, created_at
            FROM messages 
            WHERE JSON_EXTRACT(metadata, '$.symbol') = %s
            AND message_type = 'ai'
            ORDER BY created_at DESC
            LIMIT %s
            """
            return self.db.execute_query(query, (symbol, limit))
        except Exception as e:
            logger.error(f"获取分析历史失败: {e}")
            print(f"❌ 获取分析历史失败: {e}")
            return []


# 默认数据库配置
DEFAULT_DB_CONFIG = {
    "host": "localhost",
    "port": 13306,
    "database": "trading_analysis",
    "user": "root",
    "password": "12345678",
}


def get_db_config() -> Dict[str, Any]:
    """获取数据库配置"""
    # 优先从环境变量读取
    config = {
        "host": os.getenv("DB_HOST", DEFAULT_DB_CONFIG["host"]),
        "port": int(os.getenv("DB_PORT", DEFAULT_DB_CONFIG["port"])),
        "database": os.getenv("DB_NAME", DEFAULT_DB_CONFIG["database"]),
        "user": os.getenv("DB_USER", DEFAULT_DB_CONFIG["user"]),
        "password": os.getenv("DB_PASSWORD", DEFAULT_DB_CONFIG["password"]),
    }

    print(
        f"📋 数据库配置: {config['user']}@{config['host']}:{config['port']}/{config['database']}"
    )
    return config
