from typing import Union
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from pandas.tseries.holiday import USFederalHolidayCalendar
import os.path
import json

      

class Data_Manager:
    """
    DataManager handles local storage and retrieval of financial time series data for a specific ticker and interval.
    It checks for existing local data, updates or creates files as needed, and downloads new data if required.
    Each instance manages its own state (ticker, interval, file path), making it safe for concurrent or multi-ticker use.
    """

    def __init__(self, ticker: str, interval: str = '1d', path: str = r'./data_archive/'):
        """
        Initialize a DataManager object for a specific ticker and interval.

        Args:
            ticker (str): The ticker symbol to manage.
            interval (str, optional): The data interval (e.g., '1d'). Defaults to '1d'.
            path (str, optional): The directory where local data is stored. Defaults to './data_archive/'.
        """
        self.ticker = ticker
        self.interval = interval
        self.path = path
        self.file_path = os.path.join(path, rf"{ticker.lower()}_{interval.lower()}")
        print(f"Initialized Data_Manager with:")
        print(f"ticker: {ticker}")
        print(f"interval: {interval}")
        print(f"path: {path}")
        print(f"constructed file_path: {self.file_path}")

    def check_local_data(self, start_date: Union[dt, str] = None, end_date: Union[dt, str] = None) -> Union[pd.DataFrame, None]:
        """
        Check if local data exists for the ticker and interval, and if it covers the requested date range.

        Args:
            start_date (Union[datetime, str], optional): The start date for the data range.
            end_date (Union[datetime, str], optional): The end date for the data range.

        Returns:
            pd.DataFrame or None: The DataFrame containing the requested data if available and covering the range, otherwise None.
        """
        print(f"Attempting to read file at: {self.file_path}")
        print(f"File exists: {os.path.isfile(self.file_path)}")
        try:
            df = pd.read_parquet(self.file_path)
            # Ensure the index is a DatetimeIndex
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            print(f"Data range in file: {df.index.min()} to {df.index.max()}")
            
            # If date range is specified, check coverage
            if start_date is not None and end_date is not None:
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date)
                print(f"Requested date range: {start_date} to {end_date}")
                if df.index.min() <= start_date and df.index.max() >= end_date:
                    print("Date range is covered by local data")
                    # Return only the requested date range
                    return df.loc[start_date:end_date]
                else:
                    print("Date range is NOT covered by local data")
                    # Data does not cover the range
                    return None
            return df
        except Exception as e:
            print(f"Error reading local data: {e}")
            return None
    
        # File does not exist
        return None

    def update_local_data(self, df: pd.DataFrame):
        """
        Update the local data file by appending new data and removing duplicates.

        Args:
            df (pd.DataFrame): The DataFrame containing new data to append.
        """
        if os.path.isfile(self.file_path):
            base_df = pd.read_parquet(self.file_path)
            df = pd.concat([base_df, df])
        # Remove duplicate indices, keep the latest
        df = df[~df.index.duplicated(keep='last')]
        df = df.sort_index()
        df.to_parquet(self.file_path, index=True, engine='pyarrow')

    def create_local_data(self, df: pd.DataFrame):
        """
        Create a new local data file from the provided DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame containing the data to be saved.
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        df.to_parquet(self.file_path, index=True, engine='pyarrow')

    def download_data(
            self, 
            start_date: Union[dt, str] = None, 
            end_date: Union[dt, str] = None
            ) -> pd.DataFrame:
        """
        Download historical data for the ticker from Yahoo Finance.

        Args:
            start_date (Union[datetime, str], optional): The start date for the data range.
            end_date (Union[datetime, str], optional): The end date for the data range.

        Returns:
            pd.DataFrame: A DataFrame containing the downloaded data, indexed by date.
        """
        df = yf.download(
            tickers=self.ticker,
            start=start_date,
            end=end_date,
            interval=self.interval
        )
        df.columns = [col[0] for col in df.columns]
        return df

    def get_data(
            self,
            start_date: Union[dt, str] = None, 
            end_date: Union[dt, str] = None, 
            period: str = '1y'
        ) -> pd.DataFrame:
        """
        Def:
            Retrieve historical data for the ticker, checking local storage first and downloading if necessary.

        Args:
            start_date (Union[datetime, str], optional): The start date for the data range.
            end_date (Union[datetime, str], optional): The end date for the data range.
            period (str, optional): The period string (e.g. '1d','5d','1mo','3mo','6mo','1y','2y','5y','10y','ytd'). This is used to determine the date range if start_date and/or end_date are not provided.

        Returns:
            pd.DataFrame: The requested data, either from local storage or downloaded from Yahoo Finance.
        """
        # Try to get data from local storage
        start_date, end_date = date_management(start_date, end_date, period)
        local_data = self.check_local_data(start_date, end_date)
        if local_data is not None:
            return local_data
        else:
            # Download missing data
            new_data = self.download_data(start_date, end_date)
            # If file exists, update; else, create new
            if os.path.isfile(self.file_path):
                self.update_local_data(new_data)
            else:
                self.create_local_data(new_data)
            return new_data
    
def date_management(
        start_date: Union[dt, str, None] = None, 
        end_date: Union[dt, str, None] = None, 
        period: str = "1y"
        ) -> tuple:
    """
    Determines the start and end dates based on the provided start_date, end_date, and/or period.

    Supports periods: '1d','5d','1mo','3mo','6mo','1y','2y','5y','10y','ytd'.

    If both start_date and end_date are provided, returns them as datetimes.
    If only start_date and period are provided, calculates end_date.
    If only end_date and period are provided, calculates start_date.
    If only period is provided, calculates start_date and end_date based on today.

    Args:
        start_date (Union[datetime, str, None]): The start date or None.
        end_date (Union[datetime, str, None]): The end date or None.
        period (str): The period string (e.g., '1y', '6mo', '1d', 'ytd').

    Returns:
        tuple: (start_date, end_date) as datetime objects.
    """
    today = dt.today()
    # Parse dates if they are strings
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date, dayfirst=True)
        print(f"Parsed start_date: {start_date}")
    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date, dayfirst=True)
        print(f"Parsed end_date: {end_date}")

    # Handle period parsing
    period = period.lower()
    if period == '1d':
        delta = relativedelta(days=1)
    elif period == '5d':
        delta = relativedelta(days=5)
    elif period == '1mo':
        delta = relativedelta(months=1)
    elif period == '3mo':
        delta = relativedelta(months=3)
    elif period == '6mo':
        delta = relativedelta(months=6)
    elif period == '1y':
        delta = relativedelta(years=1)
    elif period == '2y':
        delta = relativedelta(years=2)
    elif period == '5y':
        delta = relativedelta(years=5)
    elif period == '10y':
        delta = relativedelta(years=10)
    elif period == 'ytd':
        # Special handling for year-to-date
        start_of_year = dt(today.year, 1, 1)
        if start_date and not end_date:
            end_date = start_date.replace(month=12, day=31)
            return (start_date, end_date)
        elif end_date and not start_date:
            start_date = dt(end_date.year, 1, 1)
            return (start_date, end_date)
        else:
            return (start_of_year, today)
    else:
        raise ValueError("Invalid period format. Use one of: '1d','5d','1mo','3mo','6mo','1y','2y','5y','10y','ytd'.")

    # Logic for date calculation
    if start_date and end_date:
        return (start_date, end_date)
    elif start_date and not end_date:
        end_date = start_date + delta
        return (start_date, end_date)
    elif end_date and not start_date:
        start_date = end_date - delta
        return (start_date, end_date)
    else:
        # Neither provided, use period ending today
        end_date = today
        start_date = end_date - delta
        return (start_date, end_date)

def _download_from_yahoo(symbols,start_date, end_date):
    """
    Fallback: télécharge les données depuis Yahoo Finance
    """
    print("[NET] Téléchargement depuis Yahoo Finance...")
    
    all_data = {}
    
    for symbol in symbols:
        try:
            data = _download_single_symbol_yahoo(symbol, start_date, end_date)
            if data is not None and len(data) >= 10:
                all_data[symbol] = data
                print(f"[OK] {symbol}: {len(data)} lignes téléchargées")
            else:
                print(f"[ERREUR] {symbol}: Échec du téléchargement")
        except Exception as e:
            print(f"[ERREUR] {symbol}: Erreur Yahoo - {e}")
    
    if not all_data:
        raise ValueError("[ERREUR] Impossible de télécharger les données depuis Yahoo Finance")
    
    return _process_loaded_data(all_data, symbols)

#---------------------------------------------------------
# UPDATED
#---------------------------------------------------------
def _download_data(symbols, start_date, end_date):
    """
    Charge les données depuis les fichiers CSV compressés locaux
    ou télécharge depuis Yahoo Finance si les fichiers locaux ne sont pas disponibles
    """
    print(f"[INFO] Chargement des données pour {symbols}...")
    print(f"   Période demandée: {start_date} à {end_date}")
    
    all_data = {}
    
    # 1. CHEMINS FLEXIBLES - essayer différents emplacements
    base_dir = os.getcwd()
    possible_data_dirs = [
        os.path.join(base_dir, "data", "compressed"),      # Recommended structure
        os.path.join(base_dir, "data"),                    # Simple data folder
        os.path.join(os.path.dirname(__file__), "data", "compressed"), # Relative to script
        os.path.join(os.path.dirname(__file__), "data"),
    ]
    
    # Chercher le bon dossier de données
    data_dir = None
    for possible_dir in possible_data_dirs:
        if os.path.exists(possible_dir):
            # Vérifier qu'il contient des fichiers CSV
            csv_files = [f for f in os.listdir(possible_dir) if f.endswith('.csv.gz')]
            if csv_files:
                data_dir = possible_dir
                print(f"[OK] Dossier de données trouvé: {data_dir}")
                print(f"   {len(csv_files)} fichiers CSV disponibles")
                break
    
    if not data_dir:
        print("[ERREUR] Aucun dossier de données locales trouvé")
        print("[RETRY] Tentative de téléchargement depuis Yahoo Finance...")
        return _download_from_yahoo(symbols,start_date, end_date)
    
    # 2. CHARGER LE LOG SI DISPONIBLE
    log_file_paths = [
        "data/download_log.json",
        "./data/download_log.json",
        os.path.join(data_dir, "download_log.json"),
        os.path.join(os.path.dirname(data_dir), "download_log.json")
    ]
    
    download_info = {}
    for log_path in log_file_paths:
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                    download_info = log_data.get('symbols', {})
                    print(f"[INFO] Log trouvé: {log_path} - {len(download_info)} symboles")
                    break
            except Exception as e:
                print(f"[WARN] Erreur lecture log {log_path}: {e}")
    
    # 3. TRAITEMENT DES SYMBOLES
    missing_symbols = []
    insufficient_data_symbols = []
    
    for symbol in symbols:
        # Nom de fichier sécurisé
        safe_symbol = symbol.replace("=", "_").replace(".", "_").replace("-", "_")
        filename = os.path.join(data_dir, f"{safe_symbol}.csv.gz")
        
        print(f"[DEBUG] Recherche de {symbol} -> {safe_symbol}.csv.gz")
        print(f"   Chemin: {filename}")
        
        if not os.path.exists(filename):
            print(f"[ERREUR] Fichier manquant: {filename}")
            # Essayer des variantes du nom
            alternative_names = [
                f"{symbol}.csv.gz",  # Nom original
                f"{symbol.replace('.', '_')}.csv.gz",  # Juste les points
                f"{symbol.replace('=', '_')}.csv.gz",  # Juste les égals
            ]
            
            found_alternative = False
            for alt_name in alternative_names:
                alt_path = os.path.join(data_dir, alt_name)
                if os.path.exists(alt_path):
                    print(f"[OK] Trouvé alternative: {alt_name}")
                    filename = alt_path
                    found_alternative = True
                    break
            
            if not found_alternative:
                missing_symbols.append(symbol)
                continue
        
        try:
            print(f"[DATA] Chargement de {symbol} depuis {filename}...")
            
            # Vérifier la taille du fichier
            file_size = os.path.getsize(filename)
            print(f"   Taille fichier: {file_size:,} bytes")
            
            if file_size == 0:
                print(f"   [ERREUR] Fichier vide!")
                missing_symbols.append(symbol)
                continue
            
            # Charger les données CSV compressées
            data = pd.read_csv(
                filename, 
                index_col=0, 
                parse_dates=True, 
                compression='gzip'
            )
            
            print(f"   [DATA] {len(data)} lignes chargées")
            print(f"   [DATE] Période: {data.index[0]} à {data.index[-1]}")
            print(f"   [DATA] Colonnes: {list(data.columns)}")
            
            # Afficher les informations du log si disponibles
            if symbol in download_info:
                info = download_info[symbol]
                print(f"   [INFO] Info log: {info.get('date_range', 'N/A')}")
            
            # Filtrer par les dates demandées
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            
            original_length = len(data)
            data = data[(data.index >= start_date) & (data.index <= end_date)]
            
            print(f"   [FILTER] Après filtrage ({start_date} à {end_date}): {len(data)} lignes")
            
            # Vérification de la quantité de données
            if len(data) < 10:
                print(f"   [ERREUR] Données insuffisantes pour {symbol}")
                print(f"       Seulement {len(data)} lignes, minimum requis: 10")
                insufficient_data_symbols.append(symbol)
                continue
            
            # Vérifier et nettoyer les données
            missing_values = data.isnull().sum().sum()
            if missing_values > 0:
                print(f"   [FIX] Nettoyage: {missing_values} valeurs manquantes")
                data = data.dropna()

                
                if len(data) < 10:
                    print(f"   [ERREUR] Données insuffisantes après nettoyage")
                    insufficient_data_symbols.append(symbol)
                    continue
                    
            # Normaliser les timestamps pour tous les types d'actifs
            if data.index.tz is not None:
                data.index = data.index.tz_convert('UTC').tz_localize(None).normalize()
            else:
                data.index = data.index.normalize()
            print(f"   [TIME] Timestamps normalisés pour {symbol}")
            
            # Vérifier les colonnes nécessaires
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in required_columns if col not in data.columns]
            
            if missing_cols:
                print(f"   [ERREUR] Colonnes manquantes: {missing_cols}")
                # Essayer de mapper les colonnes
                column_mapping = {
                    'open': 'Open', 'high': 'High', 'low': 'Low', 
                    'close': 'Close', 'volume': 'Volume',
                    'price': 'Close'  # Au cas où il n'y aurait qu'une colonne Price
                }
                
                data_renamed = data.copy()
                for old_col, new_col in column_mapping.items():
                    if old_col in data.columns and new_col in missing_cols:
                        data_renamed = data_renamed.rename(columns={old_col: new_col})
                        print(f"   [RETRY] Mappé {old_col} -> {new_col}")
                
                # Vérifier à nouveau
                still_missing = [col for col in required_columns if col not in data_renamed.columns]
                if still_missing:
                    raise ValueError(f"Colonnes toujours manquantes: {still_missing}")
                
                data = data_renamed
            
            # Vérifier la cohérence des données OHLC
            invalid_data = (
                (data['High'] < data['Low']) |
                (data['High'] < data['Open']) |
                (data['High'] < data['Close']) |
                (data['Low'] > data['Open']) |
                (data['Low'] > data['Close']) |
                (data['Close'] <= 0) |
                (data['Volume'] < 0)
            )
            
            if invalid_data.any():
                print(f"   [WARN] {invalid_data.sum()} lignes incohérentes détectées")
                data = data[~invalid_data]
                
                if len(data) < 10:
                    print(f"   [ERREUR] Données insuffisantes après validation")
                    insufficient_data_symbols.append(symbol)
                    continue
            
            all_data[symbol] = data
            
            # Statistiques finales
            price_range = f"{data['Close'].iloc[0]:.2f} -> {data['Close'].iloc[-1]:.2f}"
            print(f"   [PRICE] Prix: {price_range}")
            print(f"   [OK] Chargement réussi!")
            
        except Exception as e:
            print(f"   [ERREUR] Erreur chargement {symbol}: {e}")
            print(f"   [INFO] Type d'erreur: {type(e).__name__}")
            # Essayer le téléchargement Yahoo pour ce symbole
            try:
                print(f"   [RETRY] Tentative Yahoo Finance pour {symbol}...")
                yahoo_data = _download_single_symbol_yahoo(symbols,start_date, end_date)
                if yahoo_data is not None and len(yahoo_data) >= 10:
                    all_data[symbol] = yahoo_data
                    print(f"   [OK] Téléchargé depuis Yahoo!")
                else:
                    missing_symbols.append(symbol)
            except:
                missing_symbols.append(symbol)
    
    # 4. GESTION DES ERREURS
    if missing_symbols:
        print(f"\n[ERREUR] Symboles manquants: {missing_symbols}")
        if len(missing_symbols) == len(symbols):
            # Tous les symboles manquent, essayer Yahoo Finance
            print("[RETRY] Tentative de téléchargement complet depuis Yahoo Finance...")
            return _download_from_yahoo(symbols,start_date, end_date)
        elif len(all_data) == 0:
            raise FileNotFoundError(
                f"[ERREUR] Aucune donnée trouvée pour les symboles {symbols}\n"
                f"Dossiers vérifiés: {possible_data_dirs[:3]}\n"
                f"Assurez-vous que les fichiers CSV sont présents."
            )
    
    if insufficient_data_symbols:
        print(f"\n[WARN] Données insuffisantes: {insufficient_data_symbols}")
        if len(all_data) == 0:
            raise ValueError(
                f"[ERREUR] Données insuffisantes pour la période {start_date} à {end_date}\n"
                f"Symboles avec données insuffisantes: {insufficient_data_symbols}"
            )
    
    print(f"\n[OK] Données chargées pour {len(all_data)} symboles sur {len(symbols)} demandés")
    
    # Traitement final pour créer la structure MultiIndex
    return _process_loaded_data(all_data, symbols)


#-----------------------------------------------------------------
# UPDATED
# ----------------------------------------------------------------

def _download_single_symbol_yahoo(symbol, start_date, end_date):
    """
    Télécharge un seul symbole depuis Yahoo Finance
    """
    try:
        import yfinance as yf
        
        # Méthode 1 : yf.Ticker.history (souvent plus fiable pour les ajustements)
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(
                start=start_date,
                end=end_date,
                auto_adjust=True,
                back_adjust=True
            )
        except Exception as e:
            print(f"⚠️ Erreur yf.Ticker pour {symbol}: {e}")
            data = pd.DataFrame()
        
        # Méthode 2 : yf.download (fallback)
        if data.empty:
            print(f"⚠️ Données vides avec Ticker.history pour {symbol}, tentative avec yf.download...")
            data = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=True
            )
            
            # yf.download retourne souvent un MultiIndex pour les colonnes si un seul ticker
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
        
        if data.empty:
            print(f"[ERREUR] Échec total du téléchargement pour {symbol}")
            return None
        
        # NORMALISER LES TIMESTAMPS - CONVERTIR EN UTC ET RETIRER LE FUSEAU
        if data.index.tz is not None:
            data.index = data.index.tz_convert('UTC').tz_localize(None).normalize()
        else:
            data.index = pd.to_datetime(data.index).normalize()
            
        print(f"   [TIME] Timestamps normalisés (UTC, sans TZ) pour {symbol}")
        
        # Renommer les colonnes pour correspondre au format attendu
        # yf.download peut retourner 'Adj Close' au lieu de 'Close' si auto_adjust=False
        data = data.rename(columns={
            'Open': 'Open',
            'High': 'High', 
            'Low': 'Low',
            'Close': 'Close',
            'Volume': 'Volume'
        })
        
        return data
            
    except Exception as e:
        print(f"Erreur téléchargement Yahoo {symbol}: {e}")
        return None

#---------------------------------------------------------
# UPDATED
#---------------------------------------------------------
def _process_loaded_data(all_data, symbols):
    """
    Traite les données chargées pour créer la structure MultiIndex attendue
    Version avec gestion flexible des dates communes
    """
    print(f"[FIX] Traitement des données réelles...")
    
    if not all_data:
        raise ValueError("Aucune donnée disponible pour le traitement")
    
    # Afficher les plages de dates de chaque symbole pour diagnostiquer
    print("dates par symbole:")
    for symbol, data in all_data.items():
        print(f"   {symbol}: {data.index[0].strftime('%Y-%m-%d')} à {data.index[-1].strftime('%Y-%m-%d')} ({len(data)} jours)")
    
    # Stratégie 1: Essayer les dates communes strictes
    common_dates = None
    for symbol, data in all_data.items():
        if common_dates is None:
            common_dates = set(data.index)
        else:
            common_dates &= set(data.index)
    
    print(f"[DATA] Dates communes strictes: {len(common_dates) if common_dates else 0}")

    print(f"[DATA] Dates communes strictes: {len(common_dates) if common_dates else 0}")

    # AJOUTER CES LIGNES DE DEBUG :
    print("[DEBUG] - Détail des dates par symbole:")
    for symbol, data in all_data.items():
        sample_dates = list(data.index[:5])  # 5 premières dates
        print(f"   {symbol}: {len(data)} dates, échantillon: {sample_dates}")
        
    if common_dates:
        print(f"   Dates communes échantillon: {sorted(list(common_dates))[:5]}")
    else:
        print("   AUCUNE date commune trouvée!")
        # Vérifier pourquoi
        if len(all_data) >= 2:
            symbols = list(all_data.keys())
            dates1 = set(all_data[symbols[0]].index)
            dates2 = set(all_data[symbols[1]].index)
            print(f"   {symbols[0]} a {len(dates1)} dates")
            print(f"   {symbols[1]} a {len(dates2)} dates")
            intersection = dates1 & dates2
            print(f"   Intersection: {len(intersection)} dates")
            if len(intersection) > 0:
                print(f"   Échantillon intersection: {sorted(list(intersection))[:3]}")
    
    # Stratégie 2: Si pas assez de dates communes, utiliser l'intersection la plus large possible
    if not common_dates or len(common_dates) < 10:
        print("[WARN] Pas assez de dates communes strictes, recherche de la meilleure intersection...")
        
        # Trouver la période d'intersection maximale
        all_start_dates = [data.index[0] for data in all_data.values()]
        all_end_dates = [data.index[-1] for data in all_data.values()]
        
        latest_start = max(all_start_dates)
        earliest_end = min(all_end_dates)
        
        print(f"   Période d'intersection: {latest_start.strftime('%Y-%m-%d')} à {earliest_end.strftime('%Y-%m-%d')}")
        
        if latest_start <= earliest_end:
            # Filtrer chaque dataset sur cette période et trouver les dates communes
            filtered_data = {}
            for symbol, data in all_data.items():
                filtered = data[(data.index >= latest_start) & (data.index <= earliest_end)]
                if len(filtered) > 0:
                    filtered_data[symbol] = filtered
                    print(f"   {symbol} dans la période: {len(filtered)} jours")
            
            if filtered_data:
                # Recalculer les dates communes sur les données filtrées
                common_dates = None
                for symbol, data in filtered_data.items():
                    if common_dates is None:
                        common_dates = set(data.index)
                    else:
                        common_dates &= set(data.index)
                
                all_data = filtered_data
                print(f"[DATA] Nouvelles dates communes: {len(common_dates)}")
    
    # Stratégie 3: Si toujours insuffisant, prendre le symbole avec le plus de données comme référence
    if not common_dates or len(common_dates) < 10:
        print("[WARN] Toujours insuffisant, utilisation du symbole de référence...")
        
        # Trouver le symbole avec le plus de données dans la période
        reference_symbol = max(all_data.keys(), key=lambda s: len(all_data[s]))
        reference_dates = set(all_data[reference_symbol].index)
        
        print(f"   Symbole de référence: {reference_symbol} ({len(reference_dates)} dates)")
        
        # Pour chaque autre symbole, garder seulement les dates qui existent dans les données
        final_data = {reference_symbol: all_data[reference_symbol]}
        available_dates = reference_dates.copy()
        
        for symbol, data in all_data.items():
            if symbol == reference_symbol:
                continue
                
            # Intersection des dates disponibles avec ce symbole
            symbol_dates = set(data.index)
            available_dates &= symbol_dates
            
            if len(available_dates) >= 10:
                final_data[symbol] = data
                print(f"   {symbol} ajouté: {len(available_dates)} dates communes")
            else:
                print(f"   {symbol} ignoré: seulement {len(available_dates)} dates communes")
                # Retirer ce symbole mais garder les autres
                available_dates = reference_dates.copy()
                for kept_symbol in final_data.keys():
                    if kept_symbol != reference_symbol:
                        available_dates &= set(all_data[kept_symbol].index)
        
        all_data = final_data
        common_dates = available_dates
        
        print(f"[DATA] Dates finales avec symbole de référence: {len(common_dates)}")
    
    # Vérification finale
    if not common_dates or len(common_dates) < 5:  # Minimum absolu réduit à 5
        print("[ERREUR] Échec de toutes les stratégies, dernière tentative avec un seul symbole...")
        
        # Prendre seulement le premier symbole avec suffisamment de données
        for symbol, data in all_data.items():
            if len(data) >= 10:
                print(f"   Utilisation du symbole unique: {symbol} ({len(data)} jours)")
                all_data = {symbol: data}
                common_dates = set(data.index)
                break
        else:
            raise ValueError(
                "[ERREUR] Impossible de traiter les données.\n"
                "Suggestions:\n"
                "- Vérifiez que les symboles existent\n" 
                "- Utilisez une période plus récente\n"
                "- Réduisez le nombre de symboles"
            )
    
    common_dates = sorted(common_dates)
    print(f"[OK] Traitement final: {len(common_dates)} dates communes")
    print(f"   Période finale: {min(common_dates).strftime('%Y-%m-%d')} à {max(common_dates).strftime('%Y-%m-%d')}")
    print(f"   Symboles retenus: {list(all_data.keys())}")
    
    # Créer la structure MultiIndex (symbol, indicator)
    combined_data_frames = []
    
    for symbol, data in all_data.items():
        print(f"   [FIX] Traitement final de {symbol}...")
        
        # Filtrer pour les dates communes
        data_filtered = data.loc[data.index.isin(common_dates)].copy()
        
        if data_filtered.empty:
            print(f"     [WARN] Aucune donnée après filtrage pour {symbol}")
            continue
                
        print(f"     [DATA] {len(data_filtered)} lignes finales")
        
        # Créer le MultiIndex (symbol, indicator)
        new_columns = pd.MultiIndex.from_tuples(
            [(symbol, col) for col in data_filtered.columns],
            names=['symbol', 'indicator']
        )
        data_filtered.columns = new_columns
        
        combined_data_frames.append(data_filtered)
    
    if not combined_data_frames:
        raise ValueError("[ERREUR] Aucune donnée utilisable après traitement")
    
    # Concaténer tous les DataFrames
    combined_data = pd.concat(combined_data_frames, axis=1)
    
    print(f"[OK] Structure finale: {combined_data.shape}")
    
    return combined_data