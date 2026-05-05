# Makefile for Claude Code Fusion

SHELL := /bin/bash
.PHONY: help test lint format install publish

help:  ## 显示所有命令
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## 安装本地开发环境
	pip install -e ".[dev]"
	@echo "✅ 开发环境安装完成"

test:  ## 运行所有测试
	pytest tests/ -v --cov=claude_core --cov-report=term-missing
	@echo "✅ 测试完成"

test-quick:  ## 快速测试（不覆盖率）
	pytest tests/ -v -x

lint:  ## Ruff 检查
	ruff check .
	@echo "✅ Lint 检查通过"

format:  ## 格式化代码（黑 + 排序导入）
	black --line-length 120 *.py tests/
	isort --profile black *.py tests/
	@echo "✅ 格式化完成"

check: lint test  ## 完整检查（lint + test）

publish:  ## 发布到 PyPI（需要 Twine token）
	python -m build
	twine upload dist/*
	@echo "📦 已发布到 PyPI"

clean:  ## 清理构建文件
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -delete
	rm -rf build/ dist/ *.egg-info/
	@echo "🧹 清理完成"

help-local:  ## 本地测试帮助
	@echo "📚 本地运行示例："
	@echo ""
	@echo "1. 启动测试：make test"
	@echo "2. 检查 lint: make lint"
	@echo "3. 一键全检查：make check"
	@echo ""
	@echo "🔧 直接运行示例代码："
	@echo "  python -c \"from claude_core import run_task; print(run_task('help'))\""
