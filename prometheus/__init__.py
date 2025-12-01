"""
Prometheus v3.0 - AI驱动加密货币交易系统

基于遗传算法和多Agent进化的自动化交易系统

Author: Prometheus Team
Version: 3.0
License: MIT
"""

__version__ = "3.1.0"
__author__ = "Prometheus Team"
__license__ = "MIT"

# 版本信息
VERSION_INFO = {
    'major': 3,
    'minor': 1,
    'patch': 0,
    'release': 'stable'
}

def get_version():
    """返回版本字符串"""
    return f"{VERSION_INFO['major']}.{VERSION_INFO['minor']}.{VERSION_INFO['patch']}"

# 主要模块导出
from prometheus.core import *
from prometheus.strategies import *

__all__ = [
    '__version__',
    'get_version',
]

