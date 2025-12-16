import os
import sys
import pandas as pd
import json
# from _dash.chatbot_claude import create_chatbot_layout, register_chatbot_callbacks
from _dash.chatbot_groq import create_chatbot_layout, register_chatbot_callbacks

import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, ALL, MATCH
from dash.exceptions import PreventUpdate

sys.path.append(os.path.abspath(".."))
from utility.constants import *
from .dash_utils import *
from backtester import *
from .sidebar import create_sidebar

# Layout de l'application
def dash_layout():
    return html.Div([
        # Background Animation (From Site)
        html.Div([
            html.Div(className="blob blob-1"),
            html.Div(className="blob blob-2")
        ], className="background-blobs"),

        dcc.Location(id="url", refresh=False),
        dcc.Store(id='theme-store', storage_type='local'),
        dcc.Store(id='backtest-results-store', storage_type='session'),
        dcc.Store(id='context-store', storage_type='session'), # Stores {'type': 'client'|'folder', 'id': '...'}
        dcc.Store(id='refresh-signal', storage_type='memory'), # Signals updates for sidebars/lists
        
        # --- MOBILE VISUALS ---
        html.Div(id="mobile-overlay"),
        html.Button(
            html.I(className="fas fa-bars fa-lg"),
            id="mobile-sidebar-toggle",
            className="btn btn-light shadow-sm"
        ),
        
        # --- MODALS ---
        dbc.Modal([
            dbc.ModalHeader("Nouveau Client"),
            dbc.ModalBody([
                dbc.Input(id="new-client-name", placeholder="Nom du client", className="mb-2"),
                dbc.Input(id="new-client-email", placeholder="Email (optionnel)", className="mb-2"),
                dbc.Textarea(id="new-client-notes", placeholder="Notes", className="mb-2"),
            ]),
            dbc.ModalFooter([
                dbc.Button("Annuler", id="cancel-new-client", className="ml-auto"),
                dbc.Button("Créer", id="confirm-new-client", color="primary", className="ml-2"),
            ]),
        ], id="modal-new-client"),

        dbc.Modal([
            dbc.ModalHeader("Nouveau Dossier"),
            dbc.ModalBody([
                dbc.Input(id="new-folder-name", placeholder="Nom du dossier"),
            ]),
            dbc.ModalFooter([
                dbc.Button("Annuler", id="cancel-new-folder", className="ml-auto"),
                dbc.Button("Créer", id="confirm-new-folder", color="primary", className="ml-2"),
            ]),
        ], id="modal-new-folder"),
        
        dcc.Download(id="download-results-pdf"),
        html.Div(id='theme-wrapper', children=[
            create_sidebar(),
            html.Div(className="content-wrapper", children=[
                dbc.Container([
                    html.Div([
        html.H5(html.Span(id="wizard-title"), className="text-center text-info mb-3"),
        dbc.Progress(
            id="wizard-progress",
            value=25, # La nouvelle première étape correspond à 25%
            striped=True,
            animated=True,
            color="info",
            className="mb-3",
            style={'height': '8px'}
        ),
        html.Div([
            dbc.Badge(html.Span(id="wizard-step1-badge"), id="step1-badge", color="info", className="mr-2"),
            dbc.Badge(html.Span(id="wizard-step2-badge"), id="step2-badge", color="light", className="mr-2"),
            # Le badge de l'étape 3 est supprimé
            dbc.Badge(html.Span(id="wizard-step3-badge"), id="step3-badge", color="light", className="mr-2"), 
            dbc.Badge(html.Span(id="wizard-step4-badge"), id="step4-badge", color="light", className="mr-2"),
            dbc.Badge(html.Span(id="wizard-step5-badge"), id="step5-badge", color="light") 
            # Le badge de l'étape 5 est supprimé
        ], className="text-center mb-4")
    ], id="wizard-progress-container", style={'display': 'block'}),
    # 
    
    # Container pour le mode Wizard
    html.Div([
        # Étape 1 : Template/Stratégies Prédéfinies
        html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-magic mr-2"),
                    html.Span(id="wizard-step1-title")
                ], style=CARD_HEADER_STYLE),
                dbc.CardBody([
                    html.P(html.Span(id="wizard-step1-description"), 
                           className="text-muted mb-4"),
                    
                    dbc.Row([
                        # dbc.Col([
                        #     html.Div([
                        #         dbc.Card([
                        #             dbc.CardBody([
                        #                 html.I(className="fas fa-download fa-3x text-info mb-3"),
                        #                 html.H5("Utiliser un Template", className="text-info"),
                        #                 html.P("Stratégies prêtes à utiliser", className="text-muted small"),
                        #             ])
                        #         ], className="text-center h-100")
                        #     ], 
                        #     id="template-choice-card",
                        #     className="wizard-choice-card",
                        #     style={'cursor': 'pointer', 'border': '2px solid transparent'},
                        #     n_clicks=0)
                        # ], width=12, md=6, className="mb-3 mb-md-0"),
                        
                        dbc.Col([
                            html.Div([
                                dbc.Card([
                                    dbc.CardBody([
                                        html.I(className="fas fa-cogs fa-3x text-success mb-3"),
                                        html.H5(html.Span(id="manual-creation-card-title"), className="text-success"),
                                        html.P(html.Span(id="manual-creation-card-description"), className="text-muted small"),
                                    ])
                                ], className="text-center h-100")
                            ],
                            id="manual-choice-card",
                            className="wizard-choice-card", 
                            style={'cursor': 'pointer', 'border': '2px solid transparent'},
                            n_clicks=0)
                        ], width=12, md=6)
                    ], className="mb-4"),
                    
                    # Section template
                    html.Div([
                        html.Hr(),
                        html.Label(html.Span(id="template-selection-label"), className="font-weight-bold mb-2"),
                        dcc.Dropdown(
                            id="wizard-predefined-strategy-select",
                            placeholder="", # Sera rempli par le callback
                            clearable=True,
                            style={'marginBottom': '15px'}
                        ),
                        html.Div(id="wizard-predefined-strategy-description"),
                        dbc.Button(
                            [html.I(className="fas fa-download mr-2"), html.Span(id="apply-template-button-text")],
                            id="wizard-apply-predefined-strategy",
                            color="info",
                            disabled=True,
                            className="mt-2"
                        )
                    ], id="template-section", style={'display': 'none'}),
                    
                    html.Div([
                        dbc.Button(
                            [html.I(className="fas fa-arrow-right mr-2"), html.Span(id="button-next-assets")],
                            id="step1-next",
                            color="primary",
                            disabled=True,
                            className="float-right"
                        )
                    ], className="mt-4")
                ])
            ])
        ], id="wizard-step-1", style={'display': 'block'}),
        
            html.Div([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-layer-group mr-2"), html.Span(id="wizard-step2-title")], style=CARD_HEADER_STYLE),
                    dbc.CardBody([
                        # --- Uniquement la sélection des actifs ---
                        html.P(html.Span(id="wizard-step2-description"), className="text-muted mb-4"),
                        html.Label(html.Span(id="asset-classes-label"), className="font-weight-bold text-info mb-2"),
                        dcc.Dropdown(
                            id="wizard-asset-class-selector",
                            options=[{"label": html.Div([html.I(className="fas fa-chart-line mr-2"), f"{asset_info['label']} ({len(asset_info['assets'])} actifs)"]), "value": asset_type} for asset_type, asset_info in asset_types.items()],
                            placeholder="", # Sera rempli par le callback
                            multi=True,
                            className="mb-4"
                        ),
                        html.Div(id="wizard-asset-sections-container"),
                        html.Div(id="wizard-selected-assets-summary"),
                        dcc.Store(id='wizard-selected-stocks-store'),
                        
                        # --- Boutons de navigation ---
                        html.Div([
                            dbc.Button([html.I(className="fas fa-arrow-left mr-2"), html.Span(id="button-previous-step2")], id="step2-prev", color="secondary", className="float-left"),
                            dbc.Button([html.I(className="fas fa-arrow-right mr-2"), html.Span(id="button-next-scenario")], id="step2-next", color="primary", disabled=True, className="float-right")
                        ], className="mt-4")
                    ])
                ])
            ], id="wizard-step-2", style={'display': 'none'}),

            # Étape 3 : Scénario de Trading (votre code, nettoyé et renuméroté)
            html.Div([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-tasks mr-2"), html.Span(id="wizard-step3-title")], style=CARD_HEADER_STYLE),
                    dbc.CardBody([
                        html.P(html.Span(id="wizard-step3-description"), className="text-muted mb-4"),
                        html.Label(html.Span(id="scenario-action-label"), className="font-weight-bold text-info"),
                        dcc.Dropdown(
                            id='simple-action-dropdown', 
                            options=[],  # Les options seront remplies par le callback
                            placeholder="", 
                            clearable=False, 
                            className="mb-4"
                        ),
                        html.Label(html.Span(id="scenario-trigger-label"), className="font-weight-bold text-info"),
                        dcc.Dropdown(
                            id='simple-trigger-dropdown',
                            options=[],  # Les options seront remplies par le callback
                            placeholder="",
                            clearable=False,
                            className="mb-4"
                        ),
                        html.Div([
                            dbc.Button([html.I(className="fas fa-arrow-left mr-2"), html.Span(id="button-previous-step3")], id="step3-prev", color="secondary", className="float-left"),
                            dbc.Button([html.I(className="fas fa-arrow-right mr-2"), html.Span(id="button-next-launch")], id="step3-next", color="primary", disabled=True, className="float-right")
                        ], className="mt-4")
                    ])
                ])
            ], id="wizard-step-3", style={'display': 'none'}),

            # Étape 4 : Lancement (votre code, nettoyé et renuméroté)
            html.Div([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-rocket mr-2"), html.Span(id="wizard-step4-title")], style=CARD_HEADER_STYLE),
                    dbc.CardBody([
                        html.H5(html.Span(id="summary-ready-title"), className="text-success text-center mb-4"),
                        dbc.Card(dbc.CardBody(html.Div(id="strategy-summary")), color="light", className="mb-4"),
                        dbc.Row([
                            dbc.Col(dbc.Button([html.I(className="fas fa-save mr-2"), html.Span(id="button-save")], id="wizard-save-strategy", color="success", size="lg", className="w-100 mb-2"), width=12, md=6, className="mb-2 mb-md-0"),
                            dbc.Col(dbc.Button([html.I(className="fas fa-play mr-2"), html.Span(id="button-launch-backtest")], id="run-backtest-from-wizard", color="primary", size="lg", className="w-100 mb-2"), width=12, md=6)
                        ]),
                        html.Div(id="wizard-save-confirmation", className="mt-2 text-center"),
                        html.Div([
                            dbc.Button([html.I(className="fas fa-arrow-left mr-2"), html.Span(id="button-previous-step4")], id="step4-prev", color="secondary", className="float-left"),
                            dbc.Button([html.I(className="fas fa-redo mr-2"), html.Span(id="button-restart-wizard")], id="restart-wizard", color="info", outline=True, className="float-right")
                        ], className="mt-4")
                    ])
                ])
            ], id="wizard-step-4", style={'display': 'none'}),

            # Étape 5 : Résultats (Layout final)
            html.Div([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fas fa-chart-bar mr-2"), html.Span(id="wizard-step5-title")], style=CARD_HEADER_STYLE),
                    dbc.CardBody([
                        html.Div(id="wizard-results-placeholder"),
                        html.Div([
                            dbc.Button([html.I(className="fas fa-arrow-left mr-2"), html.Span(id="button-previous-step5")], id="step5-prev", color="secondary", className="float-left"),
                            dbc.Button([html.I(className="fas fa-redo mr-2"), html.Span(id="button-new-strategy")], id="restart-wizard-2", color="info", outline=True, className="float-right") # ID unique pour ce bouton
                        ], className="mt-4")
                    ])
                ])
            ], id="wizard-step-5", style={'display': 'none'})

        ], id="wizard-container", style={'display': 'block'}),

    # Mode avancé : conteneur affiché quand le switch est activé
    html.Div(id="advanced-container", children=[
        
        # === DEBUT DE LA SECTION CORRIGÉE ===
        # L'intégralité du composant dbc.Tabs est maintenant ici
        dbc.Tabs(id="main-tabs", active_tab="tab-creation", className="hidden-tabs", children=[
            # Onglet Création de stratégie
            dbc.Tab([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-info-circle mr-2"),
                                html.Span(id="card-title-general-info")
                            ], style=CARD_HEADER_STYLE),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Label(html.Span(id="label-strategy-name"), html_for="strategy-name"),
                                    dbc.Input(
                                        id="strategy-name", 
                                        value="Test",  # VALEUR PAR DÉFAUT AJOUTÉE
                                        placeholder="", # Sera rempli par le callback
                                        type="text", 
                                        className="mb-2",
                                        style=INPUT_STYLE
                                    ),
                                    dbc.FormText(html.Span(id="formtext-strategy-name")),
                                ], className="mb-3"),
                                
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label(html.Span(id="label-initial-capital")),
                                        dbc.Input(id="initial-capital", type="number", value=100000, style=INPUT_STYLE)
                                    ], width=12, md=4, className="mb-2 mb-md-0"),
                                    dbc.Col([
                                        dbc.Label(html.Span(id="label-allocation")),
                                        dbc.Input(id="allocation", type="number", value=10, style=INPUT_STYLE)
                                    ], width=12, md=4, className="mb-2 mb-md-0"),
                                    dbc.Col([
                                        dbc.Label(html.Span(id="label-transaction-cost")),
                                        dbc.Input(id="transaction-cost", type="number", value=1, style=INPUT_STYLE)
                                    ], width=12, md=4),
                                ]),
                            ], style=CARD_BODY_STYLE)
                        ], style=CARD_STYLE),
                        
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-shield-alt mr-2"),
                                html.Span(id="card-title-risk-management")
                            ], style=CARD_HEADER_STYLE),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label(html.Span(id="label-stop-loss")),
                                        dbc.Input(id="stop-loss", type="number", value=5, step=0.1, style=INPUT_STYLE),
                                    ], width=12, md=6, className="mb-2 mb-md-0"),
                                    dbc.Col([
                                        dbc.Label(html.Span(id="label-take-profit")),
                                        dbc.Input(id="take-profit", type="number", value=10, step=0.1, style=INPUT_STYLE),
                                    ], width=12, md=6),
                                ]),
                            ], style=CARD_BODY_STYLE)
                        ], style=CARD_STYLE),
                    ], width=4),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-layer-group mr-2"),
                                html.Span(id="card-title-assets")
                            ], style=CARD_HEADER_STYLE),
                            dbc.CardBody([
                                dbc.Card([
                                    dbc.CardHeader([
                                        html.I(className="fas fa-tags mr-2"),
                                        html.Span(id="asset-class-selection-title")
                                    ], style={
                                        'backgroundColor': '#2c3e50',
                                        'color': 'white',
                                        'fontWeight': 'bold'
                                    }),
                                    dbc.CardBody([
                                        dbc.Row([
                                            dbc.Col([
                                                html.Label(html.Span(id="asset-classes-description"), 
                                                        className="font-weight-bold text-info mb-3"),
                                                dcc.Dropdown(
                                                    id="asset-class-selector",
                                                    options=[
                                                        {
                                                            "label": html.Div([
                                                                html.I(className=asset_info.get('icon', 'fas fa-chart-line')), # Ajout d'une icône par défaut
                                                                f" {asset_info['label']} ({len(asset_info['assets'])} actifs)"
                                                            ]), 
                                                            "value": asset_type
                                                        } 
                                                        for asset_type, asset_info in asset_types.items()
                                                    ] + [{'label': html.Div([html.I(className="fas fa-database mr-2"), html.Span(id="my-imported-assets-label")]), 'value': 'custom_assets'}],
                                                    placeholder="", # Sera rempli par le callback
                                                    multi=True,
                                                    searchable=False,
                                                    clearable=True,
                                                    style={
                                                        'fontSize': '16px',
                                                        'fontWeight': 'bold'
                                                    }
                                                ),
                                                html.Small([
                                                    html.I(className="fas fa-info-circle mr-1"),
                                                    html.Span(id="asset-classes-helper")
                                                ], className="text-muted mt-2 d-block")
                                            ], width=8),
                                            dbc.Col([
                                                html.Div([
                                                    html.H6(html.Span(id="available-classes-title"), className="text-muted mb-2"),
                                                    html.Div([
                                                        dbc.Badge([
                                                            html.I(className="fas fa-chart-line mr-1"),
                                                            html.Span(id="badge-stocks")
                                                        ], color="primary", className="mr-1 mb-1"),
                                                        dbc.Badge([
                                                            html.I(className="fab fa-bitcoin mr-1"),
                                                            html.Span(id="badge-crypto")
                                                        ], color="warning", className="mr-1 mb-1"),
                                                        dbc.Badge([
                                                            html.I(className="fas fa-dollar-sign mr-1"),
                                                            html.Span(id="badge-forex")
                                                        ], color="success", className="mr-1 mb-1"),
                                                        dbc.Badge([
                                                            html.I(className="fas fa-exchange-alt mr-1"),
                                                            html.Span(id="badge-etf")
                                                        ], color="purple", className="mr-1 mb-1")
                                                    ])
                                                ], className="p-3", style={
                                                    'backgroundColor': COLORS['background'],
                                                    'borderRadius': '8px',
                                                    'border': f'1px solid {COLORS["accent"]}'
                                                })
                                            ], width=4)
                                        ])
                                    ])
                                ], className="mb-4", style={
                                    'border': '2px solid #2c3e50',
                                    'borderRadius': '10px'
                                }),
                                
                                html.Div([
                                    html.H5([
                                        html.I(className="fas fa-arrow-down mr-2"),
                                        html.Span(id="specific-assets-selection-title")
                                    ], className="text-center text-muted mb-3"),
                                    html.Hr(style={'borderColor': COLORS['accent'], 'borderWidth': '2px'})
                                ], id="sections-title", style={'display': 'none'}),
                                
                                html.Div(id="asset-sections-container", children=[
                                    html.Div([
                                        html.I(className="fas fa-hand-pointer fa-3x text-muted mb-3"),
                                        html.H5(html.Span(id="select-asset-classes-first"), className="text-muted"),
                                        html.P(html.Span(id="asset-sections-appear-helper"), 
                                            className="text-muted")
                                    ], className="text-center py-5", style={
                                        'border': f'3px dashed {COLORS["accent"]}',
                                        'borderRadius': '15px',
                                        'backgroundColor': COLORS['background']
                                    })
                                ]),
                            html.Div(id="selected-assets-summary", style={'display': 'none'})    
                            ], style=CARD_BODY_STYLE)
                        ], style=CARD_STYLE),
                        
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-calendar-alt mr-2"),
                                html.Span(id="card-title-analysis-period")
                            ], style=CARD_HEADER_STYLE),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label(html.Span(id="strategy-period-label")),
                                        dcc.DatePickerRange(
                                            id='date-picker-range',
                                            start_date='2024-01-01',
                                            end_date='2025-01-01',
                                            display_format='YYYY-MM-DD',
                                            month_format='MMMM YYYY',
                                            with_portal=True,
                                            clearable=True,
                                            updatemode='singledate',
                                            style={
                                                'width': '100%',
                                                'backgroundColor': COLORS['dropdown_bg'],
                                                'color': COLORS['dropdown_text'],
                                                'border': f'1px solid {COLORS["header"]}'
                                            }
                                        ),
                                    ], width=6),
                                ]),
                                html.Div(id='output-date-range', className="mt-3")
                            ], style=CARD_BODY_STYLE)
                        ], style=CARD_STYLE),
                        
                        dcc.Store(id='selected-stocks-store'),
                        dcc.Store(id='wizard-step-store', data=1),
                        dcc.Store(id='wizard-choice-store'),
                    ], width=8),
                ]),
                
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-cubes mr-2"),
                        html.Span(id="card-title-decision-blocks")
                    ], style=CARD_HEADER_STYLE),
                    dbc.CardBody([
                        html.P([
                            html.I(className="fas fa-info-circle mr-2 text-info"),
                            html.Span(id="decision-blocks-description")
                        ], className="alert alert-info"),
                        
                        html.Div([
                            create_static_decision_block_fixed(i, language='fr') for i in range(MAX_BLOCKS)
                        ], id='all-decision-blocks'),
                        
                        dbc.Button(
                            [html.I(className="fas fa-plus-circle mr-2"), html.Span(id="button-add-block")], 
                            id="add-decision-block-static", 
                            color="primary", 
                            className="mb-4",
                            style=BUTTON_STYLE
                        ),
                        
                        dcc.Store(id='visible-blocks-store', data=[0]),
                        dcc.Store(id='visible-conditions-store', data={'0': [0]}),
                    ], style=CARD_BODY_STYLE)
                ], style=CARD_STYLE),
                
                dbc.Button(
                    [html.I(className="fas fa-save mr-2"), html.Span(id="save-strategy-button-text")], 
                    id="save-strategy", 
                    color="success", 
                    className="mt-3 w-100",
                    style={**BUTTON_STYLE, 'padding': '12px'}
                ),
                html.Div(id="save-confirmation", className="mt-2"),

                # dbc.Button(
                #     [html.I(className="fas fa-play mr-2"), "Lancer le backtest"],
                #     id="run-backtest",
                #     color="primary",
                #     className="mt-2 w-100",
                #     style={'display': 'none'},  # Caché par défaut
                #     disabled=True
                # ),

            ], label="Création de stratégie", id="tab-creation", tab_style={"marginLeft": "0px"}, tab_id="tab-creation"),

            # Onglet Résultats
