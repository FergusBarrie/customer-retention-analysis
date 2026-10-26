"""
Build the charts for the write-up from the query output in outputs/tables/,
and save the cohort retention matrix as a readable pivot table.

Output: outputs/charts/*.png
        outputs/tables/cohort_retention_matrix.csv
        outputs/tables/cohort_cumulative_revenue_matrix.csv

Each chart answers one question, which is written in the chart title. The
colours match the portfolio website so the same chart can appear in both.

Usage: python scripts/03_make_charts.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")                  # no window needed, just write PNG files
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
CHARTS = ROOT / "outputs" / "charts"

NAVY = "#1F3353"
STEEL = "#2E4A72"
PALE = "#8FA6C4"
CLAY = "#C2703D"
INK = "#3C4B5C"
GRID = "#E3E8EE"

# The three cohorts can be compared fairly only up to month 15, because the
# data ends in June 1998 and the March 1997 cohort has nothing after that.
COMPARABLE_MONTHS = 15


def style(ax, title, xlabel="", ylabel=""):
    ax.set_title(title, color=NAVY, fontsize=12, fontweight="bold", pad=12, loc="left")
    ax.set_xlabel(xlabel, color=INK, fontsize=9)
    ax.set_ylabel(ylabel, color=INK, fontsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK, labelsize=9)


def save(fig, name):
    CHARTS.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(CHARTS / name, dpi=150, facecolor="white")
    plt.close(fig)
    print("Wrote", CHARTS / name)


def main():
    retention = pd.read_csv(TABLES / "03_cohort_retention.csv")
    cumulative = pd.read_csv(TABLES / "09_cohort_cumulative_revenue.csv")
    frequency = pd.read_csv(TABLES / "02_purchase_frequency.csv")
    concentration = pd.read_csv(TABLES / "07_revenue_concentration.csv")
    second = pd.read_csv(TABLES / "06_time_to_second_order.csv")
    by_order = pd.read_csv(TABLES / "08_value_by_order_number.csv")
    monthly = pd.read_csv(TABLES / "04_new_vs_returning_by_month.csv")
    segments = pd.read_csv(TABLES / "05_customer_segments.csv")

    # Save the two matrices as readable pivot tables as well.
    rm = retention.pivot(index="cohort_month", columns="months_since_first",
                         values="retention_pct")
    rm.round(2).to_csv(TABLES / "cohort_retention_matrix.csv")
    cm = cumulative.pivot(index="cohort_month", columns="months_since_first",
                          values="cumulative_revenue_per_customer")
    cm.round(2).to_csv(TABLES / "cohort_cumulative_revenue_matrix.csv")
    print("Wrote", TABLES / "cohort_retention_matrix.csv")
    print("Wrote", TABLES / "cohort_cumulative_revenue_matrix.csv")

    cohorts = sorted(retention.cohort_month.unique())
    colours = {c: col for c, col in zip(cohorts, [NAVY, CLAY, PALE])}

    # ---- 1. retention curves, excluding month 0 ------------------------
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for c in cohorts:
        d = retention[(retention.cohort_month == c)
                      & (retention.months_since_first.between(1, COMPARABLE_MONTHS))]
        ax.plot(d.months_since_first, d.retention_pct, marker="o", markersize=3.5,
                linewidth=1.8, color=colours[c], label=c + " cohort")
    style(ax, "Share of each cohort placing an order, by month after their first purchase",
          "Months since first purchase", "% of cohort active")
    ax.set_ylim(0, 18)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    ax.text(0.99, 0.95, "Month 0 is 100% by definition and is left out\nso the rest of the "
                        "curve is readable",
            transform=ax.transAxes, ha="right", va="top", fontsize=8, color="#7A8899")
    save(fig, "01_retention_curves.png")

    # ---- 2. retention heatmap -----------------------------------------
    grid = rm.loc[cohorts, [c for c in rm.columns if c <= COMPARABLE_MONTHS]]
    fig, ax = plt.subplots(figsize=(9, 2.6))
    im = ax.imshow(grid.values, cmap="Blues", aspect="auto", vmin=0, vmax=20)
    ax.set_xticks(range(len(grid.columns)))
    ax.set_xticklabels(grid.columns, fontsize=8)
    ax.set_yticks(range(len(grid.index)))
    ax.set_yticklabels(grid.index, fontsize=9)
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            v = grid.values[i, j]
            ax.text(j, i, "{:.0f}".format(v), ha="center", va="center", fontsize=7.5,
                    color="white" if v > 12 else INK)
    ax.set_title("Cohort retention, % of cohort active each month (month 0 capped for colour)",
                 color=NAVY, fontsize=11, fontweight="bold", loc="left", pad=10)
    ax.set_xlabel("Months since first purchase", color=INK, fontsize=9)
    ax.tick_params(colors=INK, length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    save(fig, "02_retention_heatmap.png")

    # ---- 3. cumulative revenue per acquired customer -------------------
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for c in cohorts:
        d = cumulative[(cumulative.cohort_month == c)
                       & (cumulative.months_since_first <= COMPARABLE_MONTHS)]
        ax.plot(d.months_since_first, d.cumulative_revenue_per_customer, marker="o",
                markersize=3.5, linewidth=1.8, color=colours[c], label=c + " cohort")
    style(ax, "Cumulative revenue per acquired customer",
          "Months since first purchase", "Cumulative revenue ($)")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    ax.text(0.02, 0.95, "Denominator is the whole cohort, including customers\nwho never came back",
            transform=ax.transAxes, ha="left", va="top", fontsize=8, color="#7A8899")
    save(fig, "03_cumulative_revenue_per_customer.png")

    # ---- 4. frequency: customers vs revenue ----------------------------
    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = range(len(frequency))
    width = 0.38
    ax.bar([i - width / 2 for i in x], frequency.pct_of_customers, width,
           color=PALE, label="% of customers")
    ax.bar([i + width / 2 for i in x], frequency.pct_of_revenue, width,
           color=NAVY, label="% of revenue")
    ax.set_xticks(list(x))
    ax.set_xticklabels(frequency.order_band, fontsize=9)
    style(ax, "Orders placed: share of customers against share of revenue", "", "Per cent")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    for i, (cust, rev) in enumerate(zip(frequency.pct_of_customers, frequency.pct_of_revenue)):
        ax.text(i - width / 2, cust + 0.7, "{:.0f}".format(cust), ha="center", fontsize=8, color=INK)
        ax.text(i + width / 2, rev + 0.7, "{:.0f}".format(rev), ha="center", fontsize=8, color=INK)
    save(fig, "04_purchase_frequency.png")

    # ---- 5. revenue concentration --------------------------------------
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(concentration.spend_decile, concentration.pct_of_revenue, color=STEEL,
           label="% of revenue in this decile")
    ax2 = ax.twinx()
    ax2.plot(concentration.spend_decile, concentration.cumulative_pct_of_revenue,
             color=CLAY, marker="o", markersize=4, linewidth=1.8,
             label="cumulative % of revenue")
    ax2.set_ylim(0, 105)
    ax2.set_ylabel("Cumulative % of revenue", color=INK, fontsize=9)
    ax2.tick_params(colors=INK, labelsize=9)
    ax2.spines["top"].set_visible(False)
    style(ax, "Revenue by customer spend decile (1 = highest spenders)",
          "Spend decile, about 2,357 customers each", "% of revenue")
    lines = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
    labels = ax.get_legend_handles_labels()[1] + ax2.get_legend_handles_labels()[1]
    ax.legend(lines, labels, frameon=False, fontsize=9, labelcolor=INK, loc="center right")
    save(fig, "05_revenue_concentration.png")

    # ---- 6. time to second order ---------------------------------------
    fig, ax = plt.subplots(figsize=(8, 4.0))
    labels = [b.split(". ", 1)[1] for b in second.time_to_second_order]
    ax.bar(labels, second.pct_of_repeat_buyers, color=NAVY, width=0.6)
    for i, v in enumerate(second.pct_of_repeat_buyers):
        ax.text(i, v + 0.4, "{:.1f}%".format(v), ha="center", fontsize=8.5, color=INK)
    style(ax, "How long repeat buyers took to place a second order",
          "", "% of repeat buyers")
    save(fig, "06_time_to_second_order.png")

    # ---- 7. drop-off and order value by order number -------------------
    d = by_order.dropna(subset=["drop_off_pct"])
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(d.order_number, d.drop_off_pct, color=PALE, width=0.6,
           label="% who did not order again")
    ax2 = ax.twinx()
    ax2.plot(by_order.order_number, by_order.avg_order_value, color=CLAY, marker="o",
             markersize=4, linewidth=1.8, label="average order value ($)")
    ax2.set_ylabel("Average order value ($)", color=INK, fontsize=9)
    ax2.set_ylim(0, 50)
    ax2.tick_params(colors=INK, labelsize=9)
    ax2.spines["top"].set_visible(False)
    style(ax, "The more someone has already bought, the more likely they buy again",
          "Order number", "% who never placed the next order")
    ax.set_xticks(list(by_order.order_number))
    lines = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
    labels = ax.get_legend_handles_labels()[1] + ax2.get_legend_handles_labels()[1]
    ax.legend(lines, labels, frameon=False, fontsize=9, labelcolor=INK, loc="upper right")
    save(fig, "07_dropoff_by_order_number.png")

    # ---- 8. monthly revenue and active customers -----------------------
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.bar(monthly.order_month, monthly.new_customer_revenue, color=NAVY,
           label="revenue from first orders")
    ax.bar(monthly.order_month, monthly.returning_customer_revenue,
           bottom=monthly.new_customer_revenue, color=PALE,
           label="revenue from repeat orders")
    style(ax, "Monthly revenue, split between first and repeat orders", "", "Revenue ($)")
    ax.set_xticks(range(len(monthly)))
    ax.set_xticklabels(monthly.order_month, rotation=45, ha="right", fontsize=8)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    ax.text(0.99, 0.95, "Everyone in this dataset was acquired in Q1 1997, so there are no\n"
                        "first orders from April 1997 onwards",
            transform=ax.transAxes, ha="right", va="top", fontsize=8, color="#7A8899")
    save(fig, "08_monthly_revenue_split.png")

    # ---- 9. segments ---------------------------------------------------
    seg = segments.sort_values("pct_of_revenue", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 3.8))
    y = range(len(seg))
    height = 0.38
    ax.barh([i + height / 2 for i in y], seg.pct_of_revenue, height, color=NAVY,
            label="% of revenue")
    ax.barh([i - height / 2 for i in y], seg.pct_of_customers, height, color=PALE,
            label="% of customers")
    ax.set_yticks(list(y))
    ax.set_yticklabels(seg.segment, fontsize=9)
    style(ax, "Customer segments: share of customers against share of revenue", "Per cent", "")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK, loc="lower right")
    save(fig, "09_customer_segments.png")


if __name__ == "__main__":
    main()
