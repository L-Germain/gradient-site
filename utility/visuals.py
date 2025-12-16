import os
import sys
import pandas as pd
from plotly import graph_objects as go
import plotly.express as px
sys.path.append(os.path.abspath(".."))
from indicators import calculate_indicator

#---------------------------------------------------------
# UPDATED
#---------------------------------------------------------

def generate_plotly_figures(obj):
    """
    Génère des graphiques Plotly pour visualiser les résultats du backtest
    Avec correction pour l'accès aux données MultiIndex inversées (symbol, type)
    """
    if not hasattr(obj, 'equity_df'):
        print("Exécutez d'abord le backtest avec la méthode run_backtest().")
        return {}
    
    figures = {}
    
    # 1. Courbe d'équité
    fig_equity = go.Figure()
    fig_equity.add_trace(go.Scatter(
        x=obj.equity_df.index, 
        y=obj.equity_df['total_equity'],
        mode='lines',
        name='Équité totale',
        line=dict(color='#3498db', width=2)
    ))
    fig_equity.add_trace(go.Scatter(
        x=obj.equity_df.index, 
        y=obj.equity_df['capital'],
        mode='lines',
        name='Capital disponible',
        line=dict(color='#2ecc71', width=2, dash='dash')
    ))
    fig_equity.add_trace(go.Scatter(
        x=obj.equity_df.index, 
        y=obj.equity_df['portfolio_value'],
        mode='lines',
        name='Valeur du portefeuille',
        line=dict(color='#9b59b6', width=2, dash='dot')
    ))
    
    fig_equity.update_layout(
        title=f"Courbe d'équité - {obj.name}",
        xaxis_title='Date',
        yaxis_title='Valeur (€)',
        template='plotly_dark',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        margin=dict(l=50, r=50, t=80, b=50),
        height=500
    )
    
    figures['equity'] = fig_equity
    
    # 2. Drawdown
    try:
        # Vérifier si les colonnes nécessaires existent
        if 'drawdown' not in obj.equity_df.columns:
            print("La colonne 'drawdown' n'existe pas. Calcul du drawdown...")
            # Calculer le drawdown ici si nécessaire
            obj.equity_df['previous_peak'] = obj.equity_df['total_equity'].cummax()
            obj.equity_df['drawdown'] = (obj.equity_df['total_equity'] / obj.equity_df['previous_peak'] - 1) * 100
        
        # Maintenant on peut créer le graphique de drawdown
        fig_drawdown = go.Figure()
        fig_drawdown.add_trace(go.Scatter(
            x=obj.equity_df.index, 
            y=obj.equity_df['drawdown'],
            mode='lines',
            name='Drawdown',
            line=dict(color='#e74c3c', width=2),
            fill='tozeroy'
        ))
        
        fig_drawdown.update_layout(
            title="Drawdown",
            xaxis_title='Date',
            yaxis_title='Drawdown (%)',
            template='plotly_dark',
            margin=dict(l=50, r=50, t=80, b=50),
            height=300
        )
        
        figures['drawdown'] = fig_drawdown
    except Exception as e:
        print(f"Erreur lors de la création du graphique de drawdown: {e}")
    
    # 3. Tableau des transactions
    if hasattr(obj, 'transactions_df') and not obj.transactions_df.empty:
        # Mettre en forme les données pour le tableau des transactions
        table_data = obj.transactions_df.copy()
        if isinstance(table_data['date'].iloc[0], pd.Timestamp):
            table_data['date'] = table_data['date'].dt.strftime('%Y-%m-%d')
        
        # Arrondir les valeurs numériques
        for col in ['price', 'shares', 'value', 'cost', 'remaining_capital']:
            if col in table_data.columns:
                table_data[col] = table_data[col].round(2)
        
        if 'pnl' in table_data.columns:
            table_data['pnl'] = table_data['pnl'].round(2)
            
        if 'pnl_pct' in table_data.columns:
            table_data['pnl_pct'] = table_data['pnl_pct'].round(2)
        
        figures['transactions'] = table_data
    
    # 4. Créer un graphique par symbole
    # 4. Créer un graphique par symbole
    for symbol in obj.symbols:
        # Données des prix
        fig_symbol = go.Figure()
        
        # Prix de clôture avec correction de l'accès aux données
        fig_symbol.add_trace(go.Scatter(
            x=obj.data.index,
            y=obj.data[(symbol, 'Close')],  # Structure inversée
            mode='lines',
            name=f'Prix de {symbol}',
            line=dict(color='#3498db', width=2),
            yaxis='y'  # Axe Y principal
        ))
        
        # Ajouter les transactions pour ce symbole
        if hasattr(obj, 'transactions_df') and not obj.transactions_df.empty:
            buy_transactions = obj.transactions_df[
                (obj.transactions_df['type'] == 'ACHAT') & 
                (obj.transactions_df['symbol'] == symbol)
            ]
            
            sell_transactions = obj.transactions_df[
                (obj.transactions_df['type'].isin([
                    'VENTE', 
                    'VENTE (TOUTES POSITIONS)',
                    'VENTE (POSITION)', 
                    'STOP LOSS', 
                    'TAKE PROFIT', 
                    'FIN BACKTEST',
                    'STOP LOSS (TOUTES POSITIONS)',
                    'TAKE PROFIT (TOUTES POSITIONS)', 
                    'STOP LOSS (POSITION)',
                    'TAKE PROFIT (POSITION)',
                    'FIN BACKTEST (TOUTES POSITIONS)',
                    'FIN BACKTEST (POSITION)'])) & 
                (obj.transactions_df['symbol'] == symbol)
            ]
            
            # Points d'achat
            if not buy_transactions.empty:
                fig_symbol.add_trace(go.Scatter(
                    x=buy_transactions['date'],
                    y=buy_transactions['price'],
                    mode='markers',
                    name='Achats',
                    marker=dict(
                        color='#2ecc71',
                        size=10,
                        symbol='triangle-up',
                        line=dict(
                            color='#27ae60',
                            width=2
                        )
                    ),
                    yaxis='y'  # Axe Y principal
                ))
            
            # Points de vente
            if not sell_transactions.empty:
                fig_symbol.add_trace(go.Scatter(
                    x=sell_transactions['date'],
                    y=sell_transactions['price'],
                    mode='markers',
                    name='Ventes',
                    marker=dict(
                        color='#e74c3c',
                        size=10,
                        symbol='triangle-down',
                        line=dict(
                            color='#c0392b',
                            width=2
                        )
                    ),
                    yaxis='y'  # Axe Y principal
                ))
        
        # Ajouter les indicateurs utilisés dans les conditions
        indicators_added = set()
        has_rsi = False  # Flag pour savoir si on a du RSI
        
        for block in obj.decision_blocks:
            for condition in block['conditions']:
                # Indicateur 1
                if condition['stock1'] == symbol and 'indicator1' in condition:
                    ind_type = condition['indicator1']['type']
                    if ind_type != 'PRICE':  # Ne pas ajouter le prix brut comme indicateur
                        params = condition['indicator1']['params'] if 'params' in condition['indicator1'] else []
                        indicator_name = f"{ind_type}({','.join(map(str, params))})"
                        
                        if indicator_name not in indicators_added:
                            # indicator_values = obj.calculate_indicator(obj.data, symbol, ind_type, params)
                            indicator_values = calculate_indicator(obj.data, symbol, ind_type, params)
                            
                            # Vérifier si c'est un RSI
                            if ind_type == 'RSI':
                                has_rsi = True
                                fig_symbol.add_trace(go.Scatter(
                                    x=obj.data.index,
                                    y=indicator_values,
                                    mode='lines',
                                    name=indicator_name,
                                    line=dict(width=1.5, dash='dash', color='#9b59b6'),
                                    yaxis='y2'  # Axe Y secondaire pour RSI
                                ))
                            else:
                                # Autres indicateurs sur l'axe principal
                                fig_symbol.add_trace(go.Scatter(
                                    x=obj.data.index,
                                    y=indicator_values,
                                    mode='lines',
                                    name=indicator_name,
                                    line=dict(width=1.5, dash='dash'),
                                    yaxis='y'  # Axe Y principal
                                ))
                            indicators_added.add(indicator_name)
                
                # Indicateur 2 (si comparaison d'indicateurs)
                if condition.get('comparison_type') == 'indicator' and condition['stock2'] == symbol and 'indicator2' in condition:
                    ind_type = condition['indicator2']['type']
                    if ind_type != 'PRICE':  # Ne pas ajouter le prix brut comme indicateur
                        params = condition['indicator2']['params'] if 'params' in condition['indicator2'] else []
                        indicator_name = f"{ind_type}({','.join(map(str, params))})"
                        
                        if indicator_name not in indicators_added:
                            indicator_values = calculate_indicator(obj.data, symbol, ind_type, params)
                            
                            # Vérifier si c'est un RSI
                            if ind_type == 'RSI':
                                has_rsi = True
                                fig_symbol.add_trace(go.Scatter(
                                    x=obj.data.index,
                                    y=indicator_values,
                                    mode='lines',
                                    name=indicator_name,
                                    line=dict(width=1.5, dash='dash', color='#9b59b6'),
                                    yaxis='y2'  # Axe Y secondaire pour RSI
                                ))
                            else:
                                # Autres indicateurs sur l'axe principal
                                fig_symbol.add_trace(go.Scatter(
                                    x=obj.data.index,
                                    y=indicator_values,
                                    mode='lines',
                                    name=indicator_name,
                                    line=dict(width=1.5, dash='dash'),
                                    yaxis='y'  # Axe Y principal
                                ))
                            indicators_added.add(indicator_name)
        
        # Configuration du layout avec double axe Y si RSI présent
        if has_rsi:
            # Ajouter les lignes de référence RSI (30 et 70)
            # fig_symbol.add_hline(y=30, line_dash="dot", line_color="red", 
            #                    annotation_text="RSI 30", yref='y2')
            # fig_symbol.add_hline(y=70, line_dash="dot", line_color="red", 
            #                    annotation_text="RSI 70", yref='y2')
            
            fig_symbol.update_layout(
                title=f"Prix et indicateurs - {symbol}",
                xaxis_title='Date',
                yaxis=dict(
                    title='Prix',
                    side='left'
                ),
                yaxis2=dict(
                    title='RSI',
                    side='right',
                    overlaying='y',
                    range=[0, 100],  # Fixer la plage RSI entre 0 et 100
                    showgrid=False   # Éviter la confusion avec les grilles
                ),
                template='plotly_dark',
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
                margin=dict(l=50, r=80, t=80, b=50),  # Plus de marge à droite pour l'axe RSI
                height=500
            )
        else:
            # Layout normal sans double axe
            fig_symbol.update_layout(
                title=f"Prix et indicateurs - {symbol}",
                xaxis_title='Date',
                yaxis_title='Prix',
                template='plotly_dark',
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
                margin=dict(l=50, r=50, t=80, b=50),
                height=500
            )
        
        figures[f'symbol_{symbol}'] = fig_symbol
    
    # 5. Créer un graphique du volume pour chaque symbole
    for symbol in obj.symbols:
        if (symbol, 'Volume') in obj.data.columns:  # Structure inversée
            fig_volume = go.Figure()
            
            fig_volume.add_trace(go.Bar(
                x=obj.data.index,
                y=obj.data[(symbol, 'Volume')],  # Structure inversée
                name=f'Volume {symbol}',
                marker_color='#7f8c8d'
            ))
            
            fig_volume.update_layout(
                title=f"Volume - {symbol}",
                xaxis_title='Date',
                yaxis_title='Volume',
                template='plotly_dark',
                margin=dict(l=50, r=50, t=80, b=50),
                height=300
            )
            
            figures[f'volume_{symbol}'] = fig_volume
    
    return figures