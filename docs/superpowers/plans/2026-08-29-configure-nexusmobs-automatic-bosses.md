# Configure NexusMobs Automatic Bosses Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable conservative automatic NexusMobs boss spawning in the `feraxis` overworld while preserving vanilla mob behavior and healthy TPS.

**Architecture:** Change only the `spawn` section of the live NexusMobs configuration through the authenticated Crafty Controller panel. Reload NexusMobs in place, verify persisted configuration and runtime state, and roll back by restoring the complete known-good original `spawn` block if reload or performance checks fail.

**Tech Stack:** Crafty Controller 4.10.8, Paper 26.2, NexusMobs 4.0.0, Spark, Git

---

## File Map

- Live modify: `plugins/NexusMobs/config.yml` — NexusMobs automatic spawn policy.
- Preserve: `plugins/NexusMobs/bosses.yml` — all 26 boss definitions remain unchanged.
- Preserve: `server.properties` — resource-pack settings and all server settings remain unchanged.
- Documentation: `docs/superpowers/specs/2026-08-29-nexusmobs-automatic-bosses-design.md` — approved design and rollback policy.

### Task 1: Verify the Live Baseline

**Files:**
- Inspect: `plugins/NexusMobs/config.yml`

- [x] **Step 1: Open the exact live configuration**

In the authenticated Crafty Controller, open Hanz Minecraft -> Files and edit `plugins/NexusMobs/config.yml`.

Expected: the editor identifies `plugins/NexusMobs/config.yml` and shows a saved file.

- [x] **Step 2: Confirm the source spawn block has not drifted**

Verified pre-deployment baseline values:

```yaml
spawn:
  enabled: true
  worlds:
    - world
    - world_nether
    - world_the_end
  min-spawn-interval-hours: 0.8
  max-spawn-interval-hours: 1.2
  min-distance: 800
  max-distance: 1200
  max-spawn-attempts: 50
  max-concurrent-elites: 15
  spawn-chance: 0.85
  min-players-online: 1
```

If any source value differs, stop and compare the drift with the approved design before editing.

- [x] **Step 3: Capture runtime baseline commands**

Run in the Crafty console:

```text
nexusmobs info
gamerule minecraft:mob_griefing
spark tps
```

Expected:

```text
Version: 4.0.0
Active Nexus Mobs: 0 / 15
Spawn Interval: 0.8-1.2 hours
Gamerule mob_griefing is currently set to: true
```

#### Recorded baseline

- Primary worker TPS: 5-second `20.0`; 10-second `20.0`.
- Primary worker tick durations (min/median/95th percentile/max):
  - 10-second: `23.4/28.8/41.3/277.1 ms`.
  - 1-minute: `22.5/27.9/37.6/328.6 ms`.
- Independent reviewer TPS: 5-second `20.0`; 10-second `20.0`.
- Independent reviewer tick durations (min/median/95th percentile/max):
  - 10-second: `21.1/26.0/34.4/227.0 ms`.
  - 1-minute: `21.1/25.7/35.5/353.7 ms`.

### Task 2: Apply the Approved Spawn Profile

**Files:**
- Modify: `plugins/NexusMobs/config.yml`

- [x] **Step 1: Replace only the spawn policy values**

The resulting block must be exactly:

```yaml
spawn:
  enabled: true
  worlds:
    - feraxis
  min-spawn-interval-hours: 2.0
  max-spawn-interval-hours: 3.0
  min-distance: 160
  max-distance: 320
  max-spawn-attempts: 20
  max-concurrent-elites: 1
  spawn-chance: 1.0
  min-players-online: 2
```

Do not alter `resourcepack`, `models`, `elite-mobs`, messages, items, or any other configuration section.

- [x] **Step 2: Save the file**

Use the Crafty editor Save control.

Expected: the control changes to `Saved`, and the modified timestamp advances.

- [x] **Step 3: Reopen and verify persistence before reload**

Navigate away, reopen `plugins/NexusMobs/config.yml` through Hanz Minecraft -> Files, and verify all ten approved spawn values are present.

Expected: one world (`feraxis`), 2.0-3.0 hours, 160-320 blocks, 20 attempts, one concurrent elite, chance 1.0, and two required players.

### Task 3: Reload NexusMobs and Verify Runtime State

**Files:**
- Verify: `plugins/NexusMobs/config.yml`

- [x] **Step 1: Reload NexusMobs without restarting Paper**

Run:

```text
nexusmobs reload
```

Expected:

```text
Configuration reloaded.
```

If the console returns `Error reloading config`, immediately execute Task 4.

- [x] **Step 2: Verify NexusMobs accepted the profile**

Run:

```text
nexusmobs info
```

Expected key lines:

