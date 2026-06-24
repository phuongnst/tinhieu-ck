"""
ML-based signal generation wrapping the EnsembleModel.
"""

import logging
import pandas as pd

from models.ensemble import EnsembleModel
from models.feature_engineering import create_features, create_labels

logger = logging.getLogger(__name__)


class MLSignalGenerator:
    """Wraps EnsembleModel for per-session signal generation."""

    def __init__(self):
        self.model = EnsembleModel()

    def train_on_all(self, ticker_data: dict, horizon: int = 5, gain_pct: float = 0.02) -> dict:
        """Train on combined historical data from all tickers."""
        all_X, all_y = [], []
        for ticker, df in ticker_data.items():
            try:
                X = create_features(df)
                y = create_labels(df, horizon=horizon, gain_pct=gain_pct)
                idx = X.index.intersection(y.dropna().index)
                if len(idx) >= 50:
                    all_X.append(X.loc[idx])
                    all_y.append(y.loc[idx])
            except Exception as e:
                logger.warning(f"Skip {ticker} for training: {e}")
        if not all_X:
            return {}
        X_all = pd.concat(all_X, ignore_index=True)
        y_all = pd.concat(all_y, ignore_index=True)
        return self.model.train(X_all, y_all)

    def predict(self, df: pd.DataFrame) -> float:
        """Return buy probability [0,1] for the latest bar."""
        try:
            feats = create_features(df)
            if feats.empty:
                return 0.5
            return float(self.model.predict_proba(feats.iloc[[-1]])[0])
        except Exception as e:
            logger.warning(f"ML predict failed: {e}")
            return 0.5

    def save(self):
        self.model.save()

    def load(self) -> bool:
        return self.model.load()
