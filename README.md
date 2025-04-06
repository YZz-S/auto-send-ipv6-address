# IPv6地址自动发送程序

这是一个在Windows系统上开机自启动的应用程序，它会自动获取本机的IPv6地址，并通过邮件发送到指定邮箱。

## 功能特点

- 开机自动启动
- 自动获取系统IPv6地址
- 当IPv6地址变化时自动发送邮件通知
- 支持自定义邮箱设置和检查间隔

## 使用说明

### 安装步骤

1. 确保您的系统已安装Python（建议3.6及以上版本）
2. 下载本程序所有文件到同一个文件夹
3. 修改`config.json`文件，填入您的邮箱设置
4. 运行`setup_autostart.bat`设置开机自启动

### 配置文件说明

配置文件`config.json`包含以下设置项：

```json
{
    "smtp_server": "smtp.example.com",  // SMTP服务器地址
    "smtp_port": 465,  // SMTP服务器端口（通常是465或587）
    "sender_email": "your_email@example.com",  // 发件人邮箱
    "sender_password": "your_password",  // 发件人邮箱密码或授权码
    "receiver_email": "receiver@example.com",  // 接收者邮箱
    "check_interval": 3600,  // 检查间隔（单位：秒，默认为1小时）
    "last_sent_ipv6": ""  // 最后一次发送的IPv6地址（自动更新，无需手动修改）
}
```

### 常见邮箱SMTP设置

- QQ邮箱:
  - SMTP服务器：smtp.qq.com
  - 端口：465
  - 密码：需要在QQ邮箱设置中开启SMTP服务并获取授权码

- 163邮箱:
  - SMTP服务器：smtp.163.com
  - 端口：465
  - 密码：需要在163邮箱设置中开启SMTP服务并获取授权码

- Gmail:
  - SMTP服务器：smtp.gmail.com
  - 端口：587
  - 密码：需要在Google账户中开启"不够安全的应用"访问权限

## 手动运行

如果您想手动运行程序而不等待开机启动，可以直接运行`start_ipv6_sender.vbs`文件。

## 日志文件

程序会自动生成日志文件`ipv6_sender.log`，记录运行状态和错误信息，以便于排查问题。

## 注意事项

- 请确保您的计算机已连接到网络并分配了IPv6地址
- 某些邮箱服务提供商可能需要特殊设置，如开启SMTP服务或生成应用专用密码
- 如需卸载，只需删除启动文件夹中的快捷方式即可停止自动启动 