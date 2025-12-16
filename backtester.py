import sys
import json
import pandas as pd
import numpy as np

import os

from plotly import graph_objects as go
import plotly.express as px
from simulations.synthetic_models import *
from utility.constants import *
from utility.utils import *
from utility.signals import *
from data_collection import _download_data 
from indicators import *


class Backtester:
    def __init__(self, strategy_data, custom_dataframes=None):
        """
        Initialise le backtester.
        Accepte un dictionnaire de DataFrames personnalisés pré-chargés
        et ne télécharge que les tickers manquants.
        """
        print("=== DÉBOGAGE BACKTESTER INIT (v3) ===")
        self.min_holding_period = 1
        
        # Charger la stratégie (inchangé)
        if isinstance(strategy_data, str):
            with open(strategy_data, 'r') as f:
                self.strategy = json.load(f)
        else:
            self.strategy = strategy_data

        # Initialisation des paramètres (inchangé)
        self.name = self.strategy['name']
        self.initial_capital = self.strategy['initial_capital']
        self.allocation_pct = self.strategy['allocation_pct'] / 100
        self.transaction_cost = self.strategy['transaction_cost']
        self.stop_loss_pct = self.strategy.get('stop_loss_pct', 0) / 100
        self.take_profit_pct = self.strategy.get('take_profit_pct', 0) / 100
        self.start_date = self.strategy['date_range']['start']
        self.end_date = self.strategy['date_range']['end']
        self.decision_blocks = self.strategy['decision_blocks']
        self.capital = self.initial_capital
        self.portfolio = {}
        self.transactions = []
        self.equity_curve = []
        self.condition_history = {}
        
        # --- LOGIQUE DE CHARGEMENT DES DONNÉES CORRIGÉE ---
        all_symbols_in_strategy = self._extract_symbols()
        print(f"Symboles requis par la stratégie : {all_symbols_in_strategy}")

        if not all_symbols_in_strategy:
            raise ValueError("Erreur de stratégie : Aucun actif n'est associé à cette stratégie. Vérifiez vos conditions et actions.")

        # Si custom_dataframes n'est pas fourni, on l'initialise comme un dictionnaire vide
        if custom_dataframes is None:
            custom_dataframes = {}

        # On identifie les tickers à télécharger (ceux qui ne sont PAS dans nos données locales)
        tickers_to_download = [s for s in all_symbols_in_strategy if s not in custom_dataframes]
        
        all_dataframes = []

        # 1. Télécharger UNIQUEMENT les tickers nécessaires depuis Yahoo Finance
        download_errors = []
        if tickers_to_download:
            print(f"Téléchargement des tickers depuis Yahoo : {tickers_to_download}")
            try:
                yahoo_data = _download_data(tickers_to_download, self.start_date, self.end_date)
                all_dataframes.append(yahoo_data)
            except Exception as e:
                msg = f"Erreur lors du téléchargement des données Yahoo pour {tickers_to_download} : {str(e)}"
                print(msg)
                download_errors.append(msg)
        else:
            print("Aucun ticker à télécharger depuis Yahoo.")

        # 2. Utiliser les DataFrames personnalisés qui ont été passés en argument
        custom_assets_to_use = [s for s in all_symbols_in_strategy if s in custom_dataframes]
        if custom_assets_to_use:
            print(f"Utilisation des actifs locaux pré-chargés : {custom_assets_to_use}")
            for name in custom_assets_to_use:
                df = custom_dataframes[name].copy()
                df.columns = pd.MultiIndex.from_product([[name], df.columns])
                all_dataframes.append(df)
        else:
            print("Aucun actif local à utiliser pour cette stratégie.")
        
        # 3. Combiner toutes les données
        if not all_dataframes:
            error_details = "\n".join(download_errors) if download_errors else "Aucune source de données valide trouvée."
            raise ValueError(f"Impossible de récupérer les données pour les actifs : {all_symbols_in_strategy}.\nDétails : {error_details}")
        
        self.data = pd.concat(all_dataframes, axis=1)
        self.data.sort_index(inplace=True)
        self.symbols = list(set([col[0] for col in self.data.columns]))
        print(f"Données chargées et combinées pour les symboles : {self.symbols}")
        
    def get_current_portfolio_value(self, date_idx):
        """
        Calcule la valeur actuelle du portefeuille (capital + positions)
        """
        portfolio_value = 0
        
        for symbol in self.portfolio:
            try:
                current_price = self.data.loc[self.data.index[date_idx], (symbol, 'Close')]
                total_shares = self.portfolio[symbol]['total_shares']
                portfolio_value += total_shares * current_price
            except Exception as e:
                print(f"Erreur calcul valeur pour {symbol}: {e}")
                continue
        
        total_portfolio_value = self.capital + portfolio_value
        return total_portfolio_value

    def _extract_symbols(self):
        """
        Extrait tous les symboles uniques nécessaires pour le backtest
        """
        print("=== EXTRACTION DES SYMBOLES ===")
        symbols = set()
        
        # Parcourir tous les blocs de décision
        for i, block in enumerate(self.decision_blocks):
            print(f"Bloc {i}: {block}")
            
            # Extraire les symboles des conditions
            for j, condition in enumerate(block.get('conditions', [])):
                print(f"  Condition {j}: {condition}")
                if 'stock1' in condition:
                    symbols.add(condition['stock1'])
                    print(f"    Ajouté stock1: {condition['stock1']}")
                if 'stock2' in condition:
                    symbols.add(condition['stock2'])
                    print(f"    Ajouté stock2: {condition['stock2']}")
            
            # Extraire les symboles des actions
            for symbol in block.get('actions', {}):
                symbols.add(symbol)
                print(f"    Ajouté depuis actions: {symbol}")
        
        # Éliminer les valeurs None ou vides
        final_symbols = [s for s in list(symbols) if s]
        print(f"Symboles finaux: {final_symbols}")
        return final_symbols

    def execute_buy(self, symbol, date_idx, date):
        """Version modifiée pour permettre l'accumulation de positions (compatible DCA)"""
        
        # Calculer la valeur totale du portefeuille actuel
        current_portfolio_value = self.get_current_portfolio_value(date_idx)
        
        # Montant à allouer = % du portefeuille actuel
        amount_to_allocate = current_portfolio_value * self.allocation_pct
        
        print(f"[{date}] Portefeuille actuel: {current_portfolio_value:.2f}€")
        print(f"[{date}] Allocation {self.allocation_pct*100}%: {amount_to_allocate:.2f}€")
        
        if amount_to_allocate > self.capital:
            # Limiter à la liquidité disponible
            amount_to_allocate = self.capital - self.transaction_cost
            print(f"[{date}] Limité par liquidité: {amount_to_allocate:.2f}€")
        
        if amount_to_allocate > self.transaction_cost:
            # Accès correct aux données
            try:
                price = self.data.loc[self.data.index[date_idx], (symbol, 'Close')]
            except KeyError:
                print(f"Impossible d'accéder à ({symbol}, 'Close')")
                # Chercher une colonne Close alternative
                available_cols = [col for col in self.data.columns if col[0] == symbol and 'Close' in str(col[1])]
                if available_cols:
                    price = self.data.loc[self.data.index[date_idx], available_cols[0]]
                    print(f"Utilisation de {available_cols[0]} pour le prix")
                else:
                    print(f"Aucune colonne Close trouvée pour {symbol}")
                    return
            
            shares = (amount_to_allocate - self.transaction_cost) / price
            
            if shares > 0:
                # Créer une nouvelle position
                new_position = {
                    'shares': shares,
                    'entry_price': price,
                    'entry_date': date,
                    'stop_loss': price * (1 - self.stop_loss_pct) if self.stop_loss_pct > 0 else None,
                    'take_profit': price * (1 + self.take_profit_pct) if self.take_profit_pct > 0 else None,
                    'allocated_amount': amount_to_allocate,
                    'position_id': f"{symbol}_{date.strftime('%Y%m%d_%H%M%S')}"  # ID unique
                }
                
                # Ajouter à la structure du portefeuille
                if symbol not in self.portfolio:
                    self.portfolio[symbol] = {
                        'total_shares': 0,
                        'positions': [],
                        'avg_price': 0
                    }
                
                # Mettre à jour les totaux
                old_total_value = self.portfolio[symbol]['total_shares'] * self.portfolio[symbol]['avg_price']
                new_total_shares = self.portfolio[symbol]['total_shares'] + shares
                new_total_value = old_total_value + (shares * price)
                if new_total_shares > 0:
                    new_avg_price = new_total_value / new_total_shares if new_total_value > 0 else price
                else:
                    new_avg_price = price
                
                self.portfolio[symbol]['total_shares'] = new_total_shares
                self.portfolio[symbol]['avg_price'] = new_avg_price
                self.portfolio[symbol]['positions'].append(new_position)
                
                # Mettre à jour le capital
                self.capital -= (shares * price) + self.transaction_cost
                
                # Enregistrer la transaction
                self.transactions.append({
                    'date': date,
                    'type': 'ACHAT',
                    'symbol': symbol,
                    'price': price,
                    'shares': shares,
                    'value': shares * price,
                    'cost': self.transaction_cost,
                    'remaining_capital': self.capital,
                    'portfolio_value_before': current_portfolio_value,
                    'allocation_pct_used': self.allocation_pct * 100,
                    'amount_allocated': amount_to_allocate,
                    'total_shares_after': self.portfolio[symbol]['total_shares'],
                    'avg_price_after': self.portfolio[symbol]['avg_price'],
                    'position_id': new_position['position_id']
                })
                
                print(f"[{date}] ACHAT: {shares:.6f} {symbol} @ {price:.2f}€")
                print(f"[{date}] Total {symbol}: {self.portfolio[symbol]['total_shares']:.6f} shares @ {self.portfolio[symbol]['avg_price']:.2f}€ moyenne")
                print(f"[{date}] Capital restant: {self.capital:.2f}€")

    def execute_sell(self, symbol, date_idx, date, reason="VENTE", sell_all=False, position_id=None):
        """Version modifiée pour mieux gérer les types de transactions DCA"""
        
        if symbol not in self.portfolio or self.portfolio[symbol]['total_shares'] <= 0:
            print(f"[{date}] Pas de positions à vendre pour {symbol}")
            return
        
        # Accès correct aux données
        try:
            price = self.data.loc[self.data.index[date_idx], (symbol, 'Close')]
        except KeyError:
            # Chercher une colonne Close alternative
            available_cols = [col for col in self.data.columns if col[0] == symbol and 'Close' in str(col[1])]
            if available_cols:
                price = self.data.loc[self.data.index[date_idx], available_cols[0]]
            else:
                print(f"Impossible de vendre {symbol}: pas de prix disponible")
                return
        
        # LOGIQUE DCA VENTE : Vendre un pourcentage fixe des positions
        if not sell_all and reason == "VENTE":  # DCA vente
            # Calculer la portion à vendre (basé sur allocation_pct)
            total_shares = self.portfolio[symbol]['total_shares']
            shares_to_sell = total_shares * self.allocation_pct  # Même % que pour l'achat
            
            # S'assurer qu'on ne vend pas plus que ce qu'on a
            if shares_to_sell > total_shares:
                shares_to_sell = total_shares
            
            # Valeur de la vente
            sale_value = shares_to_sell * price
            
            print(f"[{date}] DCA VENTE: {shares_to_sell:.6f} {symbol} @ {price:.2f}€")
            print(f"[{date}] Valeur de la vente: {sale_value:.2f}€")
            print(f"[{date}] Reste: {total_shares - shares_to_sell:.6f} {symbol}")
            
            # Mettre à jour le capital
            self.capital += sale_value - self.transaction_cost
            
            # Calculer le P&L global (approximatif basé sur prix moyen)
            avg_price = self.portfolio[symbol]['avg_price']
            # Soustraire les frais une seule fois du P&L total
            total_pnl = (price - avg_price) * shares_to_sell - self.transaction_cost
            total_pnl_pct = ((price / avg_price) - 1) * 100
            
            # Vendre proportionnellement dans toutes les positions (FIFO)
            remaining_to_sell = shares_to_sell
            sold_positions = []
            
            for i, position in enumerate(self.portfolio[symbol]['positions']):
                if remaining_to_sell <= 0:
                    break
                
                position_shares = position['shares']
                
                if remaining_to_sell >= position_shares:
                    # Vendre toute cette position
                    sold_shares = position_shares
                    remaining_to_sell -= position_shares
                    sold_positions.append(i)
                else:
                    # Vendre partiellement cette position
                    sold_shares = remaining_to_sell
                    position['shares'] -= sold_shares
                    remaining_to_sell = 0
                
                # Calculer le P&L de cette position
                position_pnl = (price - position['entry_price']) * sold_shares
                position_pnl_pct = ((price / position['entry_price']) - 1) * 100
            
            # Supprimer les positions entièrement vendues (en partant de la fin)
            for i in reversed(sold_positions):
                del self.portfolio[symbol]['positions'][i]
            
            # Mettre à jour les totaux du portefeuille
            self.portfolio[symbol]['total_shares'] -= shares_to_sell
            
            # Recalculer le prix moyen si il reste des positions
            if self.portfolio[symbol]['positions']:
                total_value = sum(pos['shares'] * pos['entry_price'] for pos in self.portfolio[symbol]['positions'])
                self.portfolio[symbol]['avg_price'] = total_value / self.portfolio[symbol]['total_shares']
            else:
                # Plus de positions, supprimer l'entrée
                del self.portfolio[symbol]
            
            # CORRECTION: Marquer clairement le type de transaction pour les métriques
            transaction_type = "VENTE (DCA PARTIELLE)" if shares_to_sell < total_shares else "VENTE (DCA TOTALE)"
            
            # Enregistrer la transaction DCA VENTE
            self.transactions.append({
                'date': date,
                'type': transaction_type,  # Type spécifique pour DCA
                'symbol': symbol,
                'price': price,
                'shares': shares_to_sell,
                'value': sale_value,
                'cost': self.transaction_cost,
                'pnl': total_pnl,
                'pnl_pct': total_pnl_pct,
                'remaining_capital': self.capital,
                'avg_entry_price': avg_price,
                'remaining_shares': self.portfolio[symbol]['total_shares'] if symbol in self.portfolio else 0,
                'sale_type': 'DCA_PARTIAL'  # Marqueur pour distinguer
            })
            
            print(f"[{date}] P&L DCA vente: {total_pnl:.2f}€ ({total_pnl_pct:.2f}%)")
            print(f"[{date}] Capital après vente: {self.capital:.2f}€")
        
        else:
            # VENTE TOTALE (logique existante inchangée)
            if sell_all or len(self.portfolio[symbol]['positions']) == 1:
                # Vendre toutes les positions
                total_shares = self.portfolio[symbol]['total_shares']
                avg_price = self.portfolio[symbol]['avg_price']
                
                sale_value = total_shares * price
                self.capital += sale_value - self.transaction_cost
                
                # Calculer le P&L global
                total_cost = total_shares * avg_price + self.transaction_cost * len(self.portfolio[symbol]['positions'])
                total_pnl = sale_value - total_cost - self.transaction_cost
                total_pnl_pct = ((price / avg_price) - 1) * 100
                
                self.transactions.append({
                    'date': date,
                    'type': f"{reason} (TOUTES POSITIONS)",
                    'symbol': symbol,
                    'price': price,
                    'shares': total_shares,
                    'value': sale_value,
                    'cost': self.transaction_cost,
                    'pnl': total_pnl,
                    'pnl_pct': total_pnl_pct,
                    'remaining_capital': self.capital,
                    'avg_entry_price': avg_price,
                    'positions_sold': len(self.portfolio[symbol]['positions'])
                })
                
                print(f"[{date}] {reason}: TOUTES POSITIONS {total_shares:.6f} {symbol} @ {price:.2f}€")
                print(f"[{date}] P&L total: {total_pnl:.2f}€ ({total_pnl_pct:.2f}%)")
                print(f"[{date}] Capital après vente: {self.capital:.2f}€")
                
                # Supprimer toutes les positions
                del self.portfolio[symbol]
            
            else:
                # Vendre seulement la position la plus ancienne (FIFO) - logique existante
                oldest_position = self.portfolio[symbol]['positions'][0]
                shares = oldest_position['shares']
                entry_price = oldest_position['entry_price']
                allocated_amount = oldest_position['allocated_amount']
                
                sale_value = shares * price
                self.capital += sale_value - self.transaction_cost
                
                pnl = (price - entry_price) * shares - self.transaction_cost * 2
                pnl_pct = ((price / entry_price) - 1) * 100
                allocation_return_pct = ((sale_value - self.transaction_cost) / allocated_amount - 1) * 100
                
                # Mettre à jour le portefeuille
                self.portfolio[symbol]['total_shares'] -= shares
                self.portfolio[symbol]['positions'].pop(0)
                
                # Recalculer le prix moyen si il reste des positions
                if self.portfolio[symbol]['positions']:
                    total_value = sum(pos['shares'] * pos['entry_price'] for pos in self.portfolio[symbol]['positions'])
                    self.portfolio[symbol]['avg_price'] = total_value / self.portfolio[symbol]['total_shares']
                else:
                    # Plus de positions, supprimer l'entrée
                    del self.portfolio[symbol]
                
                self.transactions.append({
                    'date': date,
                    'type': f"{reason} (POSITION)",
                    'symbol': symbol,
                    'price': price,
                    'shares': shares,
                    'value': sale_value,
                    'cost': self.transaction_cost,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'remaining_capital': self.capital,
                    'allocated_amount': allocated_amount,
                    'allocation_return_pct': allocation_return_pct,
                    'position_id': oldest_position['position_id'],
                    'remaining_positions': len(self.portfolio[symbol]['positions']) if symbol in self.portfolio else 0
                })
                
                print(f"[{date}] {reason}: {shares:.6f} {symbol} @ {price:.2f}€")
                print(f"[{date}] P&L: {pnl:.2f}€ ({pnl_pct:.2f}%)")
                remaining = len(self.portfolio[symbol]['positions']) if symbol in self.portfolio else 0
                print(f"[{date}] Positions restantes pour {symbol}: {remaining}")

    def check_dca_condition(self, symbol, period, date_idx):
        """
        Vérifie si c'est un jour d'achat DCA
        """
        # Calculer si nous sommes à un multiple de la période depuis le début
        return date_idx % period == 0

    def check_stop_loss_take_profit(self, date_idx, date):
        """Version modifiée pour gérer les positions multiples"""
        symbols_to_process = list(self.portfolio.keys())
        
        for symbol in symbols_to_process:
            if symbol not in self.portfolio:
                continue
                
            try:
                current_price = self.data.loc[self.data.index[date_idx], (symbol, 'Close')]
            except KeyError:
                continue
            
            positions_to_remove = []
            
            # Vérifier chaque position individuellement
            for i, position in enumerate(self.portfolio[symbol]['positions']):
                days_held = (date - position['entry_date']).days
                
                if days_held < self.min_holding_period:
                    continue
                
                # Vérifier le stop loss
                if position['stop_loss'] is not None and current_price <= position['stop_loss']:
                    positions_to_remove.append(i)
                    continue
                
                # Vérifier le take profit
                if position['take_profit'] is not None and current_price >= position['take_profit']:
                    positions_to_remove.append(i)
                    continue
            
            # Vendre les positions qui ont atteint leurs seuils (en commençant par la fin pour ne pas décaler les indices)
            for i in reversed(positions_to_remove):
                position = self.portfolio[symbol]['positions'][i]
                
                if position['stop_loss'] is not None and current_price <= position['stop_loss']:
                    reason = "STOP LOSS"
                elif position['take_profit'] is not None and current_price >= position['take_profit']:
                    reason = "TAKE PROFIT"
                else:
                    continue
                
                # Vendre cette position spécifique
                shares = position['shares']
                entry_price = position['entry_price']
                allocated_amount = position['allocated_amount']
                
                sale_value = shares * current_price
                self.capital += sale_value - self.transaction_cost
                
                pnl = (current_price - entry_price) * shares - self.transaction_cost * 2
                pnl_pct = ((current_price / entry_price) - 1) * 100
                allocation_return_pct = ((sale_value - self.transaction_cost) / allocated_amount - 1) * 100
                
                # Enregistrer la transaction
                self.transactions.append({
                    'date': date,
                    'type': reason,
                    'symbol': symbol,
                    'price': current_price,
                    'shares': shares,
                    'value': sale_value,
                    'cost': self.transaction_cost,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'remaining_capital': self.capital,
                    'allocated_amount': allocated_amount,
                    'allocation_return_pct': allocation_return_pct,
                    'position_id': position['position_id']
                })
                
                print(f"[{date}] {reason}: {shares:.6f} {symbol} @ {current_price:.2f}€, P&L: {pnl:.2f}€")
                
                # Supprimer la position
                self.portfolio[symbol]['total_shares'] -= shares
                self.portfolio[symbol]['positions'].pop(i)
                
                # Recalculer le prix moyen
                if self.portfolio[symbol]['positions']:
                    total_value = sum(pos['shares'] * pos['entry_price'] for pos in self.portfolio[symbol]['positions'])
                    self.portfolio[symbol]['avg_price'] = total_value / self.portfolio[symbol]['total_shares']
                else:
                    # Plus de positions
                    del self.portfolio[symbol]
                    break

    def run_backtest(self):
        """
        Version modifiée pour supporter les stratégies DCA avec signals.py
        """
        
        print(f"Démarrage du backtest pour la stratégie '{self.name}' avec support DCA...")
        
        # Initialiser la courbe d'équité
        self.equity_curve = [{
            'date': self.data.index[0],
            'capital': self.capital,
            'portfolio_value': 0,
            'total_equity': self.capital
        }]
        
        # Parcourir toutes les dates
        for i, date in enumerate(self.data.index):
            if i == 0:
                continue
            
            # 1. Vérifier les stop loss et take profit
            self.check_stop_loss_take_profit(i, date)
            
            # 2. Vérifier les conditions pour de nouvelles entrées
            for block_index, block in enumerate(self.decision_blocks):
                if not block['conditions']:
                    continue

                try:
                    # Vérifier chaque condition dans le bloc
                    all_conditions_met = True
                    has_dca_condition = False
                    dca_symbols = []
                    
                    for condition_index, condition in enumerate(block['conditions']):
                        # VÉRIFICATION SPÉCIALE POUR DCA
                        if (condition.get('indicator1', {}).get('type') == 'DCA' or 
                            condition.get('indicator2', {}).get('type') == 'DCA'):
                            
                            has_dca_condition = True
                            
                            # Extraire la période DCA
                            if condition.get('indicator1', {}).get('type') == 'DCA':
                                dca_period = condition['indicator1']['params'][0] if condition['indicator1']['params'] else 30
                                dca_symbol = condition['stock1']
                            else:
                                dca_period = condition['indicator2']['params'][0] if condition['indicator2']['params'] else 30
                                dca_symbol = condition['stock2']
                            
                            # Vérifier si c'est un jour DCA
                            is_dca_day = (i % dca_period == 0)
                            
                            if condition['operator'] == '==' and condition.get('comparison_type') == 'value':
                                # Condition: DCA == 1 (jour d'achat DCA)
                                if condition['comparison_value'] == 1:
                                    condition_met = is_dca_day
                                else:
                                    condition_met = not is_dca_day
                            else:
                                # Pour d'autres comparaisons, utiliser signals.py
                                condition_met = check_condition(self.data, condition, i)
                            
                            if not condition_met:
                                all_conditions_met = False
                                break
                            
                            if is_dca_day:
                                dca_symbols.append(dca_symbol)
                        
                        else:
                            # Condition normale (non-DCA) - UTILISER signals.py
                            if has_dca_condition:
                                # Si on a des conditions DCA ET normales, vérifier les deux
                                crossover = check_condition_crossover_with_tolerance(
                                    self.data, condition, i, block_index, condition_index, tolerance=0.00
                                )
                                condition_met = crossover and check_condition(self.data, condition, i)
                            else:
                                # Logique crossover normale pour conditions non-DCA
                                crossover = check_condition_crossover_with_tolerance(
                                    self.data, condition, i, block_index, condition_index, tolerance=0.00
                                )
                                condition_met = crossover and check_condition(self.data, condition, i)
                            
                            if not condition_met:
                                all_conditions_met = False
                                break
                    
                    # Exécuter les actions si toutes les conditions sont remplies
                    if all_conditions_met:
                        if has_dca_condition and dca_symbols:
                            print(f"[{date}] SIGNAL DCA - Jour d'opération périodique")
                            
                            # Exécuter les actions DCA selon le type
                            for symbol in dca_symbols:
                                if symbol in block.get('actions', {}):
                                    action = block['actions'][symbol]
                                    
                                    if action == 'Acheter':
                                        self.execute_buy(symbol, i, date)
                                        
                                    elif action == 'Vendre':
                                        if symbol in self.portfolio:
                                            # DCA VENTE : vente partielle régulière
                                            self.execute_sell(symbol, i, date, "VENTE", sell_all=False)
                                        else:
                                            print(f"[{date}] Pas de positions {symbol} à vendre")
                        else:
                            print(f"[{date}] SIGNAL D'ACHAT/VENTE - Crossover détecté dans le bloc {block_index}")
                            
                            # Exécuter les actions normales
                            for symbol, action in block.get('actions', {}).items():
                                if action == "Acheter":
                                    self.execute_buy(symbol, i, date)
                                elif action == "Vendre":
                                    if symbol in self.portfolio:
                                        self.execute_sell(symbol, i, date, "VENTE", sell_all=True)  # Vente totale
                
                except Exception as e:
                    print(f"Erreur dans le bloc de décision {block_index}: {e}")
                    continue
            
            # 3. Calculer la valeur du portefeuille
            portfolio_value = 0
            for symbol in self.portfolio:
                try:
                    current_price = self.data[(symbol, 'Close')].iloc[i]
                    portfolio_value += self.portfolio[symbol]['total_shares'] * current_price
                except:
                    continue
            
            # 4. Mettre à jour la courbe d'équité
            self.equity_curve.append({
                'date': date,
                'capital': self.capital,
                'portfolio_value': portfolio_value,
                'total_equity': self.capital + portfolio_value
            })
        
        # Liquider toutes les positions à la fin
        last_idx = len(self.data.index) - 1
        last_date = self.data.index[-1]
        
        print(f"\n=== LIQUIDATION FINALE ===")
        for symbol in list(self.portfolio.keys()):
            if symbol in self.portfolio and self.portfolio[symbol]['total_shares'] > 0:
                print(f"Liquidation finale de {symbol}: {self.portfolio[symbol]['total_shares']:.6f} shares")
                self.execute_sell(symbol, last_idx, last_date, "VENTE (FIN BACKTEST)", sell_all=True)

        
        # Créer le DataFrame de la courbe d'équité
        self.equity_df = pd.DataFrame(self.equity_curve)
        self.equity_df.set_index('date', inplace=True)
        
        # Calculer les métriques
        self.calculate_performance_metrics()
        
        return self.equity_df

    def calculate_performance_metrics(self):
        """
        Version corrigée qui compte correctement les trades DCA
        """
        if len(self.transactions) == 0:
            print("Aucune transaction n'a été effectuée pendant le backtest.")
            self.metrics = {
                'Capital initial': self.initial_capital,
                'Capital final': self.initial_capital,
                'Rendement total (%)': 0,
                'Rendement annualisé (%)': 0,
                'Drawdown maximum (%)': 0,
                'Ratio de Sharpe': 0,
                'Nombre de trades': 0,
                'Nombre d\'achats': 0,
                'Nombre de ventes': 0,
                'Positions ouvertes': 0,
                'Pourcentage de trades gagnants (%)': 0,
                'Profit moyen par trade': 0,
                'Profit moyen des trades gagnants': 0,
                'Perte moyenne des trades perdants': 0,
                'Profit factor': 0
            }
            return

        # Créer un DataFrame avec les transactions
        self.transactions_df = pd.DataFrame(self.transactions)
        
        # Calculer les métriques de base
        final_equity = self.equity_df['total_equity'].iloc[-1]
        total_return = (final_equity / self.initial_capital - 1) * 100
        
        # Calculer le rendement annualisé
        days = (self.equity_df.index[-1] - self.equity_df.index[0]).days
        annualized_return = ((1 + total_return / 100) ** (365 / days) - 1) * 100 if days > 0 else 0
        
        # Calculer le drawdown maximum
        try:
            if 'total_equity' not in self.equity_df.columns:
                print("Avertissement: 'total_equity' n'est pas dans les colonnes du DataFrame")
                self.equity_df['total_equity'] = self.initial_capital
                
            self.equity_df['previous_peak'] = self.equity_df['total_equity'].cummax()
            # Éviter la division par zéro
            self.equity_df['drawdown'] = self.equity_df.apply(
                lambda row: 0 if row['previous_peak'] == 0 
                else ((row['total_equity'] / row['previous_peak'] - 1) * 100),
                axis=1
            )
            max_drawdown = self.equity_df['drawdown'].min()
        except Exception as e:
            print(f"Erreur lors du calcul du drawdown: {e}")
            self.equity_df['drawdown'] = 0
            max_drawdown = 0
        
        # Calculer le ratio de Sharpe (corrigé)
        daily_returns = self.equity_df['total_equity'].pct_change().dropna()
        if len(daily_returns) > 0:
            std_returns = daily_returns.std()
            if std_returns > 0:
                sharpe_ratio = np.sqrt(252) * daily_returns.mean() / std_returns
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        # CORRECTION: Compter correctement les trades (achats ET ventes)
        sell_types = ['VENTE', 'STOP LOSS', 'TAKE PROFIT', 'FIN BACKTEST', 'VENTE (FIN BACKTEST)', '(VENTE) FIN BACKTEST']
        buy_types = ['ACHAT']
        
        # Compter achats et ventes
        buy_transactions = self.transactions_df[self.transactions_df['type'].isin(buy_types)]
        sell_transactions = self.transactions_df[
            self.transactions_df['type'].isin(sell_types) | 
            self.transactions_df['type'].str.contains('VENTE', na=False)
        ]
        
        num_buys = len(buy_transactions)
        num_sells = len(sell_transactions)
        num_trades = num_sells  # Les trades complets sont basés sur les ventes (qui ont un P&L)
        open_positions = num_buys - num_sells if num_buys > num_sells else 0
        
        print(f"DEBUG: {num_buys} achats, {num_sells} ventes, {open_positions} positions ouvertes")
        print(f"DEBUG: Types de transactions uniques: {self.transactions_df['type'].unique()}")
        
        # Si pas de trades de vente mais qu'il y a des achats, calculer un trade virtuel
        if num_trades == 0 and num_buys > 0:
            print("DEBUG: Aucune vente détectée mais des achats présents - création d'un trade virtuel")
            # Calculer la valeur du portefeuille à la fin
            final_portfolio_value = 0
            for symbol in self.portfolio:
                if self.portfolio[symbol]['total_shares'] > 0:
                    try:
                        final_price = self.data[(symbol, 'Close')].iloc[-1]
                        final_portfolio_value += self.portfolio[symbol]['total_shares'] * final_price
                    except:
                        continue
            
            # Créer un trade virtuel pour les métriques
            if final_portfolio_value > 0:
                virtual_pnl = final_portfolio_value - sum(
                    t['value'] + t.get('cost', 0) for t in self.transactions 
                    if t['type'] == 'ACHAT'
                )
                
                virtual_trade = {
                    'type': 'VENTE (VIRTUELLE)',
                    'pnl': virtual_pnl,
                    'value': final_portfolio_value
                }
                
                temp_transactions = self.transactions_df.copy()
                temp_transactions = pd.concat([
                    temp_transactions, 
                    pd.DataFrame([virtual_trade])
                ], ignore_index=True)
                
                sell_transactions = temp_transactions[
                    temp_transactions['type'].str.contains('VENTE', na=False)
                ]
                num_trades = len(sell_transactions)
        
        # Identifier les trades gagnants et perdants
        if 'pnl' in sell_transactions.columns and len(sell_transactions) > 0:
            winning_trades = sell_transactions[sell_transactions['pnl'] > 0]
            losing_trades = sell_transactions[sell_transactions['pnl'] < 0]
            
            win_rate = len(winning_trades) / num_trades * 100 if num_trades > 0 else 0
            
            # Profit moyen par trade
            avg_profit = sell_transactions['pnl'].mean() if num_trades > 0 else 0
            avg_winning_trade = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
            avg_losing_trade = abs(losing_trades['pnl'].mean()) if len(losing_trades) > 0 else 0  # Valeur absolue
            
            # Calculer le profit factor (corrigé)
            gross_profit = winning_trades['pnl'].sum() if len(winning_trades) > 0 else 0
            gross_loss = abs(losing_trades['pnl'].sum()) if len(losing_trades) > 0 else 0
            
            if gross_loss > 0:
                profit_factor = gross_profit / gross_loss
            elif gross_profit > 0:
                profit_factor = 100.0  # Valeur maximale conventionnelle
            else:
                profit_factor = 1.0  # Ni gains ni pertes
            
            print(f"DEBUG: Winning trades: {len(winning_trades)}, Losing trades: {len(losing_trades)}")
            print(f"DEBUG: Win rate: {win_rate:.2f}%, Avg profit: {avg_profit:.2f}")
        else:
            win_rate = 0
            avg_profit = 0
            avg_winning_trade = 0
            avg_losing_trade = 0
            profit_factor = 0
        
        # Enregistrer les métriques (avec nouvelles métriques)
        self.metrics = {
            'Capital initial': self.initial_capital,
            'Capital final': final_equity,
            'Rendement total (%)': total_return,
            'Rendement annualisé (%)': annualized_return,
            'Drawdown maximum (%)': max_drawdown,
            'Ratio de Sharpe': sharpe_ratio,
            'Nombre de trades': num_trades,
            'Nombre d\'achats': num_buys,
            'Nombre de ventes': num_sells,
            'Positions ouvertes': open_positions,
            'Pourcentage de trades gagnants (%)': win_rate,
            'Profit moyen par trade': avg_profit,
            'Profit moyen des trades gagnants': avg_winning_trade,
            'Perte moyenne des trades perdants': avg_losing_trade,
            'Profit factor': profit_factor
        }
        
        # Afficher les métriques
        print("\n=== RÉSULTATS DU BACKTEST ===")
        for metric, value in self.metrics.items():
            if isinstance(value, (int, float)):
                print(f"{metric}: {value:.2f}")
            else:
                print(f"{metric}: {value}")


