# Stage B reproduction (task 2.8)

Independent re-grade of package `5e995faff2132247f4534aff7bfe8b2587290d8774040d4d39b837114ccb029e` by `tools/phase2/reproduce_stage_b.py` (no shared grading code; truth from the source label stores), commit `c231ee968d`. All checks pass: **True**.

Verdict: `M_A2` against `B5_A2`, +16.03% (95% interval +10.66% to +22.29%); win: **False**.

| Check | Reproduced | Stage B | Difference | Tolerance | OK |
|---|---|---|---|---|---|
| all: cells | 4814716 | 4814716 | 0.00e+00 | 0 | yes |
| all: events | 192761 | 192761 | 0.00e+00 | 0 | yes |
| all: AP B0 | 0.04003579858 | 0.04003579858 | 0.00e+00 | 1e-09 | yes |
| all: Brier B0 | 0.03859633897 | 0.03859633897 | 0.00e+00 | 1e-09 | yes |
| all: AP B1 | 0.07967324098 | 0.07967324098 | 0.00e+00 | 1e-09 | yes |
| all: Brier B1 | 0.0378042072 | 0.0378042072 | 0.00e+00 | 1e-09 | yes |
| all: AP B2 | 0.07946171715 | 0.07946171715 | 0.00e+00 | 1e-09 | yes |
| all: Brier B2 | 0.03780390195 | 0.03780390195 | 0.00e+00 | 1e-09 | yes |
| all: AP B3 | 0.1987325289 | 0.1987325289 | 2.78e-17 | 1e-09 | yes |
| all: Brier B3 | 0.03477066501 | 0.03477066501 | 0.00e+00 | 1e-09 | yes |
| all: AP B4 | 0.3861975553 | 0.3861975553 | 5.55e-17 | 1e-09 | yes |
| all: Brier B4 | 0.02994364615 | 0.02994364615 | 0.00e+00 | 1e-09 | yes |
| all: AP B5_A2 | 0.4036189064 | 0.4036189064 | 5.55e-17 | 1e-09 | yes |
| all: Brier B5_A2 | 0.03169537005 | 0.03169537005 | 0.00e+00 | 1e-09 | yes |
| all: AP M_A2 | 0.4683050174 | 0.4683050174 | 5.55e-17 | 1e-09 | yes |
| all: Brier M_A2 | 0.03045517437 | 0.03045517437 | 0.00e+00 | 1e-09 | yes |
| test: cells | 3416518 | 3416518 | 0.00e+00 | 0 | yes |
| test: events | 120878 | 120878 | 0.00e+00 | 0 | yes |
| test: AP B0 | 0.03538046631 | 0.03538046631 | 0.00e+00 | 1e-09 | yes |
| test: Brier B0 | 0.03419474819 | 0.03419474819 | 0.00e+00 | 1e-09 | yes |
| test: AP B1 | 0.06336874363 | 0.06336874363 | 0.00e+00 | 1e-09 | yes |
| test: Brier B1 | 0.03374774659 | 0.03374774659 | 0.00e+00 | 1e-09 | yes |
| test: AP B2 | 0.06322675796 | 0.06322675796 | 1.39e-17 | 1e-09 | yes |
| test: Brier B2 | 0.03374683668 | 0.03374683668 | 0.00e+00 | 1e-09 | yes |
| test: AP B3 | 0.1599307616 | 0.1599307616 | 0.00e+00 | 1e-09 | yes |
| test: Brier B3 | 0.03159545107 | 0.03159545107 | 0.00e+00 | 1e-09 | yes |
| test: AP B4 | 0.3151407611 | 0.3151407611 | 5.55e-17 | 1e-09 | yes |
| test: Brier B4 | 0.02838641316 | 0.02838641316 | 0.00e+00 | 1e-09 | yes |
| test: AP B5_A2 | 0.3152370646 | 0.3152370646 | 5.55e-17 | 1e-09 | yes |
| test: Brier B5_A2 | 0.03054555145 | 0.03054555145 | 0.00e+00 | 1e-09 | yes |
| test: AP M_A2 | 0.3605396386 | 0.3605396386 | 0.00e+00 | 1e-09 | yes |
| test: Brier M_A2 | 0.02997577962 | 0.02997577962 | 0.00e+00 | 1e-09 | yes |
| held_out: cells | 1398198 | 1398198 | 0.00e+00 | 0 | yes |
| held_out: events | 71883 | 71883 | 0.00e+00 | 0 | yes |
| held_out: AP B0 | 0.05141117352 | 0.05141117352 | 0.00e+00 | 1e-09 | yes |
| held_out: Brier B0 | 0.04935169273 | 0.04935169273 | 0.00e+00 | 1e-09 | yes |
| held_out: AP B1 | 0.2151333467 | 0.2151333467 | 0.00e+00 | 1e-09 | yes |
| held_out: Brier B1 | 0.04771623018 | 0.04771623018 | 0.00e+00 | 1e-09 | yes |
| held_out: AP B2 | 0.2140735561 | 0.2140735561 | 0.00e+00 | 1e-09 | yes |
| held_out: Brier B2 | 0.04771740242 | 0.04771740242 | 0.00e+00 | 1e-09 | yes |
| held_out: AP B3 | 0.2830580169 | 0.2830580169 | 5.55e-17 | 1e-09 | yes |
| held_out: Brier B3 | 0.04252934838 | 0.04252934838 | 0.00e+00 | 1e-09 | yes |
| held_out: AP B4 | 0.5485495818 | 0.5485495818 | 0.00e+00 | 1e-09 | yes |
| held_out: Brier B4 | 0.03374876856 | 0.03374876856 | 0.00e+00 | 1e-09 | yes |
| held_out: AP B5_A2 | 0.5814877981 | 0.5814877981 | 0.00e+00 | 1e-09 | yes |
| held_out: Brier B5_A2 | 0.03450496923 | 0.03450496923 | 0.00e+00 | 1e-09 | yes |
| held_out: AP M_A2 | 0.6725168153 | 0.6725168153 | 0.00e+00 | 1e-09 | yes |
| held_out: Brier M_A2 | 0.03162658269 | 0.03162658269 | 0.00e+00 | 1e-09 | yes |
| all: improvement | 0.1602653146 | 0.1602653146 | 2.22e-16 | 1e-09 | yes |
| test: improvement | 0.1437095414 | 0.1437095414 | 2.22e-16 | 1e-09 | yes |
| held_out: improvement | 0.1565450168 | 0.1565450168 | 0.00e+00 | 1e-09 | yes |
| weighted AP routine, draw 0, M_A2 | 0.5029674171 | 0.5029674171 | 0.00e+00 | 1e-09 | yes |
| weighted AP routine, draw 0, B5_A2 | 0.4413064894 | 0.4413064894 | 5.55e-17 | 1e-09 | yes |
| weighted AP routine, draw 1, M_A2 | 0.4735039275 | 0.4735039275 | 0.00e+00 | 1e-09 | yes |
| weighted AP routine, draw 1, B5_A2 | 0.4001465842 | 0.4001465842 | 5.55e-17 | 1e-09 | yes |
| weighted AP routine, draw 2, M_A2 | 0.4874057035 | 0.4874057035 | 0.00e+00 | 1e-09 | yes |
| weighted AP routine, draw 2, B5_A2 | 0.4103119573 | 0.4103119573 | 5.55e-17 | 1e-09 | yes |
| all: improvement interval, low | 0.1066479473 | 0.1066479473 | 4.30e-16 | 1e-09 | yes |
| all: improvement interval, high | 0.2228725128 | 0.2228725128 | 0.00e+00 | 1e-09 | yes |
| all: AP interval M_A2, low | 0.4222151257 | 0.4222151257 | 5.55e-17 | 1e-09 | yes |
| all: AP interval M_A2, high | 0.5147944978 | 0.5147944978 | 0.00e+00 | 1e-09 | yes |
| all: AP interval B5_A2, low | 0.3511805784 | 0.3511805784 | 0.00e+00 | 1e-09 | yes |
| all: AP interval B5_A2, high | 0.4555759651 | 0.4555759651 | 0.00e+00 | 1e-09 | yes |
| win | 0 | 0 | 0.00e+00 | 0 | yes |
