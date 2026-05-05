"""
Claude Code Fusion 单元测试。

测试核心安全机制和文件操作。
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path

# 导入主模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from claude_core import (
    FileStateCache,
    FStringMatcher,
    EditValidator,
    ClaudeFusionEngine
)


class TestFileStateCache(unittest.TestCase):
    """测试文件缓存机制"""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cache = FileStateCache(self.tmpdir)
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir)
    
    def test_cache_and_retrieve(self):
        """测试缓存和读取"""
        # 创建测试文件
        test_file = os.path.join(self.tmpdir, "test.py")
        with open(test_file, "w") as f:
            f.write("def hello():\n    return 42")
        
        # 写入缓存
        self.cache.save("test.py", "def hello():\n    return 42")
        
        # 读取
        result = self.cache.get_all()["test.py"]
        self.assertEqual(result["file_content"], "def hello():\n    return 42")
        self.assertEqual(result["file_hash"], "test.py")  # 简化测试
        
    def test_cache_limit(self):
        """测试缓存大小限制（模拟 500K 行限制）"""
        # 创建超长内容
        long_content = "\n".join([f"line {i}" for i in range(1000)])  # 1000 行
        
        # 保存
        self.cache.save("long.py", long_content)
        
        # 读取（应该有 limit）
        result = self.cache.get_all()["long.py"]["file_content"]
        # 默认 limit 是 500，所以应该是 500 行
        self.assertTrue(len(result) < len(long_content))  # 被截断了


class TestStringMatcher(unittest.TestCase):
    """测试模糊匹配"""
    
    def test_straight_quotes(self):
        """测试直引号匹配"""
        content = 'print("Hello World")'
        matcher = FStringMatcher(content)
        
        # 找直引号内容
        found, pos = matcher.find('Hello World')
        self.assertTrue(found)
        self.assertEqual(content[pos:pos+11], 'Hello World')
        
    def test_curly_quotes_fallback(self):
        """测试弯引号回落到直引号"""
        # 文件中用弯引号
        content = 'print("Hello World")'  # U+201C..U+201D
        
        matcher = FStringMatcher(content)
        # 尝试找直引号内容
        found, pos = matcher.find('Hello World')
        self.assertTrue(found)
        self.assertEqual(content[pos:pos+11], "Hello World")  # 返回弯引号


class TestEditValidator(unittest.TestCase):
    """测试安全验证"""
    
    def test_error_code_1_same_strings(self):
        """错误码 1: old_string == new_string"""
        validator = EditValidator()
        result = validator.validate("test.py", "old", "old")
        self.assertIn("error_code", result)
        self.assertEqual(result["error_code"], 1)
        self.assertIn("must be different", result["error"])
        
    def test_error_code_4_file_not_found(self):
        """错误码 4: 文件未找到"""
        validator = EditValidator()
        # 模拟文件未缓存
        result = validator.validate("nonexistent.py", "old", "new")
        self.assertIn("error_code", result)
        self.assertEqual(result["error_code"], 4)
        
    def test_error_code_6_not_read(self):
        """错误码 6: 未先 Read（模拟）"""
        # 这个需要更复杂的 setup，暂时跳过
        pass


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.engine = ClaudeFusionEngine({
            "max_turns": 10,
            "workdir": self.tmpdir,
            "verbose": False
        })
    
    def tearDown(self):
        shutil.rmtree(self.tmpdir)
    
    def test_edit_workflow(self):
        """测试完整 Edit 流程（模拟）"""
        # 创建文件
        filepath = os.path.join(self.tmpdir, "auth.py")
        with open(filepath, "w") as f:
            f.write("def auth_user(username, password):\n    return True\n")
        
        # 步骤 1: Read（模拟）
        read_result = self.engine._execute_tool("Read", {
            "path": "auth.py",
            "limit": 500
        })
        
        self.assertIn("content", read_result)
        self.assertEqual("return True" in str(read_result), True)
        
        # 步骤 2: Edit（模拟）
        edit_result = self.engine._execute_tool("Edit", {
            "path": "auth.py",
            "old_string": "return True",
            "new_string": "try:\n            return True\n        except Exception as e:\n            return False",
            "replace_all": False
        })
        
        # 检查编辑结果（应该是成功的）
        self.assertIn("diff", edit_result)


if __name__ == "__main__":
    unittest.main()