# Onglet Résultats
            dbc.Tab([
                html.H2([
                    html.I(className="fas fa-chart-bar mr-2"),
                    html.Span(id="backtest-results-title")
                ], className="text-center my-4 text-light"),
                
                # Message informatif simple
                html.Div([
                    html.P([
                        html.Span(id="backtest-results-placeholder-text"),
                        html.Br(),
                        html.Span(id="backtest-results-instruction")
                    ], className="text-center", style={'color': '#0f172a', 'fontSize': '1.1rem'})
                ], id="backtest-placeholder-info", className="text-center mb-3"),
                
                # Card avec logo en attente
                html.Div(id="visualization-placeholder", children=[
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Img(
                                    src='/assets/logo.png',
                                    style={
                                        'width': '300px',
                                        'height': 'auto',
                                        'opacity': '0.6',
                                        'marginBottom': '20px'
                                    }
                                ),
                                html.P("En attente des résultats du backtest...", 
                                    className="text-center",
                                    style={'color': '#475569', 'fontSize': '1.1rem', 'fontWeight': '500'})
                            ], className="text-center p-5")
                        ])
                    ], style=CARD_STYLE)
                ]),
                html.Div([
                    dbc.Button(
                        [html.I(className="fas fa-share-alt mr-2"), "Partager dans la communauté"],
                        id="share-strategy-btn",
                        color="info",
                        className="mt-3",
                        style={'display': 'none'}  # Caché par défaut
                    ),
                    html.Div(id='share-strategy-confirmation', className="mt-2")
                ], className="text-center"),
            ], label="Résultats", id="tab-results", tab_id="tab-results"),
            

            # Onglet pour les stratégies sur Options
            dbc.Tab([
                # Titre de l'onglet
                html.H2([
                    html.I(className="fas fa-chart-area mr-2"),
                    html.Span(id="options-tab-title")
                ], className="text-center my-4 text-light"),

                # Carte pour la sélection des contrats
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-tasks mr-2"),
                        html.Span(id="options-card-title")
                    ], style=CARD_HEADER_STYLE),
                    dbc.CardBody([
                        # Labels pour les titres des colonnes
                        dbc.Row([
                            dbc.Col(html.Label(html.Span(id="options-label-underlying"), className="font-weight-bold")),
                            dbc.Col(html.Label(html.Span(id="options-label-maturity"), className="font-weight-bold")),
                            dbc.Col(html.Label(html.Span(id="options-label-strike"), className="font-weight-bold")),
                            dbc.Col(html.Label(html.Span(id="options-label-type"), className="font-weight-bold")),
                        ], className="mb-2 d-none d-lg-flex"), # Masqué sur les petits écrans pour plus de clarté

                        # Conteneur qui accueillera les lignes de sélection
                        dcc.Loading(
                            id="loading-options-chain",
                            type="default",
                            children=html.Div(
                                id='option-rows-container',
                                children=[
                                    # La première ligne est créée au chargement de la page
                                    create_option_selection_row(0)
                                ]
                            )
                        )
                    ], style=CARD_BODY_STYLE)
                ], style=CARD_STYLE),

                # Conteneur qui accueillera les graphiques générés dynamiquement
                dcc.Loading(
                    id="loading-charts",
                    type="default",
                    children=html.Div(id='option-charts-container', className="mt-4")
                )

            ], label="Options", id="options-tab", tab_id="options-tab"),

            # Onglet pour l'importation de données CSV
            dbc.Tab([
                html.H2([
                    html.I(className="fas fa-file-upload mr-2"),
                    html.Span(id="import-tab-title")
                ], className="text-center my-4 text-light"),

                dbc.Card([
                    dbc.CardHeader(html.Span(id="import-card-title"), style=CARD_HEADER_STYLE),
                    dbc.CardBody([
                        # --- NOUVEAU BLOC D'INSTRUCTIONS ---
                        dbc.Alert([
                            html.H5(html.Span(id="import-format-title"), className="alert-heading"),
                            html.P(html.Span(id="import-format-description")),
                            html.Ul([
                                html.Li(html.B(html.Span(id="import-format-col1"))),
                                html.Li(html.B(html.Span(id="import-format-col2"))),
                                html.Li(html.B(html.Span(id="import-format-col-other")))
                            ])
                        ], color="info"),
                        
                        dcc.Upload(
                            id='upload-data',
                            children=html.Div([html.Span(id="import-upload-text"), html.A(html.Span(id="import-upload-link"))]),
                            style={
                                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                                'borderWidth': '2px', 'borderStyle': 'dashed',
                                'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px 0'
                            },
                            multiple=False
                        ),
                        
                        html.Div(id='output-data-upload-filename'),
                        html.Hr(),
                        dbc.Label(html.Span(id="import-label-asset-name"), className="font-weight-bold"),
                        dbc.Input(id='custom-asset-name', placeholder="", className="mb-3"),
                        dbc.Button(html.Span(id="import-button-save"), id='save-custom-asset-button', color="success", className="w-100"),
                        html.Div(id='upload-status-message', className="mt-3")
                    ])
                ], style=CARD_STYLE)
            ], label="Import CSV", id="import-tab", tab_id="import-tab"),
            

            # Onglet Backtest Synthétique
            dbc.Tab([
                html.Div([
                    html.H2([
                        html.I(className="fas fa-atom mr-2"),
                        html.Span(id="synthetic-backtest-title")
                    ], className="text-center my-4 text-light"),
                    
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="fas fa-cogs mr-2"),
                            html.Span(id="synthetic-model-config-title")
                        ], style=CARD_HEADER_STYLE),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label(html.Span(id="synthetic-model-type-label"), className="font-weight-bold mb-2"),
                                    dcc.Dropdown(
                                        id='synthetic-model-dropdown',
                                        options=[
                                            {'label': 'Monte Carlo GBM', 'value': 'gbm'},
                                            {'label': 'Heston Stochastic Volatility', 'value': 'heston'},
                                            {'label': 'Bates Jump-Diffusion', 'value': 'bates'},
                                            {'label': 'SABR Model', 'value': 'sabr'}
                                        ],
                                        value='gbm',
                                        clearable=False
                                    ),
                                ], width=12, lg=6, className="mb-3 mb-lg-0"),
                                
                                dbc.Col([
                                    dbc.Row([
                                        dbc.Col([
                                            html.Label(html.Span(id="synthetic-horizon-label"), className="text-sm"),
                                            dbc.Input(id="synthetic-horizon", type="number", value=1, min=0.1, max=5, step=0.1, style=INPUT_STYLE)
                                        ], width=4),
                                        dbc.Col([
                                            html.Label(html.Span(id="synthetic-days-label"), className="text-sm"),
                                            dbc.Input(id="synthetic-steps", type="number", value=252, min=50, max=2000, step=1, style=INPUT_STYLE)
                                        ], width=4),
                                        dbc.Col([
                                            html.Label(html.Span(id="synthetic-simulations-label"), className="text-sm"),
                                            dbc.Input(id="synthetic-simulations", type="number", value=1000, min=10, max=10000, step=100, style=INPUT_STYLE)
                                        ], width=4),
                                    ])
                                ], width=12, lg=6)
                            ])
                        ], style=CARD_BODY_STYLE)
                    ], style=CARD_STYLE),
                    
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="fas fa-rocket mr-2"),
                            html.Span(id="synthetic-generation-title")
                        ], style=CARD_HEADER_STYLE),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label(html.Span(id="synthetic-calibration-period-label"), className="font-weight-bold mb-2"),
                                    dcc.DatePickerRange(
                                        id='synthetic-calibration-dates',
                                        start_date='2020-01-01',
                                        end_date='2025-01-01',
                                        display_format='YYYY-MM-DD'
                                    ),
                                ], width=6),
                                
                                dbc.Col([
                                    dbc.Button(
                                        [html.I(className="fas fa-rocket mr-2"), html.Span(id="synthetic-launch-button")],
                                        id="run-synthetic-backtest-direct",
                                        color="success",
                                        size="lg",
                                        className="w-100",
                                        style=BUTTON_STYLE
                                    ),
                                    html.Div(id="synthetic-backtest-status", className="mt-2")
                                ], width=6)
                            ])
                        ], style=CARD_BODY_STYLE)
                    ], style=CARD_STYLE),
                    
                    html.Div(id="synthetic-results-container"),
                    
                    dcc.Store(id='synthetic-data-store'),
                    dcc.Store(id='synthetic-model-info-store'),
                ])
            ], label="Backtest Synthétique", id="synthetic-tab", tab_id="synthetic-tab"),

            # Onglet Comparaison de Stratégies
            dbc.Tab([
                html.H2([
                    html.I(className="fas fa-balance-scale mr-2"),
                    html.Span(id="compare-tab-title")
                ], className="text-center my-4 text-light"),
                
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-folder-open mr-2"),
                        html.Span(id="strategy-selection-title")
                    ], style=CARD_HEADER_STYLE),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label([
                                    html.I(className="fas fa-chess-king mr-2"),
                                    html.Span(id="strategy-1-label")
                                ], className="font-weight-bold text-primary"),
                                dcc.Dropdown(
                                    id='compare-strategy-1',
                                    placeholder="",
                                    clearable=True,
                                    style={'marginBottom': '10px'}
                                ),
                                html.Div(id='strategy-1-info', className="mt-2")
                            ], width=12, md=4, className="mb-3 mb-md-0"),
                            
                            dbc.Col([
                                html.Label([
                                    html.I(className="fas fa-chess-queen mr-2"),
                                    html.Span(id="strategy-2-label")
                                ], className="font-weight-bold text-info"),
                                dcc.Dropdown(
                                    id='compare-strategy-2',
                                    placeholder="",
                                    clearable=True,
                                    style={'marginBottom': '10px'}
                                ),
                                html.Div(id='strategy-2-info', className="mt-2")
                            ], width=12, md=4, className="mb-3 mb-md-0"),
                            
                            dbc.Col([
                                html.Label([
                                    html.I(className="fas fa-chess-rook mr-2"),
                                    html.Span(id="strategy-3-label")
                                ], className="font-weight-bold text-success"),
                                dcc.Dropdown(
                                    id='compare-strategy-3',
                                    placeholder="",
                                    clearable=True,
                                    style={'marginBottom': '10px'}
                                ),
                                html.Div(id='strategy-3-info', className="mt-2")
                            ], width=12, md=4)
                        ]),
                        
                        html.Hr(className="my-4"),
                        
                        dbc.Button(
                            [html.I(className="fas fa-play-circle mr-2"), html.Span(id="launch-comparison-button")],
                            id="launch-strategy-comparison",
                            color="primary",
                            size="lg",
                            className="w-100",
                            disabled=True,
                            style=BUTTON_STYLE
                        ),
                        html.Div(id='comparison-status', className="mt-3")
                    ], style=CARD_BODY_STYLE)
                ], style=CARD_STYLE),
                
                html.Div(id='comparison-results-container', className="mt-4")
                
            ], label="Comparaison", id="compare-tab", tab_id="compare-tab"),

            # Onglet Communauté
            dbc.Tab([
                dbc.Tabs(id="community-sub-tabs", active_tab="community-top", children=[
                    # Sous-onglet TOP
                    dbc.Tab([
                        html.H3([
                            html.I(className="fas fa-trophy mr-2"),
                            html.Span(id="community-top-title")
                        ], className="text-center my-4 text-light"),
                        
                        # Section Stratégies Risquées
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-fire mr-2"),
                                html.Span(id="top-risky-title"),
                                dbc.Badge("High Risk", color="danger", className="ml-2")
                            ], style=CARD_HEADER_STYLE),
                            dbc.CardBody(html.Div(id='top-risky-strategies'))
                        ], style=CARD_STYLE, className="mb-4"),
                        
                        # Section Stratégies Modérées
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-balance-scale mr-2"),
                                html.Span(id="top-moderate-title"),
                                dbc.Badge("Moderate", color="warning", className="ml-2")
                            ], style=CARD_HEADER_STYLE),
                            dbc.CardBody(html.Div(id='top-moderate-strategies'))
                        ], style=CARD_STYLE, className="mb-4"),
                        
                        # Section Stratégies Safe
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-shield-alt mr-2"),
                                html.Span(id="top-safe-title"),
                                dbc.Badge("Safe", color="success", className="ml-2")
                            ], style=CARD_HEADER_STYLE),
                            dbc.CardBody(html.Div(id='top-safe-strategies'))
                        ], style=CARD_STYLE, className="mb-4"),
                        
                    ], label="Top", id="community-top", tab_id="community-top"),
                    
                    # Sous-onglet TOUTES LES STRATÉGIES
                    # Sous-onglet TOUTES LES STRATÉGIES
                    dbc.Tab([
                        html.H3([
                            html.I(className="fas fa-list mr-2"),
                            html.Span(id="all-strategies-title")
                        ], className="text-center my-4 text-light"),
                        
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-filter mr-2"),
                                html.Span(id="sort-strategies-title")
                            ], style=CARD_HEADER_STYLE),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.ButtonGroup([
                                            dbc.Button([html.I(className="fas fa-clock mr-2"), html.Span(id="sort-recent-btn")], 
                                                    id="sort-recent", color="primary", outline=True),
                                            dbc.Button([html.I(className="fas fa-trophy mr-2"), html.Span(id="sort-top-btn")], 
                                                    id="sort-top", color="primary", outline=True),
                                            dbc.Button([html.I(className="fas fa-fire mr-2"), html.Span(id="sort-trending-btn")], 
                                                    id="sort-trending", color="primary", outline=True),
                                        ], className="mb-3")
                                    ], width=8),
                                    dbc.Col([
                                        html.Div([
                                            html.Small("Stratégies par page : ", className="mr-2"),
                                            dcc.Dropdown(
                                                id='strategies-per-page-dropdown',
                                                options=[
                                                    {'label': '10', 'value': 10},
                                                    {'label': '20', 'value': 20},
                                                    {'label': '50', 'value': 50},
                                                ],
                                                value=20,
                                                clearable=False,
                                                style={'width': '100px', 'display': 'inline-block'}
                                            )
                                        ], className="text-right")
                                    ], width=4)
                                ])
                            ])
                        ], style=CARD_STYLE, className="mb-4"),
                        
                        # Conteneur des stratégies
                        html.Div(id='all-strategies-container'),
                        
                        # Pagination NOUVELLE
                        dbc.Row([
                            dbc.Col([
                                dbc.ButtonGroup([
                                    dbc.Button("← Précédent", id="prev-page-btn", color="secondary", outline=True, disabled=True),
                                    dbc.Button("Page 1", id="page-indicator-btn", color="primary", disabled=True),
                                    dbc.Button("Suivant →", id="next-page-btn", color="secondary", outline=True),
                                ], className="d-flex justify-content-center w-100")
                            ], width=12)
                        ], className="mt-4 mb-4"),
                        
                        # Store pour la page actuelle
                        dcc.Store(id='current-page-store', data=1),
                        
                    ], label="Toutes les Stratégies", id="all-strategies-tab", tab_id="all-strategies-tab"),
                    
                    # Sous-onglet COMMUNITY FORECASTING
                    dbc.Tab([
                        html.H3([
                            html.I(className="fas fa-crystal-ball mr-2"),
                            html.Span(id="forecasting-title")
                        ], className="text-center my-4 text-light"),
                        
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-chart-line mr-2"),
                                html.Span(id="forecasting-subtitle")
                            ], style=CARD_HEADER_STYLE),
                            dbc.CardBody([
                                html.P(html.Span(id="forecasting-description"), className="text-muted mb-4"),
                                
                                dbc.Row([
                                    dbc.Col([
                                        html.Label(html.Span(id="forecast-asset-label"), className="font-weight-bold"),
                                        dcc.Dropdown(
                                            id='forecast-asset-select',
                                            options=[{'label': ticker_to_name.get(asset, asset), 'value': asset} 
                                                    for asset_type in asset_types.values() 
                                                    for asset in asset_type['assets'][:5]],
                                            placeholder="Choisir un actif...",
                                            style={'marginBottom': '15px', 'zIndex': '9999'}
                                        )
                                    ], width=6),
                                    dbc.Col([
                                        html.Label(html.Span(id="forecast-horizon-label"), className="font-weight-bold"),
                                        dcc.Dropdown(
                                            id='forecast-horizon-select',
                                            options=[
                                                {'label': '1 semaine', 'value': '1w'},
                                                {'label': '1 mois', 'value': '1m'},
                                                {'label': '3 mois', 'value': '3m'},
                                                {'label': '6 mois', 'value': '6m'},
                                                {'label': '1 an', 'value': '1y'}
                                            ],
                                            value='1m',
                                            placeholder="Sélectionner l'horizon...",
                                            style={'marginBottom': '15px'}
                                        )
                                    ], width=6)
                                ]),
                                
                                dbc.Row([
                                    dbc.Col([
                                        html.Label(html.Span(id="forecast-prediction-label"), className="font-weight-bold"),
                                        dcc.Dropdown(
                                            id='forecast-direction',
                                            options=[
                                                {'label': '📈 Hausse', 'value': 'up'},
                                                {'label': '📉 Baisse', 'value': 'down'},
                                                {'label': '➡️ Stable', 'value': 'stable'}
                                            ],
                                            placeholder="Votre prédiction...",
                                            style={'marginBottom': '15px'}
                                        )
                                    ], width=6),
                                    dbc.Col([
                                        html.Label(html.Span(id="forecast-confidence-label"), className="font-weight-bold"),
                                        dcc.Slider(
                                            id='forecast-confidence',
                                            min=0, max=100, step=5, value=50,
                                            marks={0: '0%', 50: '50%', 100: '100%'}
                                        )
                                    ], width=6)
                                ]),
                                
                                dbc.Button([html.I(className="fas fa-paper-plane mr-2"), html.Span(id="submit-forecast-btn")], 
                                        id='submit-forecast', color="success", className="mt-3 w-100", style=BUTTON_STYLE),
                                html.Div(id='forecast-confirmation', className="mt-3")
                            ])
                        ], style=CARD_STYLE, className="mb-4"),
                        
                        # Affichage des prévisions
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-poll mr-2"),
                                html.Span(id="community-predictions-title")
                            ], style=CARD_HEADER_STYLE),
                            dbc.CardBody(html.Div(id='forecasts-display'))
                        ], style=CARD_STYLE)
                        
                    ], label="Community Forecasting", id="forecasting-tab", tab_id="forecasting-tab"),
                ])
            ], label="Communauté", id="community-tab", tab_id="community-tab"),
            dcc.Store(id='community-votes-store', storage_type='local', data={}),
            dcc.Store(id='community-comments-store', storage_type='local', data={}),
            dcc.Store(id='community-forecasts-store', storage_type='local', data={}),
            dcc.Store(id='sort-mode-store', data='recent'),
            
        ], style={"borderBottom": "none"}),

    # 

    ], style={'display': 'none'}),

    # Stores et composants cachés globaux
    # Stores et composants cachés globaux
    dcc.Store(id='strategy-to-apply-store'),
    dcc.Store(id='strategy-store', data={'file_path': None, 'strategy_data': None}),  # ✅ STORE UNIFIÉ
    dcc.Store(id='backtest-results-store'),
    dcc.Store(id='language-store', storage_type='session', data='fr'),
    dcc.Store(id='current-strategy-file-store', storage_type='session'),
    dcc.Store(id='votes-trigger-store', data={}),
    dcc.Store(id='comments-trigger-store', data={}),
    # dcc.Store(id='community-votes-store', storage_type='local', data={}),
    # dcc.Store(id='community-comments-store', storage_type='local', data={}),
    

    
    html.Div([
        # Paramètres Heston
        dbc.Input(id='heston-kappa', value=2.0, type="number"),
        dbc.Input(id='heston-theta', value=0.04, type="number"),
        dbc.Input(id='heston-xi', value=0.3, type="number"),
        dbc.Input(id='heston-rho', value=-0.7, type="number"),
        
        # Paramètres Bates  
        dbc.Input(id='bates-kappa', value=2.0, type="number"),
        dbc.Input(id='bates-theta', value=0.04, type="number"),
        dbc.Input(id='bates-xi', value=0.3, type="number"),
        dbc.Input(id='bates-rho', value=-0.7, type="number"),
        dbc.Input(id='bates-lambda', value=2.0, type="number"),
        dbc.Input(id='bates-mu-jump', value=0.0, type="number"),
        dbc.Input(id='bates-sigma-jump', value=0.1, type="number"),
        
        # Paramètres SABR
        dbc.Input(id='sabr-alpha', value=0.2, type="number"),
        dbc.Input(id='sabr-beta', value=0.5, type="number"),
        dbc.Input(id='sabr-rho', value=-0.3, type="number"),
        dbc.Input(id='sabr-nu', value=0.3, type="number"),
    ], style={'display': 'none'}),

    html.Div(
        children=[
            html.Div([
                dcc.Dropdown(
                    id=f'action-{block_i}-{action_idx}',
                    options=[
                        {'label': 'Acheter', 'value': 'Acheter'},
                        {'label': 'Vendre', 'value': 'Vendre'},
                        {'label': 'Ne rien faire', 'value': 'Ne rien faire'}
                    ],
                    value='Ne rien faire',
                    style={'display': 'none'}
                )
                for action_idx in range(10)
            ], id=f'block-{block_i}-actions')
            for block_i in range(MAX_BLOCKS)
        ],
        id='all-actions-container',
        style={'display': 'none'}
    ),
    dcc.Store(id='custom-asset-store', storage_type='session'),

    create_chatbot_layout()
])
            ])
        ])
    ])


