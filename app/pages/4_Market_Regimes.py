"""K-means market regimes and the PCA view behind them."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components import loaders
from components.sidebar import setup
from config import ASSET_NAMES, REGIME_COLORS

asset = setup("Market Regimes", icon="🧭")

regimes, profiles, pca, master = (loaders.regimes(), loaders.regime_profiles(),
                                  loaders.pca_variance(), loaders.master())
if regimes is None:
    loaders.missing_notice("regimes.csv", "Shawn")
    st.stop()

r = regimes[regimes["asset"] == asset].sort_values("date")
current = r.iloc[-1]["regime_name"]
st.metric(f"{ASSET_NAMES[asset]}: current regime", current.title())

# ---- price colored by regime
if master is not None:
    df = r.merge(master[["date", "asset", "close"]], on=["date", "asset"])
    fig = go.Figure(go.Scatter(x=df["date"], y=df["close"], mode="lines",
                               line=dict(width=1, color="rgba(128,128,128,0.4)"), showlegend=False,
                               hoverinfo="skip"))
    for name, color in REGIME_COLORS.items():
        part = df[df["regime_name"] == name]
        fig.add_trace(go.Scatter(x=part["date"], y=part["close"], mode="markers", name=name.title(),
                                 marker=dict(size=4, color=color)))
    fig.update_layout(title="Price colored by regime", height=380, yaxis_type="log",
                      margin=dict(t=50, b=10), legend=dict(orientation="h"))
    st.plotly_chart(fig, width="stretch")

left, right = st.columns(2)
with left:
    fig = px.scatter(r.assign(Regime=r["regime_name"].str.title()), x="pc1", y="pc2",
                     color="Regime", opacity=0.55, title="Asset-days in PCA space",
                     color_discrete_map={k.title(): v for k, v in REGIME_COLORS.items()},
                     category_orders={"Regime": [k.title() for k in REGIME_COLORS]},
                     labels={"pc1": "PC1", "pc2": "PC2"})
    fig.update_traces(marker_size=4)
    fig.update_layout(height=380, margin=dict(t=50, b=10))
    st.plotly_chart(fig, width="stretch")
with right:
    if pca is not None:
        fig = px.bar(pca, x="component", y="explained_variance", text_auto=".0%",
                     title="Variance explained by each component",
                     labels={"component": "", "explained_variance": "Share of variance"})
        fig.add_scatter(x=pca["component"], y=pca["cumulative_variance"], name="Cumulative",
                        mode="lines+markers")
        fig.update_layout(height=380, yaxis_tickformat=".0%", margin=dict(t=50, b=10),
                          showlegend=False)
        st.plotly_chart(fig, width="stretch")

if profiles is not None:
    st.subheader("What each regime looks like")
    st.caption("Average of each clustering input within the regime, across all assets.")
    st.dataframe(profiles.drop(columns="regime_id"), hide_index=True, width="stretch")

counts = r["regime_name"].value_counts(normalize=True)
st.caption(f"{ASSET_NAMES[asset]} spent " + ", ".join(
    f"{counts.get(n, 0):.0%} of days {n}" for n in REGIME_COLORS) + " (2021–2025).")
