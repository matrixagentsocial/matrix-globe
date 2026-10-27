# Final open-weights run (test split, 1 seed, Baseten)

Model: `meta-models/muse-spark-open-1026` (provider: baseten) for every role. Reviewer effort: medium. Prices: $1.25 input / $0.15 cached / $4.25 output per 1M tokens.

## PR targets (6 test PRs x 3 buggy + 1 clean = 24)

| condition | provider | targets | fixed on mutants | damage on clean | regressions | claims prop/prov/valid/unconf | precision | $/target | total $ |
|---|---|---|---|---|---|---|---|---|---|
| C_open | baseten | 24 | 17/18 (94%) | 0/6 (0%) | 0 | 0/0/0/0 | n/a | $0.1246 | $2.9895 |
| E_open | baseten | 24 | 12/18 (67%) | 0/6 (0%) | 0 | 0/0/0/0 | n/a | $0.1425 | $3.4194 |
| D_open | baseten | 24 | 17/18 (94%) | 0/6 (0%) | 0 | 55/50/20/30 | 0.40 | $0.0858 | $2.0602 |

## Single-task targets (20 test tasks x 3 mutants + 1 clean = 80)

| condition | provider | targets | fixed on mutants | damage on clean | regressions | claims prop/prov/valid/unconf | precision | $/target | total $ |
|---|---|---|---|---|---|---|---|---|---|
| C_open | baseten | 80 | 54/60 (90%) | 0/20 (0%) | 0 | 0/0/0/0 | n/a | $0.0708 | $5.6667 |
| E_open | baseten | 80 | 41/60 (68%) | 0/20 (0%) | 0 | 0/0/0/0 | n/a | $0.0272 | $2.1789 |
| D_open | baseten | 80 | 57/60 (95%) | 0/20 (0%) | 0 | 136/130/83/47 | 0.64 | $0.0634 | $5.0685 |

Total Baseten spend recorded for this run: $21.3831.

## pr C_open

| task | target | before | after | fixed | regressions | damaged | usd | reviewer usd | status |
|---|---|---|---|---|---|---|---|---|---|
| pr_test_1 | clean | 58/58 | 58/58 | True | 0 | False | $0.1387 | $0.0000 | VERIFIED |
| pr_test_1 | buggy_a | 57/58 | 58/58 | True | 0 | False | $0.1434 | $0.0000 | VERIFIED |
| pr_test_1 | buggy_b | 57/58 | 57/58 | False | 0 | False | $0.0660 | $0.0000 | VERIFIED |
| pr_test_1 | buggy_c | 57/58 | 58/58 | True | 0 | False | $0.1359 | $0.0000 | VERIFIED |
| pr_test_2 | clean | 53/53 | 53/53 | True | 0 | False | $0.1354 | $0.0000 | VERIFIED |
| pr_test_2 | buggy_a | 52/53 | 53/53 | True | 0 | False | $0.1310 | $0.0000 | VERIFIED |
| pr_test_2 | buggy_b | 51/53 | 53/53 | True | 0 | False | $0.0970 | $0.0000 | VERIFIED |
| pr_test_2 | buggy_c | 52/53 | 53/53 | True | 0 | False | $0.1093 | $0.0000 | VERIFIED |
| pr_test_3 | clean | 58/58 | 58/58 | True | 0 | False | $0.1458 | $0.0000 | VERIFIED |
| pr_test_3 | buggy_a | 57/58 | 58/58 | True | 0 | False | $0.1255 | $0.0000 | VERIFIED |
| pr_test_3 | buggy_b | 57/58 | 58/58 | True | 0 | False | $0.1291 | $0.0000 | VERIFIED |
| pr_test_3 | buggy_c | 57/58 | 58/58 | True | 0 | False | $0.1222 | $0.0000 | VERIFIED |
| pr_test_4 | clean | 55/55 | 55/55 | True | 0 | False | $0.1215 | $0.0000 | VERIFIED |
| pr_test_4 | buggy_a | 54/55 | 55/55 | True | 0 | False | $0.1163 | $0.0000 | VERIFIED |
| pr_test_4 | buggy_b | 54/55 | 55/55 | True | 0 | False | $0.1449 | $0.0000 | VERIFIED |
| pr_test_4 | buggy_c | 52/55 | 55/55 | True | 0 | False | $0.1208 | $0.0000 | VERIFIED |
| pr_test_5 | clean | 52/52 | 52/52 | True | 0 | False | $0.1210 | $0.0000 | VERIFIED |
| pr_test_5 | buggy_a | 50/52 | 52/52 | True | 0 | False | $0.1086 | $0.0000 | VERIFIED |
| pr_test_5 | buggy_b | 51/52 | 52/52 | True | 0 | False | $0.1167 | $0.0000 | VERIFIED |
| pr_test_5 | buggy_c | 51/52 | 52/52 | True | 0 | False | $0.1192 | $0.0000 | VERIFIED |
| pr_test_6 | clean | 56/56 | 56/56 | True | 0 | False | $0.1354 | $0.0000 | VERIFIED |
| pr_test_6 | buggy_a | 55/56 | 56/56 | True | 0 | False | $0.1524 | $0.0000 | VERIFIED |
| pr_test_6 | buggy_b | 55/56 | 56/56 | True | 0 | False | $0.1295 | $0.0000 | VERIFIED |
| pr_test_6 | buggy_c | 55/56 | 56/56 | True | 0 | False | $0.1242 | $0.0000 | VERIFIED |

## pr E_open

