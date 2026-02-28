# Ark

Ark 是一个用于系统迁移和重装准备的 AI 辅助备份工具。

## 核心流程

1. 第一阶段：后缀初筛 + AI 建议 + TUI 人工确认。
2. 第二阶段：本地信号与 AI 语义融合进行路径分级。
3. 第三阶段：终审后执行镜像备份。

## 隐私边界

Ark 仅向 AI 发送最小必要元数据：
- basename
- extension
- parent_dir_name（仅最后一层目录）
- size_bucket
- mtime_bucket

Ark 不上传文件内容。

## 技术栈

- 语言：Python
- TUI：questionary + rich
- LLM 路由：litellm
- 协议：MIT

## 状态

项目正在积极开发中。
