# 使用案例（Use Cases）

> 文档说明：如何使用 **Claude Code Fusion**（和谐架构）完成真实编码任务

---

## 📚 目录

1. [场景 1：快速修复错误处理](#场景 1-快速修复错误处理)
2. [场景 2：代码重构（提取类）](#场景 2-代码重构提取类)
3. [场景 3：添加日志系统](#场景 3-添加日志系统)
4. [场景 4：与 Hermes 集成（高级）](#场景 4-与-hermes 集成高级)
5. [场景对比](#场景对比)

---

## 场景 1：快速修复错误处理

**目标**：为现有 `auth.py` 添加完整的错误处理（try-except）

### 传统方式

```bash
# 1. 打开 IDE
# 2. 找到 auth.py
# 3. 手动写 try-except
# 4. 测试...
# 耗时：5-10 分钟
```

### 和谐架构方式

**方式 A：交互式**（类似 Claude Code）

```bash
# 在终端中
cd ~/.hermes/skills/claude-code-fusion
python

# 在 Python REPL 中
from claude_core import ClaudeFusionEngine

# 实例化
engine = ClaudeFusionEngine({
    "max_turns": 10,
    "workdir": "/path/to/your/project",  # 你的项目目录
    "verbose": True
})

# 提交任务
result = engine.submit_message("""
为 src/auth.py 中的 validate_user 函数添加错误处理。
具体要求：
1. 捕获所有异常并重试 3 次
2. 添加日志记录
3. 返回标准错误码
""")

# 查看结果
print(f"轮次：{result['turns']}")  # 输出：4
print(f"结果：{result['result']}")  # 输出：Edit completed...
print(f"步骤：{result['steps']}")   # 输出：[Read, Edit, Verify, Done]
```

**方式 B：一行命令**

```bash
cd /path/to/project
python -c "
from claude_core import run_task
result = run_task(
    goal='为 auth.py 的 login 函数添加错误处理',
    max_turns=10
)
print(result['result'])
"
```

**执行过程可视化**：

```
Turn 1/10: [Read] auth.py (150 行)
  ✅ 缓存文件内容
  ✅ 识别 login 函数位置（行 23-45）

Turn 2/10: [Edit] 添加 try-except 块
  ✓ old_string: "return verify_password(...)"
  ✓ new_string: "try:\n    return verify_password(...)\n  except:\n    ...retry logic..."
  保存修改...

Turn 3/10: [Read] 验证修改后的文件
  ✅ 确认新代码正确

Turn 4/10: [Done] 返回报告
  📝 修改摘要：
     - 添加了重试逻辑（最多 3 次）
     - 添加了 logger.debug()
     - 添加了异常分类（AuthError vs NetworkError）
```

---

## 场景 2：代码重构（提取类）

**目标**：将重复的 HTTP 请求逻辑提取为类

```python
# 原始代码：api.py
def fetch_user():
    r = requests.get("https://api.example.com/user")
    return r.json()

def fetch_posts():
    r = requests.get("https://api.example.com/posts")
    return r.json()

def fetch_comments():
    r = requests.get("https://api.example.com/comments")
    return r.json()
```

### 和谐架构解决方案

```python
from claude_core import ClaudeFusionEngine

engine = ClaudeFusionEngine({
    "max_turns": 15,
    "workdir": "."
})

result = engine.submit_message("""
重构 api.py：
1. 提取一个 APIClient 类
2. 使用 __init__ 设置 base_url
3. 添加 retry装饰器（重试3次，间隔1秒）
4. 保持原有函数作为类方法
""")

# 结果：
# - Turn 1: Read api.py
# - Turn 2: Edit - 创建 APIClient 类
# - Turn 3: Edit - 添加 retry_decorator
# - Turn 4: Edit - 替换旧代码
# - Turn 5: Done
```

**执行特点**：
- **安全机制**：每次 Edit 前先 Check（errorCode 6 保护）
- **模糊匹配**：自动处理缩进差异
- **多行操作**：支持 replace 整个函数体

---

## 场景 3：添加日志系统

**目标**：为整个项目添加结构化日志

```python
from claude_core import run_task

result = run_task(
    goal="""
分析当前项目结构，然后：
1. 创建 logging.py 配置文件
2. 为每个主要模块添加 logger = get_logger('module')
3. 设置日志级别：DEBUG (开发), INFO (生产)
4. 输出格式：JSON
""",
    max_turns=20
)
```

**多步骤推理**：
```
Turn 1: Read 项目结构（目录遍历）
Turn 2: Write logging.py（新文件）
Turn 3: Edit utils.py（添加 logger）
Turn 4: Edit api.py（添加 logger）
Turn 5: Edit main.py（配置日志级别）
Turn 6: Done
```

---

## 场景 4：与 Hermes 集成（高级）

这是**和谐架构**的核心价值：使用你的模型（qwopus 3.5B）代替昂贵的 Claude API。

### 步骤 1：配置 Hermes

```bash
# 确保你的模型已配置
hermes config list
# 模型：fredrezones55/qwopus3.5:27b
```

### 步骤 2：替换 `_think()` 方法

```python
from hermes_tools import execute_code

class HermesFusionEngine(ClaudeFusionEngine):
    def _think(self, system_prompt: str):
        """使用 Hermes execute_code 调用真实 LLM"""
        
        # 构建 prompt（类似 Claude Code）
        messages_str = self._format_messages()
        
        # 调用你的模型
        code = f"""
import json

def analyze_and_act(msgs):
    '''思考：决定下一步（tool_use 或 done）'''
    # 这里可以写你的推理逻辑，或者使用外部 LLM
    # Hermes 的 execute_code 会运行这段代码
        
    if "error" in msgs and "fix" in msgs:
        return {
            "action": "tool_use",
            "tool": "Edit",
            "params": {
                "path": "auth.py",
                "old_string": "original",
                "new_string": "retry logic"
            }
        }
    
    return {
        "action": "done",
        "result": "已完成"
    }

msgs = """ + repr(messages_str) + """
print(json.dumps(analyze_and_act(msgs)))
"""
        
        # 使用你的模型（便宜！）
        output = execute_code(
            code=code, 
            model="fredrezones55/qwopus3.5:27b"
        )
        
        import json
        return json.loads(output)
```

### 成本对比

| 方式 | API 成本 | 速度 |
|------|------|------|
| Claude Code（原生） | ~$0.20/次 | 慢（API） |
| 和谐架构（你的模型） | **~$0.001/次** | **快**（本地 3.5B） |

---

## 场景对比

### 场景 A：简单任务（单文件编辑）

**使用和谐架构**：
- 优点：轻量、无依赖、启动快（<1s）
- 缺点：复杂逻辑需要多轮（Turn 限制 10）

**适合**：
- ✅ 添加错误处理
- ✅ 修复 typos
- ✅ 添加注释

### 场景 B：复杂任务（跨文件重构）

**使用真实 Claude Code**（如果你有 API key）：
- 上下文窗口更大（200K tokens）
- 推理能力更强
- 并行执行能力

**和谐架构扩展**：
```python
# 使用 delegate_task（Hermes）实现并行
from hermes_tools import delegate_task

result = delegate_task(
    goal="重构整个 project/ 目录",
    tasks=[
        {"goal": "Read utils.py 并优化", "workdir": "."},
        {"goal": "Read api.py 并优化", "workdir": "."}
    ]
)
```

---

## 最佳实践

### 1. 安全使用

```python
# ✅ 正确：先 Read 后 Edit（errorCode 6 保护）
read_result = engine._execute_tool("Read", {"path": "file.py"})
edit_result = engine._execute_tool("Edit", {"path": "file.py", ...})

# ❌ 错误：直接 Edit（会返回 error_code: 6）
edit_result = engine._execute_tool("Edit", {"path": "file.py", ...})  # 失败！
```

### 2. 错误处理

```python
try:
    engine = ClaudeFusionEngine(...)
    result = engine.submit_message("...")
except KeyError as e:
    print(f"错误码：{e} (参考 SKILL.md 错误码表)")
```

### 3. 性能优化

```python
# 大文件？只读相关行
result = engine.submit_message("...")
# engine.FileStateCache 会自动 limit=500

# 使用 Docker？挂载卷
docker run -v ~/project:/app/workspace claude-harmony
```

---

## 故障排查

| 现象 | 可能原因 | 解决方案 |
|------|------|---------  |
| `error_code: 4` | 文件未找到 | 先用 `Read` 或创建文件 |
| `error_code: 6` | 未先 Read | 按顺序 Read → Edit |
| `error_code: 7` | 文件被外部修改 | 重新 `Read` |
| `error_code: 9` | 多匹配 | 提供 `replace_all: true` 或更精确的 context |

---

**作者**：walle-wangzan  
**版本**：v0.1.0  
**更新**：2026-05-05