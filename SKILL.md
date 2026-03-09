---
name: email-companion
description: 智能邮件处理与情感支持技能。支持 QQ 邮箱和 163 邮箱，使用 OpenClaw 定时任务系统自动扫描邮件、发送日报。
author: IhaveBB
version: 1.0.0
tags: ["email", "productivity", "automation", "emotional-support"]
requires:
  - python3
  - pip3
config:
  email:
    description: 邮箱地址
    required: true
  auth_code:
    description: 邮箱授权码
    required: true
    secret: true
---

# Email Companion - 邮件伴侣 📧

一个智能邮件处理与情感支持技能，自动扫描邮件、发送日报，做你的 AI 朋友。

## ✨ 核心功能

- 📬 **自动扫描邮件** - 支持 QQ/163 邮箱，每 15 分钟自动扫描
- 📊 **每日日报** - 每天早上 8 点发送邮件总结 + 情感支持
- 💝 **情感支持** - 基于对话历史的暖心小作文
- 🔒 **安全隐私** - 所有数据本地存储

## 🚀 快速使用

### 1. 安装

```bash
# 安装依赖
pip3 install --user -r requirements.txt
```

### 2. 配置（三选一）

**方式 1：命令行配置（最简单）**
```bash
python3 main.py --init
# 按提示输入邮箱、授权码即可
```

**方式 2：一键配置**
```bash
python3 main.py --email your@qq.com --auth YOUR_AUTH_CODE
```

**方式 3：安装向导**
```bash
python3 install.py
```

### 3. 测试

```bash
python3 main.py --scan    # 扫描邮件
python3 main.py --report  # 发送日报
```

### 4. 设置定时任务（可选）

```bash
python3 main.py --setup
```

## ⚙️ 配置说明

**只需要 3 个信息：**

1. **邮箱地址** - 你的 QQ 或 163 邮箱
2. **授权码** - 邮箱的 SMTP/IMAP 授权码（不是登录密码）
3. **收件邮箱** - 接收日报的邮箱（可与发件邮箱相同）

**获取授权码：**

- **QQ 邮箱**：设置→账户→开启 IMAP/SMTP→生成授权码
- **163 邮箱**：设置→POP3/SMTP/IMAP→开启服务→设置授权码

## ⚠️ 注意事项

- 授权码不是登录密码，需要在邮箱设置中获取
- config.json 包含敏感信息，已被加入.gitignore
- 163 邮箱可能需要联系客服开通完整 IMAP 权限

## 🤝 作者

**IhaveBB** - https://github.com/IhaveBB/email-companion-skill
