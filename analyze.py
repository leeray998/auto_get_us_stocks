import yfinance as yf
import pandas as pd
import os

def run_analysis():
    # 1. 读取日期配置
    if not os.path.exists("config.txt"):
        print("Error: config.txt not found")
        return
    with open("config.txt", "r") as f:
        target_date = f.read().strip()

    # 2. 读取股票列表
    if not os.path.exists("stocks.txt"):
        print("Error: stocks.txt not found")
        return
    with open("stocks.txt", "r") as f:
        tickers = [line.strip() for line in f if line.strip()]

    results = []
    for symbol in tickers:
        try:
            tk = yf.Ticker(symbol)
            # 获取季度损益表
            df_q = tk.quarterly_income_stmt
            if df_q is None or df_q.empty:
                continue
                
            df_q.columns = pd.to_datetime(df_q.columns)
            
            # 过滤：只保留目标日期之前发布的财报，并按时间倒序
            valid_cols = df_q.loc[:, df_q.columns < target_date].T
            valid_cols = valid_cols.sort_index(ascending=False)
            
            if len(valid_cols) >= 3:
                # 提取最近三个季度营收 (Q0 是最接近 target_date 的)
                rev0 = valid_cols['Total Revenue'].iloc[0] 
                rev1 = valid_cols['Total Revenue'].iloc[1] 
                rev2 = valid_cols['Total Revenue'].iloc[2] 
                
                # 计算环比 (QoQ)
                qoq = (rev0 - rev1) / rev1
                
                # 计算同比 (YoY) - 找去年同季 (往前数第4个间隔)
                yoy_str = "N/A"
                if len(valid_cols) >= 5:
                    rev_yoy = valid_cols['Total Revenue'].iloc[4]
                    yoy_str = f"{(rev0 - rev_yoy) / rev_yoy:.2%}"

                results.append({
                    "Symbol": symbol,
                    "Latest Report": valid_cols.index[0].strftime('%Y-%m-%d'),
                    "Revenue (Latest)": f"{rev0:,.0f}",
                    "Revenue (Q-1)": f"{rev1:,.0f}",
                    "Revenue (Q-2)": f"{rev2:,.0f}",
                    "QoQ": f"{qoq:+.2%}",
                    "YoY": yoy_str
                })
        except Exception as e:
            continue

    if results:
        final_df = pd.DataFrame(results)
        # 显式输出 Markdown 格式
        print(final_df.to_markdown(index=False))
    else:
        print("No data found for the given date and tickers.")

if __name__ == "__main__":
    run_analysis()
