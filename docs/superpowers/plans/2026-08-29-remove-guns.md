# Remove Guns Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove every Guns datapack and resource-pack component, publish a cache-safe `v1.0.14` asset, and point the live server at its verified URL and SHA-1.

**Architecture:** A standard-library Python builder will extract the configured `v1.0.12` ZIP into a temporary directory, delete a reviewed manifest of Guns-only paths, clean Guns entries from shared JSON files, validate retained content, and create `v1.0.14`. Unit tests use a synthetic resource pack; an integration run validates the actual 28 MB source artifact before any live change.

**Tech Stack:** Python 3 standard library, `unittest`, ZIP/JSON/SHA-1 validation, Git/GitHub CLI, Crafty Controller through Chrome, Minecraft Paper commands.

---

## File Map

- Create `tools/remove_guns_resource_pack.py`: deterministic Guns removal, validation, ZIP creation, and SHA-1 reporting.
- Create `tests/test_remove_guns_resource_pack.py`: synthetic-pack regression tests that prove Guns content is removed and retained content survives.
- Modify `README.md`: document the new `v1.0.14` release URL and SHA-1 after publication.
- Produce outside Git: `outputs/server-resource-pack-backpackplus-v1.0.14.zip`: uploadable release artifact.
- Modify live `server.properties`: new resource-pack URL and SHA-1.
- Delete live `feraxis/datapacks/guns26-1v0-dp-admin-only-v2.zip`: the already-disabled culprit datapack.

### Task 1: Add failing resource-pack removal tests

**Files:**
- Create: `tests/test_remove_guns_resource_pack.py`

- [ ] **Step 1: Write the synthetic ZIP test**

Create a temporary resource pack containing `assets/guns`, gun item/model/sound/texture trees, shared font/atlas/lang/sound JSON entries, and representative retained files under `backpacks`, `moldomre`, `tooltrims`, and `invminecarts`. Invoke the not-yet-created builder as a subprocess and assert:

```python
result = subprocess.run(
    [sys.executable, str(SCRIPT), "--source", str(source_zip), "--output", str(output_zip)],
    capture_output=True,
    text=True,
)
self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
self.assertTrue(output_zip.exists())
```

After extracting the result, assert that all reviewed Guns roots and references are absent, all JSON parses, and retained sentinel files are byte-identical.

- [ ] **Step 2: Run the test and verify RED**

Run:

```powershell
python -m unittest tests.test_remove_guns_resource_pack -v
```

Expected: `FAIL` because `tools/remove_guns_resource_pack.py` does not exist and the subprocess exits non-zero.

- [ ] **Step 3: Commit the failing test**

```powershell
git add tests/test_remove_guns_resource_pack.py
git commit -m "test: define complete Guns resource removal"
```

### Task 2: Implement deterministic Guns removal

**Files:**
- Create: `tools/remove_guns_resource_pack.py`
- Test: `tests/test_remove_guns_resource_pack.py`

- [ ] **Step 1: Define the reviewed removal manifest**

Use normalized POSIX-style paths. Delete these complete Guns-only trees:

```python
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
```

Do not delete `assets/minecraft/textures/item/models` or `assets/minecraft/textures/item/weapons`; those are Vanilla+ book and weapon assets.

- [ ] **Step 2: Clean shared JSON without discarding retained entries**

Implement JSON transforms:

```python
def clean_font(data):
    data["providers"] = [
        provider for provider in data.get("providers", [])
        if "guns:" not in json.dumps(provider).lower()
    ]
    return data

def clean_block_atlas(data):
    gun_sources = {"3d", "blocks", "custom", "defusal", "gravitygun", "guns", "items"}
    data["sources"] = [
        source for source in data.get("sources", [])
        if source.get("source", "").split("/")[0].lower() not in gun_sources
    ]
    return data

def clean_language(data):
    gun_keys = {
        "death.attack.shot", "death.attack.shot.item",
        "death.attack.pulse", "death.attack.pulse.item",
        "item.minecraft.knowledge_book",
    }
    return {
        key: value for key, value in data.items()
        if not key.startswith("thepa.") and key not in gun_keys
    }

def clean_sounds(data):
    gun_keys = {"entity.arrow.hit", "random.eat"}
    return {
        key: value for key, value in data.items()
        if not key.startswith("mcgo.") and key not in gun_keys
    }
```

Write transformed JSON with UTF-8, two-space indentation, and a final newline. Delete a transformed shared file only if its top-level provider/list/object becomes empty.

- [ ] **Step 3: Implement extraction, validation, and deterministic ZIP output**

The CLI must:

```python
parser.add_argument("--source", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
```

Then:

1. Reject source ZIP entries containing absolute paths or `..` traversal.
2. Extract into `TemporaryDirectory`.
3. Apply `DELETE_TREES`, `DELETE_FILES`, and shared JSON transforms.
4. Parse every remaining `.json` and `.mcmeta` file with `json.load`.
5. Reject remaining paths or text containing `assets/guns`, `guns:`, `mcgo.`, `mcgo/`, or `thepa.item`.
6. Require `pack.mcmeta`, `assets/backpacks`, `assets/moldomre`, `assets/tooltrims`, and `assets/invminecarts`.
7. Write files in sorted order with a fixed ZIP timestamp and `ZIP_DEFLATED` compression.
8. Print file count, removed path count, output byte size, and lowercase SHA-1.

- [ ] **Step 4: Run tests and verify GREEN**

```powershell
python -m unittest tests.test_remove_guns_resource_pack -v
```

Expected: all tests `ok`, followed by `OK`.

