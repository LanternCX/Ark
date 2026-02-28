# Ark 架构（开发文档）

本文面向开发者。面向用户的操作流程请查看 `README.zh-CN.md` 中的 TUI 阶段说明。

## 1. 分层边界

Ark 采用单向依赖：

`collector/signals/ai -> decision -> tui/backup -> cli`

- `ark/collector/*`：文件发现与元数据采集。
- `ark/signals/*`：本地启发式评分。
- `ark/ai/*`：模型分批、路由、认证集成。
- `ark/decision/*`：分级决策逻辑。
- `ark/tui/*`：交互与人工审核。
- `ark/backup/*`：镜像复制执行。
- `ark/cli.py`：仅负责入口与装配。

## 2. 运行时流程

1. `ark` 进入主菜单。
2. 用户在 `Backup Settings` 与 `LLM Settings` 修改参数。
3. 参数通过 `JSONConfigStore` 持久化到 `~/.ark/config.json`。
4. `Execute Backup` 调用 `ark/pipeline/run_backup.py` 执行分阶段流程。
5. Stage 1/2/3 产出最终选择路径。
6. 非 dry run 时由 `backup.executor` 执行镜像复制。

## 3. 配置模型

`PipelineConfig` 分为两类字段：

- 备份执行字段（`target`、`source_roots`、`dry_run`、`non_interactive`）。
- LLM 字段（开关、provider/model、base URL、认证凭据）。

执行前会做配置校验，常见阻断条件：

- 缺少 target/source roots。
- 启用 LLM 但缺少 provider/model。
- Gemini 选择 OAuth 但缺少 client id/client secret/refresh token。

## 4. AI 路由策略

- 非 Gemini provider 默认使用 LiteLLM API key 路径。
- Gemini 支持两种模式：
  - `api_key`
  - `google_oauth`（浏览器授权 + refresh token 刷新）
- OAuth token 刷新基于 Google 官方认证 SDK。

## 5. 测试约定

- 行为变更先写测试（TDD）。
- 测试目录与源码目录结构镜像。
- 先跑定向测试，再跑全量 `pytest`。

## 6. 文档约定

- 用户文档需保持双语（`README.md`、`README.zh-CN.md`）。
- `docs/` 只放开发文档，避免与 skills 治理内容重复。
- OAuth 开通与排障文档见：
  - `docs/google-oauth-setup.md`
  - `docs/google-oauth-setup.zh-CN.md`
