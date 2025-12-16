# Ajouter ces imports au début de votre fichier dashboard
import os
import sys
from dash import dcc, html
import dash_bootstrap_components as dbc
sys.path.append(os.path.abspath(".."))
from utility.constants import *
from utility.translations import TEXT 
from plotly import graph_objects as go
import plotly.express as px
import json

# Fonctions utilitaires
def create_styled_dropdown(id, options, placeholder='Sélectionner...', value=None, 
                         searchable=True, clearable=True, multi=False, disabled=False):
    """Fonction utilitaire pour créer des dropdowns stylisés"""
    return dcc.Dropdown(
        id=id,
        options=options,
        value=value,
        placeholder=placeholder,
        searchable=searchable,
        clearable=clearable,
        multi=multi,
        disabled=disabled,
        className='dash-dropdown',
        style={'marginBottom': '10px'}
    )

def generate_indicator_input(indicator_type, outer_i, inner_j, pos):
    """Fonction utilitaire pour générer les entrées d'indicateurs"""
    return html.Div([
        create_styled_dropdown(
            id={'type': f'{indicator_type}-type', 'outer': outer_i, 'inner': inner_j, 'pos': pos},
            options=[{'label': ind, 'value': ind} for ind in indicators.keys()],
            placeholder='Indicateur'
        ),
        html.Div(
            id={'type': f'{indicator_type}-params-container', 'outer': outer_i, 'inner': inner_j, 'pos': pos},
            className="mt-2"
        ),
    ])

def generate_condition_block(outer_i, inner_j, available_stocks=None, language='fr'):
    """MODIFIÉ - Ajout du paramètre language"""
    t = TEXT.get(language, TEXT['fr'])
    stock_options = [{'label': s, 'value': s} for s in available_stocks or []]
    
    comparison_types = [
        {'label': t.get('dropdown-indicator', 'Indicateur'), 'value': 'indicator'},
        {'label': t.get('dropdown-value', 'Valeur'), 'value': 'value'}
    ]

    return html.Div([
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # Indicateur 1 avec stock
                    dbc.Col([
                        html.Label(html.Span(id=f"label-indicator1-{outer_i}-{inner_j}"), className="font-weight-bold text-info mb-2"),
                        create_styled_dropdown(
                            id={'type': 'stock1', 'outer': outer_i, 'inner': inner_j},
                            options=stock_options,
                            placeholder=t.get('placeholder-select-stock', 'Sélectionner une action'),
                            searchable=True
                        ),
                        generate_indicator_input("indicator1", outer_i, inner_j, 1)
                    ], width=4),

                    # Opérateur
                    dbc.Col([
                        html.Label(html.Span(id=f"label-operator-{outer_i}-{inner_j}"), className="font-weight-bold text-info mb-2"),
                        create_styled_dropdown(
                            id={'type': 'operator', 'outer': outer_i, 'inner': inner_j},
                            options=[{'label': op, 'value': op} for op in operators],
                            placeholder=t.get('placeholder-operator', 'Opérateur')
                        ),
                    ], width=2),

                    # Partie droite (comparaison)
                    dbc.Col([
                        html.Label(html.Span(id=f"label-comparison-type-{outer_i}-{inner_j}"), className="font-weight-bold text-info mb-2"),
                        create_styled_dropdown(
                            id={'type': 'comparison-type', 'outer': outer_i, 'inner': inner_j},
                            options=comparison_types,
                            value='indicator',
                            clearable=False
                        ),
                        html.Div(id={'type': 'comparison-container', 'outer': outer_i, 'inner': inner_j})
                    ], width=4),
                    
                    # Bouton de suppression
                    dbc.Col([
                        dbc.Button(
                            "×", 
                            id={'type': 'remove-condition', 'index': outer_i, 'inner': inner_j},
                            color="danger", 
                            size="sm", 
                            style={'marginTop': '30px', **BUTTON_STYLE}
                        )
                    ], width=2, className="d-flex justify-content-end")
                ])
            ])
        ], style=CARD_STYLE)
    ], className="mb-3", id={'type': 'condition-block', 'outer': outer_i, 'inner': inner_j})


