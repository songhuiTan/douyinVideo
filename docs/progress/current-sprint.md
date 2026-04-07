---
sprint_id: sprint-2026-04-06-01
status: BUILDING
created: 2026-04-06
updated: 2026-04-06
title: TikTok 视频拆解网站 — 爆款复刻指南生成器
type: full-sprint
---

## 当前阶段

BUILDING — GATE 1 通过，核心代码已写入

## 已完成的步骤

1. Sprint 初始化 ✅
2. 前置检查（gstack v0.15.14.0 + CE Plugin）✅
3. `/office-hours` 完整执行 ✅
   - Builder 模式（黑客松/Demo）
   - 4 轮问答 → Approach A 确认
   - 设计文档生成 + reviewer 审查（16 issues fixed）
4. 设计文档 **APPROVED** ✅
5. GATE 1 — `/plan-eng-review` 工程审查 ✅
   - 14 issues found (2 P1, 3 P2 架构; 1 P1, 2 P2, 2 P3 代码质量; 1 P1, 1 P2, 1 P3 性能)
   - 2 critical gaps: Gemini rate limiting, Claude timeout handling
   - 所有骨架代码保留，审查确认可复用
   - 7 个新文件需创建: pipeline.py, transcriber.py, claude_reasoner.py, main.py, api/routes.py, tests/, frontend/

## 待完成步骤（下一阶段: BUILD → REVIEW）

6. ✅ 定修复代码质量问题（schemas, gemini imports, subprocess timeout, input校验)
7. ✅ 丨 创建 transcriber.py + claude_reasoner.py + pipeline.py + FastAPI main.py
8. ✅ 丨 搭建 Next.js 前端（上传+进度+结果展示+导出）
9. GATE 2 — REVIEW ✅ (14 P0 修复 → 3 P1 → 0 P2/P3,全部降级，10. GATE 3 — TEST（端到端测试）
11. GATE 4 — SHIP

## 设计文档

- 位置: `plans/design-doc-office-hours.md`
- 状态: **APPROVED** ✅
- 方案: PySceneDetect + Gemini 2.5 Flash + Claude Sonnet 4
- 核心输出: 复刻指南（分镜+提示词+节奏+配乐）

## 关键决策记录

- D1: MVP 只做分析，不做视频生成
- D2: 技术栈 Next.js + FastAPI
- D3: Gemini 原生视频理解（不抽帧）+ gpt-4o-mini-transcribe + Claude Sonnet 4
- D4: 分段功能必须保留
- D5: Approach A（分段+多模型协作）
- D6: 成本 ~$0.06-0.15/60s 视频
- D8: 骨架代码全部保留，经 eng review 确认可复用
- D9: MVP 用内存 dict 做状态管理，不做 SQLite
- D10: 分段合并阈值：短于 2s 的段合并到相邻段，上限 12 段
- D11: ffmpeg 分段用 stream copy（-c copy）避免重编码

## 阻塞问题

（无）

## 骨架代码状态

以下文件在 GATE 前被提前创建，经 `/plan-eng-review` 审查确认全部可复用：
- `backend/config.py` — 可用，需加启动时 API key 校验
- `backend/requirements.txt` — 可用
- `backend/models/schemas.py` — 需加 ViralPatterns 模型
- `backend/services/video_processor.py` — 可用，需加 timeout 和输入校验
- `backend/services/gemini_analyzer.py` — 可用，需加 async 包装
