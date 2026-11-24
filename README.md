# XAI Lending Platform: Explainable Credit Underwriting & Loan Restructuring

Pure Python full-stack **Explainable AI (XAI) Credit Underwriting Platform** built with **Reflex**, combining a 10-fold LightGBM + XGBoost ensemble across 891 engineered features, exact **TreeSHAP** local attributions, **EBA 5-Component Risk-Based Pricing (RBP)**, an **Actuarial EMI What-If Simulator**, and a **Vectorized AI Auto-Optimize** counterfactual loan restructuring engine.

---

## Architecture & Core Capabilities

The codebase follows a clean **Domain-Driven Design (DDD)** separation:

| Module / Path | Responsibility |
| :--- | :--- |
| `src/config/` | Centralized cross-platform path resolution (`paths.py`), retail pricing parameters (`pricing_config.py`), and JSON schema/constraint metadata (`src/config/metadata/*.json`) covering **891 aligned model features**. |
| `src/data_processing/` | Fair-Lending-compliant ETL pipelines transforming raw *Home Credit* tables and enforcing strict removal of prohibited demographic attributes. |
| `src/engine/` | `CreditScoringEngine` (5 LightGBM + 5 XGBoost weighted soft voting, vectorized `predict_batch_pd`, `shap.TreeExplainer`) and `RiskBasedPricingEngine` (EBA 5-component RBP & Actuarial EMI). |
| `src/models/` | Pre-trained 10-fold binary model weights (`lgb_model_fold_1..5.joblib`, `xgb_model_fold_1..5.joblib`, `~40.7 MB` total). |
| `src/services/` | Stateless domain logic: dataset ingestion (`ingestion_service.py`), TreeSHAP formatting (`explanation_service.py`), Actuarial EMI/DTI calculations (`financial_service.py`), and vectorized counterfactual search (`restructuring_service.py`). |
| `src/state/` | Reflex reactive state hierarchy (`BaseUnderwritingState` -> `DatasetState` -> `FeatureSearchState` -> `InspectionState` -> `SimulatorState` -> `OptimizationState` -> `UnderwritingState`). |
| `src/ui/` & `src/app.py` | Multi-page dark-theme Reflex UI (`/data` and `/inspection`) with `rxconfig.py` entry config. |
| `tests/` | 29 automated unit & end-to-end integration tests (`test_domain_services.py`, `test_fix_verification.py`, `test_inspect_flow.py`). |
| `data/production/demo_samples.parquet` | Bundled 1,000-client production sample (`2.7 MB`) enabling zero-setup app launch and full test execution without Kaggle downloads. |
| `data/raw/.gitkeep` | Placeholder directory for optional raw Kaggle CSVs (excluded from version control). |

### Key Financial & Decision Rules

- **Dual-Gate Underwriting Rule:** An application is **APPROVED** if and only if:
  1. Ensemble **PD <= 6.80%**, **AND**
  2. Contractual **DTI <= 50.0%**.
- **EBA 5-Component Risk-Based Pricing (RBP):** Contractual interest rates aggregate five auditable banking cost components, clamped between a commercial floor of **8.50%** and a regulatory ceiling of **25.00%**, with monthly installments computed using the actuarial annuity (EMI) formula:

$$
\text{Rate}_{\text{raw}} = R_{\text{FTP}}(\text{term}) + C_{\text{OpEx}}\ (1.80\%) + (\text{PD} \times \text{LGD}_{65\%}) + S_{\text{Capital}}\ (1.80\%) + M_{\text{Target}}\ (1.50\%)
$$

---

## Prerequisites & OS Setup

### 1. Python Version
- **Python 3.11 – 3.13** recommended (verified on **Python `3.13.5`**).

### 2. OS System Libraries
LightGBM, XGBoost, and Reflex require runtime native dependencies depending on your operating system:

- **macOS (Homebrew):**
  ```bash
  brew install libomp
  ```
- **Linux (Ubuntu / Debian):**
  ```bash
  sudo apt-get update && sudo apt-get install -y libgomp1 unzip
  ```
  *(Note: `libgomp1` provides OpenMP support for LightGBM/XGBoost; `unzip` is used when Reflex bootstraps Bun.)*
- **Windows:**
  - Install the [Microsoft Visual C++ Redistributable (`vc_redist.x64`)](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist) if not already present.

### 3. Reflex Frontend Toolchain
- Reflex automatically downloads and configures its **Bun / Node.js** frontend build toolchain on the first `reflex run` execution (internet access required on initial startup).

