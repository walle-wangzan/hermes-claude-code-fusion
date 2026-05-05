# Dockerfile for Claude Code Fusion - Hermes 和谐架构

FROM python:3.12-slim

# 设置时区（深圳/北京）
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 设置工作目录
WORKDIR /app

# 安装基础工具（git 用于 clone，bash）
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    bash \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目配置（先复制依赖文件，利用 Docker 缓存）
COPY pyproject.toml .
COPY README.md .

# 安装依赖（包括 dev dependencies）
RUN pip install --no-cache-dir -e ".[dev]"

# 复制所有代码
COPY . .

# 创建非 root 用户（安全最佳实践）
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# 切换到非 root 用户
USER appuser

# 创建默认数据目录
ENV WORKDIR=/app/workspace
RUN mkdir -p $WORKDIR && chown -R appuser:appuser $WORKDIR
VOLUME ["$WORKDIR"]

# 健康检查（可选，检测 pytest 是否工作）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from claude_core import ClaudeFusionEngine; print('healthy')" || exit 1

# 默认命令
CMD ["/bin/bash", "-c", "\n\necho '========================================' && \\\necho 'Claude Code Fusion - Hermes 和谐架构启动!' && \\\necho '========================================' && \\\necho '' && \\\necho '可用命令:' && \\\necho '  make test      运行测试' && \\\necho '  make lint      代码检查' && \\\necho '  python -h      查看帮助' && \\\necho '  exit           退出容器' && \\\necho '' && \\\necho '工作目录：$WORKDIR' && \\\necho '项目版本：$(git describe --tags --exact-match 2>/dev/null || echo unknown)' && \\\necho '' && \\\necho '准备就绪。输入任务描述开始：' && \\\nwhile true; do \\\n    read -r -p '> ' task; \\\n    if [ -z "\$task" ]; then continue; fi; \\\n    if [ "\$task" = "exit" ]; then exit 0; fi; \\\n    echo '正在处理：\$task'; \\\n    python -c \"from claude_core import run_task; \\\nresult = run_task('\$task', max_turns=10, workdir='\\\$WORKDIR'); \\\nprint('完成:'); \\\nfor line in result['result'].split('\n'): \\\n    print('  ' + line); \\\n\" 2>&1 || echo '执行出错 (未连接 Hermes)'; \\\ndone && \\\n"]

# 可选：添加元数据
LABEL maintainer="walle-wangzan"
LABEL description="Claude Code Fusion with Hermes Agent - Harmony Architecture"
LABEL org.opencontainers.image.source="https://github.com/walle-wangzan/hermes-claude-code-fusion"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image/license="MIT"
