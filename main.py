import requests
import pandas as pd
import matplotlib.pyplot as plt

def fetch_export(item_id: str, start_iso: str, end_iso: str, timezone="EET"):
    base = "https://api-baltic.transparency-dashboard.eu/api/v1/export"
    params = {
        "id": item_id,
        "start_date": start_iso,
        "end_date": end_iso,
        "output_time_zone": timezone,
        "output_format": "json",
        "json_header_groups": 1,
        "download": 0
    }
    resp = requests.get(base, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()

def parse_export_json(js):
    """
    Parses the JSON from the Baltic TSO API and returns a DataFrame
    with timestamps as index and columns for each country.
    """
    if "data" not in js:
        raise ValueError("JSON does not contain 'data' key")
    
    data = js["data"]
    timeseries = data.get("timeseries", [])
    columns = [col["group_level_0"] for col in data.get("columns", [])]

    # Build rows
    rows = []
    for ts in timeseries:
        ts_time = pd.to_datetime(ts["_from"])  # local timestamp
        row = [ts_time] + ts["values"]
        rows.append(row)
    
    df = pd.DataFrame(rows, columns=["timestamp"] + columns)
    df.set_index("timestamp", inplace=True)
    return df

def analyze_day(date_str: str):
    # date_str like "2025-09-22"
    start_iso = f"{date_str}T00:00:00"
    end_iso   = f"{date_str}T23:59:59"
    print("Fetching aFRR activation...")
    js_afrr = fetch_export("activations_afrr", start_iso, end_iso)
    s_afrr = parse_export_json(js_afrr)
    print("Fetching imbalance volumes...")
    js_imb = fetch_export("imbalance_volumes_v2", start_iso, end_iso)
    s_imb = parse_export_json(js_imb)

    # Align to 15-min intervals
    s_afrr_q = s_afrr.resample("15min").mean()
    s_imb_q  = s_imb.resample("15min").mean()

    # Compute diagnostics
    # Align to 15-min intervals
    s_afrr_q = s_afrr.resample("15min").mean()  # updated per FutureWarning
    s_imb_q  = s_imb.resample("15min").mean()

    if s_afrr_q.empty or s_imb_q.empty:
        print("No data returned for aFRR or imbalance on", date_str)
        return  # stop here

    # Compute diagnostics
    df = pd.DataFrame({
        "afrr_MW": s_afrr_q.iloc[:, 0],      # use first column if multiple
        "imbalance_MW": s_imb_q.iloc[:, 0]   # same here
    }).dropna(how="all")

    df["imbalance_abs_MWh"] = df["imbalance_MW"].abs() * 0.25
    df["afrr_MWh"] = df["afrr_MW"] * 0.25
    total_imb = df["imbalance_abs_MWh"].sum()
    total_afrr = df["afrr_MWh"].sum()
    ratio = total_afrr / total_imb if total_imb > 0 else float("nan")
    corr = df["afrr_MW"].corr(df["imbalance_MW"].abs())
    print("Metrics for", date_str)
    print("  total imbalance (MWh):", total_imb)
    print("  total aFRR (MWh):", total_afrr)
    print("  ratio aFRR / imbalance:", ratio)
    print("  corr( aFRR , |imbalance| ): ", corr)

    # Plot
    fig, ax1 = plt.subplots(figsize=(12,5))
    ax1.plot(df.index, df["imbalance_MW"], label="imbalance (MW)")
    ax1.axhline(0, color="k", linestyle="--", linewidth=0.5)
    ax1.set_ylabel("Imbalance (MW)")
    ax1.set_xlabel("Time")

    ax2 = ax1.twinx()
    ax2.plot(df.index, df["afrr_MW"], label="aFRR activation (MW)", color="C1")
    ax2.set_ylabel("aFRR (MW)")

    # Combine legends
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left")

    plt.title(f"aFRR vs Imbalance — {date_str}")
    plt.tight_layout()
    plt.savefig(f"afrr_vs_imbalance_{date_str}.png", dpi=150)
    plt.close(fig)
    print("Saved plot to file:", f"afrr_vs_imbalance_{date_str}.png")

    js_cb = fetch_export("current_balancing_state_v2", start_iso, end_iso)
    df_cb = parse_export_json(js_cb)

    print(df_cb.head())

if __name__ == "__main__":
    analyze_day("2025-09-22")
