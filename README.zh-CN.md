# Ark

Ark 是一个用于系统迁移和重装准备的 AI 辅助备份工具。

## 快速开始

使用一个命令启动：

```bash
ark
```

Ark 会进入一级 TUI 菜单：

1. `Settings`
2. `Execute Backup`
3. `Exit`

所有运行参数都在 TUI 中配置，并会本地持久化。

配置文件路径：`~/.ark/config.json`

## 开发文档

- 架构说明：`docs/architecture.zh-CN.md`
- Google OAuth 配置指南（Gemini）：`docs/google-oauth-setup.zh-CN.md`

## TUI 阶段说明

本节按用户视角说明每个 TUI 阶段：这个阶段做什么、会有什么后果、建议怎么做。

### 阶段 0：主菜单

1. `Settings`
   - 作用：配置备份参数和 LiteLLM 参数。
   - 后果：配置会保存到 `~/.ark/config.json`，下次启动自动复用。
   - 建议：首次使用先完成设置，再执行备份。
2. `Execute Backup`
   - 作用：执行完整分阶段备份流程。
   - 后果：当 `Dry run=False` 时会真实复制文件。
   - 建议：先做一次 dry run。
3. `Exit`
   - 作用：退出 Ark。
   - 后果：不会触发备份执行。
   - 建议：确认设置已保存后再退出。

### 阶段 1：`Settings -> Backup Settings`

- `Backup target path`
  - 作用：设置镜像备份的目标根目录。
  - 后果：路径错误或无写权限会导致备份失败或写到错误位置。
  - 建议：使用稳定且可写的磁盘路径。
- `Source roots (comma separated)`
  - 作用：设置 Ark 扫描与备份候选的源目录。
  - 后果：漏填会漏备份；范围过大增加噪声和误判风险。
  - 建议：先填高价值目录（如 Documents/Pictures/Projects）。
- `Dry run?`
  - 作用：模拟完整流程但不复制文件。
  - 后果：开启时不会产生真实备份结果。
  - 建议：首次验证务必开启。
- `Non-interactive reviews?`
  - 作用：跳过人工审核，直接使用默认策略。
  - 后果：执行更快，但误分类风险更高。
  - 建议：重要迁移场景建议关闭。

### 阶段 2：`Settings -> LLM Settings`

- `Enable LiteLLM integration?`
  - 作用：开启或关闭 AI 辅助决策。
  - 后果：开启后必须配置 provider/model。
  - 建议：先完成平台和密钥配置再开启。
- `LLM provider group`
  - 作用：选择服务商分组（OpenAI 兼容、Frontier、China-Friendly、本地/自定义）。
  - 后果：决定后续平台候选和默认模型预设。
  - 建议：优先选择本地区可用且成本可控的分组。
- `LLM platform`
  - 作用：选择具体服务平台。
  - 后果：影响接口兼容性、延迟和计费。
  - 建议：先用主流预设平台跑通，再做优化切换。
- `Recommended model preset`
  - 作用：在当前 provider 下从 3 个顶级模型预设中选择一个。
  - 后果：该选择会作为下一步模型输入的默认值。
  - 建议：如果想平衡成本与效果，先选中间档位。
- `Override recommended model?`
  - 作用：决定是否改用自定义模型 ID。
  - 后果：选择 `No` 时会直接使用预设，不再提示自定义模型输入。
  - 建议：除非你明确知道目标模型字符串，否则保持 `No`。
- `LLM model`
  - 作用：指定 LiteLLM 调用的模型。
  - 后果：直接影响效果、速度和成本。
  - 建议：仅在开启覆盖时填写；请严格使用 LiteLLM 文档中的模型 ID（含必须的 provider 前缀，例如 `zai/...`、`deepseek/...`）。
- `LLM base URL (optional)`
  - 作用：为兼容网关或本地服务覆盖 API 地址。
  - 后果：URL 错误会导致连接失败。
  - 建议：不需要自建网关时保持默认。
- `LLM API key`
  - 作用：用于调用平台鉴权。
  - 后果：密钥错误会认证失败；密钥会保存到 `~/.ark/config.json`。
  - 建议：使用专用密钥并设置额度上限。
- `Test LLM connectivity now?`
  - 作用：用当前 LLM 配置发送最小探测请求。
  - 后果：可立即确认鉴权、模型和端点是否可用。
  - 建议：修改 provider/model/key/OAuth 后都建议执行一次。

### 阶段 3：`Execute Backup`

1. `Stage 1: Suffix Screening`
   - 作用：按文件后缀进行第一轮筛选。
   - 后果：通过的后缀决定后续可进入分级的文件范围。
   - 建议：不确定时偏保守，避免过度过滤。
2. `Stage 2: Path Tiering`
   - 作用：结合本地信号和 AI 语义做路径分级。
   - 后果：分级结果影响最终候选优先级。
   - 建议：重点核查关键个人/工作目录是否进入高优先级。
3. `Stage 3: Final Review and Backup`
   - 作用：最终确认并执行复制。
   - 后果：当 `Dry run=False` 时会实际写入备份文件。
   - 建议：先在树形分页视图中完成目录级决策，再确认选中数量。

### Stage 3 树形复核（新增）

- 最终选择从“单行路径列表”升级为“树形分页视图”。
- 目录节点支持三态：
  - `checked`：子孙文件全部选中
  - `partial`：子孙文件部分选中
  - `unchecked`：子孙文件全部未选
- 勾选目录会递归作用于全部子孙节点。
- 低价值分支可默认隐藏以降低噪音，并可在同一轮复核中随时切换显示。

### 首次使用建议流程

1. 先配置 `Backup Settings`。
2. 再配置 `LLM Settings`。
3. 打开 `Dry run` 执行一次。
4. 检查日志和筛选结果。
5. 关闭 `Dry run` 进行正式备份。

## 隐私边界

Ark 支持两种 AI 数据共享模式：

1. 最小元数据模式
   - basename
   - extension
   - parent_dir_name（仅最后一层目录）
   - size_bucket
   - mtime_bucket
2. 完整路径模式（可选开启）
   - 发送完整文件路径字符串，用于后缀/路径减枝建议

Ark 不上传文件内容。

## 技术栈

- 语言：Python
- TUI：questionary + rich
- LLM 路由：litellm
- 协议：MIT

## 状态

项目正在积极开发中。