def auth_layout():
    return dbc.Container([html.Div([
        html.H1([
            # html.I(className="fas fa-chart-line mr-3"),
            html.Span(id="auth-app-title")
        ], className="text-center my-4 text-light")
    ], style={'backgroundColor': COLORS['header'], 'padding': '20px', 'borderRadius': '8px', 'marginBottom': '20px', 'boxShadow': '0 4px 8px rgba(0, 0, 0, 0.2)', 'border': '1px solid #34495e'}),
    dbc.RadioItems(
        id="auth-mode",
        options=[
            {"label": html.Span(id="auth-login-label"), "value": "login"},
            {"label": html.Span(id="auth-register-label"), "value": "register"}
        ],
        value="login",
        inline=True,
        className="mb-3"
    ),
    dbc.Input(id="email", placeholder="", type="email", className="mb-2", style=INPUT_STYLE),
    dbc.Input(id="password", placeholder="", type="password", className="mb-2",style=INPUT_STYLE),

    html.Div([
        html.A(html.Span(id="forgot-password-link-text"), id="forgot-password-link", style={"cursor": "pointer", **BUTTON_STYLE}),
            html.Div([
            dbc.Input(id="reset-email", type="email", placeholder="", style={"marginBottom": "10px", **INPUT_STYLE}),
            dbc.Button(html.Span(id="send-reset-email-text"), id="send-reset-email", n_clicks=0, style={"marginBottom": "10px", **BUTTON_STYLE}),
            html.Div(id="reset-feedback", style={"marginBottom": "10px"})],id="forgot-password-container", style={"display": "none"}),
    ]),

    dbc.Button(html.Span(id="submit-btn-text"), id="submit-btn", color="primary", className="mb-3", style=BUTTON_STYLE),

    dbc.Alert(id="feedback", is_open=False)
    ], className="p-5", style= CARD_STYLE)


