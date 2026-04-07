"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { Upload, Download, Copy, FileText, CheckCircle, Loader2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

interface AnalysisState {
  status: string;
  progress: number;
  message: string;
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [videoId, setVideoId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [analysisState, setAnalysisState] = useState<AnalysisState | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Polling for analysis status
  useEffect(() => {
    if (!videoId || !analyzing) return;

    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/status/${videoId}`);
        if (!res.ok) return;
        const data = await res.json();

        setAnalysisState(data);

        if (data.status === "completed") {
          setAnalyzing(false);
          clearInterval(pollInterval);
          // Fetch result
          try {
            const resultRes = await fetch(`${API_BASE}/api/result/${videoId}`);
            if (resultRes.ok) {
              const resultData = await resultRes.json();
              setResult(resultData);
            }
          } catch {
            setError("获取结果失败");
          }
        } else if (data.status === "failed") {
          setAnalyzing(false);
          clearInterval(pollInterval);
          setError(data.message || "分析失败");
        }
      } catch {
        // Network error, keep polling
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [videoId, analyzing]);

  const handleUpload = useCallback(async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/api/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "上传失败");
      }

      const data = await res.json();
      setVideoId(data.video_id);

      // Start analysis
      const analyzeRes = await fetch(`${API_BASE}/api/analyze/${data.video_id}`, {
        method: "POST",
      });
      if (!analyzeRes.ok) {
        const errData = await analyzeRes.json().catch(() => ({}));
        throw new Error(errData.detail || "启动分析失败");
      }

      setAnalyzing(true);
      setAnalysisState({ status: "processing", progress: 0.05, message: "分析已启动" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失败");
    } finally {
      setUploading(false);
    }
  }, [file]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type.startsWith("video/")) {
      setFile(droppedFile);
      setError(null);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  // Result view
  if (result) {
    return <ResultView guide={result} onReset={() => { setResult(null); setFile(null); setVideoId(null); setAnalysisState(null); setError(null); }} />;
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] gap-8">
      <div className="w-full max-w-md">
        <label className="block text-sm font-medium text-[#a1a1aa] mb-2">
          上传 TikTok/抖音爆款视频
        </label>
        <p className="text-xs text-[#525252] mb-3">
          支持 MP4, MOV, AVI, MKV, WebM, 15-120秒, 最大 500MB
        </p>

        {/* Drop zone */}
        <div
          className="relative"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) { setFile(f); setError(null); }
            }}
            className="hidden"
          />
          <div
            className="border-2 border-dashed border-[#333] rounded-lg p-8 text-center cursor-pointer hover:border-[#fe2c55] transition-colors"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="mx-auto h-6 w-6 text-[#a1a1aa]" />
            <p className="text-sm text-[#525252] mt-2">
              点击或拖拽视频到这里
            </p>
          </div>
        </div>

        {/* File selected */}
        {file && (
          <div className="mt-4 space-y-3">
            <div className="flex items-center gap-3 text-sm text-[#a1a1aa]">
              <FileText size={16} />
              <span className="truncate">{file.name}</span>
              <span className="text-[#525252]">
                {(file.size / (1024 * 1024)).toFixed(1)} MB
              </span>
            </div>
            <button
              onClick={handleUpload}
              disabled={uploading || analyzing}
              className="w-full bg-[#fe2c55] hover:bg-[#e84067] text-white font-semibold py-3 rounded-lg transition-colors disabled:opacity-50"
            >
              {uploading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="animate-spin" size={18} />
                  上传中...
                </span>
              ) : analyzing ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="animate-spin" size={18} />
                  分析中...
                </span>
              ) : (
                "开始拆解"
              )}
            </button>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-4 p-3 bg-red-500/10 text-red-400 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Analyzing progress */}
        {analyzing && analysisState && (
          <div className="mt-8">
            <div className="flex items-center gap-3">
              <Loader2 className="animate-spin text-[#fe2c55]" size={20} />
              <div className="flex-1">
                <p className="text-sm font-medium">
                  {analysisState.message || "AI 正在分析中..."}
                </p>
                <div className="mt-2">
                  <div className="h-1.5 bg-[#262626] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#fe2c55] rounded-full transition-all duration-500"
                      style={{ width: `${Math.round(analysisState.progress * 100)}%` }}
                    />
                  </div>
                  <span className="text-xs text-[#525252]">
                    {Math.round(analysisState.progress * 100)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ResultView({ guide, onReset }: { guide: any; onReset: () => void }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const text = guide.export_markdown || JSON.stringify(guide, null, 2);
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExport = () => {
    const content = guide.export_markdown || JSON.stringify(guide, null, 2);
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `replication-guide-${guide.video_id}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{guide.title}</h1>
          <p className="text-[#a1a1aa] mt-1">{guide.summary}</p>
        </div>
        <div className="flex gap-2 shrink-0">
          <button
            onClick={onReset}
            className="px-4 py-2 rounded-lg border border-[#333] hover:border-[#fe2c55] text-sm transition-colors"
          >
            新分析
          </button>
          <button
            onClick={handleCopy}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-[#333] hover:border-[#fe2c55] text-sm transition-colors"
          >
            {copied ? <CheckCircle size={14} className="text-green-400" /> : <Copy size={14} />}
            {copied ? "已复制" : "复制指南"}
          </button>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-[#333] hover:border-[#fe2c55] text-sm transition-colors"
          >
            <Download size={14} />
            导出 Markdown
          </button>
        </div>
      </div>

      {/* Prompts */}
      {guide.prompts?.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">逆向提示词</h2>
          <div className="grid gap-4">
            {guide.prompts.map((prompt: any) => (
              <div key={prompt.type} className="bg-[#1a1a1a] border border-[#262626] rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium uppercase tracking-wider text-[#525252]">
                    {prompt.type}
                  </span>
                  <span className="text-xs text-[#a1a1aa]">
                    {Math.round(prompt.confidence * 100)}%
                  </span>
                </div>
                <pre className="mt-2 text-sm whitespace-pre-wrap text-[#d4d4d4] bg-[#111] rounded p-3 font-mono">
                  {prompt.prompt}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Patterns */}
      {guide.patterns && (
        <div>
          <h2 className="text-lg font-semibold mb-3">爆款模式</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-[#1a1a1a] border border-[#262626] rounded-lg p-4">
              <p className="text-xs text-[#525252]">结构</p>
              <p className="text-sm mt-1">
                {Array.isArray(guide.patterns.structure) ? guide.patterns.structure.join(" → ") : guide.patterns.structure}
              </p>
            </div>
            <div className="bg-[#1a1a1a] border border-[#262626] rounded-lg p-4">
              <p className="text-xs text-[#525252]">节奏</p>
              <p className="text-sm mt-1">{guide.patterns.pacing}</p>
            </div>
            <div className="bg-[#1a1a1a] border border-[#262626] rounded-lg p-4">
              <p className="text-xs text-[#525252]">视觉风格</p>
              <p className="text-sm mt-1">{guide.patterns.visual_style}</p>
            </div>
            <div className="bg-[#1a1a1a] border border-[#262626] rounded-lg p-4">
              <p className="text-xs text-[#525252]">配乐建议</p>
              <p className="text-sm mt-1">{guide.patterns.music_suggestion}</p>
            </div>
          </div>
        </div>
      )}

      {/* Segments */}
      {guide.segments?.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">
            分镜表 ({guide.segments.length} 段)
          </h2>
          <div className="space-y-4">
            {guide.segments.map((seg: any) => (
              <div key={seg.index} className="bg-[#1a1a1a] border border-[#262626] rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-[#a1a1aa]">
                    段 {seg.index} ({Number(seg.time_range?.[0]).toFixed(1)}s - {Number(seg.time_range?.[1]).toFixed(1)}s)
                  </span>
                  <span className="text-xs text-[#525252]">{seg.shot_type}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-[#525252]">运镜</p>
                    <p>{seg.camera_movement}</p>
                  </div>
                  <div>
                    <p className="text-[#525252]">节奏</p>
                    <p>{seg.rhythm}</p>
                  </div>
                </div>
                <p className="text-sm text-[#d4d4d4] mt-2">{seg.visual_description}</p>
                {seg.technique && (
                  <p className="text-sm text-[#525252] mt-1">
                    <span className="font-medium">拍摄技巧: </span>
                    {seg.technique}
                  </p>
                )}
                {seg.notes && (
                  <p className="text-sm text-[#525252] mt-1">
                    <span className="font-medium">复刻要点: </span>
                    {seg.notes}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reusable Template - safe rendering via pre tag */}
      {guide.patterns?.reusable_template && (
        <div>
          <h2 className="text-lg font-semibold mb-3">可复用拍摄模板</h2>
          <div className="bg-[#1a1a1a] border border-[#262626] rounded-lg p-4">
            <pre className="max-w-none text-sm whitespace-pre-wrap font-mono text-[#d4d4d4]">
              {guide.patterns.reusable_template}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
