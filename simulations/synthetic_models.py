# synthetic_models.py - Infrastructure des modèles génératifs pour TradingLab

import numpy as np
import pandas as pd
import yfinance as yf
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class BaseGenerativeModel(ABC):
    """
    Classe abstraite pour tous les modèles génératifs
    Interface standardisée pour TradingLab
    """
    
    def __init__(self, ticker='AAPL', start_date='2020-01-01', end_date='2025-01-01'):
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.is_fitted = False
        
    @abstractmethod
    def fit(self):
        """Estime les paramètres du modèle à partir des données historiques"""
        pass
    
    @abstractmethod
    def simulate(self, T=1, n_steps=252, n_simulations=1000):
        """Génère des données synthétiques"""
        pass
    
    @abstractmethod
    def to_dataframe(self):
        """Convertit les données simulées au format DataFrame compatible avec Backtester"""
        pass
    
    def get_model_info(self):
        """Retourne les informations du modèle"""
        return {
            'name': self.__class__.__name__,
            'ticker': self.ticker,
            'fitted': self.is_fitted,
            'parameters': self.get_parameters() if hasattr(self, 'get_parameters') else {}
        }

class MonteCarloGBM(BaseGenerativeModel):
    """
    Modèle Geometric Brownian Motion (GBM) - Le plus simple
    """
    
    def __init__(self, ticker='AAPL', start_date='2020-01-01', end_date='2025-01-01'):
        super().__init__(ticker, start_date, end_date)
        self.model_name = "Monte Carlo GBM"
        
    def fit(self):
        """Estime μ et σ à partir des données historiques"""
        print(f"📊 Calibration du modèle GBM pour {self.ticker}...")
        
        # Télécharger les données
        try:
            data = yf.download(self.ticker, start=self.start_date, end=self.end_date, progress=False)
            self.prices = data['Close'].dropna()
            
            if len(self.prices) < 30:
                raise ValueError(f"Données insuffisantes pour {self.ticker}")
                
            # Calculer les rendements logarithmiques
            log_returns = np.log(self.prices / self.prices.shift(1)).dropna()
            
            # Paramètres annualisés
            self.mu = float(log_returns.mean() * 252)  # Drift annuel
            self.sigma = float(log_returns.std() * np.sqrt(252))  # Volatilité annuelle
            self.S0 = float(self.prices.iloc[-1])  # Prix initial
            
            self.is_fitted = True
            
            # print(f"✅ Calibration terminée:")
            # print(f"   • Prix initial: ${self.S0:.2f}")
            # print(f"   • Drift annuel (μ): {self.mu*100:.2f}%")
            # print(f"   • Volatilité annuelle (σ): {self.sigma*100:.2f}%")
            
        except Exception as e:
            # print(f"❌ Erreur lors de la calibration: {e}")
            raise
    
    def simulate(self, T=1, n_steps=252, n_simulations=1000):
        """Génère des trajectoires GBM"""
        if not self.is_fitted:
            self.fit()
            
        # print(f"🎲 Simulation GBM: {n_simulations} trajectoires sur {T} an(s)")
        
        self.T = T
        self.n_steps = n_steps
        self.n_simulations = n_simulations
        self.dt = T / n_steps
        
        # Initialisation
        self.simulations = np.zeros((n_steps + 1, n_simulations))
        self.simulations[0] = self.S0
        
        # Génération vectorisée pour efficacité
        random_shocks = np.random.standard_normal((n_steps, n_simulations))
        
        for t in range(1, n_steps + 1):
            drift = (self.mu - 0.5 * self.sigma**2) * self.dt
            diffusion = self.sigma * np.sqrt(self.dt) * random_shocks[t-1]
            self.simulations[t] = self.simulations[t-1] * np.exp(drift + diffusion)
        
        # print("✅ Simulation GBM terminée!")
        return self
    
    def to_dataframe(self, simulation_index=0):
        """Convertit une simulation au format OHLCV compatible TradingLab"""
        if not hasattr(self, 'simulations'):
            raise ValueError("Aucune simulation disponible. Lancez d'abord simulate()")
        
        # Utiliser la première simulation par défaut ou une spécifique
        prices = self.simulations[:, simulation_index]
        
        # Créer les dates
        start_date = pd.to_datetime(self.end_date)
        dates = pd.date_range(start=start_date, periods=len(prices), freq='D')
        
        # Générer OHLCV réaliste à partir des prix
        df = pd.DataFrame(index=dates)
        
        # Prix de clôture = simulation
        df['Close'] = prices
        
        # Générer OHLV de manière cohérente
        daily_vol = self.sigma / np.sqrt(252)  # Volatilité journalière
        
        # Variation intra-day (plus petite que la variation inter-day)
        intraday_noise = np.random.normal(0, daily_vol * 0.3, len(prices))
        
        # Open = Close précédent avec petit gap
        df['Open'] = df['Close'].shift(1) * (1 + np.random.normal(0, daily_vol * 0.1, len(prices)))
        df['Open'].iloc[0] = prices[0]  # Premier Open = premier prix
        
        # High et Low basés sur la volatilité intra-day
        high_factor = 1 + np.abs(np.random.normal(0, daily_vol * 0.5, len(prices)))
        low_factor = 1 - np.abs(np.random.normal(0, daily_vol * 0.5, len(prices)))
        
        df['High'] = np.maximum(df['Open'], df['Close']) * high_factor
        df['Low'] = np.minimum(df['Open'], df['Close']) * low_factor
        
        # Volume corrélé à la volatilité (plus de volume = plus de volatilité)
        base_volume = 1000000  # Volume de base
        vol_factor = np.abs(np.diff(np.log(prices), prepend=np.log(prices[0])))
        volume_multiplier = 1 + vol_factor * 10  # Facteur d'amplification
        df['Volume'] = (base_volume * volume_multiplier).astype(int)
        
        # Nettoyer les valeurs aberrantes
        df = df.dropna()
        
        return df
    
    def get_parameters(self):
        """Retourne les paramètres du modèle"""
        if not self.is_fitted:
            return {}
        return {
            'mu': self.mu,
            'sigma': self.sigma,
            'S0': self.S0
        }