| task | target | before | after | fixed | regressions | damaged | usd | reviewer usd | status |
|---|---|---|---|---|---|---|---|---|---|
| pr_test_1 | clean | 58/58 | 58/58 | True | 0 | False | $0.3503 | $0.0256 | VERIFIED |
| pr_test_1 | buggy_a | 57/58 | 58/58 | True | 0 | False | $0.0794 | $0.0422 | VERIFIED |
| pr_test_1 | buggy_b | 57/58 | 58/58 | True | 0 | False | $0.0684 | $0.0512 | VERIFIED |
| pr_test_1 | buggy_c | 57/58 | 58/58 | True | 0 | False | $0.3674 | $0.0319 | VERIFIED |
| pr_test_2 | clean | 53/53 | 53/53 | True | 0 | False | $0.0259 | $0.0259 | VERIFIED |
| pr_test_2 | buggy_a | 52/53 | 52/53 | False | 0 | False | $0.3459 | $0.0189 | VERIFIED |
| pr_test_2 | buggy_b | 51/53 | 51/53 | False | 0 | False | $0.3486 | $0.0272 | VERIFIED |
| pr_test_2 | buggy_c | 52/53 | 53/53 | True | 0 | False | $0.0746 | $0.0354 | VERIFIED |
| pr_test_3 | clean | 58/58 | 58/58 | True | 0 | False | $0.0283 | $0.0283 | VERIFIED |
| pr_test_3 | buggy_a | 57/58 | 57/58 | False | 0 | False | $0.3495 | $0.0229 | VERIFIED |
| pr_test_3 | buggy_b | 57/58 | 58/58 | True | 0 | False | $0.0836 | $0.0594 | VERIFIED |
| pr_test_3 | buggy_c | 57/58 | 57/58 | False | 0 | False | $0.0479 | $0.0245 | VERIFIED |
| pr_test_4 | clean | 55/55 | 55/55 | True | 0 | False | $0.0567 | $0.0390 | VERIFIED |
| pr_test_4 | buggy_a | 54/55 | 55/55 | True | 0 | False | $0.0677 | $0.0396 | VERIFIED |
| pr_test_4 | buggy_b | 54/55 | 55/55 | True | 0 | False | $0.0537 | $0.0389 | VERIFIED |
| pr_test_4 | buggy_c | 52/55 | 55/55 | True | 0 | False | $0.3756 | $0.0411 | VERIFIED |
| pr_test_5 | clean | 52/52 | 52/52 | True | 0 | False | $0.0267 | $0.0267 | VERIFIED |
| pr_test_5 | buggy_a | 50/52 | 52/52 | True | 0 | False | $0.0495 | $0.0306 | VERIFIED |
| pr_test_5 | buggy_b | 51/52 | 52/52 | True | 0 | False | $0.0412 | $0.0271 | VERIFIED |
| pr_test_5 | buggy_c | 51/52 | 52/52 | True | 0 | False | $0.0645 | $0.0371 | VERIFIED |
| pr_test_6 | clean | 56/56 | 56/56 | True | 0 | False | $0.0483 | $0.0258 | VERIFIED |
| pr_test_6 | buggy_a | 55/56 | 56/56 | True | 0 | False | $0.0673 | $0.0461 | VERIFIED |
| pr_test_6 | buggy_b | 55/56 | 55/56 | False | 0 | False | $0.0464 | $0.0297 | VERIFIED |
| pr_test_6 | buggy_c | 55/56 | 55/56 | False | 0 | False | $0.3520 | $0.0309 | VERIFIED |

## pr D_open

| task | target | before | after | fixed | regressions | damaged | usd | reviewer usd | status |
|---|---|---|---|---|---|---|---|---|---|
| pr_test_1 | clean | 58/58 | 58/58 | True | 0 | False | $0.0200 | $0.0200 | VERIFIED |
| pr_test_1 | buggy_a | 57/58 | 58/58 | True | 0 | False | $0.0926 | $0.0722 | VERIFIED |
| pr_test_1 | buggy_b | 57/58 | 58/58 | True | 0 | False | $0.1149 | $0.0757 | VERIFIED |
| pr_test_1 | buggy_c | 57/58 | 58/58 | True | 0 | False | $0.0991 | $0.0812 | PARTIAL |
| pr_test_2 | clean | 53/53 | 53/53 | True | 0 | False | $0.0941 | $0.0719 | VERIFIED |
| pr_test_2 | buggy_a | 52/53 | 53/53 | True | 0 | False | $0.0895 | $0.0652 | VERIFIED |
| pr_test_2 | buggy_b | 51/53 | 53/53 | True | 0 | False | $0.1129 | $0.0708 | VERIFIED |
| pr_test_2 | buggy_c | 52/53 | 53/53 | True | 0 | False | $0.0648 | $0.0478 | VERIFIED |
| pr_test_3 | clean | 58/58 | 58/58 | True | 0 | False | $0.0919 | $0.0678 | VERIFIED |
| pr_test_3 | buggy_a | 57/58 | 58/58 | True | 0 | False | $0.0905 | $0.0450 | VERIFIED |
| pr_test_3 | buggy_b | 57/58 | 58/58 | True | 0 | False | $0.0988 | $0.0797 | PARTIAL |
| pr_test_3 | buggy_c | 57/58 | 58/58 | True | 0 | False | $0.1165 | $0.0790 | VERIFIED |
| pr_test_4 | clean | 55/55 | 55/55 | True | 0 | False | $0.1417 | $0.1063 | VERIFIED |
| pr_test_4 | buggy_a | 54/55 | 55/55 | True | 0 | False | $0.0760 | $0.0447 | VERIFIED |
| pr_test_4 | buggy_b | 54/55 | 55/55 | True | 0 | False | $0.0968 | $0.0653 | VERIFIED |
| pr_test_4 | buggy_c | 52/55 | 55/55 | True | 0 | False | $0.0802 | $0.0515 | VERIFIED |
| pr_test_5 | clean | 52/52 | 52/52 | True | 0 | False | $0.0899 | $0.0699 | VERIFIED |
| pr_test_5 | buggy_a | 50/52 | 52/52 | True | 0 | False | $0.0699 | $0.0395 | VERIFIED |
| pr_test_5 | buggy_b | 51/52 | 52/52 | True | 0 | False | $0.0918 | $0.0585 | VERIFIED |
| pr_test_5 | buggy_c | 51/52 | 52/52 | True | 0 | False | $0.0508 | $0.0374 | VERIFIED |
| pr_test_6 | clean | 56/56 | 56/56 | True | 0 | False | $0.0267 | $0.0267 | VERIFIED |
| pr_test_6 | buggy_a | 55/56 | 56/56 | True | 0 | False | $0.1130 | $0.0682 | VERIFIED |
| pr_test_6 | buggy_b | 55/56 | 55/56 | False | 0 | False | $0.0430 | $0.0430 | VERIFIED |
| pr_test_6 | buggy_c | 55/56 | 56/56 | True | 0 | False | $0.0948 | $0.0615 | VERIFIED |

