"""Cached readers for every file in DATA_CONTRACT.md. Pages never read files directly."""

import json

import pandas as pd
import streamlit as st

from config import EXTERNAL, MODELS, PROCESSED


@st.cache_data
def _csv(path):
    if not path.exists():
        return None
    df = pd.read_csv(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df


def master():
    return _csv(PROCESSED / "master.csv")

def features():
    return _csv(PROCESSED / "features.csv")

def regimes():
    return _csv(PROCESSED / "regimes.csv")

def regime_profiles():
    return _csv(PROCESSED / "regime_profiles.csv")

def pca_variance():
    return _csv(PROCESSED / "pca_explained_variance.csv")

def predictions():
    return _csv(PROCESSED / "predictions.csv")

def events():
    return _csv(EXTERNAL / "events.csv")


@st.cache_data
def metrics():
    path = MODELS / "metrics.json"
    return json.loads(path.read_text()) if path.exists() else None


def model_entry(model, feature_set):
    m = metrics()
    if m is None:
        return None
    return next((e for e in m["models"]
                 if e["model"] == model and e["feature_set"] == feature_set), None)


def missing_notice(name, owner):
    st.info(f"`{name}` isn't available yet. It's {owner}'s handoff; this section "
            "fills in automatically once the file lands.")
