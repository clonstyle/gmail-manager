#!/usr/bin/env python3
"""
Gmail 智能邮件管理工具
功能：自动分类、标签、重要邮件筛选、归档、摘要、统计、垃圾清理

作者: Vincent
版本: 1.0.0
"""

import os
import pickle
import base64
import re
import argparse
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# 配置
TOKEN_FILE = os.path.expanduser('~/.gmail_manager/token.pickle')
CLIENT_SECRET_FILE = os.path.expanduser('~/.gmail_manager/client_secret.json')

# 分类规则
CATEGORY_RULES = {
    '工作': ['work', 'job', 'project', 'meeting', '会议', '项目', '工作', 'task'],
    '财务': ['invoice', 'payment', 'bill', 'receipt', '发票', '账单', '付款', 'order'],
    '社交': ['facebook', 'twitter', 'linkedin', 'social', '邀请', '好友', 'friend'],
    '推广': ['promotion', 'offer', 'sale', 'discount', '优惠', '促销', '广告', 'marketing'],
    '通知': ['notification', 'alert', 'reminder', '通知', '提醒', 'update'],
    '安全': ['security', 'login', 'password', 'verify', '安全', '登录', '验证', 'auth'],
    '订阅': ['newsletter', 'subscribe', '订阅', 'unsubscribe']
}

# 重要发件人域名
IMPORTANT_DOMAINS = [
    'google.com', 'github.com', 'gitlab.com', 'nvidia.com',
    'openai.com', 'microsoft.com', 'apple.com'
]

# 垃圾邮件关键词
SPAM_KEYWORDS = [
    'unsubscribe', 'promotion', 'marketing', 'limited time',
    'act now', 'click here', '免费', '限时', '立即购买'
]


def get_service():
    """获取 Gmail API 服务"""
    if not os.path.exists(TOKEN_FILE):
        print("❌ 未找到授权文件，请先运行: python email_manager.py --auth")
        return None
    
    with open(TOKEN_FILE, 'rb') as token:
        creds = pickle.load(token)
    return build('gmail', 'v1', credentials=creds)


def authenticate():
    """完成 Google OAuth 授权"""
    print("=" * 60)
    print("🔐 Google OAuth 授权")
    print("=" * 60)
    print()
    
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"❌ 未找到 client_secret.json")
        print(f"   请将文件放到: {CLIENT_SECRET_FILE}")
        print()
        print("获取方法:")
        print("1. 访问 https://console.cloud.google.com/apis/credentials")
        print("2. 创建 OAuth 2.0 客户端 ID")
        print("3. 下载 client_secret.json")
        return False
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/calendar.readonly'
    ]
    
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE, scopes=SCOPES)
    
    creds = flow.run_local_server(port=8080, open_browser=True)
    
    # 保存凭证
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, 'wb') as token:
        pickle.dump(creds, token)
    
    print()
    print("✅ 授权成功！")
    return True


def get_message_content(service, msg_id):
    """获取邮件内容"""
    try:
        message = service.users().messages().get(
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
        else:
            data = payload.get('body', {}).get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
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
        print(f"❌ 获取邮件失败: {e}")
        return None


def classify_email(email_data):
    """自动分类邮件"""
    text = f"{email_data['subject']} {email_data['snippet']} {email_data['body']}".lower()
    categories = []
    
    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in text for keyword in keywords):
            categories.append(category)
    
    return categories if categories else ['其他']


def is_important(email_data):
    """判断是否为重要邮件"""
    sender_lower = email_data['sender'].lower()
    
    # 检查发件人域名
    if any(domain in sender_lower for domain in IMPORTANT_DOMAINS):
        return True
    
    # 检查重要关键词
    important_keywords = ['urgent', 'important', 'action required', 'meeting', 'deadline']
    if any(kw in email_data['subject'].lower() for kw in important_keywords):
        return True
    
    return False


def is_spam(email_data):
    """判断是否为垃圾邮件"""
    text = f"{email_data['subject']} {email_data['snippet']}".lower()
    spam_score = sum(1 for kw in SPAM_KEYWORDS if kw in text)
    return spam_score >= 2