class HestonSynthetic(BaseGenerativeModel):
    """
    Modèle de Heston avec volatilité stochastique
    """
    
    def __init__(self, ticker='AAPL', start_date='2020-01-01', end_date='2025-01-01'):
        super().__init__(ticker, start_date, end_date)
        self.model_name = "Heston Stochastic Volatility"
    
    def fit(self):
        """Estime les paramètres de Heston"""
        # print(f"📊 Calibration du modèle Heston pour {self.ticker}...")
        
        try:
            # Télécharger les données
            data = yf.download(self.ticker, start=self.start_date, end=self.end_date, progress=False)
            self.prices = data['Close'].dropna()
            self.log_returns = np.log(self.prices / self.prices.shift(1)).dropna()
            
            # Paramètres de base
            self.mu = float(self.log_returns.mean() * 252)
            self.vol_annual = float(self.log_returns.std() * np.sqrt(252))
            self.v0 = self.vol_annual**2
            self.S0 = float(self.prices.iloc[-1])
            
            # Estimation des paramètres Heston
            self._estimate_heston_parameters()
            
            self.is_fitted = True
            # print("✅ Calibration Heston terminée!")
            
        except Exception as e:
            # print(f"❌ Erreur calibration Heston: {e}")
            raise
    
    def _estimate_heston_parameters(self):
        """Estimation simplifiée des paramètres Heston"""
        # Volatilité réalisée
        window_size = 21
        realized_vol = self.log_returns.rolling(window=window_size).std() * np.sqrt(252)
        realized_var = realized_vol**2
        
        # Estimation simple par régression
        var_series = realized_var.dropna()
        
        if len(var_series) >= 50:
            var_lagged = var_series.shift(1).dropna()
            common_idx = var_series.index.intersection(var_lagged.index)
            
            if len(common_idx) >= 20:
                try:
                    from scipy.stats import linregress
                    var_t = var_series.loc[common_idx].values
                    var_t_minus_1 = var_lagged.loc[common_idx].values
                    delta_var = var_t - var_t_minus_1
                    
                    # Nettoyer les données
                    valid_mask = ~(np.isnan(var_t_minus_1) | np.isnan(delta_var))
                    if np.sum(valid_mask) >= 10:
                        reg = linregress(var_t_minus_1[valid_mask], delta_var[valid_mask])
                        
                        dt = 1/252
                        beta = reg.slope
                        alpha = reg.intercept
                        
                        if beta < 0:  # Paramètres valides
                            self.kappa = max(-beta / dt, 0.1)
                            self.theta = max(-alpha / beta if beta != 0 else self.v0, 0.001)
                            
                            # Xi à partir des résidus
                            residuals = delta_var[valid_mask] - (alpha + beta * var_t_minus_1[valid_mask])
                            self.xi = max(np.sqrt(np.var(residuals) / dt), 0.01)
                        else:
                            self._set_default_heston_params()
                    else:
                        self._set_default_heston_params()
                except:
                    self._set_default_heston_params()
            else:
                self._set_default_heston_params()
        else:
            self._set_default_heston_params()
        
        # Corrélation prix-volatilité
        try:
            vol_changes = realized_vol.pct_change().dropna()
            common_idx2 = self.log_returns.index.intersection(vol_changes.index)
            
            if len(common_idx2) >= 30:
                ret_aligned = self.log_returns.loc[common_idx2].values
                vol_change_aligned = vol_changes.loc[common_idx2].values
                
                valid_mask = ~(np.isnan(ret_aligned) | np.isnan(vol_change_aligned))
                if np.sum(valid_mask) >= 20:
                    corr_matrix = np.corrcoef(ret_aligned[valid_mask], vol_change_aligned[valid_mask])
                    self.rho = float(np.clip(corr_matrix[0, 1], -0.95, 0.95))
                else:
                    self.rho = -0.7
            else:
                self.rho = -0.7
        except:
            self.rho = -0.7
        
        if np.isnan(self.rho):
            self.rho = -0.7
        
        # Vérification condition de Feller
        if 2 * self.kappa * self.theta <= self.xi**2:
            self.kappa = (self.xi**2) / (2 * self.theta) * 1.2
    
    def _set_default_heston_params(self):
        """Paramètres Heston par défaut"""
        self.kappa = 2.0
        self.theta = self.v0
        self.xi = 0.3
        self.rho = -0.7
    
    def simulate(self, T=1, n_steps=252, n_simulations=1000):
        """Simule le modèle de Heston"""
        if not self.is_fitted:
            self.fit()
        
        # print(f"🎲 Simulation Heston: {n_simulations} trajectoires sur {T} an(s)")
        
        self.T = T
        self.n_steps = n_steps
        self.n_simulations = n_simulations
        self.dt = T / n_steps
        
        # Initialisation
        self.S_paths = np.zeros((n_steps + 1, n_simulations))
        self.v_paths = np.zeros((n_steps + 1, n_simulations))
        
        self.S_paths[0, :] = self.S0
        self.v_paths[0, :] = self.v0
        
        # Simulation
        for t in range(1, n_steps + 1):
            # Browniens corrélés
            Z1 = np.random.standard_normal(n_simulations)
            Z2_indep = np.random.standard_normal(n_simulations)
            Z2 = self.rho * Z1 + np.sqrt(1 - self.rho**2) * Z2_indep
            
            # État précédent
            S_prev = self.S_paths[t-1, :]
            v_prev = np.maximum(self.v_paths[t-1, :], 1e-8)
            
            # Mise à jour variance (CIR)
            v_drift = self.kappa * (self.theta - v_prev) * self.dt
            v_diffusion = self.xi * np.sqrt(v_prev * self.dt) * Z2
            v_new = v_prev + v_drift + v_diffusion
            self.v_paths[t, :] = np.maximum(v_new, 1e-8)
            
            # Mise à jour prix
            drift = (self.mu - 0.5 * v_prev) * self.dt
            diffusion = np.sqrt(v_prev * self.dt) * Z1
            S_new = S_prev * np.exp(drift + diffusion)
            self.S_paths[t, :] = np.maximum(S_new, 0.01)
        
        # print("✅ Simulation Heston terminée!")
        return self
    
    def to_dataframe(self, simulation_index=0):
        """Convertit simulation Heston au format OHLCV"""
        if not hasattr(self, 'S_paths'):
            raise ValueError("Aucune simulation disponible. Lancez d'abord simulate()")
        
        prices = self.S_paths[:, simulation_index]
        volatilities = np.sqrt(self.v_paths[:, simulation_index])
        
        # Dates
        start_date = pd.to_datetime(self.end_date)
        dates = pd.date_range(start=start_date, periods=len(prices), freq='D')
        
        df = pd.DataFrame(index=dates)
        df['Close'] = prices
        
        # OHLV basé sur la volatilité stochastique
        daily_vols = volatilities / np.sqrt(252)
        
        # Open avec gaps
        df['Open'] = df['Close'].shift(1) * (1 + np.random.normal(0, daily_vols * 0.1))
        df['Open'].iloc[0] = prices[0]
        
        # High/Low basés sur la volatilité stochastique
        high_factor = 1 + np.abs(np.random.normal(0, daily_vols * 0.6))
        low_factor = 1 - np.abs(np.random.normal(0, daily_vols * 0.6))
        
        df['High'] = np.maximum(df['Open'], df['Close']) * high_factor
        df['Low'] = np.minimum(df['Open'], df['Close']) * low_factor
        
        # Volume corrélé à la volatilité
        base_volume = 1000000
        vol_factor = volatilities / np.mean(volatilities)
        df['Volume'] = (base_volume * vol_factor * (1 + np.random.uniform(0.5, 1.5, len(prices)))).astype(int)
        
        return df.dropna()
    
    def get_parameters(self):
        """Retourne les paramètres Heston"""
        if not self.is_fitted:
            return {}
        return {
            'mu': self.mu,
            'kappa': self.kappa,
            'theta': self.theta,
            'xi': self.xi,
            'rho': self.rho,
            'v0': self.v0,
            'S0': self.S0
        }

