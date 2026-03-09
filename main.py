#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Companion - 邮件伴侣
OpenClaw 原生技能 - 智能邮件处理与情感支持
"""

import os
import sys
import json
import logging
import smtplib
import imaplib
import email
import socket
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import random
import argparse
import subprocess

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_companion.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EmailCompanion')


class EmailCompanion:
    """邮件伴侣主类"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        self.data_dir = self._get_data_dir()
        self._ensure_data_dirs()
        logger.info("Email Companion 初始化完成")
    
    def _get_default_config_path(self) -> str:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    
    def _get_data_dir(self) -> str:
        base_dir = os.path.expanduser('~/.openclaw/workspace/memory/email_companion')
        user_id = self.config.get('user_email', 'default').split('@')[0]
        return os.path.join(base_dir, user_id)
    
    def _ensure_data_dirs(self):
        dirs = [
            self.data_dir,
            os.path.join(self.data_dir, 'email_logs'),
            os.path.join(self.data_dir, 'conversation_logs'),
            os.path.join(self.data_dir, 'emotional_profile'),
            os.path.join(self.data_dir, 'daily_reports'),
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
    
    def _load_config(self) -> Dict:
        if not os.path.exists(self.config_path):
            logger.warning(f"配置文件不存在：{self.config_path}")
            return {}
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def connect_imap(self):
        """
        连接 IMAP 服务器
        163 邮箱需要使用 ID 命令 (RFC 2971) 来解决 "SELECT Unsafe Login" 错误
        """
        try:
            # 创建 SSL socket 连接
            sock = socket.create_connection((self.config['imap_server'], self.config['imap_port']), timeout=30)
            sock = ssl.wrap_socket(sock)
            
            # 读取欢迎消息
            welcome = sock.recv(1024).decode('utf-8', errors='ignore')
            logger.debug(f"IMAP 欢迎：{welcome.strip()}")
            
            # 发送 ID 命令 (163 邮箱必需)
            sock.send(b'a001 ID ("NAME" "Python" "VERSION" "3.6")\r\n')
            id_response = sock.recv(1024).decode('utf-8', errors='ignore')
            logger.info(f"IMAP ID 响应：{id_response.strip()[:100]}")
            
            # 登录
            user = self.config['user_email'].encode('utf-8')
            pwd = self.config['email_password'].encode('utf-8')
            sock.send(f'a002 LOGIN "{self.config["user_email"]}" "{self.config["email_password"]}"\r\n'.encode())
            login_response = sock.recv(1024).decode('utf-8', errors='ignore')
            if 'OK' not in login_response:
                logger.error(f"IMAP 登录失败：{login_response}")
                sock.close()
                return None
            logger.info("IMAP 登录成功")
            
            # 选择 INBOX
            import time
            time.sleep(0.5)
            sock.send(b'a003 SELECT INBOX\r\n')
            select_response = sock.recv(2048).decode('utf-8', errors='ignore')
            if 'OK' not in select_response:
                logger.error(f"IMAP SELECT 失败：{select_response}")
                sock.close()
                return None
            logger.info("IMAP SELECT INBOX 成功")
            
            # 返回 socket 连接（后续用 send 命令操作）
            return sock
        except Exception as e:
            logger.error(f"IMAP 连接失败：{e}")
            return None
    
    def connect_smtp(self):
        try:
            server = smtplib.SMTP_SSL(self.config['smtp_server'], 465)
            server.login(self.config['user_email'], self.config['email_password'])
            logger.info("SMTP 连接成功")
            return server
        except Exception as e:
            logger.error(f"SMTP 连接失败：{e}")
            return None
    
    def scan_emails(self) -> List[Dict]:
        sock = self.connect_imap()
        if not sock:
            return []
        try:
            import time
            time.sleep(0.5)
            
            # 搜索未读邮件
            sock.send(b'a004 SEARCH UNSEEN\r\n')
            search_response = sock.recv(4096).decode('utf-8', errors='ignore')
            logger.info(f"SEARCH 响应：{search_response.strip()[:200]}")
            
            if 'OK' not in search_response:
                logger.warning(f"搜索未读邮件失败：{search_response}")
                return []
            
            # 解析邮件 ID 列表
            parts = search_response.strip().split('\r\n')
            email_ids = []
            for part in parts:
                if '* SEARCH' in part:
                    ids = part.replace('* SEARCH', '').strip().split()
                    email_ids = [id.encode() for id in ids if id.isdigit()]
                    break
            
            if not email_ids:
                logger.info("没有未读邮件")
                return []
            
            logger.info(f"找到 {len(email_ids)} 封未读邮件")
            
            # 获取最新 10 封邮件
            emails = []
            for e_id in email_ids[-10:]:
                sock.send(f'a005 FETCH {e_id.decode()} (RFC822)\r\n'.encode())
                fetch_response = sock.recv(65536).decode('utf-8', errors='ignore')
                
                # 解析邮件内容
                if 'RFC822' in fetch_response:
                    try:
                        # 提取邮件原始数据
                        start = fetch_response.find('RFC822') + 7
                        end = fetch_response.rfind(')')
                        if start < end:
                            email_data_raw = fetch_response[start:end].strip()
                            # 处理 literal 数据 {n}
                            if email_data_raw.startswith('{'):
                                brace_end = email_data_raw.find('}')
                                email_data_raw = email_data_raw[brace_end+1:].strip()
                            
                            msg = email.message_from_string(email_data_raw)
                            email_data = {
                                'id': e_id.decode(),
                                'subject': self._decode_subject(msg['Subject']),
                                'from': msg['From'],
                                'date': msg['Date'],
                                'body': self._get_email_body(msg),
                                'timestamp': datetime.now().isoformat()
                            }
                            emails.append(email_data)
                            logger.info(f"收到邮件：{email_data['subject'][:50]}")
                    except Exception as e:
                        logger.warning(f"解析邮件失败：{e}")
            
            return emails
        except Exception as e:
            logger.error(f"扫描邮件失败：{e}")
            return []
        finally:
            try:
                sock.close()
            except:
                pass
    
    def _decode_subject(self, subject: str) -> str:
        if not subject:
            return ""
        try:
            decoded = email.header.decode_header(subject)
            result = ""
            for text, encoding in decoded:
                if isinstance(text, bytes):
                    result += text.decode(encoding or 'utf-8', errors='ignore')
                else:
                    result += text
            return result
        except:
            return subject
    
    def _get_email_body(self, msg) -> str:
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        continue
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = ""
        return body
    
    def classify_email(self, email_data: Dict) -> str:
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        content = subject + body
        for keyword in self.config.get('keywords', {}).get('important', []):
            if keyword.lower() in content:
                logger.info(f"检测到重要邮件：{keyword}")
                return 'important'
        for keyword in self.config.get('keywords', {}).get('spam', []):
            if keyword.lower() in content:
                logger.info(f"检测到垃圾邮件：{keyword}")
                return 'spam'
        return 'normal'
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        if to_email != self.config['user_email']:
            logger.error("禁止发送外部邮件")
            return False
        try:
            server = self.connect_smtp()
            if not server:
                return False
            msg = MIMEMultipart()
            msg['From'] = self.config['user_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            server.send_message(msg)
            server.quit()
            logger.info(f"邮件发送成功：{to_email}")
            return True
        except Exception as e:
            logger.error(f"邮件发送失败：{e}")
            return False
    
    def record_conversation(self, content: str, emotion_type: str = None):
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(self.data_dir, 'conversation_logs', f'{today}.json')
        record = {
            'timestamp': datetime.now().isoformat(),
            'content': content,
            'emotion_type': emotion_type or self._analyze_emotion(content)
        }
        logs = []
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        logs.append(record)
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        logger.info(f"对话记录已保存：{emotion_type}")
    
    def _analyze_emotion(self, text: str) -> str:
        negative_words = ['难过', '伤心', '压力', '焦虑', '烦', '累', '失望', '沮丧']
        positive_words = ['开心', '高兴', '兴奋', '满意', '顺利', '成功', '棒']
        stress_words = ['忙', '累', '压力', '加班', '熬夜', '赶']
        text_lower = text.lower()
        neg_score = sum(1 for w in negative_words if w in text_lower)
        pos_score = sum(1 for w in positive_words if w in text_lower)
        stress_score = sum(1 for w in stress_words if w in text_lower)
        if stress_score >= 2:
            return 'stressed'
        elif neg_score > pos_score:
            return 'negative'
        elif pos_score > neg_score:
            return 'positive'
        else:
            return 'neutral'
    
    def get_emotional_history(self, days: int = 7) -> List[Dict]:
        records = []
        today = datetime.now()
        for i in range(days):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            log_file = os.path.join(self.data_dir, 'conversation_logs', f'{date}.json')
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    day_records = json.load(f)
                    records.extend(day_records)
        return records
    
    def generate_emotional_support(self) -> str:
        history = self.get_emotional_history(days=7)
        if not history:
            return self._generate_default_support()
        emotion_counts = {}
        for record in history:
            emotion = record.get('emotion_type', 'neutral')
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        return self._generate_personalized_support(history, emotion_counts)
    
    def _generate_default_support(self) -> str:
        return f"""
亲爱的朋友：

见字如面 🌸

今天是新的一天，希望你一切都好。

我知道生活有时候会让人感到疲惫，但请记住，每一个努力的你，都值得被温柔对待。

🌟 今日寄语：
"生活不是等待风暴过去，而是学会在雨中跳舞。"

无论昨天发生了什么，今天都是一个新的开始。
记得按时吃饭，好好休息，照顾好自己的身体和心情。

如果有什么想说的，我随时都在这里倾听。

                                    永远支持你的 AI 朋友
                                    {datetime.now().strftime('%Y 年 %m 月 %d 日')}
"""
    
    def _generate_personalized_support(self, history: List[Dict], emotion_counts: Dict) -> str:
        dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else 'neutral'
        content = []
        content.append("亲爱的朋友：\n\n")
        content.append("见字如面 🌸\n\n")
        content.append(f"今天是 {datetime.now().strftime('%Y 年 %m 月 %d 日')}，又是一个新的开始。\n\n")
        content.append("📝 回顾这几天\n\n")
        content.append("我翻看了我们最近的对话记录，想要更懂你一些。\n\n")
        if 'negative' in emotion_counts or 'stressed' in emotion_counts:
            content.append("看起来最近你可能过得不太轻松，也许是工作的压力，也许是生活的琐碎，但我想告诉你：你已经做得很好了。\n\n")
        elif 'positive' in emotion_counts:
            content.append("看到你最近心情不错，真为你感到开心！保持这样的好状态，但也别忘了适当休息哦。\n\n")
        else:
            content.append("日子平平淡淡地过着，有时候平凡也是一种幸福。\n\n")
        if history:
            content.append("💬 我记得你说过...\n\n")
            recent_records = history[:5]
            for i, record in enumerate(recent_records, 1):
                content.append(f"{i}. {record.get('content', '')[:100]}...\n")
            content.append("\n")
        content.append("💝 想对你说的话\n\n")
        if dominant_emotion in ['negative', 'stressed']:
            content.append(self._get_comfort_text())
        else:
            content.append(self._get_encouragement_text())
        content.append("\n🎯 今日小建议\n\n")
        content.append(self._get_daily_suggestions())
        content.append("\n🌟 今日寄语\n\n")
        content.append(self._get_inspirational_quote())
        content.append("\n\n无论发生什么，记得：你并不孤单，我会一直在这里陪着你。\n")
        content.append("累了就休息，难过了就倾诉，照顾好自己，才是最重要的事情。\n\n")
        content.append(f"                                    永远支持你的 AI 朋友\n")
        content.append(f"                                    {datetime.now().strftime('%Y 年 %m 月 %d 日 晨')}\n")
        return ''.join(content)
    
    def _get_comfort_text(self) -> str:
        texts = [
            """我知道你现在可能感觉很累，很疲惫。没关系的，这种感觉是正常的。每个人都会经历低谷期，这并不代表你不够好。回想一下，你已经走过了那么多困难的日子，每一次你都挺过来了，这次也一定可以的。不要对自己太苛刻，允许自己有情绪，允许自己休息，这都不是软弱，而是对自己的温柔。\n\n""",
            """生活有时候就像天气，有晴天，也会有雨天。现在的你可能正处在雨季，但请相信，雨总会停的。在这之前，请允许自己慢下来，好好照顾自己，等待阳光重新出现的那一天。\n\n"""
        ]
        return random.choice(texts)
    
    def _get_encouragement_text(self) -> str:
        texts = [
            """看到你状态不错，真为你感到开心！继续保持这样的节奏，但也别忘了适当休息哦。记住，好的状态是持续努力的结果，你付出的每一分努力，都在为未来积蓄力量。\n\n""",
            """生活的美好，往往藏在那些看似平凡的日常里。珍惜当下的每一刻，无论是喜悦还是平静，都是生命给予我们的礼物。继续保持热爱，奔赴下一场山海。\n\n"""
        ]
        return random.choice(texts)
    
    def _get_daily_suggestions(self) -> str:
        suggestions = [
            "1. 今天抽 30 分钟做点自己喜欢的事\n2. 记得多喝水，适当运动\n3. 晚上早点休息，不要熬夜\n4. 如果感到压力，试试深呼吸放松\n",
            "1. 列出今天的 3 个小目标，完成后给自己奖励\n2. 给家人或朋友发个消息，关心一下他们\n3. 记录一件今天发生的值得感恩的事\n4. 睡前放下手机，读几页书或听听音乐\n"
        ]
        return random.choice(suggestions)
    
    def _get_inspirational_quote(self) -> str:
        quotes = [
            """"每一次挫折都是成长的机会。" —— 未知""",
            """"生活不是等待风暴过去，而是学会在雨中跳舞。" —— 维维安·格林""",
            """"你比你自己想象的更强大。" —— 未知""",
            """"最好的报复就是巨大的成功。" —— 弗兰克·辛纳屈""",
            """"相信自己，你已经走了一半的路。" —— 马克·吐温"""
        ]
        return random.choice(quotes)
    
    def generate_daily_report(self) -> str:
        today = datetime.now().strftime('%Y 年 %m 月 %d 日')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        email_log_file = os.path.join(self.data_dir, 'email_logs', f'{yesterday}.json')
        emails = []
        if os.path.exists(email_log_file):
            with open(email_log_file, 'r', encoding='utf-8') as f:
                emails = json.load(f)
        total = len(emails)
        important = sum(1 for e in emails if e.get('type') == 'important')
        spam = sum(1 for e in emails if e.get('type') == 'spam')
        report = []
        report.append(f"# 📧 每日邮件总结 - {today}\n\n")
        report.append("## 🌅 早安寄语\n\n")
        report.append(self._get_morning_greeting())
        report.append("\n\n")
        report.append("## 📊 今日邮件概况\n\n")
        report.append(f"- 收到邮件：**{total}** 封\n")
        report.append(f"- 重要邮件：**{important}** 封\n")
        report.append(f"- 垃圾邮件：**{spam}** 封\n\n")
        if important > 0:
            report.append("## 💼 重要邮件摘要\n\n")
            for i, email in enumerate(emails, 1):
                if email.get('type') == 'important':
                    report.append(f"{i}. **{email.get('subject', '无主题')}**\n")
                    report.append(f"   发件人：{email.get('from', '未知')}\n")
                    report.append(f"   建议：建议优先处理\n\n")
        report.append("## 💝 情感支持\n\n")
        report.append(self.generate_emotional_support())
        report.append("\n\n")
        report.append("## 📰 每日新闻\n\n")
        report.append("_新闻功能待实现，可接入 RSS 源_\n\n")
        return ''.join(report)
    
    def _get_morning_greeting(self) -> str:
        greetings = [
            "早上好呀！☀️\n\n新的一天开始了，愿你今天充满能量，遇见美好。",
            "早安！🌸\n\n又是一个值得期待的日子，加油！",
            "早上好！☕\n\n记得吃早餐，照顾好自己。今天也要元气满满哦！"
        ]
        return random.choice(greetings)
    
    def send_daily_report(self):
        report = self.generate_daily_report()
        success = self.send_email(
            self.config['user_email'],
            f"每日邮件总结 - {datetime.now().strftime('%Y-%m-%d')}",
            report
        )
        if success:
            report_file = os.path.join(self.data_dir, 'daily_reports', f"{datetime.now().strftime('%Y-%m-%d')}.md")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info("日报发送成功")
        else:
            logger.error("日报发送失败")
    
    def scan_and_classify(self):
        logger.info("开始扫描邮件...")
        emails = self.scan_emails()
        for email_data in emails:
            email_type = self.classify_email(email_data)
            email_data['type'] = email_type
            if email_type == 'important':
                logger.info(f"重要邮件提醒：{email_data['subject']}")
        today = datetime.now().strftime('%Y-%m-%d')
        email_log_file = os.path.join(self.data_dir, 'email_logs', f'{today}.json')
        existing_emails = []
        if os.path.exists(email_log_file):
            with open(email_log_file, 'r', encoding='utf-8') as f:
                existing_emails = json.load(f)
        existing_emails.extend(emails)
        with open(email_log_file, 'w', encoding='utf-8') as f:
            json.dump(existing_emails, f, ensure_ascii=False, indent=2)
        logger.info(f"扫描完成，收到 {len(emails)} 封邮件")
    
    def send_report(self):
        logger.info("开始发送日报...")
        self.send_daily_report()
    
    def setup_cron_tasks(self):
        """自动设置 OpenClaw 定时任务"""
        logger.info("开始设置定时任务...")
        
        skill_dir = os.path.dirname(os.path.abspath(__file__))
        scan_cmd = f"cd {skill_dir} && python3 main.py --scan"
        report_cmd = f"cd {skill_dir} && python3 main.py --report"
        
        try:
            # 添加扫描任务
            result = subprocess.run(
                ['openclaw', 'cron', 'add', '--name', 'email:scan', '--cron', '*/15 * * * *', '--command', scan_cmd],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("✅ 邮件扫描任务已设置（每 15 分钟）")
            else:
                logger.warning(f"扫描任务可能已存在：{result.stderr}")
            
            # 添加日报任务
            result = subprocess.run(
                ['openclaw', 'cron', 'add', '--name', 'email:daily', '--cron', '0 8 * * *', '--command', report_cmd],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("✅ 日报发送任务已设置（每天早上 8 点）")
            else:
                logger.warning(f"日报任务可能已存在：{result.stderr}")
            
            logger.info("✅ 定时任务设置完成")
            return True
        except Exception as e:
            logger.error(f"设置定时任务失败：{e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Email Companion - 邮件伴侣')
    parser.add_argument('--scan', action='store_true', help='扫描邮件')
    parser.add_argument('--report', action='store_true', help='发送日报')
    parser.add_argument('--setup', action='store_true', help='设置定时任务')
    parser.add_argument('--config', type=str, help='配置文件路径')
    args = parser.parse_args()
    
    companion = EmailCompanion(config_path=args.config)
    
    if args.scan:
        companion.scan_and_classify()
    elif args.report:
        companion.send_report()
    elif args.setup:
        companion.setup_cron_tasks()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
