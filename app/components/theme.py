"""
CryptoLens look: black and graphite surfaces, gray text, one orange accent.
Orange is reserved for what matters (high risk, stressed regime, events,
the selected model) so it always means "look here".
"""

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

ORANGE = "#ff7a1a"
ORANGE_SOFT = "rgba(255,122,26,0.14)"
INK = "#e7e7e9"
GRAY = "#9a9ca3"
GRAY_DARK = "#5c5f66"
LINE = "#2a2c31"
SURFACE = "#17181b"

pio.templates["cryptolens"] = go.layout.Template(layout=dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=GRAY, size=12),
    title=dict(font=dict(color=INK, size=15)),
    colorway=[ORANGE, "#d4d4d8", GRAY_DARK, "#a1a1aa"],
    xaxis=dict(gridcolor=LINE, linecolor=LINE, zerolinecolor=LINE),
    yaxis=dict(gridcolor=LINE, linecolor=LINE, zerolinecolor=LINE),
    hoverlabel=dict(bgcolor=SURFACE, bordercolor=LINE, font=dict(color=INK)),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
))
pio.templates.default = "plotly_dark+cryptolens"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&family=JetBrains+Mono:wght@500;700&display=swap');
html, body, [class*="css"], .stMarkdown, p, label {{ font-family: 'Inter', sans-serif; }}
h1, h2, h3 {{ font-family: 'Inter', sans-serif; font-weight: 800 !important; letter-spacing: -0.02em; }}
h1 {{ font-size: 2.1rem !important; }}
[data-testid="stSidebar"] {{ background: #0f1012; border-right: 1px solid {LINE}; }}
[data-testid="stMetricValue"] {{ font-family: 'JetBrains Mono', monospace; font-weight: 700; color: {INK}; }}
[data-testid="stMetricLabel"] p {{ color: {GRAY}; text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.08em; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-color: {LINE} !important; border-radius: 10px; }}
.cl-eyebrow {{ color: {ORANGE}; font: 600 0.72rem 'JetBrains Mono', monospace; letter-spacing: 0.16em; text-transform: uppercase; }}
.cl-card {{ background: {SURFACE}; border: 1px solid {LINE}; border-radius: 12px; padding: 22px 24px; }}
.cl-card.high {{ border-color: {ORANGE}; background: linear-gradient(180deg, {ORANGE_SOFT}, {SURFACE} 70%); }}
.cl-big {{ font: 800 2.6rem 'Inter', sans-serif; color: {INK}; letter-spacing: -0.03em; line-height: 1.1; margin: 6px 0 2px; }}
.cl-big.high {{ color: {ORANGE}; }}
.cl-sub {{ color: {GRAY}; font-size: 0.9rem; }}
.cl-bar {{ height: 8px; background: {LINE}; border-radius: 4px; margin: 16px 0 6px; overflow: hidden; }}
.cl-bar > div {{ height: 100%; background: {ORANGE}; }}
.cl-mono {{ font-family: 'JetBrains Mono', monospace; color: {INK}; }}
code {{ color: #d4d4d8 !important; background: #222428 !important; }}
.cl-demo {{ background: {ORANGE_SOFT}; border: 1px solid rgba(255,122,26,0.35); border-left: 4px solid {ORANGE};
            border-radius: 8px; padding: 10px 14px; color: #ffb27a; font-size: 0.88rem; margin-bottom: 8px; }}
.cl-demo b {{ color: {ORANGE}; }}
/* DataFacts: a nutrition label, inverted for dark mode */
.df-label {{ border: 2px solid {INK}; border-radius: 4px; padding: 14px 18px 10px; background: #0b0b0c; }}
.df-title {{ font: 800 2rem 'Inter', sans-serif; color: {INK}; letter-spacing: -0.02em; line-height: 1; }}
.df-sub {{ color: {GRAY}; font-size: 0.82rem; margin: 4px 0 8px; }}
.df-rule-xl {{ border-top: 10px solid {INK}; margin: 6px 0; }}
.df-rule-md {{ border-top: 4px solid {INK}; margin: 6px 0; }}
.df-row {{ display: flex; justify-content: space-between; border-top: 1px solid {GRAY_DARK}; padding: 6px 0; font-size: 0.92rem; color: {INK}; }}
.df-row b {{ font-weight: 800; }}
.df-row span.v {{ font-family: 'JetBrains Mono', monospace; }}
.df-warn {{ border-top: 1px solid {GRAY_DARK}; padding: 6px 0; font-size: 0.86rem; color: {ORANGE}; }}
.df-foot {{ color: {GRAY}; font-size: 0.75rem; padding-top: 6px; border-top: 4px solid {INK}; margin-top: 6px; }}
</style>
"""


def apply():
    st.html(CSS)
