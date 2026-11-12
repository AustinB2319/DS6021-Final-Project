"""Shared page setup: page config, mock-data banner and the asset selector."""

import streamlit as st

from config import ASSET_NAMES, ASSETS, USE_MOCK


def setup(title, icon="🔍"):
    """Call first on every page. Returns the selected asset code."""
    st.set_page_config(page_title=f"{title} · CryptoLens", page_icon=icon, layout="wide")

    # Remember the asset across pages (widget state alone resets when you switch pages)
    current = st.session_state.get("asset", "btc")
    st.session_state["asset"] = st.sidebar.selectbox(
        "Asset", ASSETS, index=ASSETS.index(current), format_func=ASSET_NAMES.get)

    st.sidebar.divider()
    st.sidebar.caption("CryptoLens · DS 6021 Final Project")
    st.sidebar.caption("Educational project, not financial advice.")

    if USE_MOCK:
        st.warning("**Demo mode:** every number here is simulated mock data, not real "
                   "results. Set `CRYPTOLENS_MOCK=0` to use the team's real files.",
                   icon="🧪")

    st.title(f"{icon} {title}")
    return st.session_state["asset"]
