#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AKShare集成功能
验证所有替换后的数据获取功能是否正常工作
"""

import sys
import os
import traceback
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_akshare_stock_data():
    """测试股票历史数据获取"""
    print("=" * 50)
    print("测试股票历史数据获取")
    print("=" * 50)
    
    try:
        from tradingagents.dataflows.akshare_utils import get_akshare_stock_data
        
        # 测试中国股票
        symbol = "000001"  # 平安银行
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        print(f"获取股票数据: {symbol} from {start_date} to {end_date}")
        data = get_akshare_stock_data(symbol, start_date, end_date)
        
        if not data.empty:
            print(f"✅ 成功获取数据，共 {len(data)} 条记录")
            print("数据列:", list(data.columns))
            print("最新几条数据:")
            print(data.head())
        else:
            print("❌ 未获取到数据")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        traceback.print_exc()

def test_akshare_stock_info():
    """测试股票基本信息获取"""
    print("\n" + "=" * 50)
    print("测试股票基本信息获取")
    print("=" * 50)
    
    try:
        from tradingagents.dataflows.akshare_utils import get_akshare_stock_info
        
        symbol = "000001"  # 平安银行
        print(f"获取股票信息: {symbol}")
        info = get_akshare_stock_info(symbol)
        
        if info:
            print("✅ 成功获取股票信息")
            for key, value in list(info.items())[:10]:  # 只显示前10个字段
                print(f"  {key}: {value}")
        else:
            print("❌ 未获取到股票信息")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        traceback.print_exc()

def test_akshare_news():
    """测试股票新闻获取"""
    print("\n" + "=" * 50)
    print("测试股票新闻获取")
    print("=" * 50)
    
    try:
        from tradingagents.dataflows.akshare_utils import get_akshare_news
        
        symbol = "000001"  # 平安银行
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        print(f"获取股票新闻: {symbol} from {start_date} to {end_date}")
        news = get_akshare_news(symbol, start_date, end_date)
        
        if news:
            print("✅ 成功获取新闻")
            print("新闻内容预览:")
            print(news[:500] + "..." if len(news) > 500 else news)
        else:
            print("❌ 未获取到新闻")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        traceback.print_exc()

def test_interface_functions():
    """测试interface.py中的函数"""
    print("\n" + "=" * 50)
    print("测试interface.py中的函数")
    print("=" * 50)
    
    try:
        from tradingagents.dataflows.interface import get_YFin_data_online
        
        symbol = "000001"  # 平安银行
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        
        print(f"测试get_YFin_data_online: {symbol} from {start_date} to {end_date}")
        result = get_YFin_data_online(symbol, start_date, end_date)
        
        if result and not result.startswith("No data found"):
            print("✅ 成功获取数据")
            print("数据预览:")
            print(result[:500] + "..." if len(result) > 500 else result)
        else:
            print("❌ 未获取到数据或数据为空")
            print(f"返回结果: {result}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        traceback.print_exc()

def test_finnhub_news():
    """测试新闻获取函数"""
    print("\n" + "=" * 50)
    print("测试新闻获取函数")
    print("=" * 50)
    
    try:
        from tradingagents.dataflows.interface import get_finnhub_news
        
        ticker = "000001"  # 平安银行
        curr_date = datetime.now().strftime("%Y-%m-%d")
        look_back_days = 7
        
        print(f"测试get_finnhub_news: {ticker}, 回看 {look_back_days} 天")
        result = get_finnhub_news(ticker, curr_date, look_back_days)
        
        if result:
            print("✅ 成功获取新闻")
            print("新闻预览:")
            print(result[:500] + "..." if len(result) > 500 else result)
        else:
            print("❌ 未获取到新闻")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        traceback.print_exc()

def test_financial_data():
    """测试财务数据获取"""
    print("\n" + "=" * 50)
    print("测试财务数据获取")
    print("=" * 50)
    
    try:
        from tradingagents.dataflows.interface import get_simfin_balance_sheet
        
        ticker = "000001"  # 平安银行
        freq = "annual"
        curr_date = datetime.now().strftime("%Y-%m-%d")
        
        print(f"测试get_simfin_balance_sheet: {ticker} ({freq})")
        result = get_simfin_balance_sheet(ticker, freq, curr_date)
        
        if result:
            print("✅ 成功获取财务数据")
            print("数据预览:")
            print(result[:500] + "..." if len(result) > 500 else result)
        else:
            print("❌ 未获取到财务数据")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        traceback.print_exc()

def main():
    """主测试函数"""
    print("开始测试AKShare集成功能...")
    print(f"测试时间: {datetime.now()}")
    
    # 运行所有测试
    test_akshare_stock_data()
    test_akshare_stock_info()
    test_akshare_news()
    test_interface_functions()
    test_finnhub_news()
    test_financial_data()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()
