# IPv6地址自动发送程序

这是一个在Windows系统上开机自启动的应用程序，它会自动获取本机的IPv6地址，并通过邮件发送到指定邮箱。当IPv6地址发生变化时，程序会自动发送新的地址，便于远程访问。

## 功能特点

- 开机自动启动，无需手动干预
- 多种方式获取系统IPv6地址，提高成功率：
  - 通过socket连接方式获取
  - 通过ipconfig命令解析系统网络配置
  - 通过在线API获取公网IPv6地址
- 当IPv6地址变化时自动发送邮件通知
- 支持仅发送开机通知功能，不检测IPv6地址
- 支持多种加密传输方式（SSL/TLS），保障邮件传输安全
- 支持自定义邮箱设置和检查间隔
- 自动记录日志，便于排查问题
- 完全兼容中文环境和UTF-8编码
- 所有路径可在配置文件中自定义，提高灵活性
- 防止重复启动机制，避免多实例运行导致的重复发送邮件问题

## 文件说明

- `auto_send_ipv6.py` - 主程序，负责获取IPv6地址并发送邮件
- `boot_notification.py` - 开机通知程序，仅在开机时发送通知邮件
- `config.json` - 配置文件，包含邮箱信息和路径设置
- `setup_autostart.bat` - 设置IPv6地址发送功能开机自启动的批处理脚本
- `setup_boot_notification.bat` - 设置开机通知功能自启动的批处理脚本
- `start_ipv6_sender.vbs` - 后台运行IPv6发送程序的VBS脚本（由setup_autostart.bat自动创建）
- `start_boot_notification.vbs` - 后台运行开机通知程序的VBS脚本（由setup_boot_notification.bat自动创建）
- `test_ipv6_email.py` - 测试IPv6地址获取和邮件发送的脚本
- `test_boot_notification.py` - 测试开机通知功能的脚本
- `test_qq_email.py` - 专门测试QQ邮箱SMTP发送功能的脚本
- `requirements.txt` - 依赖库列表
- `ipv6_sender.log` - 日志文件（程序运行时自动创建）
- `boot_notification.log` - 开机通知日志文件（开机通知程序运行时自动创建）

## 使用说明

### 安装步骤

1. 确保您的系统已安装Python（建议3.6及以上版本）
2. 下载本程序所有文件到同一个文件夹
3. 修改`config.json`文件，填入您的邮箱设置及自定义路径
4. 根据需要选择安装方式：
   - 运行`setup_autostart.bat`设置IPv6地址发送功能的开机自启动
   - 或运行`setup_boot_notification.bat`设置开机通知功能的开机自启动
   - 它们会自动安装所需的依赖库
   - 创建开机启动快捷方式
   - 生成后台运行的VBS脚本
   - 检测并防止重复安装，避免多实例问题

### 配置文件说明

配置文件`config.json`包含以下设置项：

```json
{
    "smtp_server": "smtp.example.com",  // SMTP服务器地址
    "smtp_port": 465,  // SMTP服务器端口（通常是465或587）
    "smtp_encryption": "SSL",  // 加密方式: SSL, TLS, 或 None
    "sender_email": "your_email@example.com",  // 发件人邮箱
    "sender_password": "your_password",  // 发件人邮箱密码或授权码
    "receiver_email": "receiver@example.com",  // 接收者邮箱
    "check_interval": 3600,  // 检查间隔（单位：秒，默认为1小时）
    "last_sent_ipv6": "",  // 最后一次发送的IPv6地址（自动更新，无需手动修改）
    
    "paths": {  // 路径配置（所有路径均可自定义）
        "log_file": "ipv6_sender.log",  // 日志文件路径
        "config_file": "config.json",  // 配置文件路径
        "vbs_script": "start_ipv6_sender.vbs",  // VBS脚本文件名
        "python_script": "auto_send_ipv6.py",  // Python主程序文件名
        "startup_folder": "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup",  // 开机启动文件夹
        "shortcut_name": "IPv6AddressSender.lnk"  // 快捷方式文件名
    }
}
```

#### 邮件加密传输设置

程序支持三种加密传输方式：

- **SSL加密** (`"smtp_encryption": "SSL"`): 最常用的加密方式，默认选项，通常使用465端口
- **TLS加密** (`"smtp_encryption": "TLS"`): 另一种常用的加密方式，通常使用587端口
- **无加密** (`"smtp_encryption": "None"`): 不推荐使用，大多数现代邮件服务器要求加密传输

**注意**: 不同的邮件服务商支持的加密方式和端口可能不同，请根据邮件服务商的要求进行设置。一般来说，SSL加密是最广泛支持的安全传输方式。

#### 路径配置说明

路径配置提供以下功能：

