import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.title("📊 Behavioral Analysis & Stress Testing Dashboard")

st.markdown("""
Upload your portfolio CSV file to analyze trading behaviors and perform stress testing.
You can customize the thresholds for behavioral flags using the controls below.
""")

# Downloadable template CSV
def get_template():
    data = {
        "Ticker": ["AAPL", "TSLA", "MSFT"],
        "Buy Date": ["2023-01-01", "2023-02-15", "2023-03-10"],
        "Sell Date": ["2023-01-15", "2023-03-01", "2023-04-01"],
        "Buy Price": [150, 800, 280],
        "Sell Price": [140, 600, 300],
        "Quantity": [10, 5, 8]
    }
    df = pd.DataFrame(data)
    return df

def convert_df_to_bytes(df):
    output = BytesIO()
    df.to_csv(output, index=False)
    return output.getvalue()

st.download_button(
    label="📥 Download CSV Template",
    data=convert_df_to_bytes(get_template()),
    file_name='portfolio_template.csv',
    mime='text/csv'
)

uploaded_file = st.file_uploader("Upload your portfolio CSV", type=["csv"])

st.sidebar.header("Behavioral Analysis Settings")
drop_threshold = st.sidebar.slider(
    "Select drop threshold (%) for major fall",
    min_value=1,
    max_value=50,
    value=20,
    step=1,
    help="If the stock falls more than this % from buy price, it triggers a behavioral flag."
)
short_holding_days = st.sidebar.number_input(
    "Max holding period (days) to consider 'sold early'",
    min_value=1,
    max_value=365,
    value=30,
    step=1
)

def behavioral_analysis(df, drop_thresh, max_holding):
    df["Buy Date"] = pd.to_datetime(df["Buy Date"])
    df["Sell Date"] = pd.to_datetime(df["Sell Date"])
    df["Holding Period"] = (df["Sell Date"] - df["Buy Date"]).dt.days
    df["Return %"] = (df["Sell Price"] - df["Buy Price"]) / df["Buy Price"] * 100
    df["Major Fall"] = (df["Return %"] < -drop_thresh)
    df["Sold Early"] = (df["Holding Period"] < max_holding)
    df["Behavioral Flag"] = np.where(df["Major Fall"] & df["Sold Early"], "🚩 Major Fall & Sold Early",
                             np.where(df["Major Fall"], "⚠️ Major Fall",
                             np.where(df["Sold Early"], "⚠️ Sold Early", "✅ No Major Flags")))
    return df

def stress_testing(df):
    # Simple stress test: What if price drops 10%, 20%, 30% from buy price?
    stress_scenarios = [10, 20, 30]
    results = {}
    for scenario in stress_scenarios:
        df[f"Return if -{scenario}%"] = ((df["Buy Price"] * (1 - scenario / 100)) - df["Buy Price"]) / df["Buy Price"] * 100
        results[f"-{scenario}% Drop"] = df[f"Return if -{scenario}%"].sum()
    return results

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.subheader("Uploaded Portfolio Data")
        st.dataframe(df)

        # Run behavioral analysis
        analyzed_df = behavioral_analysis(df, drop_threshold, short_holding_days)
        st.subheader("Behavioral Analysis Results")
        st.dataframe(analyzed_df[["Ticker", "Return %", "Holding Period", "Behavioral Flag"]])

        # Summary stats
        flags_count = analyzed_df["Behavioral Flag"].value_counts()
        st.markdown("### Summary of Behavioral Flags")
        for flag, count in flags_count.items():
            st.write(f"{flag}: **{count}** trades")

        # Stress testing results
        st.subheader("Stress Testing Summary")
        stress_results = stress_testing(df)
        for scenario, total_return in stress_results.items():
            st.write(f"Total portfolio return if all prices drop by {scenario}: **{total_return:.2f}%**")

        # Engaging feedback
        st.subheader("Intelligent Feedback")
        if (analyzed_df["Behavioral Flag"] == "🚩 Major Fall & Sold Early").any():
            st.warning("🚩 Some trades show major drops combined with short holding periods — this could indicate panic selling or emotional trading.")
        else:
            st.success("No major behavioral red flags detected. Keep up the disciplined trading!")

    except Exception as e:
        st.error(f"Error processing the file: {e}")
else:
    st.info("Please upload your portfolio CSV file to begin the analysis.")

