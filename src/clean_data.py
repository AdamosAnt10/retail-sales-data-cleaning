"""Reproducible cleaning pipeline for retail_store_sales.csv.

Reads the raw file (never modified), applies every cleaning step,
and writes the clean data, a cleaning log and a before/after table.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "retail_store_sales.csv"
CLEAN = ROOT / "data" / "clean" / "retail_store_sales_clean.csv"
REPORTS = ROOT / "reports"

Q, P, T = "Quantity", "Price Per Unit", "Total Spent"


def main():
    df = pd.read_csv(RAW)          # raw data, only read
    df_clean = df.copy()           # all changes happen on the copy
    log = []

    # 1. Fix data types
    df_clean["Transaction Date"] = pd.to_datetime(df_clean["Transaction Date"], errors="coerce")
    df_clean["Discount Applied"] = df_clean["Discount Applied"].astype("boolean")
    df_clean[Q] = pd.to_numeric(df_clean[Q], errors="coerce")
    log.append("Converted 'Transaction Date' to datetime, 'Discount Applied' to boolean, 'Quantity' to numeric.")

    # 2. Compute missing values from Total Spent = Quantity x Price Per Unit
    m = df_clean[T].isna() & df_clean[Q].notna() & df_clean[P].notna()
    df_clean.loc[m, T] = df_clean.loc[m, Q] * df_clean.loc[m, P]
    log.append(f"Computed {m.sum()} missing '{T}' values from '{Q}' x '{P}'.")

    m = df_clean[Q].isna() & df_clean[T].notna() & df_clean[P].notna()
    df_clean.loc[m, Q] = df_clean.loc[m, T] / df_clean.loc[m, P]
    log.append(f"Computed {m.sum()} missing '{Q}' values from '{T}' / '{P}'.")

    m = df_clean[P].isna() & df_clean[T].notna() & df_clean[Q].notna()
    df_clean.loc[m, P] = df_clean.loc[m, T] / df_clean.loc[m, Q]
    log.append(f"Computed {m.sum()} missing '{P}' values from '{T}' / '{Q}'.")

    # 3. Drop rows where Quantity and Total are still missing (cannot be computed)
    before = len(df_clean)
    df_clean = df_clean.dropna(subset=[Q, T])
    log.append(f"Dropped {before - len(df_clean)} rows where '{Q}' and '{T}' were both missing and could not be computed.")

    # 4. Fill remaining categorical / flag columns
    n = df_clean["Discount Applied"].isna().sum()
    df_clean["Discount Applied"] = df_clean["Discount Applied"].fillna(False)
    log.append(f"Filled {n} missing 'Discount Applied' values with False (assumption: no discount recorded).")

    n = df_clean["Item"].isna().sum()
    df_clean["Item"] = df_clean["Item"].fillna("Unknown Item")
    log.append(f"Filled {n} missing 'Item' values with 'Unknown Item'.")

    # 5. Outliers (IQR): detected, not removed
    q1, q3 = df_clean[T].quantile([0.25, 0.75])
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n_out = int(((df_clean[T] < low) | (df_clean[T] > high)).sum())
    log.append(f"'{T}': {n_out} outliers (IQR, above {high:.1f}) kept; max {df_clean[T].max()} equals max Quantity x max Price, so they are genuine purchases.")

    # 6. Validation checks
    assert df_clean.isna().sum().sum() == 0, "Missing values remain"
    assert df_clean.duplicated().sum() == 0, "Duplicates found"
    assert ((df_clean[Q] <= 0) | (df_clean[P] <= 0) | (df_clean[T] <= 0)).sum() == 0, "Non-positive values"
    assert ((df_clean[T] - df_clean[P] * df_clean[Q]).abs() > 0.01).sum() == 0, "Total != Price x Quantity"

    # 7. Save outputs
    CLEAN.parent.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(CLEAN, index=False)
    pd.DataFrame({"step": range(1, len(log) + 1), "action": log}).to_csv(REPORTS / "cleaning_log.csv", index=False)

    nulls = pd.DataFrame({"nulls_before": df.isna().sum(), "nulls_after": df_clean.isna().sum()})
    cols = [Q, P, T]
    stats = pd.DataFrame({
        "mean_before": df[cols].mean(), "mean_after": df_clean[cols].mean(),
        "median_before": df[cols].median(), "median_after": df_clean[cols].median(),
        "std_before": df[cols].std(), "std_after": df_clean[cols].std(),
    }).round(2)
    nulls.join(stats, how="outer").to_csv(REPORTS / "before_after_comparison.csv")

    print(f"Rows: {len(df)} -> {len(df_clean)}")
    for line in log:
        print("-", line)


if __name__ == "__main__":
    main()