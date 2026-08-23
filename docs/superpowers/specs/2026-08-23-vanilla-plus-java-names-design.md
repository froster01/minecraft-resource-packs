# Vanilla+ Java English Names Design

## Goal

Make Vanilla+ custom item and advancement names resolve correctly for Java Edition clients, while removing the unused Bedrock export from this repository.

## Scope

- Delete the repository's `bedrock/` directory.
- Add a small Java Edition resource-pack ZIP under `java/`.
- Include the official Vanilla+ English translations for all `item.moldomre.*` keys and the 44 custom `advancements.*` keys.
- Keep the existing Paper 26.2 datapack unchanged.
- Do not redistribute the full official Vanilla+ resource pack; the patch is intended to layer after it or supply only the missing names.

## File format

The patch ZIP will contain:

```text
pack.mcmeta
assets/minecraft/lang/en_us.json
```

The language file will be merged by Java Edition's language manager and will use the exact official English values, including `item.moldomre.gingerbread_man: Gingerbread Man` and the Vanilla+ advancement titles/descriptions.

## Verification

- Parse `en_us.json` as JSON.
- Confirm 290 `item.moldomre.*` keys and 44 custom advancement keys are present.
- Confirm the ZIP contains `pack.mcmeta` and the language file at the correct paths.
- Confirm no `bedrock/` directory remains.
- Confirm the Paper datapack archive is byte-for-byte unchanged.
