import yfinance as yf
import pandas as pd
import os

def run_analysis():
    # 1. 读取配置
    if not os.path.exists("config.txt") or not os.path.exists("stocks.txt"):
        print("Error: config.txt or stocks.txt missing")
        return
    
    with open("config.txt", "r") as f:
        target_date_str = f.read().strip()
    with open("stocks.txt", "r") as f:
        tickers = [line.strip().upper() for line in f if line.strip()]

    target_dt = pd.to_datetime(target_date_str)

    results = []
    for symbol in tickers:
        try:
            print(f"正在分析: {symbol}...")
            tk = yf.Ticker(symbol)
            df_q = tk.quarterly_income_stmt
            if df_q is None or df_q.empty:
                continue
            
            df_all = df_q.T
            df_all.index = pd.to_datetime(df_all.index).tz_localize(None)
            df_all = df_all.sort_index(ascending=False)
            
            # 过滤掉晚于目标的日期
            valid_df = df_all[df_all.index <= target_dt]

            if len(valid_df) >= 1:
                # 提取营收和对应的日期
                revs = []
                dates = []
                for i in range(5):
                    if len(valid_df) > i:
                        val = valid_df['Total Revenue'].iloc[i]
                        dt = valid_df.index[i].strftime('%Y-%m-%d')
                        revs.append(val if pd.notna(val) else None)
                        dates.append(dt)
                    else:
                        revs.append(None)
                        dates.append(f"No_Data_{i}")

                # 计算 QoQ 和 YoY
                qoq_str = "N/A"
                if revs[0] and revs[1]:
                    qoq_str = f"{(revs[0] - revs[1]) / revs[1]:+.2%}"

                yoy_str = "N/A"
                if revs[0] and revs[4]:
                    yoy_str = f"{(revs[0] - revs[4]) / revs[4]:+.2%}"

                # --- 核心改动：构建动态表头的字典 ---
                row = {
                    "Symbol": symbol,
                    "Report_Date": dates[0],
                    "Rev_Latest": revs[0],
                    f"Q-1({dates[1]})": revs[1], # 这里把日期塞进表头了
                    f"Q-2({dates[2]})": revs[2],
                    f"Q-3({dates[3]})": revs[3],
                    "QoQ": qoq_str,
                    "YoY": yoy_str
                }
                results.append(row)
        except Exception as e:
            print(f"{symbol} 处理失败: {e}")
            continue

    if results:
        final_df = pd.DataFrame(results)
        
        # 自动识别所有营收列进行格式化（包含带日期的列）
        for col in final_df.columns:
            if "Rev" in col or "Q-" in col:
                final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
        
        # 保存 CSV
        final_df.to_csv("report.csv", index=False, float_format='%.0f')
        
        print("✅ 格式优化完成！")
        print(final_df.to_markdown(index=False))
    else:
        print("未找到符合日期要求的数据。")

if __name__ == "__main__":
    run_analysis()
