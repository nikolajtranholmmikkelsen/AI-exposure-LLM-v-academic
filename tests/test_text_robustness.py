"""Check text matching tradeoffs and the resulting estimates."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('text_robustness', ROOT / 'scripts/06_text_robustness.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
OUT = ROOT / 'results/text_robustness'


def test_literal_matching_and_known_false_positive():
    rules = pd.read_csv(ROOT / 'data/rubric/physical_task_patterns.csv')
    assert ('apply', 'Apply') in module.match_rules('Apply makeup to face.', rules)
    assert ('apply', 'Apply') in module.match_rules('Apply theoretical expertise to computer research.', rules)
    assert module.match_rules('Pose for photographers.', rules)
    assert not module.match_rules('Review applications and compose reports.', rules)
    assert not module.match_rules('Review financial reports.', rules)


def test_audit_flags_and_unchanged_weights():
    tasks = pd.read_csv(OUT / 'task_overrides.csv')
    prior = pd.read_csv(ROOT / 'results/robustness/task_overrides.csv')
    pd.testing.assert_frame_equal(tasks[prior.columns], prior)
    assert len(tasks) == 18796
    rules = pd.read_csv(ROOT / 'data/rubric/physical_task_patterns.csv')
    assert tasks.text_flag.eq(tasks.Task.map(lambda text: bool(module.match_rules(text, rules)))).all()
    assert tasks.combined_flag.eq(tasks.text_flag | tasks.broad_flag).all()
    for variant in ['text', 'combined']:
        assert tasks.loc[tasks[variant + '_flag'], variant + '_exposure'].eq(0).all()
        assert np.allclose(tasks.loc[~tasks[variant + '_flag'], variant + '_exposure'],
                           tasks.loc[~tasks[variant + '_flag'], 'baseline_exposure'])


def test_aggregation_sample_and_correlations():
    tasks = pd.read_csv(OUT / 'task_overrides.csv')
    occ = pd.read_csv(OUT / 'occupation_exposure.csv').set_index('O*NET-SOC Code')
    comp = pd.read_csv(OUT / 'comparison_occupation.csv')
    prior = pd.read_csv(ROOT / 'results/hybrid/comparison_occupation.csv')
    pd.testing.assert_frame_equal(comp[['soc6', 'title', 'AIOE']], prior[['soc6', 'title', 'AIOE']])
    assert len(comp) == 683
    summary = pd.read_csv(OUT / 'summary.csv').set_index('variant')
    for variant in ['text', 'combined']:
        score = (tasks.weight * tasks[variant + '_exposure']).groupby(tasks['O*NET-SOC Code']).sum() / tasks.groupby('O*NET-SOC Code').weight.sum()
        assert np.allclose(occ[variant], score.round(4).reindex(occ.index))
        assert np.isclose(summary.loc[variant, 'spearman'], comp[variant].corr(comp.AIOE, method='spearman'))
        assert np.isclose(summary.loc[variant, 'pearson'], comp[variant].corr(comp.AIOE))
    assert (occ.combined <= occ.text).all() and (occ.text <= occ.original).all()
