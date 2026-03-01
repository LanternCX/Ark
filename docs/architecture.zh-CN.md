# Ark 架构（开发文档）

本文面向开发者。面向用户的操作流程请查看 `README.zh-CN.md` 中的 TUI 阶段说明。

## 1. 分层边界

Ark 采用单向依赖：

`collector/signals/ai -> decision -> tui/backup -> cli`

- `src/collector/*`：文件发现与元数据采集。
- `src/signals/*`：本地启发式评分。
- `src/ai/*`：模型分批、路由、认证集成。
- `src/decision/*`：分级决策逻辑。
- `src/tui/*`：交互与人工审核。
- `src/backup/*`：镜像复制执行。
- `main.py`：源码运行入口。
- `src/cli.py`：Typer 应用装配与运行编排入口。

## 2. 运行时流程

1. `python3 main.py`（或打包可执行文件 / 已安装 `ark`）进入主菜单。
2. 用户在 `Backup Settings` 与 `LLM Settings` 修改参数。
3. 参数通过 `JSONConfigStore` 持久化到 `<运行目录>/.ark/config.json`。
4. `Execute Backup` 调用 `src/pipeline/run_backup.py` 执行分阶段流程。
5. Stage 1 按后缀类别分层筛选。
6. Stage 1/2/3 产出最终选择路径。
7. Stage 3 使用树形分页 + 三态选择 + 图案化交互。
8. 非 dry run 时由 `backup.executor` 执行镜像复制。
9. 运行态检查点写入 `<运行目录>/.ark/state/backup_runs`，支持中断恢复。

`<运行目录>` 指源码模式下 `main.py` 所在目录，或打包模式下可执行文件所在目录。

## 3. 配置模型

`PipelineConfig` 分为三类字段：

- 备份执行字段（`target`、`source_roots`、`dry_run`、`non_interactive`）。
- LLM 路由字段（`llm_enabled`、`llm_provider_group`、`llm_provider`、`llm_model`、`llm_base_url`、`llm_api_key`、`llm_auth_method`、`google_client_id`、`google_client_secret`、`google_refresh_token`）。
- AI 决策字段（`ai_suffix_enabled`、`ai_path_enabled`、`send_full_path_to_ai`、`ai_prune_mode`）。

执行前会做配置校验，常见阻断条件：

- 缺少 target/source roots。
- 启用 LLM 但缺少 provider/model。
- Gemini 选择 OAuth 但缺少 client id/client secret/refresh token。
- `ai_prune_mode` 不是 `hide_low_value` / `show_all`。

## 4. AI 路由策略

- 非 Gemini provider 默认使用 LiteLLM API key 路径。
- Gemini 支持两种模式：
  - `api_key`
  - `google_oauth`（浏览器授权 + refresh token 刷新）
- OAuth token 刷新基于 Google 官方认证 SDK。

AI 分类作用域：

- 后缀风险建议可影响 Stage 1 默认白名单。
- 路径风险建议可影响 Stage 2 理由与 Stage 3 初始减枝。
- Stage 3 在最终人工确认前可执行串行目录 DFS AI 决策（`keep/drop/not_sure`）。
- 在配置允许时可发送完整路径字符串；不会发送文件内容。
- 扫描减枝与后缀分类默认值来自外部规则文件，并与 AI 决策融合。

## 5. 运行态检查点与日志

- Pipeline 支持分阶段检查点（`scan`、`stage1`、`stage2`、`review`、`copy`）。
- 中断后可基于 run 元信息和检查点 payload 恢复。
- 运行日志使用 rich 控制台输出 + 轮转文件日志。
- LiteLLM 依赖日志会统一对齐并过滤到 warning 噪音基线。
- 每次运行的结构化事件会追加写入 JSONL，便于复盘。

## 6. 测试约定

- 行为变更先写测试（TDD）。
- 测试目录与源码目录结构镜像。
- 先跑定向测试，再跑全量 `pytest`。

## 7. 文档约定

- 用户文档需保持双语（`README.md`、`README.zh-CN.md`）。
- `docs/` 只放开发文档，避免与 skills 治理内容重复。
- OAuth 开通与排障文档见：
  - `docs/google-oauth-setup.md`
  - `docs/google-oauth-setup.zh-CN.md`