class BacktesterSynthetic(Backtester):
    """Version du Backtester qui accepte des données synthétiques"""
    
    def __init__(self, strategy_data, synthetic_data):
        """
        Initialise avec des données synthétiques au lieu de télécharger
        """
        # Copier les paramètres de stratégie
        if isinstance(strategy_data, dict):
            self.strategy = strategy_data
        else:
            with open(strategy_data, 'r') as f:
                self.strategy = json.load(f)
        
        self.name = self.strategy['name']
        self.initial_capital = self.strategy['initial_capital']
        self.allocation_pct = self.strategy['allocation_pct'] / 100
        self.transaction_cost = self.strategy['transaction_cost']
        self.stop_loss_pct = self.strategy.get('stop_loss_pct', 0) / 100
        self.take_profit_pct = self.strategy.get('take_profit_pct', 0) / 100
        self.start_date = self.strategy['date_range']['start']
        self.end_date = self.strategy['date_range']['end']
        self.decision_blocks = self.strategy['decision_blocks']
        self.min_holding_period = 1
        
        # Utiliser les données synthétiques fournies
        self.data = synthetic_data
        self.symbols = list(set([col[0] for col in synthetic_data.columns]))
        
        # Variables pour la performance
        self.capital = self.initial_capital
        self.portfolio = {}
        self.transactions = []
        self.equity_curve = []
        self.condition_history = {}
        
        print(f"BacktesterSynthetic initialisé:")
        print(f"   Stratégie: {self.name}")
        print(f"   Données: {len(synthetic_data)} points, {len(self.symbols)} symboles")