def create_static_condition_block_complete(outer_i, inner_j, available_stocks=None, language='fr'):
    """Version debug pour vérifier les IDs"""
    t = TEXT.get(language, TEXT['fr'])
    
    # Debug - afficher l'ID qui sera créé
    operator_id = f'operator-{outer_i}-{inner_j}'
    # print(f"🆔 Création du dropdown opérateur avec ID: {operator_id}")
    
    return html.Div([
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # Indicateur 1
                    dbc.Col([
                        html.Label(html.Span(id=f"static-label-indicator1-{outer_i}-{inner_j}"), 
                                 className="font-weight-bold text-info mb-2"),
                        dcc.Dropdown(
                            id=f'stock1-{outer_i}-{inner_j}',
                            options=[],
                            searchable=True,
                            placeholder=t.get('placeholder-select-stock', 'Sélectionner une action'),
                            style={'marginBottom': '10px'},
                            persistence=True,
                            persistence_type='session'
                        ),
                        dcc.Dropdown(
                            id=f'indicator1-type-{outer_i}-{inner_j}',
                            options=[],
                            placeholder=t.get('placeholder-indicator', 'Indicateur'),
                            style={'marginBottom': '10px'},
                            persistence=True,
                            persistence_type='session'
                        ),
                        html.Div(id=f'indicator1-params-{outer_i}-{inner_j}', className="mt-2"),
                    ], width=4),

                    # OPÉRATEUR - SECTION CRITIQUE
                    dbc.Col([
                        html.Label(html.Span(id=f"static-label-operator-{outer_i}-{inner_j}"), 
                                 className="font-weight-bold text-info mb-2"),
                        dcc.Dropdown(
                            id=operator_id,  # Utiliser la variable pour être sûr
                            options=[
                                {'label': '>', 'value': '>'},
                                {'label': '<', 'value': '<'},
                                {'label': '>=', 'value': '>='},
                                {'label': '<=', 'value': '<='},
                                {'label': '==', 'value': '=='},
                                {'label': '!=', 'value': '!='}
                            ],  # OPTIONS EN DUR POUR DEBUG
                            placeholder=t.get('placeholder-operator', 'Opérateur'),
                            style={'marginBottom': '10px'},
                            persistence=True,
                            persistence_type='session',
                            clearable=False  # Empêcher la suppression accidentelle
                        ),
                    ], width=2),

                    # Comparaison
                    dbc.Col([
                        html.Label(html.Span(id=f"static-label-comparison-type-{outer_i}-{inner_j}"), 
                                 className="font-weight-bold text-info mb-2"),
                        dcc.Dropdown(
                            id=f'comparison-type-{outer_i}-{inner_j}',
                            options=[
                                {'label': 'Indicateur', 'value': 'indicator'},
                                {'label': 'Valeur', 'value': 'value'}
                            ],  # OPTIONS EN DUR POUR DEBUG
                            value='indicator',
                            clearable=False,
                            style={'marginBottom': '10px'},
                            persistence=True,
                            persistence_type='session'
                        ),
                        
                        # Indicateur 2
                        html.Label(html.Span(id=f"indicator2-label-{outer_i}-{inner_j}"),
                                 className="font-weight-bold text-info mb-2",
                                 style={'display': 'block', 'marginBottom': '10px'}),
                        dcc.Dropdown(
                            id=f'stock2-{outer_i}-{inner_j}',
                            options=[],
                            searchable=True,
                            placeholder=t.get('placeholder-select-stock', 'Sélectionner une action'),
                            style={'marginBottom': '10px', 'display': 'block'},
                            persistence=True,
                            persistence_type='session'
                        ),
                        dcc.Dropdown(
                            id=f'indicator2-type-{outer_i}-{inner_j}',
                            options=[],
                            placeholder=t.get('placeholder-indicator', 'Indicateur'),
                            style={'marginBottom': '10px', 'display': 'block'},
                            persistence=True,
                            persistence_type='session'
                        ),
                        html.Div(id=f'indicator2-params-{outer_i}-{inner_j}', 
                               className="mt-2", 
                               style={'display': 'block'}),
                        
                        # Valeur de comparaison
                        html.Label(html.Span(id=f"value-label-{outer_i}-{inner_j}"),
                                 className="font-weight-bold text-info mb-2",
                                 style={'display': 'none', 'marginBottom': '10px'}),
                        dbc.Input(
                            id=f'comparison-value-{outer_i}-{inner_j}',
                            type="number",
                            placeholder=t.get('placeholder-numeric-value', 'Valeur numérique'),
                            style={**INPUT_STYLE, 'display': 'none'},
                            persistence=True,
                            persistence_type='session'
                        )
                    ], width=4),
                    
                    # Bouton suppression
                    dbc.Col([
                        dbc.Button(
                            "×", 
                            id=f'remove-condition-{outer_i}-{inner_j}',
                            color="danger", 
                            size="sm", 
                            style={'marginTop': '30px'}
                        )
                    ], width=2, className="d-flex justify-content-end")
                ]),
                
                # Paramètres cachés
                html.Div([
                    html.Div([
                        dbc.Input(
                            id=f'indicator1-param-{outer_i}-{inner_j}-{k}',
                            type='number',
                            style={'display': 'none'},
                            persistence=True,
                            persistence_type='session'
                        ) for k in range(3)
                    ], style={'display': 'none'}),
                    html.Div([
                        dbc.Input(
                            id=f'indicator2-param-{outer_i}-{inner_j}-{k}',
                            type='number',
                            style={'display': 'none'},
                            persistence=True,
                            persistence_type='session'
                        ) for k in range(3)
                    ], style={'display': 'none'})
                ], style={'display': 'none'})
            ])
        ], style=CARD_STYLE)
    ], 
    className="mb-3", 
    id=f'condition-block-{outer_i}-{inner_j}',
    style={'display': 'none' if inner_j > 0 else 'block'}
    )
    
