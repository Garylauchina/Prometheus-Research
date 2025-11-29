# Prometheus v3.0 - 快速开始

## 🚀 一键部署（推荐）

如果您想快速在VPS上部署，只需运行：

```bash
# 下载并运行部署脚本
curl -sSL https://raw.githubusercontent.com/Garylauchina/prometheus-v30/main/deploy.sh | bash
```

或者克隆仓库后运行：

```bash
git clone https://github.com/Garylauchina/prometheus-v30.git
cd prometheus-v30
chmod +x deploy.sh
./deploy.sh
```

脚本会自动完成：
- ✅ 安装系统依赖
- ✅ 设置Python虚拟环境
- ✅ 配置API凭证
- ✅ 创建systemd服务
- ✅ 启动交易系统

---

## 📋 手动部署

如果您想手动控制每一步，请参考 [DEPLOY.md](DEPLOY.md) 获取详细指南。

---

## 🐳 Docker部署

### 使用Docker Compose（推荐）

1. **克隆项目**
   ```bash
   git clone https://github.com/Garylauchina/prometheus-v30.git
   cd prometheus-v30
   ```

2. **配置API凭证**
   
   创建`.env`文件：
   ```bash
   nano .env
   ```
   
   添加以下内容：
   ```ini
   OKX_API_KEY="your_api_key"
   OKX_SECRET_KEY="your_secret_key"
   OKX_PASSPHRASE="your_passphrase"
   ```

3. **启动容器**
   ```bash
   docker-compose up -d
   ```

4. **查看日志**
   ```bash
   docker-compose logs -f
   ```

### 使用纯Docker

```bash
# 构建镜像
docker build -t prometheus-v30 .

# 运行容器
docker run -d \
  --name prometheus-v30 \
  --restart always \
  -e OKX_API_KEY="your_api_key" \
  -e OKX_SECRET_KEY="your_secret_key" \
  -e OKX_PASSPHRASE="your_passphrase" \
  -v $(pwd)/trading_logs:/app/trading_logs \
  prometheus-v30
```

---

## 📊 监控系统

运行监控脚本查看系统状态：

```bash
./monitor.sh
```

输出示例：
```
============================================================
  Prometheus v3.0 - 系统监控
============================================================

[服务状态]
✅ Prometheus服务: 运行中
   启动时间: 2025-11-29 15:00:00

[系统资源]
CPU使用率: 15.2%
内存使用: 512MB/2GB
磁盘使用: 5GB/20GB (25%)

[进程信息]
进程ID: 12345
内存使用: 128 MB
CPU使用: 5.2 %

[最近日志]
...

[交易统计]
ROI: 2.08%
总交易: 0
活跃Agent: 5/5
```

---

## 🔧 常用命令

### 服务管理

```bash
# 查看状态
sudo systemctl status prometheus.service

# 启动服务
sudo systemctl start prometheus.service

# 停止服务
sudo systemctl stop prometheus.service

# 重启服务
sudo systemctl restart prometheus.service

# 查看实时日志
sudo journalctl -u prometheus.service -f
```

### Docker管理

```bash
# 查看容器状态
docker ps

# 查看日志
docker logs -f prometheus-v30

# 停止容器
docker stop prometheus-v30

# 启动容器
docker start prometheus-v30

# 重启容器
docker restart prometheus-v30
```

---

## 📝 配置说明

### 运行时长

默认运行30天（2,592,000秒）。修改方法：

**Systemd服务**:
编辑 `/etc/systemd/system/prometheus.service`，修改：
```ini
ExecStart=.../python run_virtual_trading.py --duration 86400
```
（86400秒 = 24小时）

**Docker**:
修改 `docker-compose.yml` 或 `Dockerfile` 中的 `CMD` 参数。

### 日志级别

```bash
# 修改为DEBUG模式（更详细的日志）
python run_virtual_trading.py --duration 3600 --log-level DEBUG
```

---

## ⚠️ 注意事项

1. **API凭证安全**
   - 永远不要将`.env`文件提交到Git
   - 使用环境变量或密钥管理工具
   - 定期轮换API密钥

2. **资源监控**
   - 定期检查CPU和内存使用
   - 确保有足够的磁盘空间存储日志
   - 建议设置日志轮转

3. **网络稳定性**
   - 确保VPS网络稳定
   - 考虑使用VPN或代理（如果需要）
   - 监控API调用频率，避免超限

4. **备份**
   - 定期备份配置文件
   - 保存重要的交易报告
   - 记录系统配置和参数

---

## 🆘 故障排查

### 服务无法启动

```bash
# 查看详细错误
sudo journalctl -u prometheus.service -n 50

# 检查配置文件
sudo systemctl cat prometheus.service

# 检查权限
ls -la /home/your_username/prometheus-v30
```

### API连接失败

- 检查API凭证是否正确
- 确认网络可以访问OKX
- 验证API密钥权限（需要读取+交易）

### 内存不足

- 减少Agent数量
- 增加VPS内存
- 优化代码（减少数据缓存）

---

## 📚 更多资源

- [完整部署指南](DEPLOY.md)
- [项目README](README.md)
- [GitHub仓库](https://github.com/Garylauchina/prometheus-v30)

---

**祝您交易顺利！** 🚀
