# Final run: PR targets (test split)

| condition | targets | fixed on mutants | damage on clean | regressions | claims prop/prov/valid/unconf | precision | $/target | total $ |
|---|---|---|---|---|---|---|---|---|
| pr_R | 48 | 0/36 (0%) | 0/12 (0%) | 0 | 0/0/0/0 | n/a | $0.0000 | $0.0000 |
| pr_C | 48 | 36/36 (100%) | 0/12 (0%) | 0 | 0/0/0/0 | n/a | $0.0069 | $0.3319 |
| pr_E | 24 | 17/18 (94%) | 0/6 (0%) | 0 | 0/0/0/0 | n/a | $0.1957 | $4.6966 |
| pr_D | 24 | 17/18 (94%) | 0/6 (0%) | 2 | 73/72/20/52 | 0.28 | $0.3115 | $7.4762 |
| pr_B | 6 | regen 6/6 | n/a | 0 | 0/0/0/0 | n/a | $0.3390 | $2.0340 |

## pr_R

| task | target | before | after | fixed | regressions | damaged | usd | reviewer usd | status |
|---|---|---|---|---|---|---|---|---|---|
| pr_test_1 | clean | 58/58 | 58/58 | True | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_1 | clean | 58/58 | 58/58 | True | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_1 | buggy_a | 57/58 | 57/58 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_1 | buggy_a | 57/58 | 57/58 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_1 | buggy_b | 57/58 | 57/58 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_1 | buggy_b | 57/58 | 57/58 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_1 | buggy_c | 57/58 | 57/58 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_1 | buggy_c | 57/58 | 57/58 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_2 | clean | 53/53 | 53/53 | True | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_2 | clean | 53/53 | 53/53 | True | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_2 | buggy_a | 52/53 | 52/53 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_2 | buggy_a | 52/53 | 52/53 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_2 | buggy_b | 51/53 | 51/53 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_2 | buggy_b | 51/53 | 51/53 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_2 | buggy_c | 52/53 | 52/53 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_2 | buggy_c | 52/53 | 52/53 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_3 | clean | 58/58 | 58/58 | True | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_3 | clean | 58/58 | 58/58 | True | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_3 | buggy_a | 57/58 | 57/58 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_3 | buggy_a | 57/58 | 57/58 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_3 | buggy_b | 57/58 | 57/58 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_3 | buggy_b | 57/58 | 57/58 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_3 | buggy_c | 57/58 | 57/58 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_3 | buggy_c | 57/58 | 57/58 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_4 | clean | 55/55 | 55/55 | True | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_4 | clean | 55/55 | 55/55 | True | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_4 | buggy_a | 54/55 | 54/55 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_4 | buggy_a | 54/55 | 54/55 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_4 | buggy_b | 54/55 | 54/55 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_4 | buggy_b | 54/55 | 54/55 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_4 | buggy_c | 52/55 | 52/55 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_4 | buggy_c | 52/55 | 52/55 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_5 | clean | 52/52 | 52/52 | True | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_5 | clean | 52/52 | 52/52 | True | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_5 | buggy_a | 50/52 | 50/52 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_5 | buggy_a | 50/52 | 50/52 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_5 | buggy_b | 51/52 | 51/52 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_5 | buggy_b | 51/52 | 51/52 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_5 | buggy_c | 51/52 | 51/52 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_5 | buggy_c | 51/52 | 51/52 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_6 | clean | 56/56 | 56/56 | True | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_6 | clean | 56/56 | 56/56 | True | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_6 | buggy_a | 55/56 | 55/56 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_6 | buggy_a | 55/56 | 55/56 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_6 | buggy_b | 55/56 | 55/56 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_6 | buggy_b | 55/56 | 55/56 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_6 | buggy_c | 55/56 | 55/56 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |
| pr_test_6 | buggy_c | 55/56 | 55/56 | False | 0 | False | $0.0000 | $0.0000 | UNREVIEWED |

## pr_C