def create_static_decision_block_fixed(block_i, available_stocks=None, language='fr'):
    """MODIFIÉ - Ajout du paramètre language avec IDs uniques pour traductions"""
    t = TEXT.get(language, TEXT['fr'])
    all_conditions = []
    for condition_j in range(MAX_CONDITIONS):  # Créer TOUTES les conditions
        condition = create_static_condition_block_complete(block_i, condition_j, available_stocks, language)
        all_conditions.append(condition)
    
    return html.Div([
        html.Div([
            html.H5([
                html.I(className="fas fa-cubes mr-2"),
                html.Span(id=f"decision-block-title-{block_i}", children=t.get('decision-block-title', 'Bloc de Décision')),
                f"  ", f" {block_i + 1} ", f"  ",
                dbc.Button(
                    "×", 
                    id=f'remove-decision-block-{block_i}',
                    color="danger", 
                    size="sm",
                    className="ml-2",
                    style=BUTTON_STYLE
                )
            ], className="text-primary font-weight-bold d-flex align-items-center"),
            html.P(html.Span(id=f"decision-block-description-{block_i}", children=t.get('decision-block-description', 'Définissez les conditions et actions pour ce bloc de décision.')), 
                   className="text-muted small"),
        ], className="mb-3"),

        # Container pour toutes les conditions - TOUTES CRÉÉES
        html.Div(all_conditions, id=f'conditions-container-{block_i}'),

        dbc.Button(
            [html.I(className="fas fa-plus-circle mr-2"), html.Span(id=f"add-condition-text-{block_i}", children=t.get('button-add-condition', 'Ajouter une condition'))], 
            id=f'add-condition-{block_i}', 
            color="secondary", 
            size="sm", 
            className="mb-3",
            style=BUTTON_STYLE
        ),

        dbc.Card([
            dbc.CardHeader(html.Span(id=f"actions-header-{block_i}", children=t.get('actions-to-execute', 'Actions à exécuter')), style=CARD_HEADER_STYLE),
            dbc.CardBody([
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Label(html.Span(id=f'action-label-{block_i}-{stock_idx}'), 
                                     style={"fontWeight": "bold", "display": "none"})
                        ], width=6),
                        dbc.Col([
                            dcc.Dropdown(
                                id=f'stock-action-{block_i}-{stock_idx}',
                                value='Ne rien faire',
                                clearable=False,
                                style={'marginBottom': '5px'}
                            )
                        ], width=6)
                    ], 
                    id=f'action-row-{block_i}-{stock_idx}',
                    className="mb-1",
                    style={'display': 'none'}
                    ) for stock_idx in range(10)
                ], id=f'stock-actions-{block_i}', className="mt-2")
            ], style=CARD_BODY_STYLE)
        ], style=CARD_STYLE),

        html.Hr(style={'borderColor': '#34495e'})
    ], 
    id=f'decision-block-{block_i}', 
    className="mb-4 p-3",
    style={
        'backgroundColor': COLORS['background'], 
        'borderRadius': '8px', 
        'border': f'1px solid {COLORS["header"]}',
        'display': 'none' if block_i > 0 else 'block'
    }
    )

# 3. Fonctions utilitaires pour le résumé
def create_empty_summary(language='fr'):
    """MODIFIÉ - Ajout du paramètre language"""
    t = TEXT.get(language, TEXT['fr'])
    return html.Div([
        html.Div([
            html.I(className="fas fa-hand-pointer fa-3x text-primary mb-3"),
            html.H5(html.Span(id="empty-summary-title"), className="text-primary mb-3"),
            html.P([
                html.Span(id="empty-summary-step1-prefix"),
                html.Strong(html.Span(id="empty-summary-asset-classes")),
                html.Span(id="empty-summary-step1-suffix")
            ], className="text-muted mb-2"),
            html.P(html.Span(id="empty-summary-step2"), className="text-muted mb-2"),
            html.P(html.Span(id="empty-summary-step3"), className="text-muted")
        ], className="text-center")
    ], className="py-5")

