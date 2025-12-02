# OKX API 配置修复指南

## 问题：API密钥与环境不匹配

### 修复步骤

1. **获取正确的模拟盘API**
   - 访问：https://www.okx.com/trade-demo
   - 进入模拟盘交易界面
   - 右上角"资产" → "API管理" → "创建模拟盘V5 API"

2. **更新配置文件**
   
   打开 `config/okx_config.py`（或 `config/okx_config.example.py`）
   
   将API信息替换为新的模拟盘API：
   ```python
   OKX_PAPER_TRADING = {
       'api_key': '新的模拟盘API-Key',
       'api_secret': '新的模拟盘Secret-Key',
       'passphrase': '新的模拟盘Passphrase',
   }
   ```

3. **验证API类型**
   
   模拟盘API特征：
   - ✅ 在"模拟盘交易"页面创建
   - ✅ API管理页面显示"模拟盘API"
   - ✅ 默认账户余额：10,000 USDT
   
   实盘API特征：
   - ❌ 在主账户"API管理"创建
   - ❌ 显示真实资产
   - ❌ 需要绑定手机/邮箱验证

4. **重新测试**
   ```bash
   python run_okx_paper_test.py
   ```
   
   成功标志：
   ```
   ✅ OKX模拟盘连接成功
      模拟账户余额: 10000.00 USDT  ← 应该看到这个
   ```

## 常见问题

**Q: 我已经用的是模拟盘API，为什么还报错？**
A: 可能原因：
   1. API Key复制错误（有多余空格）
   2. Passphrase输入错误
   3. API权限未勾选"交易"
   4. API刚创建，需要等待1-2分钟生效

**Q: 模拟盘API在哪里找？**
A: 
   1. 登录OKX
   2. 点击顶部"交易"
   3. 选择"模拟盘交易"（不是"现货交易"）
   4. 进入后右上角"资产"图标
   5. 点击"API"或"API管理"

**Q: 可以用实盘API测试吗？**
A: 不建议！
   - 实盘API连接真实账户
   - 可能产生真实交易和损失
   - 建议只用模拟盘测试

## 下一步

配置好后，重新运行测试：
```bash
python run_okx_paper_test.py
```

如果还有问题，请检查：
1. API是否在"模拟盘交易"下创建
2. API权限是否包含"交易"
3. 配置文件是否保存正确

