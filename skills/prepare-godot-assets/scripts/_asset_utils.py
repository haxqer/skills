#!/usr/bin/env python3
"""Shared, dependency-free asset inspection helpers."""

from __future__ import annotations

import hashlib
import re
import struct
import wave
from pathlib import Path
from typing import Any


FORMAT_BY_EXTENSION = {
    # Images
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".webp": "webp",
    ".bmp": "bmp",
    ".tga": "tga",
    ".svg": "svg",
    ".gif": "gif",
    ".tif": "tiff",
    ".tiff": "tiff",
    ".psd": "psd",
    ".ase": "aseprite",
    ".aseprite": "aseprite",
    ".exr": "exr",
    ".hdr": "hdr",
    ".dds": "dds",
    ".ktx": "ktx",
    ".ktx2": "ktx2",
    # Audio and video
    ".wav": "wav",
    ".ogg": "ogg",
    ".mp3": "mp3",
    ".flac": "flac",
    ".aac": "aac",
    ".m4a": "m4a",
    ".ogv": "ogv",
    ".mp4": "mp4",
    ".webm": "webm",
    ".mov": "mov",
    ".mkv": "mkv",
    ".avi": "avi",
    # Models
    ".gltf": "gltf",
    ".glb": "glb",
    ".obj": "obj",
    ".fbx": "fbx",
    ".dae": "dae",
    ".blend": "blend",
    ".stl": "stl",
    ".ply": "ply",
    # Fonts
    ".ttf": "ttf",
    ".otf": "otf",
    ".woff": "woff",
    ".woff2": "woff2",
    # Godot and data
    ".tscn": "tscn",
    ".scn": "scn",
    ".tres": "tres",
    ".res": "res",
    ".gdshader": "gdshader",
    ".gd": "gdscript",
    ".json": "json",
    ".jsonl": "jsonl",
    ".csv": "csv",
    ".tsv": "tsv",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".xml": "xml",
    ".txt": "text",
    ".md": "markdown",
    # Packages and potentially executable content
    ".zip": "zip",
    ".rar": "rar",
    ".7z": "7z",
    ".gz": "gzip",
    ".tar": "tar",
    ".exe": "executable",
    ".dll": "executable",
    ".so": "executable",
    ".dylib": "executable",
    ".app": "executable",
    ".bat": "script",
    ".cmd": "script",
    ".ps1": "script",
    ".sh": "script",
    ".py": "script",
    ".js": "script",
}

MEDIA_BY_FORMAT = {
    **{
        key: "image"
        for key in (
            "png",
            "jpeg",
            "webp",
            "bmp",
            "tga",
            "svg",
            "gif",
            "tiff",
            "psd",
            "aseprite",
            "exr",
            "hdr",
            "dds",
            "ktx",
            "ktx2",
        )
    },
    **{key: "audio" for key in ("wav", "ogg", "mp3", "flac", "aac", "m4a")},
    **{key: "video" for key in ("ogv", "mp4", "webm", "mov", "mkv", "avi")},
    **{
        key: "model"
        for key in ("gltf", "glb", "obj", "fbx", "dae", "blend", "stl", "ply")
    },
    **{key: "font" for key in ("ttf", "otf", "woff", "woff2")},
    **{key: "godot-resource" for key in ("tscn", "scn", "tres", "res")},
    **{key: "code" for key in ("gdshader", "gdscript", "script", "executable")},
    **{
        key: "data"
        for key in ("json", "jsonl", "csv", "tsv", "yaml", "xml", "text", "markdown")
    },
    **{key: "archive" for key in ("zip", "rar", "7z", "gzip", "tar")},
}

