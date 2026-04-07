---
name: harness-init
description: 初始化项目 Harness（创建目录结构、安装插件、生成配置）
allowed-tools: ["*"]
---

# /harness-init — 初始化项目

执行 harness-init skill，为新项目设置完整的 Harness 环境。

## 流程

1. 环境检查（Claude Code、Git、Bun、gstack、CE）
2. 创建目录结构（docs/progress/、docs/solutions/、plans/）
3. 生成配置文件（current-sprint.md、session-bridge.md）
4. 安装 Harness Skills 和 Hooks
5. 验证安装
