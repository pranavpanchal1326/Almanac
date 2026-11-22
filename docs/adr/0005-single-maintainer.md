# ADR 0005: One maintainer: what replaces the blueprint's second person

Date: 2026-11-22        Status: **accepted** (by the project owner, 2026-11-22)

## Context

Almanac is built by one person. The blueprint assumes a team of two or three and asks for a
second person in four places, three of which it lists under "never cut" (section 16.12):

| Blueprint | Requirement |
|---|---|
| Task 2.8 | A second person reproduces stage B |
| Task 3.10 | A leakage review by someone who did not build the model |
| Task 4.6, section 11 step 3 | An independent rebuild by a second person; digests must match |
| Task 4.7, rule R5, Appendix D.3 | Locking requires two people, each ticking the checklist |

These are blueprint rules, not promises made in public: the pre-registration (2027.01) and its
amendments never require a second person, so working alone breaks none of the stamped rules. But
each rule protects against something real, and dropping them silently would weaken the record.
This decision says what each was for, what replaces it, and what is lost.

## Decision

| Requirement | What it protects against | Replacement | What is lost |
|---|---|---|---|
| **Two-person lock** (4.7) | The builder quietly changing the forecast after the fact | The package digest has been public on GitHub since 22 Nov 2026 (`docs/phase4/package_2027.01_manifest.json`, commit `694b841`), and is now timestamped by two independent RFC 3161 authorities and anchored in Bitcoin (below). At the lock, the archive is also deposited with a permanent identifier. Any change to any layer changes the digest, and the change would be visible to anyone | A second human witness to the lock ceremony itself. The external timestamps make tampering detectable; they do not prevent mistakes a second reader would have caught |
| **Independent rebuild** (4.6) | A package that cannot be rebuilt from its recorded inputs | The maintainer rebuilds the package in a clean environment (fresh clone, fresh environment, recorded commit) and compares digests; the result is recorded. The frozen weights are to be published with the lock, so that anyone can rebuild it | Independence: a rebuild by the same person proves reproducibility, not that a second mind followed the recipe |
| **Leakage review** (3.10) | A leak the builder cannot see because they built it | Remains open and is the one step that still needs an outsider. A review kit (checklist of blueprint section 3.9 with evidence links) is prepared so that any reviewer can do it in about two hours, and the call for a reviewer is public. Until then the automated leakage tests stand in, and are labelled as not independent | An independent eye, until a reviewer is found |
| **Stage B reproduction** (2.8) | An error in the grade | Done by separate code that shares nothing with the grader: 64 of 64 values within tolerance (`docs/phase2/stage_b_reproduction.md`) | The same as above: separate code, not a separate person |

Every public description of the issue (the label, the scorecard, the README) states plainly that it
is built and locked by one maintainer, and links here.

## Timestamps of the package digest (done 2026-11-22)

The committed manifest `docs/phase4/package_2027.01_manifest.json` was timestamped; its SHA-256 is
the package digest, `bc834b2691f0f1c9fdee05a0c0fbae87958efe3a8d3e670aeff113f9b02b7949`. Only that
hash left the machine.

| Proof | Service | Time (UTC) |
|---|---|---|
| `docs/phase4/proofs/package_2027.01_manifest.json.freetsa.tsr` | FreeTSA, RFC 3161 | 2026-11-22 08:24:35 |
| `docs/phase4/proofs/package_2027.01_manifest.json.digicert.tsr` | DigiCert, RFC 3161 | 2026-11-22 08:24:37 |
| `docs/phase4/proofs/package_2027.01_manifest.json.ots` | OpenTimestamps (Bitcoin) | pending until a block confirms it; upgraded in a later commit |

Both RFC 3161 tokens verified (`Verification: OK`) at stamping time and again independently.
How to check them: [docs/phase4/proofs/README.md](../phase4/proofs/README.md).

## What changes in the plan

- Task 4.6 becomes a recorded clean-environment rebuild by the maintainer.
- Task 4.7 becomes a single-maintainer lock on 15 January 2027: confirm the digest still matches,
  upgrade the Bitcoin proof, deposit the archive with a permanent identifier, publish the frozen
  weights, sign the lock commit, and fill in the label. The checklist in Appendix D.3 is ticked by
  one person, and says so.
- Task 3.10 stays open until an outside reviewer is found; the lock does not wait for it, and the
  label says whether it has happened.
- Task 2.8 stands as done by separate code.

## The opposite case, argued

**"A forecast locked by one person is not trustworthy."** Trust here never rested on the
character of the people at the lock; it rests on what anyone can check. The digest was public
before any 2026 truth existed, three independent services have witnessed it, and the grade will
be computed by public code from public data. A second signer adds a witness to the ceremony, not to
the forecast. What a second person adds that nothing else does is a second mind on the method,
which is why the leakage review is kept open rather than replaced.

**"Then wait to lock until a second person is found."** The lock date does not move (blueprint,
section 16.1), and the exam is only worth taking if the forecast is fixed before the truth arrives.
Delaying the lock to find a witness would trade a real guarantee for a ceremonial one.