class BatesSynthetic(BaseGenerativeModel):
    """
    Modèle de Bates (Heston + Sauts)
    """
    
    def __init__(self, ticker='AAPL', start_date='2020-01-01', end_date='2025-01-01'):
        super().__init__(ticker, start_date, end_date)
        self.model_name = "Bates Jump-Diffusion"
    
    def fit(self):
        """Calibre le modèle de Bates"""
        # print(f"📊 Calibration du modèle Bates pour {self.ticker}...")
        
        try:
            # Données de base
            data = yf.download(self.ticker, start=self.start_date, end=self.end_date, progress=False)
            self.prices = data['Close'].dropna()
            self.log_returns = np.log(self.prices / self.prices.shift(1)).dropna()
            
            # Paramètres de base
            self.mu = float(self.log_returns.mean() * 252)
            self.vol_annual = float(self.log_returns.std() * np.sqrt(252))
            self.v0 = self.vol_annual**2
            self.S0 = float(self.prices.iloc[-1])
            
            # Détection des sauts
            self._detect_jumps()
            
            # Paramètres Heston (comme la classe précédente)
            self._estimate_heston_parameters()
            
            # Paramètres de saut
            self._estimate_jump_parameters()
            
            self.is_fitted = True
            # print("✅ Calibration Bates terminée!")
            
        except Exception as e:
            print(f"❌ Erreur calibration Bates: {e}")
            raise
    
    def _detect_jumps(self):
        """Détecte les sauts dans les données"""
        abs_returns = np.abs(self.log_returns)
        jump_threshold = 2.5
        return_std = abs_returns.std()
        self.jump_indicator = abs_returns > jump_threshold * return_std
        
        self.n_jumps = int(self.jump_indicator.sum())
        self.jump_frequency = float(self.n_jumps / len(self.log_returns))
    
    def _estimate_heston_parameters(self):
        """Estime Heston sur données filtrées (sans sauts)"""
        # Même logique que HestonSynthetic mais sur données filtrées
        normal_returns = self.log_returns[~self.jump_indicator]
        
        if len(normal_returns) >= 50:
            # Estimation simplifiée
            self.kappa = 2.0
            self.theta = self.v0
            self.xi = 0.3
            self.rho = -0.7
        else:
            self.kappa = 2.0
            self.theta = self.v0
            self.xi = 0.3
            self.rho = -0.7
    
    def _estimate_jump_parameters(self):
        """Estime les paramètres de saut"""
        # Fréquence des sauts (annualisée)
        self.lambda_j = max(self.n_jumps / len(self.log_returns) * 252, 0.1)
        
        # Paramètres des sauts
        jump_returns = self.log_returns[self.jump_indicator]
        
        if len(jump_returns) > 0:
            self.mu_j = float(jump_returns.mean())
            self.sigma_j = float(jump_returns.std())
        else:
            self.mu_j = 0.0
            self.sigma_j = self.vol_annual * 1.5
        
        # Ajustement du drift
        jump_compensation = self.lambda_j * (np.exp(self.mu_j + 0.5 * self.sigma_j**2) - 1)
        self.mu_adjusted = self.mu - jump_compensation
    
    def simulate(self, T=1, n_steps=252, n_simulations=1000):
        """Simule le modèle de Bates"""
        if not self.is_fitted:
            self.fit()
        
        # print(f"🎲 Simulation Bates: {n_simulations} trajectoires sur {T} an(s)")
        
        self.T = T
        self.n_steps = n_steps
        self.n_simulations = n_simulations
        self.dt = T / n_steps
        
        # Initialisation
        self.S_paths = np.zeros((n_steps + 1, n_simulations))
        self.v_paths = np.zeros((n_steps + 1, n_simulations))
        self.jump_paths = np.zeros((n_steps + 1, n_simulations))
        
        self.S_paths[0, :] = self.S0
        self.v_paths[0, :] = self.v0
        
        # Simulation
        for t in range(1, n_steps + 1):
            # Browniens corrélés
            Z1 = np.random.standard_normal(n_simulations)
            Z2_indep = np.random.standard_normal(n_simulations)
            Z2 = self.rho * Z1 + np.sqrt(1 - self.rho**2) * Z2_indep
            
            # État précédent
            S_prev = self.S_paths[t-1, :]
            v_prev = np.maximum(self.v_paths[t-1, :], 1e-8)
            
            # Mise à jour variance (CIR)
            v_drift = self.kappa * (self.theta - v_prev) * self.dt
            v_diffusion = self.xi * np.sqrt(v_prev * self.dt) * Z2
            v_new = v_prev + v_drift + v_diffusion
            self.v_paths[t, :] = np.maximum(v_new, 1e-8)
            
            # Génération des sauts
            n_jumps = np.random.poisson(self.lambda_j * self.dt, n_simulations)
            jump_sizes = np.zeros(n_simulations)
            
            for i in range(n_simulations):
                if n_jumps[i] > 0:
                    jumps = np.random.normal(self.mu_j, self.sigma_j, n_jumps[i])
                    jump_sizes[i] = np.sum(jumps)
            
            self.jump_paths[t, :] = jump_sizes
            
            # Mise à jour prix (avec sauts)
            drift = (self.mu_adjusted - 0.5 * v_prev) * self.dt
            diffusion = np.sqrt(v_prev * self.dt) * Z1
            log_return = drift + diffusion + jump_sizes
            
            self.S_paths[t, :] = S_prev * np.exp(log_return)
        
        # print("✅ Simulation Bates terminée!")
        return self
    
    def to_dataframe(self, simulation_index=0):
        """Convertit simulation Bates au format OHLCV"""
        if not hasattr(self, 'S_paths'):
            raise ValueError("Aucune simulation disponible. Lancez d'abord simulate()")
        
        prices = self.S_paths[:, simulation_index]
        volatilities = np.sqrt(self.v_paths[:, simulation_index])
        jumps = self.jump_paths[:, simulation_index]
        
        # Dates
        start_date = pd.to_datetime(self.end_date)
        dates = pd.date_range(start=start_date, periods=len(prices), freq='D')
        
        df = pd.DataFrame(index=dates)
        df['Close'] = prices
        
        # OHLV avec impact des sauts
        daily_vols = volatilities / np.sqrt(252)
        jump_impact = np.abs(jumps)  # Impact absolu des sauts
        
        # Open avec gaps plus importants lors des sauts
        gap_factor = daily_vols * 0.1 + jump_impact * 0.5
        df['Open'] = df['Close'].shift(1) * (1 + np.random.normal(0, gap_factor))
        df['Open'].iloc[0] = prices[0]
        
        # High/Low avec volatilité augmentée par les sauts
        intraday_vol = daily_vols * 0.6 + jump_impact * 0.3
        high_factor = 1 + np.abs(np.random.normal(0, intraday_vol))
        low_factor = 1 - np.abs(np.random.normal(0, intraday_vol))
        
        df['High'] = np.maximum(df['Open'], df['Close']) * high_factor
        df['Low'] = np.minimum(df['Open'], df['Close']) * low_factor
        
        # Volume augmenté lors des sauts
        base_volume = 1000000
        vol_factor = volatilities / np.mean(volatilities)
        jump_volume_factor = 1 + jump_impact * 5  # Les sauts augmentent le volume
        df['Volume'] = (base_volume * vol_factor * jump_volume_factor * 
                       (1 + np.random.uniform(0.5, 1.5, len(prices)))).astype(int)
        
        return df.dropna()
    
    def get_parameters(self):
        """Retourne les paramètres Bates"""
        if not self.is_fitted:
            return {}
        return {
            'mu': self.mu,
            'kappa': self.kappa,
            'theta': self.theta,
            'xi': self.xi,
            'rho': self.rho,
            'lambda_j': self.lambda_j,
            'mu_j': self.mu_j,
            'sigma_j': self.sigma_j,
            'v0': self.v0,
            'S0': self.S0
        }

