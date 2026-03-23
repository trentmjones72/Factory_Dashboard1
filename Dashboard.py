import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Factory Efficiency Dashboard", layout="wide")

st.title("Factory Efficiency Dashboard")
st.write(
    "An interactive dashboard for tracking manufacturing performance, downtime, scrap, "
    "and bottlenecks across production lines."
)

# ----------------------------
# Create sample dataset
# ----------------------------
np.random.seed(42)

dates = pd.date_range("2026-03-01", periods=30)
lines = ["Line A", "Line B", "Line C"]
downtime_causes = ["Maintenance", "Material Shortage", "Equipment Failure", "Changeover"]

rows = []
for date in dates:
    for line in lines:
        target_output = np.random.randint(950, 1100)
        actual_output = target_output - np.random.randint(0, 180)
        downtime = np.random.randint(15, 140)
        scrap_rate = np.random.uniform(1.0, 5.0)
        cause = np.random.choice(downtime_causes)
        runtime = 480 - downtime  # assume 480 min shift

        rows.append({
            "Date": date,
            "Line": line,
            "Target Output": target_output,
            "Actual Output": actual_output,
            "Downtime (min)": downtime,
            "Scrap Rate (%)": scrap_rate,
            "Downtime Cause": cause,
            "Runtime (min)": runtime
        })

df = pd.DataFrame(rows)

df["Efficiency (%)"] = df["Actual Output"] / df["Target Output"] * 100
df["Availability (%)"] = df["Runtime (min)"] / 480 * 100
df["Quality (%)"] = 100 - df["Scrap Rate (%)"]

# Simple OEE-style approximation
df["OEE (%)"] = (
    (df["Availability (%)"] / 100)
    * (df["Efficiency (%)"] / 100)
    * (df["Quality (%)"] / 100)
    * 100
)

# ----------------------------
# Sidebar filters
# ----------------------------
st.sidebar.header("Filters")

selected_lines = st.sidebar.multiselect(
    "Select Production Line(s)",
    options=lines,
    default=lines
)

selected_causes = st.sidebar.multiselect(
    "Select Downtime Cause(s)",
    options=downtime_causes,
    default=downtime_causes
)

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(df["Date"].min().date(), df["Date"].max().date())
)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = df["Date"].min().date()
    end_date = df["Date"].max().date()

filtered_df = df[
    (df["Line"].isin(selected_lines)) &
    (df["Downtime Cause"].isin(selected_causes)) &
    (df["Date"].dt.date >= start_date) &
    (df["Date"].dt.date <= end_date)
]

if filtered_df.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

# ----------------------------
# KPI section
# ----------------------------
avg_efficiency = filtered_df["Efficiency (%)"].mean()
avg_oee = filtered_df["OEE (%)"].mean()
total_downtime = filtered_df["Downtime (min)"].sum()
avg_scrap = filtered_df["Scrap Rate (%)"].mean()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Average Efficiency", f"{avg_efficiency:.1f}%")
k2.metric("Average OEE", f"{avg_oee:.1f}%")
k3.metric("Total Downtime", f"{total_downtime:.0f} min")
k4.metric("Average Scrap Rate", f"{avg_scrap:.2f}%")

# ----------------------------
# Aggregate data for charts
# ----------------------------
daily_summary = (
    filtered_df.groupby("Date", as_index=False)
    .agg({
        "Actual Output": "sum",
        "Target Output": "sum",
        "Downtime (min)": "sum",
        "OEE (%)": "mean"
    })
)

downtime_summary = (
    filtered_df.groupby("Downtime Cause", as_index=False)["Downtime (min)"]
    .sum()
    .sort_values("Downtime (min)", ascending=False)
)

line_summary = (
    filtered_df.groupby("Line", as_index=False)
    .agg({
        "Actual Output": "sum",
        "Downtime (min)": "sum",
        "Scrap Rate (%)": "mean",
        "OEE (%)": "mean"
    })
)

# ----------------------------
# Charts
# ----------------------------
st.subheader("Production Output Over Time")
fig1, ax1 = plt.subplots(figsize=(10, 4))
ax1.plot(daily_summary["Date"], daily_summary["Actual Output"], marker="o", label="Actual Output")
ax1.plot(daily_summary["Date"], daily_summary["Target Output"], marker="o", linestyle="--", label="Target Output")
ax1.set_xlabel("Date")
ax1.set_ylabel("Units Produced")
ax1.legend()
plt.xticks(rotation=45)
st.pyplot(fig1)

st.subheader("Downtime by Cause")
fig2, ax2 = plt.subplots(figsize=(8, 4))
ax2.bar(downtime_summary["Downtime Cause"], downtime_summary["Downtime (min)"])
ax2.set_xlabel("Downtime Cause")
ax2.set_ylabel("Downtime (min)")
plt.xticks(rotation=20)
st.pyplot(fig2)

st.subheader("Average OEE by Line")
fig3, ax3 = plt.subplots(figsize=(8, 4))
ax3.bar(line_summary["Line"], line_summary["OEE (%)"])
ax3.set_xlabel("Production Line")
ax3.set_ylabel("OEE (%)")
st.pyplot(fig3)

# ----------------------------
# Bottleneck detection
# ----------------------------
st.subheader("Bottleneck Analysis")

worst_line = line_summary.sort_values("OEE (%)").iloc[0]
top_downtime_cause = downtime_summary.iloc[0]

st.write(
    f"**Primary bottleneck:** {worst_line['Line']} is currently the weakest-performing line "
    f"with an average OEE of **{worst_line['OEE (%)']:.1f}%**."
)

st.write(
    f"**Largest downtime driver:** {top_downtime_cause['Downtime Cause']} accounts for "
    f"**{top_downtime_cause['Downtime (min)']:.0f} minutes** of downtime in the selected period."
)

# ----------------------------
# Simple recommendation engine
# ----------------------------
st.subheader("Recommended Actions")

recommendations = []

if worst_line["OEE (%)"] < 75:
    recommendations.append(
        f"Investigate {worst_line['Line']} first, as its OEE is below 75%."
    )

if top_downtime_cause["Downtime Cause"] == "Equipment Failure":
    recommendations.append(
        "Prioritize preventive maintenance and inspection schedules to reduce equipment-related downtime."
    )
elif top_downtime_cause["Downtime Cause"] == "Material Shortage":
    recommendations.append(
        "Review inventory planning and material delivery timing to reduce supply interruptions."
    )
elif top_downtime_cause["Downtime Cause"] == "Changeover":
    recommendations.append(
        "Standardize and shorten changeover procedures to improve line availability."
    )
elif top_downtime_cause["Downtime Cause"] == "Maintenance":
    recommendations.append(
        "Review maintenance planning to reduce unplanned intervention during production hours."
    )

if avg_scrap > 3.5:
    recommendations.append(
        "Scrap rate is elevated. Review quality control checkpoints and process stability."
    )

if avg_efficiency < 90:
    recommendations.append(
        "Production efficiency is below target. Check for minor stoppages, line speed losses, or operator delays."
    )

if not recommendations:
    recommendations.append(
        "Performance is stable in the selected period. Continue monitoring key downtime and quality trends."
    )

for rec in recommendations:
    st.write(f"- {rec}")

# ----------------------------
# Detailed data table
# ----------------------------
st.subheader("Detailed Performance Data")
st.dataframe(filtered_df, use_container_width=True)

# ----------------------------
# Download filtered data
# ----------------------------
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Filtered Data as CSV",
    data=csv,
    file_name="factory_efficiency_filtered.csv",
    mime="text/csv"
)