def create_detailed_summary(assets_by_type, all_selected_assets, language='fr'):
    """MODIFIÉ - Ajout du paramètre language et IDs pour traduction"""
    t = TEXT.get(language, TEXT['fr'])
    summary_components = []
    
    # En-tête statistique
    total_classes = len(assets_by_type)
    total_assets = len(all_selected_assets)

    # Titre et sous-titre avec IDs pour traduction
    if total_classes > 1:
        portfolio_title_id = "portfolio-cross-asset-title"
        portfolio_subtitle_id = "multi-market-strategy-subtitle"
    else:
        portfolio_title_id = "portfolio-single-asset-title"
        portfolio_subtitle_id = "mono-market-strategy-subtitle"

    header = dbc.Alert([
        dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className="fas fa-trophy mr-2"),
                    html.Span(id=portfolio_title_id)
                ], className="mb-1"),
                html.Small(html.Span(id=portfolio_subtitle_id), className="text-success")
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Badge([
                        html.I(className="fas fa-layer-group mr-1"),
                        f"{total_classes} ",
                        html.Span(id="summary-classes-label")
                    ], color="light", className="mr-2", style={'fontSize': '16px'}),
                    dbc.Badge([
                        html.I(className="fas fa-coins mr-1"),
                        f"{total_assets} ",
                        html.Span(id="summary-assets-label")
                    ], color="light", style={'fontSize': '16px'})
                ], className="text-right")
            ], width=6)
        ])
    ], color="success", className="mb-3")
    summary_components.append(header)
    
    # ... le reste de la fonction avec traductions ...
    color_map = {'actions_cac40': 'primary', 'crypto': 'warning', 'forex': 'info', 'etfs': 'purple'}
    icon_map = {'actions_cac40': 'fas fa-chart-line', 'crypto': 'fab fa-bitcoin', 'forex': 'fas fa-dollar-sign','etfs': 'fas fa-layer-group' }
    
    for asset_class, assets in assets_by_type.items():
        asset_info = asset_types[asset_class]
        type_label = asset_info['label']
        color = color_map.get(asset_class, 'secondary')
        icon = icon_map.get(asset_class, 'fas fa-chart-bar')
        
        percentage = (len(assets) / total_assets) * 100
        
        asset_badges = []
        for asset in assets:
            display_name = ticker_to_name.get(asset, asset)
            badge = dbc.Badge([
                html.I(className="fas fa-dot-circle mr-1", style={'fontSize': '0.7rem'}),
                display_name
            ], 
            color=color, 
            className="mr-2 mb-2", 
            style={'fontSize': '0.95rem', 'padding': '8px 15px', 'fontWeight': 'bold'})
            asset_badges.append(badge)
        
        class_card = dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.I(className=f"{icon} mr-2"),
                        html.Strong(type_label),
                        dbc.Badge(html.Span(id="summary-active-badge"), color="light", className="ml-2", style={'fontSize': '0.7rem'})
                    ], width=8),
                    dbc.Col([
                        html.Div([
                            html.Strong(f"{len(assets)}", className="text-light"),
                            html.Small([" ", html.Span(id="summary-assets-unit")], className="text-light ml-1"),
                            html.Br(),
                            html.Small(f"{percentage:.1f}%", className="text-light")
                        ], className="text-right")
                    ], width=4)
                ])
            ], style={'backgroundColor': f'var(--bs-{color})', 'color': 'white'}),
            dbc.CardBody([
                html.Div(asset_badges, className="d-flex flex-wrap mb-2"),
                html.Hr(className="my-2"),
                dbc.Row([
                    dbc.Col([
                        html.Small([
                            html.I(className="fas fa-chart-pie mr-1"),
                            html.Span(id="summary-weight-label"),
                            f": {percentage:.1f}% ",
                            html.Span(id="summary-portfolio-label")
                        ], className="text-muted")
                    ], width=6),
                    dbc.Col([
                        html.Small([
                            html.I(className="fas fa-layer-group mr-1"),
                            html.Span(id="summary-class-label"),
                            f": {type_label}"
                        ], className="text-muted")
                    ], width=6)
                ])
            ])
        ], className="mb-3", style={
            'border': f'3px solid var(--bs-{color})',
            'borderRadius': '10px',
            'boxShadow': '0 6px 12px rgba(0,0,0,0.15)'
        })
        
        summary_components.append(class_card)
    
    if total_classes >= 2:
        advice_card = dbc.Card([
            dbc.CardBody([
                html.H6([
                    html.I(className="fas fa-brain mr-2 text-info"),
                    html.Span(id="strategic-analysis-title")
                ], className="mb-3"),
                html.P([
                    html.Span(id="strategic-analysis-description"),
                    f" {total_classes} ",
                    html.Span(id="strategic-analysis-classes"),
                    f" {total_assets} ",
                    html.Span(id="strategic-analysis-instruments"),
                    html.Span(id="strategic-analysis-potential")
                ], className="mb-2"),
                html.Ul([
                    html.Li([html.Span(id="strategy-arbitrage")]),
                    html.Li([html.Span(id="strategy-diversification")]),
                    html.Li([html.Span(id="strategy-rotation")]),
                    html.Li([html.Span(id="strategy-cross-asset")])
                ], className="mb-0", style={'fontSize': '0.9rem'})
            ])
        ], color="light", className="mt-3")
        summary_components.append(advice_card)
    
    return html.Div(summary_components)


