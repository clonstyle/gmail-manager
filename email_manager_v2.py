#!/usr/bin/env python3
"""
Gmail 智能邮件管理工具 v2.0
功能：自动分类、标签、重要邮件筛选、归档、摘要、统计、垃圾清理
新增：飞书通知、多邮箱账户支持

作者: Vincent
版本: 2.0.0
"""

import os
import sys
import pickle
import base64
import re
import json
import argparse
import imaplib
import email
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# 配置文件路径
CONFIG_DIR = os.path.expanduser('~/.gmail_manager')
TOKEN_FILE = os.path.join(CONFIG_DIR, 'token.pickle')
CLIENT_SECRET_FILE = os.path.join(CONFIG_DIR, 'client_secret.json')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
FEISHU_CONFIG_FILE = os.path.join(CONFIG_DIR, 'feishu_config.json')
ACCOUNTS_FILE = os.path.join(CONFIG_DIR, 'accounts.json')

# 确保配置目录存在
os.makedirs(CONFIG_DIR, exist_ok=True)

# 分类规则
CATEGORY_RULES = {
    '工作': ['work', 'job', 'project', 'meeting', '会议', '项目', '工作', 'task', 'deadline'],
    '财务': ['invoice', 'payment', 'bill', 'receipt', '发票', '账单', '付款', 'order', 'subscription'],
    '社交': ['facebook', 'twitter', 'linkedin', 'social', '邀请', '好友', 'friend', 'connection'],
    '推广': ['promotion', 'offer', 'sale', 'discount', '优惠', '促销', '广告', 'marketing', 'newsletter'],
    '通知': ['notification', 'alert', 'reminder', '通知', '提醒', 'update', '系统'],
    '安全': ['security', 'login', 'password', 'verify', '安全', '登录', '验证', 'auth', '2fa'],
    '订阅': ['newsletter', 'subscribe', '订阅', 'unsubscribe', 'digest'],
    '购物': ['order', 'shipping', 'delivery', 'amazon', 'taobao', 'jd', '购物', '订单', '快递']
}

# 重要发件人域名
IMPORTANT_DOMAINS = [
    'google.com', 'github.com', 'gitlab.com', 'nvidia.com',
    'openai.com', 'microsoft.com', 'apple.com', 'amazon.com'
]

# 垃圾邮件关键词
SPAM_KEYWORDS = [
    'unsubscribe', 'promotion', 'marketing', 'limited time',
    'act now', 'click here', '免费', '限时', '立即购买', '清仓',
    'earn money', 'get rich', 'winner', 'congratulations', 'prize'
]


