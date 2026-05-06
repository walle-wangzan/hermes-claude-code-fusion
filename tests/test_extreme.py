"""Claude Code Fusion 单元测试。

测试核心安全机制和文件操作。
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from claude_core import FileStateCache, FileStateEntry, FStringMatcher, EditValidator


class TestFileStateEntry(unittest.TestCase):
    """测试文件缓存条目"""
    
    def test_create_entry(self):
        """测试创建缓存条目"""
        entry = FileStateEntry("test.py", "def hello(): pass", 500)
        
        self.assertEqual(entry.path, "test.py")
        self.assertEqual(entry.content, "def hello(): pass")
        self.assertEqual(entry.limit, 500)
        
    def test_etag_generation(self):
        """测试 ETag 生成（内容哈希）"""
        entry1 = FileStateEntry("test.py", "def hello(): pass", 500)
        entry2 = FileStateEntry("test.py", "def hello(): pass", 500)
        entry3 = FileStateEntry("test.py", "def world(): pass", 500)
        
        self.assertEqual(entry1.etag, entry2.etag)  # 相同内容
        self.assertNotEqual(entry1.etag, entry3.etag)  # 不同内容


class TestFileStateCache(unittest.TestCase):
    """测试文件缓存机制"""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cache = FileStateCache(self.tmpdir)
        
    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        
    def test_cache_and_retrieve(self):
        """测试缓存和读取"""
        self.cache.save("test.py", "def hello():\n    return 42")
        
        result = self.cache.get_all()["test.py"]
        self.assertIn("content" or "file_content", result)
        
    def test_limit_behavior(self):
        """测试缓存有限（默认 500 行）"""
        long_content = "\n".join([f"line {i}" for i in range(1000)])
        
        self.cache.save("long.py", long_content)
        entries = self.cache.get_all()
        
        self.assertLess(len(entries["long.py"]["file_content"]), len(long_content))


class TestFStringMatcher(unittest.TestCase):
    """测试模糊字符串匹配"""
    
    def test_exact_match(self):
        """测试精确匹配"""
        content = 'print("Hello World")'
        matcher = FStringMatcher()
        
        found_str, pos = matcher.find_actual_string(content, "Hello World")
        self.assertTrue(found_str is not None)
        self.assertEqual(found_str, "Hello World")


class TestEditValidator(unittest.TestCase):
    """测试文件编辑安全验证"""
    
    def setUp(self):
        pass
        
    def test_error_code_1_same_strings(self):
        """错误码 1: old_string 和 new_string 相同"""
        validator = EditValidator(None, None)
        result = validator.validate(
            path="test.py",
            old_string="same",
            new_string="same"
        )
        
        self.assertIn("error_code", result)
        self.assertEqual(result["error_code"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2, failfast=True)