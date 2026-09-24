from __future__ import annotations

import json
import re
import stat
from pathlib import Path


AUTH_COOKIE_NAMES = {
    "language", "csrftoken", "SPC_SI", "SPC_SEC_SI", "SPC_F", "SPC_CLIENTID",
    "SPC_ST", "SPC_U", "SPC_R_T_ID", "SPC_R_T_IV", "SPC_T_ID", "SPC_T_IV",
}


def _extract_cookie_string(text: str):
    patterns = [
        r"(?:-b|--cookie)\s+(['\"])(.*?)\1",
        r"(?:-H|--header)\s+(['\"])cookie:\s*(.*?)\1",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(2).replace("\\\n", "").strip()
    return None


def load_playwright_cookies(path: Path):
    """Read JSON, Netscape, raw Cookie header, or a pasted curl command.

    Only Shopee authentication/session cookies are imported. Values are never
    returned in logs by this module.
    """
    if not path.exists(): raise FileNotFoundError(path)
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        print("WARNING: cookie file is readable by other users; consider: chmod 600", path)
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    pairs = {}
    if text.startswith("["):
        payload = json.loads(text)
        for row in payload:
            if row.get("name") in AUTH_COOKIE_NAMES: pairs[row["name"]] = str(row["value"])
    elif "\t" in text and "# Netscape HTTP Cookie File" in text:
        for line in text.splitlines():
            if not line or line.startswith("#"): continue
            fields = line.split("\t")
            if len(fields) >= 7 and fields[5] in AUTH_COOKIE_NAMES: pairs[fields[5]] = fields[6]
    else:
        cookie_string = _extract_cookie_string(text) or text
        for part in cookie_string.split(";"):
            if "=" not in part: continue
            name, value = part.strip().split("=", 1)
            if name in AUTH_COOKIE_NAMES: pairs[name] = value
    required = {"SPC_ST", "SPC_U"}
    missing = required - set(pairs)
    if missing:
        raise ValueError(f"Cookie file does not contain required Shopee session cookies: {sorted(missing)}")
    return [{"name":name,"value":value,"domain":".shopee.vn","path":"/","secure":True,"sameSite":"Lax"} for name,value in pairs.items()]
