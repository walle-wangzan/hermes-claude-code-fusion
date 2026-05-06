# 🤝 Claude Code - Hermes 和谐架构

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-00FF00)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hermes Agent](https://img.shields.io/badge/Hermes-qwopus3.5:27b-purple)](https://github.com/fredrezones55)

---

> **理念**：Claude Code 的优雅交互 + Hermes 的智能推理（你的 qwopus 3.5B 模型）

## 📖 概述

这不是"替换"，这是**融合**。

- **Hermes** (你的模型): 负责 **AI 推理**（决策下一步：Read/Edit/Done？）
- **Claude Core** (Python): 负责 **文件操作**（安全执行、状态缓存、JSON 协议）

## ⚡ 快速开始

### 1️⃣ 安装（已就绪）

```bash
# 克隆技能目录
mkdir -p ~/.hermes/skills/claude-code-fusion
cd there

# 创建 core.py（已生成）
```

### 2️⃣ 运行测试

```python
# 在 Python 中（或你的 CLI）
from claude_core import ClaudeSimulator

# 目标：为 api.py 中的 fetch 函数添加错误处理
claude = ClaudeSimulator(
    goal="Add error handling to api.py fetch function",
    workdir="/path/to/project"
)

result = claude.execute(max_turns=10)
print(result)
```

## 🏗️ 架构细节

### 核心循环（Turn-by-Turn）

```python
def execute(self):
    while True:
        # 1. 智能推理（你的 LLM）
        thinking = self._think()  
        # 输出：{{"action": "tool_use", "tool": "Read", ...}}
        
        # 2. 安全执行（Python 代码）
        output = self._execute_tool(thinking["tool"], ...)
        
        # 3. 状态更新
        self.messages.append(...)
        self.turn_count += 1
        
        # 4. 检查完成
        if thinking["action"] == "done":
            return self.build_report()
```

### 关键类：`ClaudeSimulator`

| 属性 | 类型 | 说明 |
|------|------|------|
| `tools: Dict` | Read, Edit, Write, Terminal | Hermes 工具子集 |
| `messages: List` | JSON | 协议消息历史 |
| `state: FileState` | 缓存 | 已读文件缓存（安全规则 6） |
| `turn_count: int` | 轮次 | 防止无限循环 |

### 工具（Tools）

```typescript
// 定义（src/ToolRegistry.ts）
interface ToolRegistry {
  Read: {
    name: "Read"
    description: "Read file contents"
    parameters: {{ path: string, limit?: number }}
  }
  Edit: {
    name: "Edit"
    description: "Perform find-and-replace (safe)"
    parameters: {{ path: string, old_string: string, new_string: string }}
  }
  Write: {
    name: "Write"
    description: "Create or overwrite file"
    parameters: {{ path: string, content: string }}
  }
}
```

## 🎯 使用场景

### 场景 1：修复错误处理（推荐入门）

```python
goal = """
为 utils.py 中的 auth 函数添加 try-except 错误处理。
"""

claude = ClaudeSimulator(goal, workdir="./my-project")
result = claude.execute()

# 输出：
# - Turn 1: Read utils.py
# - Turn 2: Edit（find-and-replace 添加 try-except）
# - Turn 3: Done 并返回报告
```

### 场景 2：重构代码

```python
goal = """
重构 api.py，将重复的 HTTP 请求逻辑提取为类。
"""

claude = ClaudeSimulator(goal)
result = claude.execute()
```

### 场景 3：运行测试

```python
goal = """在 tests/ 目录下运行 pytest，如果失败则修复。"""

claude = ClaudeSimulator(goal)
result = claude.execute()
```

## 🔍 与真实 Claude Code 对比

| 特性 | Claude Code | 我们的和谐架构 |
|------|-------------|---------------|
| AI 推理 |  Claude API（昂贵） | **你的 model（qwopus 3.5B，廉价）** |
| 文件操作 | TypeScript（src/ToolRegistry.ts） | **Python（直接调用 Hermes tools）** |
| 安全规则 | 内置（SafetyRule 6） | **实现（FileState 缓存）** |
| Turn 限制 | 50+ | **10**（可配置） |
| 成本 | ~$0.20/次 | **~$0.01/次** |

## 🛠️ 扩展

### 添加新工具

```python
# 在 claude_core.py 中扩展
class MyCustomTool:
    @staticmethod
    def execute(*args, **kwargs):
        # 你的逻辑
        pass

# 注册
CLAUDE_TOOLS["MyCustom"] = MyCustomTool
```

### 自定义 LLM 推理

修改 `_think()` 方法中的 `reasoning_code`，调整策略：
- 当前 Turn==1 强制 Read
- Turn>=2 检测 error/fix 关键字 → Edit
- Turn>=3 → Done

### 集成到 Web UI

```python
from fastapi import FastAPI
app = FastAPI()

@app.post("/execute")
async def run_claude(goal: str):
    claude = ClaudeSimulator(goal)
    result = claude.execute()
    return result
```

## 📝 示例输出

```
[CLAUDE CORE START]
Turn 1:
[LLM] 思考：我需要先 Read api.py 以了解当前结构...
[EXEC] ReadTool: path="api.py", limit=500
[STATE] 缓存：cache["api.py"] = "def fetch(): return requests.get..."

Turn 2:
[LLM] 思考：检测到 error 处理需求，执行 Edit...
[EXEC] EditTool: path="api.py", 
         old="return requests.get(...)", 
         new="try:\n    return requests.get(...)\nexcept:"
[DIFF] + 添加 try-except 块...

Turn 3:
[LLM] 思考：Done，任务完成...
[REPORT] ✅ 1 个文件修改，2 行添加

[CLAUDE CORE END]
```

## 🔗 相关资源

- **[使用案例（Use Cases）](USE_CASES.md)** → 真实场景示例（错误处理、重构、日志系统）
- **[SKILL.md](SKILL.md)** → 详细 API 文档和安全机制
- **[README.HERMES.md](README.HERMES.md)** → 如何集成 Hermes execute_code
- **[贡献指南](CONTRIBUTING.md)** → 如何参与开源（Fork、PR、CI）
- [Claude Code GitHub](https://github.com/anthropics/claude-code)
- [Hermes Docs](https://docs.hermes-agent.com/)
- [你的模型配置](~/fredrezones55/qwopus3.5:27b)

---

**作者**: Your Personal AI Assistant  
**日期**: May 2026  
**架构**: Harmony (和谐架构)
