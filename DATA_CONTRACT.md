# CryptoLens Data Contract

This file defines **every file each team member hands off**: where it goes, when it's due, and exactly what columns it contains. The app, the models and the slides all depend on these files, so if your output matches this spec, everything downstream just works.

> **Changing the contract:** if you need to add, rename or drop a column, post it in the group chat and update this file in the same pull request. Don't change a schema silently. Someone downstream is reading that column.

---

## Handoff summary

| File | Owner | Due | Used by |
|---|---|---|---|
| `data/raw/*` | Imaan | Nov 8 | Reproducibility / submission |
| `data/processed/master.csv` | Imaan | Nov 10 (v1), Nov 13 (v2) | Aeden, Diego, Shawn, Austin |
| `data/DATA_DICTIONARY.md` | Imaan | Nov 10 | Everyone, DataFacts panel |
| `data/external/events.csv` | Shawn | Nov 12 | Imaan (merge), Austin (event overlay) |
| `data/processed/features.csv` | Aeden | Nov 17 | Diego, Shawn |
| `data/processed/regimes.csv` | Shawn | Nov 20 | Diego, Austin |
| `data/processed/pca_explained_variance.csv` | Shawn | Nov 20 | Austin, slides |
| `data/processed/regime_profiles.csv` | Shawn | Nov 20 | Austin, slides |
| `data/processed/predictions.csv` | Diego | Nov 24 | Austin |
| `models/metrics.json` | Diego | Nov 24 | Austin (DataFacts), slides |
| `models/experiment_log.csv` | Diego | Nov 24 | Rubric (experiment tracking) |
| `reports/figures/*` | Aeden | Nov 24 | Austin, slides |
| `ai/logs/<your_name>.md` | Everyone | Ongoing, final Dec 1 | Austin (AI usage doc) |

---

## Global rules (apply to every file)

| Rule | Spec |
|---|---|
| **Keys** | Every row-level file is keyed on `date` + `asset`. One row per date × asset, with no duplicates. |
| **`date`** | String `YYYY-MM-DD`, UTC calendar day, **no time or timezone** (not `time`, not `2021-01-01 00:00:00+00:00`). |
| **`asset`** | Lowercase: `btc`, `eth`, `xrp`, `sol`. |
| **Column names** | `snake_case`, lowercase. No spaces or hyphens. (`tx_cnt`, not `TxCnt`.) |
| **Missing values** | Leave empty (NaN). **Never fill with 0.** Zero and "no data" mean different things. |
| **Sort order** | `asset`, then `date` ascending. |
| **Format** | CSV, UTF-8, comma-separated, header row, **no index column** (`to_csv(index=False)`). |
| **Study period** | 2021-01-01 to 2025-12-31. Earlier warm-up rows (for rolling windows) are fine in `master.csv`, but `features.csv` starts at 2021-01-01. |
| **Train / test** | Train/dev = 2021–2024. Test = 2025. Anything *fit* (scalers, thresholds, PCA, K-means, models) is fit on 2021–2024 only. |
| **Versioning** | If a schema changes, bump the version in the filename (`master_v2.csv`) and note it in the changelog at the bottom. |

### On-chain coverage

Coin Metrics Community has **no on-chain data for SOL**. In every file:

- SOL rows exist, but all on-chain columns are empty.
- The market + on-chain comparison (Model 2) uses **BTC, ETH, XRP only**.
- `master.csv` includes a `has_onchain` flag so nobody has to hard-code this.

---

## 1. `data/raw/`: Imaan · due Nov 8

Untouched downloads, saved so the pipeline can be rerun and raw data can be submitted.

```
data/raw/
├── binance/         # one CSV per symbol, extracted from the monthly ZIPs (no ZIPs in git)
├── coinmetrics/     # coinmetrics_raw.csv as returned by the API
├── fear_greed/      # fear_greed_raw.csv
└── fred/            # one CSV per series (VIXCLS, DTWEXBGS, DGS10)
```

---

## 2. `data/processed/master.csv`: Imaan · v1 Nov 10, v2 Nov 13