| task | target | before | after | fixed | regressions | damaged | usd | reviewer usd | status |
|---|---|---|---|---|---|---|---|---|---|
| pr_test_1 | clean | 58/58 | 58/58 | True | 0 | False | $0.0072 | $0.0000 | VERIFIED |
| pr_test_1 | clean | 58/58 | 58/58 | True | 0 | False | $0.0026 | $0.0000 | VERIFIED |
| pr_test_1 | buggy_a | 57/58 | 58/58 | True | 0 | False | $0.0096 | $0.0000 | VERIFIED |
| pr_test_1 | buggy_a | 57/58 | 58/58 | True | 0 | False | $0.0094 | $0.0000 | VERIFIED |
| pr_test_1 | buggy_b | 57/58 | 58/58 | True | 0 | False | $0.0083 | $0.0000 | VERIFIED |
| pr_test_1 | buggy_b | 57/58 | 58/58 | True | 0 | False | $0.0072 | $0.0000 | VERIFIED |
| pr_test_1 | buggy_c | 57/58 | 58/58 | True | 0 | False | $0.0087 | $0.0000 | VERIFIED |
| pr_test_1 | buggy_c | 57/58 | 58/58 | True | 0 | False | $0.0090 | $0.0000 | VERIFIED |
| pr_test_2 | clean | 53/53 | 53/53 | True | 0 | False | $0.0075 | $0.0000 | VERIFIED |
| pr_test_2 | clean | 53/53 | 53/53 | True | 0 | False | $0.0023 | $0.0000 | VERIFIED |
| pr_test_2 | buggy_a | 52/53 | 53/53 | True | 0 | False | $0.0066 | $0.0000 | VERIFIED |
| pr_test_2 | buggy_a | 52/53 | 53/53 | True | 0 | False | $0.0070 | $0.0000 | VERIFIED |
| pr_test_2 | buggy_b | 51/53 | 53/53 | True | 0 | False | $0.0074 | $0.0000 | VERIFIED |
| pr_test_2 | buggy_b | 51/53 | 53/53 | True | 0 | False | $0.0087 | $0.0000 | VERIFIED |
| pr_test_2 | buggy_c | 52/53 | 53/53 | True | 0 | False | $0.0076 | $0.0000 | VERIFIED |
| pr_test_2 | buggy_c | 52/53 | 53/53 | True | 0 | False | $0.0072 | $0.0000 | VERIFIED |
| pr_test_3 | clean | 58/58 | 58/58 | True | 0 | False | $0.0087 | $0.0000 | VERIFIED |
| pr_test_3 | clean | 58/58 | 58/58 | True | 0 | False | $0.0020 | $0.0000 | VERIFIED |
| pr_test_3 | buggy_a | 57/58 | 58/58 | True | 0 | False | $0.0065 | $0.0000 | VERIFIED |
| pr_test_3 | buggy_a | 57/58 | 58/58 | True | 0 | False | $0.0085 | $0.0000 | VERIFIED |
| pr_test_3 | buggy_b | 57/58 | 58/58 | True | 0 | False | $0.0102 | $0.0000 | VERIFIED |
| pr_test_3 | buggy_b | 57/58 | 58/58 | True | 0 | False | $0.0070 | $0.0000 | VERIFIED |
| pr_test_3 | buggy_c | 57/58 | 58/58 | True | 0 | False | $0.0072 | $0.0000 | VERIFIED |
| pr_test_3 | buggy_c | 57/58 | 58/58 | True | 0 | False | $0.0111 | $0.0000 | VERIFIED |
| pr_test_4 | clean | 55/55 | 55/55 | True | 0 | False | $0.0021 | $0.0000 | VERIFIED |
| pr_test_4 | clean | 55/55 | 55/55 | True | 0 | False | $0.0017 | $0.0000 | VERIFIED |
| pr_test_4 | buggy_a | 54/55 | 55/55 | True | 0 | False | $0.0056 | $0.0000 | VERIFIED |
| pr_test_4 | buggy_a | 54/55 | 55/55 | True | 0 | False | $0.0075 | $0.0000 | VERIFIED |
| pr_test_4 | buggy_b | 54/55 | 55/55 | True | 0 | False | $0.0063 | $0.0000 | VERIFIED |
| pr_test_4 | buggy_b | 54/55 | 55/55 | True | 0 | False | $0.0060 | $0.0000 | VERIFIED |
| pr_test_4 | buggy_c | 52/55 | 55/55 | True | 0 | False | $0.0077 | $0.0000 | VERIFIED |
| pr_test_4 | buggy_c | 52/55 | 55/55 | True | 0 | False | $0.0053 | $0.0000 | VERIFIED |
| pr_test_5 | clean | 52/52 | 52/52 | True | 0 | False | $0.0022 | $0.0000 | VERIFIED |
| pr_test_5 | clean | 52/52 | 52/52 | True | 0 | False | $0.0029 | $0.0000 | VERIFIED |
| pr_test_5 | buggy_a | 50/52 | 52/52 | True | 0 | False | $0.0089 | $0.0000 | VERIFIED |
| pr_test_5 | buggy_a | 50/52 | 52/52 | True | 0 | False | $0.0057 | $0.0000 | VERIFIED |
| pr_test_5 | buggy_b | 51/52 | 52/52 | True | 0 | False | $0.0059 | $0.0000 | VERIFIED |
| pr_test_5 | buggy_b | 51/52 | 52/52 | True | 0 | False | $0.0058 | $0.0000 | VERIFIED |
| pr_test_5 | buggy_c | 51/52 | 52/52 | True | 0 | False | $0.0092 | $0.0000 | VERIFIED |
| pr_test_5 | buggy_c | 51/52 | 52/52 | True | 0 | False | $0.0055 | $0.0000 | VERIFIED |
| pr_test_6 | clean | 56/56 | 56/56 | True | 0 | False | $0.0032 | $0.0000 | VERIFIED |
| pr_test_6 | clean | 56/56 | 56/56 | True | 0 | False | $0.0081 | $0.0000 | VERIFIED |
| pr_test_6 | buggy_a | 55/56 | 56/56 | True | 0 | False | $0.0111 | $0.0000 | VERIFIED |
| pr_test_6 | buggy_a | 55/56 | 56/56 | True | 0 | False | $0.0082 | $0.0000 | VERIFIED |
| pr_test_6 | buggy_b | 55/56 | 56/56 | True | 0 | False | $0.0075 | $0.0000 | VERIFIED |
| pr_test_6 | buggy_b | 55/56 | 56/56 | True | 0 | False | $0.0089 | $0.0000 | VERIFIED |
| pr_test_6 | buggy_c | 55/56 | 56/56 | True | 0 | False | $0.0108 | $0.0000 | VERIFIED |
| pr_test_6 | buggy_c | 55/56 | 56/56 | True | 0 | False | $0.0085 | $0.0000 | VERIFIED |

