import akshare as ak
import datetime
import requests
import os

# --- 配置区 ---
# 在这里填入你关注的股票代码列表
WATCH_LIST = ["300750", "600519", "000001", "300059"] 

def get_realtime_data():
    # 获取全 A 股实时行情
    df_spot = ak.stock_zh_a_spot_em()
    
    # 筛选关注的股票
    stocks = df_spot[df_spot["代码"].isin(WATCH_LIST)]
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md_content = f"# ⚡ 实时行情快报\n\n"
    md_content += f"> 更新时间：{now}\n\n"
    
    md_content += "| 股票名称 | 最新价 | 涨跌幅 | 成交额 | 最高/最低 |\n"
    md_content += "| :--- | :--- | :--- | :--- | :--- |\n"
    
    feishu_text = f"⚡ 实时行情 ({now})\n"
    
    for _, row in stocks.iterrows():
        status = "🔴" if row['涨跌幅'] > 0 else "🟢"
        md_content += f"| {row['名称']} | {row['最新价']} | {status} {row['涨跌幅']}% | {row['成交额']/1e8:.2f}亿 | {row['最高']}/{row['最低']} |\n"
        feishu_text += f"\n{status} {row['名称']}: {row['最新价']} ({row['涨跌幅']}%)"
    
    return md_content, feishu_text, now

def send_to_feishu(text):
    webhook = os.getenv("FEISHU_WEBHOOK")
    if webhook:
        payload = {"msg_type": "text", "content": {"text": text}}
        try:
            requests.post(webhook, json=payload, timeout=10)
        except Exception as e:
            print(f"发送飞书失败: {e}")

if __name__ == "__main__":
    md_report, fs_text, timestamp = get_realtime_data()
    
    # 1. 保存 Markdown 用于 GitHub 提交 (Obsidian 归档)
    folder = "Realtime_Logs"
    os.makedirs(folder, exist_ok=True)
    filename = f"{folder}/Snapshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md_report)
    
    # 2. 发送实时消息到飞书 (手机端即时查看)
    send_to_feishu(fs_text)
    print("实时数据获取并推送成功！")
