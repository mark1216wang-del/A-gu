import akshare as ak
import datetime
import requests
import os
import time

# 1. 增加浏览器伪装，降低被断开连接的风险
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "http://quote.eastmoney.com/"
}

def get_data_with_retry(retries=3):
    """增加重试机制，防止单次请求失败导致整个流程中断"""
    for i in range(retries):
        try:
            # 获取实时行情 (A股)
            # 如果东财接口持续报错，可以尝试更换为 ak.stock_zh_a_spot_qq() 腾讯接口
            df_spot = ak.stock_zh_a_spot_em()
            
            # 获取人气榜
            hot_df = ak.stock_hot_rank_em()
            
            if not df_spot.empty and not hot_df.empty:
                return df_spot, hot_df
        except Exception as e:
            print(f"第 {i+1} 次获取数据失败: {e}")
            time.sleep(5) # 等待5秒后重试
    return None, None

def generate_report():
    df_spot, hot_df = get_data_with_retry()
    
    if df_spot is None:
        return "❌ 数据获取失败，请检查网络或接口状态。", ""

    # 设定关注列表
    watch_list = ["300750", "600519", "000001"] # 宁德、茅台、平安
    stocks = df_spot[df_spot["代码"].isin(watch_list)]
    
    today = datetime.date.today().strftime("%Y-%m-%d")
    md_content = f"# 📈 每日复盘报告 ({today})\n\n"
    
    # 自选股部分
    md_content += "## 🎯 自选股表现\n| 名称 | 最新价 | 涨跌幅 | 成交额 |\n| --- | --- | --- | --- |\n"
    for _, row in stocks.iterrows():
        # 转换成交额单位为亿
        turnover = f"{row['成交额']/1e8:.2f}亿" if '成交额' in row else "N/A"
        md_content += f"| {row['名称']} | {row['最新价']} | {row['涨跌幅']}% | {turnover} |\n"
    
    # 人气榜部分 (取Top 10)
    md_content += "\n## 🔥 东财人气榜 Top 10\n"
    top_10_hot = hot_df.head(10)
    for i, row in top_10_hot.iterrows():
        md_content += f"{i+1}. **{row['股票名称']}** ({row['股票代码']}) - 热度: {row['热度值']}\n"
        
    return md_content, today

def send_feishu(content):
    webhook = os.getenv("FEISHU_WEBHOOK")
    if not webhook:
        print("未配置 FEISHU_WEBHOOK，跳过推送。")
        return
    
    # 飞书机器人消息格式
    payload = {
        "msg_type": "text",
        "content": {"text": content}
    }
    
    try:
        # 增加 timeout 防止 GitHub Actions 卡死
        response = requests.post(webhook, json=payload, timeout=15)
        response.raise_for_status()
        print("飞书消息推送成功！")
    except Exception as e:
        print(f"飞书推送失败: {e}")

if __name__ == "__main__":
    print("开始获取金融数据...")
    report, date_str = generate_report()
    
    # 1. 保存到本地目录 (供 Obsidian 使用)
    if report and date_str:
        os.makedirs("Stocks", exist_ok=True)
        file_path = f"Stocks/{date_str}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告已保存至: {file_path}")
        
        # 2. 推送至飞书
        send_feishu(report)