class FeishuNotifier:
    """飞书通知器"""
    
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url or self._load_webhook()
        self.enabled = bool(self.webhook_url)
    
    def _load_webhook(self):
        """从配置文件加载 webhook"""
        if os.path.exists(FEISHU_CONFIG_FILE):
            with open(FEISHU_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('webhook_url')
        return None
    
    def save_webhook(self, webhook_url):
        """保存 webhook 到配置文件"""
        config = {'webhook_url': webhook_url}
        with open(FEISHU_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        self.webhook_url = webhook_url
        self.enabled = True
        print(f"✅ 飞书 webhook 已保存")
    
    def send_message(self, title, content, msg_type="text"):
        """发送飞书消息"""
        if not self.enabled:
            print("⚠️ 飞书通知未配置")
            return False
        
        try:
            import requests
            
            if msg_type == "markdown":
                data = {
                    "msg_type": "interactive",
                    "card": {
                        "header": {
                            "title": {"tag": "plain_text", "content": title}
                        },
                        "elements": [
                            {"tag": "div", "text": {"tag": "lark_md", "content": content}}
                        ]
                    }
                }
            else:
                data = {
                    "msg_type": "text",
                    "content": {"text": f"{title}\n{content}"}
                }
            
            response = requests.post(
                self.webhook_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    return True
                else:
                    print(f"❌ 飞书发送失败: {result.get('msg')}")
            else:
                print(f"❌ 飞书请求失败: HTTP {response.status_code}")
            
        except Exception as e:
            print(f"❌ 飞书通知错误: {e}")
        
        return False
    
    def notify_new_emails(self, account, emails):
        """通知新邮件"""
        if not emails:
            return
        
        title = f"📧 {account} 收到 {len(emails)} 封新邮件"
        
        content_lines = []
        for email in emails[:5]:  # 最多显示5封
            subject = email.get('subject', '无主题')[:30]
            sender = email.get('sender', '未知')[:25]
            categories = ', '.join(email.get('categories', ['其他']))
            content_lines.append(f"• **{subject}** - {sender} ({categories})")
        
        if len(emails) > 5:
            content_lines.append(f"\n...还有 {len(emails) - 5} 封邮件")
        
        content = "\n".join(content_lines)
        self.send_message(title, content, msg_type="markdown")
    
    def notify_important_email(self, email):
        """通知重要邮件"""
        title = "⭐ 收到重要邮件"
        content = f"**主题:** {email.get('subject', '无主题')}\n**发件人:** {email.get('sender', '未知')}\n**时间:** {email.get('date', '')}"
        self.send_message(title, content, msg_type="markdown")


class EmailAccount:
    """邮箱账户基类"""
    
    def __init__(self, name, email_address, account_type='gmail'):
        self.name = name
        self.email_address = email_address
        self.account_type = account_type
    
    def get_emails(self, query='', max_results=50):
        """获取邮件列表"""
        raise NotImplementedError
    
    def archive_email(self, msg_id):
        """归档邮件"""
        raise NotImplementedError


class GmailAccount(EmailAccount):
    """Gmail 账户"""
    
    def __init__(self, name, email_address, token_file=None):
        super().__init__(name, email_address, 'gmail')
        self.token_file = token_file or TOKEN_FILE
        self.service = None
    
    def connect(self):
        """连接到 Gmail"""
        if not os.path.exists(self.token_file):
            print(f"❌ 未找到授权文件: {self.token_file}")
            return False
        
        try:
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
            self.service = build('gmail', 'v1', credentials=creds)
            return True
        except Exception as e:
            print(f"❌ 连接 Gmail 失败: {e}")
            return False
    
    def get_emails(self, query='newer_than:1d', max_results=50):
        """获取邮件"""
        if not self.service and not self.connect():
            return []
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                email_data = self._get_message_detail(msg['id'])
                if email_data:
                    emails.append(email_data)
            
            return emails
        except Exception as e:
            print(f"❌ 获取邮件失败: {e}")
            return []
    
    def _get_message_detail(self, msg_id):
        """获取邮件详情"""
        try:
            message = self.service.users().messages().get(
                userId='me', id=msg_id, format='full'
            ).execute()
            
            payload = message.get('payload', {})
            headers = payload.get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # 获取正文
            body = ''
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        data = part.get('body', {}).get('data', '')
                        if data:
                            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                            break
            
            return {
                'id': msg_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body[:500],
                'snippet': message.get('snippet', ''),
                'labels': message.get('labelIds', [])
            }
        except Exception as e:
            print(f"❌ 获取邮件详情失败: {e}")
            return None
    
    def archive_email(self, msg_id):
        """归档邮件"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            return True
        except Exception as e:
            print(f"❌ 归档失败: {e}")
            return False


class IMAPAccount(EmailAccount):
    """IMAP 邮箱账户（支持 QQ、163、Outlook 等）"""
    
    def __init__(self, name, email_address, password, imap_server, imap_port=993):
        super().__init__(name, email_address, 'imap')
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.mail = None
    
    def connect(self):
        """连接到 IMAP 服务器"""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mail.login(self.email_address, self.password)
            return True
        except Exception as e:
            print(f"❌ IMAP 连接失败: {e}")
            return False
    
    def get_emails(self, folder='INBOX', limit=50):
        """获取邮件"""
        if not self.mail and not self.connect():
            return []
        
        try:
            self.mail.select(folder)
            _, data = self.mail.search(None, 'UNSEEN')  # 获取未读邮件
            email_ids = data[0].split()[-limit:]  # 最近 N 封
            
            emails = []
            for e_id in email_ids:
                _, msg_data = self.mail.fetch(e_id, '(RFC822)')
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                email_data = {
                    'id': e_id.decode(),
                    'subject': msg.get('Subject', 'No Subject'),
                    'sender': msg.get('From', 'Unknown'),
                    'date': msg.get('Date', ''),
                    'body': self._get_body(msg),
                    'snippet': '',
                    'labels': ['UNREAD']
                }
                emails.append(email_data)
            
            return emails
        except Exception as e:
            print(f"❌ 获取 IMAP 邮件失败: {e}")
            return []
    
    def _get_body(self, msg):
        """获取邮件正文"""
        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                pass
        return body[:500]
    
    def archive_email(self, msg_id):
        """标记为已读（IMAP 归档）"""
        try:
            self.mail.store(msg_id.encode(), '+FLAGS', '\\Seen')
            return True
        except Exception as e:
            print(f"❌ IMAP 归档失败: {e}")
            return False


class EmailManager:
    """邮件管理器"""
    
    def __init__(self):
        self.accounts = []
        self.feishu = FeishuNotifier()
        self._load_accounts()
    
    def _load_accounts(self):
        """加载已保存的账户"""
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, 'r') as f:
                accounts_data = json.load(f)
                for acc_data in accounts_data:
                    if acc_data['type'] == 'gmail':
                        account = GmailAccount(
                            acc_data['name'],
                            acc_data['email']
                        )
                    elif acc_data['type'] == 'imap':
                        account = IMAPAccount(
                            acc_data['name'],
                            acc_data['email'],
                            acc_data.get('password', ''),
                            acc_data['imap_server'],
                            acc_data.get('imap_port', 993)
                        )
                    self.accounts.append(account)
    
    def save_accounts(self):
        """保存账户配置"""
        accounts_data = []
        for acc in self.accounts:
            acc_data = {
                'name': acc.name,
                'email': acc.email_address,
                'type': acc.account_type
            }
            if isinstance(acc, IMAPAccount):
                acc_data['imap_server'] = acc.imap_server
                acc_data['imap_port'] = acc.imap_port
            accounts_data.append(acc_data)
        
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(accounts_data, f, indent=2)
    
    def add_gmail_account(self, name, email_address):
        """添加 Gmail 账户"""
        account = GmailAccount(name, email_address)
        self.accounts.append(account)
        self.save_accounts()
        print(f"✅ 已添加 Gmail 账户: {name} ({email_address})")
    
    def add_imap_account(self, name, email_address, password, imap_server, imap_port=993):
        """添加 IMAP 账户"""
        account = IMAPAccount(name, email_address, password, imap_server, imap_port)
        self.accounts.append(account)
        self.save_accounts()
        print(f"✅ 已添加 IMAP 账户: {name} ({email_address})")
    
    def classify_email(self, email_data):
        """自动分类邮件"""
        text = f"{email_data['subject']} {email_data.get('snippet', '')} {email_data.get('body', '')}".lower()
        categories = []
        
        for category, keywords in CATEGORY_RULES.items():
            if any(keyword in text for keyword in keywords):
                categories.append(category)
        
        return categories if categories else ['其他']
    
    def is_important(self, email_data):
        """判断是否为重要邮件"""
        sender_lower = email_data['sender'].lower()
        
        # 检查发件人域名
        if any(domain in sender_lower for domain in IMPORTANT_DOMAINS):
            return True
        
        # 检查重要关键词
        important_keywords = ['urgent', 'important', 'action required', 'meeting', 'deadline', '紧急']
        if any(kw in email_data['subject'].lower() for kw in important_keywords):
            return True
        
        return False
    
    def check_all_accounts(self, notify=True):
        """检查所有账户的新邮件"""
        print("=" * 60)
        print("📧 检查所有邮箱账户")
        print("=" * 60)
        print()
        
        all_new_emails = []
        important_emails = []
        
        for account in self.accounts:
            print(f"🔍 检查 {account.name} ({account.email_address})...")
            
            emails = account.get_emails(limit=20)
            print(f"   找到 {len(emails)} 封邮件")
            
            # 分类和标记
            for email_data in emails:
                email_data['account'] = account.name
                categories = self.classify_email(email_data)
                email_data['categories'] = categories
                
                all_new_emails.append(email_data)
                
                if self.is_important(email_data):
                    important_emails.append(email_data)
                    if notify:
                        self.feishu.notify_important_email(email_data)
            
            print()
        
        # 发送汇总通知
        if notify and all_new_emails:
            self.feishu.notify_new_emails("所有账户", all_new_emails)
        
        return all_new_emails, important_emails
    
    def generate_summary(self):
        """生成邮件摘要报告"""
        emails, important = self.check_all_accounts(notify=False)
        
        print("\n" + "=" * 60)
        print("📊 邮件摘要报告")
        print("=" * 60)
        print(f"📧 新邮件总数: {len(emails)}")
        print(f"⭐ 重要邮件: {len(important)}")
        
        # 按账户统计
        by_account = defaultdict(list)
        for e in emails:
            by_account[e['account']].append(e)
        
        print("\n📂 按账户统计:")
        for account_name, acc_emails in by_account.items():
            print(f"   {account_name}: {len(acc_emails)} 封")
        
        # 按分类统计
        by_category = Counter()
        for e in emails:
            for cat in e.get('categories', ['其他']):
                by_category[cat] += 1
        
        print("\n📂 按分类统计:")
        for cat, count in by_category.most_common():
            print(f"   {cat}: {count} 封")
        
        print()
        return emails


def setup_feishu():
    """配置飞书 webhook"""
    print("=" * 60)
    print("🔧 配置飞书通知")
    print("=" * 60)
    print()
    print("获取 webhook URL 步骤:")
    print("1. 在飞书群聊中，点击右上角「...」")
    print("2. 选择「设置」→「群机器人」")
    print("3. 点击「添加机器人」→「自定义机器人」")
    print("4. 复制 webhook URL")
    print()
    
    webhook = input("请输入飞书 webhook URL: ").strip()
    
    if webhook:
        notifier = FeishuNotifier()
        notifier.save_webhook(webhook)
        
        # 测试发送
        print("\n🧪 测试发送消息...")
        if notifier.send_message("✅ 邮件管理工具", "飞书通知已配置成功！"):
            print("✅ 测试消息发送成功！")
        else:
            print("❌ 测试消息发送失败")
    else:
        print("❌ 未输入 webhook URL")


def setup_account():
    """配置邮箱账户"""
    print("=" * 60)
    print("🔧 添加邮箱账户")
    print("=" * 60)
    print()
    print("1. Gmail 账户")
    print("2. QQ 邮箱 (IMAP)")
    print("3. 163 邮箱 (IMAP)")
    print("4. Outlook (IMAP)")
    print("5. 其他 IMAP 邮箱")
    print()
    
    choice = input("请选择 (1-5): ").strip()
    
    manager = EmailManager()
    
    if choice == '1':
        name = input("账户名称 (如: 工作邮箱): ").strip()
        email_addr = input("Gmail 地址: ").strip()
        manager.add_gmail_account(name, email_addr)
        print("\n⚠️ 请确保已完成 Gmail OAuth 授权:")
        print("   python email_manager_v2.py --auth")
    
    elif choice in ['2', '3', '4', '5']:
        name = input("账户名称: ").strip()
        email_addr = input("邮箱地址: ").strip()
        password = input("邮箱密码/授权码: ").strip()
        
        if choice == '2':
            imap_server = 'imap.qq.com'
        elif choice == '3':
            imap_server = 'imap.163.com'
        elif choice == '4':
            imap_server = 'outlook.office365.com'
        else:
            imap_server = input("IMAP 服务器地址: ").strip()
        
        manager.add_imap_account(name, email_addr, password, imap_server)


def main():
    parser = argparse.ArgumentParser(description='Gmail 智能邮件管理工具 v2.0')
    parser.add_argument('--auth', action='store_true', help='完成 Gmail OAuth 授权')
    parser.add_argument('--setup-feishu', action='store_true', help='配置飞书通知')
    parser.add_argument('--setup-account', action='store_true', help='添加邮箱账户')
    parser.add_argument('--check', action='store_true', help='检查所有账户新邮件')
    parser.add_argument('--summary', action='store_true', help='生成邮件摘要')
    parser.add_argument('--notify', action='store_true', default=True, help='发送飞书通知')
    
    args = parser.parse_args()
    
    if args.setup_feishu:
        setup_feishu()
        return
    
    if args.setup_account:
        setup_account()
        return
    
    if args.auth:
        print("请使用 Gmail 授权流程...")
        return
    
    # 默认操作
    manager = EmailManager()
    
    if not manager.accounts:
        print("❌ 未配置邮箱账户，请先运行:")
        print("   python email_manager_v2.py --setup-account")
        return
    
    if args.summary or args.check:
        manager.generate_summary()
    else:
        manager.check_all_accounts(notify=args.notify)


if __name__ == '__main__':
    main()
