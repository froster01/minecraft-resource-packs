# Remove Guns From Server and Resource Pack

## Goal

Remove the unused Guns datapack from the Hanz Minecraft server and remove all of its client assets from the combined GitHub resource pack without affecting Vanilla+, Backpacks, Tool Trims, InvMinecarts, or other retained content.

## Scope

The removal includes the complete Guns feature surface:

- The server datapack `guns26-1v0-dp-admin-only-v2.zip`.
- The `assets/guns` resource namespace.
- Gun and turret item definitions and models.
- Ammunition, grenade, explosive, C4, and defusal assets.
- Guns sounds, fonts, recipe icons, translations, textures, and atlas entries.
- Any references from shared Minecraft namespace JSON files to removed Guns resources.

Existing player inventories may retain inert items whose custom appearance disappears after the resource pack update. No player or world data will be deleted.

## Release Strategy

Start from the currently configured `server-resource-pack-backpackplus-v1.0.12.zip`, whose SHA-1 is `3885dfcfd993b3c58d051fd600b92eceeba77ab9`. Produce a new `server-resource-pack-backpackplus-v1.0.14.zip` instead of replacing an existing release asset. Keeping the URL versioned prevents stale Minecraft client caches and preserves rollback artifacts.

Publish the new ZIP under GitHub release tag `v1.0.10`, then update `server.properties` to its exact GitHub download URL and newly calculated SHA-1.

## Validation

Automated validation will fail before removal and pass afterward. It will check that:

- No known Guns directories remain.
- No resource-pack JSON references the removed `guns` namespace or known Guns-only paths.
- Every remaining JSON file parses successfully.
- Every remaining model, texture, sound, and font reference resolves within the pack or is an allowed vanilla reference.
- The ZIP has `pack.mcmeta` and `assets` at its root.
- Retained namespaces and representative Vanilla+, Backpacks, Tool Trims, and InvMinecarts files remain present.

The produced ZIP's SHA-1 will be calculated locally and compared with an independently downloaded copy after GitHub publication.

## Live Rollout

1. Delete the already-disabled Guns datapack file from the server.
2. Upload the new GitHub resource-pack asset.
3. Update the resource-pack URL and SHA-1 in `server.properties`.
4. Restart the Minecraft server so the property changes take effect.
5. Verify the server starts cleanly, the Guns datapack is absent, the configured URL and SHA match GitHub, and TPS remains at 20.

## Rollback

The existing `v1.0.12` release asset and its verified SHA-1 remain available. If the new pack fails client loading, restore the old URL and SHA in `server.properties` and restart. The removed Guns datapack will not be re-enabled because profiling proved it causes severe tick lag.
