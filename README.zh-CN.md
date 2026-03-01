# Ark

Ark 是一个用于系统迁移和重装准备的 AI 辅助备份工具。

## 快速开始

源码模式下无需安装到系统环境，直接运行：

```bash
python3 main.py
```

可选（已安装时）：

```bash
ark
```

Ark 会进入一级 TUI 菜单：

1. `Settings`
2. `Execute Backup`
3. `Exit`

所有运行参数都在 TUI 中配置，并会本地持久化。

配置文件路径：`<运行目录>/.ark/config.json`

`<运行目录>` 定义：

- 源码运行：`main.py` 所在目录
- 打包运行：可执行文件所在目录

## 开发文档

- 架构说明：`docs/architecture.zh-CN.md`
- Google OAuth 配置指南（Gemini）：`docs/google-oauth-setup.zh-CN.md`

## 发布打包

- GitHub Actions 发布流程会同时构建 `windows-x64` 与 `macos-arm64` 产物。
- 每个发布包都会带上运行目录内的默认文件：
  - `.ark/config.json`
  - `src/rules/baseline.ignore`
  - `src/rules/suffix_rules.toml`

## TUI 上手指南

推荐按这个顺序使用 Ark：先配置备份参数，再按需配置 AI，先跑一次 `Dry run` 看结果，确认后再执行正式复制。

### 程序运行流程

每次运行 Ark 都会经过同一条主流程：

1. **启动与加载配置**：启动后会读取 `<运行目录>/.ark/config.json`，你上次保存的设置会自动带入。
2. **进入主菜单**：你可以继续修改 `Settings`，也可以直接 `Execute Backup` 执行备份。
3. **配置生效**：在 `Settings` 中修改并保存后，新的配置会立即成为本次运行的执行依据。
4. **执行前校验**：进入 `Execute Backup` 时，Ark 会先检查关键配置是否完整（例如目标路径、源目录、模型凭据是否满足当前模式要求）。
5. **分阶段筛选与确认**：依次经过 Stage 1（后缀筛选）、Stage 2（路径分层）、Stage 3（最终确认）。
6. **写入结果**：当 `Dry run = No` 时，Stage 3 确认后的文件会实际复制到目标目录；当 `Dry run = Yes` 时，只展示流程结果，不写文件。
7. **可恢复运行**：执行过程会持续写检查点，如果中断，下次可继续上次进度。

你可以把它理解成：**先配置 -> 再预演 -> 最后落盘**。

### 第一步：`Settings -> Backup Settings`

| UI 原文 | 中文释义 | 行为与后果 |
| --- | --- | --- |
| `Backup target path` | 备份目标路径 | 这是最终写入位置。路径错误或不可写会导致备份失败，或写到非预期目录。 |
| `Source roots (comma separated)` | 源目录（逗号分隔） | 决定扫描范围。范围过小会漏文件，范围过大会增加筛选工作量。 |
| `Dry run?` | 仅模拟执行（不复制文件） | `Yes` 会走完整流程但不写文件；`No` 会把确认后的文件真正复制到目标目录。 |
| `Non-interactive reviews?` | 跳过人工确认（使用默认选择） | `Yes` 执行更快，但无法逐步人工修正；`No` 可以在关键阶段手动确认。 |

首次使用建议：`Dry run? = Yes`，`Non-interactive reviews? = No`。

### 第二步：`Settings -> LLM Settings`（可选）

如果你关闭 LiteLLM，Ark 会只使用本地规则与本地启发式逻辑。

| UI 原文 | 中文释义 | 行为与后果 |
| --- | --- | --- |
| `Enable LiteLLM integration?` | 启用 LiteLLM 集成 | `No` 表示纯本地决策；`Yes` 会启用模型相关配置并参与筛选。 |
| `LLM provider group` | LLM 服务商分组 | 决定可选平台和推荐模型范围。 |
| `LLM platform` | LLM 平台 | 决定具体调用端点，直接影响可用性、速度和费用。 |
| `Recommended model preset` | 推荐模型预设 | 快速选择当前平台下的推荐模型。 |
| `Override recommended model?` | 覆盖推荐模型 | `No` 直接用推荐值；`Yes` 需要手动输入模型 ID。 |
| `LLM model (custom allowed)` | LLM 模型名称（允许自定义） | 实际请求使用的模型标识；填错会导致请求失败或路由异常。 |
| `LLM base URL (optional)` | LLM 基础地址（可选） | 仅在你使用代理网关或自定义端点时需要填写。 |
| `Gemini authentication method` | Gemini 认证方式 | 选择 `api_key` 或 `google_oauth`，会改变后续需要填写的凭据。 |
| `Google client id` | Google 客户端 ID | Gemini OAuth 必填，用于浏览器登录与令牌刷新。 |
| `Google client secret` | Google 客户端密钥 | Gemini OAuth 必填，用于浏览器登录与令牌刷新。 |
| `Login with Google in browser now?` | 立即浏览器登录 Google | 立即完成授权并写入 refresh token，避免执行时被鉴权阻断。 |
| `LLM API key` | LLM API 密钥 | 模型调用凭据；错误会导致鉴权失败，值会保存在本地配置中。 |
| `Use AI suffix risk classification?` | 启用 AI 后缀风险分类 | 控制 Stage 1 是否使用 AI 后缀建议。关闭后仅用本地逻辑。 |
| `Use AI path pruning suggestions?` | 启用 AI 路径减枝建议 | 控制路径层是否使用 AI 建议。关闭后仅用本地逻辑。 |
| `Send full file paths to AI?` | 向 AI 发送完整路径 | `No` 为最小元数据模式；`Yes` 会发送完整路径字符串。 |
| `Hide low-value branches by default?` | 默认隐藏低价值分支 | 控制 Stage 3 初始可见范围，影响首轮查看效率。 |
| `Test LLM connectivity now?` | 立即测试 LLM 连通性 | 用当前设置发送测试请求，立即反馈配置是否可用。 |

### 第三步：执行 `Execute Backup`

- `Stage 1: Suffix Screening`：按后缀先筛一轮候选文件。
- `Stage 2: Path Tiering`：按路径优先级整理候选。
- `Stage 3: Final Review and Backup`：最终确认并执行复制。

在 Stage 3 中，`Enter` 用于展开目录，`Space` 用于切换选中状态。

### 配置项在流程中的生效位置

- `Backup target path`、`Source roots`、`Dry run?` 会直接影响本次 `Execute Backup` 的执行结果。
- `Non-interactive reviews?` 会决定你是否看到人工确认步骤。
- LLM 相关配置只在启用 LiteLLM 时参与决策；如果关闭 LiteLLM，流程会回到纯本地规则。
- `Send full file paths to AI?` 只影响发送给 AI 的信息范围，不改变本地文件内容。

### 中断后如何继续

Ark 会把检查点写入 `<运行目录>/.ark/state/backup_runs/`。如果上次执行中断，下次启动可以继续上次进度，也可以重新开始。

### 常用文件位置

- 配置文件：`<运行目录>/.ark/config.json`
- 运行日志：`<运行目录>/.ark/logs/ark.log`
- 检查点与运行记录：`<运行目录>/.ark/state/backup_runs/`

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