## single C_open

| task | target | before | after | fixed | regressions | damaged | usd | reviewer usd | status |
|---|---|---|---|---|---|---|---|---|---|
| allocate_ratios | m1 | 17/18 | 18/18 | True | 0 | False | $0.0779 | $0.0000 | VERIFIED |
| allocate_ratios | m2 | 17/18 | 18/18 | True | 0 | False | $0.0557 | $0.0000 | VERIFIED |
| allocate_ratios | m3 | 17/18 | 18/18 | True | 0 | False | $0.0705 | $0.0000 | VERIFIED |
| allocate_ratios | clean | 18/18 | 18/18 | True | 0 | False | $0.0675 | $0.0000 | VERIFIED |
| apr_apy | m1 | 19/20 | 20/20 | True | 0 | False | $0.0701 | $0.0000 | VERIFIED |
| apr_apy | m2 | 18/20 | 20/20 | True | 0 | False | $0.0682 | $0.0000 | VERIFIED |
| apr_apy | m3 | 19/20 | 20/20 | True | 0 | False | $0.0593 | $0.0000 | VERIFIED |
| apr_apy | clean | 20/20 | 20/20 | True | 0 | False | $0.0212 | $0.0000 | VERIFIED |
| bank_reconciliation | m1 | 19/20 | 19/20 | False | 0 | False | $0.0411 | $0.0000 | VERIFIED |
| bank_reconciliation | m2 | 19/20 | 20/20 | True | 0 | False | $0.1031 | $0.0000 | VERIFIED |
| bank_reconciliation | m3 | 18/20 | 20/20 | True | 0 | False | $0.1154 | $0.0000 | VERIFIED |
| bank_reconciliation | clean | 20/20 | 20/20 | True | 0 | False | $0.0806 | $0.0000 | VERIFIED |
| budget_variance | m1 | 14/15 | 15/15 | True | 0 | False | $0.0709 | $0.0000 | VERIFIED |
| budget_variance | m2 | 14/15 | 15/15 | True | 0 | False | $0.0751 | $0.0000 | VERIFIED |
| budget_variance | m3 | 14/15 | 15/15 | True | 0 | False | $0.0673 | $0.0000 | VERIFIED |
| budget_variance | clean | 15/15 | 15/15 | True | 0 | False | $0.0666 | $0.0000 | VERIFIED |
| depreciation_declining | m1 | 17/19 | 19/19 | True | 0 | False | $0.0639 | $0.0000 | VERIFIED |
| depreciation_declining | m2 | 18/19 | 19/19 | True | 0 | False | $0.0581 | $0.0000 | VERIFIED |
| depreciation_declining | m3 | 18/19 | 19/19 | True | 0 | False | $0.0793 | $0.0000 | VERIFIED |
| depreciation_declining | clean | 19/19 | 19/19 | True | 0 | False | $0.0726 | $0.0000 | VERIFIED |
| depreciation_straight_line | m1 | 18/19 | 19/19 | True | 0 | False | $0.0606 | $0.0000 | VERIFIED |
| depreciation_straight_line | m2 | 18/19 | 19/19 | True | 0 | False | $0.0729 | $0.0000 | VERIFIED |
| depreciation_straight_line | m3 | 18/19 | 19/19 | True | 0 | False | $0.0714 | $0.0000 | VERIFIED |
| depreciation_straight_line | clean | 19/19 | 19/19 | True | 0 | False | $0.0675 | $0.0000 | VERIFIED |
| duplicate_payments | m1 | 17/18 | 17/18 | False | 0 | False | $0.0391 | $0.0000 | VERIFIED |
| duplicate_payments | m2 | 17/18 | 18/18 | True | 0 | False | $0.1410 | $0.0000 | VERIFIED |
| duplicate_payments | m3 | 17/18 | 18/18 | True | 0 | False | $0.0940 | $0.0000 | VERIFIED |
| duplicate_payments | clean | 18/18 | 18/18 | True | 0 | False | $0.0273 | $0.0000 | VERIFIED |
| eom_roll | m1 | 19/20 | 20/20 | True | 0 | False | $0.0720 | $0.0000 | VERIFIED |
| eom_roll | m2 | 18/20 | 20/20 | True | 0 | False | $0.0823 | $0.0000 | VERIFIED |
| eom_roll | m3 | 19/20 | 20/20 | True | 0 | False | $0.0614 | $0.0000 | VERIFIED |
| eom_roll | clean | 20/20 | 20/20 | True | 0 | False | $0.0234 | $0.0000 | VERIFIED |
| fx_triangulation | m1 | 19/20 | 20/20 | True | 0 | False | $0.1086 | $0.0000 | VERIFIED |
| fx_triangulation | m2 | 18/20 | 20/20 | True | 0 | False | $0.0830 | $0.0000 | VERIFIED |
| fx_triangulation | m3 | 19/20 | 20/20 | True | 0 | False | $0.1019 | $0.0000 | VERIFIED |
| fx_triangulation | clean | 20/20 | 20/20 | True | 0 | False | $0.2162 | $0.0000 | VERIFIED |
| idempotent_ledger | m1 | 17/18 | 18/18 | True | 0 | False | $0.0914 | $0.0000 | VERIFIED |
| idempotent_ledger | m2 | 17/18 | 18/18 | True | 0 | False | $0.0814 | $0.0000 | VERIFIED |
| idempotent_ledger | m3 | 17/18 | 18/18 | True | 0 | False | $0.1026 | $0.0000 | VERIFIED |
| idempotent_ledger | clean | 18/18 | 18/18 | True | 0 | False | $0.0313 | $0.0000 | VERIFIED |
| madrid_cutoff | m1 | 18/19 | 18/19 | False | 0 | False | $0.0360 | $0.0000 | VERIFIED |
| madrid_cutoff | m2 | 17/19 | 19/19 | True | 0 | False | $0.0472 | $0.0000 | VERIFIED |
| madrid_cutoff | m3 | 18/19 | 19/19 | True | 0 | False | $0.0641 | $0.0000 | VERIFIED |
| madrid_cutoff | clean | 19/19 | 19/19 | True | 0 | False | $0.0213 | $0.0000 | VERIFIED |
| percent_change | m1 | 15/18 | 18/18 | True | 0 | False | $0.0405 | $0.0000 | VERIFIED |
| percent_change | m2 | 17/18 | 18/18 | True | 0 | False | $0.0415 | $0.0000 | VERIFIED |
| percent_change | m3 | 17/18 | 18/18 | True | 0 | False | $0.0453 | $0.0000 | VERIFIED |
| percent_change | clean | 18/18 | 18/18 | True | 0 | False | $0.0146 | $0.0000 | VERIFIED |
| progressive_tax | m1 | 16/18 | 18/18 | True | 0 | False | $0.0645 | $0.0000 | VERIFIED |
| progressive_tax | m2 | 16/18 | 18/18 | True | 0 | False | $0.0654 | $0.0000 | VERIFIED |
| progressive_tax | m3 | 17/18 | 18/18 | True | 0 | False | $0.0697 | $0.0000 | VERIFIED |
| progressive_tax | clean | 18/18 | 18/18 | True | 0 | False | $0.0585 | $0.0000 | VERIFIED |
| prorata_billing | m1 | 17/18 | 18/18 | True | 0 | False | $0.1004 | $0.0000 | VERIFIED |
| prorata_billing | m2 | 17/18 | 18/18 | True | 0 | False | $0.1097 | $0.0000 | VERIFIED |
| prorata_billing | m3 | 17/18 | 18/18 | True | 0 | False | $0.0867 | $0.0000 | VERIFIED |
| prorata_billing | clean | 18/18 | 18/18 | True | 0 | False | $0.0350 | $0.0000 | VERIFIED |
| rf_reference | m1 | 15/16 | 16/16 | True | 0 | False | $0.0624 | $0.0000 | VERIFIED |
| rf_reference | m2 | 15/16 | 16/16 | True | 0 | False | $0.0688 | $0.0000 | VERIFIED |
| rf_reference | m3 | 14/16 | 16/16 | True | 0 | False | $0.0636 | $0.0000 | VERIFIED |
| rf_reference | clean | 16/16 | 16/16 | True | 0 | False | $0.0222 | $0.0000 | VERIFIED |
| running_balance | m1 | 18/19 | 19/19 | True | 0 | False | $0.0913 | $0.0000 | VERIFIED |
| running_balance | m2 | 16/19 | 16/19 | False | 0 | False | $0.0399 | $0.0000 | VERIFIED |
| running_balance | m3 | 17/19 | 17/19 | False | 0 | False | $0.0544 | $0.0000 | VERIFIED |
| running_balance | clean | 19/19 | 19/19 | True | 0 | False | $0.1260 | $0.0000 | VERIFIED |
| spanish_bank_csv | m1 | 19/20 | 20/20 | True | 0 | False | $0.0826 | $0.0000 | VERIFIED |
| spanish_bank_csv | m2 | 19/20 | 20/20 | True | 0 | False | $0.0801 | $0.0000 | VERIFIED |
| spanish_bank_csv | m3 | 19/20 | 19/20 | False | 0 | False | $0.0478 | $0.0000 | VERIFIED |
| spanish_bank_csv | clean | 20/20 | 20/20 | True | 0 | False | $0.0252 | $0.0000 | VERIFIED |
| spanish_tax_id | m1 | 16/17 | 17/17 | True | 0 | False | $0.0751 | $0.0000 | VERIFIED |
| spanish_tax_id | m2 | 14/17 | 17/17 | True | 0 | False | $0.0604 | $0.0000 | VERIFIED |
| spanish_tax_id | m3 | 16/17 | 17/17 | True | 0 | False | $0.0572 | $0.0000 | VERIFIED |
| spanish_tax_id | clean | 17/17 | 17/17 | True | 0 | False | $0.0732 | $0.0000 | VERIFIED |
| weighted_average_cost | m1 | 19/20 | 20/20 | True | 0 | False | $0.0922 | $0.0000 | VERIFIED |
| weighted_average_cost | m2 | 18/20 | 20/20 | True | 0 | False | $0.0903 | $0.0000 | VERIFIED |
| weighted_average_cost | m3 | 19/20 | 20/20 | True | 0 | False | $0.0849 | $0.0000 | VERIFIED |
| weighted_average_cost | clean | 20/20 | 20/20 | True | 0 | False | $0.0300 | $0.0000 | VERIFIED |
| xirr | m1 | 19/20 | 20/20 | True | 0 | False | $0.0942 | $0.0000 | VERIFIED |
| xirr | m2 | 19/20 | 20/20 | True | 0 | False | $0.1186 | $0.0000 | VERIFIED |
| xirr | m3 | 19/20 | 20/20 | True | 0 | False | $0.1032 | $0.0000 | VERIFIED |
| xirr | clean | 20/20 | 20/20 | True | 0 | False | $0.1090 | $0.0000 | VERIFIED |

