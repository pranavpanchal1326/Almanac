# Project Almanac — Production Blueprint

> Working codename. Run a trademark search before using it in public.

| Field | Value |
|---|---|
| Document version | 0.3 (adds the lean 30 GB storage plan: sections 7.6, 8.1, 8.6, tasks 0.11, 1.1–1.3, 1.12, 4.2, risk R23) |
| Date | 2026-11-14 |
| Status | For team review. Nothing described here has been built yet. |
| Scope | Research system, production platform, product, and company |
| Supersedes | Version 0.1 partial draft of the same date |

---

## Contents

**Part A — What and why**
- 0. How to read this document
- 1. Executive summary
- 2. Product definition
- 3. Science foundations

**Part B — Data**
- 4. Primary dataset
- 5. Second-source embeddings
- 6. Data source register
- 7. Volumes and storage maths
- 8. Sampling design
- 9. Data quality, contracts, versioning

**Part C — Platform**
- 10. System architecture
- 11. Forecast registry
- 12. Grading service
- 13. Technology stack

**Part D — Engineering**
- 14. Repository and engineering standards
- 15. Model engineering

**Part E — Execution**
- 16. Phase-by-phase plan

**Part F — Product and operations**
- 17. Productisation
- 18. Operations
- 19. Security and compliance

**Part G — Company**
- 20. Cost model
- 21. Team
- 22. Go-to-market
- 23. Legal and licensing
- 24. Risk register
- 25. Roadmap and measures

**Part H — Appendices**
- A. Code skeletons
- B. Configuration templates
- C. Document templates
- D. Checklists
- E. Glossary
- F. Verification log and sources
- G. Open questions

---

# PART A — WHAT AND WHY

## 0. How to read this document

### 0.1 Evidence labels

Every factual claim that the plan depends on carries one of four labels. A production plan built on unlabelled claims cannot be audited.

| Label | Meaning | What to do |
|---|---|---|
| **[V]** | Verified on 2026-11-14 by reading the primary source or the data itself | Use it; re-check if months have passed |
| **[S]** | Taken on 2026-11-14 from a secondary source: press, a vendor page, a search summary | Confirm at the primary source before relying on it |
| **[M]** | From the author's memory; not checked | Confirm before relying on it |
| **[E]** | An estimate derived in this document | Check the derivation; replace with a measurement as soon as one exists |

### 0.2 Requirement words

- **MUST** — the design is wrong without it.
- **SHOULD** — do it unless a recorded decision says otherwise.
- **MAY** — optional.

### 0.3 Decisions and changes

- Every decision that departs from this document is recorded as an architecture decision record (template in Appendix C.4).
- Section 24 holds the risk register. Appendix G holds open questions. Both are reviewed weekly.

### 0.4 Limits of this draft

- **No code here has been run.** Appendix A is a set of starting points, not tested software.
- **Costs are estimates** built from price lists read on one day.
- **Legal statements are not legal advice.** Section 23 lists what counsel must review.
- **Team size is assumed** to be two or three people part-time until funding. Timelines scale with that.

---

## 1. Executive summary

### 1.1 The product in one paragraph

Almanac forecasts how the surface of the Earth will change, one and two years ahead: where forest will be cleared, where cities will spread, where cropland will appear or be abandoned. It publishes each forecast before the satellite data that can confirm or refute it exists. When that data arrives, an automated grader scores the forecast in public against simple baselines. The scorecard is the product's proof.

### 1.2 The thesis

Models have made answers cheap. They have not made being right cheap. The value that survives falling model prices sits in contact with reality: measurements, outcomes, and public checks. Almanac is built so that every claim it makes has a date on which reality checks it.

### 1.3 Why now

| Enabler | Fact | Label |
|---|---|---|
| Free global input | AlphaEarth Foundations describes every 10 m of land, yearly, 2017–2025, under CC-BY 4.0 | [V] |
| Method shown to work | A transformer forecasting in embedding space halved error against persistence, code MIT | [V] |
| Forest benchmark exists | Google's ForestCast benchmark for deforestation risk is public | [V] |
| Demand trigger | The EU deforestation law applies to large and medium companies from 30 December 2026 | [S] |
| Gap opening | A widely used free deforestation-checking tool, GFW Pro, shuts down on 31 December 2026 | [S] |
| Exam cadence | The 2025 layer began appearing on 29 January 2026, so a yearly exam is predictable | [S] |

### 1.4 What exists at each milestone

| Milestone | Date | What exists |
|---|---|---|
| Phase 0 gate | 22 Nov 2026 | Proof that yearly change in the data is real and exceeds noise at three sites |
| Scoreboard | 6 Dec 2026 | Fixed datasets, five baselines scored (the sixth needs the model code), win condition written and timestamped |
| Model gate | 27 Dec 2026 | A model that beats the best baseline on held-out years and held-out regions, or a stop decision |
| Lock | 15 Jan 2027 | Public, timestamped forecasts for 2026 and 2027, with code and a map |
| First exam | From late Jan 2027 | Automated public scorecard as the 2026 layer arrives |
| Product alpha | Apr 2027 | Programming interface, map tiles, area reports, three design partners |
| Scale | Aug 2027 | Global 80 m forecasts, cloud pipelines, security audit under way |
| Second exam | Jan 2028 | A graded two-year record; general availability decision |

### 1.5 The three risks that matter most

1. **Year-to-year structural change may not be predictable enough at fine scale.** The reference method was shown on within-year dynamics. Mitigation: a cheap global coarse model first, a hard gate in week 6, and a fallback to coarse risk maps.
2. **Single supplier.** One company produces the input data, and the free copy is a third-party mirror. Mitigation: local copies, a second embedding source on the bench, and a paid fallback route.
3. **A larger group ships the same thing.** The groups closest are the data's producer and the authors of the reference method. Mitigation: be first with a graded public record, which cannot be back-filled.

---

## 2. Product definition

### 2.1 Users and the job each one hires the product for

| User | Job | What they need from a forecast | What it must not be mistaken for |
|---|---|---|---|
| Commodity importer's compliance lead | Decide which sourcing areas to audit first | Ranked risk of forest loss for each sourcing polygon, next 12–24 months | Evidence of past compliance. The law asks about the past since 31 Dec 2020, not the future |
| Compliance-platform vendor | Add a forward-looking layer to an existing product | A stable programming interface, bulk scoring of many polygons, clear licence | A replacement for their monitoring |
| Conservation agency or patrol planner | Send limited patrols where clearing is likely | A map of the top-risk cells in a jurisdiction, refreshed yearly | A list of suspects |
| Reinsurer or catastrophe modeller | Project where insured exposure will grow | Built-up growth probability per cell, with uncertainty | A valuation |
| City or infrastructure planner | Anticipate where settlement will spread | Built-up growth map, two years ahead | A zoning decision |
| Development bank or statistics office | Estimate settlement growth between censuses | Aggregated growth by administrative area | A census |
| Researcher | Compare methods fairly | Open benchmark, baselines, hidden test regions | — |

### 2.2 Product surfaces

| Surface | Audience | Content | Access |
|---|---|---|---|
| Public scorecard | Everyone | Every locked forecast, its grade against baselines, confidence intervals, misses included | Open |
| Public coarse map | Everyone | Global change-risk layer at 640 m | Open, CC-BY |
| Forecast interface | Developers, vendors | Point, polygon and bulk queries; issue metadata | Keyed, metered |
| Map tiles | Web and GIS users | Raster tiles for each layer and level | Keyed |
| Area report | Compliance and planning staff | One document per area: risk, drivers, uncertainty, history, method note | Keyed |
| Watchlists and webhooks | Operations teams | Notify when a new issue changes an area's rank | Keyed |
| Bulk delivery | Enterprise | Cloud-optimised files through signed links | Contract |
| Open benchmark | Researchers | Datasets, splits, baselines, leaderboard with hidden test set | Open |

### 2.3 The forecast object

A forecast is a record with a fixed meaning. Everything downstream depends on this definition being exact.

| Field | Definition |
|---|---|
| `issue_id` | Identifier of the forecast issue, for example `2027.01` |
| `cell` | A grid cell at a stated level (2.4), identified by tile, level, row, column |
| `data_cutoff_year` | Last year of input data used. No later data touches the forecast |
| `target_year` | The calendar year being forecast |
| `horizon` | `target_year − data_cutoff_year`: 1 or 2 |
| `embedding_mean` | Predicted 64-number description for the target year, length 1 |
| `embedding_spread` | Predicted per-number standard deviation |
| `p_change` | Probability that the cell's description moves more than the published threshold between cutoff year and target year |
| `readouts` | Probability of each land class in the target year, and the change from the cutoff year |
| `model_version` | Version of the forecasting model |
| `input_dataset_version` | Version of the input embeddings |
| `package_digest` | Digest of the locked package that contains this record (section 11) |

Rules:

- A forecast MUST be reproducible from `model_version`, `input_dataset_version` and the code commit named in the package.
- A forecast MUST NOT be edited after locking. A correction is a new issue that names the one it replaces.
- Probabilities MUST be calibrated on a validation year before release, and the calibration method is part of the model version.

### 2.4 Grid levels

Levels follow the input files' own pyramid, so no resampling choice is hidden in the product.

| Level | Cell size | Cells per tile side | Typical use |
|---|---|---|---|
| L0 | 10 m | 8192 | Detail on request for small areas |
| L1 | 20 m | 4096 | Rarely used |
| L2 | 40 m | 2048 | Rarely used |
| L3 | 80 m | 1024 | Regional product |
| L4 | 160 m | 512 | Regional overview |
| L5 | 320 m | 256 | Global model once in the cloud |
| L6 | 640 m | 128 | Global training, inference and public layer in version 1 |
| L7 | 1.28 km | 64 | Global quick-look |

### 2.5 Layers in version 1

| Layer | Meaning | Levels |
|---|---|---|
| `change_risk` | `p_change` | L3, L5, L6 |
| `forest_loss_risk` | Probability a forested cell loses tree cover by the target year | L3, L5, L6 |
| `builtup_gain_risk` | Probability built-up share rises above a threshold | L3, L5, L6 |
| `cropland_change_risk` | Probability of cropland gain or loss | L5, L6 |
| `uncertainty` | Summary of `embedding_spread` | L3, L5, L6 |
| `rank_in_area` | Percentile of the cell within a named area | Computed on request |

### 2.6 Non-goals

- **Not a monitoring product.** Detecting change that already happened is done by others and by free alert systems.
- **Not compliance evidence.** A forecast cannot show that past production was deforestation-free.
- **Not legal or parcel-level determination.** No statement about who will act or who owns land.
- **Not faster than yearly in version 1.** The input is yearly.
- **Not about people.** No inference about individuals or households.
- **Not for targeting.** Uses that aim harm at communities are prohibited (section 19.6).

### 2.7 Product principles

1. **Lock before truth.** No forecast counts unless it was locked and timestamped by independent parties before the target data existed.
2. **Publish the losses.** Every issue is graded and stays visible, including bad ones.
3. **Baselines next to every number.** A score with no baseline beside it is not shown.
4. **Uncertainty is part of the answer.** No layer ships without it.
5. **Reproducible by a stranger.** Code, data pointers, environment and steps are public for the open layers.
6. **Licence-clean.** Every input's licence is recorded and honoured (section 6.6).
7. **Plain claims.** The product says "ranked risk", never "will be deforested".

### 2.8 Service targets

| Property | Alpha | General availability |
|---|---|---|
| Interface availability, monthly | 99.0% | 99.9% |
| Point query latency, 95th percentile | 500 ms | 200 ms |
| Polygon query (up to 10,000 ha), 95th percentile | 5 s | 2 s |
| Tile latency, 95th percentile | 400 ms | 150 ms |
| Issue cadence | Yearly | Yearly plus mid-year refresh |
| Time from new input layer to locked issue | 30 days | 10 days |
| Time from truth arrival to published grade | 14 days | 3 days |

---

## 3. Science foundations

### 3.1 What the input is

An **embedding** is a short list of numbers that a model produces to summarise something. AlphaEarth Foundations produces 64 numbers for every 10 m patch of land for each calendar year. Patches that look and behave alike across the year get similar lists. [V]

Properties that shape the design:

| Property | Consequence |
|---|---|
| Each list has length 1 (it is a point on a sphere) | Compare two lists with their dot product. Average with care and renormalise |
| One list per year | Seasons are blended. A field that rotates two crops gets one blended description [S] |
| Stored as 8-bit integers | Small rounding noise in every value |
| The producing model is not released | We cannot make embeddings ourselves for new dates. Supply risk (section 24) |
| Built from optical, radar and other sources | More robust to cloud than optical data alone |
| Versioned (1.1 since 2025-11-17) | A reprocessing can change past years. Pin and checksum everything |

### 3.2 Notation

| Symbol | Meaning |
|---|---|
| `x` | A cell |
| `t` | A year |
| `e(x,t)` | The embedding of cell `x` in year `t`, 64 numbers, length 1 |
| `H(x,t)` | History: `e(x,t−k+1) … e(x,t)` |
| `N(x)` | The neighbourhood of `x` |
| `d(x)` | Static drivers at `x`: distance to roads, slope, protection status, and so on |
| `δ(x,t,h)` | Change: `1 − e(x,t) · e(x,t+h)` |
| `τ` | Change threshold |
| `y(x,t,h)` | Change event: 1 if `δ(x,t,h) > τ`, else 0 |

### 3.3 Two definitions of change

The product uses both and reports them separately.

**Embedding change.** `δ` above the threshold `τ`. It is available everywhere and needs no outside labels. It is self-referential: the forecast is graded against the same data family it was made from.

**Label change.** A transition recorded in an independent map: forest to non-forest in the annual forest-loss maps, new buildings in building datasets. It is independent of the embeddings but exists only for some classes and regions, and has its own errors.

### 3.4 The noise floor and the threshold

Year-to-year embeddings differ slightly even where nothing happened, because of cloud, season timing and rounding.

Procedure, fixed in Phase 0:

1. Choose stable reference sites in each major biome: desert interior, old-growth forest interior, long-established urban core, permanent open water.
2. Compute `δ(x,t,1)` for all cells and all year pairs at each site and level.
3. Record the full distribution per biome and level.
4. Set `τ` per level as the 99th percentile of the pooled stable distribution. Publish the value.
5. Re-estimate when the input dataset version changes. A changed `τ` is a new model version.

Gate: at the known-change sites, the share of cells above `τ` in the year of the known event MUST exceed the stable-site share by at least a factor of five. If it does not, the yearly data cannot support the product and the project stops (section 16.2).

### 3.5 The forecasting tasks

| Task | Question | Output | Primary metric |
|---|---|---|---|
| T1 Occurrence | Which cells change? | `p_change` per cell | Average precision |
| T2 Direction | Where change happens, what does the cell become? | `embedding_mean` | Cosine distance on changed cells |
| T3 Readout | What land class is each cell in the target year? | Class probabilities | Average precision per transition |
| T4 Amount | How much change falls in each coarse block? | Expected changed area per 10 km block | Mean absolute error; rank correlation |
| T5 Calibration | Do stated probabilities match frequencies? | Reliability curve | Expected calibration error |

T1 is the primary task. The win condition (3.10) is stated on T1.

### 3.6 Why "nothing changes" is hard to beat

Most land does not change in a given year. A forecast that copies last year is right almost everywhere, so average error across all cells says little. Three consequences:

1. Metrics MUST focus on the rare event: average precision, and precision within the top-ranked share of area.
2. Every score MUST be shown as **skill**: `1 − score_model / score_reference`, against the best simple baseline.
3. The serious competitor is not "nothing changes". It is "change happens next to where it happened before", which is cheap and strong.

### 3.7 Uncertainty

| Mechanism | What it gives | Version |
|---|---|---|
| Gaussian head | A mean and a per-number spread in one pass | 1 |
| Calibrated probability | `p_change` mapped through isotonic regression fitted on the validation year | 1 |
| Conformal intervals | Distribution-free intervals for block-level amounts (T4) | 1 |
| Ensemble of futures | Several plausible outcomes per cell, from a flow-matching branch | 2 |

The reference method found that treating the 64 numbers as independent worked better than modelling their correlations. [V] Version 1 keeps them independent.

### 3.8 Scoring rules

| Rule | Used for | Note |
|---|---|---|
| Average precision | T1, T3 | The headline. Robust to heavy imbalance |
| Precision at top `k`% of area | T1, T3 | Matches how patrols and audits use the map. Report `k` = 0.1, 1, 5 |
| Brier score and log loss | T1 | Proper scoring rules; reward honest probabilities |
| Reliability curve, expected calibration error | T5 | Ten equal-mass bins |
| Fractions skill score | T1, T3 | Gives credit for a hit within a neighbourhood. Report at 1, 3 and 9 cells |
| Cosine distance | T2 | Only on cells that changed |
| Continuous ranked probability score | T2, T4 | Closed form for the Gaussian head (Appendix A.7) |
| Mean absolute error, Spearman correlation | T4 | Per 10 km block |

### 3.9 Splits and leakage

Years available: 2017–2025. A one-year-ahead example uses history up to year `t` and the target at `t+1`.

| Split | Target years (horizon 1) | Target years (horizon 2) | Purpose |
|---|---|---|---|
| Train | 2018–2023 | 2019–2023 | Fit |
| Validation | 2024 | 2024 | Model choice, calibration, early stopping |
| Test | 2025 | 2025 | Reported backtest. Touched once per model family |
| Forward | 2026 | 2027 | The public exam |

Spatial rules:

- **Split by tile, not by cell.** A tile is 82 km square. All cells in a tile go to the same side.
- **Buffer.** Tiles that share an edge with a test tile are removed from training.
- **Held-out regions.** At least one large region per continent is kept out of training entirely and reported separately.
- **Held-out biome check.** Report scores by biome so that a single dominant biome cannot carry the headline.

Leakage sources and controls:

| Source | Control |
|---|---|
| Neighbouring cells on both sides of a split | Tile-level split with buffer |
| The same event seen at two levels | A tile's levels always share a side |
| Labels and inputs derived from the same satellites | Stated as a limit; independent label sources preferred for the headline readout scores |
| Reprocessed input years | Pin dataset version; store content digests; refuse to mix versions |
| Tuning on the test year | Test year touched once per model family; every touch logged |
| Drivers updated after the cutoff | Each driver carries a "valid as of" date; anything later than the cutoff is excluded |

### 3.10 Significance and the win condition

- **Primary metric:** average precision on T1, horizon 1, level L6, test year 2025, held-out regions. L6 is chosen because the whole planet at L6 fits on the development laptop (section 7).
- **Reference:** the best of the six baselines in section 15.9 on the same data.
- **Win condition (proposed):** relative improvement of at least 20%, with the lower end of a 95% interval above 10%.
- **Interval method:** paired block bootstrap. Resample tiles with replacement, 2,000 draws, recompute both scores on each draw.
- **One primary metric.** Everything else is secondary and reported without a claim of significance.
- The win condition is written into the pre-registration document (Appendix C.1) and timestamped before any model is trained.

### 3.11 Ways the science can fail, and how each shows up

| Failure | Early sign | Response |
|---|---|---|
| Yearly blending hides the change | Phase 0 gate fails | Stop |
| Change is forecastable only by proximity | Model matches the proximity baseline but does not beat it | Ship the baseline as the product, or stop |
| Skill exists at coarse levels only | L6 passes, L3 fails | Sell coarse risk maps; drop detail |
| Regime shift: a law or price change alters behaviour | Skill drops in one region in one year | Report it; add national drivers; never hide it |
| Labels are too noisy to grade readouts | Disagreement between two label sources exceeds the model's error | Grade on the intersection of sources |
| Overview levels were made by a method that breaks the meaning | Probe accuracy collapses at coarse levels | Build own coarse levels by averaging L0 and renormalising |

---

# PART B — DATA

## 4. Primary dataset

### 4.1 AlphaEarth Foundations Satellite Embedding, version 1, annual

| Property | Value | Label |
|---|---|---|
| Producer | Google and Google DeepMind | [V] |
| Content | 64 numbers per cell; length 1 after decoding | [V] |
| Cell size | 10 m | [V] |
| Years | 2017–2025, one layer per calendar year | [V] |
| Projection | Native UTM zone per file | [V] |
| File tile | 8192 × 8192 cells (81.92 km square) | [V] |
| Stored type | Signed 8-bit integer; −128 means no data | [V] |
| Total archive | About 465 TB | [S] |
| Licence | CC-BY 4.0 | [V] |
| Dataset version | 1.1 since 2025-11-17 | [S] |
| Arrival of a new year | 2025 layer began appearing 2026-01-29, added zone by zone | [S] |
| Producer's commitment | At least one year's notice of any change in delivery, subject to input satellites | [S] |

Required attribution, word for word:

> The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.

This sentence MUST appear on the scorecard site, in the web app's attribution panel, in every area report, and in the README of every public repository that touches the data.

### 4.2 Access routes

| Route | Cost | Account | Limits | Role in this project |
|---|---|---|---|---|
| Source Cooperative mirror | Free | None | Third-party copy, not supported by Google | Primary for all work |
| Google Cloud Storage bucket | Reader pays transfer and requests | Cloud project with billing | Most current | Fallback; source of new years if the mirror lags |
| Earth Engine | Free tier 150 compute-hours a month; paid commercial tiers | Verified project | Free tier is non-commercial only | Small server-side sampling in research; cross-checks |

Decision: build on the mirror; keep our own copy of everything we sample; keep the Google bucket configured and tested as fallback.

### 4.3 Exact layout on the mirror [V]

HTTPS base, reachable from the development laptop with no account and with partial reads enabled:

```
https://data.source.coop/tge-labs/aef/v1/annual/
```

Same data as an S3 address (the bucket sits in the `us-west-2` region):

```
s3://us-west-2.opendata.source.coop/tge-labs/aef/v1/annual/
```

File pattern:

```
<year>/<utm zone><N|S>/<earth-engine image id>-<y offset>-<x offset>.tiff
<year>/<utm zone><N|S>/<earth-engine image id>-<y offset>-<x offset>.vrt
```

Real example:

```
2017/10N/x0dyfir8mjpv8ty4m-0000000000-0000000000.tiff
2017/10N/x0dyfir8mjpv8ty4m-0000000000-0000000000.vrt
```

Each Earth Engine image is 16384 × 16384 cells and is cut into four files. Each offset is `0000000000` or `0000008192`.

Index and listing files in the same folder:

| File | Size | Use |
|---|---|---|
| `manifest.txt` | 68 MB | Plain list of every object |
| `aef_index.parquet` | 78 MB | The one to use |
| `aef_index.gpkg` | 539 MB | For desktop GIS |
| `aef_index.csv` | 798 MB | Avoid; the footprint text makes it huge |

Index columns: `WKT`, `crs`, `path`, `year`, `utm_zone`, `utm_west`, `utm_south`, `utm_east`, `utm_north`, `wgs84_west`, `wgs84_south`, `wgs84_east`, `wgs84_north`.

Footprints are clipped to their UTM zone's longitude range, so none crosses the antimeridian.

### 4.4 File internals [V]

Read from the header of `2017/10N/x0dyfir8mjpv8ty4m-0000000000-0000000000.tiff`:

| Property | Value |
|---|---|
| Container | BigTIFF, little-endian |
| File size | 3.65 GB |
| Bands | 64, named `A00`–`A63`, stored as **separate planes** |
| Internal block | 1024 × 1024 cells |
| Blocks per band at L0 | 64 (8 × 8) |
| Compression | Code 50000 (Zstandard), no predictor |
| Compressed block, one band | 0.56–0.85 MB in the sample |
| Pyramid | 4096, 2048, 1024, 512, 256, 128, … down to 1 |
| Blocks per band at L3 and coarser | 1 |

