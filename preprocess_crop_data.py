from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(BASE_DIR / ".matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.preprocessing import LabelEncoder, StandardScaler


DATA_PATH = BASE_DIR / "ahs_dataset_nisr.csv"
OUTPUT_DIR = BASE_DIR / "outputs"
GRAPH_DIR = OUTPUT_DIR / "graphs"
PROCESSED_DATA_PATH = OUTPUT_DIR / "processed_crop_dataset.csv"
REPORT_PATH = OUTPUT_DIR / "preprocessing_report.md"

PROPOSAL_CROPS = ["maize", "beans", "cassava", "rice", "irish_potato"]
FEATURE_COLUMNS = [
    "soil_ph",
    "nitrogen",
    "phosphorus",
    "potassium",
    "annual_rainfall_mm",
    "avg_temperature_C",
    "avg_humidity_pct",
    "altitude_m",
]
TARGET_COLUMN = "recommended_crop"
DISTRICT_COLUMN = "district_real"


def ensure_output_dirs() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    GRAPH_DIR.mkdir(exist_ok=True)


def load_project_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    scoped_df = df[df[TARGET_COLUMN].isin(PROPOSAL_CROPS)].copy()
    return scoped_df


def build_preprocessed_dataset() -> tuple[pd.DataFrame, dict[str, object]]:
    df = load_project_dataset()
    working_df = df[[DISTRICT_COLUMN, TARGET_COLUMN, *FEATURE_COLUMNS]].copy()

    missing_before = working_df[FEATURE_COLUMNS].isna().sum()

    for column in FEATURE_COLUMNS:
        district_means = working_df.groupby(DISTRICT_COLUMN)[column].transform("mean")
        working_df[column] = working_df[column].fillna(district_means)
        working_df[column] = working_df[column].fillna(working_df[column].median())

    missing_after = working_df[FEATURE_COLUMNS].isna().sum()

    label_encoder = LabelEncoder()
    working_df["target_encoded"] = label_encoder.fit_transform(working_df[TARGET_COLUMN])

    scaler = StandardScaler()
    scaled_values = scaler.fit_transform(working_df[FEATURE_COLUMNS])
    scaled_df = pd.DataFrame(
        scaled_values,
        columns=[f"{column}_scaled" for column in FEATURE_COLUMNS],
        index=working_df.index,
    )

    processed_df = pd.concat(
        [
            working_df[[DISTRICT_COLUMN, TARGET_COLUMN, "target_encoded"]].reset_index(drop=True),
            working_df[FEATURE_COLUMNS].reset_index(drop=True),
            scaled_df.reset_index(drop=True),
        ],
        axis=1,
    )

    metadata = {
        "raw_shape": tuple(pd.read_csv(DATA_PATH).shape),
        "scoped_shape": tuple(working_df.shape),
        "missing_before": missing_before,
        "missing_after": missing_after,
        "class_counts": working_df[TARGET_COLUMN].value_counts().sort_values(ascending=False),
        "label_encoder": label_encoder,
        "label_mapping": {
            label: int(code)
            for code, label in enumerate(label_encoder.classes_)
        },
        "raw_feature_summary": working_df[FEATURE_COLUMNS].describe().round(3),
        "scaled_feature_summary": pd.DataFrame(
            scaled_values, columns=FEATURE_COLUMNS
        ).describe().round(3),
    }
    return processed_df, metadata


def create_graphs(processed_df: pd.DataFrame) -> list[Path]:
    sns.set_theme(style="whitegrid")
    graph_paths: list[Path] = []

    class_plot_path = GRAPH_DIR / "crop_distribution.png"
    plt.figure(figsize=(10, 6))
    order = processed_df[TARGET_COLUMN].value_counts().index
    sns.countplot(data=processed_df, y=TARGET_COLUMN, order=order, color="#2a9d8f")
    plt.title("Proposal Crop Distribution")
    plt.xlabel("Number of Records")
    plt.ylabel("Crop")
    plt.tight_layout()
    plt.savefig(class_plot_path, dpi=200)
    plt.close()
    graph_paths.append(class_plot_path)

    correlation_plot_path = GRAPH_DIR / "feature_correlation_heatmap.png"
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        processed_df[FEATURE_COLUMNS].corr(),
        annot=True,
        cmap="YlGnBu",
        fmt=".2f",
        square=True,
    )
    plt.title("Correlation Heatmap of Proposal Features")
    plt.tight_layout()
    plt.savefig(correlation_plot_path, dpi=200)
    plt.close()
    graph_paths.append(correlation_plot_path)

    raw_boxplot_path = GRAPH_DIR / "raw_feature_boxplots.png"
    raw_melted = processed_df[FEATURE_COLUMNS].melt(
        var_name="Feature", value_name="Value"
    )
    plt.figure(figsize=(14, 6))
    sns.boxplot(data=raw_melted, x="Feature", y="Value", color="#90be6d")
    plt.title("Raw Feature Distributions Before Scaling")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(raw_boxplot_path, dpi=200)
    plt.close()
    graph_paths.append(raw_boxplot_path)

    scaled_boxplot_path = GRAPH_DIR / "scaled_feature_boxplots.png"
    scaled_columns = [f"{column}_scaled" for column in FEATURE_COLUMNS]
    scaled_melted = processed_df[scaled_columns].melt(
        var_name="Feature", value_name="Scaled Value"
    )
    plt.figure(figsize=(14, 6))
    sns.boxplot(data=scaled_melted, x="Feature", y="Scaled Value", color="#577590")
    plt.title("Scaled Feature Distributions After Standardization")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(scaled_boxplot_path, dpi=200)
    plt.close()
    graph_paths.append(scaled_boxplot_path)

    return graph_paths


