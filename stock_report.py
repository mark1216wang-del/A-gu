import akshare as ak
import datetime
import requests
import os

def get_data():
    # 1. 获取个股（以宁德时代、贵州茅台为例）
    df_spot = ak.stock_zh_a_spot_em()
    watch_list = ["300750", "600519"]
    stocks = df_spot[df_spot["代码"].isin(watch_list)]
    
    # 2. 获取人气榜 Top 10
    hot_df = ak.stock_hot_rank_em().head(10)
    
    # 3. 构造 Markdown 内容
    today = datetime.date.today().strftime("%Y-%m-%d")
    md_content = f"# 📈 每日复盘报告 ({today})\n\n"
    
    md_content += "## 🎯 自选股表现\n| 名称 | 最新价 | 涨跌幅 | 成交额 |\n| --- | --- | --- | --- |\n"
    for _, row in stocks.iterrows():
        md_content += f"| {row['名称']} | {row['最新价']} | {row['涨跌幅']}% | {row['成交额']/1e8:.2f}亿 |\n"
    
    md_content += "\n## 🔥 东财人气榜 Top 10\n"
    for i, row in hot_df.iterrows():
        md_content += f"{i+1}. **{row['股票名称']}** ({row['股票代码']}) - 热度: {row['热度值']}\n"
        
    return md_content, today

def send_feishu(content):
    webhook = os.getenv("FEISHU_WEBHOOK")
    if webhook:
        payload = {"msg_type": "text", "content": {"text": content}}
        requests.post(webhook, json=payload)

if __name__ == "__main__":
    report, date_str = get_data()
    
    # 保存为文件（供 Obsidian 同步）
    file_path = f"Stocks/{date_str}.md"
    os.makedirs("Stocks", exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    # 同时发给飞书
    send_feishu(report)