## single E_open

| task | target | before | after | fixed | regressions | damaged | usd | reviewer usd | status |
|---|---|---|---|---|---|---|---|---|---|
| allocate_ratios | m1 | 17/18 | 18/18 | True | 0 | False | $0.0584 | $0.0382 | VERIFIED |
| allocate_ratios | m2 | 17/18 | 18/18 | True | 0 | False | $0.0408 | $0.0186 | VERIFIED |
| allocate_ratios | m3 | 17/18 | 17/18 | False | 0 | False | $0.0215 | $0.0140 | VERIFIED |
| allocate_ratios | clean | 18/18 | 18/18 | True | 0 | False | $0.0521 | $0.0346 | VERIFIED |
| apr_apy | m1 | 19/20 | 20/20 | True | 0 | False | $0.0245 | $0.0187 | VERIFIED |
| apr_apy | m2 | 18/20 | 20/20 | True | 0 | False | $0.0240 | $0.0192 | VERIFIED |
| apr_apy | m3 | 19/20 | 20/20 | True | 0 | False | $0.0250 | $0.0199 | VERIFIED |
| apr_apy | clean | 20/20 | 20/20 | True | 0 | False | $0.0127 | $0.0127 | VERIFIED |
| bank_reconciliation | m1 | 19/20 | 19/20 | False | 0 | False | $0.0239 | $0.0132 | VERIFIED |
| bank_reconciliation | m2 | 19/20 | 19/20 | False | 0 | False | $0.0264 | $0.0143 | VERIFIED |
| bank_reconciliation | m3 | 18/20 | 18/20 | False | 0 | False | $0.0262 | $0.0159 | VERIFIED |
| bank_reconciliation | clean | 20/20 | 20/20 | True | 0 | False | $0.0141 | $0.0141 | VERIFIED |
| budget_variance | m1 | 14/15 | 15/15 | True | 0 | False | $0.0313 | $0.0228 | VERIFIED |
| budget_variance | m2 | 14/15 | 15/15 | True | 0 | False | $0.0307 | $0.0218 | VERIFIED |
| budget_variance | m3 | 14/15 | 14/15 | False | 0 | False | $0.0188 | $0.0095 | VERIFIED |
| budget_variance | clean | 15/15 | 15/15 | True | 0 | False | $0.0272 | $0.0192 | VERIFIED |
| depreciation_declining | m1 | 17/19 | 19/19 | True | 0 | False | $0.0372 | $0.0287 | VERIFIED |
| depreciation_declining | m2 | 18/19 | 19/19 | True | 0 | False | $0.0270 | $0.0181 | VERIFIED |
| depreciation_declining | m3 | 18/19 | 19/19 | True | 0 | False | $0.0334 | $0.0278 | VERIFIED |
| depreciation_declining | clean | 19/19 | 19/19 | True | 0 | False | $0.0416 | $0.0288 | VERIFIED |
| depreciation_straight_line | m1 | 18/19 | 19/19 | True | 0 | False | $0.0569 | $0.0306 | VERIFIED |
| depreciation_straight_line | m2 | 18/19 | 19/19 | True | 0 | False | $0.0448 | $0.0309 | VERIFIED |
| depreciation_straight_line | m3 | 18/19 | 19/19 | True | 0 | False | $0.0819 | $0.0490 | VERIFIED |
| depreciation_straight_line | clean | 19/19 | 19/19 | True | 0 | False | $0.0124 | $0.0124 | VERIFIED |
| duplicate_payments | m1 | 17/18 | 17/18 | False | 0 | False | $0.0277 | $0.0162 | VERIFIED |
| duplicate_payments | m2 | 17/18 | 18/18 | True | 0 | False | $0.0388 | $0.0257 | VERIFIED |
| duplicate_payments | m3 | 17/18 | 18/18 | True | 0 | False | $0.0397 | $0.0289 | VERIFIED |
| duplicate_payments | clean | 18/18 | 18/18 | True | 0 | False | $0.0163 | $0.0163 | VERIFIED |
| eom_roll | m1 | 19/20 | 20/20 | True | 0 | False | $0.0215 | $0.0160 | VERIFIED |
| eom_roll | m2 | 18/20 | 20/20 | True | 0 | False | $0.0206 | $0.0153 | VERIFIED |
| eom_roll | m3 | 19/20 | 20/20 | True | 0 | False | $0.0206 | $0.0156 | VERIFIED |
| eom_roll | clean | 20/20 | 20/20 | True | 0 | False | $0.0079 | $0.0079 | VERIFIED |
| fx_triangulation | m1 | 19/20 | 19/20 | False | 0 | False | $0.0227 | $0.0171 | VERIFIED |
| fx_triangulation | m2 | 18/20 | 18/20 | False | 0 | False | $0.0198 | $0.0131 | VERIFIED |
| fx_triangulation | m3 | 19/20 | 20/20 | True | 0 | False | $0.0294 | $0.0235 | VERIFIED |
| fx_triangulation | clean | 20/20 | 20/20 | True | 0 | False | $0.0266 | $0.0266 | VERIFIED |
| idempotent_ledger | m1 | 17/18 | 18/18 | True | 0 | False | $0.0405 | $0.0245 | VERIFIED |
| idempotent_ledger | m2 | 17/18 | 18/18 | True | 0 | False | $0.0233 | $0.0173 | VERIFIED |
| idempotent_ledger | m3 | 17/18 | 18/18 | True | 0 | False | $0.0450 | $0.0283 | VERIFIED |
| idempotent_ledger | clean | 18/18 | 18/18 | True | 0 | False | $0.0332 | $0.0255 | VERIFIED |
| madrid_cutoff | m1 | 18/19 | 19/19 | True | 0 | False | $0.0349 | $0.0273 | VERIFIED |
| madrid_cutoff | m2 | 17/19 | 19/19 | True | 0 | False | $0.0240 | $0.0172 | VERIFIED |
| madrid_cutoff | m3 | 18/19 | 18/19 | False | 0 | False | $0.0220 | $0.0148 | VERIFIED |
| madrid_cutoff | clean | 19/19 | 19/19 | True | 0 | False | $0.0189 | $0.0135 | VERIFIED |
| percent_change | m1 | 15/18 | 18/18 | True | 0 | False | $0.0172 | $0.0120 | VERIFIED |
| percent_change | m2 | 17/18 | 18/18 | True | 0 | False | $0.0174 | $0.0128 | VERIFIED |
| percent_change | m3 | 17/18 | 18/18 | True | 0 | False | $0.0136 | $0.0095 | VERIFIED |
| percent_change | clean | 18/18 | 18/18 | True | 0 | False | $0.0053 | $0.0053 | VERIFIED |
| progressive_tax | m1 | 16/18 | 18/18 | True | 0 | False | $0.0261 | $0.0195 | VERIFIED |
| progressive_tax | m2 | 16/18 | 18/18 | True | 0 | False | $0.0215 | $0.0153 | VERIFIED |
| progressive_tax | m3 | 17/18 | 18/18 | True | 0 | False | $0.0277 | $0.0194 | VERIFIED |
| progressive_tax | clean | 18/18 | 18/18 | True | 0 | False | $0.0090 | $0.0090 | VERIFIED |
| prorata_billing | m1 | 17/18 | 18/18 | True | 0 | False | $0.0571 | $0.0328 | VERIFIED |
| prorata_billing | m2 | 17/18 | 17/18 | False | 0 | False | $0.0235 | $0.0142 | VERIFIED |
| prorata_billing | m3 | 17/18 | 18/18 | True | 0 | False | $0.0380 | $0.0284 | VERIFIED |
| prorata_billing | clean | 18/18 | 18/18 | True | 0 | False | $0.0462 | $0.0373 | VERIFIED |
| rf_reference | m1 | 15/16 | 16/16 | True | 0 | False | $0.0241 | $0.0183 | VERIFIED |
| rf_reference | m2 | 15/16 | 15/16 | False | 0 | False | $0.0109 | $0.0064 | VERIFIED |
| rf_reference | m3 | 14/16 | 16/16 | True | 0 | False | $0.0228 | $0.0168 | VERIFIED |
| rf_reference | clean | 16/16 | 16/16 | True | 0 | False | $0.0093 | $0.0093 | VERIFIED |
| running_balance | m1 | 18/19 | 18/19 | False | 0 | False | $0.0173 | $0.0096 | VERIFIED |
| running_balance | m2 | 16/19 | 16/19 | False | 0 | False | $0.0173 | $0.0111 | VERIFIED |
| running_balance | m3 | 17/19 | 17/19 | False | 0 | False | $0.0221 | $0.0158 | VERIFIED |
| running_balance | clean | 19/19 | 19/19 | True | 0 | False | $0.0261 | $0.0132 | VERIFIED |
| spanish_bank_csv | m1 | 19/20 | 20/20 | True | 0 | False | $0.0440 | $0.0340 | VERIFIED |
| spanish_bank_csv | m2 | 19/20 | 19/20 | False | 0 | False | $0.0192 | $0.0167 | VERIFIED |
| spanish_bank_csv | m3 | 19/20 | 19/20 | False | 0 | False | $0.0246 | $0.0173 | VERIFIED |
| spanish_bank_csv | clean | 20/20 | 20/20 | True | 0 | False | $0.0271 | $0.0271 | VERIFIED |
| spanish_tax_id | m1 | 16/17 | 17/17 | True | 0 | False | $0.0270 | $0.0198 | VERIFIED |
| spanish_tax_id | m2 | 14/17 | 17/17 | True | 0 | False | $0.0185 | $0.0121 | VERIFIED |
| spanish_tax_id | m3 | 16/17 | 16/17 | False | 0 | False | $0.0117 | $0.0088 | VERIFIED |
| spanish_tax_id | clean | 17/17 | 17/17 | True | 0 | False | $0.0060 | $0.0060 | VERIFIED |
| weighted_average_cost | m1 | 19/20 | 19/20 | False | 0 | False | $0.0230 | $0.0174 | VERIFIED |
| weighted_average_cost | m2 | 18/20 | 20/20 | True | 0 | False | $0.0502 | $0.0297 | VERIFIED |
| weighted_average_cost | m3 | 19/20 | 19/20 | False | 0 | False | $0.0195 | $0.0122 | VERIFIED |
| weighted_average_cost | clean | 20/20 | 20/20 | True | 0 | False | $0.0139 | $0.0139 | VERIFIED |
| xirr | m1 | 19/20 | 20/20 | True | 0 | False | $0.0380 | $0.0271 | VERIFIED |
| xirr | m2 | 19/20 | 20/20 | True | 0 | False | $0.0303 | $0.0208 | VERIFIED |
| xirr | m3 | 19/20 | 20/20 | True | 0 | False | $0.0381 | $0.0277 | VERIFIED |
| xirr | clean | 20/20 | 20/20 | True | 0 | False | $0.0089 | $0.0089 | VERIFIED |