def build_report(metadata: dict[str, object], graph_paths: list[Path]) -> str:
    missing_before = metadata["missing_before"]
    missing_after = metadata["missing_after"]
    class_counts = metadata["class_counts"]
    label_mapping = metadata["label_mapping"]
    raw_feature_summary = metadata["raw_feature_summary"]
    scaled_feature_summary = metadata["scaled_feature_summary"]

    graph_lines = "\n".join(
        f"- `{path.relative_to(BASE_DIR).as_posix()}`" for path in graph_paths
    )
    label_lines = "\n".join(
        f"- `{label}` -> `{code}`" for label, code in label_mapping.items()
    )

    report = f"""# Crop Data Preprocessing Report

## Dataset Scope
- Raw dataset shape: `{metadata["raw_shape"]}`
- Proposal-scoped dataset shape: `{metadata["scoped_shape"]}`
- Target column: `{TARGET_COLUMN}`
- Environmental features used: `{", ".join(FEATURE_COLUMNS)}`
- Crop classes kept to match the proposal scope: `{", ".join(PROPOSAL_CROPS)}`

## Step-by-Step Preprocessing
1. Loaded `ahs_dataset_nisr.csv`.
2. Filtered the dataset to the five crops named in the proposal.
3. Selected the eight environmental features described in Chapter Three.
4. Checked missing values in the modeling features.
5. Applied district-level mean imputation with median fallback where needed.
6. Encoded the crop target using label encoding.
7. Standardized the eight numeric features using `StandardScaler`.
8. Saved the processed dataset and graphs to the `outputs` folder.

## Missing-Value Check Before Imputation
```text
{missing_before.to_frame("missing_count").to_string()}
```

## Missing-Value Check After Imputation
```text
{missing_after.to_frame("missing_count").to_string()}
```

## Class Distribution
```text
{class_counts.to_frame("count").to_string()}
```

## Label Encoding Map
{label_lines}

## Raw Feature Summary
```text
{raw_feature_summary.to_string()}
```

## Scaled Feature Summary
```text
{scaled_feature_summary.to_string()}
```

## Graphs Generated
{graph_lines}
"""
    return report


def main() -> None:
    ensure_output_dirs()
    processed_df, metadata = build_preprocessed_dataset()
    processed_df.to_csv(PROCESSED_DATA_PATH, index=False)
    graph_paths = create_graphs(processed_df)
    REPORT_PATH.write_text(build_report(metadata, graph_paths), encoding="utf-8")

    print(f"Saved processed dataset to: {PROCESSED_DATA_PATH}")
    print(f"Saved preprocessing report to: {REPORT_PATH}")
    print("Saved graphs:")
    for graph_path in graph_paths:
        print(f"- {graph_path}")


if __name__ == "__main__":
    main()
