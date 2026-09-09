"""Check the physical override rules and the unchanged comparison sample."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/robustness"


def test_rule_membership_and_zero_overrides():
    audit = pd.read_csv(OUT / "activity_audit.csv")
    tasks = pd.read_csv(OUT / "task_overrides.csv")
    keys = ["O*NET-SOC Code", "Task ID"]
    for rule, codes in [("narrow", ["4.A.3.a.1", "4.A.3.a.2"]),
                        ("broad", ["4.A.3.a.1", "4.A.3.a.2", "4.A.3.a.3", "4.A.3.a.4"])]:
        expected = audit.assign(flag=audit['GWA Element ID'].isin(codes)).groupby(keys).flag.any()
        checked = tasks.set_index(keys).join(expected)
        assert checked[rule + '_flag'].eq(checked.flag).all()
        assert checked.loc[checked.flag, rule + '_exposure'].eq(0).all()
        assert checked.loc[~checked.flag, rule + '_exposure'].eq(checked.loc[~checked.flag, 'baseline_exposure']).all()


def test_weights_and_aggregation():
    tasks = pd.read_csv(OUT / "task_overrides.csv")
    occ = pd.read_csv(OUT / "occupation_exposure.csv").set_index('O*NET-SOC Code')
    original = pd.read_csv(ROOT / 'results/task/task_exposure.csv')
    assert len(tasks) == len(original) == 18796
    assert np.allclose(tasks.weight, tasks.importance * tasks.relevance / 100)
    for rule in ['narrow', 'broad']:
        numerator = (tasks.weight * tasks[rule + '_exposure']).groupby(tasks['O*NET-SOC Code']).sum()
        denominator = tasks.groupby('O*NET-SOC Code').weight.sum()
        assert np.allclose(occ[rule], (numerator / denominator).round(4).reindex(occ.index))
    assert (occ.broad <= occ.narrow).all() and (occ.narrow <= occ.original).all()


def test_fixed_sample_and_correlations():
    comp = pd.read_csv(OUT / 'comparison_occupation.csv')
    original = pd.read_csv(ROOT / 'results/hybrid/comparison_occupation.csv')
    pd.testing.assert_frame_equal(comp[['soc6', 'title', 'AIOE']], original[['soc6', 'title', 'AIOE']])
    assert len(comp) == 683
    summary = pd.read_csv(OUT / 'summary.csv').set_index('variant')
    for rule in ['original', 'narrow', 'broad']:
        assert np.isclose(summary.loc[rule, 'pearson'], comp[rule].corr(comp.AIOE))
        assert np.isclose(summary.loc[rule, 'spearman'], comp[rule].corr(comp.AIOE, method='spearman'))