def create_multi_trajectory_results_display(analysis_results, model_type, symbols, language='fr'):
    """Crée l'affichage pour les résultats multi-trajectoires avec traductions"""
    
    t = TEXT.get(language, TEXT['fr'])
    results_components = []
    
    results_components.append(
        dbc.Alert([
            html.Strong(f"🎲 Backtest Monte Carlo - {len(analysis_results['raw_data'])} Trajectoires"),
            html.Br(),
            html.Small(f"Modèle: {model_type.upper()} | Symboles: {', '.join(symbols)}", className="text-info")
        ], color="primary", className="mb-4")
    )
    
    central = analysis_results['central_metrics']
    results_components.append(dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-chart-bar mr-2"),
            t.get('average-results-title', 'Résultats Moyens')
        ], style=CARD_HEADER_STYLE),
        dbc.CardBody([
            html.Table([
                html.Tbody([
                    html.Tr([
                        html.Td(t.get('trajectory-count-label', 'Nombre de trajectoires :'), style={'fontWeight': 'bold', 'padding': '8px'}),
                        html.Td(f"{central['Nombre de trajectoires']}", style={'textAlign': 'right', 'padding': '8px'})
                    ]),
                    html.Tr([
                        html.Td(t.get('median-return-label', 'Rendement médian :'), style={'fontWeight': 'bold', 'padding': '8px'}),
                        html.Td(f"{central['Rendement médian (%)']:.2f}%", 
                               style={'textAlign': 'right', 'padding': '8px', 'color': 'green' if central['Rendement médian (%)'] > 0 else 'red', 'fontWeight': 'bold'})
                    ]),
                    html.Tr([
                        html.Td(t.get('average-return-label', 'Rendement moyen :'), style={'fontWeight': 'bold', 'padding': '8px'}),
                        html.Td(f"{central['Rendement moyen (%)']:.2f}%", 
                               style={'textAlign': 'right', 'padding': '8px', 'color': 'green' if central['Rendement moyen (%)'] > 0 else 'red'})
                    ]),
                    html.Tr([
                        html.Td(t.get('median-sharpe-label', 'Sharpe médian :'), style={'fontWeight': 'bold', 'padding': '8px'}),
                        html.Td(f"{central['Sharpe médian']:.2f}", style={'textAlign': 'right', 'padding': '8px'})
                    ]),
                    html.Tr([
                        html.Td(t.get('median-drawdown-label', 'Drawdown médian :'), style={'fontWeight': 'bold', 'padding': '8px'}),
                        html.Td(f"{central['Drawdown médian (%)']:.2f}%", 
                               style={'textAlign': 'right', 'padding': '8px', 'color': 'red', 'fontWeight': 'bold'})
                    ]),
                ])
            ], style={'width': '100%', 'fontSize': '14px'})
        ], style=CARD_BODY_STYLE)
    ], style=CARD_STYLE, className="mb-4"))
    
    var = analysis_results['var_metrics']
    conf = analysis_results['confidence_intervals']
    
    results_components.append(dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-exclamation-triangle mr-2"),
            t.get('risk-analysis-title', 'Analyse de Risque')
        ], style=CARD_HEADER_STYLE),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H5(t.get('var-title', 'Value at Risk (VaR)'), className="text-danger mb-3"),
                    html.Table([
                        html.Tbody([
                            html.Tr([
                                html.Td(t.get('var-95-label', 'VaR 95% (perte max 5% scénarios) :'), style={'fontWeight': 'bold', 'padding': '6px'}),
                                html.Td(f"{var['VaR 95% (perte max 5% scenarios)']:.2f}%", 
                                       style={'textAlign': 'right', 'padding': '6px', 'color': 'red', 'fontWeight': 'bold'})
                            ]),
                            html.Tr([
                                html.Td(t.get('var-99-label', 'VaR 99% (perte max 1% scénarios) :'), style={'fontWeight': 'bold', 'padding': '6px'}),
                                html.Td(f"{var['VaR 99% (perte max 1% scenarios)']:.2f}%", 
                                       style={'textAlign': 'right', 'padding': '6px', 'color': 'darkred', 'fontWeight': 'bold'})
                            ]),
                            html.Tr([
                                html.Td(t.get('loss-probability-label', 'Probabilité de perte :'), style={'fontWeight': 'bold', 'padding': '6px'}),
                                html.Td(f"{var['Probabilité de perte']:.1f}%", 
                                       style={'textAlign': 'right', 'padding': '6px', 'color': 'orange'})
                            ]),
                        ])
                    ], style={'width': '100%', 'fontSize': '13px'})
                ], width=6),
                
                dbc.Col([
                    html.H5(t.get('scenarios-title', 'Scénarios'), className="text-info mb-3"),
                    html.Table([
                        html.Tbody([
                            html.Tr([
                                html.Td(t.get('best-scenario-label', 'Meilleur scénario :'), style={'fontWeight': 'bold', 'padding': '6px'}),
                                html.Td(f"{analysis_results['scenario_metrics']['Meilleur scénario (%)']:.1f}%", 
                                       style={'textAlign': 'right', 'padding': '6px', 'color': 'green', 'fontWeight': 'bold'})
                            ]),
                            html.Tr([
                                html.Td(t.get('worst-scenario-label', 'Pire scénario :'), style={'fontWeight': 'bold', 'padding': '6px'}),
                                html.Td(f"{analysis_results['scenario_metrics']['Pire scénario (%)']:.1f}%", 
                                       style={'textAlign': 'right', 'padding': '6px', 'color': 'red', 'fontWeight': 'bold'})
                            ]),
                            html.Tr([
                                html.Td(t.get('winning-scenarios-label', '% scénarios gagnants :'), style={'fontWeight': 'bold', 'padding': '6px'}),
                                html.Td(f"{analysis_results['scenario_metrics']['% scénarios gagnants']:.1f}%", 
                                       style={'textAlign': 'right', 'padding': '6px', 'color': 'green'})
                            ]),
                        ])
                    ], style={'width': '100%', 'fontSize': '13px'})
                ], width=6)
            ])
        ], style=CARD_BODY_STYLE)
    ], style=CARD_STYLE, className="mb-4"))
    
    import plotly.express as px
    df = analysis_results['raw_data']
    
    fig_hist = px.histogram(
        df, 
        x='total_return_pct', 
        nbins=50,
        title=f"Distribution des Rendements ({len(df)} trajectoires)",
        labels={'total_return_pct': 'Rendement Total (%)', 'count': 'Nombre de Scénarios'},
        color_discrete_sequence=['#3498db']
    )
    
    fig_hist.add_vline(x=var['VaR 95% (perte max 5% scenarios)'], line_dash="dash", line_color="red", 
                      annotation_text="VaR 95%")
    fig_hist.add_vline(x=var['VaR 99% (perte max 1% scenarios)'], line_dash="dash", line_color="darkred", 
                      annotation_text="VaR 99%")
    
    fig_hist.update_layout(template='plotly_dark', height=400)
    
    results_components.append(dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-chart-bar mr-2"),
            t.get('returns-distribution-title', 'Distribution des Rendements')
        ], style=CARD_HEADER_STYLE),
        dbc.CardBody([
            dcc.Graph(figure=fig_hist, config={'displayModeBar': True})
        ], style=CARD_BODY_STYLE)
    ], style=CARD_STYLE, className="mb-4"))
    
    return html.Div(results_components)


