"""
Music Player, Telegram Voice Chat Bot
Copyright (c) 2021-present Asm Safone <https://github.com/AsmSafone>

Modified to add ArtistBots API support.
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


def _getenv(key: str, default: str = "") -> str:
    return os.environ.get(key, default) or default


class Config:
    def __init__(self) -> None:
        self.API_ID: str = _getenv("API_ID")
        self.API_HASH: str = _getenv("API_HASH")
        self.SESSION: str = _getenv("SESSION")
        self.BOT_TOKEN: str = _getenv("BOT_TOKEN")
        self.SUDOERS: list = [
            int(id) for id in _getenv("SUDOERS", " ").split() if id.isnumeric()
        ]
        if not self.SESSION or not self.API_ID or not self.API_HASH:
            print("ERROR: SESSION, API_ID and API_HASH is required!")
            quit(0)

        self.SPOTIFY: bool = False
        self.QUALITY: str = _getenv("QUALITY", "high").lower()
        self.PREFIXES: list = _getenv("PREFIX", "").split() or [""]
        self.LANGUAGE: str = _getenv("LANGUAGE", "en").lower()
        self.STREAM_MODE: str = (
            "audio"
            if _getenv("STREAM_MODE", "audio").lower() == "audio"
            else "video"
        )
        self.ADMINS_ONLY: bool = bool(_getenv("ADMINS_ONLY", "False"))
        self.SPOTIFY_CLIENT_ID: str = _getenv("SPOTIFY_CLIENT_ID")
        self.SPOTIFY_CLIENT_SECRET: str = _getenv("SPOTIFY_CLIENT_SECRET")

        # ── ArtistBots API ─────────────────────────────────────────────────────
        # API_URL       : رابط ArtistBots للصوت  (مثال: https://artistbots.onrender.com)
        # VIDEO_API_URL : رابط ArtistBots للفيديو (عادةً نفس API_URL)
        # API_KEYS      : مفاتيح API مفصولة بفاصلة (مثال: key1,key2,key3)
        # API_KEY       : مفتاح واحد (fallback إذا API_KEYS فارغ)
        self.API_URL: str = _getenv("API_URL").strip()
        self.VIDEO_API_URL: str = _getenv("VIDEO_API_URL", _getenv("API_URL")).strip()
        self.API_KEY: str = _getenv("API_KEY").strip()
        self.API_KEYS: List[str] = self._parse_api_keys()

    def _parse_api_keys(self) -> List[str]:
        """يقرأ API_KEYS (مفصولة بفاصلة) أو يرجع للـ API_KEY المفرد"""
        raw = _getenv("API_KEYS", "").strip()
        keys = [k.strip() for k in raw.split(",") if k.strip()] if raw else []
        if not keys and self.API_KEY:
            keys = [self.API_KEY]
        return keys


config = Config()
