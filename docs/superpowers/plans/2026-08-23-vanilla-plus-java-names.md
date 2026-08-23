# Vanilla+ Java English Names Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an English-only Java resource-pack patch for Vanilla+ names, remove the obsolete Bedrock export, and preserve the existing Paper datapack.

**Architecture:** Keep the server-side datapack in `datapacks/paper-26.2/` unchanged. Add a separately downloadable Java resource-pack ZIP containing only `pack.mcmeta` and the merged-language override `assets/minecraft/lang/en_us.json`; Java clients can layer it after the full Vanilla+ pack.

**Tech Stack:** Minecraft Java resource-pack ZIP, JSON, PowerShell validation, Git.

---

### Task 1: Remove the obsolete Bedrock export

**Files:**
- Delete: `bedrock/`

- [ ] **Step 1: Verify the deletion target is the repository Bedrock directory**

Run:

```powershell
$repo = 'C:\Users\Ferostzz\AppData\Local\Temp\minecraft-resource-packs-work-20260823\repo'
Resolve-Path (Join-Path $repo 'bedrock')
```

Expected: a path inside the isolated repository clone.

- [ ] **Step 2: Delete only that directory**

Run:

```powershell
Remove-Item -LiteralPath (Join-Path $repo 'bedrock') -Recurse -Force
```

- [ ] **Step 3: Confirm the directory is gone**

Run:

```powershell
Test-Path -LiteralPath (Join-Path $repo 'bedrock')
```

Expected: `False`.

### Task 2: Generate the English Java translation patch

**Files:**
- Create: `java/vanilla-plus-english-patch-26.2.zip`

- [ ] **Step 1: Extract the official English keys without inventing translations**

Read the official Vanilla+ `assets/minecraft/lang/en_us.json` and select keys matching `item.moldomre.*` plus `advancements.story.moldomre_*`, `advancements.adventure.moldomre_*`, and `advancements.vanillaplus.*`.

- [ ] **Step 2: Build the patch ZIP with the exact resource-pack paths**

The ZIP must contain:

```text
pack.mcmeta
assets/minecraft/lang/en_us.json
```

The language file must include the selected official values.

- [ ] **Step 3: Document how to layer the patch**

Update `README.md` to state that Java clients should load this patch after the full Vanilla+ resource pack, and that the Paper datapack remains separate.

### Task 3: Verify and commit the repository change

**Files:**
- Modify: `README.md`
- Delete: `bedrock/`
- Add: `java/vanilla-plus-english-patch-26.2.zip`

- [ ] **Step 1: Validate the JSON and key coverage**

Parse the language JSON, assert 290 `item.moldomre.*` keys and 44 custom advancement keys, and verify `item.moldomre.gingerbread_man` equals `Gingerbread Man`.

- [ ] **Step 2: Validate the ZIP layout**

List the ZIP and assert that `pack.mcmeta` and `assets/minecraft/lang/en_us.json` exist at the root-relative paths.

- [ ] **Step 3: Confirm the datapack is unchanged**

Compare the SHA-256 hash of `datapacks/paper-26.2/vanilla-plus-paper-26.2.zip` with the hash recorded before editing.

- [ ] **Step 4: Review the Git diff and commit**

Run:

```powershell
git status --short
git diff --stat
git add README.md java docs bedrock
git commit -m "fix: add Java Vanilla Plus translations"
```

Expected: only the README, new patch ZIP, design/plan docs, and Bedrock deletion are included; the Paper datapack is not modified.
