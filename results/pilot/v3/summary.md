# Pilot v3 summary (dev PR targets, 1 seed)

| condition | targets | fixed on mutants | damage on clean | regressions | claims prop/prov/valid/unconf | precision | $/target | total $ |
|---|---|---|---|---|---|---|---|---|
| condR | 12 | 0/9 (0%) | 0/3 (0%) | 0 | 0/0/0/0 | n/a | $0.0000 | $0.0000 |
| condC | 12 | 9/9 (100%) | 0/3 (0%) | 0 | 0/0/0/0 | n/a | $0.0085 | $0.1025 |
| condE | 12 | 9/9 (100%) | 0/3 (0%) | 0 | 0/0/0/0 | n/a | $0.1570 | $1.8846 |
| condD | 7 | 5/5 (100%) | 0/2 (0%) | 0 | 19/18/5/13 | 0.28 | $0.3189 | $2.2321 |

## condR

| task | target | before | after | fixed | regressions | damaged | usd | reviewer usd | status |
|---|---|---|---|---|---|---|---|---|---|
| pr_dev_1 | clean | 56/56 | 56/56 | True | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_dev_1 | buggy_a | 55/56 | 55/56 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_dev_1 | buggy_b | 54/56 | 54/56 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_dev_1 | buggy_c | 55/56 | 55/56 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_dev_2 | clean | 56/56 | 56/56 | True | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_dev_2 | buggy_a | 55/56 | 55/56 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_dev_2 | buggy_b | 54/56 | 54/56 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_dev_2 | buggy_c | 55/56 | 55/56 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_dev_3 | clean | 57/57 | 57/57 | True | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_dev_3 | buggy_a | 56/57 | 56/57 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_dev_3 | buggy_b | 56/57 | 56/57 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_dev_3 | buggy_c | 56/57 | 56/57 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |

## condC

| task | target | before | after | fixed | regressions | damaged | usd | reviewer usd | status |
|---|---|---|---|---|---|---|---|---|---|
| pr_dev_1 | clean | 56/56 | 56/56 | True | 0 | False | $0.0067 | $0.0000 | VERIFIED |
| pr_dev_1 | buggy_a | 55/56 | 56/56 | True | 0 | False | $0.0062 | $0.0000 | VERIFIED |
| pr_dev_1 | buggy_b | 54/56 | 56/56 | True | 0 | False | $0.0064 | $0.0000 | VERIFIED |
| pr_dev_1 | buggy_c | 55/56 | 56/56 | True | 0 | False | $0.0056 | $0.0000 | VERIFIED |
| pr_dev_2 | clean | 56/56 | 56/56 | True | 0 | False | $0.0120 | $0.0000 | VERIFIED |
| pr_dev_2 | buggy_a | 55/56 | 56/56 | True | 0 | False | $0.0126 | $0.0000 | VERIFIED |
| pr_dev_2 | buggy_b | 54/56 | 56/56 | True | 0 | False | $0.0094 | $0.0000 | VERIFIED |
| pr_dev_2 | buggy_c | 55/56 | 56/56 | True | 0 | False | $0.0130 | $0.0000 | VERIFIED |
| pr_dev_3 | clean | 57/57 | 57/57 | True | 0 | False | $0.0032 | $0.0000 | VERIFIED |
| pr_dev_3 | buggy_a | 56/57 | 57/57 | True | 0 | False | $0.0091 | $0.0000 | VERIFIED |
| pr_dev_3 | buggy_b | 56/57 | 57/57 | True | 0 | False | $0.0092 | $0.0000 | VERIFIED |
| pr_dev_3 | buggy_c | 56/57 | 57/57 | True | 0 | False | $0.0090 | $0.0000 | VERIFIED |

## condE