The sidecar `.vrt` presents each file north-up: origin at the top-left corner, negative row step. The underlying file is stored bottom-up.

### 4.5 What the internals mean for reading

1. **A small window costs a whole block.** Any window inside one block needs 64 range requests, one per band, and about 40 MB of transfer per year. A 64 × 64 window costs the same as the 1024 × 1024 block around it.
2. **The natural sampling unit at L0 is one block:** 1024 × 1024 cells, 10.24 km square, about 1.05 million cell histories.
3. **Coarse levels are cheap.** From L3 down, one band is one block. The 64 band blocks of a level are likely stored next to each other, so one range read may fetch a whole level. Confirm from the offsets before relying on it.
4. **How the pyramid was built is undocumented.** Averaging shortens vectors. Renormalise after reading any coarse level. Compare one L1 block against the mean of the matching L0 cells to learn the method (task 0.7).
5. **Request count matters more than bytes at coarse levels.** Use HTTP/2, connection reuse and bounded concurrency. Back off on errors. Be a polite client on a free mirror.

### 4.6 Reading rules

- **MUST read through the `.vrt`, or flip explicitly.** Loading the raw files directly produced upside-down data in common tools until fixes landed in GDAL, Rasterio and TorchGeo. [S] Pin those versions and keep an orientation test in continuous integration (section 14.6).
- **MUST mask −128 before any arithmetic.**
- **MUST decode before use:** divide by 127.5, square, restore the sign.

```python
import numpy as np


def dequantize(values: np.ndarray) -> np.ndarray:
    """Stored int8 -> float32 in [-1, 1]. Apply the no-data mask first."""
    v = values.astype(np.float32)
    return ((v / 127.5) ** 2) * np.sign(v)
```

- **MUST check length after decoding.** Log the distribution of vector length per file. Drift signals a format or version change.
- **MUST record `DATASET_VERSION` with every sample.**
- **SHOULD store samples in the original 8-bit form** and decode at load time. It is four times smaller than 32-bit floats and loses nothing.

### 4.7 Ready-made loader

`aef-loader` (Apache-2.0) reads the mirror as lazy arrays, one dataset per UTM zone, and can reproject zones onto a common grid. It builds on `obstore`, `VirtualiZarr`, `virtual-tiff`, `odc-geobox` and `geopandas`, and reports twice the speed of a common alternative for single-tile reads. [V]

Its documentation does not say how it handles orientation, no-data or Python versions. Decision: evaluate it in Phase 0 against our own minimal reader (Appendix A.2). Adopt it only if it passes the orientation and decode tests; otherwise keep the minimal reader, which has fewer moving parts.

### 4.8 Supply risks specific to this dataset

| Risk | Control |
|---|---|
| Mirror removed or throttled | Local copy of all samples; fallback route tested quarterly |
| Past years reprocessed | Version pin; content digests in the lineage manifest; refuse mixed versions |
| A year arrives late | The exam date moves; the lock date does not |
| The yearly series ends | One year's notice is promised; second-source embeddings (section 5) kept warm |
| Licence terms change for future years | Past years remain CC-BY; legal review each release |

---

## 5. Second-source embeddings

Purpose: reduce dependence on one supplier, and open a path to forecasts faster than yearly.

| Product | What is known | Label | Role |
|---|---|---|---|
| TESSERA v2 | Open model; 10 m; 128 numbers per cell, stored as 8-bit plus a scale; global coverage for 2024, other years on request | [S] | First alternative for a model that runs on two sources |
| OlmoEarth v1.3 | 128 numbers per cell; a precomputed set readable from object storage; custom licence that may limit commercial use | [S] | Research comparison only until licence is read |
| Clay | Open-source model, Apache-2.0; compute embeddings yourself | [S] | Option if we must generate our own |
| Prithvi-EO-2.0 | Open weights; 30 m; compute embeddings yourself | [S] | Option; used by the reference method |

Findings that matter:

- The reference method accepts embeddings from several models at once through a separate input projection per model. [V] The architecture in section 15 keeps that property so a second source can be added without redesign.
- Published comparisons disagree on which embedding is best, and each comes from its own developer. [S] We do not rely on any ranking.
- AlphaEarth is the only product found with nine global yearly layers openly available. It stays primary.

Action: in Phase 3, run the T1 backtest on one region with a second source to measure how much skill depends on the supplier (task 3.9).

---

## 6. Data source register

Every dataset the project touches is listed here with its role, access, licence and evidence label. A dataset not in this register MUST NOT enter a pipeline.

### 6.1 Labels — forest

| ID | Dataset | Content | Resolution, cadence | Access | Licence | Label |
|---|---|---|---|---|---|---|
| LF1 | Global Forest Change v1.13 (Hansen, UMD, Google, USGS, NASA) | Tree cover 2000, loss year 2001–2025, gain | 30 m, yearly | `storage.googleapis.com/earthenginepartners-hansen/GFC-2025-v1.13/download.html` | CC-BY 4.0 [M] | Version [V] |
| LF2 | OPERA land-surface disturbance alert (DIST-ALERT-HLS v1) and annual summary (DIST-ANN-HLS) | Vegetation disturbance outside the historical norm | 30 m; alerts every few days, record from January 2023 | NASA Earthdata; AWS open data registry; Earth Engine | NASA open data [M] | [S] |
| LF3 | GLAD and RADD forest alerts | Optical and radar deforestation alerts | 10–30 m, weekly | Global Forest Watch; Wageningen | CC-BY 4.0 [M] | [M] |
| LF4 | EU Joint Research Centre global forest cover map for 2020 | Forest presence at the law's cut-off date | 10 m, single date | EU Forest Observatory | CC-BY 4.0 [M] | [M]; version unconfirmed |
| LF5 | Tropical Moist Forest change (Joint Research Centre) | Degradation and deforestation in humid tropics | 30 m, yearly | Joint Research Centre | Open [M] | [M] |
| LF6 | ForestCast benchmark | Inputs, training and evaluation data for deforestation-risk forecasting, Southeast Asia v1.0.0 | Tiles | Google Cloud Storage path `nature-trace/datasets/tfds/forestcast/southeast_asia/1.0.0` | Not stated on the announcement | [V] |

Notes:

- LF1's producers warn that combining the original 2000–2012 record with later years needs caution, and that a full reprocessing (version 2.0) is planned with no date. [V] Use only loss years 2018–2025, which fall in the newer processing era.
- LF2 is the fastest independent truth. It allows interim grading months before the yearly maps.
- LF6's licence MUST be confirmed before any commercial use. Research evaluation is the intended use.

### 6.2 Labels — built-up

| ID | Dataset | Content | Resolution, cadence | Access | Licence | Label |
|---|---|---|---|---|---|---|
| LB1 | Open Buildings 2.5D Temporal | Building presence, count, height | 4 m effective, yearly 2016–2023 | Earth Engine; Google Research site | CC-BY 4.0 or ODbL 1.0, user's choice | [V] |
| LB2 | Global Human Settlement Layer, 2023 package | Built-up surface, volume, height; population | 100 m at 5-year epochs 1975–2030; 10 m for 2018 | Joint Research Centre open data | CC-BY 4.0 [M] | [S] |
| LB3 | Overture Maps buildings | Building footprints from several sources | Vector, monthly | `s3://overturemaps-us-west-2/release/<version>/theme=buildings/type=building/` | ODbL [M] | Path [S] |
| LB4 | World Settlement Footprint | Settlement extent and evolution | 10–30 m | German Aerospace Center | CC-BY 4.0 [M] | [M] |
| LB5 | Microsoft global building footprints | Machine-detected footprints | Vector | GitHub release | ODbL [M] | [M] |

Notes:

- LB1 ends in 2023 and covers Africa, South and Southeast Asia, Latin America and the Caribbean. It grades 2018–2023 backtests in those regions only.
- LB2's 2025 and 2030 epochs are projections, not observations. They MUST NOT be used as truth.
- LB3 changes with mapping effort as well as with real construction. A new footprint is weak evidence of a new building.

### 6.3 Labels — land cover, water, crops, fire

| ID | Dataset | Content | Resolution, cadence | Licence | Label |
|---|---|---|---|---|---|
| LC1 | Dynamic World V1 | Nine-class probabilities per Sentinel-2 scene | 10 m, every few days, 2015-06-27 to present | CC-BY 4.0 | [S] |
| LC2 | ESA WorldCover 2020 and 2021 | Eleven-class map | 10 m, two years | CC-BY 4.0 [M] | [M] |
| LC3 | GLAD global land cover and land use change | Change 2000–2020 | 30 m | CC-BY 4.0 [M] | [M] |
| LW1 | Global Surface Water (Joint Research Centre) | Water occurrence and transitions | 30 m, yearly | Open [M] | [M] |
| LK1 | WorldCereal | Crop extent and type | 10 m | CC-BY 4.0 [M] | [M] |
| LX1 | Burned area (MCD64A1) and active fire (FIRMS) | Fire extent and detections | 500 m monthly; 375 m daily | NASA open data [M] | [M] |

Notes:

- LC1 is the main source for training readout probes because it has dates. Mask by top-class probability as its authors recommend. [S]
- LX1 separates fire-driven loss from clearing. Report both; a forecast that predicts fire scars is a different product from one that predicts clearing.

### 6.4 Drivers

Drivers are inputs to the model, not truth. Each carries a "valid as of" date.

| ID | Dataset | Feature derived | Licence | Commercial use | Label |
|---|---|---|---|---|---|
| DR1 | Overture transportation (mostly OpenStreetMap) | Distance to nearest road by class; road density | ODbL [M] | Allowed with share-alike duties (6.6) | Path [S] |
| DR2 | Copernicus 30 m elevation model | Elevation, slope | Free with attribution [M] | Allowed [M] | [M] |
| DR3 | World Database on Protected Areas | Inside protected area; category | Restricted [M] | **Needs permission** [M] | [M] |
| DR4 | ERA5-Land | Rainfall and temperature normals and anomalies | Copernicus licence [M] | Allowed [M] | [M] |
| DR5 | WorldPop | Population density | CC-BY 4.0 [M] | Allowed | [M] |
| DR6 | VIIRS night lights (Black Marble) | Radiance level and trend | NASA open data [M] | Allowed | [M] |
| DR7 | geoBoundaries | Country and first-level area codes | CC-BY 4.0 [M] | Allowed | [M] |
| DR8 | Travel time to cities | Accessibility | CC-BY 4.0 [M] | Allowed | [M] |
| DR9 | World Bank commodity prices | National-scale price signals for soy, beef, palm oil, gold, timber | Open [M] | Allowed | [M] |
| DR10 | Mining and concession polygons | Inside or near a concession | Varies by source | Check each | [M] |

Notes:

- **DR3 is a licence trap.** Do not use it in a commercial product without written permission. Until then, protected status comes from national open sources or is left out.
- **Do not use GADM for administrative boundaries.** Its licence forbids commercial use. [M] Use DR7.
- DR9 enters as a small set of country-year numbers. It is how the model can see a regime shift coming.

### 6.5 Imagery for checking and display

Raw imagery is not a model input. It is needed to check results by eye and to give users a picture behind the map.

| Use | Source | Note |
|---|---|---|
| Visual checks in Phase 0 and in grading | Sentinel-2 Level-2A through a public catalogue | Free; pick low-cloud scenes |
| Long history | Landsat Collection 2 | Free; some hosts bill the reader |
| Web basemap | Own yearly mosaic, or a paid basemap | Some popular free mosaics are non-commercial for recent years [M]. Check before embedding |

### 6.6 Licence duties

| Licence family | Duty | How we meet it |
|---|---|---|
| CC-BY 4.0 | Credit the source; say if changed | Attribution register generated from this section; shown in app, reports and repositories |
| ODbL | Credit; share a derived **database** under the same licence; keep it open | Keep ODbL-derived features in a separate, separately published table; legal review before weights trained on them are sold |
| Non-commercial or permission-based | No commercial use without permission | Excluded from pipelines by a licence gate in continuous integration |
| Not stated | Unknown | Treated as restricted until confirmed in writing |

A licence gate MUST run in continuous integration: each pipeline declares the register IDs it reads, and the build fails if any ID is marked restricted for the build's target (research or commercial).

### 6.7 Register maintenance

- One owner for the register.
- Every row gains a "verified on" date and a link to the licence text when its label moves from [M] or [S] to [V].
- Rows are re-verified every six months and before any commercial launch.
- All [M] rows in this section MUST reach [V] before Phase 6.

---

## 7. Volumes and storage maths

All figures are estimates [E] built from one measured file and the reported archive size. Replace them with counts from the index in task 0.2.

### 7.1 Files per year

- Reported archive: about 465 TB. [S]
- One full land tile at L0: 3.65 GB. [V]
- Implied object count: roughly 127,000 files, or about 14,000–16,000 per year. Tiles on coasts are smaller, so the true count is higher.
- **Counted in task 0.2 (2026-11-15) [V]: 302,466 files; 33,148–34,155 per year; 34,266 distinct tile footprints, 32,931 of them with all nine years.** The estimate above was low by a factor of 2.4. See `docs/phase0/index_counts.md`.

### 7.2 Size per tile-year by level

Compression ratio taken as 0.8, from the sampled blocks.

| Level | Cells | Uncompressed | Compressed [E] |
|---|---|---|---|
| L0 | 8192² | 4.29 GB | 3.65 GB [V] |
| L3 | 1024² | 67 MB | 53 MB |
| L4 | 512² | 16.8 MB | 13 MB |
| L5 | 256² | 4.2 MB | 3.4 MB |
| L6 | 128² | 1.05 MB | 0.85 MB |
| L7 | 64² | 0.26 MB | 0.21 MB |

### 7.3 Whole planet, by level [E]

Using 15,000 tiles a year. **Superseded by the count in 7.1: about 33,600 tiles a year, so every figure in this table, and the transfer and request figures in 7.5, should be scaled by roughly 2.2 until task 1.1 measures them. Measured level-0 blocks compress to 0.31–0.60 of raw size, not 0.8.**

| Level | One year | Nine years | Fits on the laptop (485 GB free)? |
|---|---|---|---|
| L0 | 55 TB | 490 TB | No |
| L3 | 0.8 TB | 7 TB | No |
| L4 | 0.2 TB | 1.8 TB | No |
| L5 | 50 GB | 450 GB | No; needs an external drive |
| L6 | 13 GB | 115 GB | **Yes** |
| L7 | 3 GB | 29 GB | Yes |

This table drives the plan: the whole planet at 640 m for all nine years would fit on the development laptop. Version 0.3 of this plan goes further and does not store it at all: the planet is streamed once, and only a sampled tenth is kept (sections 7.6 and 8.6).

### 7.4 Fine-resolution chips [E]

| Sample | Transfer | Cell histories |
|---|---|---|
| 1 chip (1024²), 1 year | 40 MB | 1.05 million |
| 1 chip, 9 years | 360 MB | 1.05 million |
| 200 chips, 9 years | 72 GB | 210 million |
| 500 chips, 9 years | 180 GB | 524 million |

### 7.5 Transfer time [E]

| Job | Bytes | At 20 Mbit/s | At 100 Mbit/s |
|---|---|---|---|
| Global L6, nine years | About 130 GB including headers | 14 hours | 3 hours |
| 200 chips at L0, nine years | 72 GB | 8 hours | 1.6 hours |
| 300 tiles at L3, nine years | 144 GB | 16 hours | 3.2 hours |

Request count for global L6 is about 135,000 files with two or three requests each. Run it overnight with at most 16 concurrent connections.

### 7.6 Disk plan for the laptop

The lean plan, adopted in version 0.3. All sizes [E].

| Store | Size | Location |
|---|---|---|
| Sampled global patches at L6, difference-encoded | 4–12 GB | `D:\almanac-data\patches-l6` |
| Labels and drivers for those patches | 2–4 GB | `D:\almanac-data\labels` |
| Per-tile change summaries from the streaming pass | Under 1 GB | `D:\almanac-data\summaries` |
| Global forecast and baseline layers | 1–3 GB | `D:\almanac-data\forecasts` |
| Working files and checkpoints | 15–20 GB | `D:\almanac-data\work` |
| **Total** | **About 30 GB** | |

What changed from the 280 GB plan:

| Before | Now | Saving |
|---|---|---|
| Whole planet at L6 kept on disk, 115–130 GB | Stream every tile once; keep about 10% of patches | About 105 GB |
| Stored values as read | First year plus year-to-year differences, compressed | 2–4× on what remains, to be measured in task 0.11 |
| Byte-exact raw cache on the laptop | Digests and object tags only; re-read from the mirror if needed | Up to 130 GB |
| 200 fine blocks downloaded in week 2, 72 GB | Deferred until after gate 2; then 20 m level first, about 18 GB | 72 GB now |
| Global inference from a local store | Stream a tile, score it, write the forecast, discard the tile | No store needed |

Transfer does not shrink: the streaming pass still reads about 130 GB from the mirror once. Only what is kept shrinks.

An external drive is now optional. It becomes useful again if the fine blocks or regional L3 stores are built.

---

## 8. Sampling design

### 8.1 Three datasets

| Name | Level | Coverage | Purpose |
|---|---|---|---|
| **G** — global | L6 | A fixed sample of about 10% of patches from every land tile, nine years (section 8.6) | Primary model; primary metric |
| **D** — detail | L1 first, then L0 | Up to 200 blocks chosen by strata | Does skill hold at fine scale; neighbourhood effects |
| **R** — regional | L3 | 300 tiles in chosen regions | Regional product; second-source comparison |

Build order: G in week 2; D only after gate 2 passes; R in Phase 3. The public global layer is produced by streaming inference, not from a stored copy.

### 8.2 Identifiers

- **Tile ID:** `<utm zone>_E<west>_N<south>`, the zone and the south-west corner in metres, for example `10N_E500000_N5079040`. Changed in Phase 0: the supplier's image id differs every year for the same footprint, so it cannot name a tile across years.
- **Block ID:** tile ID plus `_b<row>_<col>`, rows and columns 0–7 at L0.
- **Cell ID:** tile ID, level, row, column.
- IDs are derived from the supplier's paths, so they stay stable as long as the supplier's layout does. A mapping table is stored in case it changes.

### 8.3 Strata for dataset D

| Stratum | Blocks | How candidates are found |
|---|---|---|
| Forest frontier, humid tropics | 40 | Blocks with high loss in LF1 for 2018–2024, in the Amazon, Congo Basin and Southeast Asia |
| Forest change, dry and temperate | 20 | Same, in Gran Chaco, Cerrado, Miombo, boreal harvest zones |
| City edge, fast growth | 40 | Blocks with strong built-up gain in LB1 or LB2 around large and mid-sized cities on every continent |
| New infrastructure and mining | 20 | Blocks containing new dams, mines, highways, large solar farms |
| Cropland expansion or loss | 30 | Blocks with class transitions in LC1 or LC3 |
| Stable controls | 30 | Desert interior, old-growth interior, old urban core, permanent water |
| Random land | 20 | Uniform over land area |
| **Total** | **200** | |

Rules:

- No more than five blocks from one tile.
- Each continent with people on it gets at least 20 blocks.
- The list of chosen blocks, with the reason for each, is committed to the repository before download.

### 8.4 Split assignment

1. List all tiles in G.
2. Assign each tile to a 2° × 2° super-block.
3. Assign super-blocks to train, validation-region and test-region sets at 70 / 10 / 20 by a seeded hash of the super-block ID, stratified by continent.
4. Additionally hold out one named large region per continent from training entirely. The list is fixed in the pre-registration document.
5. Remove from training any tile that shares an edge with a test tile.
6. D and R inherit the side of the tile they sit in.

The time split of section 3.9 applies on top: the "test region, test year" corner is the headline.

### 8.5 Balancing within training

- Changed cells are rare. Each training batch is drawn half from cells with a change event in the target year and half uniformly.
- The loss is reweighted so that reported probabilities remain calibrated to the true base rate (section 15.6).
- Sampling weights are stored with the dataset version, not in code.

### 8.6 Lean storage: stream, sample, difference-encode

**Streaming pass.** One job visits every land tile once:

1. Read the tile's L6 level for all nine years into memory (about 8 MB).
2. Run the quality gates that need only this tile.
3. Compute change `δ` for every cell and year pair. Write a small per-tile summary: change counts per patch and year, no-data share, vector-length statistics.
4. Decide which of the tile's 16 patches (32 × 32 cells each) to keep, by the rule below.
5. Write kept patches to the store. Record the tile's object tags and digests. Discard the rest.

**Which patches are kept.** The rule is fixed and committed before the pass runs.

| Kind | Rule | Why |
|---|---|---|
| Changed | Every patch with at least one change event in any year | These carry the signal |
| Near change | Patches adjacent to a changed patch | The model must learn where change does **not** spread |
| Stable sample | A seeded random share of the remaining patches, stratified by continent and biome, sized so the total is about 10% of all patches | Without stable land the model cannot learn the base rate |
| Test tiles | In test-region tiles, the stable share is raised to at least 25% | Scores on the headline fold must not depend on a thin sample |

Each kept patch stores its **inclusion probability**. Training loss and every metric are weighted by its inverse, so results describe the whole planet, not the sample.

**Two-pass threshold.** The change threshold `τ` is needed to decide what counts as changed, but it is estimated from stable cells worldwide. So the pass first keeps the per-tile `δ` histograms, `τ` is fixed from those (task 1.8), and patch selection runs from the summaries. If summaries are too coarse for that, a provisional `τ` from Phase 0 is used for selection, and the final `τ` is applied afterwards to the kept data.

**Difference encoding.** Store year one as read, then for each later year the stored value minus the previous year's, as 8-bit integers with wrap-around. It is lossless. Because most cells barely change, the differences cluster near zero and compress well. The gain is unmeasured; task 0.11 measures it on the Phase 0 sites before the format is adopted.

**No raw cache on the laptop.** The lineage manifest keeps addresses, object tags and digests. If a tile is needed again it is re-read from the mirror. This trades storage for dependence on the mirror; the cloud environments still keep a raw cache (section 10.5).

**Things this makes harder, accepted knowingly:**

- A change of threshold, patch size or sampling rule means re-streaming the planet: about 130 GB of transfer and a night.
- Baseline B3 needs change events from neighbouring patches. The per-tile summaries hold those, so B3 is computed from summaries, not from the patch store.
- Any analysis of land that was not sampled needs a new read.
- If the mirror disappears, unsampled data is gone from our side. Risk R04 rises from low to medium.

---

## 9. Data quality, contracts, versioning

### 9.1 Quality gates

A sample store is not usable until every gate passes. Gates run in the pipeline and their results are stored with the dataset version.

| Gate | Check | Fail action |
|---|---|---|
| Q1 Orientation | A fixed block over a known coastline matches a reference water mask north-up | Stop the pipeline |
| Q2 Georeference | Centre of a known landmark falls within one cell of its surveyed position | Stop |
| Q3 No-data | Share of −128 per file within expected bounds for its footprint | Flag file |
| Q4 Vector length | After decoding, 99% of valid cells have length in [0.98, 1.02] at L0 | Flag file |
| Q5 Version | `DATASET_VERSION` equal across all years of a tile | Reject tile |
| Q6 Year completeness | All nine years present for a tile | Mark tile incomplete; exclude from training |
| Q7 Stability | At stable control sites, `δ` distribution matches the Phase 0 record within tolerance | Investigate before training |
| Q8 Integrity | Stored object tags match those recorded at download | Re-download |
| Q9 Duplicates | No two samples share a cell and year | Reject |
| Q10 Pyramid consistency | A coarse level equals the renormalised mean of the level below within tolerance, or the measured method | Rebuild coarse levels ourselves |