def create_option_selection_row(index, language='fr'):
    """MODIFIÉ - Ajout du paramètre language"""
    t = TEXT.get(language, TEXT['fr'])
    return dbc.Row([
        # Colonne pour le sous-jacent
        dbc.Col(dcc.Dropdown(
            id={'type': 'option-underlying-selector', 'index': index},
            options=[
                {'label': "AAPL (Apple Inc.)", 'value': 'AAPL'},
                {'label': "GOOGL (Alphabet / Google)", 'value': 'GOOGL'},
                {'label': "SPY (ETF S&P 500)", 'value': 'SPY'},
                {'label': "MSFT (Microsoft Corp.)", 'value': 'MSFT'},
                {'label': "AMZN (Amazon.com Inc.)", 'value': 'AMZN'},
                {'label': "TSLA (Tesla Inc.)", 'value': 'TSLA'},
                {'label': "NVDA (NVIDIA Corp.)", 'value': 'NVDA'},
            ],
            placeholder=t.get('placeholder-underlying', 'Actif...'),
        ), width=3),
        
        # Colonnes pour maturité, strike, et type
        dbc.Col(dcc.Dropdown(
            id={'type': 'option-maturity-selector', 'index': index}, 
            placeholder=t.get('placeholder-maturity', 'Maturité...'), 
            disabled=True
        ), width=3),
        dbc.Col(dcc.Dropdown(
            id={'type': 'option-strike-selector', 'index': index}, 
            placeholder=t.get('placeholder-strike', 'Strike...'), 
            disabled=True
        ), width=2),
        dbc.Col(dcc.Dropdown(
            id={'type': 'option-type-selector', 'index': index},
            options=[
                {'label': t.get('option-call', 'Call 📈'), 'value': 'call'}, 
                {'label': t.get('option-put', 'Put 📉'), 'value': 'put'}
            ],
            placeholder=t.get('placeholder-option-type', 'Type...'), 
            disabled=True
        ), width=2),

        # Bouton de suppression
        dbc.Col(dbc.Button("×", id={'type': 'delete-option-row', 'index': index}, color="danger", outline=True), width=1, className="d-flex align-items-center"),
        
    ], className="mb-3", align="center")

# def get_asset_placeholder(asset_class, language='fr'):
#     """Fonction utilitaire pour obtenir le bon placeholder selon la classe d'actif"""
#     t = TEXT.get(language, TEXT['fr'])
    
#     placeholders = {
#         'actions_cac40': t.get('choose-cac40-stock', 'Choisir une action CAC40'),
#         'crypto': t.get('choose-crypto', 'Choisir une crypto'),
#         'forex': t.get('choose-forex', 'Choisir une paire forex'),
#         'etfs': t.get('choose-etf', 'Choisir un ETF'),
#         'custom_assets': t.get('choose-custom-asset', 'Choisir un actif personnalisé')
#     }
    
#     return placeholders.get(asset_class, t.get('choose-asset', 'Choisir un actif'))

