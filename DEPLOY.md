# Prometheus v3.0 - VPS部署指南

**版本**: 1.0  
**日期**: 2025年11月29日

---

## 📋 简介

本指南将引导您如何在Linux VPS（Virtual Private Server）上部署Prometheus v3.0交易系统，并将其作为后台服务7x24小时运行。

### 推荐系统配置

| 组件 | 最低要求 | 推荐配置 |
|---|---|---|
| 操作系统 | Ubuntu 20.04 LTS | **Ubuntu 22.04 LTS** |
| CPU | 1核 | 2核或以上 |
| 内存 | 1GB RAM | 2GB RAM或以上 |
| 存储 | 10GB SSD | 20GB SSD或以上 |
| 网络 | 10 Mbps | 100 Mbps或以上 |

---

## 🚀 部署步骤

### 步骤1：准备VPS环境

1.  **连接到您的VPS**

    通过SSH连接到您的服务器。将`your_server_ip`替换为您的VPS IP地址。

    ```bash
    ssh root@your_server_ip
    ```

2.  **更新系统**

    确保您的系统是最新的。

    ```bash
    sudo apt update && sudo apt upgrade -y
    ```

3.  **安装必要工具**

    安装Git（用于克隆代码）、Python 3.11和`venv`（用于创建虚拟环境）。

    ```bash
    sudo apt install -y git python3.11 python3.11-venv
    ```

---

### 步骤2：克隆项目代码

1.  **克隆您的私有仓库**

    从GitHub克隆`prometheus-v30`项目。由于是私有仓库，您需要使用您的GitHub用户名和Personal Access Token。

    ```bash
    git clone https://Garylauchina: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@github.com/Garylauchina/prometheus-v30.git
    ```

    *注意：将Token直接放在URL中是为了方便，但存在安全风险。更安全的方式是配置Git凭证助手。*

2.  **进入项目目录**

    ```bash
    cd prometheus-v30
    ```

---

### 步骤3：设置Python虚拟环境

使用虚拟环境可以隔离项目依赖，避免与系统其他Python包冲突。

1.  **创建虚拟环境**

    ```bash
    python3.11 -m venv venv
    ```

2.  **激活虚拟环境**

    ```bash
    source venv/bin/activate
    ```

    激活后，您的命令行提示符前会显示`(venv)`。

3.  **安装依赖**

    ```bash
    pip install -r requirements.txt
    ```

---

### 步骤4：配置API凭证

为了安全，我们将API凭证存储在环境变量中，而不是硬编码在代码里。

1.  **创建环境变量配置文件**

    创建一个名为`.env`的文件来存储您的OKX API凭证。

    ```bash
    nano .env
    ```

2.  **编辑`.env`文件**

    将以下内容复制到文件中，并替换为您的真实凭证。

    ```ini
    # OKX API Credentials
    OKX_API_KEY="your_api_key"
    OKX_SECRET_KEY="your_secret_key"
    OKX_PASSPHRASE="your_passphrase"
    ```

    按`Ctrl+X`，然后按`Y`和`Enter`保存并退出。

3.  **更新`.gitignore`**

    确保`.env`文件不会被意外上传到GitHub。我们已经将其添加到了`.gitignore`中。

    ```bash
    cat .gitignore
    # ...
    .env
    # ...
    ```

---

### 步骤5：手动运行测试

在设置为后台服务之前，先手动运行一次，确保一切正常。

1.  **加载环境变量**

    ```bash
    source .env
    ```

2.  **运行10分钟测试**

    ```bash
    python run_virtual_trading.py --duration 600
    ```

3.  **观察输出**

    您应该能看到系统正常启动，并开始每分钟迭代。如果没有错误，按`Ctrl+C`停止测试。

---

## ⚙️ 设置为后台服务 (Systemd)

为了让交易系统在您关闭SSH连接后依然能7x24小时运行，并能自动重启，我们将其配置为一个`systemd`服务。

### 步骤1：创建服务文件

1.  **创建`prometheus.service`文件**

    ```bash
    sudo nano /etc/systemd/system/prometheus.service
    ```

2.  **编辑服务文件**

    将以下内容复制到文件中。**请确保将`User`和`WorkingDirectory`中的`your_username`替换为您的VPS用户名（例如`root`）**。

    ```ini
    [Unit]
    Description=Prometheus v3.0 Trading Bot
    After=network.target
    
    [Service]
    User=your_username
    Group=your_username
    
    WorkingDirectory=/home/your_username/prometheus-v30
    ExecStart=/home/your_username/prometheus-v30/venv/bin/python run_virtual_trading.py --duration 2592000
    
    # Environment File for API Keys
    EnvironmentFile=/home/your_username/prometheus-v30/.env
    
    # Auto-restart configuration
    Restart=always
    RestartSec=10
    
    # Logging
    StandardOutput=journal
    StandardError=journal
    SyslogIdentifier=prometheus-v30
    
    [Install]
    WantedBy=multi-user.target
    ```

    **配置说明**:
    - `Description`: 服务的描述。
    - `User`/`Group`: 运行服务的用户和组。
    - `WorkingDirectory`: 项目的根目录。
    - `ExecStart`: 启动服务的命令。这里我们设置为运行30天（2,592,000秒）。
    - `EnvironmentFile`: 加载包含API密钥的`.env`文件。
    - `Restart=always`: 如果服务意外退出，总是自动重启。
    - `RestartSec=10`: 重启前等待10秒。
    - `StandardOutput`/`StandardError`: 将日志输出到`journald`。

---

### 步骤2：管理服务

1.  **重新加载`systemd`配置**

    ```bash
    sudo systemctl daemon-reload
    ```

2.  **启动Prometheus服务**

    ```bash
    sudo systemctl start prometheus.service
    ```

3.  **设置开机自启**

    ```bash
    sudo systemctl enable prometheus.service
    ```

4.  **检查服务状态**

    ```bash
    sudo systemctl status prometheus.service
    ```

    如果一切正常，您应该会看到`active (running)`的状态。

---

### 步骤3：查看日志

使用`journalctl`命令可以查看您的交易机器人日志。

1.  **实时查看日志**

    ```bash
    sudo journalctl -u prometheus.service -f
    ```

2.  **查看最近100行日志**

    ```bash
    sudo journalctl -u prometheus.service -n 100
    ```

---

## 🔄 更新项目

当您在本地更新了代码并推送到GitHub后，可以按照以下步骤在VPS上更新。

1.  **停止服务**

    ```bash
    sudo systemctl stop prometheus.service
    ```

2.  **拉取最新代码**

    ```bash
    cd /home/your_username/prometheus-v30
    git pull origin main
    ```

3.  **更新依赖（如果需要）**

    ```bash
    source venv/bin/activate
    pip install -r requirements.txt
    ```

4.  **重启服务**

    ```bash
    sudo systemctl start prometheus.service
    ```

---

## 自动化部署

为了简化部署和更新流程，我们提供了一个自动化脚本`deploy.sh`。您只需运行一个命令即可完成所有操作。

**请查看 `deploy.sh` 文件获取详细用法。**

---

**部署完成！** 您的Prometheus v3.0交易系统现在已经在VPS上7x24小时运行。🚀
