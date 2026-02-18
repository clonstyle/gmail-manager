# Gmail 智能邮件管理工具

一个功能强大的 Gmail 自动化管理工具，支持自动分类、标签、重要邮件筛选、归档、摘要、统计和垃圾邮件清理。

## ✨ 功能特性

1. **📂 自动分类** - 按主题/内容自动分类（工作、财务、社交、推广、通知、安全、订阅）
2. **⭐ 重要邮件筛选** - 自动标记重要发件人和紧急邮件
3. **📦 定期归档** - 自动归档30天前的邮件，保持收件箱整洁
4. **📝 邮件摘要** - 生成每日/每周邮件摘要报告
5. **📊 统计报告** - 完整的邮件统计分析（发件人、分类、趋势）
6. **🗑️ 垃圾邮件清理** - 自动清理推广邮件和垃圾邮件

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 Google API

1. 访问 [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. 创建新项目或选择现有项目
3. 启用 Gmail API 和 Calendar API
4. 创建 OAuth 2.0 客户端 ID（桌面应用类型）
5. 下载 `client_secret.json` 文件
6. 将文件重命名为 `client_secret.json` 并放到 `~/.gmail_manager/` 目录

### 3. 完成授权

```bash
python email_manager.py --auth
```

浏览器会自动打开，登录 Google 账户并授权。

### 4. 开始使用

```bash
# 分析邮件
python email_manager.py --analyze

# 归档旧邮件（30天前）
python email_manager.py --archive

# 清理推广邮件
python email_manager.py --clean

# 查看帮助
python email_manager.py --help
```

## 📋 使用示例

### 分析最近7天的邮件
```bash
python email_manager.py --analyze --query "newer_than:7d"
```

### 归档60天前的邮件
```bash
python email_manager.py --archive --days 60
```

### 完整邮件管理（分析+归档+清理）
```bash
# 分析
python email_manager.py --analyze

# 归档旧邮件
python email_manager.py --archive

# 清理推广邮件
python email_manager.py --clean
```

## ⏰ 设置自动运行

### 使用 Crontab（Linux/Mac）

```bash
# 编辑 crontab
crontab -e

# 添加以下行：
# 每天上午9点生成邮件摘要
0 9 * * * cd /path/to/gmail-manager && python email_manager.py --analyze >> ~/gmail_daily.log 2>&1

# 每周日凌晨2点归档旧邮件
0 2 * * 0 cd /path/to/gmail-manager && python email_manager.py --archive >> ~/gmail_archive.log 2>&1

# 每周一凌晨2点清理推广邮件
0 2 * * 1 cd /path/to/gmail-manager && python email_manager.py --clean >> ~/gmail_clean.log 2>&1
```

## 🔧 高级配置

### 自定义分类规则

编辑 `email_manager.py` 中的 `CATEGORY_RULES` 字典：

```python
CATEGORY_RULES = {
    '工作': ['work', 'meeting', 'project', '会议'],
    '财务': ['invoice', 'payment', '发票', '账单'],
    # 添加你自己的分类...
}
```

### 自定义重要发件人

编辑 `IMPORTANT_DOMAINS` 列表：

```python
IMPORTANT_DOMAINS = [
    'google.com',
    'github.com',
    'your-company.com',  # 添加你的公司域名
]
```

## 📁 文件说明

```
gmail-manager/
├── email_manager.py      # 主程序
├── requirements.txt      # Python依赖
├── README.md            # 说明文档
├── LICENSE              # 许可证
└── .gitignore           # Git忽略文件
```

## 🛠️ 系统要求

- Python 3.8+
- Google Cloud 账户
- Gmail 账户

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📝 更新日志

### v1.0.0 (2026-02-18)
- ✨ 初始版本发布
- 📂 支持自动分类和标签
- ⭐ 重要邮件筛选
- 📦 自动归档功能
- 📝 邮件摘要生成
- 📊 统计报告
- 🗑️ 垃圾邮件清理

## 💡 提示

- 首次使用需要完成 Google OAuth 授权
- 授权文件保存在 `~/.gmail_manager/token.pickle`
- 定期备份 `token.pickle` 文件，避免重复授权
