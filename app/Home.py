"""CryptoLens home page. Run from the repo root:  streamlit run app/Home.py"""

import streamlit as st

from components import loaders
from components.sidebar import setup
from config import ASSET_NAMES

asset = setup("CryptoLens", icon="🔍")

st.markdown(
    "**Predicting 7-day cryptocurrency volatility risk and market regimes, "
    "with transparent DataFacts behind every prediction.**\n\n"
    "Rather than forecasting prices, CryptoLens asks a narrower question: *is this asset "
    "likely to enter a high-volatility week?* It also asks whether blockchain activity "
    "improves that prediction beyond market data alone."
)

master, preds, regimes, metrics = (loaders.master(), loaders.predictions(),
                                   loaders.regimes(), loaders.metrics())

st.subheader(f"Snapshot: {ASSET_NAMES[asset]}")
c1, c2, c3 = st.columns(3)

if master is not None:
    m = master[master["asset"] == asset].sort_values("date")
    last, prev = m.iloc[-1], m.iloc[-8]
    price = last["close"]
    c1.metric("Last close (USDT)", f"{price:,.2f}" if price >= 1 else f"{price:.4f}",
              f"{last['close'] / prev['close'] - 1:+.1%} vs. 7 days ago")

if preds is not None and metrics is not None:
    final = metrics["final_model"]
    p = preds[(preds["asset"] == asset) & (preds["model"] == final["model"])]
    fs = final["feature_set"] if (p["feature_set"] == final["feature_set"]).any() else "market"
    p = p[p["feature_set"] == fs].sort_values("date")
    if len(p):
        prob = p.iloc[-1]["prob_high_vol"]
        c2.metric("7-day volatility risk", "High" if prob >= metrics["decision_threshold"] else "Normal",
                  f"{prob:.0%} probability", delta_color="off")

if regimes is not None:
    r = regimes[regimes["asset"] == asset].sort_values("date")
    c3.metric("Current market regime", r.iloc[-1]["regime_name"].title())

st.divider()
st.markdown(
    "**Explore**\n"
    "- **Asset Explorer**: price and volatility history with regulatory and market events\n"
    "- **Risk Forecast**: the model's 7-day risk call and its DataFacts\n"
    "- **Model Comparison**: market-only vs. market + on-chain, against a naive baseline\n"
    "- **Market Regimes**: what K-means and PCA found in the data"
)
st.caption("Pick an asset in the sidebar; it carries across every page.")
