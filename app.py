import streamlit as st
import pandas as pd
from src import config, data_loader, indicators, plotter, ai_analysis, pdf_generator
import tempfile
import base64
import os

# Set Up Streamlit App UI 
st.set_page_config(page_title="AI Technical Analysis", layout="wide")   # Page layout set to full width
st.title("Technical Stock Analysis Dashboard")  # Displays the title at the top
st.sidebar.header("Configuration")  # Header in the sidebar

# Sidebar Input 
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL):", config.DEFAULT_TICKER)
start_date = st.sidebar.date_input("Start Date", value=config.DEFAULT_START_DATE)
end_date = st.sidebar.date_input("End Date", value=config.DEFAULT_END_DATE)

show_rsi = st.sidebar.toggle("Show RSI", value=True)
show_macd = st.sidebar.toggle("Show MACD", value=True)

# Strategy Selection 
analysis_type = st.sidebar.selectbox(
    "Select Analysis Type:", 
    ["Options Trading Strategy", "Buy/Hold/Sell Recommendation"])

# If Options Strategy is selected, provide further options 
# option_strategy = None
# if analysis_type == "Options Trading Strategy":
#     option_strategy = st.sidebar.selectbox(
#         "Select Options Strategy:", 
#         ["Straddle", "Vertical Spread", "Iron Condor", "Covered Call", "Protective Put"])

# Fetch and Store Stock Data 
if st.sidebar.button("Fetch Data"):
    data = data_loader.fetch_stock_data(ticker, start_date, end_date)
    st.session_state["stock_data"] = data
    st.success("Stock data loaded successfully!")

# Check if Data is Available 
if "stock_data" in st.session_state:
    data = indicators.calculate_indicators(st.session_state["stock_data"])
    # Sidebar: Select Technical Indicators
    selected_indicators = st.sidebar.multiselect(
        "Select Indicators:",
        ["20-Day SMA", "50-Day SMA", "20-Day EMA", "50-Day EMA", "Implied Volatility", "Bollinger Bands", "VWAP"],
        default=["20-Day SMA"]
    )
    # Final Chart Formatting and Display 
    fig = plotter.create_chart(data, selected_indicators, show_rsi, show_macd)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("AI-Powered Analysis")
    if st.button("Run AI Analysis"):
        with st.spinner("Analyzing the chart, please wait..."):
            # Choose prompt based on analysis type 
            if analysis_type == "Options Trading Strategy":
                prompt = """
                Prompt:
                    You are a professional Options Trader and Technical Analyst. Analyze the provided stock chart and technical indicators. 
                Instructions:
                    1. Base you recommendation strictly on the technical data: candlestick chart, SMA, EMA, RSI, MACD, Bollinger Bands, Implied Volatility (IV), and Volume
                    2. Start by stating:
                        - Recommended options strategy (e.g., Iron Condor, Call Spread, Put Spread, Covered Call, Protective Put)
                        - Whether to enter the trade (Yes or No), based only on technical evidence.
                    3. Then , explain:
                        - Why the selected strategy fits the current technical setup.
                        - Suggested strick prices and expiration date, using support/resistance and current price action.
                        - Risk/reward profile: potential gain vs. max loss, ideal entry/exit points.
                        - Technical indicators that support the strategy (e.g., RSI > 70 = overbought, MACD crossover, IV rising, Volume)
                Guidelines:
                    - Be concise, professional, and evidence-based.
                    - Do not recommend a trade unless indicators show clear confirmation
                """
            else:
                prompt = """
                You are a Stock Trader specializing in Technical Analysis at a top financial institution. Analyze the stock chart's technical indicators and provide a buy/hold/sell recommendation. Base your recommendation only on the candlestick chart and the displayed technical indicators. First, provide the recommendation, then, provide your detailed reasoning.
                """
            
            # Run AI Analysis
            analysis, chart_path = ai_analysis.run_ai_analysis(fig, prompt)

            # Display Ai Analysis Results 
            st.write("**AI Analysis Results:**")
            st.write(analysis)

            # PDF Report 
            pdf = pdf_generator.PDF()
            pdf.add_page()
            pdf.add_chart(chart_path)
            pdf.add_analysis_text(analysis)

            # Save to a temporary file 
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
                pdf.output(tmp_pdf.name)
                pdf_file_path = tmp_pdf.name

            # Show the PDF preview in iframe 
            with open(pdf_file_path, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600px" type="application/pdf"></iframe>'
                st.markdown("### 📄 Preview AI Analysis Report")
                st.markdown(pdf_display, unsafe_allow_html=True)

            with open(pdf_file_path, "rb") as f:
                st.download_button(
                    label="⬇️Download PDF",
                    data=f.read(),
                    file_name=f'{ticker}_analysis.pdf',
                    mime="application/pdf"
                )

            # Clean up temporary file 
            os.remove(chart_path)
            os.remove(pdf_file_path)
