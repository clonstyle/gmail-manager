#!/bin/bash
# 每周邮件统计报告 - 发送到飞书群
# 会话ID: oc_fdb356a2abe58650e743f3545d223678

REPORT_FILE="/tmp/weekly_email_report_$(date +%Y%m%d).txt"

cd /root/.openclaw/skills/gmail-manager

# 生成邮件摘要报告
python3 email_manager_v2.py --summary > "$REPORT_FILE" 2>&1

# 读取报告内容
REPORT_CONTENT=$(cat "$REPORT_FILE")

# 使用 OpenClaw message 工具发送到飞书群
openclaw message send \
  --channel feishu \
  --target "chat:oc_fdb356a2abe58650e743f3545d223678" \
  --message "📧 每周邮件统计报告

$REPORT_CONTENT

---
报告时间: $(date '+%Y-%m-%d %H:%M:%S')"

# 清理临时文件
rm -f "$REPORT_FILE"
