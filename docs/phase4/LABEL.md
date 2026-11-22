# Issue 2027.01 — forecast label

Fixed on 2026-11-21 under [ADR 0004](../adr/0004-gate-2.md), before the 2026 forecast was made. It
is published with the lock on 15 January 2027 unchanged, except that the package digest and the
lock timestamps are filled in where marked.

---

**What this is.** A forecast, made before the event, of where forest will be lost in 2026 across
the Amazon and Cerrado (74°W–41°W, 24°S–5°N), on 499 exam tiles at about 640 m. For each eligible
cell it gives the probability that at least 2.5% of the cell (about 1 hectare) loses forest in
2026, as Global Forest Change will record it.

**Headline forecast:** model M (A2), a neural network over AlphaEarth annual embeddings, the mean
of three seeds, frozen on 2026-11-21. **Locked beside it** and graded on the same truth: the
reference B5 (A2), and the simple baselines B0–B4, including gradient-boosted trees (B4).

**How it will be graded.** Rules fixed and timestamped before any model was trained
(pre-registration 2027.01 and amendments 1 and 2). The forecast wins only if all three hold on
2026 truth: its average precision is at least **20%** above the reference's; the lower end of the
95% interval of that improvement is above 10%; and it is better on the test tiles and on the
held-out region separately. Anything less is reported as not a win.

**What happened when it was tested on 2025 (backtest, graded once).** The model scored 16.0%
above the reference (95% interval +10.7% to +22.3%), better on both the test tiles (+14.4%) and the
held-out region (+15.7%). **That is short of the 20% margin, so the backtest was not a win.** The
model was locked as the headline because it was the best forecast on every part of that test;
the margin for the 2026 exam was not changed.

**Known weaknesses.**

- The probabilities ran **high** on 2025: in every tenth of the forecasts more loss was predicted
  than happened (in the ninth tenth, 16% forecast against 6% observed). Read the map as a ranking
  of risk first; treat the numbers as upper-leaning. The calibration was fitted on 2024, a year
  with more loss, and is not refitted.
- On validation (2024, 146 tiles) the model was 4.6% *below* the reference; that check was too
  small to tell the two apart, but it is part of the record.
- The 2025 test data were read twice, against the protocol's single-read rule: once for the
  graded backtest and once, by mistake, for an independent re-grade of the same frozen forecasts.
  The second read changed nothing and is logged and disclosed (ADR 0004).
- One region, one event type, one year ahead. Nothing here says the method works elsewhere.
- Built and locked by one maintainer. The second-person checks of the original plan are replaced by public, external ones: the digest has been public since 22 November 2026 and is timestamped by two independent authorities and in Bitcoin. An independent leakage review is still being sought ([ADR 0005](../adr/0005-single-maintainer.md)).

**Verify it yourself.** Package digest: `bc834b2691f0f1c9fdee05a0c0fbae87958efe3a8d3e670aeff113f9b02b7949` (sealed 2026-11-22; check it with `python tools/verify_issue.py PACKAGE --digest <digest>`). Timestamps of the digest: FreeTSA 2026-11-22 08:24:35 UTC and DigiCert 2026-11-22 08:24:37 UTC (RFC 3161), and OpenTimestamps in Bitcoin ([proofs](proofs/README.md)). Lock timestamps: `<filled in at lock>`.
Code, rules, every run (including failed ones) and the test-touch log:
https://github.com/pranavpanchal1326/Almanac.

Input data: AlphaEarth Foundations annual embeddings (CC-BY 4.0); labels: Global Forest Change.
