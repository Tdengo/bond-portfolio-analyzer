import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.express as px

# Set Page Layout
st.set_page_config(page_title="Risk Calculator for Municipal Bonds", layout="wide")

st.title("Bond Risk & TEY")
st.markdown("Analyze municipal bond tax-equivalent yields, interest rate risk (Duration), and pricing type")

# --- Sidebar for Single Bond & Market Parameters ---
st.sidebar.header("Market & Single Bond Analysis")
face_value = st.sidebar.number_input("Face Value ($)", value=1000)
coupon_rate = st.sidebar.slider("Coupon Rate (%)", 0.0, 10.0, 4.0) / 100
years_to_maturity = st.sidebar.slider("Years to Maturity", 1, 30, 10)
current_yield = st.sidebar.slider("Current Market Yield (%)", 1.0, 15.0, 4.0) / 100

tax_rate = st.sidebar.number_input("Corporate Tax Rate (%)", value=21.0) / 100




# --- Math & Logic ---
periods = years_to_maturity * 2  # Assuming semi-annual payments
rate_per_period = current_yield / 2
coupon_pmt = (face_value * coupon_rate) / 2

# 1. Current Price
current_price = npf.pv(rate_per_period, periods, coupon_pmt, face_value) * -1

# 2. Pricing Type (Premium, Par, Discount)
if round(current_price, 2) > face_value:
    delta_text = "Premium"
elif round(current_price, 2) < face_value:
    delta_text = "- Discount"
else:
    delta_text = "Par"

# 3. Macaulay and Modified Duration
# Create arrays for cash flows and time periods
times = np.arange(1, periods + 1)
cash_flows = np.full(periods, coupon_pmt)
cash_flows[-1] += face_value  # Add principal repayment to the final period

# Calculate PV of each cash flow
pv_cash_flows = cash_flows / ((1 + rate_per_period) ** times)

# Macaulay Duration (in half-years, so divide by 2 for years)
mac_duration = np.sum((times * pv_cash_flows) / current_price) / 2
# Modified Duration
mod_duration = mac_duration / (1 + rate_per_period)

# 4. Tax Equivalent Yield
tey = current_yield / (1 - tax_rate)

# --- Plotting the Curves ---
yields = np.linspace(0.01, 0.15, 100)
true_prices = []
duration_estimates = []

for y in yields:
    # A. True Price Curve (Exact calculation)
    price = npf.pv(y / 2, periods, coupon_pmt, face_value) * -1
    true_prices.append(price)

    # B. Duration Estimate Line (Linear tangent line approximation)
    yield_change = y - current_yield
    # Formula: Estimated Price = Current Price * (1 - Mod_Duration * Change_in_Yield)
    est_price = current_price * (1 - mod_duration * yield_change)
    duration_estimates.append(est_price)

# --- Single Bond Rate Shock Math ---
shocks_bps = [-200, -100, -50, 50, 100, 200]
sb_shock_data = []

for bps in shocks_bps:
    shocked_yield = max(0.0001, current_yield + (bps / 10000))  # Prevent negative yields
    shocked_price = npf.pv(shocked_yield / 2, periods, coupon_pmt, face_value) * -1

    sb_shock_data.append({
        "Rate Shock": f"{bps:+} bps",
        "New Yield": shocked_yield,
        "New Price": shocked_price,
        "Dollar Impact": shocked_price - current_price,
        "% Impact": (shocked_price - current_price) / current_price
    })

sb_shock_df = pd.DataFrame(sb_shock_data)


# Function to color table text red/green
def color_impact(val):
    color = 'salmon' if val < 0 else 'lightgreen'
    return f'color: {color}'

# Create a DataFrame for Streamlit charting
chart_data = pd.DataFrame({
    'Yield (%)': yields * 100,
    'True Price': true_prices,
    'Duration Estimate': duration_estimates
}).set_index('Yield (%)')

# --- UI Display ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Key Metrics for Single Bond Analysis")
    # Display the Pricing Type as the "delta" below the price
    if delta_text == "Par":
        st.metric("Current Bond Price", f"${current_price:,.2f}", delta_text, delta_color = "off")
    else:
        st.metric("Current Bond Price", f"${current_price:,.2f}", delta_text)
    st.metric("Modified Duration", f"{mod_duration:.2f} Years", "Price risk metric", delta_color="off")
    st.metric("Tax-Equivalent Yield (TEY)", f"{(tey * 100):.2f}%")
    st.markdown("##### Interest Rate Stress Test")
    styled_sb_df = sb_shock_df.style.map(color_impact, subset=['Dollar Impact', '% Impact']).format(
        {"New Yield": "{:.2%}", "New Price": "${:,.2f}", "Dollar Impact": "${:+,.2f}", "% Impact": "{:+.2%}"}
    )
    st.dataframe(styled_sb_df, hide_index=True, use_container_width=True)

