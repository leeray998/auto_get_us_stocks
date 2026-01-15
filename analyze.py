import yfinance as yf
import pandas as pd
import os

def run_analysis():
    # 1. 读取配置
    if not os.path.exists("config.txt") or not os.path.exists("stocks.txt"):
        print("❌ 错误: 缺少配置文件")
        return
    
    with open("config.txt", "r") as f:
        target_date_str = f.read().strip()
    with open("stocks.txt", "r") as f:
        tickers = [line.strip().upper() for line in f if line.strip()]

    target_dt = pd.to_datetime(target_date_str)
    results = []

    for symbol in tickers:
        try:
            print(f"🔍 正在提取 (yfinance): {symbol}...")
            tk = yf.Ticker(symbol)
            
            # 强制从原始对象提取季度利润表
            df_q = tk.get_financials(freq='quarterly') 
            if df_q is None or df_q.empty:
                # 备用：如果上面的方法不行，用旧方法
                df_q = tk.quarterly_income_stmt
            
            if df_q is None or df_q.empty:
                print(f"⚠️ {symbol} 雅虎数据库暂无数据")
                continue
            
            # 转置处理：行变日期
            df_all = df_q.T
            df_all.index = pd.to_datetime(df_all.index).tz_localize(None)
            df_all = df_all.sort_index(ascending=False)
            
            # 过滤：只看目标日期之前的数据
            valid_df = df_all[df_all.index <= target_dt]

            if len(valid_df) >= 1:
                # 寻找营收字段（兼容不同公司的命名习惯）
                search_cols = ['Total Revenue', 'Operating Revenue', 'Revenue']
                target_col = next((c for c in search_cols if c in valid_df.columns), None)
                
                if not target_col:
                    print(f"⚠️ {symbol} 找不到营收列名")
                    continue

                rev_series = valid_df[target_col]
                rev_values = rev_series.tolist()
                date_labels = [d.strftime('%Y-%m-%d') for d in rev_series.index]

                # 补齐到 5 个季度以便算 YoY
                while len(rev_values) < 5:
                    rev_values.append(None)
                    date_labels.append("N/A")

                # 计算函数
                def calc_pct(cur, prev):
                    if cur and prev and prev != 0:
                        return f"{(cur - prev) / prev:+.2%}"
                    return "N/A"

                # 构建动态字典
                row = {
                    "Symbol": symbol,
                    "Report_Date": date_labels[0],
                    "Rev_Latest": rev_values[0],
                    f"Q-1({date_labels[1]})": rev_values[1],
                    f"Q-2({date_labels[2]})": rev_values[2],
                    f"Q-3({date_labels[3]})": rev_values[3],
                    "QoQ": calc_pct(rev_values[0], rev_values[1]),
                    "YoY": calc_pct(rev_values[0], rev_values[4])
                }
                results.append(row)
                print(f"✅ {symbol} 解析完成")

        except Exception as e:
            print(f"❌ {symbol} 出错: {e}")

    # 3. 保存
    if results:
        final_df = pd.DataFrame(results)
        # 强制处理长数字显示问题
        num_cols = [c for c in final_df.columns if "Rev" in c or "Q-" in c]
        for col in num_cols:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
        
        final_df.to_csv("report.csv", index=False, float_format='%.0f')
        print("\n" + final_df.to_markdown(index=False))
    else:
        print("📭 没抓到任何数据，请检查 stocks.txt 里的代码是否正确。")

if __name__ == "__main__":
    run_analysis()
