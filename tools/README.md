# OKX数据下载工具

用于下载OKX历史K线数据到本地，方便后续开发测试。

---

## 🚀 快速开始

### 1. 下载BTC-USDT数据（推荐配置）

```powershell
cd tools
python download_okx_data.py --symbol BTC-USDT --period 1h --years 3
```

**预计**：
- 数据量：~26,000条（3年 × 365天 × 24小时）
- 下载时间：~2分钟
- 文件大小：~2MB

---

### 2. 批量下载多个配置

```powershell
python batch_download.py
```

**将下载**：
1. BTC-USDT 1小时K线（3年）
2. BTC-USDT 4小时K线（5年）
3. BTC-USDT 日线（10年）
4. ETH-USDT 1小时K线（3年）
5. ETH-USDT 日线（5年）

**预计**：
- 总数据量：~50,000条
- 下载时间：~5分钟
- 文件大小：~5MB

---

### 3. 加载和分析数据

```powershell
python load_and_analyze.py
```

**输出**：
- 📊 市场条件分析（波动率、价格范围、成交量）
- 🌪️ 极端波动时期（Top 10）
- 💡 推荐模型参数（SlippageModel、MarketCondition）

---

## 📖 详细使用

### 下载单个数据集

```powershell
# 基本用法
python download_okx_data.py --symbol BTC-USDT --period 1h --years 3

# 下载不同周期
python download_okx_data.py --symbol BTC-USDT --period 15m --years 1   # 15分钟
python download_okx_data.py --symbol BTC-USDT --period 4h --years 5    # 4小时
python download_okx_data.py --symbol BTC-USDT --period 1d --years 10   # 日线

# 下载不同币种
python download_okx_data.py --symbol ETH-USDT --period 1h --years 3
python download_okx_data.py --symbol SOL-USDT --period 1h --years 2

# 强制重新下载
python download_okx_data.py --symbol BTC-USDT --period 1h --years 3 --force

# 自定义保存目录
python download_okx_data.py --symbol BTC-USDT --period 1h --years 3 --data-dir D:/MyData
```

### 参数说明

| 参数 | 说明 | 默认值 | 可选值 |
|------|------|--------|--------|
| `--symbol` | 交易对 | BTC-USDT | BTC-USDT, ETH-USDT等 |
| `--period` | 时间周期 | 1h | 1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1w |
| `--years` | 下载年数 | 3 | 1-10 |
| `--data-dir` | 保存目录 | ../data/okx | 任意路径 |
| `--force` | 强制重新下载 | False | 无需值 |

---

## 📂 数据格式

### CSV格式
```csv
timestamp,open,high,low,close,volume,volume_quote
2024-01-01 00:00:00,42000.0,42100.0,41900.0,42050.0,123.45,5187225.0
2024-01-01 01:00:00,42050.0,42200.0,42000.0,42150.0,156.78,6601437.0
...
```

### Parquet格式
- 压缩存储，文件更小（约CSV的1/3）
- 读取速度更快（约CSV的10倍）
- 保留数据类型（无需转换）

### 元数据（JSON）
```json
{
  "symbol": "BTC_USDT",
  "period": "1h",
  "start_time": "2021-12-04T00:00:00",
  "end_time": "2024-12-04T23:00:00",
  "num_candles": 26280,
  "price_range": {
    "min": 15500.0,
    "max": 69000.0
  },
  "download_time": "2024-12-04T15:30:00"
}
```

---

## 💻 在代码中使用

### 1. 加载数据

```python
import pandas as pd

# 方法1：使用工具函数
from tools.load_and_analyze import load_data

df = load_data(symbol="BTC-USDT", period="1h", years=3)

# 方法2：直接读取
df = pd.read_parquet("../data/okx/BTC_USDT_1h_3y.parquet")
```

### 2. 用于回测

```python
# 加载数据
df = load_data("BTC-USDT", "1h", 3)

# 遍历每个时间点
for i in range(100, len(df)):
    # 获取历史数据（前100个K线）
    historical = df.iloc[i-100:i]
    current = df.iloc[i]
    
    # 使用Agent进行决策
    decision = agent.daimon.guide({
        'market_data': historical,
        'current_price': current['close'],
        ...
    })
    
    # 模拟执行
    ...
```

### 3. 计算真实市场参数