## pr_E

| task | target | before | after | fixed | regressions | damaged | usd | reviewer usd | status |
|---|---|---|---|---|---|---|---|---|---|
| pr_test_1 | clean | 58/58 | 58/58 | True | 0 | False | $0.1707 | $0.1684 | VERIFIED |
| pr_test_1 | buggy_a | 57/58 | 58/58 | True | 0 | False | $0.1912 | $0.1872 | VERIFIED |
| pr_test_1 | buggy_b | 57/58 | 58/58 | True | 0 | False | $0.2505 | $0.2470 | VERIFIED |
| pr_test_1 | buggy_c | 57/58 | 58/58 | True | 0 | False | $0.2207 | $0.2163 | VERIFIED |
| pr_test_2 | clean | 53/53 | 53/53 | True | 0 | False | $0.3895 | $0.3850 | VERIFIED |
| pr_test_2 | buggy_a | 52/53 | 53/53 | True | 0 | False | $0.1925 | $0.1912 | VERIFIED |
| pr_test_2 | buggy_b | 51/53 | 53/53 | True | 0 | False | $0.2240 | $0.2221 | VERIFIED |
| pr_test_2 | buggy_c | 52/53 | 53/53 | True | 0 | False | $0.1759 | $0.1746 | VERIFIED |
| pr_test_3 | clean | 58/58 | 58/58 | True | 0 | False | $0.1969 | $0.1949 | VERIFIED |
| pr_test_3 | buggy_a | 57/58 | 58/58 | True | 0 | False | $0.1928 | $0.1913 | VERIFIED |
| pr_test_3 | buggy_b | 57/58 | 57/58 | False | 0 | False | $0.0898 | $0.0882 | VERIFIED |
| pr_test_3 | buggy_c | 57/58 | 58/58 | True | 0 | False | $0.2267 | $0.2250 | VERIFIED |
| pr_test_4 | clean | 55/55 | 55/55 | True | 0 | False | $0.0918 | $0.0918 | VERIFIED |
| pr_test_4 | buggy_a | 54/55 | 55/55 | True | 0 | False | $0.2104 | $0.2091 | VERIFIED |
| pr_test_4 | buggy_b | 54/55 | 55/55 | True | 0 | False | $0.1469 | $0.1459 | VERIFIED |
| pr_test_4 | buggy_c | 52/55 | 55/55 | True | 0 | False | $0.1701 | $0.1687 | VERIFIED |
| pr_test_5 | clean | 52/52 | 52/52 | True | 0 | False | $0.1116 | $0.1098 | VERIFIED |
| pr_test_5 | buggy_a | 50/52 | 52/52 | True | 0 | False | $0.1326 | $0.1316 | VERIFIED |
| pr_test_5 | buggy_b | 51/52 | 52/52 | True | 0 | False | $0.1115 | $0.1101 | VERIFIED |
| pr_test_5 | buggy_c | 51/52 | 52/52 | True | 0 | False | $0.1336 | $0.1323 | VERIFIED |
| pr_test_6 | clean | 56/56 | 56/56 | True | 0 | False | $0.2358 | $0.2344 | VERIFIED |
| pr_test_6 | buggy_a | 55/56 | 56/56 | True | 0 | False | $0.2467 | $0.2441 | VERIFIED |
| pr_test_6 | buggy_b | 55/56 | 56/56 | True | 0 | False | $0.2928 | $0.2880 | VERIFIED |
| pr_test_6 | buggy_c | 55/56 | 56/56 | True | 0 | False | $0.2918 | $0.2886 | VERIFIED |

