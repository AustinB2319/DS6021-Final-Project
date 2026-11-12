"""The final model's 7-day volatility risk call, with its DataFacts panel."""

import plotly.graph_objects as go
import streamlit as st

from components import datafacts, loaders
from components.sidebar import setup
from config import ASSET_NAMES, MODEL_NAMES, ONCHAIN_ASSETS

asset = setup("Risk Forecast", icon="⚡")

preds, metrics = loaders.predictions(), loaders.metrics()
if preds is None or metrics is None:
    loaders.missing_notice("predictions.csv / metrics.json", "Diego")
    st.stop()

final = metrics["final_model"]
model = final["model"]
# Assets without on-chain data fall back to the market-only version of the final model
feature_set = final["feature_set"] if asset in ONCHAIN_ASSETS else "market"
entry = loaders.model_entry(model, feature_set)

p = preds[(preds["asset"] == asset) & (preds["model"] == model)
          & (preds["feature_set"] == feature_set)].sort_values("date")
latest = p.iloc[-1]
prob, threshold = latest["prob_high_vol"], metrics["decision_threshold"]
is_high = prob >= threshold

left, right = st.columns([1, 2])
with left:
    st.subheader(ASSET_NAMES[asset])
    st.metric(f"Risk for the 7 days after {latest['date']:%b %d, %Y}",
              "🔴 High volatility" if is_high else "🟢 Normal volatility")
    st.progress(float(prob), text=f"{prob:.0%} probability of a high-volatility week")
    st.caption(f"Model: {MODEL_NAMES.get(model, model)}. \"High\" means 7-day realized "
               "volatility above this asset's 75th percentile (2021–2024).")

with right:
    test = p[p["split"] == "test"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=test["date"], y=test["prob_high_vol"], name="Predicted probability",
                             line=dict(width=1.5)))
    hits = test[test["actual"] == 1]
    fig.add_trace(go.Scatter(x=hits["date"], y=[1.02] * len(hits), mode="markers",
                             name="Actual high-vol week", marker=dict(symbol="line-ns-open", size=8)))
    fig.add_hline(y=threshold, line_dash="dash", annotation_text="threshold",
                  annotation_position="bottom right")
    fig.update_layout(title="2025 test period: predicted risk vs. what happened", height=360,
                      yaxis=dict(range=[0, 1.06], tickformat=".0%"), margin=dict(t=50, b=10),
                      hovermode="x unified", legend=dict(orientation="h"))
    st.plotly_chart(fig, width="stretch")

datafacts.render(asset, entry, metrics, data_through=latest["date"], prob=prob)
