import streamlit as st
import pandas as pd

st.title("Behavioral & Stress Testing Portfolio Analyzer")

# Sample CSV template
sample_csv = """Ticker,Buy Date,Sell Date,Buy Price,Sell Price,Shares
AAPL,2023-01-01,2023-03-01,150,170,10
MSFT,2023-02-01,2023-04-01,280,240,5
GOOG,2023-01-15,2023-03-15,2500,2300,2
"""

st.download_button(
    label="Download CSV Template",
    data=sample_csv,
    file_name="portfolio_template.csv",
    mime="text/csv"
)

st.write("---")

uploaded_file = st.file_uploader("Upload your portfolio CSV", type=["csv"])

def behavioral_analysis(df):
    feedback = []
    # Example behavior checks:
    for idx, row in df.iterrows():
        ret_pct = ((row['Sell Price'] - row['Buy Price']) / row['Buy Price']) * 100
        holding_period = (pd.to_datetime(row['Sell Date']) - pd.to_datetime(row['Buy Date'])).days
        
        # Flag 1: Sold early on big gains? Maybe fear-driven.
        if ret_pct > 15 and holding_period < 30:
            feedback.append(f"Sold {row['Ticker']} early despite >15% gain in less than 30 days — possible fear of losing profits.")
        
        # Flag 2: Sold at loss very quickly? Impulsive behavior.
        if ret_pct < -5 and holding_period < 15:
            feedback.append(f"Quickly sold {row['Ticker']} at a loss >5% within {holding_period} days — might be panic selling.")

        # Flag 3: Holding losing stocks too long? Possibly hope bias.
        if ret_pct < 0 and holding_period > 90:
            feedback.append(f"Held {row['Ticker']} for over 90 days at a loss — could be holding onto losing stocks too long.")

    return feedback

def stress_test(df):
    # Simple stress test: Calculate portfolio loss if all stocks drop 10%, 20%, 30%
    results = {}
    total_value = (df['Sell Price'] * df['Shares']).sum()
    
    for drop in [0.10, 0.20, 0.30]:
        stressed_value = total_value * (1 - drop)
        loss = total_value - stressed_value
        results[f"{int(drop*100)}% drop"] = {'Portfolio Value': stressed_value, 'Loss': loss}
    
    return results

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.write("### Uploaded Portfolio")
        st.dataframe(df)

        # Behavioral analysis
        st.write("### Behavioral Analysis Feedback")
        feedback = behavioral_analysis(df)
        if feedback:
            for f in feedback:
                st.warning(f)
        else:
            st.success("No major behavioral flags detected!")

        # Stress Testing
        st.write("### Stress Testing Results")
        stress_results = stress_test(df)
        stress_df = pd.DataFrame(stress_results).T
        stress_df['Portfolio Value'] = stress_df['Portfolio Value'].apply(lambda x: f"${x:,.2f}")
        stress_df['Loss'] = stress_df['Loss'].apply(lambda x: f"${x:,.2f}")
        st.table(stress_df)

        # Summary feedback based on stress test
        if max([r['Loss'] for r in stress_results.values()]) > (0.25 * (df['Sell Price'] * df['Shares']).sum()):
            st.error("Warning: Portfolio may face significant losses in severe market downturns.")
        else:
            st.info("Portfolio loss under stress scenarios is within acceptable limits.")

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Upload a CSV file to analyze your portfolio.")
