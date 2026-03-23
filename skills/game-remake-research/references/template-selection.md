# Template Selection

Use one primary archetype template and at most one secondary lens. Do not load all four unless the user explicitly wants a hybrid comparison.

Command examples assume `$GAME_REMAKE_RESEARCH` points at the installed skill root. If it is unset, run the same script from this skill's local `scripts/` directory.

## Primary Lens Decision

| Template | Choose when the game primarily wins on | Watch out for |
| --- | --- | --- |
| `template-mmo.md` | Persistent world, social dependency, long-term economy, live cadence | Reducing everything to solo loops and losing the reason the grind existed |
| `template-arpg.md` | Combat feel, loot chase, buildcraft, density, repeatable endgame | Copying surface loot rarity without the underlying chase and pacing |
| `template-roguelike.md` | Run rhythm, randomness governance, fail-forward design, meta progression boundaries | Treating randomness as enough without controlling anti-brick and recovery |
| `template-card.md` | Rules engine precision, timing windows, resource curve, matchup ecology | Failing to define exact rule timing, visibility, and anti-snowball controls |

## Hybrid Guidance

- `MMO + ARPG`
  Use `template-mmo.md` as primary if the product promise is long-term social persistence. Use `template-arpg.md` as primary if the product promise is moment-to-moment combat and loot chase with optional online layers.
- `Roguelike + Card`
  Use `template-card.md` as primary if the rules engine and card ecology dominate the experience. Use `template-roguelike.md` as primary if run pacing, randomness governance, and fail-forward structure dominate.
- `ARPG + Roguelike`
  Use `template-arpg.md` as primary if buildcraft and combat feel define mastery. Use `template-roguelike.md` as primary if run structure and reset cadence define mastery.
- `MMO + Card` or other hybrids
  Pick the lens that best explains why players return after the first ten hours. Use the secondary lens only to cover systems the primary lens under-explains.

## Working Rule

1. Pick the primary lens.
2. Record it in `research-manifest.yaml`.
3. If needed, add a secondary lens in `secondary_lenses`.
4. Generate the archetype file with `scaffold_remake_docs.py --archetype ...` and a concrete `--version-scope` when the pack will later be audited or handed off.
5. Remember that `scaffold_remake_docs.py` currently supports only `--language en`; keep the working pack in English while audit, status, and handoff scripts are still in play.
6. Read the matching template reference file and matching metrics reference file.
7. Only then add a secondary template if gaps remain.

## Script Example

```bash
python3 "$GAME_REMAKE_RESEARCH/scripts/scaffold_remake_docs.py" \
  --game "MapleStory" \
  --out ./docs/remake-maplestory \
  --archetype mmo \
  --version-scope "KMS baseline as observed on 2026-03-01" \
  --language en \
  --with-support-files
```

Add `--single-file` only when you also want `remake-dossier-template.md` as a manual one-file writing template.
Translate only a derived dossier or handoff artifact after the English pack is finished; do not rename working-pack section headings before running audit or handoff tooling.