### 9.2 Contract for a sample store

| Array | Shape | Type | Meaning |
|---|---|---|---|
| `emb` | `[tile, year, band, row, col]` | int8 | Stored values, undecoded |
| `valid` | `[tile, year, row, col]` | bool | False where any band is −128 |
| `label_<id>` | `[tile, year, row, col]` | uint8 or float16 | One array per label source, resampled to the level |
| `driver_<id>` | `[tile, row, col]` | float16 | One array per driver |

Required attributes on the store: level, list of years, tile IDs, input dataset version, supplier object tags, download date range, pipeline code commit, gate results, split assignment version.

Chunking: one chunk per tile-year for `emb` at L6 (about 1 MB). At L0, one chunk per block-year-band group of eight bands.

### 9.3 Versioning and lineage

- **Every dataset has an immutable version ID.** A new download, a new gate result or a new split makes a new version.
- **Storage with snapshots.** The sample stores live in a transactional array store that supports commits and rollbacks (section 13). On the laptop, a plain Zarr directory plus a manifest file with digests is enough for Phase 0–2.
- **Lineage manifest.** A JSON file per version: for each object read, the address, object tag, byte range, read time; for each array written, its digest.
- **Model runs name a dataset version.** A training run that does not record one is discarded.
- **Data card.** Each dataset version ships with a filled data card (Appendix C.3).

### 9.4 Refresh procedure when a new year arrives

1. Poll the mirror's index weekly from 15 January.
2. For each tile with the new year present, read the needed levels and append to a **new** dataset version.
3. Run all gates.
4. Trigger grading of the locked forecast for that year on the tiles that arrived (section 12).
5. Do not retrain until coverage of the new year exceeds 95% of land tiles.

---

# PART C — PLATFORM

## 10. System architecture

### 10.1 Design principles

1. **Batch first.** Forecasts are made once per issue and never change. Serving is reading files, not running models.
2. **Immutable artefacts.** Datasets, models, forecast packages and grades are versioned and never overwritten.
3. **Everything addressable.** Any number shown to a user can be traced to a package digest, a model version, a dataset version and a code commit.
4. **Compute next to data.** The mirror's bucket is in `us-west-2`. Cloud compute runs in the same region so reads are fast and in-region.
5. **Boring infrastructure.** Managed services over self-run clusters until load proves otherwise. No Kubernetes before general availability.
6. **Laptop to cloud without rewrites.** The same pipeline code runs against a local folder or object storage, selected by configuration.
7. **Integrity is the product.** The threat that matters most is someone, including us, altering a forecast after the fact. The registry is designed against that first.

### 10.2 Component diagram

```
              +--------------------------- control plane ----------------------------+
              | orchestrator | dataset registry | model registry | secrets | CI/CD   |
              +----------------------------------------------------------------------+

 SOURCES          INGEST                 STORES                 COMPUTE          REGISTRIES
+---------+   +---------------+   +--------------------+   +---------------+   +-----------------+
| mirror  |-->| readers       |-->| sample stores      |-->| training      |-->| model registry  |
| labels  |   | quality gates |   | (versioned arrays) |   | (GPU)         |   +--------+--------+
| drivers |   +---------------+   | label and driver   |   +---------------+            |
+---------+                       | stores             |                                v
                                  +---------+----------+   +---------------+   +-----------------+
                                            |              | batch         |-->| forecast        |
                                            +------------->| inference     |   | registry (lock) |
                                                           +---------------+   +--------+--------+
                                                                                        |
+---------+   +---------------+   +--------------------+                                v
| truth   |-->| grading       |-->| scorecard site     |<------ forecasts -----+-----------------+
| arrives |   | service       |   | (static, public)   |                       | serving:        |
+---------+   +---------------+   +--------------------+                       | interface,      |
                                                                               | tiles, web app  |
                                                                               +-----------------+
```

### 10.3 Components

| Component | Responsibility | State it owns |
|---|---|---|
| Readers | Windowed and pyramid reads from the mirror; decode; mask | None |
| Quality gates | Run section 9.1 checks; write results | Gate reports |
| Sample stores | Hold embeddings, labels, drivers on a common grid per level | Versioned arrays |
| Dataset registry | Map dataset version to location, lineage, gates, split | Catalogue |
| Training | Fit models; log runs | Checkpoints, metrics |
| Model registry | Hold approved models with cards and promotion status | Model artefacts |
| Batch inference | Apply a model to a dataset version; write forecast layers | Forecast layers |
| Forecast registry | Package, digest, sign, timestamp, publish, lock | Immutable packages |
| Grading service | Fetch truth; score against baselines; publish | Grade records |
| Scorecard site | Show every issue and its grade | Static files |
| Serving | Interface, tiles, reports, web app | Accounts, usage |
| Orchestrator | Schedule and track every pipeline step | Run history |

### 10.4 Environments

| Environment | Where | Data | Purpose | Who can write |
|---|---|---|---|---|
| Local | Developer laptop | G at L6; D chips | Research, Phases 0–3 | Developer |
| Dev | Cloud account A | Subsets | Integration, pipeline tests | Engineers |
| Staging | Cloud account B | Full copy of latest issue | Release rehearsal, load tests | Pipeline only |
| Production | Cloud account C | Everything | Customers and public | Pipeline only, with approval |

Rules:

- Separate cloud accounts per environment. No shared credentials.
- Promotion is by artefact digest, never by rebuild.
- No human writes to production storage. Break-glass access is logged and reviewed.

### 10.5 Storage layout

One bucket per purpose per environment. Names below are patterns.

| Bucket | Content | Protection |
|---|---|---|
| `almanac-<env>-raw-cache` | Byte-exact copies of objects read from suppliers | Versioning on; lifecycle to cold storage after 90 days |
| `almanac-<env>-stores` | Sample, label and driver stores | Versioning on |
| `almanac-<env>-models` | Checkpoints and registered models | Versioning on |
| `almanac-<env>-forecasts` | Locked forecast packages | **Object lock, compliance mode, 10 years**; versioning on |
| `almanac-<env>-grades` | Grade records | Object lock, compliance mode |
| `almanac-<env>-public` | Public layers, scorecard site, open benchmark | Read-only public; versioning on |
| `almanac-<env>-logs` | Access and audit logs | Write-once; 1 year minimum |

Prefix convention inside the forecasts bucket:

```
issues/<issue_id>/
  manifest.json
  model_card.md
  prereg.md
  layers/<layer>/<level>/<utm_zone>/<tile_id>.tif
  tiles/<layer>/<level>.pmtiles
  aggregates/<scheme>/<layer>.parquet
  signatures/
  timestamps/
```

### 10.6 Formats

| Data kind | Format | Why |
|---|---|---|
| Arrays for training (embeddings, labels, drivers) | Zarr version 3 in a transactional store | Chunked, parallel, versioned snapshots |
| Forecast layers for analysis | Cloud-optimised GeoTIFF, native UTM, one file per tile and level | Range-readable; every GIS tool opens it; authoritative grid |
| Forecast layers for display | Raster tiles packed in PMTiles, Web Mercator | One file per layer on a CDN; no tile server for coarse levels |
| Tables (index, aggregates, usage exports) | GeoParquet | Columnar; queryable in place |
| Catalogue | STAC items and collections | Standard discovery for partners |
| Manifests, cards, grades | JSON and Markdown | Human and machine readable; diffable |

The analysis grid is the supplier's native UTM grid. Display tiles are a rendering, never the source of a number.

### 10.7 Pipelines

Each pipeline is a graph of assets partitioned by year, tile and level. Every step is idempotent: running it twice with the same inputs produces the same outputs and no duplicates.

| Pipeline | Trigger | Partitions | Output |
|---|---|---|---|
| `index_sync` | Weekly; daily from 15 January | — | Local copy of the supplier index; diff report |
| `ingest_embeddings` | New index rows, or backfill | year × tile × level | Raw cache objects; sample store chunks |
| `ingest_labels` | New label release | source × year × tile | Label arrays on the model grid |
| `ingest_drivers` | Quarterly | source × tile | Driver arrays with "valid as of" dates |
| `quality_gates` | After any ingest | dataset version | Gate report; pass or block |
| `build_dataset` | Manual, with approval | dataset version | Frozen dataset version with split |
| `train` | Manual | run | Checkpoints, metrics, candidate model |
| `evaluate` | After train | model × dataset | Backtest report against baselines |
| `infer` | Manual, with approval | model × year × tile × level | Forecast layers |
| `package_and_lock` | Manual, two-person approval | issue | Locked package (section 11) |
| `grade` | New truth | issue × truth source × tile | Grade records (section 12) |
| `publish` | After lock or grade | issue | Scorecard pages, public layers, catalogue |

Operational rules:

- Retries with exponential backoff and jitter on network reads. A cap on concurrent connections to any free supplier.
- A failed partition never blocks its siblings.
- Every run records code commit, container digest, dataset version and configuration digest.
- Backfills are ordinary runs over a partition range, not special scripts.

### 10.8 Batch inference sizing [E]

Assumption to be measured in Phase 2: a mid-range cloud GPU scores 50,000 cells a second with the medium model.

| Level | Cells per year | GPU-hours | Cost at $1 an hour |
|---|---|---|---|
| L6 | 0.25 billion | 1.4 | $1.40 |
| L5 | 1.0 billion | 5.5 | $5.50 |
| L3 | 15.7 billion | 87 | $87 |
| L0 | 1.0 trillion | 5,600 | $5,600, plus reading 55 TB |

Consequences:

- Global L6 and L5 inference is trivial and runs on the laptop.
- Global L3 is a routine cloud job.
- Global L0 is not worth running. L0 is produced on request for named areas.

### 10.9 Serving path

```
client -> CDN -> gateway (auth, rate limit, metering)
                    |-> point/polygon service -> forecast files (range reads) + aggregates (parquet)
                    |-> tile service ---------> PMTiles on CDN (coarse) or dynamic tiles (L3)
                    |-> report service -------> templated document from the same queries
                    |-> account service ------> relational database
```

- Point and polygon queries read forecast files directly with range requests. No database holds forecast values.
- Polygon queries on large areas use precomputed aggregates: per administrative area, and per hexagonal cell at two sizes.
- Responses carry `issue_id`, `package_digest` and a link to the manifest, so any client can verify what it received.
- Results are cached by `(issue_id, query digest)`. Because issues never change, cache entries never expire.

### 10.10 Tenancy and metering

- One logical tenant per customer organisation. Keys are scoped to a tenant and to a set of permitted layers and levels.
- Customer areas of interest are confidential. They are stored encrypted, never logged in clear, never used for anything but that customer's requests.
- Usage is metered per request and per square kilometre scored. Metering events are append-only.

### 10.11 Failure handling

| Failure | Behaviour |
|---|---|
| Supplier unreachable | Ingest pauses and alerts; serving unaffected |
| A tile fails a quality gate | Tile excluded; issue ships with a coverage map that shows the gap |
| Inference job dies midway | Restart resumes at the first unfinished partition |
| Lock step interrupted | Nothing is published; the partial package is discarded and rebuilt |
| Truth arrives corrupted | Grade withheld; incident opened |
| Serving region down | Static scorecard and coarse tiles stay up on the CDN; interface returns a clear error |

---

## 11. Forecast registry

### 11.1 Requirements

| # | Requirement |
|---|---|
| R1 | A locked package MUST be impossible to alter without detection |
| R2 | The time of locking MUST be attested by parties outside our control |
| R3 | Anyone MUST be able to verify R1 and R2 without our cooperation |
| R4 | The package MUST contain everything needed to regenerate it |
| R5 | Locking MUST require two people |
| R6 | A superseded issue MUST remain visible, marked as superseded, with its grade |

### 11.2 Package contents

| Item | Purpose |
|---|---|
| Forecast layer files | The forecast itself |
| `manifest.json` | List of every file with size and SHA-256 digest; the package digest |
| `prereg.md` | The pre-registration: metrics, baselines, win condition, grading code version |
| `model_card.md` | What the model is, its training data, limits, backtest results |
| `data_card.md` | Dataset version, sources, gates, known gaps |
| `environment.lock` | Exact dependency versions and container digest |
| `code_ref.txt` | Repository address and commit digest |
| `coverage.parquet` | Which tiles are included and why any are missing |
| `baselines/` | The baseline forecasts for the same cells, locked alongside |

Baselines are locked with the forecast so that the comparison cannot be tuned after the truth is known.

### 11.3 Package digest

1. Compute SHA-256 of every file.
2. Sort entries by path.
3. Write `manifest.json` in canonical form: sorted keys, no insignificant whitespace, UTF-8.
4. The **package digest** is SHA-256 of that manifest.

A skeleton is in Appendix A.10.

### 11.4 Locking procedure

Performed by two people on a call, following the checklist in Appendix D.3.

| Step | Action | Attestation it creates |
|---|---|---|
| 1 | Freeze: tag the code commit; record dataset and model versions | Signed tag |
| 2 | Build the package in the pipeline; compute digests | — |
| 3 | Independent rebuild by the second person from the same inputs; digests MUST match | Reproducibility |
| 4 | Sign the manifest with a transparency-logged signature | Public log entry with time |
| 5 | Request a timestamp token for the package digest from two independent timestamp authorities | Two signed tokens under the internet standard for trusted timestamps |
| 6 | Anchor the digest in a public blockchain through an open timestamping service | Proof independent of any company |
| 7 | Deposit the package, or its manifest and coarse layers, in a research archive that issues a permanent identifier | Dated, immutable public record |
| 8 | Publish a release in the public repository containing the manifest and proofs | Public history |
| 9 | Write the package to the object-locked bucket | Storage that we cannot overwrite |
| 10 | Announce the digest publicly on at least two channels | Third-party copies |

Steps 4–8 are redundant on purpose. Any one of them surviving is enough.

### 11.5 What is public and what is paid

| Content | Public at lock | Paid |
|---|---|---|
| Manifest and all proofs | Yes | — |
| Global L6 layers | Yes, CC-BY | — |
| Baselines at L6 | Yes | — |
| L5 and L3 layers | Digest only | Delivered to customers; made public when graded |
| L0 on-request layers | Digest only | Delivered to the requesting customer |

Because the digest of every paid file is in the public manifest, a paid layer can be proven afterwards to have existed, unaltered, at lock time. Paid layers become public once graded, so the full record can be checked by anyone.

### 11.6 Verification by a third party

1. Download the manifest and the proofs.
2. Recompute the manifest's digest; compare with the announced package digest.
3. Verify the signature against the public transparency log.
4. Verify each timestamp token and the blockchain proof.
5. Download any file; recompute its digest; compare with the manifest.

A script for these steps ships in the public repository and is itself covered by step 1 of the lock.

### 11.7 Issue numbering and supersession

- `issue_id` is `<year>.<sequence>`, for example `2027.01`.
- A correction creates `2027.02` with `supersedes: 2027.01` in its manifest and a plain-language reason.
- Both are graded. The scorecard shows both.

---

## 12. Grading service

### 12.1 Principle

The grader is written, tagged and locked **before** the truth exists. Its code version is named in the pre-registration. Changing the grader after truth arrives is a correction with its own public record, and the original grade stays visible.

### 12.2 Truth sources and timing

| Truth | Arrives | Grades |
|---|---|---|
| New yearly embedding layer | From late January, zone by zone [S] | T1, T2, T5 |
| Disturbance alerts (LF2) | Continuously | Interim forest readout, quarterly |
| Yearly forest-loss map (LF1) | Once a year | Final forest readout |
| Land-cover probabilities (LC1) | Continuously | Built-up, crop and water readouts |
| Building datasets (LB1, LB3) | Irregular | Built-up readout where available |

### 12.3 Procedure

1. **Detect.** `index_sync` reports new truth for a locked issue.
2. **Fetch and gate.** Truth passes the same quality gates as training data.
3. **Align.** Truth is brought to the forecast's grid and level by the method fixed in the pre-registration.
4. **Derive events.** Compute `δ` and change events with the locked threshold; derive label transitions.
5. **Score.** Compute every metric in section 3.8 for the model and for each locked baseline.
6. **Stratify.** Report by continent, biome, level, horizon, and split side (seen region or held-out region).
7. **Quantify uncertainty.** Paired block bootstrap over tiles, 2,000 draws.
8. **Judge.** Apply the win condition exactly as written.
9. **Record.** Write an immutable grade record with digests of truth, forecast and grader.
10. **Publish.** Update the scorecard.

### 12.4 Partial and final grades

- A **partial grade** is published when at least 20% of land tiles have truth. It is labelled partial and lists the zones covered.
- The **final grade** is published when coverage reaches 95%, or 120 days after first arrival, whichever comes first.
- The final grade is the one that counts for the win condition.

### 12.5 Scorecard content

For each issue:

- Verdict against the win condition, in one sentence.
- Primary metric for the model and every baseline, with intervals.
- Skill by continent and biome, as a small table.
- Reliability curve.
- Precision in the top 0.1%, 1% and 5% of area.
- Ten best hits and ten worst misses, each with before and after imagery.
- Coverage map.
- Links to the manifest, proofs, grader version and raw grade records.

Misses are shown with the same prominence as hits.

### 12.6 Guarding against self-deception

| Risk | Guard |
|---|---|
| Truth and forecast share a supplier, so a supplier-wide artefact looks like skill | Headline readout grades use independent labels; embedding-change grades are reported separately |
| Reprocessed truth for the cutoff year changes the baseline | Change events use the cutoff-year layer as it was at lock time, stored in the raw cache |
| Threshold tuned after the fact | Threshold is in the locked package |
| Favourable regions emphasised | Stratified tables are fixed in the pre-registration |
| Quietly dropping a bad issue | Requirement R6; the scorecard is generated from the registry listing |

---

## 13. Technology stack

Each row is a recommendation with the reason and the alternative. Versions are pinned at setup and recorded in the lock file; version numbers below are those found on 2026-11-14.

### 13.1 Languages and runtime

| Need | Choice | Why | Alternative |
|---|---|---|---|
| Main language | Python 3.12 or 3.13 | Widest geospatial wheel coverage. The laptop has 3.14; the deep-learning library publishes 3.14 Windows wheels [S], but mapping libraries may lag. Decide in task 0.1 by installing | Python 3.14 if every dependency installs cleanly |
| Environment and packaging | `uv` with a committed lock file | Fast, reproducible, manages Python versions | `pixi` if a library needs conda-forge builds |
| Performance-critical readers | Python first; Rust extension only if profiling demands | Avoid early complexity | — |
| Web front end | TypeScript | Type safety for a map-heavy app | — |

### 13.2 Geospatial and array libraries

| Need | Choice | Why | Alternative |
|---|---|---|---|
| Raster reads | Rasterio on GDAL, pinned to a version with the orientation fix | Reads the sidecar files; mature | `aef-loader` after evaluation; `async-tiff` for high-volume reads |
| Object storage access | `obstore` | Fast, one interface for local and cloud | `fsspec` |
| Arrays | Zarr version 3; Xarray on top | Chunked, labelled, parallel | NumPy memory maps on the laptop for Phases 0–1 |
| Versioned array store | Icechunk (1.0 released July 2025; 2.x current [S]) | Transactions, snapshots, rollbacks on object storage | Plain Zarr plus manifest files |
| Tables | DuckDB with its spatial extension; GeoParquet | Query the 78 MB index and aggregates in place | GeoPandas for small work |
| Projections | PyProj | Standard | — |
| Zonal statistics | `exactextract` | Correct handling of partial cells | Rasterstats |
| Vector tiles and display tiles | PMTiles | Single-file archives on a CDN | Dynamic tile server only |
| Dynamic tiles | TiTiler | Serves cloud-optimised files directly | — |
| Catalogue | STAC, with `pystac` | Partners expect it | — |

### 13.3 Machine learning

| Need | Choice | Why | Alternative |
|---|---|---|---|
| Framework | PyTorch (2.15.0 current [S]) | Reference code uses it; broad support | — |
| GPU build | Use the official install selector. Builds for CUDA 12.8 were dropped from the matrix in 2.14 and CUDA 13 is the default [S]; the laptop's GPU family is supported from 2.7 with CUDA 12.8 or newer [S] | Avoids a silent CPU-only install | — |
| Training loop | Plain PyTorch with a thin in-house trainer | Full control; few dependencies | Lightning |
| Tabular baseline | LightGBM | The strong simple competitor | XGBoost |
| Classical metrics | scikit-learn, SciPy | Standard | — |
| Experiment tracking | MLflow, self-hosted | Open source; model registry included | Weights & Biases |
| Hyperparameter search | Optuna, small budgets | Enough for this scale | — |
| Geospatial model utilities | TorchGeo, only where it saves work | An embedding-loading interface was added in 2026 [S] | Own code |

### 13.4 Platform

| Need | Choice | Why | Alternative |
|---|---|---|---|
| Cloud | AWS, region `us-west-2` | Same region as the mirror | Any, with egress cost considered |
| Infrastructure as code | OpenTofu | Reviewable, repeatable environments | Terraform |
| Orchestrator | Dagster | Asset-centred; partitions and lineage built in | Prefect; Airflow |
| Batch compute | Managed batch service on spot capacity | Cheap fan-out, no cluster to run | Ray or Dask clusters |
| GPU training in the cloud | Specialist GPU cloud by the hour | Lower hourly price than general clouds [S] | Managed training service |
| Containers | Docker images built in CI, signed, referenced by digest | Reproducibility | — |
| Interface service | FastAPI on a managed container service | Typed, documented by default | — |
| Relational database | Managed PostgreSQL | Accounts, keys, usage | — |
| Cache and rate limits | Managed Redis-compatible store | Standard | — |
| CDN and edge | A CDN with range-request support in front of the public bucket | Tiles and scorecard stay up under load | — |
| Identity | A hosted identity provider with single sign-on and multi-factor | Do not build auth | — |
| Secrets | Cloud secrets manager; no secrets in code or images | Standard | — |

### 13.5 Engineering tools

| Need | Choice |
|---|---|
| Source control | Git; hosted repository with branch protection |
| CI/CD | Hosted runners; workflows pinned to commit digests |
| Lint and format | Ruff |
| Types | Pyright in strict mode for library code |
| Tests | Pytest, Hypothesis |
| Data validation | Pydantic for records; Pandera for tables |
| Pre-commit | `pre-commit` with lint, types, secret scan |
| Dependency audit | `pip-audit` and an open vulnerability database scanner |
| Static analysis | CodeQL or Semgrep |
| Secret scanning | Gitleaks |
| Image and IaC scanning | Trivy; Checkov |
| Software bill of materials | CycloneDX, generated per image |
| Signing | Sigstore `cosign`, keyless |
| Observability | OpenTelemetry; Prometheus and Grafana, or a managed equivalent |
| Error tracking | Sentry or equivalent |
| Docs | Markdown in the repository; a static docs site |

### 13.6 Front end

| Need | Choice | Why |
|---|---|---|
| Framework | React with a static-first build | Scorecard pages are static; the app is an island |
| Map | MapLibre GL JS | Open source; PMTiles support |
| Large overlays | deck.gl | Many points and polygons without lag |
| Charts | A small declarative chart library | Reliability curves, score tables |
| Accessibility | WCAG 2.2 level AA as a release gate | Public-sector buyers require it |

### 13.7 What we deliberately do not use yet

