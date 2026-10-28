# Data Quality Audit Report: Retail Store Sales

## 1. Dataset overview
- Source: Kaggle, "Retail Store Sales: Dirty for Data Cleaning" (raw file: `data/raw/retail_store_sales.csv`, never modified).
- Size: 12,575 rows, 11 columns. One row = one transaction (`Transaction ID` is unique).
- Cleaned output: `data/clean/retail_store_sales_clean.csv` (11,971 rows).
- Everything is reproducible with `python src/clean_data.py`.

## 2. Diagnostic findings

| Check | Result |
|---|---|
| Fully duplicated rows | 0 |
| Duplicated `Transaction ID` | 0 |
| Missing `Item` | 1,213 (9.6%) |
| Missing `Price Per Unit` | 609 (4.8%) |
| Missing `Quantity` | 604 (4.8%) |
| Missing `Total Spent` | 604 (4.8%) |
| Missing `Discount Applied` | 4,199 (33.4%) |
| Hidden missing values (ERROR, UNKNOWN, ...) | none found |
| Wrong data types | `Transaction Date` (text), `Discount Applied` (text) |
| Invalid dates | 0 |
| Non-positive numeric values | 0 |
| Outliers (IQR) | `Total Spent`: 60; `Quantity`: 0; `Price Per Unit`: 0 |

## 3. Cleaning decisions and rationale

| Step | Action | Rows affected | Rationale |
|---|---|---|---|
| 1 | Converted `Transaction Date` to datetime, `Discount Applied` to boolean | all | Needed for time analysis and correct filtering. No invalid dates existed. |
| 2 | Computed missing `Price Per Unit` as `Total Spent / Quantity` | 609 | The relation `Total Spent = Quantity x Price Per Unit` holds in every complete row (0 mismatches), so the value is derived, not guessed. |
| 3 | Dropped rows with `Quantity` and `Total Spent` both missing | 604 (4.8%) | Two unknowns in one equation cannot be solved. Imputing a median would invent sales that may not have happened and distort revenue. |
| 4 | Filled missing `Item` with "Unknown Item" | 609 | `Item` cannot be derived from other columns. A placeholder keeps the row and makes the gap visible. |
| 5 | Filled missing `Discount Applied` with False | 3,988 | Assumed conservative business logic: unless explicitly recorded as True, no discount was verified. Downstream analyses relying on promotions should interpret this feature with caution. |
| 6 | Kept `Total Spent` outliers | 60 | See Section 5. |

## 4. Before and after

- Rows: 12,575 -> 11,971 (604 removed).
- Missing cells: 7,229 -> 0.
- `Quantity`: mean 5.54 -> 5.54, median 6.0 -> 6.0, std 2.86 -> 2.86.
- `Price Per Unit`: mean 23.37 -> 23.36, median 23.0 -> 23.0, std 10.74 -> 10.74.
- `Total Spent`: mean 129.65 -> 129.65, median 108.5 -> 108.5, std 94.75 -> 94.75.
- The distributions of the numeric columns are essentially unchanged, so dropping incomplete rows and deriving values did not distort them. `Discount Applied` is the exception (see Section 6).

Full table: `reports/before_after_comparison.csv`. Step-by-step log: `reports/cleaning_log.csv`.

## 5. Outliers
IQR limits for `Total Spent`: up to 403.5. Sixty rows exceed it, with a maximum of 410. Since the maximum `Quantity` is 10 and the maximum `Price Per Unit` is 41, the largest possible purchase is 10 x 41 = 410. These are genuine large purchases, not errors, so they were kept.

## 6. Limitations and assumptions
- Dropping 604 rows (4.8%) assumes those rows are not systematically different from the rest.
- `Discount Applied`: among the rows where it was known, about 50.4% were True. After filling with False, True drops to about 33.6%, so the filled column understates discounts. We treat this column as an indicator of *confirmed discounts* rather than ground truth; downstream modeling should consider sensitivity analysis or treating unrecorded discounts as a separate category if necessary.
- `Unknown Item` rows (609) cannot be used for item-level analysis.

## 7. Reproducibility
Run `python src/clean_data.py` from the project root. The script reads the raw file, applies all steps, runs validation checks (no missing values, no duplicates, no non-positive values, `Total Spent = Quantity x Price Per Unit`) and writes the clean data, the log and the before/after table.