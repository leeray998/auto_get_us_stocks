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
            tk = yf.Ticker(symbol)
            df_q = tk.quarterly_income_stmt
            if df_q is None or df_q.empty:
                continue
            
            df_q.columns = pd.to_datetime(df_q.columns)
            # 过滤日期并排序
            valid_cols = df_q.loc[:, df_q.columns < target_date].T
            valid_cols = valid_cols.sort_index(ascending=False)
            
            if len(valid_cols) >= 2:
                rev0 = valid_cols['Total Revenue'].iloc[0]
                rev1 = valid_cols['Total Revenue'].iloc[1]
                rev2 = valid_cols['Total Revenue'].iloc[2] if len(valid_cols) >= 3 else None
                
                qoq = (rev0 - rev1) / rev1
                yoy_str = "N/A"
                if len(valid_cols) >= 5:
                    rev_yoy = valid_cols['Total Revenue'].iloc[4]
                    yoy_str = f"{(rev0 - rev_yoy) / rev_yoy:+.2%}"

                results.append({
                    "Symbol": symbol,
                    "Report_Date": valid_cols.index[0].strftime('%Y-%m-%d'),
                    "Revenue_Latest": round(rev0, 2),
                    "Revenue_Q-1": round(rev1, 2),
                    "Revenue_Q-2": round(rev2, 2) if rev2 is not None else "nan",
                    "QoQ": f"{qoq:+.2%}",
                    "YoY": yoy_str
                })
        except Exception:
            continue

    # 无论是否有结果，都生成 report.csv 以防止 Action 报错
    if results:
        final_df = pd.DataFrame(results)
    else:
        # 如果没有数据，生成一个带表头的空 CSV
        final_df = pd.DataFrame(columns=["Symbol", "Report_Date", "Revenue_Latest", "QoQ", "YoY"])
        print("Warning: No valid data found for these tickers.")

    # 核心步骤：保存文件
    final_df.to_csv("report.csv", index=False)
    print(final_df.to_markdown(index=False))

if __name__ == "__main__":
    run_analysis()
