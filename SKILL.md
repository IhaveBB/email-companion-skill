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

一个智能邮件处理与情感支持技能，不仅管理你的邮件，更是一个懂你、关心你的 AI 朋友。

## ✨ 核心功能

### 1. 邮件管理 📬
- **支持邮箱**：QQ 邮箱、163 邮箱
- **定时扫描**：每 15 分钟自动扫描新邮件
- **智能分类**：自动识别重要邮件（面试、Offer、发票等）
- **垃圾过滤**：自动识别验证码、推广等垃圾邮件

### 2. 每日日报 📊
- **发送时间**：每天早上 8:00（可配置）
- **邮件总结**：昨日邮件概况、重要邮件摘要
- **情感支持**：基于历史对话的暖心小作文（2000-3000 字）
- **每日新闻**：自动抓取 RSS 新闻（澎湃/36 氪/知乎）

### 3. 情感支持 💝
- **对话记录**：记录所有对话，情感类优先标记
- **情绪分析**：主动分析用户情绪状态
- **连续关怀**：关联前几天情绪，提供连贯支持

### 4. 安全机制 🔒
- **发送限制**：可配置是否允许发送到外部邮箱
- **外部确认**：给他人发邮件可配置二次确认
- **操作日志**：所有发送操作记录在案
- **本地存储**：所有数据本地存储，保护隐私

## 🚀 安装方法

### 方法 1：使用 ClawHub（推荐）

```bash
clawhub install email-companion
```

### 方法 2：手动安装

```bash
# 1. 克隆或下载 skill
cd ~/.openclaw/workspace/skills/
git clone https://github.com/IhaveBB/email-companion-skill.git email-companion

# 2. 安装依赖
cd email-companion
pip3 install --user -r requirements.txt

# 3. 运行安装向导
python3 install.py
```

### 方法 3：从 ClawHub 安装

访问 https://clawhub.com 搜索 "email-companion" 进行安装。

## ⚙️ 配置说明

运行安装向导会自动引导你完成配置：

```bash
python3 install.py
```

或手动创建配置文件：

```bash
cp config.example.json config.json
# 然后编辑 config.json 填写你的邮箱信息
```

### 配置项说明

```json
{
  "user_email": "your_email@qq.com",        // 邮箱地址
  "email_provider": "qq",                    // qq 或 163
  "email_password": "your_auth_code",        // 授权码（不是密码）
  "smtp_server": "smtp.qq.com",              // SMTP 服务器
  "smtp_port": 465,                          // SMTP 端口
  "imap_server": "imap.qq.com",              // IMAP 服务器
  "imap_port": 993,                          // IMAP 端口
  "scan_interval": 15,                       // 扫描间隔（分钟）
  "report_time": "08:00",                    // 日报时间
  "timezone": "Asia/Shanghai",               // 时区
  "keywords": {                              // 关键词
    "important": ["面试", "Offer", "发票"],
    "spam": ["验证码", "推广"]
  },
  "emotional_support": {
    "enabled": true,
    "min_length": 2000,
    "max_length": 5000
  },
  "security": {
    "allow_external_send": false,
    "require_confirm_new_recipient": true
  }
}
```

## 📖 使用方法

### 基本命令

```bash
# 扫描邮件
python3 main.py --scan

# 发送日报
python3 main.py --report

# 设置定时任务
python3 main.py --setup

# 查看帮助
python3 main.py --help
```

### 定时任务

安装向导会自动设置 OpenClaw 定时任务，也可以手动设置：

```bash
# 查看任务
openclaw cron list

# 邮件扫描（每 15 分钟）
openclaw cron add --name "email:scan" --cron "*/15 * * * *" \
  --command "cd ~/.openclaw/workspace/skills/email-companion && python3 main.py --scan"

# 日报发送（每天 8 点）
openclaw cron add --name "email:daily" --cron "0 8 * * *" \
  --command "cd ~/.openclaw/workspace/skills/email-companion && python3 main.py --report"
```

## 🔑 获取邮箱授权码

### QQ 邮箱
1. 登录网页版 QQ 邮箱
2. 设置 → 账户 → 开启 IMAP/SMTP 服务
3. 生成授权码

### 163 邮箱
1. 登录网页版 163 邮箱
2. 设置 → POP3/SMTP/IMAP → 开启服务
3. 设置客户端授权密码

## 📁 数据存储

```
~/.openclaw/workspace/memory/email_companion/{user_id}/
├── email_logs/          # 邮件日志
├── conversation_logs/   # 对话记录
├── emotional_profile/   # 情绪档案
└── daily_reports/       # 日报存档
```

## ⚠️ 注意事项

1. **授权码安全**
   - 授权码不是登录密码
   - `config.json` 已被加入 `.gitignore`
   - 不要上传到公开仓库

2. **邮箱限制**
   - 需要开启 IMAP/SMTP 服务
   - 163 邮箱可能需要联系客服开通完整权限

3. **扫描频率**
   - 建议不低于 15 分钟/次
   - 过于频繁可能触发限制

## 🛠️ 故障排查

**IMAP 连接失败：**
- 检查授权码是否正确
- 确认已开启 IMAP/SMTP 服务

**SELECT Unsafe Login：**
- 163 邮箱需联系客服开通权限
- 或改用 QQ 邮箱

**日报未发送：**
- 检查日志：`cat email_companion.log`
- 确认收件人配置正确

## 📚 更多文档

详细文档请查看：[README.md](README.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📮 作者

- **IhaveBB**
- GitHub: https://github.com/IhaveBB/email-companion-skill
- 邮箱：ihavebb@outlook.com
