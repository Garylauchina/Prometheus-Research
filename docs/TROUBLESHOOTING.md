# Prometheus v3.0 - 故障排查与踩坑记录

**版本**: 1.0  
**日期**: 2025年11月29日  
**Docker支持**: ✅ 已完全支持Docker部署

---

## 目录

1. [故障排查哲学：像侦探一样思考](#1-故障排查哲学像侦探一样思考)
2. [故障排查流程](#2-故障排查流程)
3. [常见问题与解决方案 (FAQ)](#3-常见问题与解决方案-faq)
   - [基本系统问题](#31-基本系统问题)
   - [API连接问题](#32-api连接问题)
   - [交易执行问题](#33-交易执行问题)
   - [Docker部署问题](#34-docker部署问题)
   - [数据与存储问题](#35-数据与存储问题)
4. [日志分析指南](#4-日志分析指南)
5. [踩坑记录 (Lessons Learned)](#5-踩坑记录-lessons-learned)
6. [如何记录新的问题](#6-如何记录新的问题)

---

## 1. 故障排查哲学：像侦探一样思考

> "当排除了所有不可能，剩下的无论多么不合情理，也必然是真相。" - 夏洛克·福尔摩斯

排查问题时，遵循以下原则：

1.  **查看日志**: 日志是第一现场，90%的线索都在里面。
2.  **隔离问题**: 尝试复现问题，缩小范围。是代码问题还是环境问题？是策略问题还是API问题？
3.  **大胆假设，小心求证**: 提出可能性，然后用实验去验证。
4.  **记录一切**: 记录问题现象、排查过程和解决方案，形成知识库。
5.  **从简单到复杂**: 先检查基础配置和环境，再深入复杂的策略逻辑。
6.  **善用备份**: 关键操作前创建配置备份，以便快速恢复。

---

## 2. 故障排查流程

### 2.1 紧急故障处理步骤

1. **检查系统状态**
   - 服务是否运行: `sudo systemctl status prometheus.service` (系统服务)
   - 或: `docker ps | grep prometheus` (Docker部署)

2. **检查日志**
   - 系统服务: `sudo journalctl -u prometheus.service -n 100`
   - 或: `docker logs <container_id>` (Docker部署)
   - 交易日志: `tail -n 100 trading_logs/latest.log`

3. **检查API连接**
   - 尝试简单的API调用: `curl -v https://www.okx.com/api/v5/public/time`

4. **检查资金状态**
   - 登录OKX交易所，确认账户资金和持仓状态

5. **必要时重启服务**
   - 系统服务: `sudo systemctl restart prometheus.service`
   - 或: `docker restart <container_id>` (Docker部署)

### 2.2 故障分类与优先级

| 故障类型 | 优先级 | 可能原因 |
|---------|-------|----------|
| 系统无法启动 | 高 | 依赖缺失、配置错误、端口冲突 |
| API连接失败 | 高 | 网络问题、API密钥错误、交易所维护 |
| 交易执行失败 | 高 | 资金不足、交易规则限制、API权限问题 |
| 策略表现异常 | 中 | 参数设置不当、市场环境变化、数据异常 |
| 性能问题 | 中 | 内存泄漏、资源不足、代码效率低 |
| 日志/监控问题 | 低 | 权限问题、磁盘空间不足 |

---

## 3. 常见问题与解决方案 (FAQ)

### 3.1 基本系统问题

### Q1: 系统无法启动，提示 `ModuleNotFoundError`

-   **现象**: `ModuleNotFoundError: No module named 'okx'`
-   **原因**: Python依赖未安装或虚拟环境未激活。
-   **解决方案**:
    - **系统服务部署**:
      1.  确保已激活虚拟环境: `source venv/bin/activate`
      2.  安装依赖: `pip install -r requirements.txt`
    - **Docker部署**:
      1.  检查镜像是否正确构建: `docker images | grep prometheus`
      2.  重新构建镜像: `docker-compose build`

### 3.2 API连接问题

### Q2: API调用失败，提示 `Invalid API Key` 或 `Authentication error`

-   **现象**: 日志中出现大量API认证错误。
-   **原因**: API凭证配置错误。
-   **解决方案**:
    1.  检查`.env`文件中的`OKX_API_KEY`, `OKX_SECRET_KEY`, `OKX_PASSPHRASE`是否正确。
    2.  确认API密钥是否已过期或被禁用。
    3.  确认API权限是否包含"读取"和"交易"。
    4.  检查IP白名单设置是否正确。
    5.  **Docker部署额外检查**: 确认环境变量是否正确传递到容器中: `docker exec -it <container_id> env | grep OKX`

### Q3: 服务在后台运行一段时间后自动停止

-   **现象**: 服务状态显示为非活动状态。
-   **原因**: 
    1.  **内存不足 (OOM Killer)**: 系统内存耗尽，内核杀死了最耗内存的进程。
    2.  **代码中的致命错误**: 未被捕获的异常导致程序崩溃。
    3.  **网络长时间中断**: 导致API调用连续失败，程序退出。
-   **解决方案**:
    - **系统服务部署**:
      1.  查看系统日志: `sudo journalctl -u prometheus.service -n 100`，查找错误信息。
      2.  检查内存使用: `free -h`，考虑升级VPS内存或优化代码。
      3.  检查`Restart=always`是否已在`.service`文件中配置。
    - **Docker部署**:
      1.  查看容器日志: `docker logs <container_id>`
      2.  检查容器重启策略: `docker inspect <container_id> | grep RestartPolicy`
      3.  调整docker-compose.yml中的restart策略为`always`

### Q9: 如何重置系统并清除所有数据？

-   **现象**: 想从一个全新的状态开始测试。
-   **解决方案**:
    - **系统服务部署**:
        1.  停止服务: `sudo systemctl stop prometheus.service`
        2.  删除日志: `rm -rf trading_logs/*`
        3.  在OKX模拟盘手动平仓并划转所有资金。
        4.  重启服务: `sudo systemctl start prometheus.service`
    - **Docker部署**:
        1.  停止并移除容器: `docker-compose down`
        2.  删除挂载卷数据: `rm -rf trading_logs/*`
        3.  在OKX模拟盘手动平仓并划转所有资金。
        4.  重启服务: `docker-compose up -d`

### Q5: 如何重置系统并清除所有数据？

-   **现象**: 想从一个全新的状态开始测试。
-   **解决方案**:
    1.  停止服务: `sudo systemctl stop prometheus.service`
    2.  删除日志: `rm -rf trading_logs/*`
    3.  在OKX模拟盘手动平仓并划转所有资金。
    4.  重启服务: `sudo systemctl start prometheus.service`

---

## 4. 日志分析指南

### 4.1 日志级别说明

- **DEBUG**: 详细的调试信息，包括API请求和响应
- **INFO**: 一般操作信息，如策略决策、交易执行
- **WARNING**: 需要注意的问题，但不影响系统运行
- **ERROR**: 错误信息，可能导致部分功能失效
- **CRITICAL**: 严重错误，需要立即处理

### 4.2 关键日志模式

| 日志模式 | 说明 | 处理建议 |
|---------|------|----------|
| `APIError` | API调用失败 | 检查API凭证和网络连接 |
| `Order failed` | 下单失败 | 检查资金、价格和交易规则 |
| `ConnectionError` | 网络连接错误 | 检查网络连接和代理设置 |
| `TimeoutError` | 请求超时 | 考虑增加超时设置或检查网络 |
| `Insufficient balance` | 资金不足 | 增加资金或调整交易规模 |

### 4.3 日志分析工具

```bash
# 查找所有错误
grep -i "error" trading_logs/latest.log

# 查找特定时间段的日志
grep "2025-11-29 14:" trading_logs/latest.log

# 统计API错误次数
grep -c "APIError" trading_logs/latest.log

# 实时监控新日志
tail -f trading_logs/latest.log | grep -i "trade\|order"
```

---

## 5. 踩坑记录 (Lessons Learned)

### 5.1 OKX API的中文Passphrase编码问题

-   **问题**: 在v3.0初次测试中，使用了中文作为Passphrase，导致API签名验证失败，错误为 `UnicodeEncodeError: 'ascii' codec can't encode characters`。
-   **原因**: OKX Python SDK在进行HMAC-SHA256签名时，未正确处理非ASCII字符，默认使用了ASCII编码。
-   **解决方案**: **永远不要使用中文或特殊字符作为API Passphrase**。必须使用纯英文和数字。
-   **教训**: 
    -   不要想当然地认为所有系统都支持UTF-8。
    -   对于涉及加密和签名的部分，务必使用最简单、最通用的字符集。
    -   在Docker环境中更要注意编码问题，确保容器内外编码一致。

### 5.2 仓位模式不匹配导致的平仓失败

-   **问题**: 在v3.0测试中，尝试平仓时API返回错误，提示"没有该方向的持仓"。
-   **原因**: OKX合约账户有**开平仓模式**和**买卖模式**。如果API调用中的`posSide`参数与账户设置不匹配，将无法正确执行订单。
-   **解决方案**: 
    1.  在API调用中明确指定`posSide` (`long`或`short`)。
    2.  确保账户的持仓模式与代码逻辑一致。
    3.  添加仓位检查逻辑，在下单前验证当前持仓状态。
-   **教训**: 
    -   在与交易所API交互时，必须仔细阅读其文档，特别是关于账户设置和交易模式的部分。
    -   不要忽略API返回的每一个错误信息，它们是排查问题的关键线索。

### 5.3 遗传算法在震荡市中的"过度拟合"

-   **问题**: 在v1.0的回测中，发现某些在牛市中表现极好的Agent，在震荡市中亏损严重。
-   **原因**: 这些Agent的基因"过度拟合"了牛市的趋势行情，它们的交易阈值非常低，导致在震荡市中被反复"打脸"。
-   **解决方案**: 引入**市场状态检测**机制（v2.5），在震荡市中"抑制"这些激进的Agent，降低它们的交易频率和资金分配。
-   **教训**: 
    -   **没有一种策略能适应所有市场**。系统的适应性比单个策略的优越性更重要。
    -   必须有机制来识别和应对不同的市场环境。
    -   在实盘部署前，务必在多种市场条件下进行充分的回测。

### 5.4 初始Agent多样性不足

-   **问题**: 如果初始Agent的基因过于相似，遗传算法可能过早地收敛到一个局部最优解，而错过了全局最优解。
-   **原因**: 随机数生成器的种子问题或基因初始化范围太窄。
-   **解决方案**: 
    1.  确保基因参数的初始化范围足够宽。
    2.  引入一定的"突变"概率，即使在没有繁殖的情况下，Agent的基因也有小概率发生随机变化。
    3.  定期引入新的随机Agent，保持种群活力。
-   **教训**: 
    -   **多样性是进化的前提**。必须在系统的整个生命周期中保持种群的多样性。
    -   在利用（exploitation）已知优势策略和探索（exploration）未知可能性之间取得平衡。

### 5.5 Docker环境中的时区问题

-   **问题**: 在Docker部署中，发现交易时间记录与实际时间不符，导致市场状态判断错误。
-   **原因**: Docker容器默认使用UTC时间，而不是本地时区。
-   **解决方案**: 
    1.  在docker-compose.yml中挂载主机时区文件:
    ```yaml
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - /etc/timezone:/etc/timezone:ro
    ```
    2.  或在Dockerfile中设置时区:
    ```dockerfile
    RUN ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && dpkg-reconfigure -f noninteractive tzdata
    ```
-   **教训**: 
    -   时间同步在交易系统中至关重要，任何时间偏差都可能导致严重后果。
    -   Docker部署需要特别注意时区配置，确保与交易策略的时间预期一致。

---

## 6. 如何记录新的问题

当您遇到新的问题时，请按照以下格式记录到本文件中，以便未来参考：

```markdown
### [问题标题]

-   **问题**: [问题的简要描述]
-   **原因**: [经过排查后发现的根本原因]
-   **解决方案**: [解决问题的具体步骤]
-   **教训**: [从这次经历中学到的经验或教训]
-   **适用环境**: [系统服务部署/Docker部署/两者适用]
```

*本文档由AI生成并由人工优化*  
*最后更新: 2025-11-29*