The single cleaned dataset that everything else builds on. **v1** = market data + sentiment + macro. **v2** = v1 + on-chain columns + event flags.

| Column | Type | Description | Source |
|---|---|---|---|
| `date` | str | `YYYY-MM-DD` | All |
| `asset` | str | `btc` / `eth` / `xrp` / `sol` | All |
| `open` | float | Daily open, USDT | Binance |
| `high` | float | Daily high, USDT | Binance |
| `low` | float | Daily low, USDT | Binance |
| `close` | float | Daily close, USDT | Binance |
| `volume` | float | Base-asset volume | Binance |
| `quote_volume` | float | Volume in USDT | Binance |
| `num_trades` | int | Number of trades | Binance |
| `taker_buy_base` | float | Taker buy volume (base asset) | Binance |
| `taker_buy_quote` | float | Taker buy volume (USDT) | Binance |
| `fng_value` | int | Fear & Greed score, 0–100 (same for all assets on a date) | Alternative.me |
| `fng_class` | str | `extreme_fear` / `fear` / `neutral` / `greed` / `extreme_greed` | Alternative.me |
| `vix` | float | CBOE VIX close | FRED `VIXCLS` |
| `dollar_index` | float | Broad U.S. dollar index | FRED `DTWEXBGS` |
| `us10y` | float | 10-year Treasury yield, % | FRED `DGS10` |
| `has_onchain` | bool | `True` for btc/eth/xrp, `False` for sol | Derived |
| `tx_cnt` | float | Transaction count *(v2)* | Coin Metrics `TxCnt` |
| `adr_act_cnt` | float | Active addresses *(v2)* | Coin Metrics `AdrActCnt` |
| `fee_tot_ntv` | float | Total fees, native units *(v2)* | Coin Metrics `FeeTotNtv` |
| `sply_cur` | float | Circulating supply *(v2)* | Coin Metrics `SplyCur` |
| `event_today` | bool | An event in `events.csv` hits this asset on this date *(v2)* | events.csv |
| `event_type` | str | Event type if `event_today`, else empty *(v2)* | events.csv |

**Rules specific to this file**

- **Macro data on weekends/holidays:** FRED only publishes on business days. **Forward-fill** from the previous business day. Never back-fill, because that would leak future information into the past.
- **Binance timestamps:** 2025 spot files use microsecond timestamps; earlier files use milliseconds. Convert both correctly (no 1970 or 2050s dates).
- Drop Binance's `ignore`, `open_time` and `close_time` columns after creating `date`.

## 3. `data/DATA_DICTIONARY.md`: Imaan · due Nov 10

Every column in `master.csv`: name, description, units, source, and any cleaning applied. Aeden adds his features to it by Nov 17. The app's DataFacts panel reads from this.

---

## 4. `data/external/events.csv`: Shawn · due Nov 12

Hand-curated regulatory and major-event table, roughly 25–40 rows.

| Column | Type | Description |
|---|---|---|
| `event_id` | str | Short unique ID, e.g. `sec_ripple_ruling_2023` |
| `date` | str | `YYYY-MM-DD` (date the news broke) |
| `asset` | str | `btc` / `eth` / `xrp` / `sol` / `all` |
| `event_type` | str | One of: `enforcement`, `court_ruling`, `etf`, `exchange_failure`, `protocol_upgrade`, `network_outage`, `halving`, `macro` |
| `jurisdiction` | str | `us`, `eu`, `global`, etc. |
| `title` | str | One-line description, under 80 characters (shown in the app) |
| `source_url` | str | Link to the official source (SEC/CFTC release, project announcement) |

`asset = all` means the event applies to every asset (e.g., the FTX collapse).

---

## 5. `data/processed/features.csv`: Aeden · due Nov 17

Model-ready table: `master.csv` + engineered features + target. 2021-01-01 to 2025-12-31.

**Required columns**