| task | target | before | after | fixed | regressions | damaged | usd | reviewer usd | status |
|---|---|---|---|---|---|---|---|---|---|
| pr_dev_1 | clean | 56/56 | 56/56 | True | 0 | False | $0.0431 | $0.0431 | VERIFIED |
| pr_dev_1 | buggy_a | 55/56 | 56/56 | True | 0 | False | $0.1124 | $0.1113 | VERIFIED |
| pr_dev_1 | buggy_b | 54/56 | 56/56 | True | 0 | False | $0.0849 | $0.0837 | VERIFIED |
| pr_dev_1 | buggy_c | 55/56 | 56/56 | True | 0 | False | $0.1079 | $0.1067 | VERIFIED |
| pr_dev_2 | clean | 56/56 | 56/56 | True | 0 | False | $0.1360 | $0.1360 | VERIFIED |
| pr_dev_2 | buggy_a | 55/56 | 56/56 | True | 0 | False | $0.2327 | $0.2289 | VERIFIED |
| pr_dev_2 | buggy_b | 54/56 | 56/56 | True | 0 | False | $0.2198 | $0.2179 | VERIFIED |
| pr_dev_2 | buggy_c | 55/56 | 56/56 | True | 0 | False | $0.2064 | $0.2043 | VERIFIED |
| pr_dev_3 | clean | 57/57 | 57/57 | True | 0 | False | $0.1005 | $0.1005 | VERIFIED |
| pr_dev_3 | buggy_a | 56/57 | 57/57 | True | 0 | False | $0.1888 | $0.1878 | VERIFIED |
| pr_dev_3 | buggy_b | 56/57 | 57/57 | True | 0 | False | $0.2205 | $0.2152 | VERIFIED |
| pr_dev_3 | buggy_c | 56/57 | 57/57 | True | 0 | False | $0.2316 | $0.2291 | VERIFIED |

## condD

| task | target | before | after | fixed | regressions | damaged | usd | reviewer usd | status |
|---|---|---|---|---|---|---|---|---|---|
| pr_dev_1 | clean | 56/56 | 56/56 | True | 0 | False | $0.2652 | $0.2639 | VERIFIED |
| pr_dev_1 | buggy_a | 55/56 | 56/56 | True | 0 | False | $0.2253 | $0.2231 | VERIFIED |
| pr_dev_1 | buggy_b | 54/56 | 56/56 | True | 0 | False | $0.1881 | $0.1860 | VERIFIED |
| pr_dev_1 | buggy_c | 55/56 | 56/56 | True | 0 | False | $0.2655 | $0.2630 | VERIFIED |
| pr_dev_3 | clean | 57/57 | 57/57 | True | 0 | False | $0.5928 | $0.5900 | PARTIAL |
| pr_dev_3 | buggy_a | 56/57 | 57/57 | True | 0 | False | $0.3056 | $0.3014 | VERIFIED |
| pr_dev_2 | buggy_a | 55/56 | 56/56 | True | 0 | False | $0.3895 | $0.3877 | PARTIAL |

## Notes

- Coverage: R, C and E ran all 12 dev PR targets (3 PRs x 3 buggy + 1 clean).
  D ran 7 of 12 (all of pr_dev_1, clean + buggy_a of pr_dev_3, buggy_a of
  pr_dev_2) before the session live-spend cap of $6 stopped it; the missing
  D targets are pr_dev_2 clean/buggy_b/buggy_c and pr_dev_3 buggy_b/buggy_c.
  Session live spend was $5.8784 in total, of which about $1.66 was wasted
  on an aborted E run at the wrong effort and its polluted rerun (see the
  effort note below); the rows above are the clean reruns.
- Condition D claims (7 targets): proposed 19, PROVEN 18, UNPROVEN discarded
  1, INVALID 0, UNCONFIRMED 13 (of the proven), VALID 5. Claim precision
  (VALID/PROVEN) is 0.28. The reviser contested 0 of the 13 UNCONFIRMED
  claims and accepted 13 of 13; two D targets end PARTIAL because accepted
  UNCONFIRMED claim tests still fail on code that passes every hidden test.
- Effort note: v3 caught a bug where `--reviewer-effort` never reached the
  reviewer call, so the reviewer ran at effort high regardless. The ledger
  shows the same bug affected pilot v2: its rows labelled D (medium) and
  E (medium) also record reviewer effort high, so v2's high-vs-medium
  comparison is not an effort comparison. Fixed in the loop (the reviewer
  effort in settings is now passed to every reviewer call) with a
  mocked-LLM test; all v3 E and D rows above record reviewer effort
  medium in the ledger.
- Reading: on PR packages every reviewing condition again fixed every
  buggy target it ran on, with zero damage and zero regressions. What
  separates them is cost and, for D, claim quality: C $0.0085/target,
  E $0.1570/target, D $0.3189/target, and D's precision fell to 0.28 on
  the larger packages (13 of 18 proven claims UNCONFIRMED, none contested).
