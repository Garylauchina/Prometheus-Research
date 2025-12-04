import re

with open('diversity_test_result.log', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

print("=" * 60)
print("📊 测试日志分析")
print("=" * 60)

# 统计关键指标
prophecy_count = content.count('小预言')
evolution_count = content.count('开始进化周期')
diversity_values = re.findall(r'基因多样性:\s*([\d.]+)', content)
pnl_displays = re.findall(r'系统总盈亏', content)

print(f"\n1. 小预言（周期）: {prophecy_count} 次")
print(f"2. 进化触发: {evolution_count} 次")
print(f"3. 基因多样性值: {diversity_values if diversity_values else '未触发进化，无数据'}")
print(f"4. 系统盈亏显示: {len(pnl_displays)} 次")

# 判断
print("\n" + "=" * 60)
if evolution_count > 0:
    print("✅ 进化已触发")
    if diversity_values:
        latest_div = float(diversity_values[-1])
        if latest_div > 0:
            print(f"🎉 修复成功！基因多样性 = {latest_div}")
        else:
            print(f"⚠️  基因多样性仍为 0.00")
else:
    print(f"⚠️  测试运行了{prophecy_count}个周期，但未触发进化")
    print("   （Mock模式需要30个周期或10笔平均交易）")

if len(pnl_displays) > 0:
    print(f"✅ 系统盈亏显示正常（{len(pnl_displays)}次）")
else:
    print("⚠️  系统盈亏显示功能可能未生效")

print("=" * 60)

