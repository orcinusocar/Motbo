# Motbo

基于 MuJoCo 的开源具身智能仿真平台。第一版目标是完整、可运行、可复现的仿真实验流程。

当前完成 **阶段一：仿真核心**，包含模型加载、基础仿真、运行控制、指标采集和结果持久化。REST API、Dashboard 与 Docker 部署将在后续阶段实现。

## 环境要求

- Python 3.10+
- 可安装 MuJoCo 官方 Python 绑定

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 运行示例

校验自带双连杆机械臂模型：

```bash
motbo validate --model examples/models/simple_arm.xml
```

无界面实验并保存结果：

```bash
motbo run --model examples/models/simple_arm.xml --duration 1.0
```

同一套仿真打开 Viewer（Joint / Control 来自这次 run）：

```bash
motbo run --model examples/models/simple_arm.xml --duration 10 --render
```

或：

```bash
python examples/view_simple_arm.py
```

查询历史运行：

```bash
motbo status <run_id>
```

也可使用：

```bash
python -m app run --model examples/models/simple_arm.xml
```

## 测试

```bash
pytest
```

## 运行产物

每次运行生成独立 `run_id`，结果保存在 `data/runs/<run_id>/`：

```text
config.yaml
status.json
metrics.json
trajectory.npz
simulation.log
```

## 项目结构

```text
app/            仿真核心
examples/       示例模型、场景和实验配置
tests/          pytest
data/           本地持久化目录
```
