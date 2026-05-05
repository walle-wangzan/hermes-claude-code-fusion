# 与 Hermes Agent 集成指南

## 当前状态：纯 Python 模拟

文件 `claude_core.py` 中的 `_think()` 方法使用**确定性状态机**模拟 AI 决策：

```python
def _think(self, system_prompt: str) -> Dict[str, Any]:
    # 当前：模拟（无真实 LLM）
    if self.turn_count == 1:
        return {
            "action": "tool_use",
            "tool": "Read",
            "params": {"path": "README.md", "limit": 500},
            "reasoning": "Read first"
        }
    # ...
```

## 集成方案：替换为真实 Hermes execute_code

要让它使用你现有的模型（`fredrezones55/qwopus3.5:27b`），替换 `_think()`：

```python
from hermes_tools import execute_code, json_parse

def _think(self, system_prompt: str) -> Dict[str, Any]:
    """使用 Hermes execute_code 调用真实 LLM（替代模拟）"""
    
    # 构建 prompt（类似 Claude 的 QueryEngine）
    messages = self._format_messages_for_llm(system_prompt)
    
    # 调用 Hermes 的 execute_code（你的模型）
    code = f"""
import json
import sys

def analyze_and_act(messages, tools_desc):
    """思考：决定下一步是调用工具还是完成。"
    
    # 分析当前状态...（这里写入 Claude Code 的推理逻辑）
    # 类似 src/QueryEngine.ts:675 的 query() 函数
    
    return {{
        "action": "tool_use",  # 或 "done"
        "tool": "Read",
        "params": ...
    }}

# 调用函数
result = analyze_and_act(""" + repr(messages) + """, [])
print(json.dumps(result))
"""
    
    # 执行（使用你的模型）
    output = execute_code(code=code, model="fredrezones55/qwopus3.5:27b")
    
    # 解析 JSON
    try:
        return json_parse(output)
    except:
        import json
        return json.loads(output.split("```json")[-1].split("```")[0])
```

## 其他集成点（可选）

### 1. 使用 Hermes 的 patch() 替代 Write 操作

当前 `Edit` 工具直接写文件，可以改为调用 `hermes_tools.patch()`：

```python
else:
    from hermes_tools import patch
    result = patch(
        mode="replace",
        path=path,
        old_string=actual_old,
        new_string=new_string,
        replace_all=replace_all
    )
    return result
```

### 2. 使用 web_search 作为 MCP 工具扩展

添加 `WebSearch` 工具：

```python
from hermes_tools import web_search

elif tool_name == "WebSearch":
    query = params.get("query", "")
    result = web_search(query=query)
    return result
```

---

**当前文件已可独立运行测试，集成 Hermes 只需替换 `_think()`。**
