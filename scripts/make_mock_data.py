"""
make_mock_data.py — generate FAKE versions of every file in DATA_CONTRACT.md

Lets the app be built and deployed before the real pipeline exists. Every file
lands under mock/ with the same relative paths the real files will use, so the
app only has to switch its root folder:

    mock/data/processed/master.csv      ->  data/processed/master.csv
    mock/models/metrics.json            ->  models/metrics.json
    ...

Run from the repo root:
    python scripts/make_mock_data.py

The numbers are simulated, NOT real market data. Prices follow a random walk
whose volatility switches between calm / normal / stressed states, so the
target, regimes and model scores behave plausibly. Do not use any of it
for analysis.

# [AI-GENERATED] Tool: Claude | Log: ai/logs/austin.md (2026-11-09) | Reviewed by: Austin
# Validation: script runs end to end and every output passes check_contract()
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
ROOT = Path(__file__).resolve().parents[1] / "mock"
START, END = "2020-07-01", "2025-12-31"       # warm-up rows before 2021 for rolling windows
STUDY_START = "2021-01-01"
TRAIN_END = "2024-12-31"
ASSETS = ["btc", "eth", "xrp", "sol"]
ONCHAIN_ASSETS = ["btc", "eth", "xrp"]       # Coin Metrics Community has no SOL
SOL_LISTED = "2020-08-11"                    # SOLUSDT history starts here on Binance

rng = np.random.default_rng(SEED)
dates = pd.date_range(START, END, freq="D")
n = len(dates)


# ---------------------------------------------------------------- simulation
def simulate_states():
    """Market-wide hidden volatility state: 0 calm, 1 normal, 2 stressed."""
    P = np.array([[0.97, 0.03, 0.00],
                  [0.02, 0.96, 0.02],
                  [0.00, 0.05, 0.95]])
    s = np.empty(n, dtype=int)
    s[0] = 1
    for t in range(1, n):
        s[t] = rng.choice(3, p=P[s[t - 1]])
    return s


states = simulate_states()
STATE_VOL = np.array([0.020, 0.035, 0.060])          # daily vol per state (BTC scale)
ASSET = {
    #        start price, vol multiplier, typical daily USDT volume
    "btc": dict(price=9_100.0, mult=1.00, qv=2.0e9),
    "eth": dict(price=225.0,   mult=1.25, qv=1.0e9),
    "xrp": dict(price=0.175,   mult=1.50, qv=3.0e8),
    "sol": dict(price=1.00,    mult=1.80, qv=2.0e8),
}
z_mkt = rng.standard_normal(n)                        # common market factor


def simulate_market(asset):
    cfg = ASSET[asset]
    sigma = STATE_VOL[states] * cfg["mult"] * np.exp(rng.normal(0, 0.15, n))
    z = 0.7 * z_mkt + np.sqrt(1 - 0.49) * rng.standard_normal(n)
    r = 0.0004 + sigma * z
    close = cfg["price"] * np.exp(np.cumsum(r))
    open_ = np.r_[cfg["price"], close[:-1]]
    wick = np.abs(rng.normal(0, 0.4, n)) * sigma
    high = np.maximum(open_, close) * np.exp(wick)
    low = np.minimum(open_, close) * np.exp(-np.abs(rng.normal(0, 0.4, n)) * sigma)
    quote_volume = cfg["qv"] * np.exp(rng.normal(0, 0.3, n)) * (1 + 8 * sigma)
    taker_share = rng.uniform(0.45, 0.55, n)
    df = pd.DataFrame({
        "date": dates, "asset": asset,
        "open": open_, "high": high, "low": low, "close": close,
        "volume": quote_volume / close,
        "quote_volume": quote_volume,
        "num_trades": (quote_volume / rng.uniform(800, 1200, n)).astype(int),
        "taker_buy_base": quote_volume * taker_share / close,
        "taker_buy_quote": quote_volume * taker_share,
        "_sigma": sigma,
    })
    if asset == "sol":
        df = df[df["date"] >= SOL_LISTED]
    return df


market = pd.concat([simulate_market(a) for a in ASSETS], ignore_index=True)

# Fear & Greed: market-wide, driven by BTC's 30-day return
btc_close = market.loc[market.asset == "btc"].set_index("date")["close"]
ret30 = np.log(btc_close / btc_close.shift(30)).fillna(0)
fng_value = (50 + 150 * ret30 + rng.normal(0, 8, n)).clip(0, 100).round().astype(int)
fng_class = pd.cut(fng_value, [-1, 24, 46, 54, 75, 100],
                   labels=["extreme_fear", "fear", "neutral", "greed", "extreme_greed"])
sentiment = pd.DataFrame({"date": dates, "fng_value": fng_value.values,
                          "fng_class": fng_class.astype(str).values})

# Macro: business days only, forward-filled over weekends (as FRED will be)
vix = 18 + 10 * (states == 2) + np.cumsum(rng.normal(0, 0.6, n)) * 0.3
vix = pd.Series(vix).clip(11, 45).values
macro = pd.DataFrame({
    "date": dates,
    "vix": vix,
    "dollar_index": 118 + np.cumsum(rng.normal(0, 0.25, n)) * 0.5,
    "us10y": np.linspace(0.7, 4.3, n) + rng.normal(0, 0.08, n),
})
macro.loc[macro["date"].dt.dayofweek >= 5, ["vix", "dollar_index", "us10y"]] = np.nan
macro = macro.ffill()

# On-chain: BTC/ETH/XRP only; activity rises with volatility
ONCHAIN = {
    "btc": dict(tx=330_000, adr=900_000, fee=40, sply=18.4e6, sply_growth=900),
    "eth": dict(tx=1_150_000, adr=550_000, fee=1_500, sply=112e6, sply_growth=13_000),
    "xrp": dict(tx=1_300_000, adr=55_000, fee=1_200, sply=99.99e9, sply_growth=-1_000),
}
oc_frames = []
for a, cfg in ONCHAIN.items():
    sig = market.loc[market.asset == a, "_sigma"].values
    boost = 1 + 6 * (sig - sig.mean())
    oc_frames.append(pd.DataFrame({
        "date": dates, "asset": a,
        "tx_cnt": (cfg["tx"] * boost * np.exp(rng.normal(0, 0.10, n))).round(),
        "adr_act_cnt": (cfg["adr"] * boost * np.exp(rng.normal(0, 0.12, n))).round(),
        "fee_tot_ntv": cfg["fee"] * boost**2 * np.exp(rng.normal(0, 0.35, n)),
        "sply_cur": cfg["sply"] + cfg["sply_growth"] * np.arange(n),
    }))
onchain = pd.concat(oc_frames, ignore_index=True)

# Events: placeholder list until Shawn's real table lands
events = pd.DataFrame([
    ("mock_terra_collapse_2022", "2022-05-09", "all", "exchange_failure", "global", "[MOCK] Terra/LUNA collapse"),
    ("mock_eth_merge_2022",      "2022-09-15", "eth", "protocol_upgrade", "global", "[MOCK] Ethereum Merge to proof of stake"),
    ("mock_ftx_collapse_2022",   "2022-11-08", "all", "exchange_failure", "global", "[MOCK] FTX halts withdrawals"),
    ("mock_xrp_ruling_2023",     "2023-07-13", "xrp", "court_ruling",     "us",     "[MOCK] SEC v. Ripple summary judgment"),
    ("mock_btc_etf_2024",        "2024-01-10", "btc", "etf",              "us",     "[MOCK] Spot bitcoin ETFs approved"),
    ("mock_btc_halving_2024",    "2024-04-20", "btc", "halving",          "global", "[MOCK] Bitcoin halving"),
    ("mock_eth_etf_2024",        "2024-07-23", "eth", "etf",              "us",     "[MOCK] Spot ether ETFs begin trading"),
], columns=["event_id", "date", "asset", "event_type", "jurisdiction", "title"])
events["source_url"] = ""   # real table must have official links


# ------------------------------------------------------------------ master
master = (market.drop(columns="_sigma")
          .merge(sentiment, on="date", how="left")
          .merge(macro, on="date", how="left")
          .merge(onchain, on=["date", "asset"], how="left"))
master["has_onchain"] = master["asset"].isin(ONCHAIN_ASSETS)

ev = events.copy()
ev["date"] = pd.to_datetime(ev["date"])
ev = pd.concat([ev[ev.asset != "all"],
                *[ev[ev.asset == "all"].assign(asset=a) for a in ASSETS]])
ev = ev.drop_duplicates(["date", "asset"])[["date", "asset", "event_type"]]
master = master.merge(ev, on=["date", "asset"], how="left")
master["event_today"] = master["event_type"].notna()
master = master.sort_values(["asset", "date"]).reset_index(drop=True)


# ---------------------------------------------------------------- features
def add_features(g):
    g = g.copy()
    lr = np.log(g["close"]).diff()
    g["mkt_ret_1d"] = lr
    g["mkt_ret_7d"] = np.log(g["close"] / g["close"].shift(7))
    g["mkt_vol_7d"] = lr.rolling(7).std() * np.sqrt(365)
    g["mkt_vol_30d"] = lr.rolling(30).std() * np.sqrt(365)
    g["mkt_momentum_14d"] = g["close"] / g["close"].shift(14) - 1
    g["mkt_volume_chg_7d"] = np.log(g["quote_volume"] / g["quote_volume"].shift(7))
    g["mkt_drawdown"] = g["close"] / g["close"].rolling(365, min_periods=1).max() - 1
    g["sent_fng_value"] = g["fng_value"]
    g["macro_vix"] = g["vix"]
    g["macro_us10y"] = g["us10y"]
    for col, name in [("tx_cnt", "oc_tx_cnt_logchg_7d")]:
        g[name] = np.log(g[col] / g[col].shift(7))
    for col, name in [("adr_act_cnt", "oc_adr_act_z30"), ("fee_tot_ntv", "oc_fee_z30")]:
        m, s = g[col].rolling(30).mean(), g[col].rolling(30).std()
        g[name] = (g[col] - m) / s
    g["cat_trend_state"] = np.where(g["close"] > g["close"].rolling(200, min_periods=1).mean(),
                                    "above_200dma", "below_200dma")
    # realized vol over days t+1..t+7 (the only forward-looking column)
    g["fwd_vol_7d"] = lr.shift(-1).rolling(7).std().shift(-6) * np.sqrt(365)
    g["_lr"] = lr
    return g


feat = pd.concat([add_features(master[master["asset"] == a]) for a in ASSETS],
                 ignore_index=True)

btc_lr = feat.loc[feat["asset"] == "btc"].set_index("date")["_lr"]
corr_parts = []
for a in ASSETS:
    g = feat.loc[feat["asset"] == a].set_index("date")["_lr"]
    corr_parts.append(g.rolling(30).corr(btc_lr.reindex(g.index)).values)
feat["mkt_btc_corr_30d"] = np.concatenate(corr_parts)

consensus = {"btc": "pow", "xrp": "xrpl_consensus", "sol": "pos"}
feat["cat_consensus"] = feat["asset"].map(consensus)
feat.loc[feat.asset == "eth", "cat_consensus"] = np.where(
    feat.loc[feat.asset == "eth", "date"] < "2022-09-15", "pow", "pos")
feat["cat_asset"] = feat["asset"]
feat["cat_fng_class"] = feat["fng_class"]
feat["cat_day_of_week"] = feat["date"].dt.day_name().str.lower()

halvings = pd.to_datetime(["2020-05-11", "2024-04-20", "2028-04-15"])
def halving_phase(d):
    prev = halvings[halvings <= d].max()
    nxt = halvings[halvings > d].min()
    if (d - prev).days <= 365:
        return "post_halving_12m"
    if (nxt - d).days <= 365:
        return "pre_halving_12m"
    return "mid_cycle"
feat["cat_halving_phase"] = feat["date"].map(halving_phase)

feat = feat[feat["date"] >= STUDY_START].copy()
feat["split"] = np.where(feat["date"] <= TRAIN_END, "train", "test")

thr = (feat[feat.split == "train"].groupby("asset")["fwd_vol_7d"].quantile(0.75))
feat["high_vol_7d"] = (feat["fwd_vol_7d"] > feat["asset"].map(thr)).astype("Int64")
feat.loc[feat["fwd_vol_7d"].isna(), "high_vol_7d"] = pd.NA

feature_cols = ([c for c in feat.columns if c.startswith(("mkt_", "sent_", "macro_", "oc_", "cat_"))])
features = feat[["date", "asset", "split", *feature_cols, "fwd_vol_7d", "high_vol_7d"]].copy()


# ------------------------------------------------------------ unsupervised
REGIME_NAMES = {0: "calm", 1: "normal", 2: "stressed"}
state_by_date = pd.Series(states, index=dates)
regimes = features[["date", "asset", "split"]].copy()
true_state = regimes["date"].map(state_by_date).values
flip = rng.random(len(regimes)) < 0.10                         # imperfect clustering
regimes["regime_id"] = np.where(flip, rng.integers(0, 3, len(regimes)), true_state)
regimes["regime_name"] = regimes["regime_id"].map(REGIME_NAMES)

def zscore(s):
    return (s - s.mean()) / s.std()
regimes["pc1"] = (zscore(features["mkt_vol_30d"].fillna(features["mkt_vol_30d"].median())).values
                  * 1.6 + rng.normal(0, 0.6, len(regimes)))
regimes["pc2"] = (zscore(features["mkt_momentum_14d"].fillna(0)).values
                  * 1.1 + rng.normal(0, 0.6, len(regimes)))

ev_ratio = np.array([0.41, 0.22, 0.14, 0.10, 0.07, 0.06])
pca_var = pd.DataFrame({"component": [f"PC{i+1}" for i in range(len(ev_ratio))],
                        "explained_variance": ev_ratio,
                        "cumulative_variance": ev_ratio.cumsum()})

profile_cols = ["mkt_vol_30d", "mkt_ret_7d", "mkt_drawdown", "sent_fng_value", "oc_adr_act_z30"]
profiles = (features[profile_cols].assign(regime_id=regimes["regime_id"].values)
            .groupby("regime_id").mean().reset_index())
profiles.insert(1, "regime_name", profiles["regime_id"].map(REGIME_NAMES))
profiles.insert(2, "n_days", regimes["regime_id"].value_counts().sort_index().values)


# ---------------------------------------------------------------- modeling
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

MODELS = {           # signal strength, noise — tuned only so mock scores look plausible
    "logistic":  (1.2, 0.9),
    "knn":       (1.0, 1.1),
    "tree":      (1.1, 1.0),
    "ensemble":  (1.3, 0.8),
}
vol_z = features.groupby("asset")["mkt_vol_7d"].transform(zscore).fillna(0).values
actual = features["high_vol_7d"].astype("float").values
signal = np.nan_to_num(actual - 0.5)

pred_frames = []
for fs in ["market", "market_onchain"]:
    mask = features["asset"].isin(ONCHAIN_ASSETS).values if fs == "market_onchain" else np.ones(len(features), bool)
    bonus = 0.15 if fs == "market_onchain" else 0.0
    for model, (k, noise) in MODELS.items():
        logit = k * vol_z - 1.1 + (0.55 + bonus) * signal + rng.normal(0, noise, len(features))
        pred_frames.append(pd.DataFrame({
            "date": features["date"], "asset": features["asset"], "split": features["split"],
            "model": model, "feature_set": fs, "prob_high_vol": sigmoid(logit),
        })[mask])

base_thr = features[features.split == "train"].groupby("asset")["mkt_vol_7d"].quantile(0.75)
pred_frames.append(pd.DataFrame({
    "date": features["date"], "asset": features["asset"], "split": features["split"],
    "model": "baseline", "feature_set": "market",
    "prob_high_vol": (features["mkt_vol_7d"] > features["asset"].map(base_thr)).astype(float),
}))
predictions = pd.concat(pred_frames, ignore_index=True)
predictions["pred"] = (predictions["prob_high_vol"] >= 0.5).astype(int)
predictions = predictions.merge(features[["date", "asset", "high_vol_7d"]], on=["date", "asset"])
predictions = predictions.rename(columns={"high_vol_7d": "actual"})


def roc_auc(y, p):
    order = np.argsort(p)
    ranks = np.empty(len(p))
    ranks[order] = np.arange(1, len(p) + 1)
    pos = y == 1
    n_pos, n_neg = pos.sum(), (~pos).sum()
    return float((ranks[pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))

def scores(df):
    df = df.dropna(subset=["actual"])
    y, p, yhat = df["actual"].astype(int).values, df["prob_high_vol"].values, df["pred"].values
    tp = int(((yhat == 1) & (y == 1)).sum())
    prec = tp / max(int((yhat == 1).sum()), 1)
    rec = tp / max(int((y == 1).sum()), 1)
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"roc_auc": round(roc_auc(y, p), 3), "f1": round(f1, 3),
            "precision": round(prec, 3), "recall": round(rec, 3)}

FEATURES_BY_SET = {
    "market": [c for c in feature_cols if not c.startswith("oc_")],
    "market_onchain": feature_cols,
}
model_entries, log_rows = [], []
for (model, fs), g in predictions.groupby(["model", "feature_set"]):
    cv, test = scores(g[g.split == "train"]), scores(g[g.split == "test"])
    model_entries.append({
        "model": model, "feature_set": fs,
        "assets": sorted(g["asset"].unique().tolist()),
        "features": [] if model == "baseline" else FEATURES_BY_SET[fs],
        "cv": cv, "test": test,
        "notes": "MOCK — simulated scores",
    })
    log_rows.append({"run_id": f"mock_{len(log_rows)+1:03d}", "date_run": "2026-11-09",
                     "model": model, "feature_set": fs, "params": "{}",
                     "cv_roc_auc": cv["roc_auc"], "cv_f1": cv["f1"], "cv_recall": cv["recall"],
                     "notes": "MOCK", "owner": "mock"})

metrics = {
    "is_mock": True,
    "generated_at": "2026-11-09",
    "target": "high_vol_7d",
    "train_period": [STUDY_START, TRAIN_END],
    "test_period": ["2025-01-01", END],
    "final_model": {"model": "ensemble", "feature_set": "market_onchain"},
    "decision_threshold": 0.5,
    "models": model_entries,
}


# ------------------------------------------------------------------- write
def fmt_dates(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df

def write_csv(df, rel):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    df = fmt_dates(df).sort_values([c for c in ("asset", "date") if c in df.columns])
    df.to_csv(path, index=False, float_format="%.6g")
    return path

paths = {
    "master": write_csv(master, "data/processed/master.csv"),
    "events": write_csv(events, "data/external/events.csv"),
    "features": write_csv(features, "data/processed/features.csv"),
    "regimes": write_csv(regimes, "data/processed/regimes.csv"),
    "predictions": write_csv(predictions, "data/processed/predictions.csv"),
}
pca_var.to_csv(ROOT / "data/processed/pca_explained_variance.csv", index=False, float_format="%.4g")
(ROOT / "data/processed/regime_profiles.csv").write_text(profiles.to_csv(index=False, float_format="%.4g"))
(ROOT / "models").mkdir(parents=True, exist_ok=True)
(ROOT / "models/metrics.json").write_text(json.dumps(metrics, indent=2))
pd.DataFrame(log_rows).to_csv(ROOT / "models/experiment_log.csv", index=False)

dictionary = ["# Data dictionary (MOCK)", "",
              "Placeholder generated by scripts/make_mock_data.py. Imaan's real version replaces it.", "",
              "| Column | Type |", "|---|---|"]
dictionary += [f"| `{c}` | {t} |" for c, t in master.dtypes.astype(str).items()]
(ROOT / "data/DATA_DICTIONARY.md").write_text("\n".join(dictionary) + "\n")
(ROOT / "README.md").write_text(
    "# Mock data\n\n**Everything in this folder is simulated.** It exists so the app can be built "
    "before the real pipeline is done. Regenerate with `python scripts/make_mock_data.py`.\n")


# ------------------------------------------------------------------- check
def check_contract(path, required_cols):
    df = pd.read_csv(path)
    missing = set(required_cols) - set(df.columns)
    assert not missing, f"{path.name}: missing columns {missing}"
    assert df["date"].str.match(r"^\d{4}-\d{2}-\d{2}$").all(), f"{path.name}: bad date format"
    assert set(df["asset"].unique()) <= {"btc", "eth", "xrp", "sol", "all"}, f"{path.name}: bad asset codes"
    key = ["date", "asset"] + [c for c in ("model", "feature_set", "event_id") if c in df.columns]
    assert not df.duplicated(key).any(), f"{path.name}: duplicate rows"
    print(f"  ✓ {path.relative_to(ROOT.parent)}: {len(df):,} rows, "
          f"{df['date'].min()} → {df['date'].max()}")

print("Mock data written to mock/ — contract check:")
check_contract(paths["master"], ["date", "asset", "close", "fng_class", "vix", "has_onchain", "tx_cnt", "event_today"])
check_contract(paths["events"], ["event_id", "date", "asset", "event_type", "title", "source_url"])
check_contract(paths["features"], ["date", "asset", "split", "fwd_vol_7d", "high_vol_7d"])
check_contract(paths["regimes"], ["date", "asset", "regime_id", "regime_name", "pc1", "pc2"])
check_contract(paths["predictions"], ["date", "asset", "model", "feature_set", "prob_high_vol", "pred", "actual"])
print(f"  ✓ mock/models/metrics.json: {len(model_entries)} model entries")
