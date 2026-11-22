---
name: Leakage review
about: An independent leakage review of a forecast issue (docs/review/LEAKAGE_REVIEW.md)
title: "Leakage review of issue 2027.01 by <your name>"
labels: review
---

**Reviewer:** <!-- name, and how to reach you if you are happy to be contacted -->
**Relationship to the project:** <!-- e.g. none; a friend of the maintainer; a former colleague -->
**Commit reviewed:** <!-- output of: git rev-parse HEAD -->

## Part A: automated checks

<details><summary>Output of <code>uv run python tools/review/leakage_selfcheck.py</code></summary>

```
paste here
```

</details>

**Q-A.** Ended with `ALL PASS`: yes / no

## Part B

| Question | Answer (yes / no / unsure) | Notes |
|---|---|---|
| **Q-B1.** Can a training input contain cells of a scored tile? Is the touching rule enough? | | |
| **Q-B2.** Does any input for year Y depend on data from Y or later? | | |
| **Q-B3.** Could any choice have been influenced by the 2025 truth? | | |
| **Q-B4.** Could the 2026 layers differ from the frozen model's output? | | |
| **Q-B5.** Any other leak, or a reason the backtest overstates skill? | | |

## Part C: verdict

<!-- one of: No leakage found · Concerns, none disqualifying · Leakage found -->

**Verdict:**

**Anything else:**
