#!/usr/bin/env python3
"""
每周邮件统计报告 - 发送到飞书群
"""

import subprocess
import json
import os
from datetime import datetime, timedelta

# 飞书群配置
FEISHU_CHAT_ID = "oc_fdb356a2abe58650e743f3545d223678"

def run_email_summary():
    """运行邮件摘要"""
    result = subprocess.run(
        ["python3", "email_manager_v2.py", "--summary"],
        cwd="/root/.openclaw/skills/gmail-manager",
        capture_output=True,
        text=True
    )
    return result.stdout + result.stderr

def send_to_feishu(title, content):
    """发送消息到飞书群"""
    message = f"{title}\n\n{content}\n\n---\n📅 报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    try:
        result = subprocess.run(
            ["openclaw", "message", "send",
             "--channel", "feishu",
             "--target", f"chat:{FEISHU_CHAT_ID}",
             "--message", message],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("✅ 报告已发送到飞书群")
            return True
        else:
            print(f"❌ 发送失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 发送错误: {e}")
        return False

def main():
    print("📧 生成每周邮件统计报告...")
    
    # 获取上周时间范围
    today = datetime.now()
    last_week = today - timedelta(days=7)
    week_range = f"{last_week.strftime('%Y-%m-%d')} 至 {today.strftime('%Y-%m-%d')}"
    
    # 生成报告
    report_content = run_email_summary()
    
    # 构建标题
    title = f"📊 每周邮件统计报告 ({week_range})"
    
    # 发送
    if send_to_feishu(title, report_content):
        print("✅ 完成")
    else:
        print("❌ 失败")

if __name__ == "__main__":
    main()
