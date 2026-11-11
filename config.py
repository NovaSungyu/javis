"""Configuration with no third-party dependencies or import-time disk writes."""
from dataclasses import dataclass
from pathlib import Path
import os
import re

ROOT = Path(__file__).resolve().parent


def read_env(path):
    values = {}
    if not path.exists():
        return values
    for number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.removeprefix("export ").partition("=")
        key, value = key.strip(), value.strip()
        if not sep or not re.fullmatch(r"[A-Z_][A-Z0-9_]*", key):
            raise ValueError(f".env {number}번째 줄 형식이 잘못되었습니다.")
        if value.startswith(("'", '"')):
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError(f".env {number}번째 줄 따옴표를 확인하세요.")
            value = value[1:-1]
        if "\\n" in value:
            raise ValueError(f".env {number}번째 줄: 문자 \\n 대신 실제 줄바꿈을 사용하세요.")
        values[key] = value
    return values


@dataclass(frozen=True)
class Config:
    data_dir: Path
    provider: str = "gemini"
    gemini_key: str = ""
    groq_key: str = ""
    gemini_model: str = "auto"
    groq_model: str = "llama-3.3-70b-versatile"
    name: str = "J.A.R.V.I.S."

    @classmethod
    def load(cls, root=ROOT, environ=None):
        env = {**read_env(root / ".env"), **(os.environ if environ is None else environ)}
        gemini = env.get("GEMINI_API_KEY", "").strip()
        groq = env.get("GROQ_API_KEY", "").strip()
        # Accept the original project's Groq key convention.
        if gemini.startswith("gsk_") and not groq:
            groq, gemini = gemini, ""
        provider = env.get("AI_PROVIDER", "auto").strip().lower()
        if provider == "auto":
            provider = "gemini" if gemini or not groq else "groq"
        if provider not in ("gemini", "groq"):
            raise ValueError("AI_PROVIDER는 auto, gemini, groq 중 하나여야 합니다.")
        data = Path(env.get("JARVIS_DATA_DIR", "data")).expanduser()
        if not data.is_absolute():
            data = root / data
        return cls(
            data, provider, gemini, groq,
            env.get("GEMINI_MODEL", env.get("JARVIS_MODEL", "auto")).strip() or "auto",
            env.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip(),
            env.get("JARVIS_NAME", "J.A.R.V.I.S.").strip(),
        )
