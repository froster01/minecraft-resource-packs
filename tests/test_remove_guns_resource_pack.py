import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "remove_guns_resource_pack.py"

BANNED_PATHS = (
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
    "assets/minecraft/equipment/ct_armored.json",
    "assets/minecraft/equipment/ct_normal.json",
    "assets/minecraft/equipment/t_armored.json",
    "assets/minecraft/equipment/t_normal.json",
)


def write_json(root: Path, relative_path: str, value: object) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def write_bytes(root: Path, relative_path: str, value: bytes = b"asset") -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def zip_tree(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source).as_posix())


class RemoveGunsResourcePackTests(unittest.TestCase):
    def make_source_pack(self, root: Path) -> Path:
        pack = root / "source"
        write_json(pack, "pack.mcmeta", {"pack": {"pack_format": 75, "description": "test"}})

        retained = {
            "assets/backpacks/keep.bin": b"backpacks",
            "assets/moldomre/keep.bin": b"vanilla-plus",
            "assets/tooltrims/keep.bin": b"tool-trims",
            "assets/invminecarts/keep.bin": b"minecarts",
            "assets/minecraft/textures/item/models/book_blue.png": b"book",
            "assets/minecraft/textures/item/weapons/spear_iron.png": b"spear",
        }
        for relative_path, content in retained.items():
            write_bytes(pack, relative_path, content)

        for relative_path in BANNED_PATHS:
            if Path(relative_path).suffix:
                write_json(pack, relative_path, {"gun": True})
            else:
                write_bytes(pack, f"{relative_path}/gun-asset.bin")

        write_json(
            pack,
            "assets/minecraft/font/default.json",
            {
                "providers": [
                    {"type": "bitmap", "file": "guns:font/gun0.png", "chars": ["A"]},
                    {"type": "bitmap", "file": "moldomre:font/keep.png", "chars": ["B"]},
                ]
            },
        )
        write_json(
            pack,
            "assets/minecraft/atlases/blocks.json",
            {
                "sources": [
                    {"type": "minecraft:directory", "source": "block", "prefix": "block/"},
                    {"type": "directory", "source": "guns", "prefix": "guns/"},
                    {"type": "directory", "source": "defusal", "prefix": "defusal/"},
                ]
            },
        )
        write_json(
            pack,
            "assets/minecraft/lang/en_us.json",
            {
                "thepa.item.name.gun_0": "Revolver",
                "death.attack.shot": "%1$s was shot",
                "item.minecraft.knowledge_book": "Click to craft",
                "item.moldomre.blue_book": "Blue Book",
            },
        )
        write_json(
            pack,
            "assets/minecraft/sounds.json",
            {
                "mcgo.weapons.shotgunshot": {"sounds": ["mcgo/weapons/shotgunshot01"]},
                "random.eat": {"sounds": ["random/eat1"]},
                "block.note_block.harp": {"sounds": ["block/note_block/harp"]},
            },
        )

        source_zip = root / "source.zip"
        zip_tree(pack, source_zip)
        return source_zip

    def run_builder(self, source_zip: Path, output_zip: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--source",
                str(source_zip),
                "--output",
                str(output_zip),
            ],
            capture_output=True,
            text=True,
        )

    def test_build_removes_all_guns_content_and_preserves_other_packs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_zip = self.make_source_pack(root)
            output_zip = root / "without-guns.zip"

            result = self.run_builder(source_zip, output_zip)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(output_zip.exists())
            self.assertIn("sha1=", result.stdout.lower())

            extracted = root / "extracted"
            with zipfile.ZipFile(output_zip) as archive:
                archive.extractall(extracted)

            for relative_path in BANNED_PATHS:
                self.assertFalse((extracted / relative_path).exists(), relative_path)

            self.assertEqual((extracted / "assets/backpacks/keep.bin").read_bytes(), b"backpacks")
            self.assertEqual((extracted / "assets/moldomre/keep.bin").read_bytes(), b"vanilla-plus")
            self.assertEqual((extracted / "assets/tooltrims/keep.bin").read_bytes(), b"tool-trims")
            self.assertEqual((extracted / "assets/invminecarts/keep.bin").read_bytes(), b"minecarts")
            self.assertEqual(
                (extracted / "assets/minecraft/textures/item/models/book_blue.png").read_bytes(),
                b"book",
            )
            self.assertEqual(
                (extracted / "assets/minecraft/textures/item/weapons/spear_iron.png").read_bytes(),
                b"spear",
            )

            font = json.loads((extracted / "assets/minecraft/font/default.json").read_text("utf-8"))
            self.assertEqual(font["providers"][0]["file"], "moldomre:font/keep.png")
            atlas = json.loads((extracted / "assets/minecraft/atlases/blocks.json").read_text("utf-8"))
            self.assertEqual([source["source"] for source in atlas["sources"]], ["block"])
            language = json.loads((extracted / "assets/minecraft/lang/en_us.json").read_text("utf-8"))
            self.assertEqual(language, {"item.moldomre.blue_book": "Blue Book"})
            sounds = json.loads((extracted / "assets/minecraft/sounds.json").read_text("utf-8"))
            self.assertEqual(list(sounds), ["block.note_block.harp"])

            for path in extracted.rglob("*"):
                if path.is_file() and path.suffix in {".json", ".mcmeta"}:
                    json.loads(path.read_text("utf-8"))
                if path.is_file() and path.suffix in {".json", ".mcmeta", ".txt"}:
                    lowered = path.read_text("utf-8").lower()
                    for marker in ("guns:", "mcgo.", "mcgo/", "thepa.item"):
                        self.assertNotIn(marker, lowered, str(path))

    def test_rejects_zip_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_zip = root / "unsafe.zip"
            output_zip = root / "output.zip"
            with zipfile.ZipFile(source_zip, "w") as archive:
                archive.writestr("../escape.txt", "unsafe")

            result = self.run_builder(source_zip, output_zip)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsafe zip member", (result.stdout + result.stderr).lower())
            self.assertFalse((root / "escape.txt").exists())
            self.assertFalse(output_zip.exists())


if __name__ == "__main__":
    unittest.main()
