from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # AI Services
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    anthropic_base_url: str = ""  # 自定义 Anthropic API endpoint

    # Vision Provider
    vision_provider: str = "zhipu"             # "gemini" | "zhipu"
    zhipu_api_key: str = ""                     # 智谱 API key
    zhipu_vision_model: str = "glm-4.6v-flashx"   # glm-4.6v | glm-4.6v-flashx | glm-4.6v-flash

    # Storage
    upload_dir: Path = Path("./data/videos")
    max_video_size_mb: int = 500

    # Server
    backend_port: int = 8000
    frontend_port: int = 3000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def validate_api_keys(self):
        """启动时校验 API key 是否已配置"""
        missing = []
        if self.vision_provider == "gemini" and not self.gemini_api_key:
            missing.append("GEMINI_API_KEY")
        if self.vision_provider == "zhipu" and not self.zhipu_api_key:
            missing.append("ZHIPU_API_KEY")
        if not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY")
        if missing:
            raise ValueError(
                f"Missing API keys: {', '.join(missing)}. "
                f"Set them in .env file or environment variables."
            )


settings = Settings()
