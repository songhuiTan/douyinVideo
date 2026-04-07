---
name: ultrawork
description: 并行编排模式 — 将需求分解为可并行子任务并分发执行
allowed-tools: ["*"]
---

# /ultrawork — 并行编排

执行 ultrawork skill，进入并行编排模式。

## 流程

1. **DECOMPOSE** — 分解需求为独立子任务 + 依赖图（DAG）
2. **DISPATCH** — 按 Wave 并行分发到多个 Agent
3. **GATHER** — 汇聚所有 Agent 结果
4. **INTEGRATE** — 整合验证（测试 + 冲突检查）
5. **COMPOUND** — 沉淀并行执行经验

## 用法

- `/ultrawork 同时完成用户模块的注册、登录、和个人资料三个功能`
- `/ultrawork 研究这 5 个竞品的 API 设计并给出对比表`

## 规则

- 最多 5 个并行 Agent
- 涉及代码修改的 Agent 使用 worktree 隔离
- 每个 Agent 有明确的输入、输出和超时限制
- 熔断器：连续无进展或超时自动取消

## 并行模式选择

| 需求特征 | 推荐模式 |
|---------|---------|
| 多个独立功能开发 | Wave 并行（各功能独立 Wave） |
| 研究 + 实现 | 两阶段（先研究后实现） |
| 全面代码审查 | 扇出并行（每文件一个 Reviewer） |
| 多方案对比 | 竞争并行（多 Agent 各做一版） |