def create_synthetic_tab_layout():
    """Crée le layout de l'onglet backtest synthétique - Version simplifiée"""
    
    return dbc.Tab([
        html.Div([
            html.H2([
                html.I(className="fas fa-atom mr-2"),
                html.Span(id="synthetic-backtest-title")
            ], className="text-center my-4 text-light"),
            
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-cogs mr-2"),
                    html.Span(id="synthetic-model-config-title")
                ], style=CARD_HEADER_STYLE),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label(html.Span(id="synthetic-model-type-label"), className="font-weight-bold mb-2"),
                            dcc.Dropdown(
                                id='synthetic-model-dropdown',
                                options=[
                                    {
                                        'label': html.Div([
                                            html.Strong("Monte Carlo GBM"),
                                            html.Br(),
                                            html.Small(html.Span(id="gbm-description"), 
                                                     style={'color': '#888'})
                                        ]),
                                        'value': 'gbm'
                                    },
                                    {
                                        'label': html.Div([
                                            html.Strong("Heston Stochastic Volatility"),
                                            html.Br(),
                                            html.Small(html.Span(id="heston-description"), 
                                                     style={'color': '#888'})
                                        ]),
                                        'value': 'heston'
                                    },
                                    {
                                        'label': html.Div([
                                            html.Strong("Bates Jump-Diffusion"),
                                            html.Br(),
                                            html.Small(html.Span(id="bates-description"), 
                                                     style={'color': '#888'})
                                        ]),
                                        'value': 'bates'
                                    },
                                    {
                                        'label': html.Div([
                                            html.Strong("SABR Model"),
                                            html.Br(),
                                            html.Small(html.Span(id="sabr-description"), 
                                                     style={'color': '#888'})
                                        ]),
                                        'value': 'sabr'
                                    }
                                ],
                                value='gbm',
                                clearable=False,
                                style={'marginBottom': '15px'}
                            ),
                            
                            html.Div(id="model-description-container"),
                            
                        ], width=6),
                        
                        dbc.Col([
                            html.Label(html.Span(id="simulation-params-label"), className="font-weight-bold mb-2"),
                            
                            dbc.Row([
                                dbc.Col([
                                    html.Label(html.Span(id="synthetic-horizon-label"), className="text-sm"),
                                    dbc.Input(
                                        id="synthetic-horizon",
                                        type="number",
                                        value=1,
                                        min=0.1,
                                        max=5,
                                        step=0.1,
                                        style=INPUT_STYLE
                                    )
                                ], width=4),
                                dbc.Col([
                                    html.Label(html.Span(id="synthetic-days-label"), className="text-sm"),
                                    dbc.Input(
                                        id="synthetic-steps",
                                        type="number",
                                        value=252,
                                        min=50,
                                        max=2000,
                                        step=1,
                                        style=INPUT_STYLE
                                    )
                                ], width=4),
                                dbc.Col([
                                    html.Label(html.Span(id="synthetic-simulations-label"), className="text-sm"),
                                    dbc.Input(
                                        id="synthetic-simulations",
                                        type="number",
                                        value=1000,
                                        min=1,
                                        max=5000,
                                        step=100,
                                        style=INPUT_STYLE
                                    )
                                ], width=4),
                            ], className="mb-3"),
                            
                            html.Small(html.Span(id="simulation-note"), 
                                     className="text-muted")
                        ], width=6)
                    ])
                ], style=CARD_BODY_STYLE)
            ], style=CARD_STYLE),
            
            html.Div(id="model-params-container"),
            
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-rocket mr-2"),
                    html.Span(id="synthetic-generation-title")
                ], style=CARD_HEADER_STYLE),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label(html.Span(id="synthetic-calibration-period-label"), className="font-weight-bold mb-2"),
                            dcc.DatePickerRange(
                                id='synthetic-calibration-dates',
                                start_date='2020-01-01',
                                end_date='2025-01-01',
                                display_format='YYYY-MM-DD',
                                style={'width': '100%'}
                            ),
                            html.Small(html.Span(id="calibration-period-helper"), 
                                     className="text-muted d-block mt-2"),
                        ], width=6),
                        
                        dbc.Col([
                            dbc.Button(
                                [html.I(className="fas fa-rocket mr-2"), html.Span(id="synthetic-launch-button")],
                                id="run-synthetic-backtest-direct",
                                color="success",
                                size="lg",
                                className="w-100",
                                style=BUTTON_STYLE
                            ),
                            html.Div(id="synthetic-backtest-status", className="mt-2")
                        ], width=6)
                    ])
                ], style=CARD_BODY_STYLE)
            ], style=CARD_STYLE),
            
            html.Div(id="synthetic-results-container"),
            
            dcc.Store(id='synthetic-data-store'),
            dcc.Store(id='synthetic-model-info-store'),
            
        ])
    ], label="🧬 Backtest Synthétique", id="synthetic-tab", tab_id="synthetic-tab")