def analyze_emails(service, query='newer_than:7d', max_results=100):
    """分析邮件"""
    print("📧 正在分析邮件...")
    
    results = service.users().messages().list(
        userId='me', q=query, maxResults=max_results
    ).execute()
    
    messages = results.get('messages', [])
    print(f"   找到 {len(messages)} 封邮件\n")
    
    stats = {
        'total': len(messages),
        'categories': Counter(),
        'important': [],
        'spam': [],
        'senders': Counter(),
        'daily_count': defaultdict(int),
        'unread': 0
    }
    
    for i, msg in enumerate(messages, 1):
        print(f"\r   处理中: {i}/{len(messages)}", end='', flush=True)
        
        email_data = get_message_content(service, msg['id'])
        if not email_data:
            continue
        
        # 分类
        categories = classify_email(email_data)
        email_data['categories'] = categories
        for cat in categories:
            stats['categories'][cat] += 1
        
        # 重要邮件
        if is_important(email_data):
            stats['important'].append(email_data)
        
        # 垃圾邮件
        if is_spam(email_data):
            stats['spam'].append(email_data)
        
        # 发件人统计
        sender_domain = re.search(r'@([^>]+)', email_data['sender'])
        if sender_domain:
            stats['senders'][sender_domain.group(1)] += 1
        
        # 日期统计
        try:
            date = email_data['date'][:10]
            stats['daily_count'][date] += 1
        except:
            pass
        
        # 未读统计
        if 'UNREAD' in email_data.get('labels', []):
            stats['unread'] += 1
    
    print()
    return stats


def print_summary(stats):
    """打印统计报告"""
    print("\n" + "=" * 60)
    print("📊 邮件统计报告")
    print("=" * 60)
    print(f"📧 总邮件数: {stats['total']}")
    print(f"🔔 未读邮件: {stats['unread']}")
    print(f"⭐ 重要邮件: {len(stats['important'])}")
    print(f"🗑️  垃圾邮件: {len(stats['spam'])}")
    print()
    
    print("📂 分类统计:")
    for category, count in stats['categories'].most_common():
        print(f"   {category}: {count} 封")
    print()


def print_daily_summary(stats):
    """打印每日趋势"""
    print("=" * 60)
    print("📈 每日邮件趋势")
    print("=" * 60)
    for date in sorted(stats['daily_count'].keys())[-7:]:
        count = stats['daily_count'][date]
        bar = '█' * min(count, 20)
        print(f"{date}: {bar} ({count})")
    print()


def archive_old_emails(service, days=30, max_count=100):
    """归档旧邮件"""
    print("📦 正在归档旧邮件...")
    
    results = service.users().messages().list(
        userId='me',
        q=f'older_than:{days}d -in:archive',
        maxResults=max_count
    ).execute()
    
    messages = results.get('messages', [])
    print(f"   找到 {len(messages)} 封旧邮件\n")
    
    archived = 0
    for msg in messages[:50]:
        try:
            service.users().messages().modify(
                userId='me',
                id=msg['id'],
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            archived += 1
        except Exception as e:
            print(f"   归档失败: {e}")
    
    print(f"✅ 已归档 {archived} 封邮件")
    return archived


def clean_promotions(service, max_count=50):
    """清理推广邮件"""
    print("🗑️  正在清理推广邮件...")
    
    results = service.users().messages().list(
        userId='me',
        q='label:promotions older_than:7d',
        maxResults=max_count
    ).execute()
    
    messages = results.get('messages', [])
    print(f"   找到 {len(messages)} 封推广邮件\n")
    
    cleaned = 0
    for msg in messages[:20]:
        try:
            service.users().messages().trash(userId='me', id=msg['id']).execute()
            cleaned += 1
        except Exception as e:
            print(f"   删除失败: {e}")
    
    print(f"✅ 已清理 {cleaned} 封推广邮件")
    return cleaned


def main():
    parser = argparse.ArgumentParser(description='Gmail 智能邮件管理工具')
    parser.add_argument('--auth', action='store_true', help='完成 Google 授权')
    parser.add_argument('--analyze', action='store_true', help='分析邮件')
    parser.add_argument('--archive', action='store_true', help='归档旧邮件')
    parser.add_argument('--clean', action='store_true', help='清理推广邮件')
    parser.add_argument('--days', type=int, default=30, help='归档天数（默认30）')
    parser.add_argument('--query', default='newer_than:7d', help='搜索查询')
    
    args = parser.parse_args()
    
    # 授权模式
    if args.auth:
        authenticate()
        return
    
    # 获取服务
    service = get_service()
    if not service:
        return
    
    # 分析模式
    if args.analyze or (not args.archive and not args.clean):
        stats = analyze_emails(service, query=args.query)
        print_summary(stats)
        print_daily_summary(stats)
    
    # 归档模式
    if args.archive:
        archive_old_emails(service, days=args.days)
    
    # 清理模式
    if args.clean:
        clean_promotions(service)


if __name__ == '__main__':
    main()
