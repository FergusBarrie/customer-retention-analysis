"""
Clean the CDNOW master dataset and load it into a SQLite database.

Input : data/raw/CDNOW_master.txt
Output: data/clean/transactions.csv   one row per transaction line
        data/clean/orders.csv         one row per customer per day
        data/clean/customers.csv      one row per customer, with a cohort label
        data/clean/cdnow.db           SQLite database used by the SQL scripts
        outputs/cleaning_log.txt

About the dataset
-----------------
CDNOW was an online CD retailer. This file is the complete purchase history,
up to the end of June 1998, of the 23,570 people who made their first ever
purchase there in the first quarter of 1997. It is published by Bruce Hardie
and was first used in Fader and Hardie (2001).

That makes it unusually good for retention work: every customer is tracked
from their first purchase for up to 18 months, so retention is measured and
not estimated.

The file has four whitespace-separated columns and no header:
customer ID, date (YYYYMMDD), number of CDs, dollar value.

Usage: python scripts/01_clean_data.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "CDNOW_master.txt"
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "outputs"

log_lines = []


def log(msg):
    print(msg)
    log_lines.append(msg)


def main():
    CLEAN.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    tx = pd.read_csv(RAW, sep=r"\s+", header=None,
                     names=["customer_id", "date", "cds", "value"])
    log("Loaded {:,} transaction lines for {:,} customers".format(len(tx), tx.customer_id.nunique()))

    tx["date"] = pd.to_datetime(tx["date"], format="%Y%m%d")
    log("Date range: {} to {}".format(tx.date.min().date(), tx.date.max().date()))
    log("Missing values: {}".format(tx.isna().sum().to_dict()))
    log("")

    # --- the one genuinely ambiguous decision in this dataset ---------------
    #
    # 255 rows are exact duplicates of another row: same customer, same day,
    # same number of CDs, same value. There are two possible explanations and
    # the data cannot settle it: either a customer bought two identical items
    # on the same day (perfectly plausible - two copies of the same CD), or the
    # row was entered twice.
    #
    # I keep them. This file is the published version of the dataset used in
    # the academic literature, so removing rows would make my totals
    # incomparable with everyone else's. I check the size of the effect below
    # so the decision is informed rather than assumed.
    dupe_rows = int(tx.duplicated().sum())
    dupe_value = float(tx[tx.duplicated()].value.sum())
    dupe_share = dupe_value / float(tx.value.sum())
    log("Exact duplicate rows: {:,} ({:.2%} of rows), worth ${:,.2f} ({:.2%} of revenue)".format(
        dupe_rows, dupe_rows / len(tx), dupe_value, dupe_share))
    log("  Kept. They may be two identical items bought on the same day, and this is the")
    log("  published version of the dataset used in the literature. The effect on revenue")
    log("  is {:.2%}, so no conclusion in this project depends on the choice.".format(dupe_share))
    log("")

    # 80 lines have a value of $0 but at least one CD. Probably promotions or
    # replacements. They are real activity, so they count towards whether a
    # customer was active in a month, but they add nothing to revenue.
    zero_value = int((tx.value == 0).sum())
    log("Lines with a $0 value: {} - kept as activity, they add no revenue".format(zero_value))
    log("No negative values and no zero-CD lines, so there are no returns or "
        "adjustments to separate out.")
    log("")

    # --- orders ------------------------------------------------------------
    #
    # A row is a transaction LINE, not an order. 1,774 customer-days have more
    # than one line, which are the separate items of a single order. Anything
    # about "purchase frequency" or "average order value" has to be measured
    # per order, so I aggregate to one row per customer per day first.
    #
    # This is the same mistake-waiting-to-happen as in my e-commerce project:
    # counting rows instead of orders inflates frequency and deflates order
    # value.
    orders = (tx.groupby(["customer_id", "date"], as_index=False)
                .agg(cds=("cds", "sum"), value=("value", "sum"), lines=("value", "size")))
    multi = int((orders.lines > 1).sum())
    log("Transaction lines: {:,}".format(len(tx)))
    log("Orders (one customer, one day): {:,}".format(len(orders)))
    log("  {:,} orders ({:.1%}) have more than one line".format(multi, multi / len(orders)))
    log("")

    # --- customers ---------------------------------------------------------
    orders = orders.sort_values(["customer_id", "date"]).reset_index(drop=True)
    orders["order_number"] = orders.groupby("customer_id").cumcount() + 1
    first = orders.groupby("customer_id", as_index=False).agg(
        first_order_date=("date", "min"), last_order_date=("date", "max"),
        orders=("date", "size"), total_value=("value", "sum"), total_cds=("cds", "sum"))
    first["cohort_month"] = first.first_order_date.dt.to_period("M").astype(str)
    first["avg_order_value"] = (first.total_value / first.orders).round(2)
    first["is_repeat_buyer"] = (first.orders > 1).astype(int)
    first["customer_lifespan_days"] = (first.last_order_date - first.first_order_date).dt.days

    # Months since the customer's first order, for the cohort analysis. Using
    # whole months rather than days keeps the cohort table readable.
    orders = orders.merge(first[["customer_id", "cohort_month", "first_order_date"]],
                          on="customer_id", how="left")
    orders["order_month"] = orders.date.dt.to_period("M").astype(str)
    orders["months_since_first"] = (
        (orders.date.dt.year - orders.first_order_date.dt.year) * 12
        + (orders.date.dt.month - orders.first_order_date.dt.month)
    )

    log("Acquisition cohorts (every customer first bought in Q1 1997):")
    for cohort, count in first.cohort_month.value_counts().sort_index().items():
        log("  {}  {:,} customers".format(cohort, count))
    log("")
    log("Total revenue: ${:,.2f}".format(float(first.total_value.sum())))
    log("Repeat buyers: {:,} of {:,} ({:.1%})".format(
        int(first.is_repeat_buyer.sum()), len(first), float(first.is_repeat_buyer.mean())))
    log("Average orders per customer: {:.2f}".format(float(first.orders.mean())))
    log("Average order value: ${:.2f}".format(float(orders.value.sum() / len(orders))))
    log("Average revenue per customer: ${:.2f}".format(float(first.total_value.mean())))

    tx.to_csv(CLEAN / "transactions.csv", index=False)
    orders.to_csv(CLEAN / "orders.csv", index=False)
    first.to_csv(CLEAN / "customers.csv", index=False)

    db = CLEAN / "cdnow.db"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    tx.assign(date=tx.date.dt.strftime("%Y-%m-%d")).to_sql("transactions", con, index=False)
    orders.assign(date=orders.date.dt.strftime("%Y-%m-%d"),
                  first_order_date=orders.first_order_date.dt.strftime("%Y-%m-%d")
                  ).to_sql("orders", con, index=False)
    first.assign(first_order_date=first.first_order_date.dt.strftime("%Y-%m-%d"),
                 last_order_date=first.last_order_date.dt.strftime("%Y-%m-%d")
                 ).to_sql("customers", con, index=False)
    con.execute("CREATE INDEX idx_orders_customer ON orders(customer_id)")
    con.execute("CREATE INDEX idx_orders_month ON orders(order_month)")
    con.execute("CREATE INDEX idx_customers_cohort ON customers(cohort_month)")
    con.commit()
    con.close()

    log("")
    log("Wrote " + str(CLEAN / "transactions.csv") + " ({:,} rows)".format(len(tx)))
    log("Wrote " + str(CLEAN / "orders.csv") + " ({:,} rows)".format(len(orders)))
    log("Wrote " + str(CLEAN / "customers.csv") + " ({:,} rows)".format(len(first)))
    log("Wrote " + str(db) + " (tables: transactions, orders, customers)")
    (OUT / "cleaning_log.txt").write_text("\n".join(log_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
