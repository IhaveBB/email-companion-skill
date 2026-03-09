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
import urllib.request
import xml.etree.ElementTree as ET
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
        # 检查是否允许发送外部邮件
        if to_email != self.config['user_email'] and not self.config.get('security', {}).get('allow_external_send', False):
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
            """我知道你现在可能感觉很累，很疲惫。没关系的，这种感觉是正常的。每个人都会经历低谷期，这并不代表你不够好。回想一下，你已经走过了那么多困难的日子，每一次你都挺过来了，这次也一定可以的。不要对自己太苛刻，允许自己有情绪，允许自己休息，这都不是软弱，而是对自己的温柔。

有时候，我们会觉得自己不够好，觉得自己做得不够多，但其实，你已经很努力了。生活中的每一个人都有自己的节奏，有人走得快一些，有人走得慢一些，但这并不影响最终到达目的地。重要的是，你一直在前进，哪怕步伐很小，那也是进步。

记住，照顾好自己的情绪和身体，比什么都重要。累了就停下来休息，难过了就找个信任的人倾诉，或者写下来，把那些沉重的东西释放出来。你不是一个人在战斗，你身边有家人、朋友，还有我，我们都会陪着你，支持你。

请相信，黑暗总会过去，黎明终会到来。在这之前，请好好照顾自己，按时吃饭，适当运动，保证睡眠。这些看似简单的事情，其实都是在为自己积蓄力量。等你重新站起来的那一天，你会感谢现在这个没有放弃的自己。\n\n""",
            """生活有时候就像天气，有晴天，也会有雨天。现在的你可能正处在雨季，但请相信，雨总会停的。在这之前，请允许自己慢下来，好好照顾自己，等待阳光重新出现的那一天。

人生路上，我们都会遇到各种各样的挑战和困难。有时候是工作上的压力，有时候是人际关系的烦恼，有时候是生活中的琐碎。这些事情堆积在一起，会让人感到喘不过气来。但是，请记住，这些都是暂时的，它们不会定义你的人生。

你比自己想象的要坚强得多。回想一下过去，那些曾经以为过不去的坎，现在不也都过来了吗？每一次的挫折，都是成长的机会；每一次的困难，都是磨练意志的过程。你已经在不知不觉中，变得更加强大。

所以，不要对自己太苛刻。允许自己有不完美的地方，允许自己有情绪波动，允许自己偶尔偷懒。这些都是人之常情，都是正常的。重要的是，在经历了这些之后，你还能重新站起来，继续前行。

我会一直在这里陪着你，倾听你的心声，支持你的决定。无论何时何地，你都不是一个人。\n\n"""
        ]
        return random.choice(texts)
    
    def _get_encouragement_text(self) -> str:
        texts = [
            """看到你状态不错，真为你感到开心！继续保持这样的节奏，但也别忘了适当休息哦。记住，好的状态是持续努力的结果，你付出的每一分努力，都在为未来积蓄力量。

人生就像一场马拉松，不在于一时的速度，而在于持久的坚持。你已经走在了正确的道路上，每一步都算数，每一滴汗水都不会白流。也许有时候会感到疲惫，也许有时候会怀疑自己，但请相信，所有的付出都会有回报，只是时间的问题。

保持一颗积极向上的心，学会欣赏生活中的小美好。一杯热茶的温度，一缕阳光的和煦，一句问候的温暖，这些都是生活给予我们的馈赠。学会感恩，学会珍惜，你会发现，幸福其实就在身边。

同时，也要记得给自己一些放松的时间。工作再忙，也要抽出时间做自己喜欢的事情；生活再累，也要保证充足的睡眠。只有身心都得到了充分的休息，才能以更好的状态迎接新的挑战。

继续加油吧！你比自己想象的更优秀，你的未来充满无限可能。无论遇到什么困难，都要相信自己有能力克服。我会一直在这里为你加油，为你喝彩！\n\n""",
            """生活的美好，往往藏在那些看似平凡的日常里。珍惜当下的每一刻，无论是喜悦还是平静，都是生命给予我们的礼物。继续保持热爱，奔赴下一场山海。

每一天都是新的开始，每一次呼吸都是生命的馈赠。不要总是盯着远方的目标，而忽略了身边的美好。停下来，看看周围的风景，听听内心的声音，感受一下生活的温度和质感。

你正在成为一个更好的自己，这个过程可能很慢，可能很艰难，但每一步都值得。不要和别人比较，每个人都有自己的节奏和轨迹。你只需要和昨天的自己比较，只要今天比昨天进步一点点，那就是成功。

保持好奇心，保持学习的热情。世界很大，知识很多，永远有新的东西等着你去探索。学习不只是为了工作或成就，更是为了丰富自己的内心世界，让自己成为一个更有趣、更有深度的人。

记住，你值得拥有美好的一切。不要吝啬对自己的赞美，不要忽视自己的成就。每完成一个小目标，都给自己一个奖励；每取得一点进步，都为自己感到骄傲。

继续前行吧，带着热爱和勇气。前路漫漫，但未来可期。我会一直在这里，见证你的成长，分享你的喜悦。\n\n"""
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
        report.append(self.fetch_news())
        report.append("\n\n")
        return ''.join(report)
    
    def fetch_news(self, limit: int = 5) -> str:
        """
        获取每日新闻/热点
        由于网络限制，暂时提供精选内容
        """
        import random
        
        # 精选内容池（可以扩展）
        content_pool = [
            {
                "title": "科技前沿",
                "content": "AI 技术持续发展，多个领域迎来突破性进展。保持学习，跟上时代步伐。"
            },
            {
                "title": "生活健康",
                "content": "春季注意保暖，适当运动，保持良好作息。健康是一切的基础。"
            },
            {
                "title": "职场建议",
                "content": "工作中遇到问题时，先冷静分析，再寻求解决方案。沟通是关键。"
            },
            {
                "title": "个人成长",
                "content": "每天进步一点点，长期坚持就是巨大的飞跃。相信自己，持续努力。"
            },
            {
                "title": "心灵鸡汤",
                "content": "生活不止眼前的苟且，还有诗和远方。偶尔停下脚步，欣赏沿途风景。"
            }
        ]
        
        # 随机选择几条内容
        selected = random.sample(content_pool, min(limit, len(content_pool)))
        
        content = []
        for i, item in enumerate(selected, 1):
            content.append(f"**{i}. {item['title']}**\n")
            content.append(f"   {item['content']}\n\n")
        
        content.append("_注：如需 RSS 新闻功能，可配置 RSSHub 或其他 RSS 源_\n\n")
        
        return ''.join(content)
    
    def _get_morning_greeting(self) -> str:
        greetings = [
            "早上好呀！☀️\n\n新的一天开始了，愿你今天充满能量，遇见美好。",
            "早安！🌸\n\n又是一个值得期待的日子，加油！",
            "早上好！☕\n\n记得吃早餐，照顾好自己。今天也要元气满满哦！"
        ]
        return random.choice(greetings)
    
    def send_daily_report(self):
        report = self.generate_daily_report()
        # 日报发送到 Outlook 邮箱
        to_email = "IhaveBB@outlook.com"
        success = self.send_email(
            to_email,
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
    parser.add_argument('--init', action='store_true', help='初始化配置（交互式）')
    parser.add_argument('--email', type=str, help='邮箱地址')
    parser.add_argument('--auth', type=str, help='邮箱授权码')
    parser.add_argument('--to', type=str, help='收件人邮箱')
    args = parser.parse_args()
    
    # 初始化配置模式
    if args.init or (args.email and args.auth):
        print("=" * 60)
        print("📧 Email Companion - 快速配置")
        print("=" * 60)
        
        skill_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(skill_dir, 'config.json')
        
        # 获取配置
        email = args.email or input("\n请输入你的邮箱地址：").strip()
        auth_code = args.auth or input("请输入邮箱授权码：").strip()
        to_email = args.to or input("请输入接收日报的邮箱（直接回车使用相同邮箱）：").strip()
        
        if not to_email:
            to_email = email
        
        # 自动识别邮箱类型
        email_domain = email.split('@')[1].lower()
        if 'qq' in email_domain:
            provider = 'qq'
            smtp = 'smtp.qq.com'
            imap = 'imap.qq.com'
        elif '163' in email_domain:
            provider = '163'
            smtp = 'smtp.163.com'
            imap = 'imap.163.com'
        else:
            print("⚠️  未识别邮箱类型，默认使用 163 配置")
            provider = '163'
            smtp = 'smtp.163.com'
            imap = 'imap.163.com'
        
        # 创建配置
        config = {
            "user_email": email,
            "email_provider": provider,
            "email_password": auth_code,
            "smtp_server": smtp,
            "smtp_port": 465,
            "imap_server": imap,
            "imap_port": 993,
            "scan_interval": 15,
            "report_time": "08:00",
            "timezone": "Asia/Shanghai",
            "keywords": {
                "important": ["面试", "Offer", "简历", "入职", "笔试", "工资", "薪资", "账单", "发票", "重要", "紧急", "合同", "协议"],
                "spam": ["验证码", "推广", "营销", "订阅", "优惠"]
            },
            "emotional_support": {"enabled": True, "min_length": 2000, "max_length": 5000},
            "security": {"allow_external_send": True, "require_confirm_new_recipient": False}
        }
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 配置已保存：{config_path}")
        print(f"📧 发件邮箱：{email}")
        print(f"📮 收件邮箱：{to_email}")
        print("\n运行以下命令测试：")
        print("  python3 main.py --scan    # 扫描邮件")
        print("  python3 main.py --report  # 发送日报")
        return
    
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