| Not used | Until |
|---|---|
| Kubernetes | Sustained load or multi-region needs exceed managed containers |
| A feature store | More than one model family shares features |
| A vector database | A similarity-search product is on the roadmap |
| Streaming infrastructure | Inputs arrive faster than yearly |
| Own GPU hardware beyond the laptop | Cloud GPU spend exceeds the cost of ownership for six months running |

---

# PART D — ENGINEERING

## 14. Repository and engineering standards

### 14.1 Repository layout

One repository until the team exceeds eight engineers.

```
almanac/
  README.md
  BLUEPRINT.md
  LICENSE
  NOTICE                      # attribution register, generated
  pyproject.toml
  uv.lock
  .pre-commit-config.yaml
  .github/workflows/          # ci.yml, release.yml, nightly.yml
  docs/
    adr/                      # architecture decision records
    runbooks/
    prereg/                   # pre-registration documents, one per issue
    cards/                    # model and data cards
  configs/
    datasets/                 # one file per dataset version
    models/                   # one file per model configuration
    runs/                     # one file per training or inference run
    register.yaml             # data source register in machine form
  src/almanac/
    io/                       # readers, index, object storage, raw cache
    grid/                     # tile, block and cell identifiers; levels; transforms
    quality/                  # gates Q1-Q10
    data/                     # sample stores, labels, drivers, splits, samplers
    baselines/                # B0-B5
    models/                   # architecture, heads, losses
    train/                    # trainer, schedules, checkpoints
    evaluate/                 # metrics, bootstrap, reports
    infer/                    # batch inference, layer writers
    registry/                 # packaging, digests, signing, timestamps, verification
    grading/                  # truth alignment, scoring, grade records
    serve/                    # interface, tiles, reports
    cli/                      # command-line entry points
    common/                   # config, logging, errors, types
  pipelines/                  # orchestrator asset definitions
  infra/                      # infrastructure as code, per environment
  web/                        # scorecard site and map app
  tests/
    unit/
    property/
    golden/                   # small fixed fixtures with expected outputs
    integration/
    e2e/
  tools/                      # one-off scripts; nothing here is imported by src
  notebooks/                  # exploration only; never a source of truth
```

### 14.2 Module boundaries

| Rule | Reason |
|---|---|
| `io`, `grid`, `common` import nothing from the rest | They are the foundation |
| `models` does not import `io` | Models are testable with synthetic arrays |
| `registry` and `grading` do not import `train` or `models` | The grader must run without the training stack |
| `serve` reads only locked packages | Serving cannot depend on unreleased state |
| Nothing in `src` imports from `tools` or `notebooks` | One-off code stays one-off |

Import rules are enforced by a lint check in continuous integration.

### 14.3 Coding standards

- Type hints on every public function. Library code passes the type checker in strict mode.
- Arrays carry their axis order in the variable name or in a typed wrapper: `emb_tchw`, not `x`.
- No silent defaults for anything that changes results. Thresholds, seeds, levels and years come from configuration.
- Errors are specific and carry context: tile ID, year, level, object address.
- Network code has timeouts, bounded retries and a concurrency cap. No unbounded loops over a supplier.
- Logging is structured (JSON), with run ID and dataset version on every line.
- No notebook output is evidence. A result exists when a command reproduces it from a clean checkout.

### 14.4 Configuration

- One typed configuration object per run, loaded from a file in `configs/` and validated on load.
- The canonical form of the configuration is hashed. The digest is stored with every artefact the run produces.
- Environment variables are used only for secrets and for selecting the environment.
- A run that cannot be described by one committed file plus one commit digest is not allowed to produce a registered artefact.

### 14.5 Command-line surface

| Command | Purpose |
|---|---|
| `almanac index sync` | Fetch or refresh the supplier index; print a diff |
| `almanac index query --bbox … --years …` | List tiles and addresses for an area |
| `almanac fetch block --tile … --block … --years …` | Download one L0 block for the given years |
| `almanac fetch level --level 6 --years … --where …` | Download a pyramid level for many tiles |
| `almanac gates run --dataset …` | Run quality gates; write the report |
| `almanac dataset build --config …` | Freeze a dataset version with its split |
| `almanac baseline run --name … --dataset …` | Produce baseline forecasts |
| `almanac train --config …` | Train a model |
| `almanac evaluate --model … --dataset … --fold …` | Backtest against baselines |
| `almanac infer --model … --dataset … --level …` | Write forecast layers |
| `almanac package build --issue …` | Assemble a package and compute digests |
| `almanac package lock --issue …` | Sign, timestamp, deposit, publish |
| `almanac package verify <manifest>` | Third-party verification |
| `almanac grade --issue … --truth …` | Score a locked issue |

### 14.6 Testing strategy

| Layer | What it proves | Examples |
|---|---|---|
| Unit | A function does what it says | Tile ID parsing; level arithmetic; decode formula on hand values; cosine change on known vectors |
| Property | An invariant holds for any input | Decode then re-encode returns the original integers; decoded vectors of valid cells have length near 1; metrics are invariant to cell order |
| Golden | Real data reads correctly | A stored 64 × 64 crop from one real block, with the expected first values, shape, transform and orientation |
| Orientation | North is up | Described below |
| Schema | Stores and records match their contracts | Sample store attributes present; grade record validates |
| Pipeline | Steps compose | A synthetic two-tile, three-year supplier served from a local folder runs end to end |
| Model | The network can learn and is deterministic | Overfits one batch to near-zero loss; same seed gives the same loss; output shapes; masked years do not leak |
| Metric | Scores are right | Average precision and fractions skill score against hand-computed cases; bootstrap interval covers a known value |
| Registry | Tampering is caught | Change one byte in a packaged file; verification fails |
| End to end | The exam works | Tiny dataset: lock a forecast, reveal held-back truth, grade, render the scorecard |
| Load | Serving meets targets | Replay of realistic query mixes against staging |

**The orientation test in detail.** It guards against the known upside-down failure.

1. Fix one block that contains a coastline with an obviously asymmetric shape.
2. Store a small reference water mask for that extent, derived from an independent source.
3. In the test, read the block through the production reader and apply a frozen water probe.
4. Assert that agreement with the reference exceeds 0.8, and that agreement after flipping the array vertically is below 0.5.
5. Run it on every dependency update.

Coverage targets: 90% line coverage in `grid`, `io`, `quality`, `evaluate`, `registry`, `grading`; 70% elsewhere. Coverage is a floor, not a goal.

### 14.7 Continuous integration

| Stage | Runs on | Contents |
|---|---|---|
| Fast checks | Every push | Format, lint, import rules, types, unit and property tests, secret scan |
| Data checks | Every pull request | Golden and orientation tests against cached fixtures; schema tests; licence gate |
| Build | Every pull request | Container image, software bill of materials, vulnerability scan |
| Integration | Merge to main | Pipeline test on the synthetic supplier; model tests on CPU |
| Nightly | Schedule | End-to-end exam on the tiny dataset; dependency audit; a live read of one real block to detect supplier changes |
| Release | Tag | Signed images; documentation build; changelog |

Rules: workflows pin third-party actions by commit digest; no secret is available to pull requests from forks; a red main branch stops all merges.

### 14.8 Branching and review

- Short-lived branches from `main`; squash merge.
- Every change is reviewed by one other person. Changes to `registry`, `grading`, metrics, splits or thresholds need two reviewers.
- Commits follow a conventional format (`feat:`, `fix:`, `data:`, `eval:`), so the changelog can be generated.
- A pull request states what was tested and how to reproduce it.

### 14.9 Versioning

| Artefact | Scheme | Example |
|---|---|---|
| Code | Semantic versioning | `0.4.2` |
| Dataset | Name, level, date, short digest | `G-L6-20261128-3f9a1c` |
| Model | Family, size, dataset, sequence | `almanac-M-G-L6-003` |
| Issue | Year and sequence | `2027.01` |
| Grader | Semantic versioning, tagged before truth | `grader-1.0.0` |
| Interface | Major version in the path | `/v1/` |

### 14.10 Reproducibility rules

1. Every run fixes seeds for Python, NumPy and the deep-learning library, and records them.
2. Deterministic algorithms are switched on for registered runs. If an operation has no deterministic form, the run records that and the expected variation.
3. The container digest and lock file are recorded with every artefact.
4. A registered model MUST be reproducible within a stated tolerance by a second person from the recorded inputs before it is used for a locked issue.
5. Data loading order is seeded. Worker count is part of the configuration.

### 14.11 Documentation

- Every pipeline has a runbook: what it does, inputs, outputs, how to rerun, common failures.
- Every public layer has a one-page method note in plain language.
- The README lets a new engineer run the tiny end-to-end exam within one hour.

### 14.12 Definition of done

A change is done when: tests exist and pass; the configuration is committed; the result is reproducible from a clean checkout; documentation and runbook are updated; the change is reviewed; and, if it alters a number anyone has seen, the change log says so.

---

## 15. Model engineering

### 15.1 Shape of the problem

The model sees a square patch of cells with their yearly embeddings up to the cutoff year, plus static drivers, and predicts every cell of the patch for the target years.

| Quantity | Symbol | Version 1 value at L6 |
|---|---|---|
| Patch side | `P` | 32 cells (20.5 km) |
| History window | `K` | Last 5 years, with a mask for missing ones |
| Embedding width | `C` | 64 |
| Horizons | `h` | 1 and 2 |
| Driver channels | `F` | About 12 |

Predicting whole patches is far cheaper than one cell at a time, and it lets the network see neighbours, which the reference method does not. [V]

### 15.2 The history-length problem

With years 2017–2025, a target year `y` has only `y − 2017` years of history. Early targets have one or two years; the forward forecast for 2026 has nine. A model trained on short histories and run on long ones is being used outside its training range.

Controls:

1. **Fixed window.** Use only the last `K` years. `K` = 5 is the default; test 3 and 7.
2. **Masking.** Where fewer than `K` years exist, the missing positions carry a learned "absent" token and are excluded from attention.
3. **Random truncation in training.** Randomly hide early years so the model handles every length from 1 to `K`.
4. **Refit before the forward forecast** (15.7), so the final model has seen the longest windows available.

### 15.3 Architecture

A stack of blocks that alternate attention across years with mixing across neighbours.

```
input  [B, K, C, P, P] int8  -> decode -> float
  |- per-cell linear projection C -> d
  |- add year encoding (relative to cutoff), absent-year token where masked
  |- add driver projection F -> d (same for all years of a cell)
  |- add location encoding (fixed random Fourier features of lon/lat)
  |- append 2 query positions (horizon 1, horizon 2) per cell
  v
repeat L times:
  temporal attention   : each cell attends across its K + 2 positions
  spatial mixing       : each position mixed with neighbours (3x3 depthwise + pointwise convolution)
  feed-forward         : width 4d, GELU
  (pre-normalisation, residual connections, dropout 0.05)
  v
read the 2 query positions per cell
  |- embedding head : mean (normalised to length 1) and log-spread, C each
  |- change head    : 1 logit per horizon
  |- readout head   : 1 logit per class transition per horizon
```

Design choices and reasons:

| Choice | Reason |
|---|---|
| Attention across years, convolution across space | Years are few and ordered; neighbours are many and local. Full attention over 32 × 32 × 7 positions is costly and unnecessary |
| Query positions inside the sequence | One pass yields both horizons |
| Per-source input projection | A second embedding source can be added later without redesign, as in the reference method [V] |
| Fixed random Fourier location features | No trainable location table that could memorise places [V] |
| Pre-normalisation, GELU, feed-forward width 4d, dropout 0.05 | Matches the reference method's settings [V] |
| Receptive field | `L` blocks of 3 × 3 mixing see `L` cells in each direction: 8 blocks reach 5 km at L6 |

### 15.4 Model sizes [E]

Parameters per block are about `13 d²` (attention `4d²`, pointwise mixing `d²`, feed-forward `8d²`).

| Name | Width `d` | Blocks `L` | Parameters | Intended use |
|---|---|---|---|---|
| S | 128 | 6 | 1.3 million | Debugging; laptop iteration |
| M | 192 | 8 | 3.8 million | Version 1 default |
| L | 256 | 10 | 8.5 million | If M underfits |
| XL | 384 | 12 | 23 million | Cloud only |

Memory at M, batch 16, patch 32, seven positions, mixed precision: roughly 3–5 GB on the GPU. [E] Measure in task 2.2 and set the batch size from the measurement.

### 15.5 Losses

| Term | Definition | Weight |
|---|---|---|
| Embedding likelihood | Per-number Gaussian negative log-likelihood of the true embedding under the predicted mean and spread; spread floor 1e-4 [V] | 1.0 |
| Change | Binary cross-entropy on the change event, per horizon | 1.0 |
| Readout | Binary cross-entropy per class transition, masked where no label exists | 0.5 |
| Direction (optional) | Cosine distance on cells that changed | 0.0, test 0.5 |

Rules:

- Invalid cells contribute nothing to any term.
- The likelihood term is computed on all valid cells. Because unchanged cells dominate, also report it on changed cells only.
- Loss weights are part of the model configuration.

### 15.6 Imbalance and calibration

- **Sampling.** Half of each batch is patches that contain at least one change event in the target year; half is uniform over land.
- **Weighting.** Positive class weight in the change loss is the inverse sampling ratio, capped at 20.
- **Calibration.** After training, fit isotonic regression from raw probability to observed frequency on the validation year, using uniform (not oversampled) cells. Store the fitted map in the model artefact.
- **Check.** Reliability curve per continent on the validation year. If any continent's expected calibration error exceeds 0.02, fit calibration per continent.

### 15.7 Training protocol

Three stages, so that the procedure used for the public forecast is the same procedure that was backtested.

| Stage | Train on targets | Select or calibrate on | Evaluate on | Output |
|---|---|---|---|---|
| A — select | 2018–2023 | 2024 | — | Chosen size, window, weights, schedule |
| B — report | 2018–2024, settings frozen from A | Calibration from stage A's 2024 predictions | 2025, once | The reported backtest |
| C — forward | 2018–2025, settings frozen from A | Calibration from stage B's 2025 predictions | The future | The locked forecast for 2026 and 2027 |

Section 3.9 describes stage A's split. No setting changes after stage A.

Recipe for stage A, model M:

| Setting | Value | Note |
|---|---|---|
| Optimiser | AdamW | [V] reference |
| Peak learning rate | 1.1e-4 constant, and 3e-4 with warm-up and cosine decay | Test both; the reference used the constant [V] |
| Weight decay | 0 and 0.05 | The reference used 0 [V] |
| Gradient clip | 0.5 | [V] reference |
| Batch | 16 patches of 32 × 32 | Set from measured memory |
| Precision | Mixed | Confirm the laptop GPU supports it with the installed build |
| Averaged weights | Exponential moving average, 0.999 | Evaluate the averaged copy |
| Steps | 100,000, with evaluation every 5,000 | Stop early on the validation primary metric |
| Augmentation | Flips and quarter-turn rotations of the patch; random truncation of history; random masking of one year with probability 0.15 | Rotations are valid because the grid is square and north-up |
| Seeds | Three per configuration | Report mean and range |

### 15.8 Compute budget [E]

| Job | Where | Estimate | Basis |
|---|---|---|---|
| One stage A run, model M, L6 | Laptop GPU | 6–12 hours | Unmeasured; fix in task 2.2 |
| Ablation grid of 12 runs | Cloud, one mid-range GPU | 3–6 days, about $100–200 | $1–1.3 an hour [S] |
| Stage B and C refits | Laptop or cloud | Same as one run each | — |
| Detail model on dataset D at L0 | Cloud, one large GPU | 1–2 days, about $100–250 | $3–5 an hour [S] |

If a single run exceeds 24 hours on the laptop, move training to the cloud and keep the laptop for data work.

### 15.9 Baselines

All six are implemented, tested and locked with every issue.

| ID | Name | Rule | Purpose |
|---|---|---|---|
| B0 | Persistence | Next year equals this year. Change score is constant | Floor for direction; no ranking power |
| B1 | Great-circle extrapolation | Continue last year's movement on the sphere: `2 (a·b) b − a` for previous `a` and current `b` | Trend in each cell alone |
| B2 | Last change | Change score is last year's `δ` | "What moved keeps moving" |
| B3 | Proximity | Change score is a distance-weighted sum of change events in the last three years within 5 km | "Change spreads from where it was" |
| B4 | Gradient-boosted trees | Features: own past `δ` values, neighbourhood means and maxima of `δ` at three radii, current embedding, all drivers | The serious competitor |
| B5 | Per-cell temporal transformer | The model of 15.3 with spatial mixing removed | Isolates the value of neighbours |

The win condition is measured against the best of these on the test fold, chosen on the validation fold.

### 15.10 Readouts

Two ways to turn a forecast into land classes. Both are built; the better one on validation ships.

| Method | How | Strength | Weakness |
|---|---|---|---|
| Probe on the predicted embedding | Train logistic regression from real embeddings to each class on labelled years; apply it to samples drawn from the predicted mean and spread; average | Reuses one probe for all horizons; transparent | Errors compound; spread assumptions matter |
| Direct head | The readout head of 15.3, trained on label transitions | Optimised for the rare event | Needs labels in the training years |

Probe rules: train on training tiles only; one probe per class and level; freeze and version it; report its own accuracy on held-out tiles, because a forecast readout cannot be better than its probe.

### 15.11 Ablations

| Question | Variants |
|---|---|
| Do neighbours matter? | Full model versus B5 |
| Do drivers matter? | With all, with none, leave-one-out for roads, slope, population |
| How much history? | `K` = 3, 5, 7 |
| How large a patch? | `P` = 16, 32, 64 |
| Model size | S, M, L |
| Does the change head help the embedding head? | Joint versus separate training |
| Readout method | Probe versus direct head |
| Level transfer | Train at L6, test at L5; train at L6 then fine-tune on D at L0 |
| Supplier dependence | Second-source embeddings on one region (task 3.9) |

Each ablation changes one thing, uses three seeds, and is reported on the validation fold only.

### 15.12 Promotion checklist for a model

A model is registered as a candidate for a locked issue only if all are true:

- [ ] Trained from a committed configuration on a frozen dataset version.
- [ ] Stage B backtest meets the win condition, or the issue is explicitly labelled as not meeting it.
- [ ] Calibration error on the validation year below 0.02 overall.
- [ ] No continent with negative skill, or the model card states which and why.
- [ ] Reproduced by a second person within tolerance.
- [ ] Model card complete (Appendix C.2).
- [ ] Inference throughput measured and recorded.

### 15.13 Out of scope for version 1

- Ensembles of futures from a flow-matching branch.
- Training on two embedding sources at once.
- Forecasts within a year.
- Any learned location table.

---

# PART E — EXECUTION

## 16. Phase-by-phase plan

### 16.1 Calendar

| Week | Dates | Phase |
|---|---|---|
| 1 | 16–22 Nov 2026 | 0 — Look |
| 2 | 23–29 Nov | 1 — Scoreboard |
| 3 | 30 Nov–6 Dec | 1 — Scoreboard; model code starts |
| 4 | 7–13 Dec | 2 — Model |
| 5 | 14–20 Dec | 2 — Model |
| 6 | 21–27 Dec | 2 — Model; gate |
| 7 | 28 Dec–3 Jan 2027 | 3 — Meaning |
| 8 | 4–10 Jan | 3 — Meaning |
| 9 | 11–15 Jan | 4 — Lock |
| — | From late Jan | 5 — Exam |

Roles used below: **DE** data engineering, **ML** modelling, **PE** product and evaluation. One person may hold two.

This plan corrects the first plan of 2026-11-14 in one respect: sampling. Small windows cannot be read cheaply (section 4.5), so the datasets are the global L6 store and block-aligned L0 chips, not 20,000 small windows.

### 16.2 Phase 0 — Look (week 1)

**Question:** does yearly change in the data correspond to real change on the ground, and does it stand clear of noise?

| ID | Task | Role | Output | Acceptance test |
|---|---|---|---|---|
| 0.1 | Create the repository and environment. Decide the Python version by installing every core dependency. Install the GPU build from the official selector | DE | Repository, lock file | A script prints library versions and the GPU name; the lock file is committed |
| 0.2 | Fetch the supplier index. Count files per year and per zone | DE | Counts table | Section 7's estimates replaced by counts |
| 0.3 | Write the minimal block reader | DE | `io` module, unit tests | Reads one L0 block for one year; shape `[64, 1024, 1024]`, type int8; bytes transferred logged |
| 0.4 | Orientation and georeference checks | DE | Tests Q1, Q2 | Both pass on a coastline block; the flipped array fails |
| 0.5 | Choose three sites and record why | PE | Site list with coordinates and known events | Each site has a dated, documented change event or documented stability |
| 0.6 | Download one block × nine years per site | DE | About 1.1 GB in the raw cache | All 27 block-years present; gates Q3–Q6 pass |
| 0.7 | Learn how the pyramid was built | DE | Short note | L1 compared with the renormalised mean of L0; the method is stated or we decide to build our own levels |
| 0.8 | Change maps and pictures | PE | Per-site figures | For each year pair: a `δ` map, a false-colour view of the embeddings, and real imagery of both years side by side |
| 0.9 | Noise floor | ML | Distributions and a candidate `τ` | `δ` distributions at the stable site, per level; 99th percentile recorded |
| 0.10 | Gate review | All | Decision record 0001 | Evidence pack reviewed; decision written |
| 0.11 | Measure difference encoding on the three sites, at L0 and L6 | DE | Compression table | Size as read versus difference-encoded, both compressed; round trip is exact; decision on the store format recorded |

Site guidance for 0.5:

| Site type | What to look for | Examples to consider [M] |
|---|---|---|
| City edge | A district that visibly built out between 2018 and 2024 | The edge of any fast-growing metropolis with new districts on former farmland |
| Deforestation front | A road corridor with documented clearing since 2018 | Frontier corridors in the southern Amazon, the Chiquitania, Sumatra or the Congo Basin |
| Stable control | No land-use change, little vegetation | The interior of a hyper-arid desert |

**Gate 0.** Pass if, at both change sites, the share of cells above `τ` in the event year is at least five times the stable-site share, and the changed cells line up with the change visible in imagery. If it fails at L0, repeat at L3 and L6. If it fails at every level, **stop the project**: the yearly data cannot support it.

Commands to start:

```bash
uv init --package almanac
```

```bash
uv python pin 3.12
```

```bash
uv add numpy rasterio pyproj duckdb zarr scipy scikit-learn
```

Install the deep-learning library with the exact command the official selector gives for this operating system and GPU, then check:

