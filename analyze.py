import yfinance as yf
import pandas as pd
import os

def run_analysis():
    # 1. 读取配置
    if not os.path.exists("config.txt") or not os.path.exists("stocks.txt"):
        print("Error: config.txt or stocks.txt missing")
        return
    
    with open("config.txt", "r") as f:
        target_date = f.read().strip()
    with open("stocks.txt", "r") as f:
        tickers = [line.strip() for line in f if line.strip()]

    results = []
    for symbol in tickers:
        try:
            print(f"正在抓取: {symbol}...")
            tk = yf.Ticker(symbol)
            df_q = tk.quarterly_income_stmt
            
            if df_q is None or df_q.empty:
                print(f"警告: {symbol} 财务报表为空")
                continue
            
            # 转置并整理日期
            df_q.columns = pd.to_datetime(df_q.columns)
            valid_data = df_q.T.sort_index(ascending=False)
            
            # 过滤早于 target_date 的数据
            valid_data = valid_data[valid_data.index < target_date]
            
            if len(valid_data) >= 1:
                # 提取最近 4 个季度营收
                revs = []
                for i in range(4):
                    if len(valid_data) > i:
                        revs.append(valid_data['Total Revenue'].iloc[i])
                    else:
                        revs.append(None) # 数据不足时填充空值

                # 计算 QoQ (环比)
                qoq_str = "N/A"
                if revs[0] and revs[1]:
                    qoq_str = f"{(revs[0] - revs[1]) / revs[1]:+.2%}"

                # 计算 YoY (同比) - 至少需要 5 个季度数据来对比去年同期
                yoy_str = "N/A"
                if len(valid_data) >= 5:
                    rev_ly = valid_data['Total Revenue'].iloc[4] # 去年同期
                    if rev_ly:
                        yoy_str = f"{(revs[0] - rev_ly) / rev_ly:+.2%}"

                results.append({
                    "Symbol": symbol,
                    "Report_Date": valid_data.index[0].strftime('%Y-%m-%d'),
                    "Rev_Latest": revs[0],
                    "Rev_Q-1": revs[1],
                    "Rev_Q-2": revs[2],
                    "Rev_Q-3": revs[3],
                    "QoQ": qoq_str,
                    "YoY": yoy_str
                })
        except Exception as e:
            print(f"处理 {symbol} 时出错: {e}")
            continue

    # 2. 保存并格式化输出
    if results:
        final_df = pd.DataFrame(results)
    else:
        final_df = pd.DataFrame(columns=["Symbol", "Report_Date", "Rev_Latest", "QoQ", "YoY"])

    # 关键修改：float_format='%.0f' 彻底解决 2.25E+09 这种科学计数法问题
    final_df.to_csv("report.csv", index=False, float_format='%.0f')
    print("分析完成，报告已生成。")
    print(final_df.to_markdown(index=False))

if __name__ == "__main__":
    run_analysis()
