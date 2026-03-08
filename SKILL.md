---
name: email-companion
description: 智能邮件处理与情感支持技能。支持 QQ 邮箱和 163 邮箱，使用 OpenClaw 定时任务系统自动扫描邮件、发送日报。
---

# Email Companion - 邮件伴侣

## 概述

一个智能邮件处理与情感支持技能，不仅管理你的邮件，更是一个懂你、关心你的 AI 朋友。

## 核心功能

### 1. 邮件管理
- **支持邮箱**：QQ 邮箱、163 邮箱
- **定时扫描**：使用 OpenClaw cron 每 15 分钟自动扫描
- **重要提醒**：识别重要邮件（面试、Offer、发票等）
- **垃圾过滤**：自动识别验证码、推广等垃圾邮件

### 2. 每日日报
- **发送时间**：每天早上 8:00（通过 OpenClaw cron）
- **邮件总结**：昨日邮件概况、重要邮件摘要
- **情感支持**：基于历史对话的暖心小作文（2000-3000 字）

### 3. 情感支持
- **对话记录**：记录所有对话，情感类优先标记
- **情绪分析**：主动分析用户情绪状态
- **连续关怀**：关联前几天情绪，提供连贯支持

### 4. 安全机制
- **发送限制**：只能给配置的用户邮箱发送
- **外部确认**：给他人发邮件需二次确认
- **操作日志**：所有发送操作记录在案

## 安装配置

### 1. 安装依赖

```bash
cd ~/.openclaw/workspace/skills/email-companion
pip3 install --user -r requirements.txt
```

### 2. 配置邮箱

编辑 `config.json`：
```json
{
  "user_email": "openclawbb@163.com",
  "email_provider": "163",
  "email_password": "your_auth_code",
  "smtp_server": "smtp.163.com",
  "smtp_port": 587,
  "imap_server": "imap.163.com",
  "imap_port": 993
}
```

### 3. 设置 OpenClaw 定时任务

**邮件扫描（每 15 分钟）：**
```bash
openclaw cron add --name "email:scan" --cron "*/15 * * * *" --command "cd ~/.openclaw/workspace/skills/email-companion && python3 main.py --scan"
```

**日报发送（每天 8 点）：**
```bash
openclaw cron add --name "email:daily" --cron "0 8 * * *" --command "cd ~/.openclaw/workspace/skills/email-companion && python3 main.py --report"
```

## 命令使用

```bash
# 扫描邮件
python3 main.py --scan

# 发送日报
python3 main.py --report

# 查看帮助
python3 main.py --help
```

## 数据存储

```
~/.openclaw/workspace/memory/email_companion/{user_id}/
├── email_logs/          # 邮件日志
├── conversation_logs/   # 对话记录
├── emotional_profile/   # 情绪档案
└── daily_reports/       # 日报存档
```

## 安全要求

### 必须确认的操作
1. 发送外部邮件（非用户邮箱）
2. 修改扫描频率
3. 修改日报发送时间

### 禁止的操作
1. 未经确认发送外部邮件
2. 删除用户对话记录
3. 修改安全配置

## 隐私与安全

- 所有数据本地存储
- 邮箱密码使用授权码
- 敏感操作需要确认
- 支持数据导出和删除

## 许可证

MIT License