```bash
uv run python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

### 16.3 Phase 1 — Scoreboard (weeks 2–3)

**Question:** what does a fair exam look like, and how well do simple methods already do?

| ID | Task | Role | Output | Acceptance test |
|---|---|---|---|---|
| 1.1 | Streaming reader for L6 with resume and a concurrency cap; nothing kept on disk but summaries | DE | `stream level` command | Interrupt and resume loses nothing; never exceeds 16 connections; peak disk use under 2 GB |
| 1.2 | Commit the patch-selection rule, then run the streaming pass over the planet, nine years | DE | Per-tile summaries; lineage manifest with tags and digests | Coverage report: tiles visited per year; rule committed before the run |
| 1.3 | Write sampled store G with inclusion probabilities; run all gates | DE | Dataset version `G-L6-…`, 4–12 GB | Gate report passes; weighted cell counts reproduce the planet's totals from the summaries within 1% |
| 1.4 | Forest label at L6: share of each cell lost per year, from LF1 | DE | `label_forest_loss` | Totals per country match LF1's published statistics within 2% for three test countries |
| 1.5 | Built-up label at L6 from LB2 epochs and LB1 where available | DE | `label_builtup` | Spot checks at ten cities |
| 1.6 | Drivers at L6: road distance, slope, population, night lights, country code | DE | Driver arrays with "valid as of" dates | Each driver's date is at or before 2023 for stage A |
| 1.7 | Split assignment | ML | Split file, committed | No test tile shares an edge with a training tile; counts per continent reported |
| 1.8 | Fix `τ` at L6 from stable cells worldwide | ML | Threshold record | Base rate of change events per year reported per continent |
| 1.9 | Implement baselines B0–B4 | ML | `baselines` module, tests | Each reproduces from a clean checkout |
| 1.10 | Evaluation harness: all metrics, stratification, bootstrap | ML | `evaluate` module, tests | Hand-computed cases pass; intervals cover a known value in simulation |
| 1.11 | Score baselines on validation and test folds | ML | Baseline report | Report regenerates from one command |
| 1.12 | Choose the 200 detail blocks; do **not** download them yet | PE | Block list with reasons | List committed; download happens only after gate 2, at the 20 m level first |
| 1.13 | Write and timestamp the pre-registration | PE | `docs/prereg/2027.01.md` and proofs | Timestamp token and public commit exist before any model is trained |

**Gate 1.** Pass if the baseline report reproduces, the split and threshold are committed, and the pre-registration is timestamped. There is no stop condition here; this phase cannot fail scientifically, only be late.

Notes:

- Task 1.4 is the first place label noise bites. Record the disagreement between LF1 and LF2 for 2023–2025 at L6; it bounds what any forest readout can achieve.
- The baseline report is worth publishing even if the model later fails. A proximity baseline with honest scores is already a useful public map.

### 16.4 Phase 2 — Model (weeks 4–6)

**Question:** does a learned model beat the best simple method on places and years it has not seen?

| ID | Task | Role | Output | Acceptance test |
|---|---|---|---|---|
| 2.1 | Dataset class and balanced sampler over G | ML | `data` module | Yields correct shapes; sampling ratio matches configuration; seeded order reproduces |
| 2.2 | Model S smoke test; measure memory and speed | ML | Measurements | Overfits one batch; throughput and memory recorded; batch size set |
| 2.3 | Baseline B5 (no neighbours) | ML | Scores | Trained with the same recipe |
| 2.4 | Stage A runs, model M, three seeds | ML | Runs in the tracker | Validation curve stable across seeds |
| 2.5 | Priority ablations: neighbours, drivers, window `K` | ML | Ablation table | One change per row; three seeds each |
| 2.6 | Calibration on the validation year | ML | Calibration map | Expected calibration error below 0.02 |
| 2.7 | Freeze settings. Stage B refit. Evaluate on 2025 **once** | ML | Stage B report | Test touch logged; report regenerates |
| 2.8 | Second person reproduces stage B | DE | Reproduction note | Primary metric within the stated tolerance |
| 2.9 | Gate review | All | Decision record 0002 | Decision written |

**Gate 2.** Three outcomes:

| Outcome | Condition | Action |
|---|---|---|
| Pass | Win condition met on stage B | Continue to Phase 3 |
| Partial | Model beats B0–B3 but not B4, or the interval's lower end is below 10% | Lock the forecast anyway, labelled honestly; make B4 the product baseline; continue |
| Fail | Model does not beat B3 | Publish the baseline report and the negative result; lock B4's forecast as issue 2027.01; decide whether to continue |

A locked forecast from a simple method still starts the public record. The exam is worth taking either way.

Schedule guard: if stage A is not converging by the end of week 5, cut ablations to the neighbours-only comparison and go straight to stage B.

### 16.5 Phase 3 — Meaning (weeks 7–8)

**Question:** do the forecasts say something true about forests and buildings, as measured by independent data?

| ID | Task | Role | Output | Acceptance test |
|---|---|---|---|---|
| 3.1 | Train readout probes on training tiles | ML | Frozen probes | Each probe's own accuracy reported on held-out tiles |
| 3.2 | Compare probe readouts with direct heads on validation | ML | Choice recorded | One method chosen per layer |
| 3.3 | Grade the forest readout for 2025 against LF1 | ML | Forest report | Average precision, top-1% precision, fractions skill score, against B3 and B4 |
| 3.4 | Interim grade against disturbance alerts LF2 | ML | Interim report | Same metrics on 2025 alerts |
| 3.5 | Run the public forest benchmark LF6 if its licence allows research use | ML | Benchmark note | Our forest readout scored with the benchmark's own protocol |
| 3.6 | Grade the built-up readout against LB1 to 2023 and LC1 for 2025 | ML | Built-up report | Same metrics |
| 3.7 | Error atlas | PE | Ten best hits, ten worst misses per layer with imagery | Reviewed by the whole team |
| 3.8 | Tables by continent and biome | PE | Stratified tables | Generated from the harness, not by hand |
| 3.9 | Second-source test on one region | ML | Note | Skill with the alternative embeddings compared on the same split |
| 3.10 | Leakage review by someone who did not build the model | DE | Review note | Every item in section 3.9's leakage table checked and signed |
| 3.11 | Plain-language method notes for each public layer | PE | One page each | Read and understood by someone outside the team |

**Gate 3.** Pass if at least the forest readout shows positive skill against B3 on independent labels in the held-out regions. If no readout shows skill, the issue ships with `change_risk` only, and the readout layers are withheld and labelled experimental.

### 16.6 Phase 4 — Lock (week 9)

| ID | Task | Role | Output | Acceptance test |
|---|---|---|---|---|
| 4.1 | Stage C refit on targets to 2025 | ML | Registered model | Promotion checklist complete (15.12) |
| 4.2 | Streaming inference at L6 for 2026 and 2027: read each tile's last five years, score, write the forecast, discard the tile | ML | Forecast layers, 1–3 GB | Coverage map; no tile silently missing; input tags match the lineage manifest or the difference is reported |
| 4.3 | Baseline forecasts for the same cells | ML | Baseline layers | Present for B0–B5 |
| 4.4 | Tag the grader | ML | `grader-1.0.0` | Tag signed; named in the pre-registration |
| 4.5 | Build the package | DE | Package and manifest | Manifest validates |
| 4.6 | Independent rebuild | DE or PE | Matching digests | Second person's digests equal the first's |
| 4.7 | Lock procedure with two people | All | Proofs and public records | Every row of checklist D.3 ticked |
| 4.8 | Scorecard site and public map, first version | PE | Public site | Shows the issue, its proofs, baselines and the backtest; attribution present |
| 4.9 | Public repository release | DE | Tagged release | README lets a stranger run verification |
| 4.10 | Announcement | PE | Short public post | States the claim, the date of the exam, and how to verify |
| 4.11 | Retrospective | All | Notes | What to change before issue 2027.02 |

**Hard deadline: 15 January 2027.** If stage C is not ready, lock the stage B model's forecast, or B4's. A late lock has no value; a modest forecast locked on time has.

### 16.7 Phase 5 — Exam (from late January 2027)

| ID | Task | Role | Output |
|---|---|---|---|
| 5.1 | Daily index polling | DE | Arrival log |
| 5.2 | Ingest arriving zones into a new dataset version; gates | DE | Truth store |
| 5.3 | Partial grades at 20%, 50%, 80% coverage | ML | Scorecard updates |
| 5.4 | Final grade at 95% coverage or 120 days | ML | Final grade record |
| 5.5 | Post-exam report: what was right, what was wrong, why | All | Public report |
| 5.6 | Decision: continue, change course, or stop | All | Decision record |

The post-exam report is published whatever the result.

### 16.8 Phase 6 — Product alpha (February–April 2027)

| ID | Work | Output | Done when |
|---|---|---|---|
| 6.1 | Move pipelines to the cloud in `us-west-2`; infrastructure as code for dev and production | Environments | A full L6 issue rebuilds in the cloud from a clean account |
| 6.2 | Regional L3 stores and forecasts for three regions chosen with design partners | L3 layers | Graded backtest per region |
| 6.3 | Interface version 1: issues, point, polygon, bulk | Service in production | Contract tests and load test pass |
| 6.4 | Tiles and web app | Public app | Accessibility audit passes |
| 6.5 | Area report | Report generator | Three partners use it on their own areas |
| 6.6 | Accounts, keys, metering, billing hooks | Account service | Usage visible to customers |
| 6.7 | Security baseline (section 19.2) | Controls in place | Internal audit checklist complete |
| 6.8 | All register rows at [V]; legal review of licences | Signed-off register | Counsel's note filed |
| 6.9 | Three design partners signed | Letters or contracts | Each has named a use and a success measure |

### 16.9 Phase 7 — Scale (May–August 2027)

| ID | Work | Output | Done when |
|---|---|---|---|
| 7.1 | Global L3 ingest, about 7 TB | Global L3 store | Gates pass worldwide |
| 7.2 | Global L3 model and inference | Global L3 layers | Backtest meets the win condition at L3, or L3 stays regional |
| 7.3 | Mid-year refresh issue using the latest drivers | Issue `2027.02` | Locked and graded on interim truth |
| 7.4 | On-request L0 pipeline | Detail product | A request for 1,000 km² completes within one hour |
| 7.5 | Observability, on-call, incident process | Runbooks and dashboards | A game-day exercise is passed |
| 7.6 | Security audit preparation; penetration test | Audit readiness | Findings closed or accepted in writing |
| 7.7 | Open benchmark with a hidden test set | Public benchmark | First outside submission scored |
| 7.8 | Pricing test with five paying customers | Revenue | Section 22.5's assumptions updated |

### 16.10 Phase 8 — Second exam and general availability (September 2027–January 2028)

| ID | Work | Output |
|---|---|---|
| 8.1 | Retrain when the 2026 layer is complete; issue `2028.01` for 2027 and 2028 | Locked issue |
| 8.2 | Grade the 2027 forecast made in January 2027 at horizon 2 | Two-year record |
| 8.3 | General availability review against section 2.8 | Decision |
| 8.4 | Security audit report | Report |
| 8.5 | Evaluate forecasts within the year using a second source | Research note |

### 16.11 Weekly rhythm

| Day | Ritual | Output |
|---|---|---|
| Monday | Plan the week against this section | Three commitments per person |
| Wednesday | Evidence review: look at figures and tables together | Decisions and questions logged |
| Friday | Demo from a clean checkout | A reproducible result or an honest gap |
| Friday | Risk register and open questions review | Updated section 24 and Appendix G |

### 16.12 If the schedule slips: what to cut, in order

1. Level L5 forecasts.
2. Dataset D and the detail model.
3. Readout layers other than forest.
4. The second-source test.
5. Web polish beyond a working scorecard.
6. Ablations beyond the neighbours comparison.

Never cut: the pre-registration, the baselines, the independent rebuild, the two-person lock, the leakage review, or the published grade.

### 16.13 Gates at a glance

| Gate | Date | Question | If no |
|---|---|---|---|
| 0 | 22 Nov 2026 | Is yearly change real and above noise? | Stop |
| 1 | 6 Dec 2026 | Is the exam fair and fixed? | Finish it before training anything |
| 2 | 27 Dec 2026 | Does the model beat the best baseline? | Lock a baseline; decide |
| 3 | 10 Jan 2027 | Do readouts carry signal on independent data? | Ship change risk only |
| Lock | 15 Jan 2027 | Is a forecast publicly locked? | No fallback; this date does not move |
| Exam | Spring 2027 | Did the forecast beat its baselines on new truth? | Publish; decide |

---

# PART F — PRODUCT AND OPERATIONS

## 17. Productisation

### 17.1 Interface principles

1. **Read-only over immutable issues.** Every response names its `issue_id` and `package_digest`.
2. **Verifiable.** Every response links to the manifest, so a client can check what it received.
3. **Stable.** Fields are added, never repurposed. Breaking changes need a new major version.
4. **Honest by default.** A response includes the baseline's value next to the model's, and the uncertainty, unless the client opts out.
5. **Predictable cost.** A request's price can be computed from its area and level before it is sent.

### 17.2 Authentication and authorisation

| Aspect | Design |
|---|---|
| Machine access | API keys for simple use; OAuth 2.0 client credentials for enterprise |
| Human access | Single sign-on through the identity provider; multi-factor required |
| Scopes | Per tenant: permitted layers, levels, regions, monthly area quota |
| Key handling | Keys shown once; stored hashed; rotation without downtime; last-used time visible |
| Public endpoints | Issue list, manifests, scorecards and L6 tiles need no key but are rate-limited by address |

### 17.3 Endpoints, version 1

| Method and path | Purpose |
|---|---|
| `GET /v1/issues` | List issues with status, cutoff year, target years, digests |
| `GET /v1/issues/{issue_id}` | Issue detail: manifest link, proofs, model and data cards, coverage |
| `GET /v1/issues/{issue_id}/layers` | Layers and levels available in this issue |
| `GET /v1/issues/{issue_id}/point?lat=&lon=&level=` | Forecast for the cell containing a point |
| `POST /v1/issues/{issue_id}/area` | Aggregated forecast for one polygon |
| `POST /v1/issues/{issue_id}/areas:batch` | Submit many polygons; returns a job |
| `GET /v1/jobs/{job_id}` | Job status and result link |
| `GET /v1/issues/{issue_id}/tiles/{layer}/{z}/{x}/{y}.png` | Display tile |
| `GET /v1/issues/{issue_id}/scorecard` | Grade records, partial or final |
| `POST /v1/reports` | Generate an area report |
| `POST /v1/watchlists` · `GET` · `DELETE` | Manage watched areas |
| `POST /v1/webhooks` · `GET` · `DELETE` | Manage notification endpoints |
| `GET /v1/usage` | Usage for the calling tenant |
| `GET /v1/attribution` | The attribution register |

### 17.4 Example: point query

Request:

```
GET /v1/issues/2027.01/point?lat=-8.7632&lon=-63.9004&level=6
Authorization: Bearer <key>
```

Response, with illustrative values:

```json
{
  "issue_id": "2027.01",
  "package_digest": "sha256:<64 hex>",
  "manifest_url": "https://<public host>/issues/2027.01/manifest.json",
  "data_cutoff_year": 2025,
  "model_version": "almanac-M-G-L6-003",
  "input_dataset_version": "1.1",
  "cell": {
    "tile": "<tile id>",
    "level": 6,
    "row": 41,
    "col": 97,
    "size_m": 640,
    "centre": {"lat": -8.7629, "lon": -63.9011}
  },
  "forecasts": [
    {
      "target_year": 2026,
      "horizon": 1,
      "p_change": 0.31,
      "p_change_baseline": {"name": "B4", "value": 0.22},
      "rank_percentile_global": 99.2,
      "readouts": {
        "forest_loss": {"p": 0.27, "baseline": 0.19},
        "builtup_gain": {"p": 0.01, "baseline": 0.01}
      },
      "uncertainty": {"embedding_spread_mean": 0.041}
    },
    {
      "target_year": 2027,
      "horizon": 2,
      "p_change": 0.44,
      "p_change_baseline": {"name": "B4", "value": 0.35},
      "rank_percentile_global": 98.9,
      "readouts": {
        "forest_loss": {"p": 0.39, "baseline": 0.30},
        "builtup_gain": {"p": 0.02, "baseline": 0.02}
      },
      "uncertainty": {"embedding_spread_mean": 0.058}
    }
  ],
  "interpretation": "Ranked risk, not a prediction that this cell will change.",
  "attribution_url": "https://<api host>/v1/attribution"
}
```

### 17.5 Polygon semantics

| Question | Rule |
|---|---|
| Input | GeoJSON polygon or multipolygon, longitude and latitude in WGS84, right-hand rule |
| Validation | Self-intersections rejected; holes allowed; area limits per plan |
| Which cells count | Every cell the polygon touches, weighted by the share of the cell inside it |
| Aggregates returned | Area-weighted mean risk; expected changed area in hectares with an interval; count and area of cells above the plan's risk threshold; rank among comparable areas |
| Small polygons | If the polygon is smaller than four cells at the requested level, the response says so and recommends a finer level |
| Polygons across UTM zones | Computed per zone and combined by area |
| Antimeridian | Split at 180° by the client or by the service, stated in the response |
| Privacy | The polygon is stored only if the client saves it to a watchlist |

### 17.6 Errors

Errors use the standard problem-details JSON format with a stable `type` address, a `title`, an HTTP `status`, a `detail`, and a `request_id`.

| Status | When |
|---|---|
| 400 | Malformed geometry or parameters |
| 401 / 403 | Missing or insufficient credentials |
| 404 | Unknown issue, layer, or cell outside coverage |
| 409 | Request against a superseded issue with `strict=true` |
| 413 | Polygon exceeds the plan's area limit |
| 422 | Valid request that cannot be served: level not in this issue |
| 429 | Rate or quota limit; includes `Retry-After` |
| 503 | Dependency unavailable; safe to retry |

### 17.7 Limits, idempotency, pagination

- Rate limits per key and per tenant; quotas in square kilometres per month per level.
- Batch submissions accept an `Idempotency-Key` header. Replays return the original job.
- Lists are cursor-paginated. Cursors are opaque and expire after 24 hours.
- Every response includes remaining quota headers.

### 17.8 Versioning and deprecation

- The major version is in the path. Minor additions are backward compatible.
- A deprecated field or endpoint is announced at least 12 months before removal, flagged in responses with a header, and listed in the changelog.
- Issues are never removed. An interface version may be retired; the data remains reachable through the newest version and through the public bucket.

### 17.9 Tiles and styling

| Aspect | Rule |
|---|---|
| Coarse levels | Pre-rendered Web Mercator raster tiles in one PMTiles file per layer per issue, on the CDN |
| L3 | Rendered on demand from the cloud-optimised files; cached at the edge |
| Colour ramp | One sequential, perceptually uniform, colour-blind-safe ramp for risk; a second, distinct ramp for uncertainty. No red-green |
| Scale | Fixed breaks per layer across issues, so maps from different years are comparable |
| Legend | Always visible; states units and the issue |
| Masking | Cells without coverage are hatched, never left blank or zero |

### 17.10 Web application

| Screen | Requirements |
|---|---|
| Scorecard home | Latest issue; verdict in one sentence; model against baselines; link to verify |
| Issue page | Proofs; cards; coverage; grade history; best hits and worst misses |
| Map | Layer and level switch; issue switch; time slider across past truth and forecast; opacity; search by place or coordinates |
| Compare | Forecast beside truth once graded; forecast beside baseline before |
| Area tool | Draw or upload a polygon; summary panel; export |
| Verify | Paste a manifest address or drop a file; the page checks digests and proofs in the browser |
| Account | Keys, usage, watchlists, webhooks |
| Method | Plain-language notes per layer; limits; what the product is not |

Non-functional: keyboard operable; screen-reader labels on all controls; works at 320 px width; loads the scorecard with scripts disabled.

### 17.11 Area report

| Section | Content |
|---|---|
| Header | Area name, size, issue, date generated, package digest |
| Summary | Three sentences: overall risk rank, main risk type, uncertainty |
| Map | Risk layer over recent imagery |
| Numbers | Expected changed area with interval; share of area in the top risk classes; comparison with the baseline |
| Drivers | Which inputs most distinguish this area: road proximity, recent nearby change, slope, and so on |
| History | Observed change in the area for each past year |
| Track record | How past forecasts for this region scored |
| Limits | What the forecast cannot say; the statement that it is not compliance evidence |
| Attribution | Full register entries used |

Reports are generated from the same queries as the interface and carry the same digests.

### 17.12 Watchlists and webhooks

- A watchlist is a saved set of areas. When a new issue is locked or a grade is published, each area is rescored.
- Notifications fire on rules the customer sets: rank crosses a threshold; risk rises by more than a set amount between issues; a graded miss or hit in the area.
- Webhook payloads are signed with a shared-secret message authentication code and carry a timestamp. Deliveries retry with backoff for 24 hours, then park for manual replay.

### 17.13 Bulk delivery

- Enterprise customers receive time-limited signed links to the cloud-optimised files for their licensed regions and levels.
- Each delivery includes the manifest excerpt for those files, so the customer can verify them against the public manifest.

### 17.14 Developer experience

- An OpenAPI description is the source of truth; documentation and client libraries are generated from it.
- Client libraries for Python and TypeScript; a QGIS plugin later.
- A public sandbox key with a small quota on the L6 layers.
- Every documentation example is executed in continuous integration.

### 17.15 Wording rules

| Say | Never say |
|---|---|
| "Ranked risk of change" | "Will be deforested" |
| "In the top 1% of cells by risk" | "Illegal clearing predicted" |
| "Forecast made with data up to 2025" | "Current" or "live" |
| "Scored X against a baseline of Y" | A score with no baseline |
| "Not evidence about past land use" | "Compliant" or "deforestation-free" |

---

## 18. Operations

### 18.1 The yearly cycle

| When | Event | Work |
|---|---|---|
| Mid-January | Lock the new issue | Section 11.4 |
| Late January onward | New input year arrives zone by zone | Ingest; partial grades |
| Spring | Coverage reaches 95% | Final grade; post-exam report |
| Spring | Yearly forest-loss map released | Final forest readout grade |
| Mid-year | Refresh issue with updated drivers | Optional issue |
| Autumn | Retrain rehearsal on all data; dependency upgrades; fallback route test | Dry run of January |
| December | Freeze window | No changes to grader, metrics, splits or thresholds |

### 18.2 Monitoring

**Data**

| Signal | Check | Alert when |
|---|---|---|
| Supplier index | Row count and digest per day | Unexpected removals; schema change |
| Dataset version field | Value per tile-year | Any value not seen before |
| Vector length | Distribution per file | Median outside [0.98, 1.02] |
| No-data share | Per file against its footprint | Jump of more than 5 points |
| Stable-site change | `δ` at control sites for each new year | Outside the Phase 0 band |
| Per-number mean and variance | By biome against the previous year | Shift beyond a set tolerance |
| Label releases | Version and coverage | New version; format change |

**Model**

| Signal | Check | Alert when |
|---|---|---|
| Backtest on each retrain | Walk-forward skill | Skill falls by more than a third against the previous model |
| Calibration | Reliability on the newest graded year | Expected calibration error above 0.03 |
| Regional skill | Per continent | Any continent turns negative |
| Input range | Share of cells whose inputs fall outside the training range | Above 1% |
| Baseline gap | Model minus B4 | Shrinks for two issues running |

**Service**

| Signal | Target |
|---|---|
| Availability | Section 2.8 |
| Latency by endpoint | Section 2.8 |
| Error rate by status family | Below 0.1% server errors |
| Saturation | CPU, memory, connections below 70% at peak |
| Cache hit rate | Above 80% for tiles |
| Verification failures | Zero |

### 18.3 Service objectives and error budgets

- Each objective in section 2.8 has a monthly error budget.
- When half the budget is spent, non-urgent releases pause.
- When all of it is spent, only reliability work ships until the month ends.

### 18.4 Alerting and on-call

- Alerts page a person only when a user-visible objective is at risk or an integrity check fails. Everything else is a ticket.
- Every alert links to a runbook.
- A rotation exists from general availability; during alpha, business-hours response with a public status page.

### 18.5 Incidents

| Severity | Definition | Response |
|---|---|---|
| S0 — Integrity | A locked package fails verification; a grade was computed wrongly; truth was mishandled | Immediate; public notice within 24 hours; independent review |
| S1 | Interface or public site down; wrong data served | Within 15 minutes; hourly updates |
| S2 | Degraded performance; one region or layer affected | Within 1 hour |
| S3 | Minor defect; no customer impact | Next working day |

Every S0 and S1 gets a blameless written review within five working days, published for S0.

An S0 is the worst thing that can happen to this company. The registry design exists to make it detectable by outsiders, which is what makes the product credible.

### 18.6 Backup and recovery

| Asset | Protection | Recovery point | Recovery time |
|---|---|---|---|
| Locked packages | Object lock; cross-region replica; research archive deposit | Zero | 1 hour |
| Grade records | Object lock; cross-region replica | Zero | 1 hour |
| Sample stores | Versioned; rebuildable from the raw cache | 24 hours | 2 days |
| Raw cache | Versioned; rebuildable from the supplier while it exists | — | Days |
| Models | Versioned; rebuildable from data and configuration | Zero | 1 day |
| Accounts database | Point-in-time recovery; daily snapshots to another region | 5 minutes | 2 hours |
| Code and configuration | Hosted repository plus a mirror | Zero | 1 hour |

A restore is rehearsed twice a year. An untested backup is counted as no backup.

### 18.7 Change management

- All infrastructure changes go through code review and an automated plan.
- Production deploys are progressive: a small share of traffic first, automatic rollback on error-rate or latency regression.
- Changes to the grader, metrics, thresholds or splits follow the stricter rule in 14.8 and are forbidden in the December freeze.

### 18.8 Cost control

- Budgets and alerts per environment; every resource tagged with owner and purpose.
- Batch work on spot capacity with checkpointing.
- Lifecycle rules: raw cache to cold storage after 90 days; work areas expire after 30 days.
- Compute runs in the mirror's region to avoid transfer charges.
- A monthly cost review compares spend with section 20.

### 18.9 Runbooks to write

| Runbook | Before phase |
|---|---|
| Rerun a failed ingest partition | 1 |
| Switch to the fallback supplier route | 1 |
| Rebuild a sample store from the raw cache | 2 |
| Reproduce a registered model | 2 |
| Lock an issue | 4 |
| Verify a package as an outsider | 4 |
| Grade an issue; publish a partial grade | 5 |
| Supersede an issue | 5 |
| Respond to a failed verification (S0) | 5 |
| Rotate keys and secrets | 6 |
| Restore the accounts database | 6 |
| Roll back a deploy | 6 |

### 18.10 Support

- A public status page and changelog.
- Support by email during alpha, with a two-working-day response; contractual response times for enterprise at general availability.
- A public issue tracker for the open layers and the benchmark.

---

## 19. Security and compliance

### 19.1 Threat model

| Threat | Who | Impact | Controls |
|---|---|---|---|
| Altering a forecast after truth is known | Insider, or an attacker with storage access | Destroys the product's credibility | Object lock; external timestamps; public manifests; two-person lock; outsider verification |
| Altering a grade | Insider | Same | Locked grader version; grade records under object lock; published truth digests |
| Poisoned input from a compromised supplier copy | Attacker on the mirror | Wrong forecasts; possible manipulation of risk rankings | Raw-cache digests; cross-check samples against the second route; stability monitors |
| Forecasts used to direct harm at communities | A customer | Real-world harm | Acceptable-use policy; coarse public layers; review of sensitive requests; right to refuse service |
| Front-running: someone clears land where risk is low to avoid scrutiny | A land user reading the public map | Reduced deterrence | Public layer is coarse; fine layers are access-controlled; accepted residual risk, stated openly |
| Theft of customer areas of interest | External attacker | Commercial harm to customers | Encryption; tenant isolation; no clear-text logging; least privilege |
| Credential leakage | Anyone | Account takeover; cost | Secret scanning; short-lived credentials; hardware-backed multi-factor |
| Dependency compromise | Supply-chain attacker | Code execution in pipelines | Pinned and hashed dependencies; signed images; minimal build permissions |
| Scraping of paid layers | Competitor | Revenue loss | Rate limits; per-tenant watermarking of bulk deliveries; contract terms |
| Denial of service | Anyone | Outage | CDN; rate limits; static fallback for the scorecard |

### 19.2 Security baseline

To be in place before any customer data is held (Phase 6):

- [ ] Single sign-on and multi-factor for every human account; no shared accounts.
- [ ] Least-privilege roles; production write access held by pipelines only.
- [ ] Separate cloud accounts per environment.
- [ ] Encryption at rest with managed keys; encryption in transit everywhere.
- [ ] Secrets in a secrets manager; none in code, images or logs.
- [ ] Signed commits on protected branches; two-person review on sensitive paths.
- [ ] Central, write-once audit logging of storage, identity and deploy events.
- [ ] Vulnerability scanning of dependencies, images and infrastructure code in continuous integration.
- [ ] Laptop disk encryption and screen lock; a device inventory.
- [ ] A written incident response plan; one rehearsal completed.
- [ ] A vulnerability disclosure address and policy on the website.
- [ ] An external penetration test before general availability.

### 19.3 Supply chain

- Dependencies are pinned with hashes in the lock file.
- Third-party build actions are pinned by commit digest.
- Images are built from minimal bases, scanned, signed, and referenced by digest.
- A software bill of materials is produced for every image and stored with the release.
- Build jobs have no production credentials. Deploys use short-lived, workload-bound credentials.

### 19.4 Data protection

| Data | Sensitivity | Handling |
|---|---|---|
| Satellite embeddings, labels, drivers | Public, licensed | Per licence |
| Forecast layers | Public for L6; commercial for finer levels until graded | Access control; watermarking of deliveries |
| Customer areas of interest | Confidential; can reveal sourcing or investment plans | Encrypted; tenant-isolated; deleted on request and at contract end |
| Account data: names, emails, billing | Personal data | Minimised; processed under data protection law; a data processing agreement offered |
| Logs | May contain addresses and identifiers | Retention limits; no areas of interest in clear text |

The product makes no inference about individuals. A request to produce one is refused.

### 19.5 Compliance roadmap

Timings and costs are typical figures from memory and MUST be re-quoted. [M]

| Item | When | Why | Effort |
|---|---|---|---|
| Data protection basics: privacy notice, processing records, processing agreement | Phase 6 | Required to hold customer account data | Weeks, with counsel |
| Security audit, point-in-time report | Start Phase 7; report about 3 months later | Enterprise buyers ask for it | Months of preparation; five-figure cost |
| Security audit, period report | 6–12 months after the first | Standard enterprise requirement | Ongoing |
| Information security management certification | After revenue justifies it | European enterprise and public buyers | Six-figure total over a year |
| Accessibility conformance statement | With the web app | Public-sector procurement | Days, after an audit |
| Licence compliance sign-off | Before Phase 6 | Section 6.6 | Counsel's review |

### 19.6 Responsible use

A written policy, agreed by every customer:

1. **No use to target, displace or harass people or communities.**
2. **No use as sole evidence** for enforcement, penalties, or the denial of credit, insurance or market access. A forecast is a reason to look, not a finding.
3. **No military targeting.**
4. **Human review** is required before any action that affects a person or community.
5. **Local context.** Customers working in areas with indigenous or community land rights are pointed to guidance on rights-respecting use. A conservation group that runs a similar forecasting system published such a guideline in 2025. [S]
6. **Right to refuse or suspend service** where these terms are breached.

Internal practice: a short ethics review for any request for fine-scale layers in conflict zones, areas with contested land rights, or protected indigenous territories.

### 19.7 Regulatory position on AI law

- The product ranks land areas, not people. On a first reading it does not fall into the high-risk categories of the EU's AI law, and it is not a general-purpose model. [M]
- That reading MUST be confirmed by counsel before European sales. The application date for high-risk duties was politically agreed to move to December 2027. [S]
- Regardless of classification, the product already does what such laws ask for: documentation, logging, human oversight, stated accuracy, and transparency.

### 19.8 Sanctions and export

- Screen customers against applicable sanctions lists before contracting. [M]
- Open data layers are public; paid services are subject to the laws of the company's jurisdiction and its payment providers.
- Counsel confirms the position before the first cross-border enterprise contract.

---

# PART G — COMPANY

## 20. Cost model

All totals are estimates [E]. Price inputs were read on 2026-11-14 and move often.

### 20.1 Price inputs

| Item | Price | Label |
|---|---|---|
| Object storage, standard class | $0.023 per GB-month for the first 50 TB | [S] |
| Data transfer out to the internet | About $0.09 per GB after a small free allowance | [S] |
| Mid-range cloud GPU | $0.92–1.29 an hour | [S] |
| Large cloud GPU, specialist providers | $2.90–4.90 an hour | [S] |
| Large cloud GPU, general cloud, on demand | About $6.90 an hour | [S] |
| Reads from the mirror | Free | [V] |
| Reads from the supplier's own bucket | Reader pays | [S] |

### 20.2 Stage 0 — to the first lock (now to January 2027)

| Item | Cost |
|---|---|
| External solid-state drive (optional under the lean storage plan) | $0–200 [M] |
| Cloud GPU for ablations, if the laptop is too slow | $100–300 |
| Domain, static hosting, CDN on free tiers | Under $50 |
| Timestamps, research-archive deposit, public repository | Free |
| **Total** | **Under $600** |

The first public exam can be reached for less than the price of a mid-range phone.

### 20.3 Stage 1 — product alpha (February to April 2027), per month

| Item | Basis | Cost |
|---|---|---|
| Storage | About 3.5 TB: stores, raw cache, forecasts | $80 |
| Batch compute | Ingest and inference on spot capacity | $200 |
| GPU | Regional L3 training and inference | $300 |
| Managed database and cache | Smallest production sizes | $150 |
| Interface and tile services | Managed containers, two small instances each | $150 |
| CDN and transfer | About 200 GB out | $30 |
| Monitoring, error tracking, identity | Free or starter tiers | $100 |
| **Total** | | **About $1,000 a month** |

### 20.4 Stage 2 — scale (May 2027 onward), per month

| Item | Basis | Cost |
|---|---|---|
| Storage | 15–20 TB: global L3, raw cache partly in cold storage, forecasts | $350–450 |
| Compute | Global L3 inference per issue about $100; training $500–1,500 | $700–1,700 |
| Services | Database, containers, CDN, monitoring at production sizes | $1,000–1,500 |
| Security tooling and audit, spread over the year | Scanner, compliance platform, auditor, penetration test | $2,000–4,000 |
| **Total** | | **About $4,000–8,000 a month** |

### 20.5 Cost per unit of work

| Unit | Cost | Note |
|---|---|---|
| One global L6 issue: inference | A few dollars | Runs on a laptop |
| One global L3 issue: inference | About $100 | Section 10.8 |
| One on-request L0 area of 1,000 km² | Under $1 of compute, plus a 3.6 GB read per tile-year | In-region reads are free |
| One point or polygon query | Negligible | Range reads on static files, cached forever |
| Keeping our own copy of global L3, nine years | About $160 a month | 7 TB |
| Keeping our own copy of everything at L0 | About $10,700 a month | 465 TB; not planned |

### 20.6 What the numbers imply

- **Infrastructure is not the constraint.** People are. A team of four costs far more than Stage 2's entire cloud bill.
- **Marginal cost per customer is near zero.** Forecasts are computed once and served as files.
- **The expensive mistake is copying fine-resolution data we do not need.** L0 is read on request and cached per customer area.
- **Leaving the mirror's region costs money.** Keep compute in `us-west-2`.

### 20.7 Guardrails

- A monthly budget per environment with alerts at 50%, 80% and 100%.
- Any single job estimated above $200 needs a second person's approval.
- GPU instances shut down automatically when idle for 30 minutes.

---

## 21. Team

### 21.1 Roles for the first nine weeks

| Role | Owns | Skills needed |
|---|---|---|
| Data engineering | Readers, raw cache, stores, gates, pipelines, packaging | Python, cloud storage, raster data, careful testing |
| Modelling | Baselines, model, training protocol, evaluation harness, calibration | Deep learning in PyTorch, statistics, discipline about leakage |
| Product and evaluation | Site choice, error atlas, pre-registration, scorecard site, method notes, public communication | Clear writing, maps, front-end basics, scepticism |

With two people, modelling and evaluation are split so that the person who builds the model does not also grade it alone.

### 21.2 Advisers to line up early

| Adviser | Why | When |
|---|---|---|
| Remote-sensing scientist | Knows how the labels fail; reviews the evaluation design | Before gate 1 |
| Land-use or forestry practitioner in a frontier region | Says whether the misses and hits make sense on the ground | Phase 3 |
| Forecast-verification statistician | Reviews metrics, bootstrap and the win condition | Before the pre-registration is timestamped |
| Technology lawyer | Licences, terms, liability | Before Phase 6 |
| Security lead, part-time | Baseline, audit preparation | Phase 6 |

### 21.3 Hiring order after the first exam

1. Platform engineer: pipelines, infrastructure, reliability.
2. Front-end and visualisation engineer: map app, scorecard, reports.
3. Second modeller with a remote-sensing background.
4. Partnerships lead with supply-chain or conservation contacts.
5. Customer-facing geospatial analyst.

### 21.4 Who decides what

| Activity | Responsible | Approves | Consulted | Informed |
|---|---|---|---|---|
| Change a metric, split or threshold | Modelling | Product and evaluation, plus one adviser | Data engineering | Everyone |
| Promote a model | Modelling | Second reproducer | Product and evaluation | Everyone |
| Lock an issue | Data engineering | Two people present | Modelling | Public |
| Publish a grade | Modelling | Product and evaluation | Data engineering | Public |
| Supersede an issue | Product and evaluation | All founders | Advisers | Public |
| Add a data source | Data engineering | Register owner | Counsel if the licence is unclear | Everyone |
| Accept a customer in a sensitive area | Product and evaluation | All founders | Adviser | — |

### 21.5 Working agreements

- A result is a command that reproduces it.
- Bad news travels the same day.
- The test year is touched once; whoever touches it logs it.
- Disagreements about evidence are settled by running the experiment, when it costs less than a day.

---

## 22. Go-to-market

### 22.1 Positioning

> Monitoring tools tell you what changed. Almanac ranks where change is likely next, and publishes how often it was right.

The proof is the public scorecard. No claim is made that the scorecard does not support.

### 22.2 Segments

| Segment | Pain | Why now | Offer | Proof they need |
|---|---|---|---|---|
| Compliance platforms for deforestation-free supply chains | Customers ask "where should we look first?"; their product only looks backward | The EU law applies from 30 December 2026 [S]; a free checking tool closes the next day [S] | A forward-risk layer through the interface, under their brand or ours | Backtest in their customers' sourcing regions; clean licence; uptime |
| Importers and traders of the covered commodities | Too many suppliers to audit; penalties and reputational risk | Same | Risk ranking of sourcing polygons; area reports | That ranking finds real cases earlier than their current process |
| Conservation agencies and funders | Patrols and grants are spread thin | Predictive tools are proven in principle by an existing programme in six countries [S] | Open coarse map; fine layers at cost or free for public agencies | Regional skill; rights-respecting use |
| Reinsurers and catastrophe modellers | Exposure grows between model updates | Rising losses at the urban edge | Built-up growth probabilities, global | Skill against their own exposure history |
| Infrastructure, telecom and retail planners | Need to know where settlement will be in two years | Costly to guess wrong | Growth maps and aggregates by area | Backtests in their markets |
| Development banks and statistics offices | 35 countries skipped the last census round [S] | The current census round runs to 2034 | Settlement-growth aggregates between counts | Agreement with new census results as they arrive |

### 22.3 The first wedge

**Forward forest-risk for supply-chain compliance, sold through platforms that already own the customer.**

Reasons:

- The law's start date creates a buying moment. [S]
- Many vendors already do monitoring; none found in this research sells a publicly graded forecast.
- Platforms have distribution; we have one layer they lack.
- The yearly forest-loss map and the disturbance alerts give independent truth for grading.

Honest limits:

- The law asks about the past since 31 December 2020. A forecast is not evidence for a due-diligence statement. It helps decide where to spend audit effort.
- The Commission's 2026 simplification is expected to cut companies' compliance costs by about three quarters. [S] Buyers will be price-sensitive.
- If forest clearing falls because the law works, base rates drop and ranking gets harder. That is a good outcome for forests and a real risk for this wedge.

### 22.4 Competitors and neighbours

| Who | What they do | Relation | Label |
|---|---|---|---|
| A conservation group's predictive deforestation programme | Predicts illegal clearing up to six months ahead; claims 80% accuracy; used by governments in six countries; built on radar alerts | Closest in purpose. Shorter horizon, forest only, not publicly graded in the way proposed here | [S] |
| Google's deforestation-risk benchmark | Public benchmark and models for Southeast Asia | Research artefact; a yardstick for our forest readout; a possible future product from a much larger group | [V] |
| The reference method's authors | General forecasting in embedding space; code public | Could ship a similar forecast; currently research | [V] |
| The embedding producer | Makes the input | Could add forecasting to its own platform | [V] |
| Satellite deforestation monitoring vendors | Detect and verify past change for compliance; typical prices €10,000–50,000 a year | Channel partners first; competitors if they add forecasts | [S] |
| Compliance workflow platforms | Traceability, statements, supplier management; entry prices around €12,000 a year | Channel partners | [S] |
| Free screening tools named by the EU | Basic checks against public maps | Set the floor for "free" | [S] |
| Location-intelligence and exposure-data firms | Sell present-day built-up and population layers | Neighbours for the built-up product | [M] |

### 22.5 Pricing hypotheses

These are hypotheses to test with five customers, anchored on the prices found for adjacent products.

| Plan | For | Includes | Hypothesis |
|---|---|---|---|
| Open | Everyone | Global L6 layers, scorecard, benchmark | Free, CC-BY |
| Starter | A team with one region | L3 layers for one country or biome; interface quota; area reports | €6,000–12,000 a year |
| Professional | A platform or large importer | Several regions; batch scoring; watchlists; support | €25,000–60,000 a year |
| Enterprise | Global groups, reinsurers | Global L3; on-request L0; bulk delivery; service terms | Custom |
| Partner | Compliance platforms | Embedding our layer in their product | Per scored polygon per year, or revenue share |
| Public interest | Agencies and non-profits in producer countries | Fine layers for their jurisdiction | Free or at cost |

### 22.6 Sales motion

1. **Publish the exam.** The lock, then the grade, are the marketing.
2. **Three design partners before April 2027**, one per segment that looks promising: a platform, an importer, a conservation agency. Each names a use and a measure of success.
3. **Region-specific backtests** on a prospect's own areas within a week of first contact. This is the demonstration.
4. **Partner integration** as the default path to importers.
5. **Never sell ahead of the scorecard.** A layer that has not been backtested in a region is not sold there.

### 22.7 Non-dilutive funding to explore

All from memory; eligibility and current status MUST be checked. [M]

| Source type | What it could fund |
|---|---|
| Cloud providers' credit programmes for start-ups and for open data | Storage and compute for Stage 1 and 2 |
| Open-data sponsorship programmes that host public datasets | Hosting of our public layers and benchmark |
| Space-agency incubators and Earth-observation application grants | Early salaries and pilots |
| European and national innovation grants | Research and development |
| Climate and nature philanthropies | Public-interest tier; producer-country access |
| Research collaborations with universities | Evaluation rigour; a route to peer review |

### 22.8 Commercial measures

| Measure | Alpha target (April 2027) | Scale target (August 2027) |
|---|---|---|
| Design partners signed | 3 | 5 paying |
| Regions with a graded backtest | 3 | 12 |
| Monthly active keys | 20 | 150 |
| Area scored through the interface per month | 1 million km² | 20 million km² |
| Outside verifications of a package | 10 | 100 |
| Annual recurring revenue | — | First €50,000 |

---

## 23. Legal and licensing

Nothing here is legal advice. Section 23.8 lists the questions for counsel.

### 23.1 Entity and ownership

- Incorporate before signing any customer or partner. Jurisdiction chosen with counsel, considering founders' residence, customers and grant eligibility.
- Every contributor assigns intellectual property to the entity in writing, including work done before incorporation.
- Founder vesting and a simple decision rule for deadlock are agreed before the first exam, not after.

### 23.2 Licences for what we publish

| Thing | Licence | Reason |
|---|---|---|
| Readers, grid utilities, metrics, grader, verification tool | Apache-2.0 | Trust requires that anyone can run the grader and verifier |
| Benchmark datasets and splits | CC-BY 4.0, subject to upstream terms | Adoption |
| Public L6 forecast layers and baselines | CC-BY 4.0 | Public record |
| Model code | Apache-2.0 | Reproducibility of the open layers |
| L6 model weights | Open, with the responsible-use terms attached | Reproducibility; decide the exact licence with counsel |
| Finer-level layers and their weights | Commercial terms; released openly once graded | Revenue |
| Documentation | CC-BY 4.0 | — |

### 23.3 The open-core line

| Open | Commercial |
|---|---|
| Everything needed to verify a claim: manifests, proofs, grader, baselines, L6 layers | Finer levels before grading |
| The method and the model code | Regional models tuned with partners |
| The benchmark | The interface, reports, watchlists, bulk delivery, support and service terms |
| | On-request L0 |

The rule: a stranger can always check the public record. Convenience, resolution and service are what is sold.

### 23.4 Obligations to others

- Attribution for every CC-BY source, generated from the register (section 6.6).
- Share-alike for databases derived from ODbL sources. Keep those derived tables separate and publish them.
- No use of restricted sources in commercial builds, enforced by the licence gate.
- The mirror is a community service. Be a considerate client, credit it, and consider sponsoring it once there is revenue.

### 23.5 Contracts to prepare before Phase 6

| Document | Purpose |
|---|---|
| Terms of service | Access, acceptable use, limits |
| Responsible-use policy | Section 19.6, incorporated by reference |
| Service terms | Availability targets and remedies, from general availability |
| Data processing agreement | Customer personal data |
| Master services agreement and order form | Enterprise sales |
| Partner agreement | Embedding, branding, attribution, revenue share |
| Design-partner letter | Free access in exchange for feedback and a reference |

### 23.6 Disclaimers and liability

- Forecasts are probabilistic rankings. They are not advice, not a determination about any person or parcel, and not evidence of legal compliance.
- This statement appears in the terms, in every report, and in the interface response.
- Liability is capped in contracts. Professional indemnity insurance is in place before the first paid contract.
- A customer's decision to act on a forecast is the customer's.

### 23.7 Name and marks

- Search trademarks for the chosen name in the main markets before public use.
- Register the name and logo once chosen.
- Secure domains and handles on the day the name is decided.

### 23.8 Questions for counsel

1. Does training a model on features derived from ODbL data create share-alike duties for the weights or the forecasts?
2. What licence should the open weights carry so the responsible-use terms are enforceable?
3. Can a public benchmark dataset with no stated licence be used for published research comparison? For commercial claims?
4. What is our exposure if a customer acts on a forecast and suffers a loss, or harms a third party?
5. Is the product outside the high-risk categories of the EU's AI law? What documentation should we keep to show it?
6. Do customer areas of interest count as trade secrets we must protect to a particular standard?
7. Which jurisdiction's sanctions rules apply to an open data layer versus a paid service?
8. What must the attribution and "changes made" notices say for CC-BY data transformed into forecasts?
9. Is a publicly graded forecast about a named region capable of being defamatory of land users there? How should hit-and-miss examples be presented?
10. What terms does the mirror impose, if any, beyond the dataset licence?

---

## 24. Risk register

Likelihood and impact: L low, M medium, H high. Reviewed every Friday.

| ID | Risk | L | I | Early signal | Mitigation | Response if it happens |
|---|---|---|---|---|---|---|
| R01 | Yearly embeddings too noisy to show real change | M | H | Gate 0 fails | Test at three levels before deciding | Stop in week 1 |
| R02 | Change is forecastable only by proximity | M | H | Model ties B3 or B4 | Strong baselines from the start; neighbours and drivers in the model | Ship the baseline as the product, or stop |
| R03 | Skill at coarse levels only | M | M | L6 passes, L3 fails | Coarse-first plan | Sell coarse risk; drop detail |
| R23 | The patch sample biases training or scores | M | H | Weighted totals from the sample disagree with the streaming summaries | Inclusion probabilities stored and used as weights; richer sampling in test tiles; rule committed before the pass | Re-stream with a larger stable share |
| R04 | Mirror withdrawn or throttled | M | H | Errors, policy notice | Local copies; fallback route tested quarterly | Switch to the paid route; budget for it |
| R05 | Past years reprocessed by the supplier | M | M | New version value | Version pin; raw cache; digests | Rebuild on the new version as a new dataset; never mix |
| R06 | The 2026 layer arrives late or not at all | L | H | No rows by March | Second-source test; interim truth from alerts | Grade on alerts and yearly forest map; evaluate a second source |
| R07 | Supplier or reference authors ship a forecast product | M | H | Announcements | Speed; a graded public record; partners | Compete on record, openness and service; consider building on theirs |
| R08 | Leakage inflates the backtest | M | H | Scores drop sharply on the forward exam | Tile splits; buffer; independent review; test touched once | Publish the gap; fix; supersede |
| R09 | Label noise makes readout grades meaningless | M | M | Two label sources disagree more than the model's error | Grade on agreement of sources; report label disagreement | Withhold the readout layer |
| R10 | A regime shift breaks the model in a region | M | M | Regional skill turns negative | National drivers; stratified reporting | Report it; lower confidence in that region |
| R11 | An integrity incident: a locked package or grade is wrong | L | H | Verification failure | Two-person lock; independent rebuild; external proofs | Section 18.5, severity S0 |
| R12 | Forecasts used to harm communities | L | H | A request in a contested area | Responsible-use policy; ethics review; coarse public layer | Refuse or suspend |
| R13 | Licence breach through a restricted source | M | M | A register row still [M] at Phase 6 | Licence gate; counsel's sign-off | Remove the source; rebuild |
| R14 | Team too small for the January date | H | M | Phase 1 runs past week 3 | Cut list in 16.12 | Lock a baseline forecast on time |
| R15 | Laptop cannot train the model in time | M | L | Task 2.2 measurement | Cloud GPU budget | Move training to the cloud |
| R16 | Dependency breakage in the mapping stack | M | M | Orientation test fails after an update | Pinned versions; nightly real read | Hold the upgrade; report upstream |
| R17 | The wedge market shrinks or delays again | M | M | Regulatory news | Second segment in development from Phase 6 | Shift emphasis to conservation and exposure |
| R18 | Buyers will not pay for a forecast, only for monitoring | M | H | Design partners use it but will not pay | Sell through platforms; price per polygon | Become a layer inside monitoring products |
| R19 | Public map helps bad actors avoid scrutiny | L | M | Clearing shifts to low-risk cells | Coarse public layer; fine layers controlled | Review what is public; consult advisers |
| R20 | Founder disagreement or loss of a key person | M | H | — | Written roles, vesting, documented runbooks | — |
| R21 | Compute or storage costs run away | L | M | Budget alert | Guardrails in 20.7 | Stop the job; review |
| R22 | Overview levels are not what we assume | M | M | Task 0.7 result | Build our own coarse levels from L0 for a sample | Adjust section 7; accept higher transfer |

---

## 25. Roadmap and measures

### 25.1 Twelve months

| Quarter | Theme | Outcomes |
|---|---|---|
| Nov 2026–Jan 2027 | Earn the right to exist | Gates 0–3; issue `2027.01` locked on 15 January |
| Feb–Apr 2027 | First exam; first users | Final grade published; cloud pipelines; interface and app; three design partners |
| May–Aug 2027 | Scale and harden | Global L3; mid-year issue; benchmark open; security audit under way; first revenue |
| Sep 2027–Jan 2028 | Second exam | Issue `2028.01`; two-year record; general availability decision |

### 25.2 The one number

**Skill on the forward exam:** relative improvement in average precision over the best baseline, on truth that did not exist when the forecast was locked, in regions held out of training.

Everything else is in service of that number being real, positive, and believed.

### 25.3 Measures by phase

| Phase | Measure | Target |
|---|---|---|
| 0 | Ratio of changed-cell share at change sites to stable sites | At least 5 |
| 1 | Baseline report regenerates from one command | Yes |
| 1 | Pre-registration timestamped before training | Yes |
| 2 | Stage B skill against the best baseline | At least 20%, lower bound above 10% |
| 2 | Expected calibration error | Below 0.02 |
| 3 | Forest readout skill on independent labels in held-out regions | Positive |
| 4 | Independent rebuild digests match | Yes |
| 4 | Lock date met | 15 January 2027 |
| 5 | Days from 95% truth coverage to final grade | 14 or fewer |
| 5 | Forward-exam skill | Positive, and reported whatever it is |
| 6 | Design partners | 3 |
| 7 | Regions with graded backtests | 12 |
| 8 | Issues graded in public | 3 or more |

### 25.4 Objectives for the first quarter

**Objective 1: prove or disprove the science.**
- Gate 0 decided by 22 November with an evidence pack.
- Five baselines scored on fixed folds by 6 December; the sixth, which shares the model's code, by 13 December.
- Stage B result reproduced by a second person by 27 December.

**Objective 2: make the claim impossible to fake.**
- Pre-registration timestamped by 6 December.
- Package locked with at least three independent proofs by 15 January.
- A person outside the team verifies the package from the README alone.

**Objective 3: be understood.**
- Scorecard site live at lock, readable without scripts.
- A one-page method note per public layer, tested on a non-specialist.
- Three conversations with potential design partners before the lock.

---

# PART H — APPENDICES

## Appendix A. Code skeletons

**None of this code has been run.** Each skeleton is a starting point for the task named beside it. Each needs tests before anyone relies on it.

### A.1 Query the supplier index (task 0.2)

Download `aef_index.parquet` once (78 MB) and query the local copy.

```python
import duckdb