class SABRSynthetic(BaseGenerativeModel):
    """
    Modèle SABR simplifié
    """
    
    def __init__(self, ticker='AAPL', start_date='2020-01-01', end_date='2025-01-01'):
        super().__init__(ticker, start_date, end_date)
        self.model_name = "SABR Model"
    
    def fit(self):
        """Calibre le modèle SABR"""
        # print(f"📊 Calibration du modèle SABR pour {self.ticker}...")
        
        try:
            # Données de base
            data = yf.download(self.ticker, start=self.start_date, end=self.end_date, progress=False)
            self.prices = data['Close'].dropna()
            self.log_returns = np.log(self.prices / self.prices.shift(1)).dropna()
            
            # Paramètres de base
            self.mu = float(self.log_returns.mean() * 252)
            self.vol_annual = float(self.log_returns.std() * np.sqrt(252))
            self.F0 = float(self.prices.iloc[-1])  # Forward (= spot)
            
            # Paramètres SABR simplifiés
            self.alpha0 = self.vol_annual
            self.beta = 0.5  # Élasticité
            self.rho = -0.7  # Corrélation
            self.nu = 0.3    # Vol of vol
            
            self.is_fitted = True
            # print("✅ Calibration SABR terminée!")
            
        except Exception as e:
            print(f"❌ Erreur calibration SABR: {e}")
            raise
    
    def simulate(self, T=1, n_steps=252, n_simulations=1000):
        """Simule le modèle SABR"""
        if not self.is_fitted:
            self.fit()
        
        # print(f"🎲 Simulation SABR: {n_simulations} trajectoires sur {T} an(s)")
        
        self.T = T
        self.n_steps = n_steps
        self.n_simulations = n_simulations
        dt = T / n_steps
        sqrt_dt = np.sqrt(dt)
        self.F_paths = np.zeros((n_steps + 1, n_simulations))
        self.alpha_paths = np.zeros((n_steps + 1, n_simulations))
        
        # Initialisation
        self.F_paths[0, :] = self.F0
        self.alpha_paths[0, :] = self.alpha0
        
        # Génération des nombres aléatoires corrélés
        Z1 = np.random.standard_normal((n_steps, n_simulations))
        Z2_indep = np.random.standard_normal((n_steps, n_simulations))
        Z2 = self.rho * Z1 + np.sqrt(1 - self.rho**2) * Z2_indep
        
        # Simulation pas à pas
        for t in range(n_steps):
            # Mise à jour d'alpha (log-normal)
            self.alpha_paths[t+1, :] = self.alpha_paths[t, :] * np.exp(
                -0.5 * self.nu**2 * dt + self.nu * sqrt_dt * Z2[t, :]
            )
            self.alpha_paths[t+1, :] = np.maximum(self.alpha_paths[t+1, :], 1e-8)
            
            # Mise à jour de F selon beta
            F_current = self.F_paths[t, :]
            alpha_current = self.alpha_paths[t, :]
            
            if abs(self.beta - 0.5) < 1e-10:  # Cas beta = 0.5
                F_beta = np.sqrt(np.maximum(F_current, 1e-10))
                dF = alpha_current * F_beta * sqrt_dt * Z1[t, :]
                self.F_paths[t+1, :] = F_current + dF
            else:
                # Cas général
                F_beta = np.power(np.maximum(F_current, 1e-10), self.beta)
                dF = alpha_current * F_beta * sqrt_dt * Z1[t, :]
                self.F_paths[t+1, :] = F_current + dF
            
            # Protection contre valeurs négatives
            self.F_paths[t+1, :] = np.maximum(self.F_paths[t+1, :], 1e-10)
        
        # print("✅ Simulation SABR terminée!")
        return self
    
    def to_dataframe(self, simulation_index=0):
        """Convertit simulation SABR au format OHLCV"""
        if not hasattr(self, 'F_paths'):
            raise ValueError("Aucune simulation disponible. Lancez d'abord simulate()")
        
        prices = self.F_paths[:, simulation_index]
        alphas = self.alpha_paths[:, simulation_index]
        
        # Dates
        start_date = pd.to_datetime(self.end_date)
        dates = pd.date_range(start=start_date, periods=len(prices), freq='D')
        
        df = pd.DataFrame(index=dates)
        df['Close'] = prices
        
        # OHLV basé sur alpha (volatilité locale)
        local_vols = alphas / np.sqrt(252)
        
        # Open avec gaps
        df['Open'] = df['Close'].shift(1) * (1 + np.random.normal(0, local_vols * 0.1))
        df['Open'].iloc[0] = prices[0]
        
        # High/Low basés sur la volatilité locale
        high_factor = 1 + np.abs(np.random.normal(0, local_vols * 0.6))
        low_factor = 1 - np.abs(np.random.normal(0, local_vols * 0.6))
        
        df['High'] = np.maximum(df['Open'], df['Close']) * high_factor
        df['Low'] = np.minimum(df['Open'], df['Close']) * low_factor
        
        # Volume corrélé à alpha
        base_volume = 1000000
        vol_factor = alphas / np.mean(alphas)
        df['Volume'] = (base_volume * vol_factor * (1 + np.random.uniform(0.5, 1.5, len(prices)))).astype(int)
        
        return df.dropna()
    
    def get_parameters(self):
        """Retourne les paramètres SABR"""
        if not self.is_fitted:
            return {}
        return {
            'alpha0': self.alpha0,
            'beta': self.beta,
            'rho': self.rho,
            'nu': self.nu,
            'F0': self.F0
        }

