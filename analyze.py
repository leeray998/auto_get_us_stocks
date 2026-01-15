import yfinance as yf
import pandas as pd
import os

def run_analysis():
    # 1. 检查必要配置文件
    if not os.path.exists("config.txt") or not os.path.exists("stocks.txt"):
        print("❌ 错误: 缺少 config.txt 或 stocks.txt")
        return
    
    # 读取目标日期（以此日期为基准回溯）
    with open("config.txt", "r") as f:
        target_date_str = f.read().strip()
    
    # 读取股票代码列表
    with open("stocks.txt", "r") as f:
        tickers = [line.strip().upper() for line in f if line.strip()]

    # 将输入的字符串日期转为标准时间格式
    target_dt = pd.to_datetime(target_date_str)
    results = []

    for symbol in tickers:
        try:
            print(f"🔍 正在获取数据: {symbol}...")
            tk = yf.Ticker(symbol)
            
            # 获取季度利润表
            df_q = tk.quarterly_income_stmt
            if df_q is None or df_q.empty:
                print(f"⚠️ {symbol} 无法获取报表数据")
                continue
            
            # --- 数据清洗与对齐 ---
            # 转置并确保索引是去掉时区的日期格式
            df_all = df_q.T
            df_all.index = pd.to_datetime(df_all.index).tz_localize(None)
            # 按日期从新到旧排列
            df_all = df_all.sort_index(ascending=False)
            
            # 过滤：只保留在 target_dt 之前（含当天）的数据
            valid_df = df_all[df_all.index <= target_dt]

            if len(valid_df) >= 1:
                # 提取营收序列和对应的日期序列
                # 使用 .get 确保即使字段名细微不同也能抓到数据
                raw_revs = valid_df.get('Total Revenue', pd.Series())
                rev_values = raw_revs.tolist()
                date_labels = [d.strftime('%Y-%m-%d') for d in raw_revs.index]

                # 补齐长度，至少需要 5 个季度算同比（Latest, Q-1, Q-2, Q-3, LastYear）
                while len(rev_values) < 5:
                    rev_values.append(None)
                    date_labels.append("N/A")

                # --- 计算增长率 ---
                def calc_growth(current, previous):
                    if current and previous and previous != 0:
                        return f"{(current - previous) / previous:+.2%}"
                    return "N/A"

                qoq = calc_growth(rev_values[0], rev_values[1])  # 环比
                yoy = calc_growth(rev_values[0], rev_values[4])  # 同比 (与第5个数据比)

                # --- 构建结果行 ---
                # 使用具体日期作为表头，增强直观性
                row = {
                    "Symbol": symbol,
                    "Report_Date": date_labels[0],
                    "Revenue_Latest": rev_values[0],
                    f"Q-1 ({date_labels[1]})": rev_values[1],
                    f"Q-2 ({date_labels[2]})": rev_values[2],
                    f"Q-3 ({date_labels[3]})": rev_values[3],
                    "QoQ": qoq,
                    "YoY": yoy
                }
                results.append(row)
        except Exception as e:
            print(f"❌ {symbol} 处理过程中出错: {e}")
            continue

    # --- 保存与输出 ---
    if results:
        final_df = pd.DataFrame(results)
        
        # 针对营收列进行数字格式锁定，防止科学计数法
        # 获取所有以 "Rev" 或 "(" 开头的营收数据列
        numeric_cols = [c for c in final_df.columns if "Rev" in c or "(" in c]
        for col in numeric_cols:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
        
        # 保存为 CSV
        # float_format='%.0f' 强制不保留小数位且不使用科学计数法
        final_df.to_csv("report.csv", index=False, float_format='%.0f')
        
        print("\n" + "="*30)
        print("🚀 分析完成！生成的报告预览：")
        print(final_df.to_markdown(index=False))
        print("="*30)
    else:
        print("📭 未能找到符合要求的数据，未生成报告。")

if __name__ == "__main__":
    run_analysis()