---

## Quickstart Installation

```bash
# 1. Clone the repository
git clone https://github.com/NguyenMinhTri2908/xAI.git
cd xAI

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows (Command Prompt / PowerShell)

# 3. Install pinned, cross-platform dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Out-of-the-Box Automated Verification (29 Tests)

All **29 unit and end-to-end integration tests** run immediately after installation using the bundled `data/production/demo_samples.parquet` (1,000 clients) and pre-trained `src/models/` weights — **no external Kaggle download is required**:

```bash
python -m unittest discover -s tests -v
```

Verification suite coverage:
- **`tests/test_domain_services.py`**: Actuarial EMI derivation, EBA pricing components, floor/ceiling clamping, Dual-Gate decisions, TreeSHAP formatting, and counterfactual candidate ranking.
- **`tests/test_fix_verification.py`**: Vectorized `predict_batch_pd` parity, real-time `sim_dti` recomputation prior to Dual-Gate evaluation, singleton scoring engine invariants, fail-closed unrescuable guards, and reactive state synchronization.
- **`tests/test_inspect_flow.py`**: End-to-end client scoring on `demo_samples.parquet`, 891-feature TreeSHAP extraction, baseline vs. restructured archetypes (Approved `#100001`, Rescued `#100005`, Unrescuable `#103771`).

---

## Launching the Web Application

Start the Reflex backend & frontend server from the repository root:

```bash
reflex run
```

Once compiled, open your browser to:
- **Data Management & Batch Registry (`/data` or `/`):** `http://localhost:3000/data`
  - Auto-detects `data/production/demo_samples.parquet` on startup, or lets you upload custom `.csv` / `.parquet` client files (`SK_ID_CURR` primary key required).
- **Client Inspection Workbench (`/inspection`):** `http://localhost:3000/inspection`
  - Automatically loads `demo_samples.parquet` if no dataset is active, displaying 10-fold PD scoring, TreeSHAP risk/positive drivers, EBA Risk-Based Pricing breakdown, real-time **What-If Simulator**, and **AI Auto-Optimize** loan restructuring proposals.

---

## Optional: Full-Scale 48,744-Client Kaggle ETL Setup

To rebuild and score the complete **48,744-client** inference dataset (`data/production/test_features_master.parquet`) instead of using the 1,000-client `demo_samples.parquet`:

- **Dataset Source:** [Home Credit Default Risk (Kaggle)](https://www.kaggle.com/c/home-credit-default-risk/data) (`https://www.kaggle.com/c/home-credit-default-risk/data`)

> **Important:** **`application_train.csv` is NOT required.** All 10 trained LightGBM/XGBoost fold models (`src/models/`) and training distribution benchmarks (`src/config/metadata/train_benchmarks.json`) are already bundled in the repository.

Download the following **7 CSV files** (`application_test.csv` plus the **6 historical behavioral tables**) from Kaggle and place them inside `data/raw/`:
- `application_test.csv`
- `bureau.csv`
- `bureau_balance.csv`
- `previous_application.csv`
- `POS_CASH_balance.csv`
- `installments_payments.csv`
- `credit_card_balance.csv`

You can then run either workflow below:

### Option A — Interactive UI Upload (`/data`)
1. With the 6 historical CSVs placed inside `data/raw/`, pre-aggregate any needed historical `.parquet` lookup tables (or execute the 6 historical pipelines below once) into `data/preprocess/table/`.
2. Launch `reflex run`, navigate to **Data Management & Batch Registry (`/data`)**, and upload `application_test.csv` (or any custom client `.csv` / `.parquet` batch) via the upload dropzone — the UI automatically triggers `process_master_pipeline`, aligns the **891 model features**, and saves the resulting dataset into `data/production/`.

### Option B — Command-Line Batch Pipeline
Run the 6 historical ETL modules (writing intermediate `.parquet` tables to `data/preprocess/table/` via `src/config/paths.py`), followed by the master feature builder:

```bash
python -m src.data_processing.bureau_balance_pipeline
python -m src.data_processing.bureau_pipeline
python -m src.data_processing.previous_application_pipeline
python -m src.data_processing.pos_cash_pipeline
python -m src.data_processing.installments_pipeline
python -m src.data_processing.credit_card_pipeline
python -m src.data_processing.build_master_dataset
```

This generates `data/production/test_features_master.parquet` with shape **`48,744 × 892`** (`891 aligned model features + SK_ID_CURR`, locally gitignored) and refreshes `demo_samples.parquet`.