# ========================================================================================
# FACTORY PATTERN POUR CRÉATION DE MODÈLES
# ========================================================================================

class ModelFactory:
    """Factory pour créer et gérer les modèles synthétiques"""
    
    AVAILABLE_MODELS = {
        'gbm': {
            'class': MonteCarloGBM,
            'name': 'Monte Carlo GBM',
            'description': 'Geometric Brownian Motion - Modèle le plus simple avec volatilité constante',
            'complexity': 'Simple',
            'parameters': ['mu', 'sigma']
        },
        'heston': {
            'class': HestonSynthetic,
            'name': 'Heston Stochastic Volatility',
            'description': 'Modèle avec volatilité stochastique - Capture les clusters de volatilité',
            'complexity': 'Intermédiaire',
            'parameters': ['mu', 'kappa', 'theta', 'xi', 'rho']
        },
        'bates': {
            'class': BatesSynthetic,
            'name': 'Bates Jump-Diffusion',
            'description': 'Heston + Sauts de Poisson - Modèle le plus réaliste pour les chocs de marché',
            'complexity': 'Avancé',
            'parameters': ['mu', 'kappa', 'theta', 'xi', 'rho', 'lambda_j', 'mu_j', 'sigma_j']
        },
        'sabr': {
            'class': SABRSynthetic,
            'name': 'SABR Model',
            'description': 'Stochastic Alpha Beta Rho - Populaire pour les options et dérivés',
            'complexity': 'Avancé',
            'parameters': ['alpha0', 'beta', 'rho', 'nu']
        }
    }
    
    @classmethod
    def create_model(cls, model_type, ticker='AAPL', start_date='2020-01-01', end_date='2025-01-01', **kwargs):
        """
        Crée une instance de modèle
        
        Parameters:
        -----------
        model_type : str
            Type de modèle ('gbm', 'heston', 'bates', 'sabr')
        ticker : str
            Symbole de l'actif
        start_date : str
            Date de début pour calibration
        end_date : str
            Date de fin pour calibration
        **kwargs : dict
            Paramètres additionnels pour le modèle
        """
        if model_type not in cls.AVAILABLE_MODELS:
            available = ', '.join(cls.AVAILABLE_MODELS.keys())
            raise ValueError(f"Modèle '{model_type}' non disponible. Modèles disponibles: {available}")
        
        model_class = cls.AVAILABLE_MODELS[model_type]['class']
        return model_class(ticker=ticker, start_date=start_date, end_date=end_date, **kwargs)
    
    @classmethod
    def get_model_info(cls, model_type=None):
        """Retourne les informations sur les modèles disponibles"""
        if model_type:
            return cls.AVAILABLE_MODELS.get(model_type, {})
        return cls.AVAILABLE_MODELS
    
    @classmethod
    def list_models(cls):
        """Liste tous les modèles disponibles"""
        models = []
        for key, info in cls.AVAILABLE_MODELS.items():
            models.append({
                'id': key,
                'name': info['name'],
                'description': info['description'],
                'complexity': info['complexity']
            })
        return models