GODOT_IMPORTABLE = {
    "png",
    "jpeg",
    "webp",
    "bmp",
    "tga",
    "exr",
    "hdr",
    "dds",
    "ktx",
    "wav",
    "ogg",
    "mp3",
    "ogv",
    "gltf",
    "glb",
    "obj",
    "ttf",
    "otf",
    "woff",
    "woff2",
}
GODOT_CONDITIONAL = {"svg", "ktx2", "fbx", "dae", "blend"}
GODOT_NATIVE_REVIEW = {"tscn", "scn", "tres", "res", "gdshader", "gdscript"}
CONVERTIBLE = {
    "gif",
    "tiff",
    "psd",
    "aseprite",
    "flac",
    "aac",
    "m4a",
    "mp4",
    "webm",
    "mov",
    "mkv",
    "avi",
    "stl",
    "ply",
}
REVIEW_ONLY = {
    "json",
    "jsonl",
    "csv",
    "tsv",
    "yaml",
    "xml",
    "text",
    "markdown",
    "zip",
    "rar",
    "7z",
    "gzip",
    "tar",
}
QUARANTINE = {"executable", "script"}
MAGIC_REQUIRED = {
    "png",
    "jpeg",
    "webp",
    "bmp",
    "gif",
    "tiff",
    "psd",
    "exr",
    "hdr",
    "dds",
    "ktx",
    "ktx2",
    "wav",
    "ogg",
    "mp3",
    "flac",
    "glb",
    "ttf",
    "otf",
    "woff",
    "woff2",
    "zip",
    "rar",
    "7z",
    "gzip",
    "executable",
}

