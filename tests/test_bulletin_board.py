"""
测试公告板系统v4
"""

import unittest
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from prometheus.core.bulletin_board_v4 import (
    BulletinBoardV4,
    Bulletin,
    BulletinTier,
    Priority,
    BulletinBoardPermissions
)


class TestBulletinBoardPermissions(unittest.TestCase):
    """权限系统测试"""
    
    def test_mastermind_can_post_strategic(self):
        """测试Mastermind可以发布战略公告"""
        can_post = BulletinBoardPermissions.can_publish('Mastermind', BulletinTier.STRATEGIC)
        self.assertTrue(can_post)
        print("\n✅ Mastermind可以发布战略公告")
    
    def test_mastermind_cannot_post_market(self):
        """测试Mastermind不能发布市场公告"""
        can_post = BulletinBoardPermissions.can_publish('Mastermind', BulletinTier.MARKET)
        self.assertFalse(can_post)
        print("\n✅ Mastermind不能发布市场公告（权限控制正确）")
    
    def test_supervisor_can_post_market(self):
        """测试Supervisor可以发布市场公告"""
        can_post = BulletinBoardPermissions.can_publish('Supervisor', BulletinTier.MARKET)
        self.assertTrue(can_post)
        print("\n✅ Supervisor可以发布市场公告")
    
    def test_supervisor_can_post_system(self):
        """测试Supervisor可以发布系统公告"""
        can_post = BulletinBoardPermissions.can_publish('Supervisor', BulletinTier.SYSTEM)
        self.assertTrue(can_post)
        print("\n✅ Supervisor可以发布系统公告")
    
    def test_supervisor_cannot_post_strategic(self):
        """测试Supervisor不能发布战略公告"""
        can_post = BulletinBoardPermissions.can_publish('Supervisor', BulletinTier.STRATEGIC)
        self.assertFalse(can_post)
        print("\n✅ Supervisor不能发布战略公告（权限控制正确）")
    
    def test_agent_cannot_post(self):
        """测试Agent不能发布任何公告"""
        for tier in BulletinTier:
            can_post = BulletinBoardPermissions.can_publish('Agent001', tier)
            self.assertFalse(can_post)
        print("\n✅ Agent不能发布任何公告（权限控制正确）")


class TestBulletinBoardV4(unittest.TestCase):
    """公告板v4测试"""
    
    def setUp(self):
        """初始化"""
        self.board = BulletinBoardV4(max_bulletins_per_tier=10)
    
    def test_post_strategic_bulletin(self):
        """测试发布战略公告"""
        bulletin = self.board.post(
            tier='strategic',
            title='全局策略调整',
            content={'strategy': 'conservative'},
            publisher='Mastermind',
            priority='high'
        )
        
        self.assertIsNotNone(bulletin)
        self.assertEqual(bulletin.tier, BulletinTier.STRATEGIC)
        self.assertEqual(bulletin.publisher, 'Mastermind')
        
        print(f"\n✅ 战略公告发布成功: {bulletin.bulletin_id}")
    
    def test_post_market_bulletin(self):
        """测试发布市场公告"""
        bulletin = self.board.post(
            tier='market',
            title='市场技术指标',
            content={'RSI': 75, 'ADX': 35},
            publisher='Supervisor',
            priority='normal'
        )
        
        self.assertIsNotNone(bulletin)
        self.assertEqual(bulletin.tier, BulletinTier.MARKET)
        
        print(f"\n✅ 市场公告发布成功: {bulletin.bulletin_id}")
    
    def test_post_system_bulletin(self):
        """测试发布系统公告"""
        bulletin = self.board.post(
            tier='system',
            title='环境压力报告',
            content={'pressure': 0.65},
            publisher='Supervisor',
            priority='high'
        )
        
        self.assertIsNotNone(bulletin)
        self.assertEqual(bulletin.tier, BulletinTier.SYSTEM)
        
        print(f"\n✅ 系统公告发布成功: {bulletin.bulletin_id}")
    
    def test_agent_post_rejected(self):
        """测试Agent发布被拒绝"""
        bulletin = self.board.post(
            tier='market',
            title='Agent信号',
            content={'signal': 'buy'},
            publisher='Agent001',
            priority='normal'
        )
        
        self.assertIsNone(bulletin)
        print("\n✅ Agent发布被正确拒绝")
    
    def test_read_bulletins(self):
        """测试读取公告"""
        # 发布几条公告
        self.board.post('strategic', '战略1', {}, 'Mastermind')
        self.board.post('market', '市场1', {}, 'Supervisor')
        self.board.post('system', '系统1', {}, 'Supervisor')
        
        # Agent读取
        bulletins = self.board.read('Agent001', limit=5)
        
        self.assertGreater(len(bulletins), 0)
        self.assertLessEqual(len(bulletins), 5)
        
        print(f"\n✅ 读取公告成功: {len(bulletins)}条")
    
    def test_read_specific_tier(self):
        """测试读取特定层级"""
        # 发布不同层级公告
        self.board.post('strategic', '战略1', {}, 'Mastermind')
        self.board.post('market', '市场1', {}, 'Supervisor')
        self.board.post('market', '市场2', {}, 'Supervisor')
        
        # 只读市场层
        bulletins = self.board.read('Agent001', tier='market', limit=10)
        
        for b in bulletins:
            self.assertEqual(b.tier, BulletinTier.MARKET)
        
        print(f"\n✅ 读取特定层级成功: {len(bulletins)}条市场公告")
    
    def test_bulletin_expiration(self):
        """测试公告过期"""
        # 发布一个短期公告
        bulletin = self.board.post(
            tier='market',
            title='短期公告',
            content={},
            publisher='Supervisor',
            expires_hours=0  # 立即过期
        )
        
        # 手动设置过期时间
        bulletin.expires = datetime.now() - timedelta(hours=1)
        
        self.assertTrue(bulletin.is_expired())
        print("\n✅ 公告过期检测正常")
    
    def test_cleanup_expired(self):
        """测试清理过期公告"""
        # 发布公告
        b1 = self.board.post('market', '公告1', {}, 'Supervisor')
        b2 = self.board.post('market', '公告2', {}, 'Supervisor')
        
        # 设置一个过期
        b1.expires = datetime.now() - timedelta(hours=1)
        
        # 清理
        removed = self.board.cleanup_expired()
        
        self.assertGreater(removed, 0)
        print(f"\n✅ 清理过期公告: {removed}条")
    
    def test_bulletin_statistics(self):
        """测试统计信息"""
        # 发布公告
        self.board.post('strategic', '战略1', {}, 'Mastermind')
        self.board.post('market', '市场1', {}, 'Supervisor')
        self.board.post('system', '系统1', {}, 'Supervisor')
        
        # 读取（增加阅读数）
        self.board.read('Agent001', limit=5)
        self.board.read('Agent002', limit=5)
        
        # 获取统计
        stats = self.board.get_statistics()
        
        self.assertEqual(stats['total_posts'], 3)
        self.assertGreater(stats['total_views'], 0)
        
        print("\n✅ 统计信息:")
        print(f"   总发布: {stats['total_posts']}")
        print(f"   总阅读: {stats['total_views']}")
    
    def test_max_bulletins_limit(self):
        """测试公告数量限制"""
        board = BulletinBoardV4(max_bulletins_per_tier=3)
        
        # 发布超过限制的公告
        for i in range(5):
            board.post('market', f'公告{i}', {}, 'Supervisor')
        
        # 应该只保留最新的3条
        bulletins = board.get_latest('market', count=10)
        self.assertLessEqual(len(bulletins), 3)
        
        print(f"\n✅ 公告数量限制正常: {len(bulletins)}条（最大3条）")
    
    def test_get_by_priority(self):
        """测试按优先级获取"""
        self.board.post('market', '普通1', {}, 'Supervisor', priority='normal')
        self.board.post('market', '紧急1', {}, 'Supervisor', priority='urgent')
        self.board.post('market', '高优先级1', {}, 'Supervisor', priority='high')
        
        urgent = self.board.get_by_priority('urgent')
        
        self.assertGreater(len(urgent), 0)
        for b in urgent:
            self.assertEqual(b.priority, Priority.URGENT)
        
        print(f"\n✅ 按优先级获取成功: {len(urgent)}条紧急公告")


