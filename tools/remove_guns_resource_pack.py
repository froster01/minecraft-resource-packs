#!/usr/bin/env python3
"""Build a server resource pack with every reviewed Guns asset removed."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Callable


DELETE_TREES = (
    "assets/guns",
    "assets/minecraft/items/ammo",
    "assets/minecraft/items/defusal",
    "assets/minecraft/items/guns",
    "assets/minecraft/items/misc",
    "assets/minecraft/models/item/defusal",
    "assets/minecraft/models/item/models",
    "assets/minecraft/sounds/mcgo",
    "assets/minecraft/sounds/temp",
    "assets/minecraft/textures/3d",
    "assets/minecraft/textures/blocks",
    "assets/minecraft/textures/custom",
    "assets/minecraft/textures/defusal",
    "assets/minecraft/textures/ggunz",
    "assets/minecraft/textures/gravitygun",
    "assets/minecraft/textures/guns",
    "assets/minecraft/textures/items",
    "assets/minecraft/textures/scopes",
    "assets/minecraft/textures/models/armor/tm",
    "assets/minecraft/textures/entity/equipment/humanoid/tm",
)

DELETE_FILES = (
    "assets/minecraft/equipment/ct_armored.json",
    "assets/minecraft/equipment/ct_normal.json",
    "assets/minecraft/equipment/t_armored.json",
    "assets/minecraft/equipment/t_normal.json",
    "assets/minecraft/textures/entity/equipment/humanoid/ct_armored.png",
    "assets/minecraft/textures/entity/equipment/humanoid/ct_normal.png",
    "assets/minecraft/textures/entity/equipment/humanoid/t_armored.png",
    "assets/minecraft/textures/entity/equipment/humanoid/t_normal.png",
)

GUN_MARKERS = ("guns:", "mcgo.", "mcgo/", "thepa.item")
REQUIRED_PATHS = (
    "pack.mcmeta",
    "assets/backpacks",
    "assets/moldomre",
    "assets/tooltrims",
    "assets/invminecarts",
)
FIXED_ZIP_TIMESTAMP = (2026, 8, 29, 0, 0, 0)


def clean_font(data: dict[str, Any]) -> dict[str, Any]:
    data["providers"] = [
        provider
        for provider in data.get("providers", [])
        if "guns:" not in json.dumps(provider).lower()
    ]
    return data


def clean_block_atlas(data: dict[str, Any]) -> dict[str, Any]:
    gun_sources = {"3d", "blocks", "custom", "defusal", "gravitygun", "guns", "items"}
    data["sources"] = [
        source
        for source in data.get("sources", [])
        if source.get("source", "").split("/")[0].lower() not in gun_sources
    ]
    return data


def clean_language(data: dict[str, Any]) -> dict[str, Any]:
    gun_keys = {
        "death.attack.shot",
        "death.attack.shot.item",
        "death.attack.pulse",
        "death.attack.pulse.item",
        "item.minecraft.knowledge_book",
    }
    return {
        key: value
        for key, value in data.items()
        if not key.startswith("thepa.") and key not in gun_keys
    }


def clean_sounds(data: dict[str, Any]) -> dict[str, Any]:
    gun_keys = {"entity.arrow.hit", "random.eat"}
    return {
        key: value
        for key, value in data.items()
        if not key.startswith("mcgo.") and key not in gun_keys
    }


JSON_TRANSFORMS: dict[str, tuple[Callable[[dict[str, Any]], dict[str, Any]], str]] = {
    "assets/minecraft/font/default.json": (clean_font, "providers"),
    "assets/minecraft/atlases/blocks.json": (clean_block_atlas, "sources"),
    "assets/minecraft/lang/en_us.json": (clean_language, "mapping"),
    "assets/minecraft/sounds.json": (clean_sounds, "mapping"),
}


def _safe_member_path(name: str) -> PurePosixPath:
    normalized = PurePosixPath(name.replace("\\", "/"))
    if (
        normalized.is_absolute()
        or ".." in normalized.parts
        or (normalized.parts and normalized.parts[0].endswith(":"))
    ):
        raise ValueError(f"Unsafe ZIP member: {name}")
    return normalized


def safe_extract(source_zip: Path, destination: Path) -> None:
    with zipfile.ZipFile(source_zip) as archive:
        for member in archive.infolist():
            relative = _safe_member_path(member.filename)
            if not relative.parts:
                continue
            target = destination.joinpath(*relative.parts)
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)


def remove_reviewed_paths(pack_root: Path) -> int:
    removed = 0
    for relative_path in DELETE_TREES:
        target = pack_root / relative_path
        if target.is_dir():
            removed += sum(1 for path in target.rglob("*") if path.is_file())
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
            removed += 1

    for relative_path in DELETE_FILES:
        target = pack_root / relative_path
        if target.exists():
            target.unlink()
            removed += 1
    return removed


def _is_empty_transformed(data: dict[str, Any], empty_kind: str) -> bool:
    if empty_kind == "providers":
        return not data.get("providers")
    if empty_kind == "sources":
        return not data.get("sources")
    return not data


def clean_shared_json(pack_root: Path) -> int:
    removed_entries = 0
    for relative_path, (transform, empty_kind) in JSON_TRANSFORMS.items():
        path = pack_root / relative_path
        if not path.exists():
            continue
        original = json.loads(path.read_text(encoding="utf-8"))
        before = len(original.get(empty_kind, [])) if empty_kind in {"providers", "sources"} else len(original)
        cleaned = transform(original)
        after = len(cleaned.get(empty_kind, [])) if empty_kind in {"providers", "sources"} else len(cleaned)
        removed_entries += before - after
        if _is_empty_transformed(cleaned, empty_kind):
            path.unlink()
        else:
            path.write_text(
                json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    return removed_entries


def validate_pack(pack_root: Path) -> None:
    missing = [relative_path for relative_path in REQUIRED_PATHS if not (pack_root / relative_path).exists()]
    if missing:
        raise ValueError(f"Missing required retained content: {', '.join(missing)}")

    leftovers = [relative_path for relative_path in (*DELETE_TREES, *DELETE_FILES) if (pack_root / relative_path).exists()]
    if leftovers:
        raise ValueError(f"Guns paths remain: {', '.join(leftovers)}")

    for path in sorted(pack_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(pack_root).as_posix().lower()
        if any(marker in relative for marker in GUN_MARKERS):
            raise ValueError(f"Guns marker remains in path: {relative}")
        if path.suffix.lower() in {".json", ".mcmeta"}:
            text = path.read_text(encoding="utf-8")
            json.loads(text)
            lowered = text.lower()
            marker = next((value for value in GUN_MARKERS if value in lowered), None)
            if marker:
                raise ValueError(f"Guns marker {marker!r} remains in {relative}")


def write_deterministic_zip(pack_root: Path, output_zip: Path) -> int:
    files = [path for path in sorted(pack_root.rglob("*")) if path.is_file()]
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(pack_root).as_posix()
            info = zipfile.ZipInfo(relative, FIXED_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return len(files)


def sha1_file(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_pack(source_zip: Path, output_zip: Path) -> tuple[int, int, str]:
    if not source_zip.is_file():
        raise FileNotFoundError(source_zip)
    if source_zip.resolve() == output_zip.resolve():
        raise ValueError("Source and output ZIP paths must differ")

    with tempfile.TemporaryDirectory(prefix="remove-guns-") as temporary_directory:
        pack_root = Path(temporary_directory) / "pack"
        pack_root.mkdir()
        safe_extract(source_zip, pack_root)
        removed = remove_reviewed_paths(pack_root)
        removed += clean_shared_json(pack_root)
        validate_pack(pack_root)
        file_count = write_deterministic_zip(pack_root, output_zip)

    return file_count, removed, sha1_file(output_zip)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    arguments = parse_args()
    file_count, removed, sha1 = build_pack(arguments.source, arguments.output)
    print(
        f"files={file_count} removed={removed} bytes={arguments.output.stat().st_size} sha1={sha1}"
    )


if __name__ == "__main__":
    main()
