#!/usr/bin/env python3
# core/scoring.py
# Logique de scoring centralisée et configurable

import logging
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone
from typing import Dict, Optional


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calcule le RSI (Relative Strength Index)."""
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ema_up / ema_down
    rsi = 100 - (100 / (1 + rs))
    return rsi


class ScoringEngine:
    """Moteur de scoring dynamique configurable via base de données."""
    
    def __init__(self, config: Dict):
        """
        Initialise le moteur de scoring avec la configuration.
        
        Args:
            config: Dictionnaire contenant:
                - formulas: formules personnalisées (Dict[str, str])
                - formula_weights: poids des formules personnalisées (Dict[str, float])
                - drawdown_cap: cap pour le drawdown
                - volatility_cap: cap pour la volatilité
        """
        self.config = config
        self.drawdown_cap = config.get("drawdown_cap", 0.25)
        self.volatility_cap = config.get("volatility_cap", 0.10)
        
        # Formules personnalisées définies par l'utilisateur
        self.formulas = config.get("formulas", {})
        self.formula_weights = config.get("formula_weights", {})
        
        # Log des formules chargées
        if self.formulas:
            logging.info(f"✅ Moteur de scoring initialisé avec {len(self.formulas)} formules personnalisées")
            for name, weight in self.formula_weights.items():
                if name in self.formulas:
                    logging.info(f"  - {name}: poids={weight}")
        else:
            logging.warning("⚠️ Aucune formule personnalisée définie. Le scoring retournera 0.")
    
    def evaluate_formula(self, formula_name: str, variables: Dict) -> float:
        """
        Évalue une formule personnalisée avec les variables données.
        
        Args:
            formula_name: Nom de la formule à évaluer
            variables: Dictionnaire des variables disponibles pour la formule
            
        Returns:
            Score entre 0.0 et 1.0, ou 0.0 en cas d'erreur
        """
        if formula_name not in self.formulas:
            return 0.0
        
        formula = self.formulas[formula_name]
        
        # Contexte d'évaluation sécurisé
        eval_context = {
            "np": np,
            "min": min,
            "max": max,
            "abs": abs,
            "exp": np.exp,
            "log": np.log,
            "sqrt": np.sqrt,
            "cap": self.drawdown_cap,
            "drawdown_cap": self.drawdown_cap,
            "volatility_cap": self.volatility_cap,
            **variables
        }
        
        try:
            result = eval(formula, {"__builtins__": {}}, eval_context)
            # S'assurer que le résultat est entre 0 et 1
            return float(np.clip(result, 0.0, 1.0))
        except Exception as e:
            logging.error(f"❌ Erreur dans formule '{formula_name}': {e}")
            logging.debug(f"   Formule: {formula}")
            logging.debug(f"   Variables: {variables}")
            return 0.0
    
    def compute_scores_for_ticker(self, ticker: str, period: str = "365d") -> Optional[Dict]:
        """
        Calcule les scores pour un ticker donné en utilisant les formules personnalisées.
        
        Args:
            ticker: Symbole du ticker
            period: Période historique à récupérer
            
        Returns:
            Dictionnaire avec les scores et métriques, ou None en cas d'erreur
        """
        # Récupérer le nom du produit
        product_name = ticker
        try:
            ticker_info = yf.Ticker(ticker)
            info = ticker_info.info
            product_name = info.get("longName") or info.get("shortName") or ticker
        except Exception as e:
            logging.warning(f"Impossible de récupérer le nom du produit pour {ticker}: {e}")
        
        try:
            df = yf.download(ticker, period=period, interval="1d", progress=False)
        except Exception as e:
            logging.exception(f"Erreur yfinance pour {ticker}: {e}")
            return None

        if df is None or df.empty:
            logging.warning(f"Pas de données pour {ticker}")
            return None

        # Flatten multi-index columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = df.dropna().copy()
        
        # Calcul des indicateurs techniques
        df["MA50"] = df["Close"].rolling(50, min_periods=1).mean()
        df["MA200"] = df["Close"].rolling(200, min_periods=1).mean()
        df["RSI14"] = compute_rsi(df["Close"], 14)
        df["High90"] = df["Close"].rolling(90, min_periods=1).max()
        df["Drawdown90"] = (df["High90"] - df["Close"]) / df["High90"]
        df["Vol20"] = df["Close"].pct_change().rolling(20, min_periods=1).std()
        df["Momentum30"] = df["Close"].pct_change(periods=30)

        latest = df.iloc[-1]

        # Extraction des métriques
        close = float(latest["Close"])
        ma50 = float(latest["MA50"]) if not np.isnan(latest["MA50"]) else np.nan
        ma200 = float(latest["MA200"]) if not np.isnan(latest["MA200"]) else np.nan
        rsi14 = float(latest["RSI14"]) if not np.isnan(latest["RSI14"]) else 50.0
        drawdown90 = float(latest["Drawdown90"]) if not np.isnan(latest["Drawdown90"]) else 0.0
        vol20 = float(latest["Vol20"]) if not np.isnan(latest["Vol20"]) else 0.0
        momentum30 = float(latest["Momentum30"]) if not np.isnan(latest["Momentum30"]) else 0.0

        # Variables disponibles pour toutes les formules
        common_vars = {
            "close": close,
            "ma50": ma50,
            "ma200": ma200,
            "rsi": rsi14,
            "rsi14": rsi14,
            "drawdown": drawdown90,
            "drawdown90": drawdown90,
            "vol20": vol20,
            "volatility": vol20,
            "momentum": momentum30,
            "momentum30": momentum30
        }

        # Calcul dynamique des scores pour chaque formule
        formula_scores = {}
        composite = 0.0
        total_weight = 0.0
        
        for formula_name in self.formulas.keys():
            weight = self.formula_weights.get(formula_name, 0.0)
            if weight > 0:
                score = self.evaluate_formula(formula_name, common_vars)
                formula_scores[formula_name] = score
                composite += weight * score
                total_weight += weight
        
        # Normaliser le score composite si les poids ne somment pas à 1
        if total_weight > 0 and total_weight != 1.0:
            composite = composite / total_weight
        
        score_100 = round(100.0 * composite, 1)

        return {
            "ticker": ticker,
            "product_name": product_name,
            "score": score_100,
            "close": close,
            "ma50": ma50,
            "ma200": ma200,
            "rsi14": round(rsi14, 2),
            "drawdown90_pct": round(drawdown90 * 100.0, 2),
            "vol20_pct": round(vol20 * 100.0, 2),
            "momentum30_pct": round(momentum30 * 100.0, 2),
            "components": {name: round(score, 3) for name, score in formula_scores.items()},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def compute_score_at_date(self, df: pd.DataFrame, date_idx: int) -> Optional[Dict]:
        """
        Calcule le score à une date donnée (pour le backtesting) en utilisant les formules personnalisées.
        
        Args:
            df: DataFrame avec les données historiques
            date_idx: Index de la date pour laquelle calculer le score
            
        Returns:
            Dictionnaire avec le score et les métriques, ou None si pas assez de données
        """
        historical_data = df.iloc[:date_idx+1].copy()
        
        if len(historical_data) < 200:
            return None
        
        # Calcul des indicateurs techniques
        historical_data["MA50"] = historical_data["Close"].rolling(50, min_periods=1).mean()
        historical_data["MA200"] = historical_data["Close"].rolling(200, min_periods=1).mean()
        historical_data["RSI14"] = compute_rsi(historical_data["Close"], 14)
        historical_data["High90"] = historical_data["Close"].rolling(90, min_periods=1).max()
        historical_data["Drawdown90"] = (historical_data["High90"] - historical_data["Close"]) / historical_data["High90"]
        historical_data["Vol20"] = historical_data["Close"].pct_change().rolling(20, min_periods=1).std()
        historical_data["Momentum30"] = historical_data["Close"].pct_change(periods=30)
        
        latest = historical_data.iloc[-1]
        
        # Extraction des métriques
        close = float(latest["Close"])
        ma50 = float(latest["MA50"]) if not np.isnan(latest["MA50"]) else np.nan
        ma200 = float(latest["MA200"]) if not np.isnan(latest["MA200"]) else np.nan
        rsi14 = float(latest["RSI14"]) if not np.isnan(latest["RSI14"]) else 50.0
        drawdown90 = float(latest["Drawdown90"]) if not np.isnan(latest["Drawdown90"]) else 0.0
        vol20 = float(latest["Vol20"]) if not np.isnan(latest["Vol20"]) else 0.0
        momentum30 = float(latest["Momentum30"]) if not np.isnan(latest["Momentum30"]) else 0.0
        
        # Variables disponibles pour toutes les formules
        common_vars = {
            "close": close,
            "ma50": ma50,
            "ma200": ma200,
            "rsi": rsi14,
            "rsi14": rsi14,
            "drawdown": drawdown90,
            "drawdown90": drawdown90,
            "vol20": vol20,
            "volatility": vol20,
            "momentum": momentum30,
            "momentum30": momentum30
        }

        # Calcul dynamique des scores pour chaque formule
        formula_scores = {}
        composite = 0.0
        total_weight = 0.0
        
        for formula_name in self.formulas.keys():
            weight = self.formula_weights.get(formula_name, 0.0)
            if weight > 0:
                score = self.evaluate_formula(formula_name, common_vars)
                formula_scores[formula_name] = score
                composite += weight * score
                total_weight += weight
        
        # Normaliser le score composite si les poids ne somment pas à 1
        if total_weight > 0 and total_weight != 1.0:
            composite = composite / total_weight
        
        # Construire le dictionnaire de résultat avec toutes les colonnes de scores
        result = {
            "date": historical_data.index[-1],
            "score": round(100.0 * composite, 1),
            "close": close,
            "rsi14": round(rsi14, 2),
            "ma50": ma50,
            "ma200": ma200,
            "drawdown90_pct": round(drawdown90 * 100.0, 2),
            "vol20_pct": round(vol20 * 100.0, 2),
            "momentum30_pct": round(momentum30 * 100.0, 2),
        }
        
        # Ajouter les scores individuels de chaque formule (score_xxx)
        for formula_name, score in formula_scores.items():
            result[f"score_{formula_name}"] = round(score * 100, 1)
        
        return result
