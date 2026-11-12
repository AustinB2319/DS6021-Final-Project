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
    """Nutrition-label style panel; every value comes from metrics.json and config."""
    warnings = []
    if USE_MOCK or metrics.get("is_mock"):
        warnings.append("Simulated demo data: scores are placeholders")
    if asset not in ONCHAIN_ASSETS:
        warnings.append("No free on-chain data for this asset: market features only")
    if asset not in entry["assets"]:
        warnings.append("Model was not trained on this asset")

    n_sources = sum(1 for n, _, _ in SOURCES if not (n.startswith("Coin Metrics") and asset not in ONCHAIN_ASSETS))
    t, cv = entry["test"], entry["cv"]
    row = lambda k, v, bold=True: (f'<div class="df-row"><span>{"<b>" + k + "</b>" if bold else k}</span>'
                                   f'<span class="v">{v}</span></div>')
    html = ['<div class="df-label">',
            '<div class="df-title">Data Facts</div>',
            '<div class="df-sub">Per prediction · read before trusting the number</div>',
            '<div class="df-rule-xl"></div>',
            row("Model", MODEL_NAMES.get(entry["model"], entry["model"])),
            row("Feature set", FEATURE_SET_NAMES.get(entry["feature_set"], entry["feature_set"])),
            row("&nbsp;&nbsp;Variables used", len(entry["features"]), bold=False),
            row("&nbsp;&nbsp;Data sources", n_sources, bold=False),
            row("Data through", f"{data_through:%b %d, %Y}"),
            '<div class="df-rule-md"></div>']
    if prob is not None:
        html.append(row("Predicted probability", f"{prob:.0%}"))
    html += [row("Test ROC-AUC (2025)", f"{t['roc_auc']:.2f}"),
             row("&nbsp;&nbsp;CV ROC-AUC (2021–24)", f"{cv['roc_auc']:.2f}", bold=False),
             row("Test recall, high-vol weeks", f"{t['recall']:.0%}"),
             row("Test precision", f"{t['precision']:.0%}"),
             '<div class="df-rule-md"></div>']
    html += [f'<div class="df-warn">⚠ {w}</div>' for w in warnings]
    html.append('<div class="df-foot">Predicts a volatility risk class, not price direction. '
                'Trained on 2021–2024 data. Not financial advice.</div></div>')

    left, right = st.columns([1, 1])
    with left:
        st.html("".join(html))
    with right:
        st.markdown("##### The details")
        with st.expander("Variables used", expanded=True):
            st.write(", ".join(f"`{f}`" for f in entry["features"]) or "None (rule-based baseline)")
        with st.expander("Data sources"):
            for name, what, url in SOURCES:
                if name.startswith("Coin Metrics") and asset not in ONCHAIN_ASSETS:
                    continue
                st.markdown(f"- [{name}]({url}): {what}")
            st.markdown(f"- Train {metrics['train_period'][0]} to {metrics['train_period'][1]}; "
                        f"test {metrics['test_period'][0]} to {metrics['test_period'][1]}")
        with st.expander("Limitations"):
            for item in LIMITATIONS:
                st.markdown(f"- {item}")