```python
from prometheus.core.slippage_model import MarketCondition

# 加载数据
df = load_data("BTC-USDT", "1h", 3)

# 计算波动率
volatility = df['close'].pct_change().std()

# 估算流动性深度（使用成交量中位数）
liquidity_depth = df['volume_quote'].median()

# 创建市场条件
market_condition = MarketCondition(
    liquidity_depth=liquidity_depth,
    bid_ask_spread=volatility * 0.1,  # 估算
    volatility=volatility
)

# 使用真实参数计算滑点
from prometheus.core.slippage_model import SlippageModel
slippage_model = SlippageModel()

result = slippage_model.calculate_slippage(
    order_side=OrderSide.BUY,
    order_size_usd=10000,
    order_type=OrderType.MARKET,
    market_condition=market_condition
)
```

---

## 📊 推荐下载配置

### 开发测试（最小集）
```powershell
# 只下载BTC 1小时数据（3年）
python download_okx_data.py --symbol BTC-USDT --period 1h --years 3
```

**数据量**：~26,000条  
**文件大小**：~2MB  
**适用场景**：快速测试、日常开发

---

### 完整回测（推荐）
```powershell
# 批量下载
python batch_download.py
```

**数据量**：~50,000条  
**文件大小**：~5MB  
**适用场景**：完整回测、生产环境

---

### 高频测试（可选）
```powershell
# 下载1分钟K线
python download_okx_data.py --symbol BTC-USDT --period 1m --years 1
```

**数据量**：~525,600条（1年）  
**文件大小**：~50MB  
**适用场景**：高频策略测试、微结构研究

⚠️ **注意**：1分钟数据量大，下载时间长（约30分钟）

---

## 🔧 高级用法

### 自定义时间范围

修改 `download_okx_data.py` 中的代码：

```python
# 下载特定时间段
start_time = datetime(2024, 1, 1)  # 2024年1月1日
end_time = datetime(2024, 12, 4)   # 2024年12月4日

# 修改download_historical_data方法中的时间计算
```

### 下载多个币种

创建自己的批量下载脚本：

```python
symbols = ['BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'BNB-USDT']

for symbol in symbols:
    downloader.download_historical_data(
        symbol=symbol,
        period='1h',
        years=3
    )
```

---

## ⚠️ 注意事项

### 1. API限制
- OKX API限制：20次/2秒
- 脚本已内置延迟（0.2秒/请求）
- 大量下载可能触发限制（建议分批）

### 2. 数据完整性
- OKX最早数据：约2017年（BTC）
- 下载10年可能只能获得7-8年数据
- 脚本会自动处理缺失时期

### 3. 存储空间
| 配置 | 数据量 | 空间 |
|------|--------|------|
| 1h × 3年 | ~26K | 2MB |
| 1h × 10年 | ~87K | 7MB |
| 1m × 1年 | ~525K | 50MB |
| 1m × 3年 | ~1.5M | 150MB |

### 4. 网络问题
- 如果下载中断，脚本会保存已下载的数据
- 重新运行会自动跳过已存在的文件
- 使用 `--force` 强制重新下载

---

## 🐛 常见问题

### Q1: 下载失败怎么办？
```powershell
# 检查网络连接
ping www.okx.com

# 重试下载
python download_okx_data.py --symbol BTC-USDT --period 1h --years 3
```

### Q2: 如何更新最新数据？
```powershell
# 重新下载（会覆盖旧文件）
python download_okx_data.py --symbol BTC-USDT --period 1h --years 3 --force
```

### Q3: 数据保存在哪里？
```
prometheus-v30/
├── data/
│   └── okx/
│       ├── BTC_USDT_1h_3y.csv
│       ├── BTC_USDT_1h_3y.parquet
│       ├── BTC_USDT_1h_3y.json
│       └── ...
└── tools/
    └── download_okx_data.py
```

### Q4: 如何验证数据正确性？
```powershell
python load_and_analyze.py
```
会显示数据统计和市场分析。

---

## 📚 相关文档

- `download_okx_data.py` - 单文件下载工具
- `batch_download.py` - 批量下载脚本
- `load_and_analyze.py` - 数据加载和分析示例
- `../docs/V5.1_UPGRADE_GUIDE.md` - v5.1升级指南

---

## 🙏 贡献

如果需要添加其他交易所的数据下载工具：
1. 复制 `download_okx_data.py`
2. 修改API端点和参数格式
3. 保持相同的数据格式输出

---

**Happy Trading!** 🚀

