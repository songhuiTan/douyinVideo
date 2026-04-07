# 爆款复刻 — TikTok/抖音视频拆解工具

上传一条短视频，AI 自动拆解分镜、逆向推导创作提示词、提炼爆款模式，生成可复用的拍摄模板。

## 功能

- **视频分段** — PySceneDetect 自动检测场景切换，ffmpeg 精确切割（stream copy 避免重编码）
- **视觉分析** — 智谱 GLM-4.6V 截帧分析（国内直达），或 Gemini 2.5 Flash 视频理解（需翻墙）
- **语音转写** — OpenAI Whisper 提取字幕/台词
- **AI 推理** — Claude Sonnet 4 逆向推导创作提示词 + 提炼爆款模式
- **复刻指南** — 自动生成分镜表、逆向提示词、可复用拍摄模板，支持 Markdown 导出

## 技术架构

```
┌──────────────┐     ┌─────────────────────────────────────┐
│   Next.js    │────▶│           FastAPI 后端               │
│   前端       │     │                                     │
│  :3000       │◀────│  upload → analyze → status → result │
└──────────────┘     │                                     │
                     │  视频处理管线：                       │
                     │  1. ffprobe 获取元数据               │
                     │  2. PySceneDetect 场景检测           │
                     │  3. ffmpeg 分段切割                  │
                     │  4. 并行 AI 分析（视觉+音频）         │
                     │  5. Claude 推理（提示词+模式）        │
                     │  6. 组装复刻指南                      │
                     └─────────────────────────────────────┘
```

### AI 服务

| 服务 | 用途 | Provider |
|------|------|----------|
| 视觉分析 | 分析画面内容、景别、运镜、色调等 | 智谱 GLM-4.6V / Gemini 2.5 Flash |
| 语音转写 | 提取台词、字幕 | OpenAI Whisper |
| 创意推理 | 逆向推导提示词、提炼爆款模式 | Claude Sonnet 4 |

## 项目结构

```
douyinVideo/
├── backend/
│   ├── main.py                  # FastAPI 入口，7 个 API 端点
│   ├── config.py                # Pydantic Settings 配置
│   ├── requirements.txt         # Python 依赖
│   ├── models/
│   │   └── schemas.py           # 数据模型（Pydantic）
│   └── services/
│       ├── zhipu_analyzer.py    # 智谱 GLM-4.6V 视觉分析（截帧+base64）
│       ├── gemini_analyzer.py   # Gemini 2.5 Flash 视觉分析
│       ├── claude_reasoner.py   # Claude Sonnet 4 创意推理
│       ├── transcriber.py       # OpenAI Whisper 语音转写
│       ├── video_processor.py   # 视频处理（场景检测、分段、音频提取）
│       └── pipeline.py          # 分析管线编排（异步并行）
├── frontend/
│   ├── package.json
│   └── src/app/
│       ├── page.tsx             # 主页面（上传+进度+结果+导出）
│       ├── layout.tsx
│       └── globals.css
├── .env                         # 环境变量配置
├── .env.example                 # 环境变量模板
└── docs/
    └── plans/                   # 设计文档
```

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入 API Key：

```env
# 视觉分析 Provider：zhipu（国内推荐）或 gemini（需翻墙）
VISION_PROVIDER=zhipu
ZHIPU_API_KEY=your-zhipu-api-key
ZHIPU_VISION_MODEL=glm-4.6v-flashx

# Claude 推理（支持智谱代理）
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic

# 语音转写（可选，填 placeholder 可跳过）
OPENAI_API_KEY=your-openai-api-key

# Gemini（VISION_PROVIDER=gemini 时需要）
GEMINI_API_KEY=your-gemini-api-key
```

### 2. 启动后端

```bash
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 4. 访问

打开 http://localhost:3000，上传一条短视频（15-120 秒），自动生成复刻指南。

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/upload` | 上传视频文件（mp4/mov/avi/mkv/webm，最大 500MB） |
| POST | `/api/analyze/{video_id}` | 触发视频分析 |
| GET | `/api/status/{video_id}` | 查询分析进度 |
| GET | `/api/result/{video_id}` | 获取分析结果 |
| GET | `/api/result/{video_id}/export` | 导出 Markdown 格式复刻指南 |
| GET | `/api/health` | 健康检查 |

## 分析管线流程

```
视频上传
  │
  ├─ ffprobe 元数据（时长、分辨率、音轨）
  │
  ├─ PySceneDetect 场景检测
  │   └─ 短于 2s 的段合并到相邻段，上限 12 段
  │
  ├─ ffmpeg 分段切割（-c copy 避免重编码）
  │
  ├─ 并行 AI 分析 ──────────────────────────────┐
  │   ├─ 各段视觉分析（智谱/Gemini）× N 段        │
  │   ├─ 全片视觉分析（智谱/Gemini）              │
  │   └─ 音频转写（Whisper）                      │
  │                                              │
  ├─ Claude 推理（并行）◀────────────────────────┘
  │   ├─ 逆向推导提示词（visual/narrative/style）
  │   └─ 提炼爆款模式 + 可复用拍摄模板
  │
  └─ 组装复刻指南（分镜表 + 提示词 + 模板）
```

所有 AI 服务调用通过 `asyncio.gather(return_exceptions=True)` 并行执行，单个服务失败不影响整体管线。

## 依赖

**后端** (Python 3.10+)
- FastAPI + Uvicorn
- PySceneDetect + OpenCV（场景检测）
- httpx（智谱 API 调用）
- google-generativeai（Gemini）
- anthropic（Claude）
- openai（Whisper）
- pydantic-settings（配置管理）

**前端** (Node.js 18+)
- Next.js 15 + React 18
- Tailwind CSS v4
- Lucide React（图标）

## License

MIT