MIRROR_S3 = "s3://us-west-2.opendata.source.coop/"
MIRROR_HTTPS = "https://data.source.coop/"


def tiles_for_bbox(
    index_path: str, west: float, south: float, east: float, north: float, years: list[int]
) -> list[tuple]:
    """Rows of the index whose footprint box overlaps the query box."""
    con = duckdb.connect()
    query = """
        SELECT path, year, utm_zone, crs, utm_west, utm_south, utm_east, utm_north
        FROM read_parquet(?)
        WHERE year IN (SELECT unnest(?))
          AND wgs84_east  >= ? AND wgs84_west  <= ?
          AND wgs84_north >= ? AND wgs84_south <= ?
        ORDER BY year, path
    """
    return con.execute(query, [index_path, years, west, east, south, north]).fetchall()


def to_https(path: str) -> str:
    """Confirm the form of the `path` column in task 0.2 before trusting this."""
    return path.replace(MIRROR_S3, MIRROR_HTTPS) if path.startswith(MIRROR_S3) else path


def count_files_per_year(index_path: str) -> list[tuple]:
    con = duckdb.connect()
    return con.execute(
        "SELECT year, count(*) FROM read_parquet(?) GROUP BY year ORDER BY year", [index_path]
    ).fetchall()
```

### A.2 Read one fine-resolution block (task 0.3)

```python
import numpy as np
import rasterio
from rasterio.windows import Window

