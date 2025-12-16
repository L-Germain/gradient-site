import pandas as pd
import numpy as np

from datetime import datetime
from dateutil.relativedelta import relativedelta
from data_collection import *


# AUSSI: Corrigez la méthode calculate_indicator pour la nouvelle structure
def calculate_indicator(data, symbol, indicator_type, params, date_idx=None):
    """
    Retourne la valeur ou la série d'un indicateur.
    
    Cette version est "intelligente" :
    1. Elle vérifie d'abord si l'indicateur existe déjà en tant que colonne
       dans les données de l'actif (pour les CSV importés).
    2. Si oui, elle utilise directement la valeur pré-calculée.
    3. Si non, elle calcule l'indicateur standard à la volée à partir de la colonne 'Close'.
    """
    try:
        # D'abord, on isole le DataFrame contenant toutes les colonnes pour l'actif concerné
        asset_data = data[symbol]
    except KeyError:
        raise ValueError(f"Aucune donnée trouvée pour le symbole '{symbol}' dans le DataFrame principal.")

    # --- NOUVELLE LOGIQUE : VÉRIFICATION DE L'INDICATEUR PRÉ-CALCULÉ ---
    # On regarde si le nom de l'indicateur demandé (ex: 'SMA_20') est une colonne de notre DataFrame
    if indicator_type in asset_data.columns:
        print(f"INFO: Utilisation de l'indicateur pré-calculé depuis la colonne : '{indicator_type}' pour {symbol}")
        indicator_series = asset_data[indicator_type]
        # Si un index de date est fourni, on retourne la valeur unique
        if date_idx is not None:
            return indicator_series.iloc[date_idx]
        # Sinon, on retourne la série complète
        return indicator_series
    # --- FIN DE LA NOUVELLE LOGIQUE ---

    # Si on arrive ici, l'indicateur n'était pas pré-calculé.
    # On continue avec le calcul standard à partir de la colonne 'Close'.
    
    if 'Close' not in asset_data.columns:
        raise ValueError(f"Colonne 'Close' manquante pour l'actif '{symbol}' pour calculer l'indicateur '{indicator_type}'")
    
    data_series = asset_data['Close']
    
    result = None

    if indicator_type == "PRICE":
        result = data_series
    
    elif indicator_type == "SMA":
        window = params[0] if params and len(params) > 0 else 20
        result = data_series.rolling(window=window).mean()
    
    elif indicator_type == "EMA":
        window = params[0] if params and len(params) > 0 else 20
        result = data_series.ewm(span=window, adjust=False).mean()
    
    elif indicator_type == "RSI":
        window = params[0] if params and len(params) > 0 else 14
        delta = data_series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        rs = avg_gain / avg_loss
        result = 100 - (100 / (1 + rs))
    
    elif indicator_type.startswith("BBAND"):
        window = params[0] if params and len(params) > 0 else 20
        deviation = params[1] if params and len(params) > 1 else 2
        sma = data_series.rolling(window=window).mean()
        std = data_series.rolling(window=window).std()
        
        if indicator_type == "BBAND_UPPER":
            result = sma + (std * deviation)
        elif indicator_type == "BBAND_LOWER":
            result = sma - (std * deviation)
        else:
            result = sma
    
    elif indicator_type == "MACD":
        fast_period = params[0] if params and len(params) > 0 else 12
        slow_period = params[1] if params and len(params) > 1 else 26
        signal_period = params[2] if params and len(params) > 2 else 9
        fast_ema = data_series.ewm(span=fast_period, adjust=False).mean()
        slow_ema = data_series.ewm(span=slow_period, adjust=False).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        result = macd_line - signal_line

    elif indicator_type == "DCA":
        period = params[0] if params and len(params) > 0 else 30
        result = pd.Series(0.0, index=data_series.index)
        result.iloc[0::period] = 1.0 # Signal d'achat tous les 'period' jours
    
    else:
        raise ValueError(f"Indicateur standard '{indicator_type}' non pris en charge ou non trouvé dans les colonnes du CSV.")
    
    if date_idx is not None:
        value = result.iloc[date_idx]
        return value if pd.notna(value) else np.nan
    
    return result
