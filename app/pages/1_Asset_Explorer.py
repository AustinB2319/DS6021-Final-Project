"""Price and volatility history, with regulatory and market events overlaid."""

import plotly.graph_objects as go
import streamlit as st

from components import loaders
from components.sidebar import setup
from config import ASSET_NAMES

asset = setup("Asset Explorer", icon="📈")

master, feats, events = loaders.master(), loaders.features(), loaders.events()
if master is None:
    loaders.missing_notice("master.csv", "Imaan")
    st.stop()

m = master[(master["asset"] == asset) & (master["date"] >= "2021-01-01")].sort_values("date")

start, end = st.slider("Date range", min_value=m["date"].min().date(),
                       max_value=m["date"].max().date(),
                       value=(m["date"].min().date(), m["date"].max().date()))
m = m[(m["date"].dt.date >= start) & (m["date"].dt.date <= end)]

# ---- price with event markers
fig = go.Figure(go.Scatter(x=m["date"], y=m["close"], mode="lines", name="Close",
                           line=dict(width=1.5)))
if events is not None:
    ev = events[events["asset"].isin([asset, "all"])
                & (events["date"].dt.date >= start) & (events["date"].dt.date <= end)]
    ev = ev.merge(m[["date", "close"]], on="date", how="inner")
    fig.add_trace(go.Scatter(
        x=ev["date"], y=ev["close"], mode="markers", name="Event",
        marker=dict(symbol="diamond", size=11, line=dict(width=1, color="white")),
        customdata=ev[["title", "event_type"]],
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>%{x|%b %d, %Y}<extra></extra>"))
fig.update_layout(title=f"{ASSET_NAMES[asset]} daily close (USDT)", height=420,
                  yaxis_type="log" if st.toggle("Log scale", value=True) else "linear",
                  margin=dict(t=50, b=10), hovermode="x unified", legend=dict(orientation="h"))
st.plotly_chart(fig, width="stretch")

# ---- volatility
if feats is not None:
    f = feats[(feats["asset"] == asset) & (feats["date"].dt.date >= start)
              & (feats["date"].dt.date <= end)].sort_values("date")
    vol = go.Figure()
    vol.add_trace(go.Scatter(x=f["date"], y=f["mkt_vol_30d"], name="30-day", line=dict(width=1.5)))
    vol.add_trace(go.Scatter(x=f["date"], y=f["mkt_vol_7d"], name="7-day",
                             line=dict(width=1), opacity=0.5))
    vol.update_layout(title="Realized volatility (annualized)", height=300, yaxis_tickformat=".0%",
                      margin=dict(t=50, b=10), hovermode="x unified", legend=dict(orientation="h"))
    st.plotly_chart(vol, width="stretch")
else:
    loaders.missing_notice("features.csv", "Aeden")

# ---- event table
if events is not None:
    with st.expander("Events in this period"):
        ev = events[events["asset"].isin([asset, "all"])
                    & (events["date"].dt.date >= start) & (events["date"].dt.date <= end)]
        st.dataframe(ev[["date", "title", "event_type", "jurisdiction", "source_url"]],
                     hide_index=True, width="stretch",
                     column_config={"date": st.column_config.DateColumn("Date"),
                                    "source_url": st.column_config.LinkColumn("Source")})
