# 📧 Email Companion - 邮件伴侣

一个智能邮件处理与情感支持技能，不仅管理你的邮件，更是一个懂你、关心你的 AI 朋友。

## ✨ 核心功能

### 1. 邮件管理
- 📧 **支持邮箱**：QQ 邮箱、163 邮箱
- ⏱️ **定时扫描**：每 15 分钟自动扫描收件箱
- 🔔 **重要提醒**：识别重要邮件（面试、Offer、发票等）
- 🗑️ **垃圾过滤**：自动识别验证码、推广等垃圾邮件

### 2. 每日日报
- ⏰ **发送时间**：每天早上 8:00
- 📊 **邮件总结**：昨日邮件概况、重要邮件摘要
- 💝 **情感支持**：基于历史对话的暖心小作文（2000-3000 字）

### 3. 情感支持
- 💬 **对话记录**：记录所有对话，情感类优先标记
- 🧠 **情绪分析**：主动分析用户情绪状态
- 💝 **连续关怀**：关联前几天情绪，提供连贯支持
- 🎁 **随机惊喜**：不定期发送暖心消息

### 4. 安全机制
- 🔐 **发送限制**：只能给配置的用户邮箱发送
- ⚠️ **外部确认**：给他人发邮件需二次确认
- 📝 **操作日志**：所有发送操作记录在案

## 🚀 快速开始

### 1. 安装依赖

```bash
cd ~/.openclaw/workspace/skills/email-companion
pip3 install --user -r requirements.txt
```

### 2. 运行安装脚本（推荐）

```bash
python3 install.py
```

安装脚本会自动：
- ✅ 引导你配置邮箱
- ✅ 自动识别邮箱服务商（QQ/163）
- ✅ 设置 OpenClaw 定时任务
- ✅ 生成配置文件

### 3. 或者手动配置

编辑 `config.json`：
```json
{
  "user_email": "your_email@qq.com",
  "email_provider": "qq",
  "email_password": "your_auth_code",
  "smtp_server": "smtp.qq.com",
  "smtp_port": 465,
  "imap_server": "imap.qq.com",
  "imap_port": 993
}
```

### 4. 设置定时任务

```bash
python3 main.py --setup
```

或手动添加：
```bash
# 邮件扫描（每 15 分钟）
openclaw cron add --name "email:scan" --cron "*/15 * * * *" --command "cd ~/.openclaw/workspace/skills/email-companion && python3 main.py --scan"

# 日报发送（每天早上 8 点）
openclaw cron add --name "email:daily" --cron "0 8 * * *" --command "cd ~/.openclaw/workspace/skills/email-companion && python3 main.py --report"
```

## 📋 命令使用

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

## 🔧 邮箱配置说明

### QQ 邮箱
1. 登录 https://mail.qq.com
2. 设置 → 账户
3. 开启 IMAP/SMTP 服务
4. 生成授权码

### 163 邮箱
1. 登录 https://mail.163.com
2. 设置 → POP3/SMTP/IMAP
3. 开启 IMAP/SMTP 服务
4. 获取授权码

### 配置参数

| 参数 | QQ 邮箱 | 163 邮箱 |
|------|--------|---------|
| smtp_server | smtp.qq.com | smtp.163.com |
| smtp_port | 465 (SSL) | 465 (SSL) |
| imap_server | imap.qq.com | imap.163.com |
| imap_port | 993 | 993 |

## 📁 数据存储

```
~/.openclaw/workspace/memory/email_companion/{user_id}/
├── email_logs/          # 邮件日志
├── conversation_logs/   # 对话记录
├── emotional_profile/   # 情绪档案
└── daily_reports/       # 日报存档
```

## ⚠️ 安全提示

1. **授权码**：使用授权码，不是登录密码
2. **配置文件**：`config.json` 已被加入 `.gitignore`，请勿上传到公开仓库
3. **扫描频率**：建议不低于 15 分钟，避免被邮箱服务商限制
4. **隐私保护**：所有数据本地存储

## 🐛 常见问题

### 1. 连接失败
- 检查授权码是否正确
- 检查是否开启了 IMAP/SMTP 服务
- 检查防火墙设置

### 2. 邮件发送失败
- 确认 SMTP 配置正确
- 确认授权码有效
- 查看日志文件：`email_companion.log`

### 3. 定时任务不执行
- 检查任务是否添加成功：`openclaw cron list`
- 查看任务运行记录：`openclaw cron runs <task_id>`
- 确认 Python 路径正确

## 📞 技术支持

如有问题，请查看日志文件或提交 Issue。

## 📄 许可证

MIT License