```text
Version: 4.0.0
Active Nexus Mobs: 0 / 1
Configured Types: 26
Spawn Interval: 2.0-3.0 hours
```

Do not use `nexusmobs spawn`, `nexusmobs testspawn`, or `nexusmobs weeklyspawn`.

- [x] **Step 3: Confirm vanilla mob behavior remains enabled**

Run:

```text
gamerule minecraft:mob_griefing
```

Expected:

```text
Gamerule mob_griefing is currently set to: true
```

- [x] **Step 4: Check TPS after reload**

After reload, wait 30 seconds and run `spark tps` twice, 30 seconds apart. Pass if both samples have 5s and 10s TPS >= 19.5 and 10s median tick duration <= 45 ms, with no NexusMobs reload/config errors. If either sample fails, execute rollback.

- [x] **Step 5: Inspect fresh console output for NexusMobs errors**

Expected: no YAML parse error, no `Error reloading config`, and no NexusMobs stack trace after the reload timestamp.

#### Completion record — 2026-08-30 MYT

- The persisted profile is enabled for `feraxis` only, with a 2.0-3.0 hour interval, 160-320 block distance, 20 spawn attempts, one maximum concurrent elite, spawn chance 1.0, and a minimum of two players online.
- `nexusmobs reload` succeeded at `2026-08-30 01:11:09 MYT`, and the next random spawn was scheduled in 2.78 hours.
- `nexusmobs info` reported NexusMobs v4.0.0, 0/1 active bosses, 26 configured types, and a 2.0-3.0 hour interval.
- `minecraft:mob_griefing` remained `true`.
- Post-reload sample 1: 5-second TPS `19.79`, 10-second TPS `19.89`, and 10-second median tick duration `23.7 ms`.
- Post-reload sample 2: 5-second TPS `20.0`, 10-second TPS `20.0`, and 10-second median tick duration `23.3 ms`.
- No fresh NexusMobs configuration or reload errors appeared after reload.
- Rollback was not required. No manual boss spawn was issued, and Paper was not restarted.
- The first natural boss spawn remains a monitoring item.

### Task 4: Roll Back Only if Verification Fails

**Files:**
- Modify conditionally: `plugins/NexusMobs/config.yml`

**Status:** Not required; all reload/performance gates passed. The unchecked steps below are a conditional future runbook and were not executed.

- [ ] **Step 1: Restore the complete known-good original spawn block**

Replace the complete `spawn` block with:

```yaml
spawn:
  enabled: true
  worlds:
    - world
    - world_nether
    - world_the_end
  min-spawn-interval-hours: 0.8
  max-spawn-interval-hours: 1.2
  min-distance: 800
  max-distance: 1200
  max-spawn-attempts: 50
  max-concurrent-elites: 15
  spawn-chance: 0.85
  min-players-online: 1
```

Save the file.

- [ ] **Step 2: Reload the restored profile**

Run:

```text
nexusmobs reload
```

Expected:

```text
Configuration reloaded.
```

- [ ] **Step 3: Verify the known-good runtime state and report the failure evidence**

Reopen `plugins/NexusMobs/config.yml` and confirm the complete original `spawn` block persisted. Run `nexusmobs info` and verify `Active Nexus Mobs: 0 / 15` and `Spawn Interval: 0.8-1.2 hours`. Preserve the relevant console error and Spark readings in the handoff; do not restart Paper or modify other plugins without new approval.

- [ ] **Step 4: Verify rollback performance recovery**

After confirming the restored runtime state, wait 30 seconds and run `spark tps` twice, 30 seconds apart. Recovery passes only if both samples have 5s and 10s TPS >= 19.5 and 10s median tick duration <= 45 ms, with no fresh NexusMobs errors after the rollback reload.

If either sample fails or a fresh NexusMobs error appears, stop and request explicit user approval before restarting Paper or making unrelated server changes.

### Task 5: Record and Publish the Completed State

**Files:**
- Verify: `docs/superpowers/specs/2026-08-29-nexusmobs-automatic-bosses-design.md`
- Verify: `docs/superpowers/plans/2026-08-29-configure-nexusmobs-automatic-bosses.md`

- [x] **Step 1: Run repository checks**

Run:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors and no uncommitted files after committing this plan.

- [x] **Step 2: Push the documentation commits to main after live verification passes**

Run:

```powershell
git push origin main
```

Expected: GitHub `main` advances to the local documentation commit without a force push.

- [ ] **Step 3: Write the shared handoff (controller follow-up)**

After independent reviews, the controller records the persisted spawn values, reload result, `nexusmobs info`, `mob_griefing`, Spark TPS/MSPT readings, Git commit, pushed branch, and whether rollback was required. This repository worker does not execute the controller-owned handoff.
