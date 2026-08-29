# NexusMobs Automatic Boss Spawning Design

## Goal

Enable automatic random NexusMobs bosses on Hanz Minecraft without introducing a meaningful TPS burden or changing the server's existing vanilla mob behavior.

## Current State

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

## Deployment

1. Reopen the live NexusMobs configuration and confirm the source values still match the inspected state.
2. Change only the approved spawn keys.
3. Save the file and run `nexusmobs reload` from the Crafty console.
4. Do not restart the server unless the plugin rejects the reload.

## Verification

- Run `nexusmobs info` and confirm NexusMobs remains version 4.0.0 with a 2.0-3.0 hour spawn interval and a maximum of one active boss.
- Reopen `plugins/NexusMobs/config.yml` and verify every approved value persisted.
- Confirm `minecraft:mob_griefing` is still `true`.
- Run `spark tps` after reload and confirm short-window TPS is healthy.
- Check the console for NexusMobs configuration or reload errors.
- Do not force an immediate boss spawn; natural spawning is the acceptance path.

## Rollback

If the reload causes errors or a measurable performance regression, disable automatic spawning by setting `spawn.enabled: false`, save, and run `nexusmobs reload` again. Preserve the rest of the NexusMobs configuration.
