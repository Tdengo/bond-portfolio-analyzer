# Bond Risk & Portfolio Analyzer

## Overview
This is a Python-based interactive financial dashboard designed to evaluate interest rate risk, model price-yield, and manage liquidity for municipal bond portfolios.

This tool was built to replicate the daily analytical needs of a fixed-income portfolio

## Key Features
* **Single Bond Analytics:** Calculates Present Value, Tax-Equivalent Yield (TEY), Macaulay Duration, and Modified Duration based on user-defined market parameters
* **Price-Yield & Convexity Visualization:** Utilizes Plotly to graph the true convex price-yield curve against the linear duration estimate, visually demonstrating the limitations of duration for large rate shifts
* **Interest Rate Stress Testing:** Automatically simulates ±50, 100, and 200 basis point (bps) interest rate shocks, calculating exact dollar and percentage value-at-risk (VaR) for both individual bonds and the aggregate portfolio
* **Dynamic Portfolio Management:** Features an editable, Excel-style data grid allowing users to build a custom portfolio of bonds
* **Cash Flow Laddering:** Automatically aggregates coupon payments and principal maturities across the entire portfolio, generating a stacked bar chart to visualize future liquidity

## Tech Stack
* **Language:** Python
* **Frontend/Framework:** Streamlit
* **Data & Math:** Pandas, NumPy, NumPy-Financial
* **Data Visualization:** Plotly Express

https://bond-portfolio-analyzer-kc3uwh6cc5tqtyk34scswn.streamlit.app/