class TestBulletinWorkflow(unittest.TestCase):
    """完整工作流程测试"""
    
    def test_complete_workflow(self):
        """测试完整工作流程"""
        print(f"\n{'='*60}")
        print("完整工作流程测试")
        print(f"{'='*60}")
        
        board = BulletinBoardV4()
        
        # 1. Mastermind发布战略公告
        print("\n1. Mastermind发布战略公告")
        b1 = board.post(
            tier='strategic',
            title='全局策略：保守模式',
            content={
                'max_leverage': 2,
                'max_position': 0.3,
                'reason': '市场波动加剧'
            },
            publisher='Mastermind',
            priority='high'
        )
        self.assertIsNotNone(b1)
        print(f"   ✅ 发布成功: {b1.bulletin_id}")
        
        # 2. Supervisor发布市场公告
        print("\n2. Supervisor发布市场公告")
        b2 = board.post(
            tier='market',
            title='市场技术指标',
            content={
                'RSI': 75,
                'ADX': 35,
                'trend': '强上升'
            },
            publisher='Supervisor',
            priority='normal'
        )
        self.assertIsNotNone(b2)
        print(f"   ✅ 发布成功: {b2.bulletin_id}")
        
        # 3. Supervisor发布系统公告
        print("\n3. Supervisor发布系统公告")
        b3 = board.post(
            tier='system',
            title='环境压力报告',
            content={
                'pressure': 0.65,
                'level': '高压力'
            },
            publisher='Supervisor',
            priority='high'
        )
        self.assertIsNotNone(b3)
        print(f"   ✅ 发布成功: {b3.bulletin_id}")
        
        # 4. Agent读取公告
        print("\n4. Agent读取公告")
        bulletins = board.read('Agent001', limit=10)
        self.assertEqual(len(bulletins), 3)
        
        print(f"   ✅ Agent001读取到{len(bulletins)}条公告:")
        for b in bulletins:
            print(f"      [{b.tier.value}] {b.title} ({b.priority.value})")
        
        # 5. 验证阅读优先级（战略 > 系统 > 市场）
        print("\n5. 验证阅读优先级")
        self.assertEqual(bulletins[0].tier, BulletinTier.STRATEGIC)
        self.assertEqual(bulletins[1].tier, BulletinTier.SYSTEM)
        self.assertEqual(bulletins[2].tier, BulletinTier.MARKET)
        print("   ✅ 优先级正确: 战略 > 系统 > 市场")
        
        # 6. 统计信息
        print("\n6. 统计信息")
        stats = board.get_statistics()
        print(f"   总发布: {stats['total_posts']}")
        print(f"   总阅读: {stats['total_views']}")
        print(f"   战略层: {stats['by_tier']['strategic']['count']}条")
        print(f"   市场层: {stats['by_tier']['market']['count']}条")
        print(f"   系统层: {stats['by_tier']['system']['count']}条")
        
        self.assertEqual(stats['total_posts'], 3)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestBulletinBoardPermissions))
    suite.addTests(loader.loadTestsFromTestCase(TestBulletinBoardV4))
    suite.addTests(loader.loadTestsFromTestCase(TestBulletinWorkflow))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

