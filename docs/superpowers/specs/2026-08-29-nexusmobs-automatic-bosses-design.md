# NexusMobs Automatic Boss Spawning Design

## Goal

Enable automatic random NexusMobs bosses on Hanz Minecraft without introducing a meaningful TPS burden or changing the server's existing vanilla mob behavior.

## Pre-deployment Baseline

- The server runs Paper 26.2 with NexusMobs 4.0.0.
- NexusMobs is enabled and exposes 26 boss types, but no bosses are active.
- Natural spawning is configured for `world`, `world_nether`, and `world_the_end`; the actual level name is `feraxis`, so natural boss spawning cannot currently succeed.
- The existing profile attempts a spawn every 0.8-1.2 hours and permits up to 15 concurrent elites.
- The active server resource pack v1.0.15 contains no NexusMobs model assets.
- The `minecraft:mob_griefing` gamerule is `true` and must remain unchanged so vanilla farming and mob behavior continue.

## Approved Spawn Profile

Update only `plugins/NexusMobs/config.yml` with this automatic spawn profile:

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

All unrelated NexusMobs settings and boss definitions remain unchanged.

## Behavior and Safety

- Only the `feraxis` overworld is eligible for automatic boss spawning.
- NexusMobs may have only one active elite at a time.
- A spawn cycle occurs randomly every two to three hours while at least two players are online.
- Each cycle makes at most 20 location attempts between 160 and 320 blocks from a player.
- The plugin's custom boss attacks do not break or place terrain blocks. Its lightning is effect-only, fire abilities ignite entities, and explosion effects do not damage blocks.
- Because `minecraft:mob_griefing` remains enabled, Enderman-based bosses retain vanilla Enderman block-pickup behavior. This limited risk is accepted to preserve villager farming and other vanilla mechanics.
- No boss is manually spawned during deployment.

## Resource-Pack Limitation

The active v1.0.15 resource pack does not contain NexusMobs model assets, and NexusMobs' own resource-pack URL and hash are empty. Boss logic can operate, but bosses will use their vanilla base-entity appearance instead of the plugin's custom 3D models. Adding custom visuals is a separate task that requires an author-provided NexusMobs resource pack and a new merged server-pack release.

## Recorded Baseline

- Primary worker TPS: 5-second `20.0`; 10-second `20.0`.
- Primary worker tick durations (min/median/95th percentile/max):
  - 10-second: `23.4/28.8/41.3/277.1 ms`.
  - 1-minute: `22.5/27.9/37.6/328.6 ms`.
- Independent reviewer TPS: 5-second `20.0`; 10-second `20.0`.
- Independent reviewer tick durations (min/median/95th percentile/max):
  - 10-second: `21.1/26.0/34.4/227.0 ms`.
  - 1-minute: `21.1/25.7/35.5/353.7 ms`.

## Completion Record — 2026-08-30 MYT

- The persisted profile is enabled for `feraxis` only, with a 2.0-3.0 hour interval, 160-320 block distance, 20 spawn attempts, one maximum concurrent elite, spawn chance 1.0, and a minimum of two players online.
- `nexusmobs reload` succeeded at `2026-08-30 01:11:09 MYT`, and the next random spawn was scheduled in 2.78 hours.
- `nexusmobs info` reported NexusMobs v4.0.0, 0/1 active bosses, 26 configured types, and a 2.0-3.0 hour interval.
- `minecraft:mob_griefing` remained `true`.
- Post-reload sample 1: 5-second TPS `19.79`, 10-second TPS `19.89`, and 10-second median tick duration `23.7 ms`.
- Post-reload sample 2: 5-second TPS `20.0`, 10-second TPS `20.0`, and 10-second median tick duration `23.3 ms`.
- No fresh NexusMobs configuration or reload errors appeared after reload.
- Rollback was not required. No manual boss spawn was issued, and Paper was not restarted.
- The first natural boss spawn remains a monitoring item.

## Deployment

1. Reopen the live NexusMobs configuration and confirm the source values still match the inspected state.
2. Change only the approved spawn keys.
3. Save the file and run `nexusmobs reload` from the Crafty console.
4. Paper is never restarted automatically. If the initial reload or rollback fails, stop and request explicit user approval before restarting Paper or making unrelated server changes.

## Verification

- Run `nexusmobs info` and confirm NexusMobs remains version 4.0.0 with a 2.0-3.0 hour spawn interval and a maximum of one active boss.
- Reopen `plugins/NexusMobs/config.yml` and verify every approved value persisted.
- Confirm `minecraft:mob_griefing` is still `true`.
- After reload, wait 30 seconds and run `spark tps` twice, 30 seconds apart. Pass if both samples have 5s and 10s TPS >= 19.5 and 10s median tick duration <= 45 ms, with no NexusMobs reload/config errors. If either sample fails, execute rollback.
- Check the console for NexusMobs configuration or reload errors.
- Do not force an immediate boss spawn; natural spawning is the acceptance path.

## Rollback

If the reload or performance gate fails, restore the complete known-good original `spawn` block:

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

Save the file, run `nexusmobs reload`, and then run `nexusmobs info`. Verify `Active Nexus Mobs: 0 / 15` and `Spawn Interval: 0.8-1.2 hours`.

After confirming the restored runtime state, wait 30 seconds and run `spark tps` twice, 30 seconds apart. Recovery passes only if both samples have 5s and 10s TPS >= 19.5 and 10s median tick duration <= 45 ms, with no fresh NexusMobs errors after the rollback reload.

If either sample fails or a fresh NexusMobs error appears, stop and request explicit user approval before restarting Paper or making unrelated server changes. Preserve the failure evidence and do not modify unrelated NexusMobs configuration.
