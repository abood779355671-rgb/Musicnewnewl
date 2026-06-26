"""
Music Player, Telegram Voice Chat Bot
Copyright (c) 2021-present Asm Safone <https://github.com/AsmSafone>

Modified to use ArtistBots API for downloading instead of yt-dlp direct streaming.
"""

import os
import asyncio
from datetime import timedelta
from aiohttp import ClientSession
from pyrogram.types import User, Message
from typing import Dict, Tuple, Union, Optional
from core.artistbots import download_via_api, is_api_configured


class Song:
    def __init__(self, link: Union[str, dict], request_msg: Message) -> None:
        if isinstance(link, str):
            self.title: str = None
            self.duration: str = None
            self.thumb: str = None
            self.remote: str = None       # مسار الملف المحلي بعد التحميل
            self.source: str = link       # الرابط الأصلي
            self.headers: dict = None
            self.request_msg: Message = request_msg
            self.requested_by: User = request_msg.from_user
            self.parsed: bool = False
            self._retries: int = 0
            self._video_mode: bool = False
        elif isinstance(link, dict):
            self.parsed: bool = True
            self._retries: int = 0
            self.duration: str = "N/A"
            self.headers: dict = None
            self.thumb: str = "https://telegra.ph/file/820cac7cb7b1a025542e2.jpg"
            self._video_mode: bool = False
            for key, value in link.items():
                setattr(self, key, value)
            self.request_msg: Message = request_msg
            self.requested_by: User = request_msg.from_user

    async def parse(self, video: bool = False) -> Tuple[bool, str]:
        """
        يحلّل الرابط ويحمّل الملف.
        يستخدم ArtistBots API إذا كانت مضبوطة، وإلا يرجع للطريقة القديمة (yt-dlp).
        """
        if self.parsed:
            return (True, "ALREADY_PARSED")
        if self._retries >= 5:
            return (False, "MAX_RETRY_LIMIT_REACHED")

        self._video_mode = video

        # ── مسار 1: ArtistBots API ────────────────────────────────────────────
        if is_api_configured(video=video):
            file_path = await download_via_api(self.source, video=video)
            if file_path and os.path.exists(file_path):
                # نحتاج metadata (العنوان، المدة، الصورة) من yt-dlp بدون تحميل
                meta = await self._fetch_metadata(self.source)
                if meta:
                    self.title = self._escape(meta.get("title", "Unknown"))
                    duration_sec = meta.get("duration", 0)
                    self.duration = str(timedelta(seconds=int(duration_sec))) if duration_sec else "N/A"
                    self.thumb = meta.get("thumbnail", "https://telegra.ph/file/820cac7cb7b1a025542e2.jpg")
                else:
                    self.title = "Unknown"
                    self.duration = "N/A"
                    self.thumb = "https://telegra.ph/file/820cac7cb7b1a025542e2.jpg"

                self.remote = file_path   # مسار الملف المحلي
                self.headers = {}         # لا نحتاج headers مع ملف محلي
                self.parsed = True
                return (True, "PARSED_VIA_API")

        # ── مسار 2: yt-dlp fallback (الطريقة القديمة) ───────────────────────
        return await self._parse_ytdlp(video=video)

    async def _fetch_metadata(self, url: str) -> Optional[dict]:
        """يجلب metadata فقط من yt-dlp بدون تحميل (سريع)"""
        import json
        from shlex import quote
        from subprocess import PIPE

        try:
            process = await asyncio.create_subprocess_shell(
                f"yt-dlp --print-json --skip-download -f bestaudio/best {quote(url)}",
                stdout=PIPE,
                stderr=PIPE,
            )
            out, _ = await asyncio.wait_for(process.communicate(), timeout=30)
            if out:
                return json.loads(out.decode())
        except Exception:
            pass
        return None

    async def _parse_ytdlp(self, video: bool = False) -> Tuple[bool, str]:
        """الطريقة القديمة — yt-dlp streaming مباشر"""
        import json
        from shlex import quote
        from subprocess import PIPE

        fmt = "best" if video else "bestaudio/best"
        process = await asyncio.create_subprocess_shell(
            f"yt-dlp --print-json --skip-download -f {fmt} {quote(self.source)}",
            stdout=PIPE,
            stderr=PIPE,
        )
        out, _ = await process.communicate()
        try:
            data = json.loads(out.decode())
        except Exception:
            self._retries += 1
            return await self._parse_ytdlp(video=video)

        remote_url = data.get("url")
        thumb_url = data.get("thumbnail")
        headers = data.get("http_headers", {})

        if not remote_url:
            self._retries += 1
            return await self._parse_ytdlp(video=video)

        check_remote = await self.check_remote_url(remote_url, headers)
        if check_remote:
            self.title = self._escape(data.get("title", "Unknown"))
            duration_sec = data.get("duration", 0)
            self.duration = str(timedelta(seconds=int(duration_sec))) if duration_sec else "N/A"
            self.thumb = thumb_url or "https://telegra.ph/file/820cac7cb7b1a025542e2.jpg"
            self.remote = remote_url
            self.headers = headers
            self.parsed = True
            return (True, "PARSED_VIA_YTDLP")
        else:
            self._retries += 1
            return await self._parse_ytdlp(video=video)

    @staticmethod
    async def check_remote_url(path: str, headers: Optional[Dict[str, str]] = None) -> bool:
        try:
            session = ClientSession()
            response = await session.get(path, timeout=5, headers=headers)
            response.close()
            await session.close()
            return response.status == 200
        except Exception:
            return False

    @staticmethod
    def _escape(_title: str) -> str:
        title = _title
        for i in ["**", "__", "`", "~~", "--"]:
            title = title.replace(i, f"\\{i}")
        return title

    def to_dict(self) -> Dict[str, str]:
        return {"title": self.title, "source": self.source}