| Column | Type | Description |
|---|---|---|
| `date` | str | `YYYY-MM-DD` |
| `asset` | str | `btc` / `eth` / `xrp` / `sol` |
| `split` | str | `train` (2021–2024) or `test` (2025) |
| `fwd_vol_7d` | float | Realized volatility over days t+1…t+7 (the raw value behind the target) |
| `high_vol_7d` | int | **Target.** 1 if `fwd_vol_7d` > that asset's 75th percentile, with thresholds computed on **train rows only**; else 0 |

The last 7 days of 2025 can't have a target. Leave `fwd_vol_7d` and `high_vol_7d` empty there.

**Feature naming: use these prefixes.** This is how Diego selects Model 1 vs. Model 2 without hard-coding column lists:

| Prefix | Group | Examples | In Model 1 | In Model 2 |
|---|---|---|---|---|
| `mkt_` | Market | `mkt_ret_1d`, `mkt_vol_7d`, `mkt_vol_30d`, `mkt_momentum_14d`, `mkt_volume_chg_7d`, `mkt_drawdown`, `mkt_btc_corr_30d` | ✓ | ✓ |
| `sent_` | Sentiment | `sent_fng_value` | ✓ | ✓ |
| `macro_` | Macro | `macro_vix`, `macro_us10y` | ✓ | ✓ |
| `oc_` | On-chain | `oc_tx_cnt_logchg_7d`, `oc_adr_act_z30`, `oc_fee_z30` | | ✓ |
| `cat_` | Categorical | `cat_asset`, `cat_consensus`, `cat_fng_class`, `cat_trend_state`, `cat_halving_phase`, `cat_day_of_week` | ✓ | ✓ |

**Rules specific to this file**

- **No look-ahead:** every feature on day *t* uses only data from day *t* or earlier. Only `fwd_vol_7d` and `high_vol_7d` look forward.
- Use **log changes** (`np.log(x / x.shift(7))`) rather than `pct_change` for on-chain change features. Percent changes produced 30+ standard-deviation outliers in the first notebook.
- Don't include composite scores that are exact combinations of other columns (like the earlier `OnChain_Activity_Score`). It's fine to keep one in `master.csv` for display, just not as a model feature.
- `cat_` columns hold readable strings (`pos`, `above_200dma`), not pre-encoded integers. Encoding happens inside each model pipeline.

---

## 6. Unsupervised outputs: Shawn · due Nov 20

### `data/processed/regimes.csv`

