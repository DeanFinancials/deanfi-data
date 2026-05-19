# TODO: Cap `catalysts.ranked` in `market_pulse_input.json`

## Why

`market_pulse_input.json` is the contract feeding the deanfi-website Market Pulse article generator. As of 2026-05-18 it was shipping 164 ranked catalysts (~790 KB payload). The website's only sane use of that list is rendering the top ~12 in the "Headlines Moving Markets" section.

This caused three downstream validator failures in [scripts/market-pulse/](../../deanfi-website/scripts/market-pulse/) — all symptoms of the same root cause: shipping more catalysts than the consumer can render.

1. **"Too many em dash placeholders"** — em-dash separator per catalyst pushed body count past the markdown validator's 40-em-dash ceiling.
2. **"Source link missing for catalyst: …"** — website-side truncation to 12 broke the source-link validator that iterates the full `ranked` list.
3. **"Grounding catalyst title missing: …"** — same shape mismatch in the data-grounding validator.

The website now caps at 12 defensively (see [`MARKET_PULSE_MAX_RANKED_CATALYSTS` in `runtime-package.mjs`](../../deanfi-website/scripts/market-pulse/runtime-package.mjs)), but the right fix is to make the contract honest: the input file should publish the editorial top-N, not the raw collector dump.

## What to change

### 1. `dailycombined/combine_daily_snapshots.py`

Current code around line 487–507:

```python
catalysts = catalyst_integration.apply_market_context(
    catalysts,
    sector_leaders=core.get('sector_leaders'),
    sector_laggards=core.get('sector_laggards'),
)
ranked = catalysts.get('ranked') or []
catalyst_meta = catalysts.get('metadata') or {}
completeness = catalyst_integration.validate_completeness(catalysts, market_date=market_date)
release_meta = catalyst_integration.required_official_release_today(market_date)
catalysts_block = {
    'status': 'ready' if completeness['is_valid'] else 'incomplete',
    'ranked': ranked,
    'ranking_method': catalyst_meta.get('ranking_method', 'deterministic'),
    'weekly_mode': bool(catalyst_meta.get('weekly_mode', False)),
    'expected_min_catalysts': int(catalyst_meta.get('expected_min_catalysts') or 3),
    'official_release_today': bool(release_meta.get('official_release_today')),
    'official_release_kinds': list(release_meta.get('official_release_kinds') or []),
    'completeness': completeness,
    'source_file': 'daily-news/market_catalysts.json',
}
```

Proposed:

```python
MARKET_PULSE_RANKED_LIMIT = 12  # module-level constant

# ...

catalysts = catalyst_integration.apply_market_context(
    catalysts,
    sector_leaders=core.get('sector_leaders'),
    sector_laggards=core.get('sector_laggards'),
)
ranked_all = catalysts.get('ranked') or []
ranked = ranked_all[:MARKET_PULSE_RANKED_LIMIT]
catalyst_meta = catalysts.get('metadata') or {}
# Run completeness against the FULL ranked set so expected_min_catalysts and
# the "official source on macro/policy days" rule are not hidden by the cap.
completeness = catalyst_integration.validate_completeness(catalysts, market_date=market_date)
release_meta = catalyst_integration.required_official_release_today(market_date)
catalysts_block = {
    'status': 'ready' if completeness['is_valid'] else 'incomplete',
    'ranked': ranked,
    'ranked_total': len(ranked_all),
    'ranked_limit': MARKET_PULSE_RANKED_LIMIT,
    'ranking_method': catalyst_meta.get('ranking_method', 'deterministic'),
    'weekly_mode': bool(catalyst_meta.get('weekly_mode', False)),
    'expected_min_catalysts': int(catalyst_meta.get('expected_min_catalysts') or 3),
    'official_release_today': bool(release_meta.get('official_release_today')),
    'official_release_kinds': list(release_meta.get('official_release_kinds') or []),
    'completeness': completeness,
    'source_file': 'daily-news/market_catalysts.json',
}
```

Key invariant: **completeness is validated on the full ranked list, not the truncated 12.** Otherwise a day with 50 non-official catalysts on a macro-release day could pass completeness simply because the top 12 happened to include something `source_tier == "official"` is missing from.

