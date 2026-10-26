"""
Collect the query results into one JSON file for the portfolio website, and
print the headline figures used in the written findings.

Output: outputs/website_data.json

Usage: python scripts/04_export_for_website.py
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
OUT = ROOT / "outputs" / "website_data.json"

COMPARABLE_MONTHS = 15


def load(name):
    return pd.read_csv(TABLES / name)


def json_safe(obj):
    """Replace NaN/NaT with None so the output is valid JSON.

    pandas writes missing numbers as NaN, which json.dumps happily emits as the
    bare token NaN - valid Python, invalid JSON, and the website build refuses
    to parse it. Walking the payload once at the end is the reliable fix.
    """
    import math
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_safe(v) for v in obj]
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if obj is pd.NaT:
        return None
    return obj


def main():
    overview = load("01_overview.csv").iloc[0]
    frequency = load("02_purchase_frequency.csv")
    retention = load("03_cohort_retention.csv")
    monthly = load("04_new_vs_returning_by_month.csv")
    segments = load("05_customer_segments.csv")
    second = load("06_time_to_second_order.csv")
    concentration = load("07_revenue_concentration.csv")
    by_order = load("08_value_by_order_number.csv")
    cumulative = load("09_cohort_cumulative_revenue.csv")
    cohorts = load("10_repeat_rate_by_cohort.csv")

    # Month-1 retention averaged across the three cohorts, weighted by cohort size.
    m1 = retention[retention.months_since_first == 1]
    m1_weighted = float((m1.active_customers.sum() / m1.cohort_customers.sum()) * 100)

    # Months 6 to 15, which is where the curve has levelled off.
    settled = retention[retention.months_since_first.between(6, COMPARABLE_MONTHS)]
    settled_avg = float((settled.active_customers.sum() / settled.cohort_customers.sum()) * 100)

    # Value of an acquired customer after 15 months, across all three cohorts.
    at15 = cumulative[cumulative.months_since_first <= COMPARABLE_MONTHS]
    value_15m = float(at15.revenue.sum() / cohorts.cohort_customers.sum())
    first_order_value = float(
        cumulative[cumulative.months_since_first == 0].revenue.sum()
        / cohorts.cohort_customers.sum())

    # Bands a, b and c are "within 1 month", "1-2 months" and "2-3 months".
    # Match on the band prefix rather than comparing the label strings, which
    # silently dropped the "c." band the first time I wrote this.
    within_3_months = float(
        second[second.time_to_second_order.str.startswith(("a.", "b.", "c."))]
        .pct_of_repeat_buyers.sum())

    one_time = frequency[frequency.order_band == "1 order"].iloc[0]
    best = segments[segments.segment == "Best customers"].iloc[0]
    top_decile = concentration[concentration.spend_decile == 1].iloc[0]
    top_two_deciles = float(concentration[concentration.spend_decile <= 2].pct_of_revenue.sum())

    headline = {
        "customers": int(overview["customers"]),
        "orders": int(overview["orders"]),
        "revenue": round(float(overview["revenue"]), 2),
        "avg_order_value": round(float(overview["avg_order_value"]), 2),
        "revenue_per_customer": round(float(overview["revenue_per_customer"]), 2),
        "avg_orders_per_customer": round(float(overview["avg_orders_per_customer"]), 2),
        "repeat_buyer_pct": round(float(overview["repeat_buyer_pct"]), 1),
        "one_time_buyer_pct": round(float(one_time.pct_of_customers), 1),
        "one_time_buyer_revenue_pct": round(float(one_time.pct_of_revenue), 1),
        "month1_retention_pct": round(m1_weighted, 1),
        "settled_retention_pct": round(settled_avg, 1),
        "value_per_acquired_customer_15m": round(value_15m, 2),
        "first_order_value": round(first_order_value, 2),
        "first_order_share_of_15m_value_pct": round(first_order_value / value_15m * 100, 1),
        "second_order_within_1_month_pct": round(
            float(second[second.time_to_second_order.str.startswith("a.")].pct_of_repeat_buyers.iloc[0]), 1),
        "second_order_within_3_months_pct": round(within_3_months, 1),
        "top_decile_revenue_pct": round(float(top_decile.pct_of_revenue), 1),
        "top_two_deciles_revenue_pct": round(top_two_deciles, 1),
        "top_decile_avg_spend": round(float(top_decile.avg_spend), 2),
        "best_segment_customer_pct": round(float(best.pct_of_customers), 1),
        "best_segment_revenue_pct": round(float(best.pct_of_revenue), 1),
        "dropoff_after_first_order_pct": round(float(by_order.iloc[0].drop_off_pct), 1),
        "dropoff_after_third_order_pct": round(float(by_order.iloc[2].drop_off_pct), 1),
        "aov_first_order": round(float(by_order.iloc[0].avg_order_value), 2),
        "aov_tenth_order": round(float(by_order[by_order.order_number == 10].avg_order_value.iloc[0]), 2),
        "cohort_repeat_rate_range": "{:.1f}% to {:.1f}%".format(
            float(cohorts.repeat_buyer_pct.min()), float(cohorts.repeat_buyer_pct.max())),
        "comparable_months": COMPARABLE_MONTHS,
    }

    payload = {
        "meta": {
            "project": "Customer behaviour and retention analysis",
            "dataset": "CDNOW master dataset (Fader and Hardie)",
            "dataset_url": "https://www.brucehardie.com/datasets/",
            "description": "The complete purchase history to 30 June 1998 of the 23,570 people "
                           "who made their first ever purchase at the online CD retailer CDNOW "
                           "during the first quarter of 1997.",
            "currency": "USD",
            "note": "The three cohorts can be compared fairly only to month {} because the data "
                    "ends in June 1998.".format(COMPARABLE_MONTHS),
        },
        "headline": headline,
        "cohort_retention": retention.to_dict(orient="records"),
        "cohort_cumulative_revenue": cumulative.to_dict(orient="records"),
        "purchase_frequency": frequency.to_dict(orient="records"),
        "segments": segments.to_dict(orient="records"),
        "time_to_second_order": second.to_dict(orient="records"),
        "revenue_concentration": concentration.to_dict(orient="records"),
        "value_by_order_number": by_order.where(pd.notna(by_order), None).to_dict(orient="records"),
        "monthly": monthly.to_dict(orient="records"),
        "cohort_summary": cohorts.to_dict(orient="records"),
    }
    OUT.write_text(json.dumps(json_safe(payload), indent=2, allow_nan=False),
                   encoding="utf-8")
    print("Wrote", OUT)
    print()
    print("Headline figures for the write-up")
    print("-" * 64)
    for key, value in headline.items():
        print("{:42s} {}".format(key, value))


if __name__ == "__main__":
    main()
