"""アプリケーション設定."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """環境変数ベースの設定."""

    app_name: str = "TrendVista AI"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]

    # BlueSky
    bsky_handle: str = ""
    bsky_password: str = ""

    # LLM
    llm_model_repo: str = "elyza/Llama-3-ELYZA-JP-8B-GGUF"
    llm_model_file: str = "Llama-3-ELYZA-JP-8B-q4_k_m.gguf"
    llm_n_ctx: int = 2048
    llm_n_threads: int = 4

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