### 2. `dailycombined/market_pulse_input.schema.json`

Update the `catalysts` block (lines 45–55):

```json
"catalysts": {
  "type": "object",
  "additionalProperties": true,
  "required": ["ranked"],
  "properties": {
    "ranked": {
      "type": "array",
      "items": { "type": "object" },
      "maxItems": 12
    },
    "ranked_total": { "type": "integer", "minimum": 0 },
    "ranked_limit": { "type": "integer", "minimum": 1 }
  }
}
```

### 3. Decision: publish the full list anywhere?

Pick one before implementing:

- **Slim (recommended)**: drop the full list from `market_pulse_input.json`. If a future consumer needs the raw ranked list, expose it in a sibling file (e.g. `dailycombined/catalysts_ranked_full.json`). Keeps the article-input contract narrow.
- **Wide**: add `"ranked_all": ranked_all` to the catalysts block. Simpler now, but couples unrelated future consumers' shape decisions to this file.

If we go Slim, the schema above is correct as written. If we go Wide, add `"ranked_all"` to the schema's properties.

### 4. Tests to add — `dailycombined/tests/test_market_pulse_input.py`

- **Cap honored**: build an input with >12 ranked catalysts; assert `len(catalysts['ranked']) == 12`, `catalysts['ranked_total'] == input_count`, `catalysts['ranked_limit'] == 12`.
- **Order preserved**: the 12 emitted are the first 12 from the post-`apply_market_context` ordering.
- **Completeness not fooled by cap**: 50 ranked catalysts, all `source_tier == "third_party"`, on a macro-release day → `status == 'incomplete'` and a blocking failure for the missing official source. (Today's bug would pass if completeness ran on the truncated 12.)
- **Cap floor**: ≤12 ranked catalysts pass through unchanged.

### 5. Website follow-up (keep, don't remove)

Leave `MARKET_PULSE_MAX_RANKED_CATALYSTS = 12` in [scripts/market-pulse/runtime-package.mjs](../../deanfi-website/scripts/market-pulse/runtime-package.mjs) as a defensive belt-and-suspenders cap. If upstream regresses, or a hand-crafted input file is supplied for testing, the article generator still produces a publishable result. One line, no harm.

If the website cap and the upstream cap ever diverge, the website cap wins (the smaller number always wins because both are `slice(0, N)`).

## Open questions

- Is 12 the right number? It was chosen so the "Headlines Moving Markets" section is readable and stays under the 40-em-dash markdown validator ceiling even before the em-dash separator fix. Reasonable range: 10–15.
- Should `MARKET_PULSE_RANKED_LIMIT` come from `metadata.expected_min_catalysts` × some multiplier, or stay a hard constant? Hard constant is simpler; revisit if editorial signals it.

## Rollout

1. Make the combiner change and add tests in `deanfi-data`.
2. Wait one or two daily combiner runs to confirm `market_pulse_input.json` shrinks and `ranked_total` reports the pre-cap count correctly.
3. Confirm the website workflow continues to pass (it should, because the website's own cap is now redundant but harmless).
4. Optionally remove the website-side `slice` later — but the recommendation is to leave it in place.

## Reference: the original failure modes

For context when picking up this work, the three CI failures that motivated this doc are reproduced in the website repo's session history around 2026-05-19. The website-side fixes applied that day:

- [scripts/market-pulse/markdown-renderer.mjs](../../deanfi-website/scripts/market-pulse/markdown-renderer.mjs) — replaced ` — ` separator with `. ` in `renderCatalysts`.
- [scripts/market-pulse/runtime-package.mjs](../../deanfi-website/scripts/market-pulse/runtime-package.mjs) — added `MARKET_PULSE_MAX_RANKED_CATALYSTS` and `trimRankedCatalysts`.
- [scripts/market-pulse/generate-market-pulse-openai.mjs](../../deanfi-website/scripts/market-pulse/generate-market-pulse-openai.mjs) — passes `runtimePackage` (not raw `marketPulseInput`) to `validateMarketPulseGrounding`.

The upstream change described here makes the website's cap defensive rather than load-bearing.