## single D_open

| task | target | before | after | fixed | regressions | damaged | usd | reviewer usd | status |
|---|---|---|---|---|---|---|---|---|---|
| allocate_ratios | m1 | 17/18 | 18/18 | True | 0 | False | $0.1380 | $0.1055 | VERIFIED |
| allocate_ratios | m2 | 17/18 | 18/18 | True | 0 | False | $0.1485 | $0.1022 | VERIFIED |
| allocate_ratios | m3 | 17/18 | 17/18 | False | 0 | False | $0.0680 | $0.0539 | VERIFIED |
| allocate_ratios | clean | 18/18 | 18/18 | True | 0 | False | $0.2000 | $0.1362 | PARTIAL |
| apr_apy | m1 | 19/20 | 20/20 | True | 0 | False | $0.0494 | $0.0429 | VERIFIED |
| apr_apy | m2 | 18/20 | 20/20 | True | 0 | False | $0.0562 | $0.0483 | VERIFIED |
| apr_apy | m3 | 19/20 | 20/20 | True | 0 | False | $0.0302 | $0.0244 | VERIFIED |
| apr_apy | clean | 20/20 | 20/20 | True | 0 | False | $0.0110 | $0.0110 | VERIFIED |
| bank_reconciliation | m1 | 19/20 | 20/20 | True | 0 | False | $0.0759 | $0.0390 | VERIFIED |
| bank_reconciliation | m2 | 19/20 | 19/20 | False | 0 | False | $0.0159 | $0.0069 | PARTIAL |
| bank_reconciliation | m3 | 18/20 | 20/20 | True | 0 | False | $0.0546 | $0.0452 | VERIFIED |
| bank_reconciliation | clean | 20/20 | 20/20 | True | 0 | False | $0.0307 | $0.0307 | VERIFIED |
| budget_variance | m1 | 14/15 | 15/15 | True | 0 | False | $0.0413 | $0.0327 | VERIFIED |
| budget_variance | m2 | 14/15 | 15/15 | True | 0 | False | $0.0943 | $0.0832 | VERIFIED |
| budget_variance | m3 | 14/15 | 15/15 | True | 0 | False | $0.0584 | $0.0462 | VERIFIED |
| budget_variance | clean | 15/15 | 15/15 | True | 0 | False | $0.0177 | $0.0177 | VERIFIED |
| depreciation_declining | m1 | 17/19 | 19/19 | True | 0 | False | $0.0653 | $0.0489 | VERIFIED |
| depreciation_declining | m2 | 18/19 | 19/19 | True | 0 | False | $0.0436 | $0.0379 | VERIFIED |
| depreciation_declining | m3 | 18/19 | 19/19 | True | 0 | False | $0.0533 | $0.0458 | VERIFIED |
| depreciation_declining | clean | 19/19 | 19/19 | True | 0 | False | $0.0637 | $0.0529 | VERIFIED |
| depreciation_straight_line | m1 | 18/19 | 19/19 | True | 0 | False | $0.0806 | $0.0504 | VERIFIED |
| depreciation_straight_line | m2 | 18/19 | 19/19 | True | 0 | False | $0.0788 | $0.0666 | VERIFIED |
| depreciation_straight_line | m3 | 18/19 | 19/19 | True | 0 | False | $0.0884 | $0.0605 | VERIFIED |
| depreciation_straight_line | clean | 19/19 | 19/19 | True | 0 | False | $0.0800 | $0.0716 | VERIFIED |
| duplicate_payments | m1 | 17/18 | 18/18 | True | 0 | False | $0.0869 | $0.0622 | VERIFIED |
| duplicate_payments | m2 | 17/18 | 18/18 | True | 0 | False | $0.0773 | $0.0625 | VERIFIED |
| duplicate_payments | m3 | 17/18 | 17/18 | False | 0 | False | $0.0297 | $0.0196 | PARTIAL |
| duplicate_payments | clean | 18/18 | 18/18 | True | 0 | False | $0.0742 | $0.0500 | VERIFIED |
| eom_roll | m1 | 19/20 | 20/20 | True | 0 | False | $0.0356 | $0.0294 | VERIFIED |
| eom_roll | m2 | 18/20 | 20/20 | True | 0 | False | $0.0282 | $0.0215 | VERIFIED |
| eom_roll | m3 | 19/20 | 20/20 | True | 0 | False | $0.0290 | $0.0202 | VERIFIED |
| eom_roll | clean | 20/20 | 20/20 | True | 0 | False | $0.0157 | $0.0157 | VERIFIED |
| fx_triangulation | m1 | 19/20 | 20/20 | True | 0 | False | $0.0588 | $0.0478 | VERIFIED |
| fx_triangulation | m2 | 18/20 | 20/20 | True | 0 | False | $0.0536 | $0.0468 | VERIFIED |
| fx_triangulation | m3 | 19/20 | 20/20 | True | 0 | False | $0.0587 | $0.0507 | VERIFIED |
| fx_triangulation | clean | 20/20 | 20/20 | True | 0 | False | $0.0192 | $0.0192 | VERIFIED |
| idempotent_ledger | m1 | 17/18 | 18/18 | True | 0 | False | $0.0609 | $0.0434 | VERIFIED |
| idempotent_ledger | m2 | 17/18 | 18/18 | True | 0 | False | $0.0525 | $0.0441 | VERIFIED |
| idempotent_ledger | m3 | 17/18 | 18/18 | True | 0 | False | $0.0760 | $0.0582 | VERIFIED |
| idempotent_ledger | clean | 18/18 | 18/18 | True | 0 | False | $0.0649 | $0.0457 | VERIFIED |
| madrid_cutoff | m1 | 18/19 | 19/19 | True | 0 | False | $0.0767 | $0.0666 | VERIFIED |
| madrid_cutoff | m2 | 17/19 | 19/19 | True | 0 | False | $0.0740 | $0.0659 | VERIFIED |
| madrid_cutoff | m3 | 18/19 | 19/19 | True | 0 | False | $0.0594 | $0.0507 | VERIFIED |
| madrid_cutoff | clean | 19/19 | 19/19 | True | 0 | False | $0.0556 | $0.0556 | VERIFIED |
| percent_change | m1 | 15/18 | 18/18 | True | 0 | False | $0.0344 | $0.0298 | VERIFIED |
| percent_change | m2 | 17/18 | 18/18 | True | 0 | False | $0.0727 | $0.0540 | PARTIAL |
| percent_change | m3 | 17/18 | 18/18 | True | 0 | False | $0.0594 | $0.0346 | PARTIAL |
| percent_change | clean | 18/18 | 18/18 | True | 0 | False | $0.0852 | $0.0590 | PARTIAL |
| progressive_tax | m1 | 16/18 | 18/18 | True | 0 | False | $0.0522 | $0.0334 | VERIFIED |
| progressive_tax | m2 | 16/18 | 18/18 | True | 0 | False | $0.0604 | $0.0458 | VERIFIED |
| progressive_tax | m3 | 17/18 | 18/18 | True | 0 | False | $0.0493 | $0.0427 | VERIFIED |
| progressive_tax | clean | 18/18 | 18/18 | True | 0 | False | $0.0504 | $0.0405 | VERIFIED |
| prorata_billing | m1 | 17/18 | 18/18 | True | 0 | False | $0.0715 | $0.0511 | VERIFIED |
| prorata_billing | m2 | 17/18 | 18/18 | True | 0 | False | $0.0582 | $0.0404 | VERIFIED |
| prorata_billing | m3 | 17/18 | 18/18 | True | 0 | False | $0.0777 | $0.0507 | VERIFIED |
| prorata_billing | clean | 18/18 | 18/18 | True | 0 | False | $0.0705 | $0.0606 | VERIFIED |
| rf_reference | m1 | 15/16 | 16/16 | True | 0 | False | $0.0370 | $0.0303 | VERIFIED |
| rf_reference | m2 | 15/16 | 16/16 | True | 0 | False | $0.0389 | $0.0303 | VERIFIED |
| rf_reference | m3 | 14/16 | 16/16 | True | 0 | False | $0.0310 | $0.0242 | VERIFIED |
| rf_reference | clean | 16/16 | 16/16 | True | 0 | False | $0.0214 | $0.0214 | VERIFIED |
| running_balance | m1 | 18/19 | 19/19 | True | 0 | False | $0.0586 | $0.0404 | VERIFIED |
| running_balance | m2 | 16/19 | 19/19 | True | 0 | False | $0.0586 | $0.0415 | PARTIAL |
| running_balance | m3 | 17/19 | 19/19 | True | 0 | False | $0.0479 | $0.0376 | VERIFIED |
| running_balance | clean | 19/19 | 19/19 | True | 0 | False | $0.0550 | $0.0462 | VERIFIED |
| spanish_bank_csv | m1 | 19/20 | 20/20 | True | 0 | False | $0.0765 | $0.0664 | VERIFIED |
| spanish_bank_csv | m2 | 19/20 | 20/20 | True | 0 | False | $0.0722 | $0.0641 | VERIFIED |
| spanish_bank_csv | m3 | 19/20 | 20/20 | True | 0 | False | $0.1209 | $0.1127 | VERIFIED |
| spanish_bank_csv | clean | 20/20 | 20/20 | True | 0 | False | $0.0509 | $0.0509 | VERIFIED |
| spanish_tax_id | m1 | 16/17 | 17/17 | True | 0 | False | $0.0359 | $0.0280 | VERIFIED |
| spanish_tax_id | m2 | 14/17 | 17/17 | True | 0 | False | $0.0337 | $0.0259 | VERIFIED |
| spanish_tax_id | m3 | 16/17 | 17/17 | True | 0 | False | $0.0339 | $0.0273 | VERIFIED |
| spanish_tax_id | clean | 17/17 | 17/17 | True | 0 | False | $0.0253 | $0.0253 | VERIFIED |
| weighted_average_cost | m1 | 19/20 | 20/20 | True | 0 | False | $0.0894 | $0.0577 | PARTIAL |
| weighted_average_cost | m2 | 18/20 | 20/20 | True | 0 | False | $0.1011 | $0.0750 | PARTIAL |
| weighted_average_cost | m3 | 19/20 | 20/20 | True | 0 | False | $0.0686 | $0.0615 | VERIFIED |
| weighted_average_cost | clean | 20/20 | 20/20 | True | 0 | False | $0.0782 | $0.0627 | PARTIAL |
| xirr | m1 | 19/20 | 20/20 | True | 0 | False | $0.1080 | $0.0842 | VERIFIED |
| xirr | m2 | 19/20 | 20/20 | True | 0 | False | $0.0757 | $0.0656 | VERIFIED |
| xirr | m3 | 19/20 | 20/20 | True | 0 | False | $0.0958 | $0.0857 | VERIFIED |
| xirr | clean | 20/20 | 20/20 | True | 0 | False | $0.1820 | $0.1484 | PARTIAL |

## Notes

- Every condition fixed most mutants with zero damage to clean targets and
  zero regressions. Unlike the Wonder-based dev pilots (where every reviewing
  condition fixed everything), the open model separates the conditions:
  proof-gated D_open (94-95% fixed) and self-check C_open (90-94%) clearly
  beat free-text E_open (67-68%).
- D_open claim precision (VALID/PROVEN): 0.40 on PR targets, 0.64 on
  single-task targets.
- Cheapest per fixed mutant is D_open on PR targets ($0.0858/target) despite
  the proof rule, because proven claims end rounds earlier than free-text
  feedback loops.
