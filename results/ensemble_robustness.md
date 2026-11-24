# Ensemble evaluation and generalization check

## Purpose

Compare equal-weight soft voting with the existing single-model baselines, and test whether the current high scores persist when duplicate message bodies are kept on one side of the split and when an entire data source is held out.

## Data and protocol

- Input: `data_train/processed/merged_clean.csv`.
- After removing rows without subject/body/label/source: 204,294 emails from 10 represented sources.
- 1,353 rows have a body that occurs elsewhere in the cleaned dataset. The group split keeps each normalized body hash wholly in train or test.
- Group holdout: 80/20 `GroupShuffleSplit`, random state 42. It prevents repeated bodies from crossing the split, but the same source collections still occur in both sets.
- Source holdout: all 38,936 CEAS_08 rows are test data; the other sources are training data.
- TF-IDF and security features are fit only on each training partition. Model thresholds in this comparison are 0.50. Production currently applies a 0.60 threshold and heuristic guardrail, so these numbers are model-comparison results, not production alert rates.
- Ensemble probabilities are equal-weight averages; weights were not tuned against the test data.

## Results

| Evaluation split | Model | Accuracy | Phishing F1 | ROC AUC | Brier (lower is better) |
|---|---|---:|---:|---:|---:|
| Body-group holdout | Logistic Regression | 98.94% | 98.89% | 0.9992 | 0.0085 |
| Body-group holdout | Soft vote LR + XGBoost | 99.02% | 98.98% | 0.9993 | 0.0097 |
| CEAS_08 source holdout | Random Forest | 84.09% | 84.49% | 0.8773 | 0.1527 |
| CEAS_08 source holdout | Logistic Regression | 84.22% | 84.48% | 0.8465 | 0.1486 |
| CEAS_08 source holdout | XGBoost | 87.41% | 88.11% | **0.9373** | **0.1128** |
| CEAS_08 source holdout | Soft vote RF + XGBoost | **87.58%** | **88.29%** | 0.8978 | 0.1219 |

The LR + XGBoost vote gains only 0.09 percentage points of phishing F1 over LR on the body-group split. On the source holdout, RF + XGBoost gains 0.18 points of F1 over XGBoost at the 0.50 decision threshold, while its AUC and Brier score are worse. The small threshold-specific gain does not establish a reliable ensemble advantage.

## Interpretation and decision

Do not replace the production Random Forest with an ensemble yet. The measured gains are small and inconsistent across evaluation measures, while the ensemble adds model size, dependencies, inference paths, and probability calibration work. XGBoost alone is a promising candidate for a follow-up source-held-out evaluation, but one held-out corpus is insufficient to select it for production.

The high 98–99% figures are reproducible on a random split that still contains examples from the same sources in both train and test. They fall to roughly 84–88% on the CEAS_08 source holdout. This is evidence of a substantial source/domain shift and a better explanation for why the original figures may look optimistic than deliberately lowering scores.

The label is also broader than phishing: the merged corpus combines spam, phishing, and legitimate email collections, and labels are inherited from those collections. The report should describe the target as the dataset's positive class (spam/phishing as labeled by the source corpora) unless the labels are audited and relabeled specifically for phishing. These measurements do not prove performance against modern targeted phishing, BEC, or Vietnamese email.

## Reproduction

Run from the project root:

```powershell
python -u scripts/ensemble_robustness.py
```

Machine-readable metrics are in `results/ensemble_robustness.csv`. The production model and UI were not changed because the evaluation did not show a sufficiently consistent ensemble improvement to justify deploying one.
