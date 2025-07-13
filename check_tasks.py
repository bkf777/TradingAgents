#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询数据库中的任务
"""

from database_config import DatabaseManager, get_db_config

def check_tasks():
    try:
        db = DatabaseManager(get_db_config())
        results = db.execute_query('SELECT task_id, ticker, title, status FROM tasks ORDER BY created_at DESC LIMIT 5')
        
        print("📋 最近的5个任务:")
        for i, row in enumerate(results, 1):
            print(f"{i}. Task ID: {row['task_id']}")
            print(f"   Ticker: {row['ticker']}")
            print(f"   Title: {row['title']}")
            print(f"   Status: {row['status']}")
            print()
            
        return results
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return []

if __name__ == "__main__":
    check_tasks()
