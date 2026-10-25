# Motbo Specification

## 1. 项目目标

Motbo 是一个基于 MuJoCo 的开源具身智能仿真平台，为机器人开发者提供模型管理、实验配置、仿真运行和结果分析能力。

第一版以完整、可运行、可复现的仿真实验流程为目标。

## 2. 核心功能

### 2.1 项目管理

- 创建、查看和管理仿真项目。
- 每个项目独立管理模型、实验和运行记录。
- 支持项目名称、描述和创建时间。

### 2.2 模型管理

- 支持导入 MuJoCo MJCF 模型。
- 展示模型名称、文件路径和注册时间。
- 验证模型文件格式及可加载性。
- 提供至少一个可直接运行的示例机器人模型。

### 2.3 场景管理

- 支持配置仿真场景和基础环境参数。
- 提供默认地面、光照和基础物体。
- 支持加载模型并创建仿真实例。

### 2.4 实验管理

- 创建实验并关联机器人模型。
- 配置仿真时长、时间步长、随机种子等参数。
- 保存实验配置，支持重复运行。
- 记录实验创建时间和关联项目。

### 2.5 仿真运行

- 基于 MuJoCo 执行仿真。
- 支持启动、查询状态和取消运行。
- 记录运行状态：`pending`、`running`、`completed`、`failed`、`cancelled`。
- 记录运行耗时、仿真步数和异常信息。
- 每次运行生成唯一的 `run_id`。

### 2.6 指标与结果

- 记录仿真步数、实际耗时和仿真 FPS。
- 保存运行配置、日志、指标和可选轨迹数据。
- 提供运行详情及结果查询接口。
- 支持下载运行结果文件。

### 2.7 Web Dashboard

- 展示项目列表及项目详情。
- 展示模型和实验列表。
- 支持创建实验并启动仿真。
- 展示运行状态、日志和关键指标。
- 查看历史运行记录及结果。

## 3. 技术要求

- 后端使用 Python 和 FastAPI。
- 仿真使用 MuJoCo 官方 Python 绑定。
- 前端使用 React、TypeScript 和 Vite。
- 数据库使用 SQLite。
- 文件存储使用本地持久化目录。
- API 使用 REST 和 JSON，统一前缀为 `/api/v1`。
- 使用 pytest 编写自动化测试。
- 使用 Docker Compose 提供部署方式。

## 4. 数据模型

### Project

- `id`
- `name`
- `description`
- `created_at`
- `updated_at`

### Model

- `id`
- `project_id`
- `name`
- `file_path`
- `created_at`

### Experiment

- `id`
- `project_id`
- `model_id`
- `name`
- `config`
- `created_at`

### Run

- `id`
- `experiment_id`
- `status`
- `started_at`
- `finished_at`
- `duration`
- `error_message`
- `result_path`

所有核心实体使用唯一 ID，并记录必要的创建与运行信息。

## 5. 核心 API

| 方法 | 路径 | 功能 |
|---|---|---|
| GET | `/api/v1/health` | 服务健康检查 |
| GET / POST | `/api/v1/projects` | 项目列表 / 创建项目 |
| GET / POST | `/api/v1/projects/{id}/models` | 模型列表 / 注册模型 |
| GET / POST | `/api/v1/projects/{id}/experiments` | 实验列表 / 创建实验 |
| GET | `/api/v1/experiments/{id}` | 实验详情 |
| POST | `/api/v1/experiments/{id}/runs` | 启动仿真 |
| GET | `/api/v1/runs/{id}` | 运行详情 |
| POST | `/api/v1/runs/{id}/cancel` | 取消运行 |
| GET | `/api/v1/runs/{id}/metrics` | 运行指标 |
| GET | `/api/v1/runs/{id}/logs` | 运行日志 |
| GET | `/api/v1/runs/{id}/artifacts` | 运行产物列表 |

## 6. 非功能要求

- 模型加载失败时返回清晰的错误信息。
- 单次仿真异常不得导致 API 服务整体退出。
- 运行状态和结果应持久化，服务重启后可以查询历史记录。
- 仿真任务应与 HTTP 请求生命周期解耦。
- 文件路径应限制在指定的数据目录内。
- 关键业务逻辑具备自动化测试。
- 提供清晰的安装、运行和部署说明。

## 7. MVP 验收标准

第一版完成时，应满足以下条件：

1. 可以在本地成功启动后端服务。
2. 可以创建项目并导入有效的 MJCF 模型。
3. 可以配置实验参数并启动 MuJoCo 仿真。
4. 可以查询运行状态，并获取成功或失败信息。
5. 可以持久化运行配置、日志和指标。
6. 服务重启后，历史项目和运行记录仍然存在。
7. Dashboard 可以完成基本实验操作并展示运行结果。
8. 自动化测试通过，Docker Compose 部署可用。
9. 新开发者可以依据 README 完成安装并运行示例。

## 8. 开发计划

### Phase 1：仿真核心

实现模型加载、基础仿真、运行控制、指标采集和结果持久化。

### Phase 2：后端 API

实现项目、模型、实验和运行管理接口，并补充自动化测试。

### Phase 3：Web Dashboard

实现项目管理、实验创建、运行监控和结果展示。

### Phase 4：工程化

完善 Docker 部署、CI、错误处理、文档和示例。

### Phase 5：扩展能力

逐步支持批量实验、并行仿真、更多机器人模型、场景复用及可视化增强。
