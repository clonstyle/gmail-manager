# Gmail Manager Skill

一个功能强大的 Gmail 自动化管理工具，支持自动分类、标签、重要邮件筛选、归档、摘要、统计和垃圾邮件清理。

## 功能特性

- 📂 **自动分类** - 按主题/内容自动分类（工作、财务、社交、推广、通知、安全、订阅）
- ⭐ **重要邮件筛选** - 自动标记重要发件人和紧急邮件
- 📦 **定期归档** - 自动归档30天前的邮件
- 📝 **邮件摘要** - 生成每日/每周邮件摘要报告
- 📊 **统计报告** - 完整的邮件统计分析
- 🗑️ **垃圾邮件清理** - 自动清理推广邮件
- 🔗 **飞书通知** - 新邮件自动推送到飞书
- 📧 **多邮箱支持** - 支持 Gmail + IMAP（QQ、163、Outlook）

## 安装

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 配置飞书通知（可选）
python email_manager_v2.py --setup-feishu

# 添加邮箱账户
python email_manager_v2.py --setup-account
```

## 使用

### 作为 OpenClaw Skill 使用

```bash
# 检查新邮件
openclaw skill gmail-manager check

# 生成邮件摘要
openclaw skill gmail-manager summary

# 清理垃圾邮件
openclaw skill gmail-manager clean

# 完整报告
openclaw skill gmail-manager report
```

### 直接运行

```bash
# 检查所有账户的新邮件
python email_manager_v2.py --check

# 生成邮件摘要报告
python email_manager_v2.py --summary
```

## 自动运行

### Crontab 配置

```bash
# 每小时检查一次新邮件
0 * * * * cd /path/to/gmail-manager && python email_manager_v2.py --check >> ~/gmail_check.log 2>&1

# 每天上午9点生成邮件摘要
0 9 * * * cd /path/to/gmail-manager && python email_manager_v2.py --summary >> ~/gmail_daily.log 2>&1
```

## 支持的邮箱类型

| 邮箱类型 | 协议 | 配置方式 |
|---------|------|---------|
| Gmail | OAuth 2.0 | 自动配置 |
| QQ 邮箱 | IMAP | 需要授权码 |
| 163 邮箱 | IMAP | 需要授权码 |
| Outlook | IMAP | 密码登录 |
| 其他 IMAP | IMAP | 手动输入服务器 |

## 系统要求

- Python 3.8+
- 网络连接
- Gmail 或其他邮箱账户
- 飞书群聊（如需通知功能）

## 许可证

MIT License

## 版本历史

### v2.0.0
- 新增飞书通知功能
- 支持多邮箱账户
- 改进分类规则

### v1.0.0
- 初始版本发布
