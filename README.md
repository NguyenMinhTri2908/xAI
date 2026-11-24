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
| `src/state/` | Reflex reactive state hierarchy (`BaseUnderwritingState` → `DatasetState` → `FeatureSearchState` → `InspectionState` → `SimulatorState` → `OptimizationState` → `UnderwritingState`). |
| `src/ui/` & `src/app.py` | Multi-page dark-theme Reflex UI (`/data` and `/inspection`) with `rxconfig.py` entry config. |
| `tests/` | 29 automated unit & end-to-end integration tests (`test_domain_services.py`, `test_fix_verification.py`, `test_inspect_flow.py`). |
| `data/production/demo_samples.parquet` | Bundled 1,000-client production sample (`2.7 MB`) enabling zero-setup app launch and full test execution without Kaggle downloads. |
| `data/raw/.gitkeep` | Placeholder directory for optional raw Kaggle CSVs (excluded from version control). |

### Key Financial & Decision Rules
- **Dual-Gate Underwriting Rule:** An application is **APPROVED** if and only if:
  1. Ensemble **PD <= 6.80%**, **AND**
  2. Contractual **DTI <= 50.0%**.
- **EBA 5-Component Risk-Based Pricing:**
  $$\text{Rate}_{\text{raw}} = R_{\text{FTP}}(\text{term}) + C_{\text{OpEx}}\ (1.80\%) + (\text{PD} \times \text{LGD}_{65\%}) + S_{\text{Capital}}\ (1.80\%) + M_{\text{Target}}\ (1.50\%)$$
  clamped between a commercial floor of **8.50%** and regulatory ceiling of **25.00%**, with contractual monthly installment computed using the actuarial annuity (EMI) formula.

---

## Prerequisites & OS Setup

### 1. Python Version
- **Python 3.11 – 3.13** recommended (verified on **Python `3.13.5`**).

### 2. OS System Libraries
LightGBM, XGBoost, and Reflex require runtime native dependencies depending on your operating system:

- **macOS (Homebrew):**
  ```bash
  brew install libomp