def create_synthetic_results_display(backtester, figures, model_info, strategy_data, model_type):
    """Crée l'affichage des résultats du backtest synthétique - Version simplifiée"""
    
    results_components = []
    
    results_components.append(
        dbc.Alert([
            html.Strong(f"🧬 Backtest Synthétique - Modèle {model_type.upper()}"),
            html.Br(),
            html.Small(f"Stratégie: {strategy_data.get('name', 'N/A')} | "
                      f"Symboles: {', '.join(model_info.keys()) if model_info else 'N/A'} | "
                      f"Données: {len(backtester.data)} points", className="text-info")
        ], color="info", className="mb-4")
    )

    # Bouton d'export PDF
    results_components.append(
        html.Div([
            dbc.Button(
                [html.I(className="fas fa-file-pdf mr-2"), "Télécharger Rapport PDF"],
                id="btn-download-pdf-synthetic",
                color="danger",
                className="mb-3",
                style={"marginTop": "10px"}
            ),
            dcc.Download(id="download-pdf-synthetic")
        ], className="text-center")
    )
    
    if hasattr(backtester, 'transactions') and backtester.transactions:
        results_components.append(dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-chart-bar mr-2"),
                html.Span(id="transaction-summary-title")
            ], style=CARD_HEADER_STYLE),
            dbc.CardBody([
                html.H4(html.Span(id="transaction-summary-heading"), 
                       className="text-center text-info mb-4"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.Strong(html.Span(id="total-transactions-label")), 
                                html.Span(f": {len(backtester.transactions)}")
                            ]),
                            dbc.ListGroupItem([
                                html.Strong(html.Span(id="buy-transactions-label")), 
                                html.Span(f": {sum(1 for t in backtester.transactions if t['type'] == 'ACHAT')}")
                            ]),
                            dbc.ListGroupItem([
                                html.Strong(html.Span(id="sell-transactions-label")), 
                                html.Span(f": {sum(1 for t in backtester.transactions if 'VENTE' in t['type'])}")
                            ]),
                            dbc.ListGroupItem([
                                html.Strong(html.Span(id="stop-loss-transactions-label")), 
                                html.Span(f": {sum(1 for t in backtester.transactions if t['type'] == 'STOP LOSS')}")
                            ]),
                            dbc.ListGroupItem([
                                html.Strong(html.Span(id="take-profit-transactions-label")), 
                                html.Span(f": {sum(1 for t in backtester.transactions if t['type'] == 'TAKE PROFIT')}")
                            ]),
                        ]),
                        
                        dbc.Card([
                            dbc.CardBody([
                                html.H5(html.Span(id="total-pnl-label"), className="card-title"),
                                html.H3(
                                    f"{sum(t.get('pnl', 0) for t in backtester.transactions):.2f} €",
                                    style={
                                        'color': 'green' if sum(t.get('pnl', 0) for t in backtester.transactions) > 0 else 'red',
                                        'fontWeight': 'bold'
                                    }
                                )
                            ])
                        ], color="light", className="mt-3"),
                    ], width=6),
                    
                    dbc.Col([
                        html.H5(html.Span(id="performance-metrics-title"), className="mb-3"),
                        html.Table([
                            html.Tbody([
                                html.Tr([
                                    html.Td(html.Span(id="initial-capital-label"), style={'fontWeight': 'bold', 'padding': '4px'}),
                                    html.Td(f"{backtester.metrics['Capital initial']:,.2f} €", style={'textAlign': 'right', 'padding': '4px'})
                                ]),
                                html.Tr([
                                    html.Td(html.Span(id="final-capital-label"), style={'fontWeight': 'bold', 'padding': '4px'}),
                                    html.Td(f"{backtester.metrics['Capital final']:,.2f} €", style={'textAlign': 'right', 'padding': '4px'})
                                ]),
                                html.Tr([
                                    html.Td(html.Span(id="total-return-label"), style={'fontWeight': 'bold', 'padding': '4px'}),
                                    html.Td(
                                        f"{backtester.metrics['Rendement total (%)']:.2f}%",
                                        style={
                                            'textAlign': 'right', 
                                            'padding': '4px',
                                            'color': 'green' if backtester.metrics['Rendement total (%)'] > 0 else 'red',
                                            'fontWeight': 'bold'
                                        }
                                    )
                                ]),
                                html.Tr([
                                    html.Td(html.Span(id="max-drawdown-label"), style={'fontWeight': 'bold', 'padding': '4px'}),
                                    html.Td(
                                        f"{backtester.metrics['Drawdown maximum (%)']:.2f}%",
                                        style={'textAlign': 'right', 'padding': '4px', 'color': 'red', 'fontWeight': 'bold'}
                                    )
                                ]),
                                html.Tr([
                                    html.Td(html.Span(id="sharpe-ratio-label"), style={'fontWeight': 'bold', 'padding': '4px'}),
                                    html.Td(f"{backtester.metrics['Ratio de Sharpe']:.2f}", style={'textAlign': 'right', 'padding': '4px'})
                                ]),
                                html.Tr([
                                    html.Td(html.Span(id="winning-trades-pct-label"), style={'fontWeight': 'bold', 'padding': '4px'}),
                                    html.Td(f"{backtester.metrics['Pourcentage de trades gagnants (%)']:.2f}%", style={'textAlign': 'right', 'padding': '4px'})
                                ])
                            ])
                        ], style={'width': '100%', 'fontSize': '14px'})
                    ], width=6)
                ]),
            ], style=CARD_BODY_STYLE)
        ], style=CARD_STYLE, className="mb-4"))

    symbol_cards = []
    for key, figure in figures.items():
        if key.startswith('symbol_'):
            symbol = key.replace('symbol_', '')
            
            symbol_card = dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-chart-line mr-2"),
                    html.Span(id="price-indicators-title"),
                    f" - {symbol} ",
                    html.Span(id="synthetic-data-label")
                ], style=CARD_HEADER_STYLE),
                dbc.CardBody([
                    dcc.Graph(
                        id=f'synthetic-symbol-chart-{symbol}',
                        figure=figure,
                        config={'displayModeBar': True, 'scrollZoom': True}
                    ),
                    dcc.Graph(
                        id=f'synthetic-volume-chart-{symbol}',
                        figure=figures.get(f'volume_{symbol}', {}),
                        config={'displayModeBar': True, 'scrollZoom': True}
                    ) if f'volume_{symbol}' in figures else html.Div()
                ], style=CARD_BODY_STYLE)
            ], style=CARD_STYLE, className="mb-4")
            
            symbol_cards.append(symbol_card)

    results_components.extend(symbol_cards)

    if 'transactions' in figures and isinstance(figures['transactions'], pd.DataFrame):
        transactions_df = figures['transactions'].copy()
        
        columns_to_keep = {
            'date': 'Date du trade',
            'type': 'Type',
            'symbol': 'Symbole', 
            'price': 'Prix',
            'shares': 'Quantité',
            'pnl': 'P&L',
            'pnl_pct': 'P&L %',
            'allocated_amount': 'Montant alloué',
            'allocation_return_pct': 'Retour allocation %'
        }
        
        available_columns = {k: v for k, v in columns_to_keep.items() if k in transactions_df.columns}
        transactions_df = transactions_df[list(available_columns.keys())].copy()
        transactions_df = transactions_df.rename(columns=available_columns)
        
        if 'Date du trade' in transactions_df.columns:
            if pd.api.types.is_datetime64_any_dtype(transactions_df['Date du trade']):
                transactions_df['Date du trade'] = transactions_df['Date du trade'].dt.strftime('%Y-%m-%d')
        
        results_components.append(dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-list-alt mr-2"),
                html.Span(id="transactions-journal-title"),
                " ",
                html.Span(id="synthetic-data-label")
            ], style=CARD_HEADER_STYLE),
            dbc.CardBody([
                dash_table.DataTable(
                    id='synthetic-transactions-table',
                    columns=[{"name": col, "id": col} for col in transactions_df.columns],
                    data=transactions_df.to_dict('records'),
                    sort_action='native',
                    filter_action='native',
                    page_size=15,
                    style_header={
                        'backgroundColor': COLORS['header'],
                        'color': COLORS['text'],
                        'fontWeight': 'bold',
                        'border': f'1px solid {COLORS["neutral"]}',
                        'textAlign': 'center'
                    },
                    style_cell={
                        'backgroundColor': COLORS['card_background'],
                        'color': COLORS['text'],
                        'border': f'1px solid {COLORS["neutral"]}',
                        'padding': '8px',
                        'textAlign': 'center',
                        'fontSize': '13px'
                    },
                    style_data_conditional=[
                        {
                            'if': {'column_id': 'Type', 'filter_query': '{Type} = "ACHAT"'},
                            'backgroundColor': 'rgba(46, 204, 113, 0.2)',
                            'color': COLORS['success']
                        },
                        {
                            'if': {'column_id': 'Type', 'filter_query': '{Type} contains "VENTE" || {Type} contains "STOP" || {Type} contains "FIN"'},
                            'backgroundColor': 'rgba(231, 76, 60, 0.2)',
                            'color': COLORS['danger']
                        },
                        {
                            'if': {'column_id': 'P&L', 'filter_query': '{P&L} > 0'},
                            'color': COLORS['success'],
                            'fontWeight': 'bold'
                        },
                        {
                            'if': {'column_id': 'P&L', 'filter_query': '{P&L} < 0'},
                            'color': COLORS['danger'],
                            'fontWeight': 'bold'
                        }
                    ]
                )
            ], style=CARD_BODY_STYLE)
        ], style=CARD_STYLE, className="mb-4"))

    if 'equity' in figures:
        results_components.append(dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-chart-area mr-2"),
                html.Span(id="equity-curve-title"),
                " ",
                html.Span(id="synthetic-data-label")
            ], style=CARD_HEADER_STYLE),
            dbc.CardBody([
                dcc.Graph(
                    id='synthetic-equity-chart',
                    figure=figures['equity'],
                    config={'displayModeBar': True, 'scrollZoom': True}
                )
            ], style=CARD_BODY_STYLE)
        ], style=CARD_STYLE, className="mb-4"))

    if 'drawdown' in figures:
        results_components.append(dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-chart-area mr-2"),
                html.Span(id="drawdown-title"),
                " ",
                html.Span(id="synthetic-data-label")
            ], style=CARD_HEADER_STYLE),
            dbc.CardBody([
                dcc.Graph(
                    id='synthetic-drawdown-chart',
                    figure=figures['drawdown'],
                    config={'displayModeBar': True, 'scrollZoom': True}
                )
            ], style=CARD_BODY_STYLE)
        ], style=CARD_STYLE, className="mb-4"))
    
    return html.Div(results_components)

