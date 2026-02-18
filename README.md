# Gmail 智能邮件管理工具 v2.0

一个功能强大的 Gmail 自动化管理工具，支持自动分类、标签、重要邮件筛选、归档、摘要、统计和垃圾邮件清理。

**v2.0 新增功能：**
- 🔗 **飞书通知** - 新邮件和重要邮件自动推送到飞书
- 📧 **多邮箱支持** - 支持 Gmail + IMAP（QQ、163、Outlook 等）

## ✨ 功能特性

### 核心功能
1. **📂 自动分类** - 按主题/内容自动分类（工作、财务、社交、推广、通知、安全、订阅）
2. **⭐ 重要邮件筛选** - 自动标记重要发件人和紧急邮件
3. **📦 定期归档** - 自动归档30天前的邮件，保持收件箱整洁
4. **📝 邮件摘要** - 生成每日/每周邮件摘要报告
5. **📊 统计报告** - 完整的邮件统计分析（发件人、分类、趋势）
6. **🗑️ 垃圾邮件清理** - 自动清理推广邮件和垃圾邮件

### v2.0 新增
7. **🔗 飞书通知** - 实时推送新邮件和重要邮件到飞书群聊
8. **📧 多邮箱账户** - 同时管理多个邮箱（Gmail、QQ、163、Outlook）

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置飞书通知（可选但推荐）

```bash
python email_manager_v2.py --setup-feishu
```

按提示输入飞书 webhook URL。

### 3. 添加邮箱账户

```bash
python email_manager_v2.py --setup-account
```

选择邮箱类型并输入相关信息。

### 4. 开始使用

```bash
# 检查所有账户的新邮件（带飞书通知）
python email_manager_v2.py --check

# 生成邮件摘要报告
python email_manager_v2.py --summary
```

## 📋 使用示例

### 配置飞书通知
```bash
python email_manager_v2.py --setup-feishu
```

### 添加邮箱账户
```bash
# 添加 Gmail
python email_manager_v2.py --setup-account
# 选择 1. Gmail 账户

# 添加 QQ 邮箱
python email_manager_v2.py --setup-account
# 选择 2. QQ 邮箱
```

### 检查所有邮箱
```bash
python email_manager_v2.py --check
```

### 生成完整报告
```bash
python email_manager_v2.py --summary
```

## ⏰ 设置自动运行

### 使用 Crontab（Linux/Mac）

```bash
# 编辑 crontab
crontab -e

# 添加以下行：
# 每小时检查一次新邮件（带飞书通知）
0 * * * * cd /path/to/gmail-manager && python email_manager_v2.py --check >> ~/gmail_check.log 2>&1

# 每天上午9点生成邮件摘要
0 9 * * * cd /path/to/gmail-manager && python email_manager_v2.py --summary >> ~/gmail_daily.log 2>&1
```

## 🔧 支持的邮箱类型

| 邮箱类型 | 协议 | 配置方式 |
|---------|------|---------|
| Gmail | OAuth 2.0 | 自动配置 |
| QQ 邮箱 | IMAP | 需要授权码 |
| 163 邮箱 | IMAP | 需要授权码 |
| Outlook | IMAP | 密码登录 |
| 其他 IMAP | IMAP | 手动输入服务器 |

## 📁 文件说明

```
gmail-manager/
├── email_manager_v2.py   # 主程序 v2.0（推荐）
├── email_manager.py      # 原版程序（单Gmail）
├── requirements.txt      # Python依赖
├── README.md            # 说明文档
├── LICENSE              # 许可证
└── .gitignore           # Git忽略文件
```

## 🛠️ 系统要求

- Python 3.8+
- 网络连接
- Gmail 或其他邮箱账户
- 飞书群聊（如需通知功能）

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 📝 更新日志

### v2.0.0 (2026-02-18)
- ✨ 新增飞书通知功能
- ✨ 支持多邮箱账户（Gmail + IMAP）
- ✨ 新增更多分类规则
- ✨ 改进重要邮件检测

### v1.0.0 (2026-02-18)
- ✨ 初始版本发布
- 📂 支持自动分类和标签
- ⭐ 重要邮件筛选
- 📦 自动归档功能
- 📝 邮件摘要生成
- 📊 统计报告
- 🗑️ 垃圾邮件清理

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 💡 提示

- 首次使用需要配置邮箱账户
- 飞书通知需要先在飞书群创建自定义机器人
- IMAP 邮箱（QQ/163）需要使用授权码而非密码
