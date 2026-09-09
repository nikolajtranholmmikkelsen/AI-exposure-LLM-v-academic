"""Check the saved research outputs without rerunning the estimation pipeline."""
from pathlib import Path

import pandas as pd

RESULTS = Path(__file__).resolve().parents[1] / "results"
occupations = pd.read_csv(RESULTS / "task/occupation_exposure.csv")
tasks = pd.read_csv(RESULTS / "task/task_exposure.csv")
comparison = pd.read_csv(RESULTS / "hybrid/comparison_occupation.csv")
summary = pd.read_csv(RESULTS / "summary.csv", index_col="statistic")["value"]

def test_occupation_count():
    assert len(occupations) == 923

def test_task_count():
    assert len(tasks) == 18796

def test_comparison_count():
    assert len(comparison) == 683

def test_exposure_bounds():
    for path in RESULTS.rglob("*.csv"):
        table = pd.read_csv(path)
        for column in table.columns.intersection(["exposure", "hybrid_exposure"]):
            assert table[column].between(0, 1).all(), (path, column)

def test_pearson_correlation():
    assert abs(summary["task_aioe_pearson"] - 0.8886) < 0.001

def test_spearman_correlation():
    assert abs(summary["task_aioe_spearman"] - 0.8851) < 0.001

def test_unique_occupation_codes():
    assert occupations["O*NET-SOC Code"].is_unique
