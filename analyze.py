import yfinance as yf
import pandas as pd
import os

def run_analysis():
    # 1. 读取日期配置
    if not os.path.exists("config.txt"):
        print("错误: 找不到 config.txt")
        return
    with open("config.txt", "r") as f:
        target_date = f.read().strip()

    # 2. 读取股票列表
    if not os.path.exists("stocks.txt"):
        print("错误: 找不到 stocks.txt")
        return
    with open("stocks.txt", "r") as f:
        tickers = [line.strip() for line in f if line.strip()]

    print(f"### 截止日期 {target_date} 前的财报深度分析 (含三季环比+同比) ###\n")
    
    results = []
    for symbol in tickers:
        try:
            tk = yf.Ticker(symbol)
            # 获取季度损益表
            df_q = tk.get_income_stmt(freq='quarterly')
            df_q.columns = pd.to_datetime(df_q.columns)
            
            # 过滤：只保留目标日期之前发布的财报
            # 按日期从新到旧排序
            valid_cols = df_q.loc[:, df_q.columns < target_date].T
            valid_cols = valid_cols.sort_index(ascending=False)
            
            if len(valid_cols) >= 3:
                # 提取最近三个季度营收
                rev0 = valid_cols['Total Revenue'].iloc[0] # 最新季 (Q0)
                rev1 = valid_cols['Total Revenue'].iloc[1] # 前一季 (Q-1)
                rev2 = valid_cols['Total Revenue'].iloc[2] # 前二季 (Q-2)
                
                # 计算环比 (QoQ)
                qoq = (rev0 - rev1) / rev1
                
                # 计算同比 (YoY) - 找去年同季（通常是第5行，即往回数4季）
                yoy_val = "N/A"
                if len(valid_cols) >= 5:
                    rev_year_ago = valid_cols['Total Revenue'].iloc[4]
                    yoy_val = f"{(rev0 - rev_year_ago) / rev_year_ago:.2%}"

                results.append({
                    "代码": symbol,
                    "最新报告期": valid_cols.index[0].strftime('%Y-%m-%d'),
                    "最新季营收": f"{rev0:,.0f}",
                    "Q-1营收": f"{rev1:,.0f}",
                    "Q-2营收": f"{rev2:,.0f}",
                    "环比(QoQ)": f"{qoq:.2%}",
                    "同比(YoY)": yoy_val
                })
        except Exception as e:
            # 打印错误方便调试，但不中断程序
            print(f"跳过 {symbol}: 缺少数据或解析错误")
            continue

    if results:
        final_df = pd.DataFrame(results)
        print(final_df.to_markdown(index=False))
    else:
        print("未找到符合条件的数据。")

if __name__ == "__main__":
    run_analysis()