| Column | Type | Description |
|---|---|---|
| `date` | str | `YYYY-MM-DD` |
| `asset` | str | Asset code |
| `split` | str | `train` / `test` |
| `regime_id` | int | K-means cluster number |
| `regime_name` | str | Human-readable label, e.g. `calm`, `normal`, `stressed` (shown in the app) |
| `pc1` | float | First principal component score (for the app's PCA scatter) |
| `pc2` | float | Second principal component score |

### `data/processed/pca_explained_variance.csv`

| Column | Type | Description |
|---|---|---|
| `component` | str | `PC1`, `PC2`, … |
| `explained_variance` | float | Proportion of variance explained |
| `cumulative_variance` | float | Running total |

### `data/processed/regime_profiles.csv`

One row per regime: `regime_id`, `regime_name`, `n_days`, then the **mean of each clustering input feature** for that regime. This powers the "what does each regime mean?" panel.

**Rule:** scaler, PCA and K-means are fit on `split == "train"` rows, then applied to test rows with `.transform()` / `.predict()`.

---

## 7. Modeling outputs: Diego · due Nov 24

### `data/processed/predictions.csv`

One row per date × asset × model × feature set, covering both train (out-of-fold) and test rows.

| Column | Type | Description |
|---|---|---|
| `date` | str | `YYYY-MM-DD` |
| `asset` | str | Asset code |
| `split` | str | `train` / `test` |
| `model` | str | `baseline`, `logistic`, `knn`, `tree`, `ensemble` |
| `feature_set` | str | `market` (Model 1) or `market_onchain` (Model 2) |
| `prob_high_vol` | float | Predicted probability of high volatility, 0–1 |
| `pred` | int | Predicted class (0/1) at the chosen threshold |
| `actual` | int | True `high_vol_7d` (empty where unknown) |

Train-row predictions must be **out-of-fold** from walk-forward CV, never in-sample.

### `models/metrics.json`

Feeds the app's DataFacts panel and model-comparison page.

```json
{
  "generated_at": "2026-11-24",
  "target": "high_vol_7d",
  "train_period": ["2021-01-01", "2024-12-31"],
  "test_period": ["2025-01-01", "2025-12-31"],
  "final_model": {"model": "logistic", "feature_set": "market_onchain"},
  "decision_threshold": 0.5,
  "models": [
    {
      "model": "logistic",
      "feature_set": "market_onchain",
      "assets": ["btc", "eth", "xrp"],
      "features": ["mkt_vol_7d", "oc_adr_act_z30"],
      "cv": {"roc_auc": 0.00, "f1": 0.00, "precision": 0.00, "recall": 0.00},
      "test": {"roc_auc": 0.00, "f1": 0.00, "precision": 0.00, "recall": 0.00},
      "notes": "Standardized inputs, L2 penalty, C=1.0"
    }
  ]
}
```

(The feature list above is truncated. In the real file, list every feature used.)

### `models/experiment_log.csv`

One row per experiment run: `run_id`, `date_run`, `model`, `feature_set`, `params`, `cv_roc_auc`, `cv_f1`, `cv_recall`, `notes`, `owner`. The rubric explicitly grades whether experiments are tracked.

### Saved models (optional for the app)

`models/<model>_<feature_set>.joblib`: a fitted scikit-learn `Pipeline` (preprocessing + model). The app reads `predictions.csv` rather than running models, so these are mainly for reproducibility.

---

## 8. `reports/figures/`: Aeden · due Nov 24

The final EDA charts for slides and the app. For each chart:

- `<short_name>.png` (for slides, at least 1600px wide)
- `<short_name>.json` (Plotly figure via `fig.write_json()`, so the app can render it interactively), if made in Plotly

Name files descriptively: `vol_regimes_over_time.png`, not `fig3.png`.

---

## 9. `ai/logs/<your_name>.md`: everyone · ongoing

The rubric requires documenting all AI use. Add an entry whenever you use an AI tool:

```markdown
## 2026-11-08 · ChatGPT / Claude / Copilot
- **Used for:** Writing the Binance ZIP loader
- **Prompt:** (paste, or link to ai/prompts/<file>)
- **What it produced:** Function to read monthly kline ZIPs into one DataFrame
- **How I checked it:** Row counts = 1,826 per asset; no dates outside 2021–2025; spot-checked 3 closes against Binance
- **Files affected:** src/data/pull_binance.py
```

In code, flag AI-generated blocks:

```python
# [AI-GENERATED] Tool: <tool> | Log: ai/logs/<name>.md (2026-11-08) | Reviewed by: <name>
```

---

## Before you hand off: checklist

Run this on any row-level file before pushing it:

```python
import pandas as pd

def check_contract(path, required_cols):
    df = pd.read_csv(path)
    missing = set(required_cols) - set(df.columns)
    assert not missing, f"Missing columns: {missing}"
    assert df["date"].str.match(r"^\d{4}-\d{2}-\d{2}$").all(), "date must be YYYY-MM-DD"
    assert set(df["asset"].unique()) <= {"btc", "eth", "xrp", "sol"}, "bad asset codes"
    key = ["date", "asset"] + [c for c in ("model", "feature_set") if c in df.columns]
    assert not df.duplicated(key).any(), "duplicate rows"
    print(f"✓ {path}: {len(df):,} rows, {df['asset'].nunique()} assets, "
          f"{df['date'].min()} → {df['date'].max()}")

# e.g. check_contract("data/processed/master.csv", ["date", "asset", "close"])
```

---

## Changelog

| Date | Change | By |
|---|---|---|
| 2026-11-08 | Initial contract. SOL marked as no on-chain data. | Austin |
