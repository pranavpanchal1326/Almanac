# ADR 0002: Start with one region (Amazon + Cerrado), not the planet

Date: 2026-11-15        Status: accepted (by the project owner, 2026-11-15)

## Context

- There is no buyer yet. The only buyer hypothesis is forward forest-risk for supply-chain
  compliance (blueprint section 22.3), and it is untested.
- A global pass at 640 m costs about 19 hours and 170 GB of transfer (task 1.1 trial), and it has
  to run twice, because the patch-selection rule needs a threshold that needs global statistics
  (docs/phase1/STATUS.md).
- Gate 0 left the change threshold open (ADR 0001). Committing to a sampling rule for the planet
  before that is settled risks a third pass.

## Decision

1. Phase 1 and the first locked forecast cover one region: the bounding box 74°W–41°W, 24°S–5°N
   around the Brazilian Amazon and Cerrado (`configs/regions/amazon_cerrado.json`). It holds
   2,020 tiles (18,099 files; 23 tiles lack at least one year).
2. The 640 m embeddings for every tile and year in the region are kept on disk, as read. There is
   no patch sampling and there are no inclusion probabilities in this stage.
3. The first label is forest loss. Built-up growth is deferred.
4. Other regions are added later with the same command; finished tiles are never read again.

## Alternatives considered

- **The planet, two passes.** Lost on cost and on committing to a sampling design before the
  threshold is known, with no buyer asking for global coverage.
- **A smaller front only (Pará, 234 tiles).** Cheaper, but too small to hold out whole
  sub-regions for a fair test and still have enough change events to learn from.
- **Congo Basin or Sumatra and Borneo.** Both are real clearing fronts. Neither has a second,
  national yearly clearing map to check the global one against.

## Consequences

- Easier: one download of roughly 16 GB instead of two of 170 GB; no sampling weights; the
  threshold can be studied on data that is on disk.
- Harder: the first forecast is regional. It supports no claim about other biomes, about cities,
  or about "the Earth's surface". The blueprint's sections on sampling (8), splits (8.4, 3.9), the
  disk plan (7.6), the public global layer and the pre-registration template assume a global
  dataset and must be rewritten for a region before task 1.7.
- The bounding box also takes in the Andean foothills, the Guianas and part of the Atlantic
  coast. Labels and splits decide which cells count.
- Watch: whether a model trained here beats baselines only because the region is one large
  clearing front where proximity alone predicts well.

## Revisit when

- A buyer or design partner names a different region or layer.
- Gate 2 passes: decide whether the next step is a second region or the planet.