TOKEN_RE = re.compile(r"[a-z0-9]+")
SVG_NUMBER_RE = re.compile(
    r"(?:^|\s)(width|height)\s*=\s*['\"]\s*([0-9.]+)", re.IGNORECASE
)
SVG_VIEWBOX_RE = re.compile(
    r"viewBox\s*=\s*['\"]\s*[-+0-9.eE]+[ ,]+[-+0-9.eE]+[ ,]+([-+0-9.eE]+)[ ,]+([-+0-9.eE]+)",
    re.IGNORECASE,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def detect_magic(head: bytes) -> str | None:
    stripped = head.lstrip()
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return "webp"
    if head.startswith(b"RIFF") and head[8:12] == b"WAVE":
        return "wav"
    if head.startswith(b"BM"):
        return "bmp"
    if head.startswith((b"II*\x00", b"MM\x00*")):
        return "tiff"
    if head.startswith(b"8BPS"):
        return "psd"
    if head.startswith(b"\x76\x2f\x31\x01"):
        return "exr"
    if head.startswith((b"#?RADIANCE", b"#?RGBE")):
        return "hdr"
    if head.startswith(b"DDS "):
        return "dds"
    if head.startswith(b"\xabKTX 11\xbb\r\n\x1a\n"):
        return "ktx"
    if head.startswith(b"\xabKTX 20\xbb\r\n\x1a\n"):
        return "ktx2"
    if head.startswith(b"OggS"):
        return "ogg"
    if head.startswith(b"fLaC"):
        return "flac"
    if head.startswith(b"ID3") or (
        len(head) > 2 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0
    ):
        return "mp3"
    if head.startswith(b"glTF"):
        return "glb"
    if head.startswith(b"\x00\x01\x00\x00"):
        return "ttf"
    if head.startswith(b"OTTO"):
        return "otf"
    if head.startswith(b"wOFF"):
        return "woff"
    if head.startswith(b"wOF2"):
        return "woff2"
    if head.startswith(b"PK\x03\x04"):
        return "zip"
    if head.startswith(b"Rar!\x1a\x07"):
        return "rar"
    if head.startswith(b"7z\xbc\xaf\x27\x1c"):
        return "7z"
    if head.startswith(b"\x1f\x8b"):
        return "gzip"
    if head.startswith(b"MZ") or head.startswith(b"\x7fELF"):
        return "executable"
    if head[:4] in {b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xca\xfe\xba\xbe"}:
        return "executable"
    lowered = stripped[:4096].lower()
    if lowered.startswith(b"<svg") or b"<svg" in lowered[:1024]:
        return "svg"
    return None


def extension_matches(extension: str, detected_format: str) -> bool:
    expected = FORMAT_BY_EXTENSION.get(extension.lower())
    if expected == "ogv" and detected_format == "ogg":
        return True
    return expected == detected_format


def godot_status(asset_format: str | None) -> tuple[str, str]:
    if asset_format in GODOT_IMPORTABLE:
        return "importable", "copy"
    if asset_format in GODOT_CONDITIONAL:
        return "conditional", "inspect-and-import-or-convert"
    if asset_format in GODOT_NATIVE_REVIEW:
        return "review", "inspect-active-content"
    if asset_format in CONVERTIBLE:
        return "convert", "convert"
    if asset_format in REVIEW_ONLY:
        return "review", "inspect-or-extract"
    if asset_format in QUARANTINE:
        return "quarantine", "do-not-import"
    return "unsupported", "manual-review"


def image_dimensions(path: Path, asset_format: str, head: bytes) -> dict[str, Any]:
    try:
        if asset_format == "png" and len(head) >= 24:
            width, height = struct.unpack(">II", head[16:24])
            return {"width": width, "height": height}
        if asset_format == "gif" and len(head) >= 10:
            width, height = struct.unpack("<HH", head[6:10])
            return {"width": width, "height": height}
        if asset_format == "bmp" and len(head) >= 26:
            width, height = struct.unpack("<ii", head[18:26])
            return {"width": abs(width), "height": abs(height)}
        if asset_format == "jpeg":
            return _jpeg_dimensions(path)
        if asset_format == "webp":
            return _webp_dimensions(head)
        if asset_format == "svg":
            text = head.decode("utf-8", errors="ignore")
            values = {
                key.lower(): float(value) for key, value in SVG_NUMBER_RE.findall(text)
            }
            if "width" in values and "height" in values:
                return {"width": values["width"], "height": values["height"]}
            match = SVG_VIEWBOX_RE.search(text)
            if match:
                return {
                    "width": float(match.group(1)),
                    "height": float(match.group(2)),
                    "from_viewbox": True,
                }
    except (OSError, ValueError, struct.error):
        return {}
    return {}


def _jpeg_dimensions(path: Path) -> dict[str, int]:
    with path.open("rb") as handle:
        if handle.read(2) != b"\xff\xd8":
            return {}
        while True:
            marker_start = handle.read(1)
            if not marker_start:
                return {}
            if marker_start != b"\xff":
                continue
            marker = handle.read(1)
            while marker == b"\xff":
                marker = handle.read(1)
            if marker in {b"\xd8", b"\xd9"}:
                continue
            length_raw = handle.read(2)
            if len(length_raw) != 2:
                return {}
            length = struct.unpack(">H", length_raw)[0]
            if marker and marker[0] in {
                0xC0,
                0xC1,
                0xC2,
                0xC3,
                0xC5,
                0xC6,
                0xC7,
                0xC9,
                0xCA,
                0xCB,
                0xCD,
                0xCE,
                0xCF,
            }:
                segment = handle.read(5)
                if len(segment) != 5:
                    return {}
                height, width = struct.unpack(">HH", segment[1:5])
                return {"width": width, "height": height}
            handle.seek(max(0, length - 2), 1)


def _webp_dimensions(head: bytes) -> dict[str, int]:
    if len(head) < 30 or head[:4] != b"RIFF" or head[8:12] != b"WEBP":
        return {}
    chunk = head[12:16]
    if chunk == b"VP8X" and len(head) >= 30:
        width = 1 + int.from_bytes(head[24:27], "little")
        height = 1 + int.from_bytes(head[27:30], "little")
        return {"width": width, "height": height}
    if chunk == b"VP8L" and len(head) >= 25:
        bits = int.from_bytes(head[21:25], "little")
        return {"width": (bits & 0x3FFF) + 1, "height": ((bits >> 14) & 0x3FFF) + 1}
    if chunk == b"VP8 " and len(head) >= 30 and head[23:26] == b"\x9d\x01\x2a":
        width, height = struct.unpack("<HH", head[26:30])
        return {"width": width & 0x3FFF, "height": height & 0x3FFF}
    return {}


def inspect_file(path: Path) -> dict[str, Any]:
    size = path.stat().st_size
    with path.open("rb") as handle:
        head = handle.read(65536)
    extension = path.suffix.lower()
    extension_format = FORMAT_BY_EXTENSION.get(extension)
    magic_format = detect_magic(head)
    asset_format = magic_format or extension_format
    if extension_format == "ogv" and magic_format == "ogg":
        asset_format = "ogv"
    media_type = MEDIA_BY_FORMAT.get(asset_format or "", "unknown")
    status, action = godot_status(asset_format)
    issues: list[str] = []
    if size == 0:
        issues.append("empty-file")
        status, action = "quarantine", "do-not-import"
    if (
        magic_format
        and extension_format
        and not extension_matches(extension, magic_format)
    ):
        issues.append(f"extension-mismatch:{extension_format}-vs-{magic_format}")
    if extension_format in MAGIC_REQUIRED and magic_format is None:
        issues.append("signature-missing")
    if extension_format is None:
        issues.append("unknown-extension")
    if status == "convert":
        issues.append("conversion-required")
    elif status == "conditional":
        issues.append("toolchain-dependent-import")
    elif status == "unsupported":
        issues.append("unsupported-or-unknown-format")
    elif asset_format in QUARANTINE:
        issues.append("active-or-unsafe-content")

    technical: dict[str, Any] = {}
    if media_type == "image" and asset_format:
        technical.update(image_dimensions(path, asset_format, head))
        if asset_format in {"png", "jpeg", "webp", "bmp", "gif"} and not technical.get(
            "width"
        ):
            issues.append("decode-metadata-failed")
    elif asset_format == "wav":
        try:
            with wave.open(str(path), "rb") as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                technical.update(
                    {
                        "channels": wav.getnchannels(),
                        "sample_rate": rate,
                        "sample_width_bits": wav.getsampwidth() * 8,
                        "duration_seconds": round(frames / rate, 6) if rate else None,
                    }
                )
        except (OSError, EOFError, wave.Error):
            issues.append("decode-failed")

    if {"signature-missing", "decode-metadata-failed", "decode-failed"} & set(issues):
        status, action = "quarantine", "do-not-import"

    return {
        "extension": extension,
        "extension_format": extension_format,
        "detected_format": asset_format,
        "magic_format": magic_format,
        "media_type": media_type,
        "godot_status": status,
        "recommended_action": action,
        "size_bytes": size,
        "sha256": sha256_file(path),
        "technical": technical,
        "issues": sorted(set(issues)),
    }


def path_tokens(path: str) -> list[str]:
    ignored = {
        "assets",
        "asset",
        "images",
        "image",
        "files",
        "file",
        "raw",
        "final",
        "copy",
        "new",
    }
    return [
        token
        for token in TOKEN_RE.findall(path.lower())
        if token not in ignored and not token.isdigit()
    ]


def category_hint(path: str, media_type: str) -> str:
    tokens = set(path_tokens(path))
    if media_type == "audio":
        if tokens & {"music", "bgm", "song", "theme"}:
            return "audio/music"
        if tokens & {"voice", "dialogue", "dialog", "speech", "vo"}:
            return "audio/voice"
        if tokens & {"ambience", "ambient", "atmosphere"}:
            return "audio/ambience"
        return "audio/sfx"
    if media_type == "font":
        return "fonts"
    if media_type == "model":
        if tokens & {"character", "characters", "player", "enemy", "npc", "creature"}:
            return "models/characters"
        if tokens & {"environment", "building", "terrain", "level"}:
            return "models/environments"
        return "models/props"
    if media_type == "image":
        if tokens & {
            "ui",
            "hud",
            "button",
            "buttons",
            "panel",
            "cursor",
            "icon",
            "icons",
        }:
            return "art/ui"
        if tokens & {"vfx", "fx", "effect", "effects", "particle", "particles"}:
            return "art/vfx"
        if tokens & {"tile", "tiles", "tileset", "terrain", "autotile"}:
            return "art/environments/tilesets"
        if tokens & {"background", "backgrounds", "backdrop", "skybox", "parallax"}:
            return "art/environments/backgrounds"
        if tokens & {
            "character",
            "characters",
            "player",
            "enemy",
            "npc",
            "portrait",
            "sprite",
        }:
            return "art/characters"
        if tokens & {
            "texture",
            "textures",
            "albedo",
            "normal",
            "roughness",
            "metallic",
            "orm",
        }:
            return "materials/textures"
        return "art/props"
    if media_type == "godot-resource":
        return "godot/resources"
    if media_type == "data":
        return "data"
    return f"unclassified/{media_type}"