## pr_D

| task | target | before | after | fixed | regressions | damaged | usd | reviewer usd | status |
|---|---|---|---|---|---|---|---|---|---|
| pr_test_1 | clean | 58/58 | 58/58 | True | 0 | False | $0.3712 | $0.3670 | PARTIAL |
| pr_test_1 | buggy_a | 57/58 | 58/58 | True | 0 | False | $0.3071 | $0.3024 | VERIFIED |
| pr_test_1 | buggy_b | 57/58 | 58/58 | True | 0 | False | $0.4314 | $0.4271 | VERIFIED |
| pr_test_1 | buggy_c | 57/58 | 58/58 | True | 0 | False | $0.3511 | $0.3481 | VERIFIED |
| pr_test_2 | clean | 53/53 | 53/53 | True | 0 | False | $0.3917 | $0.3883 | PARTIAL |
| pr_test_2 | buggy_a | 52/53 | 53/53 | True | 0 | False | $0.3070 | $0.3041 | VERIFIED |
| pr_test_2 | buggy_b | 51/53 | 53/53 | True | 0 | False | $0.2597 | $0.2579 | VERIFIED |
| pr_test_2 | buggy_c | 52/53 | 53/53 | True | 0 | False | $0.3628 | $0.3599 | VERIFIED |
| pr_test_3 | clean | 58/58 | 58/58 | True | 0 | False | $0.4218 | $0.4185 | VERIFIED |
| pr_test_3 | buggy_a | 57/58 | 58/58 | True | 0 | False | $0.2878 | $0.2847 | VERIFIED |
| pr_test_3 | buggy_b | 57/58 | 56/58 | False | 2 | False | $0.2764 | $0.2734 | FAILED |
| pr_test_3 | buggy_c | 57/58 | 58/58 | True | 0 | False | $0.2662 | $0.2633 | VERIFIED |
| pr_test_4 | clean | 55/55 | 55/55 | True | 0 | False | $0.3196 | $0.3153 | VERIFIED |
| pr_test_4 | buggy_a | 54/55 | 55/55 | True | 0 | False | $0.2157 | $0.2134 | VERIFIED |
| pr_test_4 | buggy_b | 54/55 | 55/55 | True | 0 | False | $0.2376 | $0.2348 | VERIFIED |
| pr_test_4 | buggy_c | 52/55 | 55/55 | True | 0 | False | $0.2605 | $0.2580 | VERIFIED |
| pr_test_5 | clean | 52/52 | 52/52 | True | 0 | False | $0.1488 | $0.1488 | VERIFIED |
| pr_test_5 | buggy_a | 50/52 | 52/52 | True | 0 | False | $0.3416 | $0.3389 | PARTIAL |
| pr_test_5 | buggy_b | 51/52 | 52/52 | True | 0 | False | $0.2426 | $0.2400 | VERIFIED |
| pr_test_5 | buggy_c | 51/52 | 52/52 | True | 0 | False | $0.2136 | $0.2111 | VERIFIED |
| pr_test_6 | clean | 56/56 | 56/56 | True | 0 | False | $0.3219 | $0.3203 | VERIFIED |
| pr_test_6 | buggy_a | 55/56 | 56/56 | True | 0 | False | $0.3590 | $0.3550 | VERIFIED |
| pr_test_6 | buggy_b | 55/56 | 56/56 | True | 0 | False | $0.3765 | $0.3734 | VERIFIED |
| pr_test_6 | buggy_c | 55/56 | 56/56 | True | 0 | False | $0.4046 | $0.4011 | VERIFIED |

## pr_B

| task | target | before | after | fixed | regressions | damaged | usd | reviewer usd | status |
|---|---|---|---|---|---|---|---|---|---|
| pr_test_1 | regen | 58/58 | 58/58 | True | 0 | False | $0.2947 | $0.0000 | VERIFIED |
| pr_test_2 | regen | 53/53 | 53/53 | True | 0 | False | $0.3879 | $0.0000 | VERIFIED |
| pr_test_3 | regen | 58/58 | 58/58 | True | 0 | False | $0.3086 | $0.0000 | VERIFIED |
| pr_test_4 | regen | 55/55 | 55/55 | True | 0 | False | $0.2935 | $0.0000 | VERIFIED |
| pr_test_5 | regen | 52/52 | 52/52 | True | 0 | False | $0.2580 | $0.0000 | VERIFIED |
| pr_test_6 | regen | 56/56 | 56/56 | True | 0 | False | $0.4913 | $0.0000 | VERIFIED |
