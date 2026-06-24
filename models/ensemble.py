"""
Stacking ensemble: XGBoost + LightGBM + RandomForest → LogisticRegression meta-learner.
"""

import logging
import os
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    HAS_LGB = False

logger = logging.getLogger(__name__)
MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'saved_models')


class EnsembleModel:
    """
    Two-level stacking ensemble.
    Level 0: RandomForest + XGBoost + LightGBM (if available).
    Level 1: LogisticRegression meta-learner on out-of-fold predictions.
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.meta = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
        self.is_trained = False
        self.feature_names: list = []

        self.base_models = [('rf', RandomForestClassifier(
            n_estimators=200, max_depth=8, min_samples_leaf=5,
            class_weight='balanced', random_state=42, n_jobs=-1
        ))]
        if HAS_XGB:
            self.base_models.append(('xgb', xgb.XGBClassifier(
                n_estimators=200, max_depth=5, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8,
                use_label_encoder=False, eval_metric='logloss',
                random_state=42, n_jobs=-1
            )))
        if HAS_LGB:
            self.base_models.append(('lgb', lgb.LGBMClassifier(
                n_estimators=200, max_depth=5, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8,
                class_weight='balanced', random_state=42, n_jobs=-1, verbose=-1
            )))

    def train(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """Train on time-series split out-of-fold, then retrain on full data."""
        if len(X) < 100:
            logger.warning(f"Insufficient data for training: {len(X)} rows")
            return {}

        self.feature_names = list(X.columns)
        Xa, ya = X.values, y.values

        # Generate OOF meta-features
        tscv = TimeSeriesSplit(n_splits=5)
        meta_feats = np.zeros((len(Xa), len(self.base_models)))

        for _, (tr_idx, val_idx) in enumerate(tscv.split(Xa)):
            Xtr = self.scaler.fit_transform(Xa[tr_idx])
            Xval = self.scaler.transform(Xa[val_idx])
            for j, (_, m) in enumerate(self.base_models):
                m.fit(Xtr, ya[tr_idx])
                meta_feats[val_idx, j] = m.predict_proba(Xval)[:, 1]

        # Retrain base models on full data
        Xfull = self.scaler.fit_transform(Xa)
        for _, m in self.base_models:
            m.fit(Xfull, ya)

        self.meta.fit(meta_feats, ya)
        self.is_trained = True

        try:
            auc = roc_auc_score(ya, self.meta.predict_proba(meta_feats)[:, 1])
        except Exception:
            auc = 0.5

        # Top features from RF
        rf = next((m for n, m in self.base_models if n == 'rf'), None)
        top_features = {}
        if rf is not None:
            imp = rf.feature_importances_
            top_idx = np.argsort(imp)[::-1][:10]
            top_features = {self.feature_names[i]: float(imp[i]) for i in top_idx}

        logger.info(f"Ensemble trained | AUC={auc:.4f} | n={len(X)} | models={[n for n,_ in self.base_models]}")
        return {'auc': auc, 'n_samples': len(X), 'top_features': top_features}

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Return buy probability array, shape (n,)."""
        if not self.is_trained:
            return np.full(len(X), 0.5)
        Xa = X.reindex(columns=self.feature_names, fill_value=0).values
        Xs = self.scaler.transform(Xa)
        meta = np.column_stack([m.predict_proba(Xs)[:, 1] for _, m in self.base_models])
        return self.meta.predict_proba(meta)[:, 1]

    def predict_single(self, features: pd.Series) -> float:
        return float(self.predict_proba(features.to_frame().T)[0])

    def save(self, path: Optional[str] = None):
        os.makedirs(MODEL_DIR, exist_ok=True)
        path = path or os.path.join(MODEL_DIR, 'ensemble.joblib')
        joblib.dump({
            'base_models': self.base_models,
            'meta': self.meta,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained,
        }, path)
        logger.info(f"Model saved → {path}")

    def load(self, path: Optional[str] = None) -> bool:
        path = path or os.path.join(MODEL_DIR, 'ensemble.joblib')
        if not os.path.exists(path):
            return False
        try:
            d = joblib.load(path)
            self.base_models = d['base_models']
            self.meta = d['meta']
            self.scaler = d['scaler']
            self.feature_names = d['feature_names']
            self.is_trained = d['is_trained']
            logger.info(f"Model loaded ← {path}")
            return True
        except Exception as e:
            logger.warning(f"Model load failed: {e}")
            return False
