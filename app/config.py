"""
App-wide settings. Every page reads data through these paths, so switching
from mock to real data is one environment variable:

    CRYPTOLENS_MOCK=1  (default)  -> reads mock/data, mock/models
    CRYPTOLENS_MOCK=0             -> reads data/, models/  (teammates' real files)
"""

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
USE_MOCK = os.getenv("CRYPTOLENS_MOCK", "1") == "1"
ROOT = REPO / "mock" if USE_MOCK else REPO

DATA = ROOT / "data"
PROCESSED = DATA / "processed"
EXTERNAL = DATA / "external"
MODELS = ROOT / "models"

ASSETS = ["btc", "eth", "xrp", "sol"]
ASSET_NAMES = {"btc": "Bitcoin (BTC)", "eth": "Ethereum (ETH)",
               "xrp": "XRP", "sol": "Solana (SOL)"}
ONCHAIN_ASSETS = ["btc", "eth", "xrp"]          # Coin Metrics Community has no SOL

REGIME_COLORS = {"calm": "#2a9d8f", "normal": "#8d99ae", "stressed": "#e76f51"}
FEATURE_SET_NAMES = {"market": "Market only", "market_onchain": "Market + on-chain"}
MODEL_NAMES = {"baseline": "Naive baseline", "logistic": "Logistic regression",
               "knn": "KNN", "tree": "Classification tree", "ensemble": "Tree ensemble"}
