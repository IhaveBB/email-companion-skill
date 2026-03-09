# 📧 Email Companion - 邮件伴侣

> OpenClaw 原生技能 - 智能邮件处理与情感支持

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
- **个性化**：基于用户历史生成个性化关怀内容

### 4. 安全机制 🔒
- **发送限制**：可配置是否允许发送到外部邮箱
- **外部确认**：给他人发邮件可配置二次确认
- **操作日志**：所有发送操作记录在案
- **本地存储**：所有数据本地存储，保护隐私

## 🚀 快速开始

### 1. 安装依赖

```bash
cd ~/.openclaw/workspace/skills/email-companion
pip3 install --user -r requirements.txt
```

### 2. 运行安装向导

```bash
python3 install.py
```

安装向导会帮你：
- 配置邮箱信息（自动识别 QQ/163 邮箱）
- 设置授权码
- 配置扫描间隔和日报时间
- 设置 OpenClaw 定时任务

### 3. 手动配置（可选）

如果不使用安装向导，可以手动创建 `config.json`：

```bash
cp config.example.json config.json
```

然后编辑 `config.json` 填写你的邮箱信息。

### 4. 测试运行

```bash
# 扫描邮件
python3 main.py --scan

# 发送日报
python3 main.py --report

# 查看帮助
python3 main.py --help
```

## 📋 配置说明

### config.json 配置项

```json
{
  "user_email": "your_email@qq.com",        // 你的邮箱地址
  "email_provider": "qq",                    // 邮箱服务商：qq 或 163
  "email_password": "your_auth_code",        // 邮箱授权码（不是登录密码）
  "smtp_server": "smtp.qq.com",              // SMTP 服务器
  "smtp_port": 465,                          // SMTP 端口
  "imap_server": "imap.qq.com",              // IMAP 服务器
  "imap_port": 993,                          // IMAP 端口
  "scan_interval": 15,                       // 扫描间隔（分钟）
  "report_time": "08:00",                    // 日报发送时间
  "timezone": "Asia/Shanghai",               // 时区
  "keywords": {                              // 关键词配置
    "important": ["面试", "Offer", "发票"],  // 重要邮件关键词
    "spam": ["验证码", "推广"]               // 垃圾邮件关键词
  },
  "emotional_support": {                     // 情感支持配置
    "enabled": true,                         // 是否启用
    "min_length": 2000,                      // 最小字数
    "max_length": 5000                       // 最大字数
  },
  "security": {                              // 安全配置
    "allow_external_send": false,            // 是否允许发送外部邮件
    "require_confirm_new_recipient": true    // 新收件人是否需要确认
  }
}
```

### 获取邮箱授权码

#### QQ 邮箱
1. 登录网页版 QQ 邮箱
2. 点击「设置」→「账户」
3. 找到「POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV 服务」
4. 开启「IMAP/SMTP 服务」
5. 点击「生成授权码」

#### 163 邮箱
1. 登录网页版 163 邮箱
2. 点击「设置」→「POP3/SMTP/IMAP」
3. 开启「IMAP/SMTP 服务」
4. 点击「客户端授权密码」→「设置」
5. 获取授权码

## 🔧 高级用法

### 定时任务设置

使用 OpenClaw cron 系统：

```bash
# 查看现有任务
openclaw cron list

# 添加邮件扫描任务（每 15 分钟）
openclaw cron add --name "email:scan" --cron "*/15 * * * *" \
  --command "cd ~/.openclaw/workspace/skills/email-companion && python3 main.py --scan"

# 添加日报发送任务（每天 8 点）
openclaw cron add --name "email:daily" --cron "0 8 * * *" \
  --command "cd ~/.openclaw/workspace/skills/email-companion && python3 main.py --report"
```

### 数据存储位置

```
~/.openclaw/workspace/memory/email_companion/{user_id}/
├── email_logs/          # 邮件日志（按日期）
├── conversation_logs/   # 对话记录（按日期）
├── emotional_profile/   # 情绪档案
└── daily_reports/       # 日报存档（按日期）
```

### 自定义情感支持内容

编辑 `main.py` 中的以下方法：
- `_get_comfort_text()` - 安慰文本
- `_get_encouragement_text()` - 鼓励文本
- `_get_daily_suggestions()` - 每日建议
- `_get_inspirational_quote()` - 励志名言

## ⚠️ 注意事项

1. **授权码安全**
   - 授权码不是登录密码
   - 不要将 `config.json` 上传到公开仓库
   - 已自动加入 `.gitignore`

2. **邮箱服务商限制**
   - QQ 邮箱：需要开启 IMAP/SMTP 服务
   - 163 邮箱：需要开启 IMAP/SMTP 服务，部分账号可能需要联系客服开通完整权限

3. **扫描频率**
   - 建议不低于 15 分钟/次
   - 过于频繁可能触发邮箱服务商限制

4. **外部邮件发送**
   - 默认只允许发送到配置的邮箱
   - 如需发送到其他邮箱，请修改 `security.allow_external_send`

## 🛠️ 故障排查

### 问题 1：IMAP 连接失败
**现象：** `IMAP 连接失败：connection timed out`

**解决：**
1. 检查邮箱授权码是否正确
2. 确认已开启 IMAP/SMTP 服务
3. 检查防火墙设置

### 问题 2：SELECT Unsafe Login
**现象：** `SELECT Unsafe Login. Please contact kefu@188.com for help`

**解决：**
- 163 邮箱需要联系客服开通完整 IMAP 权限
- 或改用 QQ 邮箱

### 问题 3：日报未发送
**现象：** 定时任务运行但没收到日报

**解决：**
1. 检查日志：`cat email_companion.log`
2. 确认收件人邮箱配置正确
3. 检查 `security.allow_external_send` 配置

## 📚 命令参考

```bash
# 扫描邮件
python3 main.py --scan

# 发送日报
python3 main.py --report

# 设置定时任务
python3 main.py --setup

# 查看帮助
python3 main.py --help

# 指定配置文件
python3 main.py --scan --config /path/to/config.json
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📮 联系方式

- 作者：IhaveBB
- 邮箱：ihavebb@outlook.com
- GitHub：https://github.com/IhaveBB/email-companion-skill
