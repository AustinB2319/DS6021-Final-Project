"""
DataFacts: a "nutrition label" shown beside every prediction.

Everything here is read from metrics.json, the data files and config, never
typed by hand, so it stays accurate as models and data change.
"""

import streamlit as st

from config import FEATURE_SET_NAMES, MODEL_NAMES, ONCHAIN_ASSETS, USE_MOCK

SOURCES = [
    ("Binance Public Data", "Daily OHLCV, trades, taker volume", "https://data.binance.vision"),
    ("Coin Metrics Community", "On-chain activity (BTC, ETH, XRP)", "https://docs.coinmetrics.io"),
    ("Alternative.me", "Fear & Greed Index", "https://alternative.me/crypto/fear-and-greed-index/"),
    ("FRED", "VIX, dollar index, 10Y yield", "https://fred.stlouisfed.org"),
]

LIMITATIONS = [
    "Trained on 2021–2024; crypto market structure keeps changing (ETFs, regulation).",
    "Predicts a volatility risk class, not price direction or size.",
    "Prices come from a single exchange (Binance).",
    "Fear & Greed is market-wide and BTC-centric, not asset-specific.",
]


def _metric_row(scores, label):
    cols = st.columns(4)
    for col, key, name in zip(cols, ["roc_auc", "f1", "precision", "recall"],
                              ["ROC-AUC", "F1", "Precision", "Recall"]):
        col.metric(f"{name} ({label})", f"{scores[key]:.2f}")


def render(asset, entry, metrics, data_through, prob=None):
    """
    asset         selected asset code
    entry         the model's entry from metrics.json
    metrics       full metrics.json dict
    data_through  last date in the data behind the prediction (Timestamp)
    prob          predicted probability shown on the page, if any
    """
    with st.container(border=True):
        st.subheader("📋 DataFacts")
        st.caption("What's behind this prediction: where the data comes from, "
                   "how the model did, and what it can't tell you.")

        a, b, c = st.columns(3)
        a.markdown(f"**Model**  \n{MODEL_NAMES.get(entry['model'], entry['model'])}")
        b.markdown(f"**Feature set**  \n{FEATURE_SET_NAMES.get(entry['feature_set'], entry['feature_set'])}"
                   f" · {len(entry['features'])} variables")
        c.markdown(f"**Data through**  \n{data_through:%b %d, %Y}")

        if prob is not None:
            st.markdown(f"**Predicted probability of high volatility:** {prob:.0%} "
                        f"(flagged high at ≥ {metrics['decision_threshold']:.0%})")

        st.markdown("**Validation**")
        _metric_row(entry["cv"], "CV 2021–24")
        _metric_row(entry["test"], "test 2025")

        warnings = []
        if USE_MOCK or metrics.get("is_mock"):
            warnings.append("Simulated demo data. These scores are placeholders.")
        if asset not in ONCHAIN_ASSETS:
            warnings.append("No free on-chain data exists for this asset, so this "
                            "prediction uses market features only.")
        if asset not in entry["assets"]:
            warnings.append("This model wasn't trained on this asset.")
        for w in warnings:
            st.warning(w, icon="⚠️")

        with st.expander("Variables used"):
            st.write(", ".join(f"`{f}`" for f in entry["features"]) or "None (rule-based baseline)")
        with st.expander("Data sources"):
            for name, what, url in SOURCES:
                if name.startswith("Coin Metrics") and asset not in ONCHAIN_ASSETS:
                    continue
                st.markdown(f"- [{name}]({url}): {what}")
            st.markdown(f"- Train period: {metrics['train_period'][0]} to {metrics['train_period'][1]}; "
                        f"test period: {metrics['test_period'][0]} to {metrics['test_period'][1]}")
        with st.expander("Limitations"):
            for item in LIMITATIONS:
                st.markdown(f"- {item}")
