from __future__ import annotations

import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(BASE_DIR / ".matplotlib"))

import joblib
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from preprocess_crop_data import (
    FEATURE_COLUMNS,
    GRAPH_DIR,
    OUTPUT_DIR,
    TARGET_COLUMN,
    build_preprocessed_dataset,
    ensure_output_dirs,
    load_project_dataset,
)


MODEL_PATH = BASE_DIR / "models" / "crop_recommendation_pipeline.joblib"
LABEL_ENCODER_PATH = BASE_DIR / "models" / "crop_label_encoder.joblib"
METRICS_CSV_PATH = OUTPUT_DIR / "model_comparison_metrics.csv"
BEST_MODEL_JSON_PATH = OUTPUT_DIR / "best_model_summary.json"
CLASSIFICATION_REPORT_PATH = OUTPUT_DIR / "best_model_classification_report.txt"
CONFUSION_MATRIX_PATH = GRAPH_DIR / "best_model_confusion_matrix.png"


def build_model_candidates() -> dict[str, object]:
    return {
        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            random_state=42,
            n_jobs=1,
            class_weight="balanced_subsample",
        ),
        "Decision Tree": DecisionTreeClassifier(
            random_state=42,
            class_weight="balanced",
        ),
        "Naive Bayes": GaussianNB(),
        "KNN": KNeighborsClassifier(n_neighbors=7),
    }


def evaluate_models() -> dict[str, object]:
    df = load_project_dataset()
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=42,
        stratify=y,
    )

    results: list[dict[str, object]] = []
    best_payload: dict[str, object] | None = None

    for model_name, model in build_model_candidates().items():
        pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", model),
            ]
        )
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)

        metrics = {
            "model": model_name,
            "accuracy": accuracy_score(y_test, predictions),
            "precision_weighted": precision_score(
                y_test, predictions, average="weighted", zero_division=0
            ),
            "recall_weighted": recall_score(
                y_test, predictions, average="weighted", zero_division=0
            ),
            "f1_weighted": f1_score(
                y_test, predictions, average="weighted", zero_division=0
            ),
            "f1_macro": f1_score(
                y_test, predictions, average="macro", zero_division=0
            ),
        }
        results.append(metrics)

        if best_payload is None or metrics["f1_weighted"] > best_payload["metrics"]["f1_weighted"]:
            best_payload = {
                "model_name": model_name,
                "pipeline": pipeline,
                "metrics": metrics,
                "y_test": y_test,
                "predictions": predictions,
            }

    if best_payload is None:
        raise RuntimeError("No model results were produced.")

    results_df = pd.DataFrame(results).sort_values(
        by="f1_weighted", ascending=False
    )
    return {
        "results_df": results_df,
        "best_payload": best_payload,
    }


def save_confusion_matrix(y_true: pd.Series, y_pred: pd.Series, labels: list[str]) -> None:
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        matrix,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
    )
    plt.title("Best Model Confusion Matrix")
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.tight_layout()
    plt.savefig(CONFUSION_MATRIX_PATH, dpi=200)
    plt.close()


def main() -> None:
    ensure_output_dirs()
    _, preprocessing_metadata = build_preprocessed_dataset()

    evaluation_payload = evaluate_models()
    results_df = evaluation_payload["results_df"]
    best_payload = evaluation_payload["best_payload"]

    results_df.to_csv(METRICS_CSV_PATH, index=False)
    joblib.dump(best_payload["pipeline"], MODEL_PATH)
    joblib.dump(preprocessing_metadata["label_encoder"], LABEL_ENCODER_PATH)

    labels = sorted(best_payload["y_test"].unique().tolist())
    save_confusion_matrix(
        best_payload["y_test"],
        best_payload["predictions"],
        labels,
    )

    report = classification_report(
        best_payload["y_test"],
        best_payload["predictions"],
        zero_division=0,
    )
    CLASSIFICATION_REPORT_PATH.write_text(report, encoding="utf-8")

    summary = {
        "selected_model": best_payload["model_name"],
        "selection_rule": "Highest weighted F1-score among the four proposal models",
        "train_test_split": "70/30 with stratification and random_state=42",
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "metrics": {
            key: round(float(value), 4)
            for key, value in best_payload["metrics"].items()
            if key != "model"
        },
    }
    BEST_MODEL_JSON_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Model comparison")
    print(results_df.round(4).to_string(index=False))
    print()
    print(f"Best model: {best_payload['model_name']}")
    print(f"Saved trained model to: {MODEL_PATH}")
    print(f"Saved metrics to: {METRICS_CSV_PATH}")
    print(f"Saved summary to: {BEST_MODEL_JSON_PATH}")
    print(f"Saved classification report to: {CLASSIFICATION_REPORT_PATH}")
    print(f"Saved confusion matrix to: {CONFUSION_MATRIX_PATH}")


if __name__ == "__main__":
    main()