# def create_synthetic_results_display(backtester, figures, model_info, strategy_data): 
#     """Crée l'affichage des résultats du backtest synthétique"""
    
#     results_components = []
    
#     results_components.append(
#         dbc.Card([
#             dbc.CardHeader([
#                 html.I(className="fas fa-info-circle mr-2"),
#                 html.Span(id="synthetic-backtest-info-title")
#             ], style=CARD_HEADER_STYLE),
#             dbc.CardBody([
#                 dbc.Row([
#                     dbc.Col([
#                         html.H5(html.Span(id="generative-model-title"), className="text-info"),
#                         html.P([html.Span(id="model-type-label"), f": {list(model_info.values())[0]['model_name'] if model_info else 'N/A'}"], className="mb-1"),
#                         html.P([html.Span(id="symbols-label"), f": {', '.join(model_info.keys()) if model_info else 'N/A'}"], className="mb-1"),
#                         html.P([html.Span(id="simulated-period-label"), f": {len(backtester.data)} jours"], className="mb-1"),
#                     ], width=6),
                    
#                     dbc.Col([
#                         html.H5(html.Span(id="tested-strategy-title"), className="text-success"),
#                         html.P([html.Span(id="strategy-name-label"), f": {strategy_data.get('name', 'N/A')}"], className="mb-1"),
#                         html.P([html.Span(id="initial-capital-display-label"), f": {strategy_data.get('initial_capital', 0):,.0f} €"], className="mb-1"),
#                         html.P([html.Span(id="allocation-display-label"), f": {strategy_data.get('allocation_pct', 0)}%"], className="mb-1"),
#                     ], width=6)
#                 ])
#             ], style=CARD_BODY_STYLE)
#         ], style=CARD_STYLE, className="mb-4")
#     )
    
#     if hasattr(backtester, 'metrics'):
#         pass
    
#     return html.Div(results_components)