- [ ] **Step 5: Commit the builder**

```powershell
git add tools/remove_guns_resource_pack.py
git commit -m "feat: build resource pack without Guns assets"
```

### Task 3: Build and validate the real `v1.0.14` artifact

**Files:**
- Read: `work/guns-removal-analysis/server-resource-pack-backpackplus-v1.0.12.zip`
- Create: `outputs/server-resource-pack-backpackplus-v1.0.14.zip`

- [ ] **Step 1: Prove the source ZIP is the configured artifact**

```powershell
Get-FileHash -Algorithm SHA1 work/guns-removal-analysis/server-resource-pack-backpackplus-v1.0.12.zip
```

Expected: `3885DFCFD993B3C58D051FD600B92ECEEBA77AB9`.

- [ ] **Step 2: Build the new ZIP**

```powershell
python work/minecraft-resource-packs-deploy/tools/remove_guns_resource_pack.py `
  --source work/guns-removal-analysis/server-resource-pack-backpackplus-v1.0.12.zip `
  --output outputs/server-resource-pack-backpackplus-v1.0.14.zip
```

Expected: exit 0 and a printed lowercase SHA-1.

- [ ] **Step 3: Independently inspect the ZIP**

Extract to `work/guns-removal-analysis/verify-v1.0.14`. Run:

```powershell
rg -n -i 'guns:|assets/guns|mcgo[./]|thepa\.item|defusal|gun_\d|bullet_\d' work/guns-removal-analysis/verify-v1.0.14
```

Expected: no Guns matches. Then parse every `.json` and `.mcmeta` and verify the retained namespace sentinels.

- [ ] **Step 4: Run the full test suite and Git checks**

```powershell
python -m unittest discover -s tests -v
git diff --check
git status --short
```

Expected: all tests pass, no whitespace errors, only intentional README changes if any.

### Task 4: Publish GitHub changes and `v1.0.14`

**Files:**
- Modify: `README.md`
- Upload: `outputs/server-resource-pack-backpackplus-v1.0.14.zip`

- [ ] **Step 1: Add the new URL and SHA-1 to README**

Document:

```text
https://github.com/froster01/minecraft-resource-packs/releases/download/v1.0.10/server-resource-pack-backpackplus-v1.0.14.zip
```

and the exact SHA-1 printed by Task 3.

- [ ] **Step 2: Re-run tests and commit**

```powershell
python -m unittest discover -s tests -v
git diff --check
git add README.md tools/remove_guns_resource_pack.py tests/test_remove_guns_resource_pack.py
git commit -m "release: remove Guns assets from server resource pack"
```

- [ ] **Step 3: Push commits and upload the new release asset**

```powershell
git push origin main
gh release upload v1.0.10 outputs/server-resource-pack-backpackplus-v1.0.14.zip `
  --repo froster01/minecraft-resource-packs
```

Expected: both commands exit 0 and `gh release view v1.0.10` lists `server-resource-pack-backpackplus-v1.0.14.zip`.

- [ ] **Step 4: Verify GitHub delivery independently**

Download the published asset to a fresh temporary path. Compute SHA-1 and compare it byte-for-byte with the local artifact. Expected: identical SHA-1 and file size.

### Task 5: Remove Guns from the live server and update properties

**Files:**
- Delete: live `feraxis/datapacks/guns26-1v0-dp-admin-only-v2.zip`
- Modify: live `server.properties`

- [ ] **Step 1: Verify the exact live targets in Crafty**

Open the server file manager in Chrome. Confirm the Guns ZIP exact filename and confirm `server.properties` still points to `v1.0.12` with SHA-1 `3885dfcfd993b3c58d051fd600b92eceeba77ab9`.

- [ ] **Step 2: Delete only the Guns datapack ZIP**

Use Crafty's delete action on `feraxis/datapacks/guns26-1v0-dp-admin-only-v2.zip`. Do not alter any other datapack or world file.

- [ ] **Step 3: Update resource-pack properties**

Set:

```properties
resource-pack=https\://github.com/froster01/minecraft-resource-packs/releases/download/v1.0.10/server-resource-pack-backpackplus-v1.0.14.zip
```

Set `resource-pack-sha1` to the lowercase output of:

```powershell
(Get-FileHash -Algorithm SHA1 outputs/server-resource-pack-backpackplus-v1.0.14.zip).Hash.ToLowerInvariant()
```

Preserve every other property exactly.

- [ ] **Step 4: Restart through Crafty**

Announce the restart to online players, restart once, and wait for the normal server-ready console message.

### Task 6: Verify the live rollout

- [ ] **Step 1: Verify server configuration after restart**

Re-open `server.properties` and confirm the saved URL and SHA-1 exactly match the independently downloaded GitHub asset.

- [ ] **Step 2: Verify the Guns datapack is absent**

Confirm the file manager no longer lists the ZIP. Run `datapack list` and confirm no enabled or available Guns pack appears.

- [ ] **Step 3: Verify health and TPS**

Run the server's TPS/MSPT command after startup settles. Expected: 20 TPS and no Guns datapack errors in startup logs.

- [ ] **Step 4: Record final evidence**

Capture the Git commit, release URL, SHA-1, deleted server filename, restart result, datapack-list result, and TPS/MSPT result in the shared workspace handoff.

- [ ] **Step 5: Roll back only if delivery verification fails**

If Minecraft rejects the new pack, restore the previous `v1.0.12` URL and SHA-1 `3885dfcfd993b3c58d051fd600b92eceeba77ab9`, restart once, and report the failed verification evidence. Do not restore or enable the Guns datapack.