# ========================================================================================
# UTILITAIRES POUR L'INTÉGRATION AVEC BACKTESTER
# ========================================================================================

class SyntheticDataManager:
    """Gestionnaire pour intégrer les données synthétiques avec le Backtester"""
    
    def __init__(self):
        self.generated_data = {}
        self.models = {}
    
    def generate_data(self, model_type, symbols, start_date, end_date, 
                     T=1, n_steps=252, n_simulations=1000, **model_params):
        """
        Génère des données synthétiques pour une liste de symboles
        
        Parameters:
        -----------
        model_type : str
            Type de modèle à utiliser
        symbols : list
            Liste des symboles à générer
        start_date : str
            Date de début (pour calibration)
        end_date : str
            Date de fin (pour calibration)
        T : float
            Horizon de simulation en années
        n_steps : int
            Nombre de pas de temps
        n_simulations : int
            Nombre de simulations (on utilise la première)
        **model_params : dict
            Paramètres spécifiques au modèle
        """
        # print(f"🔄 Génération de données synthétiques avec le modèle {model_type}")
        
        synthetic_data = {}
        
        for symbol in symbols:
            try:
                # print(f"📊 Traitement de {symbol}...")
                
                # Créer et calibrer le modèle
                model = ModelFactory.create_model(
                    model_type=model_type,
                    ticker=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # Appliquer les paramètres personnalisés si fournis
                if model_params:
                    for param, value in model_params.items():
                        if hasattr(model, param):
                            setattr(model, param, value)
                
                # Simuler
                model.fit()
                model.simulate(T=T, n_steps=n_steps, n_simulations=n_simulations)
                
                # Convertir au format OHLCV
                df = model.to_dataframe(simulation_index=0)
                synthetic_data[symbol] = df
                
                # Stocker le modèle pour référence
                self.models[symbol] = model
                
                # print(f"✅ {symbol}: {len(df)} points générés")
                
            except Exception as e:
                print(f"❌ Erreur pour {symbol}: {e}")
                continue
        
        if not synthetic_data:
            raise ValueError("Aucune donnée synthétique générée avec succès")
        
        # Convertir au format MultiIndex attendu par Backtester
        processed_data = self._convert_to_multiindex(synthetic_data)
        
        # Stocker pour référence
        self.generated_data[f"{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"] = {
            'data': processed_data,
            'metadata': {
                'model_type': model_type,
                'symbols': symbols,
                'generation_date': datetime.now(),
                'simulation_params': {
                    'T': T,
                    'n_steps': n_steps,
                    'n_simulations': n_simulations
                },
                'model_params': model_params
            }
        }
        
        return processed_data
    
    def _convert_to_multiindex(self, synthetic_data):
        """
        Convertit les données synthétiques au format MultiIndex (symbol, indicator)
        compatible avec le Backtester existant
        """
        # print("🔧 Conversion au format MultiIndex...")
        
        # Trouver les dates communes à tous les symboles
        common_dates = None
        for symbol, df in synthetic_data.items():
            if common_dates is None:
                common_dates = set(df.index)
            else:
                common_dates &= set(df.index)
        
        if not common_dates:
            raise ValueError("Aucune date commune entre les symboles")
        
        common_dates = sorted(common_dates)
        # print(f"📅 {len(common_dates)} dates communes trouvées")
        
        # Créer la structure MultiIndex
        combined_data_frames = []
        
        for symbol, df in synthetic_data.items():
            # Filtrer pour les dates communes
            df_filtered = df.loc[df.index.isin(common_dates)].copy()
            df_filtered = df_filtered.sort_index()
            
            # Créer le MultiIndex (symbol, indicator)
            new_columns = pd.MultiIndex.from_tuples(
                [(symbol, col) for col in df_filtered.columns],
                names=['symbol', 'indicator']
            )
            df_filtered.columns = new_columns
            
            combined_data_frames.append(df_filtered)
        
        # Concaténer tous les DataFrames
        combined_data = pd.concat(combined_data_frames, axis=1)
        
        # print(f"✅ Structure MultiIndex créée: {combined_data.shape}")
        return combined_data
    
    def get_model_summary(self, symbol):
        """Retourne un résumé du modèle utilisé pour un symbole"""
        if symbol not in self.models:
            return None
        
        model = self.models[symbol]
        return {
            'model_name': model.model_name,
            'symbol': symbol,
            'fitted': model.is_fitted,
            'parameters': model.get_parameters(),
            'model_info': model.get_model_info()
        }

# ========================================================================================
# EXEMPLE D'UTILISATION
# ========================================================================================

if __name__ == "__main__":
    # print("🚀 TEST DE L'INFRASTRUCTURE DES MODÈLES SYNTHÉTIQUES")
    # print("=" * 60)
    
    # 1. Lister les modèles disponibles
    # print("\n📋 Modèles disponibles:")
    # for model in ModelFactory.list_models():
        # print(f"  • {model['id']}: {model['name']} ({model['complexity']})")
        # print(f"    {model['description']}")
    
    # 2. Test avec un modèle simple (GBM)
    # print("\n🧪 Test du modèle GBM...")
    gbm = ModelFactory.create_model('gbm', ticker='AAPL')
    gbm.fit()
    gbm.simulate(T=1, n_steps=252, n_simulations=100)
    df_gbm = gbm.to_dataframe()
    # print(f"✅ GBM: {len(df_gbm)} lignes générées")
    # print(f"   Prix initial: ${df_gbm['Close'].iloc[0]:.2f}")
    # print(f"   Prix final: ${df_gbm['Close'].iloc[-1]:.2f}")
    
    # 3. Test avec Heston
    # print("\n🧪 Test du modèle Heston...")
    heston = ModelFactory.create_model('heston', ticker='AAPL')
    heston.fit()
    heston.simulate(T=1, n_steps=252, n_simulations=100)
    df_heston = heston.to_dataframe()
    # print(f"✅ Heston: {len(df_heston)} lignes générées")
    
    # 4. Test du SyntheticDataManager
    # print("\n🔧 Test du SyntheticDataManager...")
    manager = SyntheticDataManager()
    
    try:
        synthetic_data = manager.generate_data(
            model_type='gbm',
            symbols=['AAPL', 'MSFT'],
            start_date='2020-01-01',
            end_date='2025-01-01',
            T=0.5,  # 6 mois
            n_steps=126,  # ~6 mois de trading
            n_simulations=10
        )
        
        # print(f"✅ Données synthétiques générées: {synthetic_data.shape}")
        # print(f"   Colonnes: {list(synthetic_data.columns)}")
        # print(f"   Période: {synthetic_data.index[0]} à {synthetic_data.index[-1]}")
        
        # Test d'accès aux données (format Backtester)
        aapl_close = synthetic_data[('AAPL', 'Close')]
        # print(f"   AAPL Close: ${aapl_close.iloc[0]:.2f} → ${aapl_close.iloc[-1]:.2f}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