- `log_file`: 日志文件的路径，可以是相对路径或绝对路径
- `config_file`: 配置文件自身的路径，通常不需要修改
- `vbs_script`: 后台运行脚本的文件名
- `python_script`: Python主程序的文件名
- `startup_folder`: Windows系统的开机启动文件夹，可以自定义
- `shortcut_name`: 在启动文件夹中创建的快捷方式名称

注意：相对路径是相对于程序所在目录的路径，绝对路径则需要指定完整的系统路径。

### 常见邮箱SMTP设置

- QQ邮箱:
  - SMTP服务器：smtp.qq.com
  - 端口：465（SSL加密）或587（TLS加密）
  - 加密方式：SSL（推荐）或TLS
  - 密码：需要在QQ邮箱设置中开启SMTP服务并获取授权码
  - 授权码获取方法：QQ邮箱 → 设置 → 账户 → POP3/SMTP服务 → 开启 → 获取授权码

- 163邮箱:
  - SMTP服务器：smtp.163.com
  - 端口：465（SSL加密）或994（SSL加密，POP3）
  - 加密方式：SSL（推荐）
  - 密码：需要在163邮箱设置中开启SMTP服务并获取授权码

- Gmail:
  - SMTP服务器：smtp.gmail.com
  - 端口：465（SSL加密）或587（TLS加密，推荐）
  - 加密方式：TLS（推荐）或SSL
  - 密码：需要在Google账户中开启"应用专用密码"

## 测试程序

为了确保程序正常工作，提供了两个测试脚本：

1. **基本测试脚本**：`test_ipv6_email.py`
   - 显示系统信息和编码设置
   - 显示当前配置的路径设置和加密方式
   - 测试IPv6地址获取功能
   - 测试邮件发送功能

2. **QQ邮箱专用测试脚本**：`test_qq_email.py`
   - 专为QQ邮箱设计的测试脚本
   - 提供详细的SMTP连接和加密过程
   - 显示完整的错误信息和堆栈跟踪

运行测试脚本前，请确保已正确配置`config.json`文件。

## 手动运行

如果您想手动运行程序而不等待开机启动，可以：

1. 直接运行Python脚本：`python auto_send_ipv6.py`
2. 或运行VBS脚本（后台运行）：双击`start_ipv6_sender.vbs`

## 自定义安装位置

如果您想将程序安装在非默认位置，可以：

1. 修改`config.json`中的`paths`部分，设置自定义路径
2. 将日志文件和其他文件放置在自定义位置
3. 如需使用自定义的启动文件夹，请修改`startup_folder`路径

## 日志文件

程序会自动生成日志文件`ipv6_sender.log`（或配置中指定的其他文件名），记录以下信息：

- 程序启动和运行状态
- IPv6地址获取方法和结果
- 邮件发送成功或失败的详细信息
- 邮件加密传输方式
- 错误和异常情况

日志文件使用UTF-8编码，可以正确显示中文字符。

## 故障排除

### 中文乱码问题

如果遇到中文乱码问题：

- 确保系统默认编码为UTF-8
- 所有脚本文件应使用UTF-8编码保存
- 批处理文件已添加`chcp 65001`命令设置控制台为UTF-8编码

### 邮件发送失败

如果邮件发送失败：

1. 运行`test_qq_email.py`脚本获取详细错误信息
2. 检查以下常见问题：
   - SMTP服务器地址或端口是否正确
   - 加密方式是否与端口号匹配（SSL通常用465端口，TLS通常用587端口）
   - 邮箱密码或授权码是否正确
   - 是否已开启SMTP服务
   - 邮箱安全设置是否允许第三方应用访问

### 路径问题

如果遇到路径相关错误：

1. 检查`config.json`中的路径配置是否正确
2. 确保所有路径都能正确访问（特别是自定义了绝对路径的情况）
3. Windows路径中的反斜杠需要使用双反斜杠`\\`表示

### 无法获取IPv6地址

如果无法获取IPv6地址：

1. 确保您的网络已启用IPv6
2. 检查路由器是否支持IPv6并已开启
3. 运行`ipconfig`命令查看是否有IPv6地址分配

## 注意事项

- 请确保您的计算机已连接到网络并分配了IPv6地址
- 强烈建议使用SSL或TLS加密方式发送邮件，保护账户安全
- 某些邮箱服务提供商可能需要特殊设置，如开启SMTP服务或生成应用专用密码
- 如需卸载，只需删除启动文件夹中的快捷方式即可停止自动启动
- 程序默认每小时检查一次IPv6地址，可在配置文件中修改检查间隔
- 修改配置文件中的路径设置后，需要重新运行`setup_autostart.bat`以应用新的路径设置