BLOCK = 1024
BANDS = 64
NODATA = -128

GDAL_ENV = {
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tiff,.vrt",
    "GDAL_HTTP_MULTIRANGE": "YES",
    "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES",
    "GDAL_HTTP_MAX_RETRY": "5",
    "GDAL_HTTP_RETRY_DELAY": "2",
    "VSI_CACHE": "TRUE",
}


def read_block(vrt_url: str, block_row: int, block_col: int) -> tuple[np.ndarray, np.ndarray]:
    """One internal block through the north-up sidecar file.

    Returns stored values, int8 [64, 1024, 1024], and a validity mask, bool [1024, 1024].
    Row offsets that are multiples of 1024 stay block-aligned after the vertical flip,
    because the tile height (8192) is itself a multiple of 1024.
    """
    if not (0 <= block_row < 8 and 0 <= block_col < 8):
        raise ValueError(f"block ({block_row}, {block_col}) outside 0..7")
    window = Window(block_col * BLOCK, block_row * BLOCK, BLOCK, BLOCK)
    with rasterio.Env(**GDAL_ENV):
        with rasterio.open(f"/vsicurl/{vrt_url}") as ds:
            if (ds.count, ds.width, ds.height) != (BANDS, 8192, 8192):
                raise ValueError(f"unexpected layout in {vrt_url}")
            values = ds.read(window=window)
    valid = (values != NODATA).all(axis=0)
    return values, valid
```

The orientation test (section 14.6) decides whether this reader is correct. Do not skip it.

### A.3 Read a coarse level (task 1.1)

Two routes. Measure bytes transferred for each on one tile; keep the one that uses the pyramid and passes the orientation test.

```python
def read_level_via_vrt(vrt_url: str, level: int) -> np.ndarray:
    """Decimated read through the sidecar file. May or may not hit the stored pyramid."""
    side = 8192 >> level
    with rasterio.Env(**GDAL_ENV):
        with rasterio.open(f"/vsicurl/{vrt_url}") as ds:
            return ds.read(out_shape=(BANDS, side, side))


def read_level_direct(tiff_url: str, level: int) -> np.ndarray:
    """Open a stored pyramid level of the raw file and flip rows to north-up.

    Level 1 is the first stored overview, so the overview index is level - 1.
    The flip assumes the raw file is bottom-up; the orientation test must confirm it.
    """
    if level < 1:
        raise ValueError("use read_block for level 0")
    with rasterio.Env(**GDAL_ENV):
        with rasterio.open(f"/vsicurl/{tiff_url}", OVERVIEW_LEVEL=level - 1) as ds:
            values = ds.read()
    return values[:, ::-1, :].copy()
```

### A.4 Decode, mask, check (tasks 0.3, 0.6)

```python
def dequantize(values: np.ndarray) -> np.ndarray:
    """Stored int8 -> float32 in [-1, 1]. Apply the validity mask separately."""
    v = values.astype(np.float32)
    return ((v / 127.5) ** 2) * np.sign(v)


def renormalize(emb: np.ndarray, axis: int = 0, eps: float = 1e-6) -> np.ndarray:
    """Return unit-length vectors along `axis`. Needed after reading any coarse level."""
    norm = np.linalg.norm(emb, axis=axis, keepdims=True)
    return emb / np.maximum(norm, eps)


def length_report(emb: np.ndarray, valid: np.ndarray) -> dict[str, float]:
    """Quality gate Q4: distribution of vector length over valid cells. emb is [64, H, W]."""
    length = np.linalg.norm(emb, axis=0)[valid]
    q = np.percentile(length, [1, 50, 99])
    return {"p01": float(q[0]), "p50": float(q[1]), "p99": float(q[2]), "n": int(length.size)}
