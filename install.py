#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Companion 安装脚本
自动配置邮箱和定时任务
"""

import os
import json
import sys

def main():
    print("=" * 60)
    print("📧 Email Companion - 邮件伴侣 安装向导")
    print("=" * 60)
    print()
    
    # 获取当前脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')
    
    # 检查配置文件
    if os.path.exists(config_path):
        print("⚠️  检测到已有配置文件")
        print(f"   路径：{config_path}")
        choice = input("   是否重新配置？(y/n): ").strip().lower()
        if choice != 'y':
            print("✅ 使用现有配置")
            print()
        else:
            print()
    else:
        print("📝 开始配置邮箱...")
        print()
    
    # 配置模板
    config = {
        "user_email": "",
        "email_provider": "",
        "email_password": "",
        "smtp_server": "",
        "smtp_port": 465,
        "imap_server": "",
        "imap_port": 993,
        "scan_interval": 15,
        "report_time": "08:00",
        "timezone": "Asia/Shanghai",
        "keywords": {
            "important": ["面试", "Offer", "简历", "入职", "笔试", "工资", "薪资", "账单", "发票", "重要", "紧急", "合同", "协议"],
            "spam": ["验证码", "推广", "营销", "订阅", "优惠"]
        },
        "emotional_support": {"enabled": True, "min_length": 2000, "max_length": 5000},
        "security": {"allow_external_send": False, "require_confirm_new_recipient": True}
    }
    
    # 获取邮箱地址
    if not config.get('user_email'):
        while True:
            email = input("请输入你的邮箱地址：").strip()
            if '@' in email:
                config['user_email'] = email
                break
            print("❌ 请输入有效的邮箱地址")
    
    # 自动识别邮箱服务商
    email_domain = config['user_email'].split('@')[1].lower()
    if 'qq' in email_domain:
        config['email_provider'] = 'qq'
        config['smtp_server'] = 'smtp.qq.com'
        config['imap_server'] = 'imap.qq.com'
        print("✅ 识别为 QQ 邮箱")
    elif '163' in email_domain:
        config['email_provider'] = '163'
        config['smtp_server'] = 'smtp.163.com'
        config['imap_server'] = 'imap.163.com'
        print("✅ 识别为 163 邮箱")
    else:
        print("⚠️  未识别邮箱类型，请手动选择")
        print("   1. QQ 邮箱")
        print("   2. 163 邮箱")
        choice = input("   请选择 (1/2): ").strip()
        if choice == '1':
            config['email_provider'] = 'qq'
            config['smtp_server'] = 'smtp.qq.com'
            config['imap_server'] = 'imap.qq.com'
        else:
            config['email_provider'] = '163'
            config['smtp_server'] = 'smtp.163.com'
            config['imap_server'] = 'imap.163.com'
    
    print()
    print("🔑 请输入邮箱授权码（不是登录密码！）")
    print("   提示：授权码需要在邮箱设置中获取")
    config['email_password'] = input("   授权码：").strip()
    
    print()
    print("⏰ 邮件扫描间隔（分钟），默认 15 分钟：")
    interval = input("   请输入（直接回车使用默认值）：").strip()
    if interval:
        config['scan_interval'] = int(interval)
    
    print()
    print("📅 日报发送时间（24 小时制），默认 08:00：")
    report_time = input("   请输入（直接回车使用默认值）：").strip()
    if report_time:
        config['report_time'] = report_time
    
    # 保存配置
    print()
    print("💾 保存配置文件...")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"✅ 配置已保存到：{config_path}")
    print()
    
    # 提醒用户
    print("⚠️  重要提示：")
    print("   1. config.json 包含敏感信息，已被加入 .gitignore")
    print("   2. 请勿将 config.json 上传到公开仓库")
    print("   3. 本仓库的 config.json 仅为示例模板")
    print()
    
    # 设置定时任务
    print("⚙️  是否现在设置 OpenClaw 定时任务？")
    print("   - 邮件扫描：每 15 分钟自动扫描")
    print("   - 日报发送：每天早上 8 点发送")
    choice = input("   是否设置？(y/n): ").strip().lower()
    
    if choice == 'y':
        print()
        print("🚀 设置定时任务...")
        import subprocess
        scan_cmd = f"cd {script_dir} && python3 main.py --scan"
        report_cmd = f"cd {script_dir} && python3 main.py --report"
        
        try:
            result = subprocess.run(
                ['openclaw', 'cron', 'add', '--name', 'email:scan', '--cron', '*/15 * * * *', '--command', scan_cmd],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print("   ✅ 邮件扫描任务已设置")
            else:
                print(f"   ⚠️  扫描任务可能已存在")
            
            result = subprocess.run(
                ['openclaw', 'cron', 'add', '--name', 'email:daily', '--cron', '0 8 * * *', '--command', report_cmd],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print("   ✅ 日报发送任务已设置")
            else:
                print(f"   ⚠️  日报任务可能已存在")
            
            print()
            print("✅ 定时任务设置完成！")
        except Exception as e:
            print(f"❌ 设置失败：{e}")
            print("   可以稍后手动运行：python3 main.py --setup")
    else:
        print()
        print("💡 稍后可以手动运行：python3 main.py --setup")
    
    print()
    print("=" * 60)
    print("🎉 安装完成！")
    print("=" * 60)
    print()
    print("📚 使用帮助：")
    print("   - 扫描邮件：python3 main.py --scan")
    print("   - 发送日报：python3 main.py --report")
    print("   - 设置定时任务：python3 main.py --setup")
    print("   - 查看帮助：python3 main.py --help")
    print()
    print("🔍 查看定时任务：openclaw cron list")
    print()


if __name__ == '__main__':
    main()
