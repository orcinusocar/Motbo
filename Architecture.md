# Motbo Architecture

## 1. 项目简介

Motbo 是一个基于 MuJoCo 的具身智能仿真平台，提供模型管理、场景配置、仿真运行、实验管理和结果分析能力。

## 2. 技术栈

| 模块 | 技术 |
|---|---|
| 后端 | Python、FastAPI |
| 仿真引擎 | MuJoCo、官方 Python 绑定 |
| 前端 | React、TypeScript、Vite |
| API | REST、JSON |
| 数据库 | SQLite，后续可迁移至 PostgreSQL |
| 数据存储 | 本地文件系统 |
| 测试 | pytest、HTTPX |
| 部署 | Docker、Docker Compose |
| CI | GitHub Actions |

## 3. 系统架构

```text
React Dashboard
       |
    REST API
       |
   FastAPI Backend
       |
  +----+---------+-----------+
  |              |           |
Projects     Experiments    Models
  |              |           |
  +--------------+-----------+
                 |
            Run Manager
                 |
          MuJoCo Simulator
                 |
       +---------+---------+
       |         |         |
     Metrics    Logs    Trajectory
       |         |         |
       +---------+---------+
                 |
          Storage Layer
          /            \
      SQLite         File System
```

## 4. 核心模块

- **Projects**：管理仿真项目。
- **Models**：管理机器人模型及模型文件，第一版优先支持 MJCF。
- **Scenes**：配置仿真环境、地面和物体。
- **Experiments**：管理实验配置与运行参数。
- **Simulation**：加载模型，执行仿真、重置和状态采集。
- **Run Manager**：管理运行状态、任务生命周期和异常信息。
- **Metrics**：采集仿真步数、耗时、FPS 等指标。
- **Storage**：保存配置、日志、轨迹和运行结果。

## 5. 项目结构

```text
motbo/
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── projects/
│   ├── experiments/
│   ├── simulation/
│   ├── runs/
│   ├── metrics/
│   └── storage/
├── web/
├── examples/
│   ├── models/
│   ├── scenes/
│   └── experiments/
├── tests/
├── data/
├── docs/
├── deployments/
├── pyproject.toml
├── Dockerfile
├── compose.yaml
├── SPEC.md
├── ARCHITECTURE.md
└── README.md
```

## 6. 核心工作流

1. 创建项目并导入模型。
2. 配置仿真场景和实验参数。
3. 创建运行任务并启动 MuJoCo。
4. 实时查询运行状态与指标。
5. 保存运行配置、日志、轨迹和结果。
6. 在 Dashboard 中查看实验结果。

每次运行生成独立的 `run_id`，并保存对应的配置快照。

## 7. API 设计

| 方法 | 路径 | 功能 |
|---|---|---|
| GET | `/api/v1/health` | 健康检查 |
| GET / POST | `/api/v1/projects` | 项目列表 / 创建项目 |
| GET / POST | `/api/v1/projects/{id}/models` | 模型列表 / 注册模型 |
| GET / POST | `/api/v1/projects/{id}/experiments` | 实验列表 / 创建实验 |
| POST | `/api/v1/experiments/{id}/runs` | 启动实验 |
| GET | `/api/v1/runs/{id}` | 查询运行状态 |
| POST | `/api/v1/runs/{id}/cancel` | 取消运行 |
| GET | `/api/v1/runs/{id}/metrics` | 查询指标 |
| GET | `/api/v1/runs/{id}/logs` | 查询日志 |

## 8. 数据存储

SQLite 保存项目、模型、实验和运行元数据；文件系统保存模型文件、配置、日志、指标和轨迹。

```text
data/
├── models/
├── projects/
└── runs/
    └── <run_id>/
        ├── config.yaml
        ├── metrics.json
        ├── trajectory.npz
        └── simulation.log
```

## 9. 部署

本地通过 Python 虚拟环境运行；服务器通过 Docker Compose 部署 FastAPI、前端和所需的数据服务。

部署目标为阿里云 Linux 服务器，支持持久化存储、HTTPS 和后续数据库迁移。

## 10. 开发阶段

- **Phase 1：** 完成模型加载、基础仿真、运行控制和结果保存。
- **Phase 2：** 实现项目、模型、实验和运行 API。
- **Phase 3：** 开发 Dashboard，展示运行状态、日志和结果。
- **Phase 4：** 完善 Docker 部署、自动化测试和文档。
- **Phase 5：** 扩展批量实验、并行仿真及更多模型和场景。
