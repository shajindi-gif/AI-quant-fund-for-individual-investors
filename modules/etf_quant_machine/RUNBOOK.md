# RUNBOOK

## 项目说明

ETF信号评分与解释机器

## 常用命令

### 查看当前目录

```bash
pwd
ls -la
```

### 查看 Git 状态

```bash
git status --short
git branch --show-current
git log --oneline -5
```

### Python 项目环境

```bash
if [ -d .venv ]; then source .venv/bin/activate; fi
python --version
```

### Node 项目环境

```bash
node --version
npm --version
```

### 测试

```bash
if [ -f pytest.ini ] || [ -d tests ]; then python -m pytest; fi
if [ -f package.json ]; then npm test; fi
```

## 排错顺序

1. 确认当前路径是否正确。
2. 确认虚拟环境是否存在。
3. 确认依赖是否安装。
4. 查看 logs/ 最近日志。
5. 查看 reports/ 最近输出。
6. 查看 Git 未提交改动。
7. 如果是数据问题，先检查 data/config。
8. 如果是模型/API问题，先检查 .env 是否存在，但不要打印密钥内容。

## 输出规范

- 运行日志放入 logs/
- 报告放入 reports/
- 结构化结果放入 schemas/ 或 reports/
- 评估结果放入 evals/