class MultiTrajectoryBacktester:
    """Exécute un backtest sur N trajectoires synthétiques"""
    
    def __init__(self, strategy_data, model_type, symbols, **model_params):
        self.strategy_data = strategy_data
        self.model_type = model_type
        self.symbols = symbols
        self.model_params = model_params
        self.results = []

    def run_monte_carlo_backtest(self, n_trajectories=1000, **sim_params):
        """Exécute le backtest sur n_trajectories"""
        
        print(f"Lancement de {n_trajectories} backtests Monte Carlo...")
        print(f"   Paramètres simulation: {sim_params}")
        print(f"   Paramètres modèle: {self.model_params}")
        
        manager = SyntheticDataManager()
        
        for i in range(n_trajectories):
            if i % 10 == 0:  # Plus fréquent pour debug
                print(f"   Trajectoire {i+1}/{n_trajectories}")
            
            try:
                # Générer UNE trajectoire avec seed différent
                import numpy as np
                np.random.seed(42 + i * 1000)
                
                synthetic_data = manager.generate_data(
                    model_type=self.model_type,
                    symbols=self.symbols,
                    n_simulations=1,
                    **sim_params,
                    **self.model_params
                )
                
                print(f"     Données générées: {synthetic_data.shape}")
                
                # Utiliser la classe BacktesterSynthetic définie globalement
                backtester = BacktesterSynthetic(self.strategy_data, synthetic_data)
                
                print(f"     Lancement du backtest...")
                backtester.run_backtest()
                
                print(f"     Calcul des métriques...")
                backtester.calculate_performance_metrics()
                
                print(f"     Métriques calculées: {list(backtester.metrics.keys())}")
                
                # Sauvegarder les résultats - CORRECTION DE L'ENCODAGE
                result = {
                    'trajectory_id': i,
                    'final_capital': backtester.metrics['Capital final'],
                    'total_return_pct': backtester.metrics['Rendement total (%)'],
                    'annualized_return_pct': backtester.metrics['Rendement annualisé (%)'],  # [OK] Bon encodage
                    'max_drawdown_pct': backtester.metrics['Drawdown maximum (%)'],
                    'sharpe_ratio': backtester.metrics['Ratio de Sharpe'],
                    'num_trades': backtester.metrics['Nombre de trades'],
                    'win_rate_pct': backtester.metrics['Pourcentage de trades gagnants (%)'],
                    'profit_factor': backtester.metrics['Profit factor'],
                    'avg_trade_pnl': backtester.metrics['Profit moyen par trade'],
                    'equity_curve': backtester.equity_df['total_equity'].values,
                    'transactions': len(backtester.transactions)
                }
                
                self.results.append(result)
                print(f"     [OK] Trajectoire {i} réussie: {result['total_return_pct']:.2f}%")
                
            except Exception as e:
                print(f"     [ERREUR] Erreur trajectoire {i}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        success_rate = len(self.results) / n_trajectories * 100
        print(f"[OK] {len(self.results)} trajectoires sur {n_trajectories} ({success_rate:.1f}%)")
        
        if len(self.results) == 0:
            raise ValueError(f"Aucun backtest réussi sur {n_trajectories} tentatives.")
        
        return self.analyze_results()
    
    def analyze_results(self):
        """Analyse statistique des résultats - CORRECTION DE L'ENCODAGE"""
        
        if not self.results:
            raise ValueError("Aucun résultat à analyser")
        
        import numpy as np
        import pandas as pd
        
        df = pd.DataFrame(self.results)
        
        # Métriques de tendance centrale - CORRECTION DE L'ENCODAGE
        central_metrics = {
            'Nombre de trajectoires': len(df),
            'Rendement médian (%)': df['total_return_pct'].median(),  # [OK] Bon encodage
            'Rendement moyen (%)': df['total_return_pct'].mean(),
            'Sharpe médian': df['sharpe_ratio'].median(),
            'Drawdown médian (%)': df['max_drawdown_pct'].median(),
        }
        
        # Intervalles de confiance
        confidence_intervals = {}
        confidence_levels = [5, 10, 25, 75, 90, 95]
        
        for metric in ['total_return_pct', 'max_drawdown_pct', 'sharpe_ratio', 'final_capital']:
            percentiles = np.percentile(df[metric], confidence_levels)
            confidence_intervals[metric] = dict(zip(confidence_levels, percentiles))
        
        # Value at Risk (VaR)
        var_metrics = {
            'VaR 95% (perte max 5% scenarios)': np.percentile(df['total_return_pct'], 5),
            'VaR 99% (perte max 1% scenarios)': np.percentile(df['total_return_pct'], 1),
            'Expected Shortfall 95%': df[df['total_return_pct'] <= np.percentile(df['total_return_pct'], 5)]['total_return_pct'].mean(),
            'Probabilité de perte': (df['total_return_pct'] < 0).mean() * 100,
            'Probabilité de ruine (perte >50%)': (df['total_return_pct'] < -50).mean() * 100,
        }
        
        # Métriques de performance par scénario
        scenario_metrics = {
            'Meilleur scénario (%)': df['total_return_pct'].max(),
            'Pire scénario (%)': df['total_return_pct'].min(),
            '% scénarios gagnants': (df['total_return_pct'] > 0).mean() * 100,
            '% scénarios > 10%': (df['total_return_pct'] > 10).mean() * 100,
            '% scénarios > 20%': (df['total_return_pct'] > 20).mean() * 100,
            'Sharpe > 1': (df['sharpe_ratio'] > 1).mean() * 100,
        }
        
        return {
            'raw_data': df,
            'central_metrics': central_metrics,
            'confidence_intervals': confidence_intervals,
            'var_metrics': var_metrics,
            'scenario_metrics': scenario_metrics
        }