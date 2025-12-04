"""
运行Prometheus v4.0简化启动器
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from examples.v4_okx_simplified_launcher import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        # 避免Windows控制台编码问题
        try:
            print(f"\n\n❌ 错误: {e}")
        except UnicodeEncodeError:
            print(f"\n\n[X] 错误: {e}")
        import traceback
        traceback.print_exc()

