"""Claude Code Fusion 单元测试。

测试核心安全机制和文件操作。
"""

import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from claude_core import FileStateCache, FileStateEntry, FStringMatcher, EditValidator


class TestFileStateEntry(unittest.TestCase):
    """测试文件缓存条目（FileStateEntry）"""

    def test_create_entry(self):
        """测试创建缓存条目"""
        entry = FileStateEntry(
            path="test.py",
            content="def hello(): pass",
            timestamp=int(time.time() * 1000),
            limit=500
        )

        self.assertEqual(entry.path, "test.py")
        self.assertEqual(entry.content, "def hello(): pass")
        self.assertEqual(entry.limit, 500)
        self.assertEqual(entry.offset, 1)

    def test_partial_view_detection(self):
        """测试部分读取检测"""
        # 完整读取
        full = FileStateEntry("test.py", "content", timestamp=123, offset=1, limit=None)
        self.assertFalse(full.is_partial_view())

        # 部分读取
        partial = FileStateEntry("test.py", "content[0:100]", timestamp=123, offset=1, limit=100)
        self.assertTrue(partial.is_partial_view())


class TestFileStateCache(unittest.TestCase):
    """测试文件缓存机制（FileStateCache）"""

    def test_cache_set_and_get(self):
        """测试缓存的 set 和 get 操作"""
        cache = FileStateCache()
        timestamp = int(time.time() * 1000)
        
        entry = FileStateEntry("test.py", "def hello(): pass", timestamp=timestamp)
        cache.set(entry)

        result = cache.get("test.py")
        self.assertIsNotNone(result)
        self.assertEqual(result.content, "def hello(): pass")
        self.assertEqual(result.path, "test.py")

    def test_cache_has(self):
        """测试检查缓存是否存在"""
        cache = FileStateCache()
        self.assertFalse(cache.has("test.py"))

        cache.set(FileStateEntry("test.py", "content", timestamp=123))
        self.assertTrue(cache.has("test.py"))


class TestFStringMatcher(unittest.TestCase):
    """测试模糊字符串匹配（FStringMatcher - findActualString）"""

    def test_exact_match(self):
        """测试精确匹配"""
        content = 'print("Hello World")'
        matcher = FStringMatcher()

        found, pos = matcher.find(content, "Hello World")
        self.assertIsNotNone(found)
        self.assertEqual(found, "Hello World")
        # 验证位置在合理范围内
        self.assertTrue(0 <= pos <= len(content))

    def test_straight_quotes(self):
        """测试直引号匹配"""
        content = 'print("Hello World")'
        matcher = FStringMatcher()

        found, pos = matcher.find(content, 'Hello World')
        self.assertIsNotNone(found)
        self.assertEqual(content[pos:pos+11], 'Hello World')

    def test_curly_quotes_fallback(self):
        """测试弯引号标准化（U+201C/U+201D → "）"""
        # 文件中用弯引号
        content = 'print("Hello World")'  # Unicode 弯引号 (U+201C, U+201D)
        matcher = FStringMatcher()

        # 用直引号查找
        found, pos = matcher.find(content, "Hello World")
        self.assertIsNotNone(found)
        # 应该返回原始的弯引号内容
        self.assertEqual(found, "Hello World")


class TestEditValidator(unittest.TestCase):
    """测试文件编辑安全验证（EditValidator - validateInput）"""

    def setUp(self):
        """设置测试环境"""
        self.cache = FileStateCache()
        self.matcher = FStringMatcher()

    def test_error_code_1_same_strings(self):
        """错误码 1: old_string 和 new_string 相同"""
        validator = EditValidator(self.cache, self.matcher)
        result = validator.validate(
            path="test.py",
            old_string="same",
            new_string="same",
            replace_all=False
        )

        self.assertIn("errorCode", result)
        self.assertEqual(result["errorCode"], 1)
        self.assertIn("same", result["message"].lower())

    def test_error_code_4_file_not_found(self):
        """错误码 4: 文件未找到（未缓存）"""
        validator = EditValidator(self.cache, self.matcher)

        result = validator.validate(
            path="nonexistent.py",
            old_string="old",
            new_string="new",
            replace_all=False
        )

        self.assertIn("errorCode", result)
        self.assertEqual(result["errorCode"], 4)
        # 错误信息可能不同，检查关键词
        msg_lower = result["message"].lower()
        self.assertTrue("exist" in msg_lower or "read" in msg_lower)


if __name__ == "__main__":
    unittest.main(verbosity=2, failfast=False)