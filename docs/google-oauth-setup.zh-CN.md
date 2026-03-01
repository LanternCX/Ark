# Gemini 的 Google OAuth 开通指南（开发文档）

本文说明如何在 Google Cloud 注册 OAuth 凭据，并接入 Ark 的 Gemini OAuth 模式。

## 1. 准备 Google Cloud 项目

1. 打开 Google Cloud Console。
2. 新建或选择一个项目。
3. 启用 Gemini API（Generative Language API）。

## 2. 配置 OAuth Consent Screen

1. 进入 OAuth consent screen。
2. 用户类型选择 `External`。
3. 填写应用名称和支持邮箱。
4. 本地联调阶段保持 `Testing` 状态。
5. 在 `Test users` 中加入你自己的 Google 账号。

如果没有加入测试用户，登录时会返回 access denied。

## 3. 创建 Desktop OAuth Client

1. 进入 Credentials 页面。
2. 点击 Create Credentials -> OAuth client ID。
3. Application type 选择 `Desktop app`。
4. 保存生成的 `client_id` 和 `client_secret`。

## 4. 在 Ark TUI 中配置

路径：

1. `Settings`
2. `LLM Settings`
3. 选择 `Google Gemini`
4. `Gemini authentication method` 选择 `google_oauth`

然后填写：

- `Google client id`
- `Google client secret`
- 确认 `Login with Google in browser now?`

浏览器授权成功后，Ark 会把 refresh token 保存到 `<运行目录>/.ark/config.json`。

## 5. 本地保存的凭据

Ark 会在本地保存：

- `google_client_id`
- `google_client_secret`
- `google_refresh_token`

请将 `<运行目录>/.ark/config.json` 视为敏感文件，不要提交或分享。

## 6. 常见错误

- `access_denied`：当前账号未加入 OAuth 测试用户。
- `invalid_client`：client id/client secret 不匹配。
- refresh token 缺失：授权完成但未获得离线 token，请重新登录。
- token 刷新失败：凭据被撤销或 OAuth client secret 已变更。

## 7. 使用的官方 SDK

Ark 使用 Google 官方 SDK 包：

- `google-auth`
- `google-auth-oauthlib`
- `google-genai`
