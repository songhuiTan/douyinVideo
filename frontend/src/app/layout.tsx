import "./globals.css";

export const metadata = {
  title: "TikTok 爆款复刻指南生成器",
  description: "上传爆款视频， AI 自动拆解为可执行的拍摄蓝图",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        <div className="min-h-screen bg-[#0a0a0a] text-white">
          <header className="border-b border-[#262626] px-6 py-4">
            <div className="max-w-5xl mx-auto flex items-center justify-between">
              <h1 className="text-xl font-bold">
                <span className="text-[#fe2c55]">TikTok</span>{" "}爆款复刻指南
              </h1>
              <p className="text-sm text-[#a1a1aa]">
                上传爆款视频， AI 拆解为可执行的拍摄蓝图
              </p>
            </div>
          </header>
          <main className="max-w-5xl mx-auto px-6 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
