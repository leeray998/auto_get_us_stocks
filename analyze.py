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
        tickers = [line.strip() for line in f if line.strip()]

    # 将输入的字符串日期转为 Pandas 时间格式，方便对比
    target_dt = pd.to_datetime(target_date_str)

    results = []
    for symbol in tickers:
        try:
            print(f"正在分析: {symbol}...")
            tk = yf.Ticker(symbol)
            # 获取原始报表
            df_q = tk.quarterly_income_stmt
            if df_q is None or df_q.empty:
                continue
            
            # 转置：行变成日期，列变成科目
            df_all = df_q.T
            # 确保索引是日期格式（去掉时区干扰）
            df_all.index = pd.to_datetime(df_all.index).tz_localize(None)
            # 按日期从新到旧排序
            df_all = df_all.sort_index(ascending=False)
            
            # 【关键修改】：过滤掉所有晚于 target_date 的数据
            # 这样剩下的第一行就是“目标日期前最近的一期财报”
            valid_df = df_all[df_all.index <= target_dt]

            if len(valid_df) >= 1:
                # 尝试取 5 个季度的数据（前 4 个展示，第 5 个算同比）
                revs = []
                for i in range(5):
                    if len(valid_df) > i:
                        val = valid_df['Total Revenue'].iloc[i]
                        revs.append(val if pd.notna(val) else None)
                    else:
                        revs.append(None)

                # 计算 QoQ
                qoq_str = "N/A"
                if revs[0] and revs[1]:
                    qoq_str = f"{(revs[0] - revs[1]) / revs[1]:+.2%}"

                # 计算 YoY (与第 5 个数据比，即去年同期)
                yoy_str = "N/A"
                if revs[0] and revs[4]:
                    yoy_str = f"{(revs[0] - revs[4]) / revs[4]:+.2%}"

                results.append({
                    "Symbol": symbol,
                    "Report_Date": valid_df.index[0].strftime('%Y-%m-%d'),
                    "Rev_Latest": revs[0],
                    "Rev_Q-1": revs[1],
                    "Rev_Q-2": revs[2],
                    "Rev_Q-3": revs[3],
                    "QoQ": qoq_str,
                    "YoY": yoy_str
                })
        except Exception as e:
            print(f"{symbol} 处理失败: {e}")
            continue

    # --- 强力保存逻辑 (优化版) ---
    if results:
        final_df = pd.DataFrame(results)
        
        # 强制转换营收列为数字，并处理缺失值
        cols_to_fix = ["Rev_Latest", "Rev_Q-1", "Rev_Q-2", "Rev_Q-3"]
        for col in cols_to_fix:
            # errors='coerce' 会把无法转的变成 NaN
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
        
        # 导出设置：
        # 1. float_format='%.0f' 保证不出现小数点和 E+
        # 2. quoting=1 (csv.QUOTE_NONNUMERIC) 确保长数字被正确对待
        final_df.to_csv("report.csv", index=False, float_format='%.0f')
        
        print("✅ 格式优化完成！")
        print(final_df.to_markdown(index=False))
    else:
        print("未找到符合日期要求的数据。")

if __name__ == "__main__":
    run_analysis()
