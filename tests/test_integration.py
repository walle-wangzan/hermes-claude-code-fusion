"""端到端集成测试（E2E）。

测试完整的工作流：Read → Edit → Verify
"""

import os
import sys
import tempfile
from pathlib import Path

from claude_core import EditValidator, FileStateCache, FileStateEntry, FStringMatcher

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def setup_test_files():
    """创建临时测试文件"""
    temp_dir = tempfile.mkdtemp(prefix="claude-fusion-test-")

    # 创建测试文件
    test_file = Path(temp_dir) / "test_module.py"
    test_file.write_text("""#!/usr/bin/env python3
class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b
""")

    return temp_dir, test_file


def test_read_then_edit_workflow():
    """测试先 Read 后 Edit 的安全工作流"""
    temp_dir, file_path = setup_test_files()
    abs_path = str(file_path.resolve())

    try:
        # P0: 读取文件（模拟 Hermes 的 read_file）
        cache = FileStateCache()
        timestamp = int(os.path.getmtime(abs_path) * 1000)
        content = file_path.read_text()

        entry = FileStateEntry(abs_path, content, timestamp=timestamp)
        cache.set(entry)

        print(f"✓ 步骤 1: 读取文件 {file_path.name} (len={len(content)})")

        # P2: 验证编辑
        validator = EditValidator(cache, FStringMatcher())
        result = validator.validate(
            path=abs_path,
            old_string="    def add(self, a, b):\n        return a + b",
            new_string="    def add(self, a, b):\n        return a + b + 1",  # 故意修改
            replace_all=False
        )

        # errorCode 0 表示成功，其他值表示失败
        assert result.get("result") is True or result.get("errorCode") == 0, f"验证应通过，但得到：{result}"
        print("✓ 步骤 2: 编辑验证通过")

        # P3: 执行替换（在内存中，不写入）
        assert "result" in result
        assert result["result"] is True  # 验证成功
        print("✓ 步骤 3: 内容验证成功（errorCode=0）")

        # P4: 验证文件仍为原始内容（未修改）
        current_content = file_path.read_text()
        assert "return a + b" in current_content and "+ 1" not in current_content

        print("✓ 步骤 4: 原始文件未修改（安全保证）")

        print("\n✅ 集成测试通过：Read → Edit 安全 workflow")
    finally:
        import shutil

        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("=  端到端集成测试 =")
    print()
    test_read_then_edit_workflow()
    print()
    print("所有测试完成！✓")
