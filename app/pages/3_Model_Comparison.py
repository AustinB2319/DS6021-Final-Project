"""Market-only vs. market + on-chain, every model against the naive baseline."""

import pandas as pd
import plotly.express as px
import streamlit as st

from components import loaders
from components.sidebar import setup
from config import FEATURE_SET_NAMES, MODEL_NAMES

setup("Model Comparison", icon="⚖️")

metrics = loaders.metrics()
if metrics is None:
    loaders.missing_notice("metrics.json", "Diego")
    st.stop()

st.markdown("**Research question:** does adding blockchain/on-chain activity improve "
            "7-day volatility-risk predictions over market data alone?")

rows = [{"Model": MODEL_NAMES.get(e["model"], e["model"]),
         "Feature set": FEATURE_SET_NAMES.get(e["feature_set"], e["feature_set"]),
         "Assets": ", ".join(a.upper() for a in e["assets"]),
         **{f"{k.upper().replace('_', '-')} (test)": e["test"][k]
            for k in ("roc_auc", "f1", "precision", "recall")},
         "ROC-AUC (CV)": e["cv"]["roc_auc"]} for e in metrics["models"]]
table = pd.DataFrame(rows)

metric = st.radio("Metric", ["ROC-AUC", "F1", "RECALL", "PRECISION"], horizontal=True,
                  format_func=str.title)
col = f"{metric} (test)"
fig = px.bar(table, x="Model", y=col, color="Feature set", barmode="group", text_auto=".2f",
             category_orders={"Model": [MODEL_NAMES[k] for k in MODEL_NAMES]},
             title=f"{metric.title()} on the 2025 test set")
fig.update_layout(height=400, yaxis_range=[0, 1], margin=dict(t=50, b=10),
                  legend=dict(orientation="h", y=-0.15))
st.plotly_chart(fig, width="stretch")

st.caption("The market + on-chain models cover BTC, ETH and XRP only; free on-chain data "
           "doesn't exist for SOL. Compare the two feature sets on the same assets "
           "before drawing conclusions.")

st.dataframe(table.sort_values(["Model", "Feature set"]), hide_index=True,
             width="stretch")

final = metrics["final_model"]
st.success(f"**Final model:** {MODEL_NAMES.get(final['model'], final['model'])}, "
           f"{FEATURE_SET_NAMES.get(final['feature_set'], final['feature_set'])}")
