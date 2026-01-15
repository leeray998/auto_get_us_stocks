import pandas as pd
import os
import requests

def run_analysis():
    # --- 1. 配置读取 ---
    if not os.path.exists("config.txt") or not os.path.exists("stocks.txt"):
        print("❌ 错误: 缺少配置文件")
        return
    
    # 填入你的 FMP API Key (免费版即可)
    # 建议通过环境变量读取更安全，这里为了方便你直接运行
    API_KEY = "tl86gW08UvssorqG7fRdYpvsWJKtsiqu" 
    
    with open("config.txt", "r") as f:
        target_date_str = f.read().strip()
    with open("stocks.txt", "r") as f:
        tickers = [line.strip().upper() for line in f if line.strip()]

    target_dt = pd.to_datetime(target_date_str)
    results = []

    for symbol in tickers:
        try:
            print(f"🔍 正在从 FMP 获取数据: {symbol}...")
            # 获取最近 5 个季度的利润表 (FMP API)
            url = f"https://financialmodelingprep.com/api/v3/income-statement/{symbol}?period=quarter&limit=8&apikey={API_KEY}"
            response = requests.get(url)
            data = response.json()

            if not data or "Error Message" in data:
                print(f"⚠️ {symbol} 接口返回为空或错误")
                continue

            # 转换为 DataFrame 处理日期
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            
            # 过滤：只保留在目标日期之前的数据
            valid_df = df[df['date'] <= target_dt].sort_values(by='date', ascending=False)

            if len(valid_df) >= 1:
                # 提取营收和日期
                rev_values = valid_df['revenue'].tolist()
                date_labels = [d.strftime('%Y-%m-%d') for d in valid_df['date']]

                # 补齐长度
                while len(rev_values) < 5:
                    rev_values.append(None)
                    date_labels.append("N/A")

                # --- 计算增长率 ---
                def calc_growth(current, previous):
                    if current and previous and previous != 0:
                        return f"{(current - previous) / previous:+.2%}"
                    return "N/A"

                qoq = calc_growth(rev_values[0], rev_values[1])
                yoy = calc_growth(rev_values[0], rev_values[4])

                # --- 构建动态行 ---
                row = {
                    "Symbol": symbol,
                    "Report_Date": date_labels[0],
                    "Rev_Latest": rev_values[0],
                    f"Q-1 ({date_labels[1]})": rev_values[1],
                    f"Q-2 ({date_labels[2]})": rev_values[2],
                    f"Q-3 ({date_labels[3]})": rev_values[3],
                    "QoQ": qoq,
                    "YoY": yoy
                }
                results.append(row)
        except Exception as e:
            print(f"❌ {symbol} 异常: {e}")

    # --- 3. 保存逻辑 ---
    if results:
        final_df = pd.DataFrame(results)
        
        # 强制处理所有营收列为数字格式，防止科学计数法
        numeric_cols = [c for c in final_df.columns if "Rev" in c or "(" in c]
        for col in numeric_cols:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
        
        # 导出为 CSV (float_format='%.0f' 是关键)
        final_df.to_csv("report.csv", index=False, float_format='%.0f')
        
        print("\n✅ 分析完成！")
        print(final_df.to_markdown(index=False))
    else:
        print("📭 未找到数据。")

if __name__ == "__main__":
    run_analysis()