with col2:
    st.subheader("Price-Yield Curve vs. Duration")
    fig = px.line(chart_data)
    fig.update_traces(line = dict(color = "cornflowerblue"), selector = dict (name = "True Price"))
    fig.update_traces(line = dict(dash = "5, 3", color = "salmon"), selector = dict (name = "Duration Estimate"))
    fig.add_scatter(
        x = [current_yield * 100],
        y = [current_price],
        mode = 'markers',
        marker = dict(size = 8, color = 'white', line = dict(width = 3, color = 'darkcyan')),
        name = 'Current Price'
    )
    st.plotly_chart(fig, use_container_width = True)
    st.caption(
        "The True Price is curved (convexity), while the Duration Estimate is a straight line. The gap shows why duration is only highly accurate for small rate changes.")


# 5. Cash Flow Ladder Data
## --- Aggregate Cash Flow Ladder Math ---
# Find the longest maturity in the portfolio to know how many years to plot

# --- Portfolio Input (The Excel-Like Table) ---
st.subheader("Portfolio Holdings")
st.markdown("Add, edit, or delete bonds in the table below")

# Create a default starting portfolio so the app isn't empty
default_portfolio = pd.DataFrame({
    "Bond Name": ["New York Muni A", "Local School Dist B", "Water Utility C"],
    "Face Value ($)": [1000, 600, 1200],
    "Coupon Rate (%)": [4.0, 3.5, 5.0],
    "Years to Maturity": [5, 10, 3],
    "Yield to Maturity (%)": [4.0, 3.8, 4.5]
})

# st.data_editor is the magic function that lets the user add as many rows as they want
portfolio_df = st.data_editor(
    default_portfolio,
    num_rows="dynamic", # This adds the "Add Row" button!
    use_container_width=True,
    hide_index=True
)
portfolio_df = portfolio_df.dropna()

if not portfolio_df.empty:
    max_years = int(portfolio_df["Years to Maturity"].max())
else:
    max_years = 1

ladder_years = np.arange(1, max_years + 1)

# Create empty arrays to hold the total combined cash flows
total_interest = np.zeros(max_years)
total_principal = np.zeros(max_years)

# Loop through every single bond in the user's table
for index, row in portfolio_df.iterrows():
    # Extract the data for this specific bond
    face = row["Face Value ($)"]
    coupon = row["Coupon Rate (%)"] / 100
    ytm = int(row["Years to Maturity"])

    annual_pmt = face * coupon

    # Add this bond's interest to the total for every year it is active
    total_interest[:ytm] += annual_pmt

    # Add this bond's principal to the exact year it matures
    # (ytm - 1 because Python arrays start at index 0)
    total_principal[ytm - 1] += face

# Build the final combined DataFrame
cf_data = pd.DataFrame({
    'Year': ladder_years,
    'Interest (Coupon)': total_interest,
    'Principal': total_principal
})


# --- Cash Flow Ladder Display ---
st.divider()  # Adds a clean horizontal line to separate the sections
st.subheader("Expected Cash Flow Ladder")

# --- Portfolio Rate Shock Math ---
port_shock_data = []

if not portfolio_df.empty:
    for bps in shocks_bps:
        base_port_value = 0
        shocked_port_value = 0

        for index, row in portfolio_df.iterrows():
            f = row["Face Value ($)"]
            c_pmt = (f * (row["Coupon Rate (%)"] / 100)) / 2
            per = int(row["Years to Maturity"]) * 2
            base_y = row["Yield to Maturity (%)"] / 100

            shock_y = max(0.0001, base_y + (bps / 10000))

            # Sum up the PVs of all bonds in the portfolio
            base_port_value += npf.pv(base_y / 2, per, c_pmt, f) * -1
            shocked_port_value += npf.pv(shock_y / 2, per, c_pmt, f) * -1

        port_shock_data.append({
            "Rate Shock": f"{bps:+} bps",
            "Portfolio Value": shocked_port_value,
            "Dollar Impact": shocked_port_value - base_port_value,
            "% Impact": (shocked_port_value - base_port_value) / base_port_value
        })

    port_shock_df = pd.DataFrame(port_shock_data)

    # --- Portfolio Stress Test UI ---
    st.markdown("#### Aggregate Portfolio Stress Test")
    styled_port_df = port_shock_df.style.map(color_impact, subset=['Dollar Impact', '% Impact']).format(
        {"Portfolio Value": "${:,.2f}", "Dollar Impact": "${:+,.2f}", "% Impact": "{:+.2%}"}
    )
    st.dataframe(styled_port_df, hide_index=True, use_container_width=True)
    st.write("")  # Adds a little blank space before the ladder chart

# Create a stacked bar chart using Plotly
fig_cf = px.bar(
    cf_data,
    x='Year',
    y=['Interest (Coupon)', 'Principal'],
    labels={'value': 'Cash Flow ($)', 'variable': 'Payment Type'},
    color_discrete_map={'Interest (Coupon)': 'cornflowerblue', 'Principal': 'salmon'}
)

# Force the X-axis to show every single year cleanly
fig_cf.update_layout(
    barmode='stack',
    xaxis=dict(tickmode='linear', tick0=1, dtick=1),
    hovermode="x unified"
)

st.plotly_chart(fig_cf, use_container_width=True)
st.caption("This ladder visualizes the bond's predictable liquidity. The blue bars represent steady income, while the massive spike in the final year represents the return of the initial principal.")