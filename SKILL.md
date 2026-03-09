---
name: email-companion
description: 全自动邮件管理技能，支持 QQ/163 邮箱自动扫描、日报发送、情感支持、随机惊喜。
author: IhaveBB
version: 1.0.0
tags: ["email", "automation", "productivity"]
requires:
  - python3
  - pip3
---

# 📧 Email Companion - 邮件伴侣

**全自动邮件管理技能** - 自动扫描邮件、发送日报、情感支持、随机惊喜

## ✨ 功能特性

### 📬 自动邮件扫描
- 每 15 分钟自动扫描新邮件
- 智能分类：重要邮件、普通邮件、垃圾邮件
- 支持 QQ 邮箱、163 邮箱

### 📊 每日日报
- **发送时间**：每天早上 8:00 自动发送
- **内容包括**：
  - 📧 邮件总结（昨日收到多少邮件）
  - 💼 重要邮件摘要
  - 💝 情感支持小作文（2000-3000 字暖心内容）
  - 📰 今日精选（科技/生活/职场/成长）
  - 🎁 随机惊喜（每日不同的小确幸）
  - 💬 每日金句（名人名言/励志语录）

### 💝 情感支持
- 基于对话历史生成个性化关怀
- 情绪分析（积极/消极/压力）
- 连续关怀（关联前几天情绪）
- 暖心小作文（2000-3000 字）

### 🎁 随机惊喜
- 每日不同的惊喜消息
- 励志金句
- 暖心问候

## 🚀 安装使用

### 1. 安装依赖
```bash
pip3 install --user -r requirements.txt
```

### 2. 配置邮箱（首次使用）
```bash
python3 install.py
```
按提示输入：
- 邮箱地址（QQ 或 163）
- 授权码（在邮箱设置中获取）
- 接收日报的邮箱

### 3. 设置自动任务
```bash
python3 main.py --setup
```

**完成！** 之后全自动运行：
- ✅ 每 15 分钟自动扫描邮件
- ✅ 每天早上 8 点自动发送日报

## 🔑 获取授权码

### QQ 邮箱
1. 登录网页版 QQ 邮箱
2. 设置 → 账户
3. 开启 IMAP/SMTP 服务
4. 生成授权码

### 163 邮箱
1. 登录网页版 163 邮箱
2. 设置 → POP3/SMTP/IMAP
3. 开启 IMAP/SMTP 服务
4. 设置客户端授权码

## 📁 数据存储

所有数据本地存储，保护隐私：
```
~/.openclaw/workspace/memory/email_companion/
├── email_logs/          # 邮件日志
├── conversation_logs/   # 对话记录
├── emotional_profile/   # 情绪档案
└── daily_reports/       # 日报存档
```

## ⚠️ 注意事项

1. **授权码安全**
   - 授权码不是登录密码
   - config.json 已被加入.gitignore
   - 不要上传到公开仓库

2. **邮箱服务**
   - 需要开启 IMAP/SMTP 服务
   - 163 邮箱可能需要联系客服开通完整权限

3. **全自动运行**
   - 配置后无需手动操作
   - 定时任务自动执行
   - 如需修改配置重新运行 `install.py`

## 🛠️ 手动命令（可选）

虽然全自动，但也支持手动命令：

```bash
# 扫描邮件
python3 main.py --scan

# 发送日报
python3 main.py --report

# 重新设置定时任务
python3 main.py --setup
```

## 📮 作者

**IhaveBB** - https://github.com/IhaveBB/email-companion-skill

## 📄 许可证

MIT License