```

### A.5 Change and threshold (tasks 0.8, 0.9, 1.8)

```python
def cosine_change(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """a, b: unit-length float arrays [64, H, W]. Returns [H, W] in [0, 2]."""
    return 1.0 - np.sum(a * b, axis=0)


def threshold_from_stable(deltas: list[np.ndarray], percentile: float = 99.0) -> float:
    """Pool change values from stable control cells; return the chosen percentile."""
    pooled = np.concatenate([d.ravel() for d in deltas])
    return float(np.percentile(pooled, percentile))
```

### A.6 Baselines (task 1.9)

```python
from scipy.ndimage import gaussian_filter


def b1_great_circle(prev: np.ndarray, curr: np.ndarray) -> np.ndarray:
    """Continue last year's rotation on the sphere. prev, curr: unit vectors [64, H, W]."""
    dot = np.sum(prev * curr, axis=0, keepdims=True)
    return renormalize(2.0 * dot * curr - prev, axis=0)


def b2_last_change(prev: np.ndarray, curr: np.ndarray) -> np.ndarray:
    """Score = last year's change."""
    return cosine_change(prev, curr)


def b3_proximity(
    events: list[np.ndarray],
    cell_m: float,
    radius_m: float = 5000.0,
    year_weights: tuple[float, ...] = (0.5, 0.3, 0.2),
) -> np.ndarray:
    """Score = distance-weighted sum of change events in recent years.

    events: most recent first, each bool [H, W]. Tiles must be padded with neighbours
    before filtering, or edges will be biased.
    """
    sigma = (radius_m / cell_m) / 2.0
    score = np.zeros(events[0].shape, dtype=np.float32)
    for w, ev in zip(year_weights, events):
        score += w * gaussian_filter(ev.astype(np.float32), sigma=sigma, mode="constant")
    return score
```

B4 is a gradient-boosted model over a feature table: own change in each of the last three years; mean and maximum change within 1, 3 and 9 cells; the 64 current embedding values; every driver. Fit on a uniform sample of training cells plus all changed cells, with sample weights that undo the oversampling.

### A.7 Metrics (task 1.10)

```python
from scipy.ndimage import uniform_filter
from scipy.stats import norm
from sklearn.metrics import average_precision_score


def precision_at_top(y: np.ndarray, score: np.ndarray, share: float) -> float:
    """Precision among the top `share` of cells by score. y: 0/1."""
    k = max(1, int(round(share * score.size)))
    top = np.argpartition(-score.ravel(), k - 1)[:k]
    return float(y.ravel()[top].mean())


def fractions_skill_score(prob: np.ndarray, event: np.ndarray, window: int) -> float:
    """1 is perfect, 0 is no skill. prob, event: [H, W]."""
    f = uniform_filter(prob.astype(np.float64), size=window, mode="constant")
    o = uniform_filter(event.astype(np.float64), size=window, mode="constant")
    denominator = np.mean(f**2) + np.mean(o**2)
    return float(1.0 - np.mean((f - o) ** 2) / denominator) if denominator > 0 else float("nan")


def crps_gaussian(y: np.ndarray, mu: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """Closed-form continuous ranked probability score for a normal forecast."""
    z = (y - mu) / sigma
    return sigma * (z * (2.0 * norm.cdf(z) - 1.0) + 2.0 * norm.pdf(z) - 1.0 / np.sqrt(np.pi))


def expected_calibration_error(y: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    """Equal-mass bins."""
    order = np.argsort(p)
    total = 0.0
    for chunk in np.array_split(order, bins):
        if chunk.size:
            total += chunk.size * abs(p[chunk].mean() - y[chunk].mean())
    return float(total / p.size)


def paired_block_bootstrap(y, p_model, p_ref, block_ids, draws: int = 2000, seed: int = 0):
    """Interval for the relative improvement in average precision, resampling whole tiles."""
    rng = np.random.default_rng(seed)
    blocks = np.unique(block_ids)
    members = {b: np.flatnonzero(block_ids == b) for b in blocks}
    out = np.empty(draws)
    for i in range(draws):
        idx = np.concatenate([members[b] for b in rng.choice(blocks, size=blocks.size)])
        model = average_precision_score(y[idx], p_model[idx])
        ref = average_precision_score(y[idx], p_ref[idx])
        out[i] = (model - ref) / ref
    return np.percentile(out, [2.5, 50.0, 97.5])
```

At global scale the bootstrap is run on a fixed, stratified subsample of cells per tile, chosen before any score is seen and recorded in the pre-registration.

### A.8 Model (tasks 2.2–2.4)

```python
import torch
from torch import nn
from torch.nn import functional as F


class Block(nn.Module):
    """Attention across years for each cell, then mixing across neighbouring cells."""

    def __init__(self, d: int, heads: int, dropout: float = 0.05) -> None:
        super().__init__()
        self.norm_t = nn.LayerNorm(d)
        self.attn = nn.MultiheadAttention(d, heads, dropout=dropout, batch_first=True)
        self.norm_s = nn.LayerNorm(d)
        self.depthwise = nn.Conv2d(d, d, kernel_size=3, padding=1, groups=d)
        self.pointwise = nn.Conv2d(d, d, kernel_size=1)
        self.norm_f = nn.LayerNorm(d)
        self.ff = nn.Sequential(nn.Linear(d, 4 * d), nn.GELU(), nn.Dropout(dropout), nn.Linear(4 * d, d))

    def forward(self, x: torch.Tensor, absent: torch.Tensor) -> torch.Tensor:
        # x: [B, S, P, P, d]; absent: [B, S] bool, True where a year is missing.
        # The two query positions are never absent, so no sequence is fully masked.
        b, s, p, _, d = x.shape
        h = self.norm_t(x).permute(0, 2, 3, 1, 4).reshape(b * p * p, s, d)
        mask = absent[:, None, :].expand(b, p * p, s).reshape(b * p * p, s)
        a, _ = self.attn(h, h, h, key_padding_mask=mask, need_weights=False)
        x = x + a.reshape(b, p, p, s, d).permute(0, 3, 1, 2, 4)

        h = self.norm_s(x).reshape(b * s, p, p, d).permute(0, 3, 1, 2)
        h = self.pointwise(self.depthwise(h)).permute(0, 2, 3, 1).reshape(b, s, p, p, d)
        x = x + h
        return x + self.ff(self.norm_f(x))


class Almanac(nn.Module):
    def __init__(
        self,
        c: int = 64,
        f: int = 12,
        d: int = 192,
        layers: int = 8,
        heads: int = 4,
        k: int = 5,
        n_readouts: int = 4,
        loc_dim: int = 64,
    ) -> None:
        super().__init__()
        self.k = k
        self.proj_in = nn.Sequential(nn.LayerNorm(c), nn.Linear(c, d))  # one per embedding source
        self.proj_drivers = nn.Linear(f, d)
        self.proj_loc = nn.Linear(loc_dim, d)
        self.position = nn.Parameter(torch.zeros(k + 2, d))  # k years, horizon 1, horizon 2
        self.absent_token = nn.Parameter(torch.zeros(d))
        self.query = nn.Parameter(torch.zeros(2, d))
        self.blocks = nn.ModuleList(Block(d, heads) for _ in range(layers))
        self.norm = nn.LayerNorm(d)
        self.head_mean = nn.Linear(d, c)
        self.head_spread = nn.Linear(d, c)
        self.head_change = nn.Linear(d, 1)
        self.head_readout = nn.Linear(d, n_readouts)
        for param in (self.position, self.absent_token, self.query):
            nn.init.normal_(param, std=0.02)

    def forward(self, emb: torch.Tensor, absent: torch.Tensor, drivers: torch.Tensor, loc: torch.Tensor):
        # emb: [B, K, C, P, P] decoded floats; absent: [B, K] bool;
        # drivers: [B, F, P, P]; loc: [B, loc_dim]
        b, k, _, p, _ = emb.shape
        x = self.proj_in(emb.permute(0, 1, 3, 4, 2))  # [B, K, P, P, d]
        x = torch.where(absent[:, :, None, None, None], self.absent_token.expand_as(x), x)
        q = self.query[None, :, None, None, :].expand(b, 2, p, p, -1)
        x = torch.cat([x, q], dim=1) + self.position[None, :, None, None, :]
        x = x + self.proj_drivers(drivers.permute(0, 2, 3, 1))[:, None]
        x = x + self.proj_loc(loc)[:, None, None, None, :]
        mask = torch.cat([absent, absent.new_zeros(b, 2)], dim=1)
        for block in self.blocks:
            x = block(x, mask)
        y = self.norm(x[:, k:])  # [B, 2, P, P, d]
        mean = F.normalize(self.head_mean(y), dim=-1)
        spread = F.softplus(self.head_spread(y)) + 1e-4
        return mean, spread, self.head_change(y).squeeze(-1), self.head_readout(y)


def gaussian_nll(
    target: torch.Tensor, mean: torch.Tensor, spread: torch.Tensor, valid: torch.Tensor
) -> torch.Tensor:
    """target, mean, spread: [B, 2, P, P, C]; valid: [B, 2, P, P] bool."""
    nll = 0.5 * ((target - mean) / spread) ** 2 + torch.log(spread)
    per_cell = nll.sum(dim=-1)
    return (per_cell * valid).sum() / valid.sum().clamp(min=1)
```

Known gaps in this skeleton, to close in task 2.1–2.2: cells that are invalid in a given year are not yet masked inside the spatial mixing; the two heads share one trunk with no stop-gradient option; no test yet proves that an absent year cannot influence the output.

### A.9 Location features (task 2.1)

Points are mapped to three dimensions first, so there is no seam at 180° longitude.

```python
def make_location_frequencies(m: int = 32, scale: float = 8.0, seed: int = 0) -> torch.Tensor:
    """Fixed, never trained. Store the seed and scale in the model configuration."""
    generator = torch.Generator().manual_seed(seed)
    return torch.randn(m, 3, generator=generator) * scale


def location_features(
    lon_deg: torch.Tensor, lat_deg: torch.Tensor, frequencies: torch.Tensor
) -> torch.Tensor:
    lon, lat = torch.deg2rad(lon_deg), torch.deg2rad(lat_deg)
    xyz = torch.stack([lat.cos() * lon.cos(), lat.cos() * lon.sin(), lat.sin()], dim=-1)
    projected = xyz @ frequencies.T
    return torch.cat([projected.sin(), projected.cos()], dim=-1)  # [B, 2m]
```

### A.10 Package manifest and digest (task 4.5)

```python
import hashlib
import json
from pathlib import Path

EXCLUDED_DIRS = {"signatures", "timestamps"}


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def build_manifest(root: Path, meta: dict) -> tuple[dict, str]:
    """Return the manifest and the package digest. `meta` holds issue, versions, code commit."""
    files = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or path.name == "manifest.json" or relative.parts[0] in EXCLUDED_DIRS:
            continue
        files.append({"path": relative.as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    manifest = {"schema": "almanac.manifest/1", **meta, "files": files}
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return manifest, hashlib.sha256(canonical).hexdigest()


def verify_manifest(root: Path, manifest: dict) -> list[str]:
    """Return a list of problems; empty means every listed file matches."""
    problems = []
    for entry in manifest["files"]:
        path = root / entry["path"]
        if not path.is_file():
            problems.append(f"missing: {entry['path']}")
        elif sha256_file(path) != entry["sha256"]:
            problems.append(f"digest mismatch: {entry['path']}")
    return problems
```

---

## Appendix B. Configuration templates

Templates, not tested files. Pin every version at setup.

### B.1 `pyproject.toml`

```toml
[project]
name = "almanac"
version = "0.1.0"
description = "Forecasts of Earth-surface change, locked before the truth exists."
requires-python = ">=3.12,<3.14"
dependencies = [
  "numpy",
  "rasterio",
  "pyproj",
  "duckdb",
  "zarr>=3",
  "scipy",
  "scikit-learn",
  "pydantic>=2",
  "typer",
]

[project.optional-dependencies]
train = ["torch", "lightgbm", "mlflow"]
serve = ["fastapi", "uvicorn"]

[project.scripts]
almanac = "almanac.cli.main:app"

[dependency-groups]
dev = ["pytest", "hypothesis", "ruff", "pyright", "pre-commit", "pip-audit"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 110
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "PL", "RUF"]

[tool.pyright]
typeCheckingMode = "strict"
include = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
  "network: reads from a live supplier",
  "gpu: needs a GPU",
  "slow: takes more than ten seconds",
]
addopts = "-m 'not network and not gpu' --strict-markers"
```

### B.2 Continuous integration workflow

```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  fast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<commit digest>
      - uses: astral-sh/setup-uv@<commit digest>
      - run: uv sync --frozen --group dev
      - run: uv run ruff format --check .
      - run: uv run ruff check .
      - run: uv run pyright
      - run: uv run pytest tests/unit tests/property
      - run: uv run python tools/check_import_rules.py
      - run: uv run python tools/check_licence_gate.py --target research

  data:
    runs-on: ubuntu-latest
    needs: fast
    steps:
      - uses: actions/checkout@<commit digest>
      - uses: astral-sh/setup-uv@<commit digest>
      - run: uv sync --frozen --group dev
      - run: uv run pytest tests/golden tests/integration

  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<commit digest>
      - uses: astral-sh/setup-uv@<commit digest>
      - run: uv sync --frozen --group dev
      - run: uv run pip-audit
```

### B.3 Container image

```dockerfile
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:<pinned tag>@sha256:<digest> /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev

FROM python:3.12-slim
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=build /app /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
ENTRYPOINT ["almanac"]
```

### B.4 Object-locked forecast bucket (infrastructure as code)

```hcl
resource "aws_s3_bucket" "forecasts" {
  bucket              = "almanac-${var.env}-forecasts"
  object_lock_enabled = true
}

resource "aws_s3_bucket_versioning" "forecasts" {
  bucket = aws_s3_bucket.forecasts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_object_lock_configuration" "forecasts" {
  bucket = aws_s3_bucket.forecasts.id
  rule {
    default_retention {
      mode  = "COMPLIANCE"
      years = 10
    }
  }
}

resource "aws_s3_bucket_public_access_block" "forecasts" {
  bucket                  = aws_s3_bucket.forecasts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

Compliance-mode retention cannot be shortened or removed by anyone, including the account owner. Rehearse in a throwaway account with a one-day retention before applying this to production.

### B.5 Dataset configuration

```yaml
name: G-L6
level: 6
years: [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
source:
  route: source_coop
  base: https://data.source.coop/tge-labs/aef/v1/annual/
  index: aef_index.parquet
  expect_dataset_version: "1.1"
read:
  method: direct_overview        # or: vrt_decimated, after the task 1.1 comparison
  renormalize: true
  max_connections: 16
  retries: 5
  keep_raw: false                # lean plan: digests and object tags only
sample:
  patch: 32
  keep_changed: true
  keep_adjacent_to_changed: true
  stable_target_share: 0.10
  stable_share_in_test_tiles: 0.25
  seed: 20261123
  store_inclusion_probability: true
store:
  encoding: year_difference_int8 # adopt only if task 0.11 confirms the gain
  compression: zstd
labels: [LF1, LB2]
drivers: [DR1, DR2, DR5, DR6, DR7]
drivers_valid_as_of: 2023
gates: [Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10]
split:
  version: split-v1
  superblock_degrees: 2
  seed: 20261201
  shares: {train: 0.7, validation_region: 0.1, test_region: 0.2}
  buffer_tiles: 1
```

### B.6 Training run configuration

```yaml
run: stageA-M-seed0
dataset: G-L6-<date>-<digest>
stage: A
targets:
  train: [2018, 2019, 2020, 2021, 2022, 2023]
  select: [2024]
model:
  size: M
  width: 192
  layers: 8
  heads: 4
  history_window: 5
  patch: 32
  drivers: 12
  readouts: [forest_loss, builtup_gain, cropland_gain, cropland_loss]
  location: {features: 64, scale: 8.0, seed: 0}
loss:
  embedding_nll: 1.0
  change_bce: 1.0
  readout_bce: 0.5
  positive_weight_cap: 20
sampling:
  changed_share: 0.5
optim:
  name: adamw
  lr: 1.1e-4
  schedule: constant
  weight_decay: 0.0
  grad_clip: 0.5
  ema: 0.999
train:
  batch: 16
  steps: 100000
  eval_every: 5000
  precision: mixed
  workers: 4
augment:
  flips_and_rotations: true
  truncate_history: true
  mask_one_year_probability: 0.15
seed: 0
deterministic: true
```

### B.7 Data source register, machine form

```yaml
- id: AEF
  name: AlphaEarth Foundations Satellite Embedding V1 annual
  role: input
  licence: CC-BY-4.0
  commercial: allowed
  attribution: "The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind."
  evidence: V
  verified_on: 2026-11-14
- id: LF1
  name: Global Forest Change v1.13
  role: label
  licence: CC-BY-4.0
  commercial: allowed
  evidence: M          # licence from memory; version verified
  verified_on: null
- id: DR3
  name: World Database on Protected Areas
  role: driver
  licence: restricted
  commercial: needs_permission
  evidence: M
  verified_on: null
```

The licence gate reads this file. A pipeline that declares an ID whose `commercial` field is not `allowed` fails the commercial build.

---

## Appendix C. Document templates

### C.1 Pre-registration

```markdown
# Pre-registration — issue <issue_id>

Timestamped on: <date>            Proofs: <links>
Authors: <names>                  Reviewed by: <adviser>

## 1. Claim
We forecast <what> for target years <years> using data up to <cutoff year>.

## 2. Data
- Input dataset and version:
- Dataset version ID and digest:
- Levels:
- Tiles included and excluded, with reasons:
- Split version, held-out regions (named):

## 3. Change definition
- Threshold tau per level and how it was set:
- Label sources for each readout:

## 4. Primary metric and win condition
- Metric, level, horizon, fold:
- Reference baseline rule (best of B0-B5 chosen on validation):
- Win condition:
- Interval method, number of draws, seed, cell subsample rule:

## 5. Secondary metrics (reported, no claim)

## 6. Baselines
- Definitions and code versions:

## 7. Model
- Family, size, configuration digest:
- Training protocol stage and what was frozen when:

## 8. Grading
- Grader version tag:
- Truth sources, alignment method, coverage rules, partial and final grade rules:

## 9. What would count as failure

## 10. Deviations
(Empty at timestamp. Any later deviation is appended here with date and reason.)
```

### C.2 Model card

```markdown
# Model card — <model version>

## Summary
One paragraph: what it forecasts, at what level and horizon, from what data.

## Intended use
## Out-of-scope and prohibited uses

## Training data
- Dataset version, years, levels, tiles, split
- Labels and drivers used, with register IDs
- Known gaps in coverage

## Architecture and training
- Size, configuration digest, seeds, protocol stage
- Compute used

## Evaluation
- Primary metric against each baseline, with intervals (table)
- By continent and biome (table)
- Calibration (reliability curve, expected calibration error)
- Readout results on independent labels

## Limits
- Where it performs worst and why
- What it cannot see (events with no precursor, policy shocks)
- Dependence on the input supplier

## Ethical considerations
## Reproduction
Command, commit, container digest, expected tolerance.
```

### C.3 Data card

```markdown
# Data card — <dataset version>

## Summary
## Sources
| Register ID | Version | Access route | Read dates | Licence |

## Construction
- Read method, levels, renormalisation
- Label and driver processing, "valid as of" dates

## Quality gates
| Gate | Result | Notes |

## Coverage
- Tiles present per year; excluded tiles with reasons

## Split
- Version, seed, counts by continent and side, held-out regions

## Known issues
## Lineage manifest
Location and digest.
```

### C.4 Architecture decision record

```markdown
# ADR <number>: <title>

Date: <date>        Status: proposed | accepted | superseded by <n>

## Context
What forces the decision. Evidence, with links to results.

## Decision
What we will do.

## Alternatives considered
Each with the reason it lost.

## Consequences
What becomes easier, what becomes harder, what we must now watch.

## Revisit when
The observable condition that should reopen this decision.
```

### C.5 Post-exam report

```markdown
# Post-exam report — issue <issue_id>

## Verdict
One sentence against the win condition.

## Scores
Model and every baseline, primary and secondary, with intervals.

## Where it was right
## Where it was wrong
## What the baselines got that the model missed
## Calibration on new truth
## Backtest versus forward exam: the gap and its likely causes
## Changes for the next issue
## Deviations from the pre-registration
```

### C.6 Incident review

```markdown
# Incident review — <id>

Severity:        Detected:        Resolved:        Public notice: <link, for S0>

## What happened (timeline)
## Impact
## How it was detected
## Root causes
## What went well
## What we will change (owner, date)
## What we will watch to know the change worked
```

---

## Appendix D. Checklists

### D.1 Gate review

- [ ] The evidence pack regenerates from a clean checkout.
- [ ] The gate's question is answered with numbers, not impressions.
- [ ] Someone argued the opposite conclusion and was answered.
- [ ] The decision is written as an ADR.
- [ ] The risk register and open questions are updated.
- [ ] The next phase's first three tasks are assigned.

### D.2 Before any training run counts

- [ ] Dataset version frozen and named in the configuration.
- [ ] Split file committed; no test tile adjacent to a training tile.
- [ ] No driver dated after the cutoff year.
- [ ] No label from the target year used as an input.
- [ ] Input dataset version identical across all years of every tile.
- [ ] Seeds, deterministic mode and worker count set in the configuration.
- [ ] The test year is not read by this run, or the touch is logged.
- [ ] Configuration digest recorded.

### D.3 Locking an issue

Two people present. Each ticks independently.

- [ ] Promotion checklist for the model complete (15.12).
- [ ] Baselines B0–B5 produced for the same cells.
- [ ] Grader tagged and named in the pre-registration.
- [ ] Code commit tagged and signed.
- [ ] Package built by the pipeline.
- [ ] Package rebuilt independently; digests match.
- [ ] Manifest validates against its schema.
- [ ] Coverage file lists every included and excluded tile.
- [ ] Manifest signed; log entry recorded.
- [ ] Timestamp tokens obtained from two authorities.
- [ ] Blockchain anchoring submitted; receipt stored.
- [ ] Research archive deposit made; identifier recorded.
- [ ] Public repository release created with manifest and proofs.
- [ ] Package written to the object-locked bucket; lock verified by attempting an overwrite in the rehearsal account.
- [ ] Verification script run from a clean machine by the second person.
- [ ] Digest announced on two public channels.
- [ ] Scorecard shows the issue with its proofs and attribution.

### D.4 Publishing a grade

- [ ] Truth passed all quality gates.
- [ ] The cutoff-year layer used is the one stored at lock time.
- [ ] Grader version equals the one named in the pre-registration.
- [ ] Coverage stated; partial or final label correct.
- [ ] Every baseline scored on exactly the same cells.
- [ ] Intervals computed with the pre-registered method and seed.
- [ ] Stratified tables generated, none omitted.
- [ ] Ten best hits and ten worst misses selected by rule, not by hand.
- [ ] Grade record written under object lock.
- [ ] A second person reproduced the primary number.
- [ ] Any deviation from the pre-registration appended to it and shown on the scorecard.

### D.5 Software release

- [ ] All checks green on the release commit.
- [ ] Changelog generated and read by a person.
- [ ] Image built, scanned, signed; bill of materials stored.
- [ ] Database migrations reversible, rehearsed in staging.
- [ ] Load test run if a serving path changed.
- [ ] Rollback step written.
- [ ] Documentation examples executed.

### D.6 Adding a data source

- [ ] Row added to the register with role, access, licence text link, evidence label.
- [ ] Commercial-use status confirmed in writing, or the source is limited to research builds.
- [ ] Attribution text added to the generated notice.
- [ ] "Valid as of" date defined for drivers.
- [ ] Reader has unit and golden tests.
- [ ] Quality gates defined for the source.
- [ ] Storage and transfer cost estimated.
- [ ] Decision recorded as an ADR if the source affects a public number.

---

## Appendix E. Glossary

| Term | Meaning |
|---|---|
| Average precision | A score from 0 to 1 for how well a ranking puts the true events at the top. Suited to rare events |
| Backtest | Running the forecasting procedure on past data as if the later years were unknown, then scoring it against what happened |
| Baseline | A simple method scored on the same data, so a model's result has something to be compared with |
| Block | The 1024 × 1024-cell unit in which the supplier's files store data |
| Bootstrap | Estimating the uncertainty of a score by recomputing it on many resampled versions of the data |
| Calibration | The property that stated probabilities match observed frequencies |
| CC-BY | A licence that allows any use, including commercial, if the source is credited |
| Cell | One grid square at a stated level |
| Cloud-optimised GeoTIFF | An image file laid out so a program can read a small part of it over the network |
| Continuous ranked probability score | A score for a probabilistic forecast of a number; lower is better |
| Cutoff year | The last year of data a forecast is allowed to use |
| Driver | A static input that may influence change, such as distance to a road |
| Embedding | A short list of numbers a model produces to summarise something |
| Error budget | The amount of unreliability a service is allowed in a period before releases stop |
| Fractions skill score | A score that credits a forecast for being nearly in the right place |
| GeoParquet | A table file format with a geometry column |
| Grade | The recorded result of scoring a locked forecast against truth |
| Horizon | Years between the cutoff year and the target year |
| Infrastructure as code | Describing cloud resources in reviewed text files rather than clicking in a console |
| Issue | One published set of forecasts with a fixed cutoff year |
| Leakage | Information about the answer reaching the model by accident, which inflates scores |
| Level | A step in the resolution pyramid; L0 is 10 m and each level doubles the cell size |
| Lock | Making a forecast package unchangeable and provably dated |
| Manifest | The list of files in a package with their digests |
| Object lock | A storage setting that prevents anyone from altering or deleting a file for a set time |
| ODbL | A licence that allows use but requires databases derived from the data to stay open under the same terms |
| Package digest | One fingerprint that changes if any file in a package changes |
| Persistence | The baseline that assumes next year equals this year |
| PMTiles | A single file holding a whole set of map tiles |
| Pre-registration | Writing down the test, the metric and the pass mark before seeing the result |
| Probe | A small model that maps an embedding to a land class |
| Pyramid | Stored copies of an image at successively coarser resolutions |
| Readout | A land-class statement derived from a forecast embedding |
| Reliability curve | A plot of stated probability against observed frequency |
| Sidecar file | The small `.vrt` text file beside each data file that presents it north-up |
| Skill | Improvement over a reference, as a fraction: 0 is no better, 1 is perfect |
| Software bill of materials | A list of every component inside a software build |
| STAC | A standard way to describe and catalogue geospatial files |
| Target year | The year a forecast is about |
| Tile | One supplier file: 8192 × 8192 cells at L0 |
| Timestamp authority | An independent service that signs a statement that some data existed at a given time |
| UTM | A family of map projections that divide the Earth into 60 north-south zones |
| Walk-forward | Repeating a backtest with a later cutoff each time |
| Zarr | A format for large arrays stored as many small chunks |

---

## Appendix F. Verification log and sources

### F.1 Claims the plan depends on most

| Claim | Label | Where checked |
|---|---|---|
| Mirror reachable with no account; partial reads work | [V] | Header requests from the development laptop, 2026-11-14 |
| File layout, band count, 1024 blocks, separate planes, Zstandard, pyramid sizes, 3.65 GB | [V] | Header of one real file read directly |
| Sidecar file is north-up with −128 as no-data | [V] | Sidecar file read directly |
| Index files and their sizes; index columns | [V] | Header requests and first bytes of the index |
| Years 2017–2025; CC-BY 4.0; attribution text; decode formula | [V] | Mirror documentation |
| Raw files load upside-down in common tools unless handled | [S] | Third-party article |
| Archive is about 465 TB | [S] | Third-party article |
| 2025 layer began appearing 2026-01-29 | [S] | A localised catalogue page; not confirmed in English |
| Reference method's design, settings and results | [V] | Paper's full text and repository |
| Reference weights and data are non-commercial; code MIT | [V] | Repository |
| Forest-loss maps v1.13 cover 2000–2025 | [V] | Producer's download page, via search |
| EU deforestation law applies 30 Dec 2026 (large and medium) and 30 Jun 2027 (micro and small) | [S] | Law-firm and Commission summaries |
| Plot polygons above a size threshold; penalty ceiling; country risk classes | [M] | Not confirmed in this research |
| GFW Pro closes 31 Dec 2026 | [S] | Vendor comparison article; confirm at the tool's own site |
| Deep-learning library 2.15.0; Python 3.14 Windows wheels; CUDA 12.8 builds dropped | [S] | Package index and release notes, via search |
| GPU and storage prices | [S] | Provider page and price roundups |
| Overture release path and cadence | [S] | Project documentation, via search |
| Dynamic World active and CC-BY 4.0 | [S] | Catalogue page, via search |
| Licences of most label and driver sources | [M] | Not checked; see section 6 |
| Laptop: GPU, memory, disk, Python, Git | [V] | Read from the machine |

### F.2 Sources

Primary data and code:
- [AlphaEarth mirror on Source Cooperative](https://source.coop/tge-labs/aef)
- [Mirror data endpoint](https://data.source.coop/tge-labs/aef/v1/annual/)
- [aef-loader](https://github.com/jakenotjay/aef-loader)
- [E²Forecast code](https://github.com/ucam-eo/e2forecast)
- [Forecasting Earth Surface Change in Embedding Space](https://arxiv.org/abs/2611.02211)
- [AlphaEarth Foundations paper](https://arxiv.org/abs/2507.22291)
- [Satellite Embedding dataset, Earth Engine catalogue](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL)
- [AlphaEarth on Google Cloud Storage](https://medium.com/google-earth/alphaearth-foundations-satellite-embeddings-now-available-on-google-cloud-storage-f9ab0f7252d6)
- [Earth Engine non-commercial tiers](https://developers.google.com/earth-engine/guides/noncommercial_tiers)

Embeddings landscape:
- [The Technical Debt of Earth Embedding Products](https://isaac.earth/earth-embedding-products)
- [A Primer for Earth Data Embeddings](https://developmentseed.org/blog/2026-10-02-earth-embeddings/)
- [TESSERA v2](https://arxiv.org/html/2607.03949)
- [OlmoEarth v1.3](https://allenai.org/papers/olmoearth-v1-3)
- [Earth Embeddings as Products](https://arxiv.org/abs/2601.13134)
- [TorchGeo embeddings](https://wiki.osgeo.org/wiki/TorchGeo_embeddings)

Labels and drivers:
- [Global Forest Change 2000–2025 download page](https://storage.googleapis.com/earthenginepartners-hansen/GFC-2025-v1.13/download.html)
- [ForestCast, Google Research](https://research.google/blog/forecasting-the-future-of-forests-with-ai-from-counting-losses-to-predicting-risk/)
- [ForestCast paper](https://eartharxiv.org/repository/view/10674/)
- [OPERA disturbance product suite](https://www.jpl.nasa.gov/go/opera/products/dist-product-suite/)
- [OPERA disturbance alerts on the AWS open data registry](https://registry.opendata.aws/nasa-operal3dist-alert-hlsv1/)
- [Open Buildings 2.5D Temporal](https://sites.research.google/gr/open-buildings/temporal)
- [Global Human Settlement Layer datasets](https://human-settlement.emergency.copernicus.eu/datasets.php)
- [Dynamic World V1](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1)
- [Overture Maps buildings guide](https://docs.overturemaps.org/guides/buildings)
- [Overture Maps 2026-07-22 release notes](https://docs.overturemaps.org/blog/2026/07/22/release-notes/)

Regulation and market:
- [EU deforestation law: simplification package ahead of December 2026](https://www.hlc.com/en/publications/eu-deforestation-regulation-commission-publishes-simplification-package-ahead-of-december-2026)
- [Commission report COM(2026) 191](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX%3A52026DC0191)
- [Application postponed to 30 December 2026](https://taxnews.ey.com/news/2026-0237-eu-deforestation-regulation-application-postponed-to-30-december-2026)
- [Compliance software: 14 providers compared](https://polygon-one.com/en/article-eudr-software-comparison)
- [Tools for geolocation data](https://restorationscope.com/blog/eudr-geolocation-tools)
- [Compliance software for small businesses](https://eudrready.eu/eudr-software-small-business/)
- [Forest Foresight programme](https://www.wwf.nl/wat-we-doen/focus/bossen/forest-foresight-eng)
- [Forest Foresight one-pager](https://www.wwf.nl/globalassets/pdf/forest-foresight/wwf_forest_foresight_onepager.pdf)
- [Forest and human rights guideline, 2025](https://www.wwf.nl/globalassets/pdf/forest-foresight/guideline-forest--human-rights_2025.pdf)
- [UNFPA census page](https://www.unfpa.org/census?page=4)
- [EU legislators agree to delay high-risk AI rules](https://www.hoganlovells.com/en/publications/eu-legislators-agree-to-delay-for-highrisk-ai-rules)

Tooling and prices:
- [Icechunk blog](https://icechunk.io/en/stable/blog-posts/)
- [VirtualiZarr release notes](https://virtualizarr.readthedocs.io/en/latest/about/releases.html)
- [torch on the Python package index](https://pypi.org/project/torch/)
- [PyTorch releases](https://github.com/pytorch/pytorch/releases)
- [PyTorch forum: support for the newest GPU family](https://discuss.pytorch.org/t/rtx-5050-sm-120-support-timeline-when-in-stable-pytorch/224288)
- [Lambda pricing](https://lambda.com/pricing)
- [Cloud GPU pricing comparison 2026](https://www.cloudzero.com/blog/cloud-gpu-pricing-comparison/)
- [Amazon S3 pricing in 2026](https://www.manageengine.com/cloudspend/articles/s3-pricing-guide.html)

---

## Appendix G. Open questions

Reviewed every Friday. Each is closed by a task, an ADR, or counsel.

| # | Question | Closed by |
|---|---|---|
| 1 | Which Python version installs every dependency cleanly on the laptop? | Task 0.1 |
| 2 | How many files exist per year, and how many land tiles? | Task 0.2 |
| 3 | What form does the index's `path` column take? | Task 0.2 |
| 4 | Does reading through the sidecar file use the stored pyramid for coarse reads? | Task 1.1 |
| 5 | How were the pyramid levels made, and are coarse embeddings still meaningful? | Task 0.7 |
| 6 | Are the 64 band blocks of a coarse level stored contiguously? | Task 1.1 |
| 7 | Does the mirror impose rate limits or terms beyond the dataset licence? | Task 1.1; counsel |
| 8 | What is the true noise floor per level and biome? | Task 0.9 |
| 9 | What base rate of change events does the chosen threshold give at L6? | Task 1.8 |
| 10 | How much do the two forest label sources disagree at L6? | Task 1.4 |
| 11 | How fast does the laptop GPU train model M, and does mixed precision work on it? | Task 2.2 |
| 12 | Does the model beat gradient-boosted trees? | Gate 2 |
| 13 | Does skill hold in held-out regions, or only near training tiles? | Stage B |
| 14 | Does the public forest benchmark's licence allow our use? | Counsel; task 3.5 |
| 15 | How much skill survives a change of embedding supplier? | Task 3.9 |
| 16 | When exactly will the 2026 layer start to appear, and how fast will it fill? | Phase 5 |
| 17 | Will the supplier's yearly series continue on the same terms? | Watch; R06 |
| 18 | Exact legal duties under the EU deforestation law that a forward-risk layer could support | Counsel; design partners |
| 19 | Confirmed licences for every [M] row in section 6 | Before Phase 6 |
| 20 | Which licence should the open weights carry? | Counsel |
| 21 | Will any platform pay for a forecast layer, and on what unit? | Phase 6 design partners |
| 22 | Is two or three people part-time enough to meet 15 January? | Gate 1 review |
| 23 | What is the company's name? | Before the lock announcement |

---

*End of blueprint, version 0.3.*