def create_comparison_summary_table(results_dict, language='fr'):
    """Crée un tableau comparatif des métriques avec style premium"""
    t = TEXT.get(language, TEXT['fr'])
    
    if not results_dict:
        return html.Div()
    
    # Métriques à comparer
    metrics_to_compare = [
        ('Capital initial', 'initial-capital-label'),
        ('Capital final', 'final-capital-label'),
        ('Rendement total (%)', 'total-return-label'),
        ('Rendement annualisé (%)', 'annualized-return-label'),
        ('Drawdown maximum (%)', 'max-drawdown-label'),
        ('Ratio de Sharpe', 'sharpe-ratio-label'),
        ('Nombre de trades', 'trades-count-label'),
        ('Pourcentage de trades gagnants (%)', 'winning-trades-pct-label'),
        ('Profit moyen par trade', 'avg-profit-per-trade-label'),
        ('Profit factor', 'profit-factor-label')
    ]
    
    # Construire les lignes du tableau
    table_rows = []
    
    # En-tête avec style premium
    header = html.Tr([
        html.Th(t.get('metric-label', 'Métrique'), 
               style={
                   'padding': '16px',
                   'backgroundColor': '#e2e8f0',
                   'color': '#0f172a',
                   'fontWeight': '700',
                   'fontSize': '0.75rem',
                   'textTransform': 'uppercase',
                   'letterSpacing': '0.1em',
                   'borderBottom': '2px solid rgba(148, 163, 184, 0.2)',
                   'fontFamily': 'var(--font-primary)'
               }),
        *[html.Th(name, 
                 style={
                     'padding': '16px',
                     'backgroundColor': '#e2e8f0',
                     'color': '#0f172a',
                     'fontWeight': '700',
                     'fontSize': '0.75rem',
                     'textTransform': 'uppercase',
                     'letterSpacing': '0.1em',
                     'textAlign': 'center',
                     'borderBottom': '2px solid rgba(148, 163, 184, 0.2)',
                     'fontFamily': 'var(--font-primary)'
                 }) 
          for name in results_dict.keys()]
    ])
    table_rows.append(header)
    
    # Lignes de métriques avec style premium
    for metric_key, label_id in metrics_to_compare:
        row_cells = [
            html.Td(
                html.Span(id=label_id, children=metric_key), 
                style={
                    'padding': '12px 16px',
                    'fontWeight': '600',
                    'color': '#0f172a',
                    'backgroundColor': '#fafbfc',
                    'borderBottom': '1px solid rgba(148, 163, 184, 0.1)',
                    'fontFamily': 'var(--font-primary)'
                }
            )
        ]
        
        # Trouver la meilleure valeur pour colorer
        values = [results['metrics'].get(metric_key, 0) for results in results_dict.values()]
        
        # Déterminer si plus grand = mieux (sauf pour drawdown)
        is_higher_better = metric_key != 'Drawdown maximum (%)'
        best_value = max(values) if is_higher_better else min(values)
        
        for strategy_name, results in results_dict.items():
            value = results['metrics'].get(metric_key, 0)
            
            # Formatage selon le type
            if isinstance(value, (int, float)):
                if 'Capital' in metric_key or 'Profit moyen' in metric_key:
                    formatted_value = f"{value:,.2f} €"
                elif metric_key == 'Nombre de trades':
                    formatted_value = f"{int(value)}"
                else:
                    formatted_value = f"{value:.2f}"
            else:
                formatted_value = str(value)
            
            # Colorer si c'est la meilleure valeur
            cell_style = {
                'padding': '12px 16px',
                'textAlign': 'center',
                'color': '#0f172a',
                'borderBottom': '1px solid rgba(148, 163, 184, 0.1)',
                'fontFamily': 'var(--font-primary)',
                'transition': 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
            }
            
            if value == best_value and len(values) > 1:
                cell_style.update({
                    'backgroundColor': 'rgba(0, 188, 212, 0.1)',
                    'fontWeight': '700',
                    'color': '#00BCD4',
                    'borderLeft': '3px solid #00BCD4'
                })
            
            row_cells.append(html.Td(formatted_value, style=cell_style))
        
        table_rows.append(html.Tr(row_cells))
    
    # Retourner le tableau avec style premium
    return html.Div([
        html.Table(
            html.Tbody(table_rows),
            style={
                'width': '100%',
                'borderCollapse': 'collapse',
                'backgroundColor': '#ffffff',
                'borderRadius': '12px',
                'overflow': 'hidden',
                'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.12)',
                'fontFamily': 'var(--font-primary)'
            }
        )
    ], style={
        'marginTop': '20px',
        'backgroundColor': 'rgba(255, 255, 255, 0.95)',
        'backdropFilter': 'blur(16px)',
        'border': '1px solid rgba(203, 213, 225, 0.5)',
        'borderRadius': '12px',
        'padding': '4px',
        'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.12)'
    })


