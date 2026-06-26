"""
ArtistBots API Downloader
يحمّل الصوت/الفيديو عبر ArtistBots API بدلاً من yt-dlp مباشرة
"""

import os
import asyncio
import aiohttp
import re
from config import config

_YOUTUBE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")
_CHUNK_SIZE = 128 * 1024  # 128 KB

# ── Key rotation state ─────────────────────────────────────────────────────────
_api_key_index = 0
_api_key_lock = asyncio.Lock()
_api_session = None
_api_session_lock = asyncio.Lock()


def _extract_video_id(link: str) -> str:
    """استخراج video ID من رابط يوتيوب أو ID مباشر"""
    if not link:
        return ""
    s = link.strip()
    if _YOUTUBE_ID_RE.match(s):
        return s
    if "v=" in s:
        return s.split("v=")[-1].split("&")[0]
    last = s.split("/")[-1].split("?")[0]
    if _YOUTUBE_ID_RE.match(last):
        return last
    return ""


async def _next_api_key() -> str | None:
    """يرجع المفتاح التالي بنظام round-robin"""
    global _api_key_index
    keys = getattr(config, "API_KEYS", [])
    if not keys:
        return None
    async with _api_key_lock:
        key = keys[_api_key_index % len(keys)]
        _api_key_index = (_api_key_index + 1) % len(keys)
        return key


async def _get_session() -> aiohttp.ClientSession:
    """session مشترك لجميع الطلبات"""
    global _api_session
    if _api_session and not _api_session.closed:
        return _api_session
    async with _api_session_lock:
        if _api_session and not _api_session.closed:
            return _api_session
        timeout = aiohttp.ClientTimeout(total=600, sock_connect=20, sock_read=60)
        connector = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300, enable_cleanup_closed=True)
        _api_session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return _api_session


async def download_via_api(link: str, video: bool = False) -> str | None:
    """
    يحمّل الملف عبر ArtistBots API ويرجع مسار الملف المحلي.
    
    Parameters:
        link: رابط يوتيوب أو video ID
        video: True لتحميل فيديو، False لصوت فقط
    
    Returns:
        مسار الملف المحلي أو None عند الفشل
    """
    # تحقق من الإعدادات
    api_url = getattr(config, "API_URL", "") or ""
    video_api_url = getattr(config, "VIDEO_API_URL", "") or ""
    api_keys = getattr(config, "API_KEYS", [])

    base_url = video_api_url if video else api_url
    if not base_url or not api_keys:
        return None

    vid = _extract_video_id(link)
    if not vid:
        # قد يكون الرابط كاملاً وليس ID فقط
        vid = link.strip()

    file_ext = ".mp4" if video else ".mp3"
    out_path = f"downloads/{vid}{file_ext}"
    download_type = "video" if video else "audio"

    os.makedirs("downloads", exist_ok=True)
    
    # إذا الملف موجود مسبقاً أرجعه مباشرة
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return out_path

    api_key = await _next_api_key()
    if not api_key:
        return None

    params = {
        "url": vid,
        "type": download_type,
        "api_key": api_key,
    }

    try:
        session = await _get_session()
        endpoint = f"{base_url.rstrip('/')}/download"
        
        async with session.get(
            endpoint,
            params=params,
            timeout=aiohttp.ClientTimeout(total=300),
        ) as resp:
            if resp.status != 200:
                return None

            with open(out_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(_CHUNK_SIZE):
                    if not chunk:
                        break
                    f.write(chunk)

        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return out_path

        if os.path.exists(out_path):
            os.remove(out_path)
        return None

    except asyncio.TimeoutError:
        return None
    except Exception:
        return None


def is_api_configured(video: bool = False) -> bool:
    """تحقق هل API مضبوطة في الإعدادات"""
    api_keys = getattr(config, "API_KEYS", [])
    if not api_keys:
        return False
    if video:
        return bool(getattr(config, "VIDEO_API_URL", ""))
    return bool(getattr(config, "API_URL", ""))
