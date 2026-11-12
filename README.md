# DS6021-Final-Project
Final Project for DS 6021

# CryptoLens
 
**Predicting 7-day cryptocurrency volatility risk and market regimes, with transparent "DataFacts" behind every prediction.**
 
DS 6021: Introduction to Predictive Modeling · Final Project · Group [#]
 
**Live app:** https://cryptolens-ds6021-dngt49c9gwjjcvhiezyzfy.streamlit.app/

**Slides:** [`docs/slides.pdf`](docs/slides.pdf)
 
> 🚧 **Draft.** Sections marked `TODO` get filled in as each phase wraps up. See the project timeline for owners and dates.
 
---
 
## Table of contents
 
1. [Overview](#overview)
2. [Research question](#research-question)
3. [Team](#team)
4. [Data sources](#data-sources)
5. [Repository structure](#repository-structure)
6. [Getting started](#getting-started)
7. [Running the pipeline](#running-the-pipeline)
8. [Methodology](#methodology)
9. [The CryptoLens app](#the-cryptolens-app)
10. [Results](#results)
11. [Use of generative AI](#use-of-generative-ai)
12. [Limitations](#limitations)
---
 
## Overview
 
CryptoLens is an interactive risk-intelligence app for Bitcoin (BTC), Ethereum (ETH), XRP, and Solana (SOL). Instead of predicting exact prices, which is a losing game, we classify whether an asset is likely to enter a **high-volatility period over the next 7 days**. We also use unsupervised learning to identify distinct **market regimes**.
 
Every prediction in the app comes with a **DataFacts** panel, a "nutrition label" for the model. It shows:
 
- where the data came from and how fresh it is
- which variables and model produced the prediction
- the model's validation metrics
- any known gaps or limitations
## Research question
 
> **Can market data combined with blockchain/on-chain activity improve predictions of 7-day cryptocurrency volatility risk compared with market data alone?**
 
To answer it, we compare two feature sets head-to-head:
 
| | Features |
|---|---|
| **Model 1** | Market variables only (price, volume, returns, volatility, momentum, sentiment, macro) |
| **Model 2** | Market variables + on-chain variables (active addresses, transaction counts, fees, transfer activity) |
 
Secondary question: can clustering and dimensionality reduction (K-means, PCA) find interpretable market regimes, and do those regimes improve the supervised models?
 
## Team
 
| Member | Role |
|---|---|
| Imaan [Last] | Data engineering: pulling, cleaning, and merging datasets |
| Aeden [Last] | Feature engineering & EDA |
| Diego [Last] | Predictive modeling & evaluation |
| Shawn [Last] | On-chain research & unsupervised learning (PCA, K-means regimes) |
| Austin [Last] | App development & integration |
 
<!-- TODO: reorder alphabetically by last name to match the title slide -->
 
## Data sources
 
**Study period:** Jan 1, 2021 – Dec 31, 2025 · **Frequency:** daily · **Assets:** BTC, ETH, XRP, SOL
 
| Source | What we use | Access | Why |
|---|---|---|---|
| [Binance Public Data](https://data.binance.vision) | Daily OHLCV, trade count, quote volume, taker-buy volume (`*USDT` spot pairs) | Free bulk downloads, no key | Deep, consistent exchange-level history for all four assets |
| [Coin Metrics Community API](https://docs.coinmetrics.io) | Active addresses, transaction count, fees, transfer value | Free, no key (CC BY-NC) | Standardized on-chain metrics across chains |
| [Alternative.me Fear & Greed Index](https://alternative.me/crypto/fear-and-greed-index/) | Daily sentiment score (0–100) + 5-level classification | Free, no key | Market-wide sentiment; adds a categorical variable |
| [FRED](https://fred.stlouisfed.org) | VIX, U.S. dollar index, 10-year Treasury yield | Free API key | Macro risk-off context |
| Regulatory/event table (hand-curated) | Date, asset, event type, jurisdiction, source URL | Built by us from SEC/CFTC and official project sources | Event context for the app; categorical features |
| [CoinGecko](https://www.coingecko.com/en/api) *(optional)* | Current prices for the app's live view | Free tier | Not used for historical modeling |
 
<!-- TODO (Imaan/Shawn): note any on-chain metrics unavailable for XRP or SOL after the coverage check -->
 
Raw and cleaned data are saved in `data/raw/` and `data/processed/`. A full variable list is in [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md).
 
## Repository structure
 
```
cryptolens/
├── app/                    # Streamlit app
│   ├── app.py              # entry point
│   ├── pages/              # one file per app page
│   └── components/         # DataFacts panel, charts, shared helpers
├── data/
│   ├── raw/                # untouched downloads (one folder per source)
│   ├── processed/          # master_v*.csv, features_v*.csv, regimes.csv, predictions.csv
│   ├── external/           # events.csv (hand-curated regulatory/event table)
│   └── DATA_DICTIONARY.md
├── src/
│   ├── data/               # pull_binance.py, pull_coinmetrics.py, pull_fng.py, pull_fred.py, build_master.py
│   ├── features/           # build_features.py, target definition
│   ├── models/             # train.py, evaluate.py, baseline.py
│   └── unsupervised/       # pca.py, regimes.py
├── notebooks/              # 01_eda.ipynb, 02_modeling.ipynb, 03_unsupervised.ipynb
├── models/                 # saved model files (.joblib) + metrics.json
├── reports/figures/        # exported charts for slides and app
├── docs/                   # slides.pdf, AI_USAGE.md
├── ai/                     # CLAUDE.md, skills, versioned prompts
├── run_pipeline.py         # one command: raw data → processed → models
├── requirements.txt
└── README.md
```
 
### File naming conventions
 
- Data files: `snake_case.csv`, versioned with `_v1`, `_v2`, … when the schema changes
- Columns: `snake_case`, with one row per `date` × `asset`
- Dates: UTC, ISO format (`YYYY-MM-DD`)
- Asset codes: `btc`, `eth`, `xrp`, `sol`
## Getting started
 
**Requirements:** Python 3.11+
 
```bash
git clone [repo URL]
cd cryptolens
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
 
FRED needs a free API key ([get one here](https://fred.stlouisfed.org/docs/api/api_key.html)). Put it in a `.env` file in the project root:
 
```
FRED_API_KEY=your_key_here
```
 
`.env` is in `.gitignore`. **Never commit keys.**
 
## Running the pipeline
 
Reproduce everything from scratch:
 
```bash
python run_pipeline.py
```
 
Or run step by step:
 
```bash
python -m src.data.pull_binance          # 1. download raw market data
python -m src.data.pull_coinmetrics      # 2. download on-chain data
python -m src.data.pull_fng              # 3. Fear & Greed index
python -m src.data.pull_fred             # 4. macro indicators
python -m src.data.build_master          # 5. clean + merge → data/processed/master.csv
python -m src.features.build_features    # 6. features + target → features.csv
python -m src.unsupervised.regimes       # 7. PCA + K-means → regimes.csv
python -m src.models.train               # 8. train + evaluate → models/, predictions.csv
```
 
Launch the app locally:
 
```bash
streamlit run app/app.py
```
 
<!-- TODO: confirm script names once the pipeline is built -->
 
## Methodology
 
### Target variable
 
`high_vol_7d` = 1 if an asset's realized volatility over the **next 7 days** is above that asset's 75th percentile, else 0.
 
The percentile thresholds are computed on the **2021–2024 training data only**, so no information from the test period leaks into the labels.
 
<!-- TODO (Aeden/Diego): confirm threshold and volatility definition -->
 
### Avoiding look-ahead bias
 
- Features dated day *t* use only information available by the end of day *t*. The target covers days *t+1* through *t+7*.
- **Train/development:** 2021–2024. **Final test:** 2025, evaluated once, at the end.
- Model tuning uses walk-forward cross-validation (`TimeSeriesSplit`), not random K-fold. The 7-day windows overlap, so random splits would inflate scores.
### Features
 
| Type | Examples |
|---|---|
| Numeric (market) | Daily & 7-day returns, 7/30-day realized volatility, momentum, volume change, moving averages, drawdown, BTC correlation |
| Numeric (on-chain) | Active addresses, transaction count, fees, transfer value (and their changes) |
| Numeric (sentiment/macro) | Fear & Greed score, VIX, dollar index, 10Y yield |
| Categorical | Asset, consensus mechanism, Fear & Greed class, trend state (above/below 200-day MA), halving-cycle phase, day of week, event type, market regime |
 
### Models
 
| Approach | Models |
|---|---|
| Baseline | Naive persistence (current volatility is high → predict high) |
| Supervised | Logistic regression, KNN, classification tree, tree ensemble |
| Unsupervised | PCA (dimensionality reduction), K-means (market regimes) |
 
**Evaluation metrics:** ROC-AUC, F1, precision and recall on the high-volatility class, all compared against the baseline.
 
All experiments are logged in [`models/experiment_log.csv`](models/experiment_log.csv). <!-- TODO -->
 
## The CryptoLens app
 
Built with **Streamlit** and deployed on **Streamlit Community Cloud**. The app reads precomputed predictions; it doesn't retrain models live.
 
Pick an asset to see:
 
1. **Current market regime** from K-means clustering
2. **Predicted 7-day volatility risk** with the predicted probability
3. **Historical trends** and key indicators
4. **Model comparison**: market-only vs. market + on-chain
5. **Regulatory/event context** overlaid on the price history
6. **DataFacts panel**: sources, data freshness, variables, model type, validation metrics, missing-data warnings, limitations
<!-- TODO (Austin): screenshots once app v1 is up -->
 
## Results
 
<!-- TODO: fill in after the Nov 24 model freeze -->
 
| Model | Features | ROC-AUC | F1 | Recall (high vol) |
|---|---|---|---|---|
| Naive baseline | – | | | |
| Logistic regression | Market only | | | |
| Logistic regression | Market + on-chain | | | |
| … | | | | |
 
**Key findings:** TODO
 
## Use of generative AI
 
Per the course policy, we document all generative-AI use:
 
- **Full write-up:** [`docs/AI_USAGE.md`](docs/AI_USAGE.md): which tools we used, for what, and how we checked the output
- **AI-generated code** is flagged in the source with a comment block:
```python
  # [AI-GENERATED] Tool: <tool> | Prompt: ai/prompts/<file> | Reviewed by: <name>
  # Validation: <how we tested it>
```
- **Prompts** are versioned in [`ai/prompts/`](ai/prompts/) (e.g., `app_layout_v1.md`, `app_layout_v2.md`)
- **CLAUDE.md / skills** used for the project are in [`ai/`](ai/)
## Limitations
 
- Crypto markets change structurally (ETFs, regulation, exchange collapses), so patterns from 2021–2024 may not hold going forward.
- Free on-chain data coverage varies by chain; XRP and SOL may have fewer metrics than BTC and ETH.
- The Fear & Greed index is market-wide and BTC-centric, not asset-specific.
- Binance prices reflect a single exchange.
- **This project is for educational purposes and is not financial advice.**
---
 
*Data attribution: Coin Metrics Community Data (CC BY-NC 4.0), Alternative.me Fear & Greed Index, Federal Reserve Bank of St. Louis (FRED), Binance Public Data.*