def create_comparison_equity_chart(results_dict, language='fr'):
    """Crée un graphique comparatif des courbes d'équité"""
    t = TEXT.get(language, TEXT['fr'])
    
    fig = go.Figure()
    
    colors = ['#3498db', '#e74c3c', '#2ecc71']
    
    for idx, (strategy_name, results) in enumerate(results_dict.items()):
        equity_df = results['equity_df']
        
        fig.add_trace(go.Scatter(
            x=equity_df.index,
            y=equity_df['total_equity'],
            mode='lines',
            name=strategy_name,
            line=dict(color=colors[idx % len(colors)], width=2),
            hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Équité: %{y:,.2f}€<extra></extra>'
        ))
    
    fig.update_layout(
        title=t.get('equity-comparison-title', 'Comparaison des Courbes d\'Équité'),
        xaxis_title=t.get('date-label', 'Date'),
        yaxis_title=t.get('equity-label', 'Équité (€)'),
        template='plotly_dark',
        height=500,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def create_comparison_returns_distribution(results_dict, language='fr'):
    """Crée un histogramme comparant les distributions de rendements quotidiens"""
    t = TEXT.get(language, TEXT['fr'])
    
    fig = go.Figure()
    
    colors = ['#3498db', '#e74c3c', '#2ecc71']
    
    for idx, (strategy_name, results) in enumerate(results_dict.items()):
        equity_df = results['equity_df']
        daily_returns = equity_df['total_equity'].pct_change().dropna() * 100
        
        fig.add_trace(go.Histogram(
            x=daily_returns,
            name=strategy_name,
            opacity=0.7,
            marker_color=colors[idx % len(colors)],
            nbinsx=50
        ))
    
    fig.update_layout(
        title=t.get('returns-distribution-comparison', 'Distribution des Rendements Quotidiens'),
        xaxis_title=t.get('daily-return-pct', 'Rendement Quotidien (%)'),
        yaxis_title=t.get('frequency-label', 'Fréquence'),
        template='plotly_dark',
        height=400,
        barmode='overlay',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def calculate_strategy_risk_score(strategy_data, filename=None):
    """Calcule un score de risque basé sur le nom du fichier ou les paramètres"""
    # Priorité au nom du fichier
    if filename:
        filename_lower = filename.lower()
        if 'high' in filename_lower or 'risky' in filename_lower or 'risque' in filename_lower:
            return 'risky'
        elif 'medium' in filename_lower or 'moderate' in filename_lower or 'modere' in filename_lower:
            return 'moderate'
        elif 'safe' in filename_lower or 'low' in filename_lower or 'sur' in filename_lower:
            return 'safe'
    
    # Fallback : calcul basé sur les paramètres
    stop_loss = strategy_data.get('stop_loss_pct', 5)
    allocation = strategy_data.get('allocation_pct', 10)
    risk_score = (allocation / 10) * (10 / max(stop_loss, 1))
    
    if risk_score > 5:
        return 'risky'
    elif risk_score > 2:
        return 'moderate'
    else:
        return 'safe'

import hashlib

def generate_unique_key(strategy_path, context=''):
    """Génère un ID unique basé sur le hash du path"""
    path_hash = hashlib.md5(strategy_path.encode()).hexdigest()[:12]
    return f"{context}_{path_hash}" if context else path_hash

def create_strategy_card_community_v2(strategy_path, strategy_name, votes, comments_count, language='fr', context=''):
    """Carte de stratégie avec IDs optimisés"""
    t = TEXT.get(language, TEXT['fr'])
    
    try:
        with open(strategy_path, 'r', encoding='utf-8') as f:
            strategy_data = json.load(f)
        
        created_at = strategy_data.get('created_at', 'Date inconnue')
        capital = strategy_data.get('initial_capital', 0)
        allocation = strategy_data.get('allocation_pct', 0)
        nb_blocks = len(strategy_data.get('decision_blocks', []))
        stocks = strategy_data.get('selected_stocks', [])
        
        filename = os.path.basename(strategy_path)
        risk_level = calculate_strategy_risk_score(strategy_data, filename=filename)
        risk_colors = {'risky': 'danger', 'moderate': 'warning', 'safe': 'success'}
        
        # ID unique
        unique_id = generate_unique_key(strategy_path, context)
        
        return dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H5(strategy_name, className="mb-2", 
                               style={'color': '#ffffff', 'fontWeight': 'bold'}),
                        html.Small(f"Créée le {created_at}", 
                                 style={'color': '#e2e8f0'}, className="d-block mb-2"),
                        html.Div([
                            dbc.Badge(f"{len(stocks)} actifs", color="info", className="mr-1"),
                            dbc.Badge(f"{nb_blocks} blocs", color="primary", className="mr-1"),
                            dbc.Badge(risk_level.upper(), color=risk_colors[risk_level])
                        ])
                    ], width=7),
                    
                    dbc.Col([
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    html.Span("▲", style={'fontSize': '1.8rem', 'color': '#ffffff'}),
                                    id={'type': 'upvote-btn', 'index': unique_id},
                                    color="success", size="sm",
                                    style={'width': '100%', 'padding': '4px'},
                                    n_clicks=0
                                )
                            ], width=5),
                            
                            dbc.Col([
                                html.Div(
                                    html.Span(str(votes), 
                                            id={'type': 'vote-count', 'index': unique_id},
                                            style={'color': '#ffffff'}),
                                    style={'textAlign': 'center', 'fontSize': '1.3rem', 
                                           'fontWeight': 'bold', 'lineHeight': '32px'}
                                )
                            ], width=2),
                            
                            dbc.Col([
                                dbc.Button(
                                    html.Span("▼", style={'fontSize': '1.8rem', 'color': '#ffffff'}),
                                    id={'type': 'downvote-btn', 'index': unique_id},
                                    color="danger", size="sm",
                                    style={'width': '100%', 'padding': '4px'},
                                    n_clicks=0
                                )
                            ], width=5)
                        ], className="mb-2 g-1"),
                        
                        dbc.Button([
                            html.I(className="fas fa-comment mr-2", style={'color': '#ffffff'}),
                            html.Span(f"{comments_count} commentaire{'s' if comments_count != 1 else ''}", 
                                    style={'color': '#ffffff'})
                        ],
                        id={'type': 'comment-btn', 'index': unique_id},
                        color="info", size="sm",
                        style={'width': '100%', 'padding': '8px'},
                        n_clicks=0
                        ),
                    ], width=5)
                ], align="center"),
                
                html.Hr(style={'borderColor': '#6c757d', 'margin': '15px 0'}),
                
                html.Div([
                    html.Small([
                        html.Strong("Capital: ", style={'color': '#ffffff'}),
                        html.Span(f"{capital:,}€", style={'color': '#ffffff'}),
                        html.Span(" | ", style={'color': '#adb5bd'}),
                        html.Strong("Allocation: ", style={'color': '#ffffff'}),
                        html.Span(f"{allocation}%", style={'color': '#ffffff'})
                    ], style={'color': '#ffffff'})
                ]),
                
                html.Div([
                    html.Hr(id={'type': 'comment-divider', 'index': unique_id},
                           style={'borderColor': '#6c757d', 'display': 'none'}),
                    dbc.Textarea(
                        id={'type': 'comment-input', 'index': unique_id},
                        placeholder="Écrivez votre commentaire...",
                        style={'display': 'none', 'backgroundColor': '#495057', 
                               'color': '#ffffff', 'border': '1px solid #6c757d'},
                        rows=3
                    ),
                    dbc.Button([html.I(className="fas fa-paper-plane mr-2"), "Publier"],
                              id={'type': 'submit-comment', 'index': unique_id},
                              color="primary", size="sm",
                              style={'display': 'none'},
                              n_clicks=0
                    ),
                    html.Div(id={'type': 'comments-display', 'index': unique_id})
                ])
            ], style={'backgroundColor': '#2c3e50', 'padding': '20px', 'borderRadius': '8px'})
        ], style={
            'backgroundColor': '#2c3e50',
            'border': '2px solid #495057',
            'borderRadius': '8px',
            'marginBottom': '20px',
            'boxShadow': '0 4px 8px rgba(0,0,0,0.3)'
        })
        
    except Exception as e:
        return dbc.Alert(f"Erreur: {str(e)}", color="danger")
    

def create_forecast_display(forecasts_data, asset, language='fr'):
    """Affiche les prévisions pour un actif"""
    t = TEXT.get(language, TEXT['fr'])
    
    if not forecasts_data or asset not in forecasts_data:
        return dbc.Alert("Aucune prévision disponible pour cet actif", color="info")
    
    asset_forecasts = forecasts_data[asset]
    
    # Calculer les statistiques
    total = len(asset_forecasts)
    up_count = sum(1 for f in asset_forecasts if f['direction'] == 'up')
    down_count = sum(1 for f in asset_forecasts if f['direction'] == 'down')
    stable_count = sum(1 for f in asset_forecasts if f['direction'] == 'stable')
    
    up_pct = (up_count / total * 100) if total > 0 else 0
    down_pct = (down_count / total * 100) if total > 0 else 0
    stable_pct = (stable_count / total * 100) if total > 0 else 0
    
    avg_confidence = sum(f['confidence'] for f in asset_forecasts) / total if total > 0 else 0
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H5(f"📊 {total} prévisions", className="text-center"),
                html.Small(f"Confiance moyenne: {avg_confidence:.0f}%", className="text-muted d-block text-center")
            ], width=12)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H2(f"{up_pct:.0f}%", className="text-success text-center mb-0"),
                        html.P("📈 Hausse", className="text-center mb-0")
                    ])
                ], color="light")
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H2(f"{stable_pct:.0f}%", className="text-warning text-center mb-0"),
                        html.P("➡️ Stable", className="text-center mb-0")
                    ])
                ], color="light")
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H2(f"{down_pct:.0f}%", className="text-danger text-center mb-0"),
                        html.P("📉 Baisse", className="text-center mb-0")
                    ])
                ], color="light")
            ], width=4)
        ]),
        
        html.Hr(),
        
        html.H6("Prévisions récentes:", className="mt-4 mb-3"),
        html.Div([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        dbc.Badge(f"{'📈 Hausse' if f['direction'] == 'up' else '📉 Baisse' if f['direction'] == 'down' else '➡️ Stable'}", 
                                 color='success' if f['direction'] == 'up' else 'danger' if f['direction'] == 'down' else 'warning'),
                        html.Span(f" Horizon: {f['horizon']}", className="ml-2"),
                        html.Span(f" | Confiance: {f['confidence']}%", className="ml-2"),
                        html.Span(f" | {f['timestamp']}", className="ml-2 text-muted")
                    ])
                ])
            ], className="mb-2")
            for f in sorted(asset_forecasts, key=lambda x: x['timestamp'], reverse=True)[:10]
        ])
    ])