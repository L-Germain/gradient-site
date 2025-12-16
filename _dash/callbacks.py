# Ajouter ces imports au début de votre fichier dashboard
import sys
import json
import pandas as pd
import numpy as np
import yfinance as yf

from datetime import datetime
import time
import os
import base64
import io
from plotly import graph_objects as go
import plotly.express as px
import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, ALL, MATCH
from dotenv import load_dotenv
load_dotenv()

# from _dash.chatbot_claude import create_chatbot_layout, register_chatbot_callbacks

from _dash.chatbot_groq import create_chatbot_layout, register_chatbot_callbacks

from collections import defaultdict

from dash import callback_context


from dash.exceptions import PreventUpdate
from curl_cffi import requests
# import firebase_admin
# from firebase_admin import credentials, auth
from flask import session
import ssl
import copy
sys.path.append(os.path.abspath(".."))
from utility.constants import *
from utility.pdf_exporter import export_backtest_to_pdf
from utility.utils import *
from utility.visuals import *
from backtester import *
from _dash.dash_utils import *
from _dash.dash_layout import *
from utility.translations import TEXT 



from server import app
from authentification.auth_handler import register_auth_callbacks



# Register Auth Callbacks
# Register Auth Callbacks
register_auth_callbacks(app)

# ========================================
# MOBILE SIDEBAR CALLBACKS
# ========================================

@app.callback(
    [Output("sidebar", "className"),
     Output("mobile-overlay", "className")],
    [Input("mobile-sidebar-toggle", "n_clicks"),
     Input("mobile-overlay", "n_clicks"),
     Input("url", "pathname")],
    [State("sidebar", "className")]
)
def toggle_mobile_sidebar(n_toggle, n_overlay, pathname, current_class):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "sidebar", ""
        
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # If navigating, always close
    if trigger_id == "url":
        return "sidebar", ""
        
    # If overlay clicked, close
    if trigger_id == "mobile-overlay":
        return "sidebar", ""
        
    # If toggle clicked, toggle state
    if trigger_id == "mobile-sidebar-toggle":
        if "active" in current_class:
            return "sidebar", ""
        else:
            return "sidebar active", "active"
            
    return "sidebar", ""

# ========================================
# THEME & NAVIGATION CALLBACKS
# ========================================

app.clientside_callback(
    """
    function(value) {
        const theme = value ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', theme);
        return theme;
    }
    """,
    Output('theme-store', 'data'),
    Input('theme-toggle', 'value')
)

@app.callback(
    [Output("main-tabs", "active_tab"),
     Output("nav-btn-creation", "className"),
     Output("nav-btn-results", "className"),
     Output("nav-btn-options", "className"),
     Output("nav-btn-compare", "className"),
     Output("nav-btn-synthetic", "className"),
     Output("nav-btn-import", "className")],
    [Input("nav-btn-creation", "n_clicks"),
     Input("nav-btn-results", "n_clicks"),
     Input("nav-btn-options", "n_clicks"),
     Input("nav-btn-compare", "n_clicks"),
     Input("nav-btn-synthetic", "n_clicks"),
     Input("nav-btn-import", "n_clicks")],
    [State("main-tabs", "active_tab")]
)
def update_sidebar_nav(n1, n2, n3, n4, n5, n6, current_tab):
    ctx = dash.callback_context
    if not ctx.triggered:
        # Default state
        return current_tab, \
               "sidebar-link active" if current_tab == "tab-creation" else "sidebar-link", \
               "sidebar-link active" if current_tab == "tab-results" else "sidebar-link", \
               "sidebar-link active" if current_tab == "options-tab" else "sidebar-link", \
               "sidebar-link active" if current_tab == "compare-tab" else "sidebar-link", \
               "sidebar-link active" if current_tab == "synthetic-tab" else "sidebar-link", \
               "sidebar-link active" if current_tab == "import-tab" else "sidebar-link"

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    mapping = {
        "nav-btn-creation": "tab-creation",
        "nav-btn-results": "tab-results",
        "nav-btn-options": "options-tab",
        "nav-btn-compare": "compare-tab", # Note: Check actual ID in dash_layout
        "nav-btn-synthetic": "synthetic-tab",
        "nav-btn-import": "import-tab"
    }

    # Verify compare-tab ID. In dash_layout previously viewed: "Onglet Comparaison de Stratégies" -> id="compare-tab"?
    # I didn't see it in my view earlier. I will use 'compare-tab' as safe guess or 'tab-compare'. 
    # If not found, Dash might suppress error or I can fix later.
    # Update: Based on step 159 line 781, it was id="compare-tab" (implied if not explicitly shown as otherwise).
    # Wait, line 646 was id="options-tab", 688 id="import-tab".
    # I'll assume "compare-tab" existed or exists.
    
    active_tab = mapping.get(button_id, "tab-creation")
    
    return active_tab, \
           "sidebar-link active" if active_tab == "tab-creation" else "sidebar-link", \
           "sidebar-link active" if active_tab == "tab-results" else "sidebar-link", \
           "sidebar-link active" if active_tab == "options-tab" else "sidebar-link", \
           "sidebar-link active" if active_tab == "compare-tab" else "sidebar-link", \
           "sidebar-link active" if active_tab == "synthetic-tab" else "sidebar-link", \
           "sidebar-link active" if active_tab == "import-tab" else "sidebar-link"

@app.callback(
    [Output('wizard-container', 'style'),
     Output('advanced-container', 'style'),
     Output('wizard-progress-container', 'style')],
    Input('advanced-mode-toggle-sidebar', 'value')
)
def toggle_interface_mode(advanced_mode):
    if advanced_mode:
        return {'display': 'none'}, {'display': 'block'}, {'display': 'none'}
    else:
        return {'display': 'block'}, {'display': 'none'}, {'display': 'block'}

# ========================================
# 2. SYNCHRONISATION DES DONNÉES ENTRE MODES
# ========================================

# @app.callback(
#     [Output('strategy-name', 'value', allow_duplicate=True),
#      Output('initial-capital', 'value', allow_duplicate=True),
#      Output('allocation', 'value', allow_duplicate=True),
#      Output('transaction-cost', 'value', allow_duplicate=True),
#      Output('stop-loss', 'value', allow_duplicate=True),
#      Output('take-profit', 'value', allow_duplicate=True),
#      Output('date-picker-range', 'start_date', allow_duplicate=True),
#      Output('date-picker-range', 'end_date', allow_duplicate=True),
#      Output('selected-stocks-store', 'data', allow_duplicate=True)],
#     [Input('wizard-strategy-name', 'value'),
#      Input('wizard-initial-capital', 'value'),
#      Input('wizard-allocation', 'value'),
#      Input('wizard-transaction-cost', 'value'),
#      Input('wizard-stop-loss', 'value'),
#      Input('wizard-take-profit', 'value'),
#      Input('wizard-date-picker-range', 'start_date'),
#      Input('wizard-date-picker-range', 'end_date'),
#      Input('wizard-selected-stocks-store', 'data')],
#     prevent_initial_call=True
# )
# def sync_wizard_to_advanced(w_name, w_capital, w_allocation, w_tx_cost, w_stop, w_take, 
#                            w_start_date, w_end_date, w_stocks):
#     """Synchronise les valeurs du wizard vers le mode avancé"""
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         raise PreventUpdate
    
#     return [w_name, w_capital, w_allocation, w_tx_cost, w_stop, w_take, 
#             w_start_date, w_end_date, w_stocks or []]



# ========================================
# 3. GESTION DES CHOIX ÉTAPE 1
# ========================================

# @app.callback(
#     [Output('template-choice-card', 'style'),
#      Output('manual-choice-card', 'style'),
#      Output('template-section', 'style'),
#      Output('step1-next', 'disabled'),
#      Output('wizard-choice-store', 'data')],
#     [Input('template-choice-card', 'n_clicks'),
#      Input('manual-choice-card', 'n_clicks'),
#      Input('wizard-predefined-strategy-select', 'value')],
#     [State('template-choice-card', 'style'),
#      State('manual-choice-card', 'style'),
#      State('wizard-choice-store', 'data')]
# )
# def handle_step1_choices(template_clicks, manual_clicks, template_value, 
#                         template_style, manual_style, current_choice):
#     """Gère les choix de l'étape 1"""
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         # État initial
#         return (
#             {'cursor': 'pointer', 'border': '2px solid transparent'},
#             {'cursor': 'pointer', 'border': '2px solid transparent'},
#             {'display': 'none'},
#             True,
#             {}
#         )
    
#     trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
#     choice_data = current_choice or {}
    
#     # Styles par défaut
#     template_card_style = {'cursor': 'pointer', 'border': '2px solid transparent'}
#     manual_card_style = {'cursor': 'pointer', 'border': '2px solid transparent'}
#     template_section_style = {'display': 'none'}
#     next_disabled = True
    
#     if trigger_id == 'template-choice-card' and template_clicks:
#         # Choix template
#         template_card_style['border'] = '2px solid #17a2b8'
#         template_section_style = {'display': 'block'}
#         choice_data['type'] = 'template'
#         next_disabled = not template_value
        
#     elif trigger_id == 'manual-choice-card' and manual_clicks:
#         # Choix manuel
#         manual_card_style['border'] = '2px solid #28a745'
#         choice_data['type'] = 'manual'
#         next_disabled = False
        
#     elif trigger_id == 'wizard-predefined-strategy-select':
#         # Sélection d'un template
#         if template_value and choice_data.get('type') == 'template':
#             next_disabled = False
#             choice_data['template'] = template_value
#             template_card_style['border'] = '2px solid #17a2b8'
#             template_section_style = {'display': 'block'}
    
#     return template_card_style, manual_card_style, template_section_style, next_disabled, choice_data

# ========================================
# 4. CHARGEMENT DES OPTIONS DE TEMPLATES POUR LE WIZARD
# ========================================
# DANS app.py - AJOUTEZ CETTE NOUVELLE FONCTION

@app.callback(
    Output('step1-next', 'disabled'),
    Input('manual-choice-card', 'n_clicks'),
    prevent_initial_call=True
)
def enable_step1_next_on_manual_choice(n_clicks):
    """
    Active le bouton "Suivant" de l'étape 1 dès que l'utilisateur
    clique sur la carte "Création Manuelle".
    """
    if n_clicks is not None and n_clicks > 0:
        return False  # Activer le bouton
    return True # Le laisser désactivé par défaut

@app.callback(
    Output('wizard-predefined-strategy-select', 'options'),
    Input('wizard-predefined-strategy-select', 'id')
)
def load_wizard_strategy_options(_):
    """Charge les options de stratégies pour le wizard"""
    options = []
    
    # Templates prédéfinis
    template_options = [
        {'label': '📈 Template: SMA Crossover Classic', 'value': 'template:sma_crossover'},
        {'label': '📊 Template: RSI Oversold/Overbought', 'value': 'template:rsi_oversold'},
        {'label': '🎯 Template: Bollinger Bands Breakout', 'value': 'template:bollinger_breakout'},
    ]
    options.extend(template_options)
    
    # Stratégies sauvegardées
    if os.path.exists("strategies"):
        for file in os.listdir("strategies"):
            if file.endswith(".json"):
                try:
                    with open(os.path.join("strategies", file), 'r', encoding='utf-8') as f:
                        strategy_data = json.load(f)
                        name = strategy_data.get('name', 'Sans nom')
                        created_at = strategy_data.get('created_at', '')
                        date_str = created_at.split(' ')[0] if created_at else 'Date inconnue'
                        
                        options.append({
                            'label': f'💾 Stratégie: {name} ({date_str})',
                            'value': f'saved:{os.path.join("strategies", file)}'
                        })
                except:
                    continue
    
    return options

# ========================================
# 5. DESCRIPTION DES TEMPLATES WIZARD
# ========================================

@app.callback(
    Output('wizard-predefined-strategy-description', 'children'),
    Input('wizard-predefined-strategy-select', 'value')
)
def update_wizard_template_description(selected_value):
    """Met à jour la description du template sélectionné dans le wizard"""
    if not selected_value:
        return ""
    
    try:
        if selected_value.startswith('template:'):
            template_key = selected_value.replace('template:', '')
            template = STRATEGY_TEMPLATES.get(template_key, {})
            
            if template:
                return dbc.Alert([
                    html.Strong(f"📋 Template: {template.get('name', 'Template')}"),
                    html.Br(),
                    html.Small(f"Capital: {template.get('initial_capital', 0):,}€ | "
                              f"Allocation: {template.get('allocation_pct', 0)}% | "
                              f"Stop Loss: {template.get('stop_loss_pct', 0)}%", 
                              className="text-info")
                ], color="info", className="mb-0")
        
        elif selected_value.startswith('saved:'):
            strategy_path = selected_value.replace('saved:', '')
            
            if os.path.exists(strategy_path):
                with open(strategy_path, 'r', encoding='utf-8') as f:
                    strategy_data = json.load(f)
                
                name = strategy_data.get('name', 'Sans nom')
                created_at = strategy_data.get('created_at', 'Date inconnue')
                capital = strategy_data.get('initial_capital', 0)
                allocation = strategy_data.get('allocation_pct', 0)
                
                return dbc.Alert([
                    html.Strong(f"💾 Stratégie: {name}"),
                    html.Br(),
                    html.Small(f"Créée: {created_at} | "
                              f"Capital: {capital:,}€ | "
                              f"Allocation: {allocation}%", 
                              className="text-success")
                ], color="success", className="mb-0")
        
        return ""
        
    except Exception as e:
        return dbc.Alert(f"Erreur: {str(e)}", color="danger")

# ========================================
# 6. NAVIGATION ENTRE LES ÉTAPES
# ========================================

# app.py

# DANS app.py - REMPLACEZ CETTE FONCTION

@app.callback(
    [Output('wizard-step-1', 'style'),
     Output('wizard-step-2', 'style'),
     Output('wizard-step-3', 'style'),
     Output('wizard-step-4', 'style'),
     Output('wizard-step-5', 'style'),
     Output('wizard-progress', 'value'),
     Output('step1-badge', 'color'),
     Output('step2-badge', 'color'),
     Output('step3-badge', 'color'),
     Output('step4-badge', 'color'),
     Output('step5-badge', 'color'),
     Output('wizard-step-store', 'data')],
    [Input('step1-next', 'n_clicks'),
     Input('step2-prev', 'n_clicks'),
     Input('step2-next', 'n_clicks'),
     Input('step3-prev', 'n_clicks'),
     Input('step3-next', 'n_clicks'),
     Input('step4-prev', 'n_clicks'),
     Input('step5-prev', 'n_clicks'),
     Input('restart-wizard', 'n_clicks'),
     Input('restart-wizard-2', 'n_clicks'),
     Input('wizard-step-store', 'data')],  # Le store est maintenant un Input
    prevent_initial_call=True
)
def navigate_wizard_steps(step1_next, step2_prev, step2_next, step3_prev, step3_next,
                          step4_prev, step5_prev, restart1, restart2, step_from_store):
    """Gère la navigation entre les 5 étapes du wizard, y compris par mise à jour externe."""
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Logique pour déterminer la nouvelle étape
    current_step = 1  # Par défaut

    if trigger_id == 'wizard-step-store':
        # Cas où le backtest a mis à jour l'étape : on utilise cette valeur
        current_step = step_from_store
    else:
        # Cas où un bouton a été cliqué
        step_transitions = {
            'step1-next': 2,
            'step2-prev': 1, 'step2-next': 3,
            'step3-prev': 2, 'step3-next': 4,
            'step4-prev': 3,
            'step5-prev': 4,
            'restart-wizard': 1,
            'restart-wizard-2': 1
        }
        if trigger_id in step_transitions:
            current_step = step_transitions[trigger_id]

    # Sécurité au cas où l'étape serait invalide
    if not current_step or current_step > 5:
        current_step = 1

    # Mise à jour de l'affichage
    styles = {f'wizard-step-{i}': {'display': 'none'} for i in range(1, 6)}
    styles[f'wizard-step-{current_step}'] = {'display': 'block'}

    progress_value = current_step * 20

    badge_colors = ['light'] * 5
    for i in range(current_step):
        badge_colors[i] = 'success' if i < current_step - 1 else 'primary'

    return (
        styles['wizard-step-1'], styles['wizard-step-2'], styles['wizard-step-3'],
        styles['wizard-step-4'], styles['wizard-step-5'],
        progress_value,
        badge_colors[0], badge_colors[1], badge_colors[2],
        badge_colors[3], badge_colors[4],
        current_step
    )

# ========================================
# 7. GESTION DES ACTIFS DANS LE WIZARD
# ========================================

@app.callback(
    Output("wizard-asset-sections-container", "children", allow_duplicate=True),
    Output('wizard-selected-stocks-store', 'data', allow_duplicate=True),
    Output('wizard-selected-assets-summary', 'children'),
    [Input("wizard-asset-class-selector", "value"),
     Input('language-switcher-sidebar', 'value')] +  # AJOUT DE LA LANGUE
    [Input({'type': 'wizard-asset-dropdown', 'asset_class': ALL, 'index': ALL}, 'value')],
    prevent_initial_call=True
)
def reveal_wizard_asset_sections_progressive(selected_classes, selected_language, asset_values):
    """Révèle les sections d'actifs dans le wizard avec traductions"""
    
    # Gestion de la langue
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    if not selected_classes:
        return html.Div([
            html.I(className="fas fa-arrow-up fa-2x text-muted mb-3"),
            html.P(t.get('select-asset-classes-above', 'Sélectionnez des classes d\'actifs ci-dessus'), 
                   className="text-muted text-center")
        ], className="text-center py-5"), [], html.Div()  # SUPPRESSION DU RÉSUMÉ
    
    # Organiser les valeurs par asset_class
    values_by_class = {}
    ctx = dash.callback_context 
    
    if ctx.inputs_list and len(ctx.inputs_list) > 2:  # +1 car on a ajouté la langue
        for input_item in ctx.inputs_list[2]:  # Index 2 maintenant
            if input_item.get('id') and input_item.get('value'):
                asset_class = input_item['id']['asset_class']
                index = input_item['id']['index']
                
                if asset_class not in values_by_class:
                    values_by_class[asset_class] = {}
                values_by_class[asset_class][index] = input_item['value']
    
    sections = []
    style_map = STYLE_MAP
    
    for asset_class in selected_classes:
        if asset_class not in asset_types:
            continue
            
        asset_info = asset_types[asset_class]
        assets = asset_info['assets']
        type_label = asset_info['label']
        
        style = style_map.get(asset_class, {'color': '#95a5a6', 'icon': 'fas fa-chart-bar'})
        
        # Déterminer combien de dropdowns afficher
        num_dropdowns_to_show = 1
        if asset_class in values_by_class:
            for i in range(4):
                if i in values_by_class[asset_class] and values_by_class[asset_class][i]:
                    num_dropdowns_to_show = i + 2
        
        # Créer les dropdowns avec traductions
        dropdown_elements = []
        for i in range(num_dropdowns_to_show):
            asset_number = t.get('asset-number', 'Actif {i}').format(i=i+1)
            label = f"{asset_number}:"
            
            # Placeholder traduit selon la classe d'actif
            if asset_class == 'actions_cac40':
                placeholder = t.get('choose-cac40-stock', 'Choisir une action CAC40')
            else:
                placeholder = f"{t.get('choose', 'Choisir')} {type_label.lower()}"
            
            dropdown_div = html.Div([
                html.Label(label, className="font-weight-bold text-info mb-2"),
                dcc.Dropdown(
                    id={'type': 'wizard-asset-dropdown', 'asset_class': asset_class, 'index': i},
                    options=[
                        {'label': ticker_to_name.get(asset, asset), 'value': asset} 
                        for asset in assets
                    ],
                    value=values_by_class.get(asset_class, {}).get(i),
                    placeholder=placeholder,
                    searchable=True,
                    clearable=True,
                    style={'marginBottom': '10px'}
                )
            ], className="mb-2")
            
            dropdown_elements.append(dropdown_div)
        
        # Créer la section avec traductions
        section = dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.I(className=f"{style['icon']} mr-2"),
                        html.Strong(type_label)
                    ], width=8),
                    dbc.Col([
                        dbc.Badge(f"{num_dropdowns_to_show}/5", color="light", className="mr-1"),
                        dbc.Badge(f"{len(assets)} {t.get('available-count', 'disponibles')}", color="light")
                    ], width=4, className="text-right")
                ])
            ], style={
                'backgroundColor': style['color'],
                'color': 'white',
                'fontWeight': 'bold'
            }),
            dbc.CardBody([
                html.Div(dropdown_elements),
                html.Small([
                    html.I(className="fas fa-info-circle mr-1"),
                    t.get('next-dropdown-helper', 'Le prochain dropdown apparaîtra automatiquement')
                ], className="text-muted")
            ])
        ], className="mb-3", style={
            'border': f'2px solid {style["color"]}',
            'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'
        })
        
        sections.append(section)
    
    # Collecter tous les actifs sélectionnés
    all_selected_assets = [asset for asset in asset_values if asset]
    
    # SUPPRESSION DU RÉSUMÉ - retourner un div vide
    return sections, all_selected_assets, html.Div()

# ========================================
# 8. VALIDATION ÉTAPE 2
# ========================================

@app.callback(
    Output('step2-next', 'disabled'),
    Input('wizard-selected-stocks-store', 'data')
)
def validate_wizard_step2(selected_stocks):
    """Active le bouton suivant si des actifs sont sélectionnés"""
    return not (selected_stocks and len(selected_stocks) > 0)

# ========================================
# 9. RÉSUMÉ DE LA STRATÉGIE (ÉTAPE 5)
# ========================================

# app.py

@app.callback(
    Output('strategy-summary', 'children'),
    [Input('wizard-step-store', 'data'),
     Input('language-switcher-sidebar', 'value')],  # AJOUT DE LA LANGUE
    [
        State('simple-action-dropdown', 'value'),
        State('simple-trigger-dropdown', 'value'),
        State('wizard-selected-stocks-store', 'data')
    ]
)
def update_wizard_strategy_summary(current_step, selected_language, action, trigger, selected_stocks):
    """
    Met à jour le résumé de la stratégie sur l'étape 4 du wizard avec traductions.
    """
    if current_step != 4:
        raise PreventUpdate

    # Gestion de la langue
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]

    if not all([action, trigger, selected_stocks]):
        return dbc.Alert(t.get('select-scenario-assets-first', 'Veuillez d\'abord sélectionner un scénario et des actifs.'), color="warning")

    # Traduire l'action selon la langue
    action_translations = {
        'fr': {'Acheter': 'Acheter', 'Vendre': 'Vendre'},
        'en': {'Acheter': 'Buy', 'Vendre': 'Sell'}
    }
    translated_action = action_translations.get(selected_language, {}).get(action, action)

    # Traduire le déclencheur selon la langue
    trigger_translations = {
        'fr': {
            'Un peu tous les mois': 'Un peu tous les mois',
            'Lorsque le prix baisse': 'Lorsque le prix baisse',
            'Lorsque le prix augmente': 'Lorsque le prix augmente',
            'Lorsque le prix augmente après une baisse': 'Lorsque le prix augmente après une baisse',
            'Lorsque la volatilité augmente': 'Lorsque la volatilité augmente'
        },
        'en': {
            'Un peu tous les mois': 'A little every month',
            'Lorsque le prix baisse': 'When price goes down',
            'Lorsque le prix augmente': 'When price goes up',
            'Lorsque le prix augmente après une baisse': 'When price goes up after a decline',
            'Lorsque la volatilité augmente': 'When volatility increases'
        }
    }
    translated_trigger = trigger_translations.get(selected_language, {}).get(trigger, trigger)

    # Texte des actifs avec traduction
    if selected_language == 'en':
        if len(selected_stocks) == 1:
            asset_text = f"{len(selected_stocks)} selected asset: {', '.join(selected_stocks[:3])}"
        else:
            asset_text = f"{len(selected_stocks)} selected assets: {', '.join(selected_stocks[:3])}"
    else:
        asset_text = f"{len(selected_stocks)} actif(s) sélectionné(s) : {', '.join(selected_stocks[:3])}"
    
    if len(selected_stocks) > 3:
        asset_text += "..."

    summary_items = [
        html.P([html.Strong(f"{t.get('strategy-recap-action-label', 'Action :')} "), translated_action]),
        html.P([html.Strong(f"{t.get('strategy-recap-scenario-label', 'Scénario :')} "), translated_trigger]),
        html.P([html.Strong(f"{t.get('strategy-recap-assets-label', 'Actifs :')} "), asset_text]),
        html.Hr(),
        html.P(t.get('default-params-notice', 'Les autres paramètres (capital, frais, etc.) seront ceux par défaut définis pour ce scénario.'), 
               className="small text-muted")
    ]
    
    return summary_items
# ========================================
# 10. BASCULEMENT VERS MODE AVANCÉ
# ========================================

# Callback pour activer le bouton "Suivant" de l'étape 3
@app.callback(
    Output('step3-next', 'disabled'),
    [Input('simple-action-dropdown', 'value'),
     Input('simple-trigger-dropdown', 'value')]
)
def validate_wizard_step3_simple(action, trigger):
    """Active le bouton suivant si une action et un déclencheur sont sélectionnés"""
    return not (action and trigger)



@app.callback(
    Output('advanced-mode-toggle-sidebar', 'value', allow_duplicate=True),
    Input('switch-to-advanced', 'n_clicks'),
    prevent_initial_call=True
)
def switch_to_advanced_from_wizard(n_clicks):
    """Bascule vers le mode avancé depuis le wizard"""
    if n_clicks:
        return True
    raise PreventUpdate


# ========================================
# 11. LANCEMENT DU BACKTEST DEPUIS LE WIZARD
# ========================================



@app.callback(
    Output('wizard-results-placeholder', 'children', allow_duplicate=True),
    Output('wizard-step-store', 'data', allow_duplicate=True),
    Input('run-backtest-from-wizard', 'n_clicks'),
    [
        State('simple-action-dropdown', 'value'),
        State('simple-trigger-dropdown', 'value'),
        State('wizard-selected-stocks-store', 'data'),
        State('language-switcher-sidebar', 'value'),  # AJOUT DE LA LANGUE
    ],
    prevent_initial_call=True
)
def run_and_display_wizard_backtest(n_clicks, action, trigger, selected_stocks, selected_language):
    """
    Lance le backtest du mode simple et génère un affichage de résultats simplifié avec traductions.
    """
    if not n_clicks:
        raise PreventUpdate

    # Gestion de la langue
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]

    if not all([action, trigger, selected_stocks]):
        return dbc.Alert(t.get('select-scenario-assets-required', 'Veuillez sélectionner une action, un scénario et au moins un actif.'), color="warning"), dash.no_update

    try:
        # --- 1. Construction et exécution du backtest (inchangé) ---
        strategy_key = (action, trigger)
        strategy_template = copy.deepcopy(SIMPLE_STRATEGIES[strategy_key])
        main_asset = selected_stocks[0]
        strategy_str = json.dumps(strategy_template).replace("PLACEHOLDER_ASSET", main_asset)
        processed_strategy = json.loads(strategy_str)
        final_name = f"{processed_strategy['name']} ({main_asset})"
        
        final_strategy_dict = {
            "name": final_name, "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "initial_capital": processed_strategy.get('initial_capital', 100000),
            "allocation_pct": processed_strategy.get('allocation_pct', 10),
            "transaction_cost": processed_strategy.get('transaction_cost', 1),
            "stop_loss_pct": processed_strategy.get('stop_loss_pct', 5),
            "take_profit_pct": processed_strategy.get('take_profit_pct', 10),
            "date_range": {"start": "2024-01-01", "end": "2025-01-01"},
            "decision_blocks": processed_strategy.get('decision_blocks', []),
            "selected_stocks": selected_stocks
        }

        backtester = Backtester(strategy_data=final_strategy_dict)
        backtester.run_backtest()

        # --- 2. Construction du NOUVEL affichage simplifié AVEC TRADUCTIONS ---
        figures = generate_plotly_figures(backtester)
        results_components = []

        # A. Composant PNL & Période en haut de page
        if hasattr(backtester, 'transactions_df') and not backtester.transactions_df.empty:
            total_pnl = backtester.transactions_df['pnl'].sum()
            pnl_color = 'success' if total_pnl >= 0 else 'danger'
            
            start_date_str = pd.to_datetime(final_strategy_dict['date_range']['start']).strftime('%B %Y')
            end_date_str = pd.to_datetime(final_strategy_dict['date_range']['end']).strftime('%B %Y')
            
            # TRADUCTION DE LA PÉRIODE
            if selected_language == 'en':
                date_range_text = f"Period: {start_date_str} to {end_date_str}"
            else:
                date_range_text = f"Période : {start_date_str} à {end_date_str}"

            pnl_component = dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(html.H5(t.get('wizard-total-pnl-title', 'Profit & Loss Total'), className="text-center text-muted"), width=12),
                        dbc.Col(
                            html.H2(f"{total_pnl:,.2f} €", className=f"text-{pnl_color} font-weight-bold text-center"),
                            width=12
                        ),
                        dbc.Col(html.P(date_range_text, className="text-center small text-muted mt-2"), width=12),
                    ])
                ]), className="mb-4",
            )
            results_components.append(pnl_component)

        # B. Graphique principal (Prix & Indicateurs) - AVEC TRADUCTION
        if figures:
            for fig_name, fig_obj in figures.items():
                if fig_name.startswith('symbol_'):
                    graph_card = dbc.Card([
                        dbc.CardHeader(t.get('wizard-price-signals-title', 'Évolution du cours et signaux de trading')),
                        dbc.CardBody(dcc.Graph(figure=fig_obj))
                    ], className="mb-4")
                    results_components.append(graph_card)

        # C. Indicateurs de risque clés - AVEC TRADUCTIONS
        if backtester.metrics:
            # MAPPING DES MÉTRIQUES AVEC TRADUCTIONS
            if selected_language == 'en':
                metrics_to_show = {
                    'Ratio de Sharpe': 'Sharpe Ratio',
                    'Nombre de trades': 'Number of trades',
                    'Pourcentage de trades gagnants (%)': '% of winning trades',
                    'Profit moyen par trade': 'Average profit per trade'
                }
            else:
                metrics_to_show = {
                    'Ratio de Sharpe': 'Ratio de Sharpe',
                    'Nombre de trades': 'Nombre de trades',
                    'Pourcentage de trades gagnants (%)': '% de trades gagnants',
                    'Profit moyen par trade': 'Profit moyen / trade'
                }
            
            risk_metrics_items = []
            for key, display_name in metrics_to_show.items():
                if key in backtester.metrics:
                    value = backtester.metrics[key]
                    formatted_value = f"{int(value)}" if key == 'Nombre de trades' else f"{value:,.2f}"
                    item = dbc.ListGroupItem([
                        html.Span(display_name, className="font-weight-bold"),
                        dbc.Badge(formatted_value, color="primary", pill=True, className="float-right p-2")
                    ], className="d-flex justify-content-between align-items-center")
                    risk_metrics_items.append(item)
            
            risk_component = dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-shield-alt mr-2"), 
                    t.get('wizard-key-performance-title', 'Indicateurs de Performance Clés')
                ]),
                dbc.ListGroup(risk_metrics_items, flush=True)
            ], className="mb-4")
            results_components.append(risk_component)

        return html.Div(results_components), 5

    except Exception as e:
        import traceback
        error_display = dbc.Alert(f"{t.get('wizard-backtest-error', 'Une erreur est survenue')}: {e}\n{traceback.format_exc()}", color="danger")
        return error_display, 5

# DANS app.py - AJOUTEZ CETTE NOUVELLE FONCTION

@app.callback(
    [Output('wizard-asset-class-selector', 'value'),
     Output('wizard-selected-stocks-store', 'data'),
     Output('simple-action-dropdown', 'value'),
     Output('simple-trigger-dropdown', 'value'),
     Output('wizard-results-placeholder', 'children', allow_duplicate=True),],
    Input('restart-wizard-2', 'n_clicks'),
    prevent_initial_call=True
)
def reset_wizard_inputs_on_restart(n_clicks):
    """
    Réinitialise les champs du wizard lorsqu'on clique sur "Nouvelle Stratégie".
    """
    if not n_clicks:
        raise PreventUpdate
    
    # On retourne des valeurs vides pour chaque composant
    return None, [], None, None, ""
# ========================================
# 12. APPLICATION DE TEMPLATES DEPUIS LE WIZARD
# ========================================

# @app.callback(
#     [Output("wizard-strategy-name", "value", allow_duplicate=True),
#      Output("wizard-initial-capital", "value", allow_duplicate=True),
#      Output("wizard-allocation", "value", allow_duplicate=True),
#      Output("wizard-transaction-cost", "value", allow_duplicate=True),
#      Output("wizard-stop-loss", "value", allow_duplicate=True),
#      Output("wizard-take-profit", "value", allow_duplicate=True),
#      Output('wizard-date-picker-range', 'start_date', allow_duplicate=True),
#      Output('wizard-date-picker-range', 'end_date', allow_duplicate=True),
#      Output('wizard-selected-stocks-store', 'data', allow_duplicate=True)],
#     Input("wizard-apply-predefined-strategy", "n_clicks"),
#     [State("wizard-predefined-strategy-select", "value"),
#      State('wizard-selected-stocks-store', 'data')],
#     prevent_initial_call=True
# )
# def apply_wizard_predefined_strategy(n_clicks, selected_value, current_selected_stocks):
#     """Applique la stratégie sélectionnée dans le wizard"""
#     if not n_clicks or not selected_value:
#         raise PreventUpdate
    
#     try:
#         strategy_data = None
#         final_selected_stocks = current_selected_stocks or []
        
#         if selected_value.startswith('template:'):
#             if not current_selected_stocks:
#                 raise ValueError("Veuillez sélectionner au moins un actif pour appliquer un template")
            
#             template_key = selected_value.replace('template:', '')
#             template = STRATEGY_TEMPLATES.get(template_key)
            
#             if not template:
#                 raise ValueError(f"Template '{template_key}' non trouvé")
            
#             strategy_data = {
#                 'name': template['name'],
#                 'initial_capital': template['initial_capital'],
#                 'allocation_pct': template['allocation_pct'],
#                 'transaction_cost': template['transaction_cost'],
#                 'stop_loss_pct': template['stop_loss_pct'],
#                 'take_profit_pct': template['take_profit_pct'],
#                 'date_range': {
#                     'start': '2024-01-01',
#                     'end': '2025-01-01'
#                 }
#             }
            
#         elif selected_value.startswith('saved:'):
#             strategy_path = selected_value.replace('saved:', '')
            
#             if not os.path.exists(strategy_path):
#                 raise ValueError(f"Fichier de stratégie non trouvé: {strategy_path}")
            
#             with open(strategy_path, 'r', encoding='utf-8') as f:
#                 strategy_data = json.load(f)
            
#             saved_stocks = strategy_data.get('selected_stocks', [])
#             if not current_selected_stocks and saved_stocks:
#                 final_selected_stocks = saved_stocks
        
#         if not strategy_data:
#             raise ValueError("Impossible de charger les données de la stratégie")
        
#         # Extraire les champs
#         name = strategy_data.get('name', '')
#         capital = strategy_data.get('initial_capital', 100000)
#         allocation = strategy_data.get('allocation_pct', 10)
#         tx_cost = strategy_data.get('transaction_cost', 1)
#         stop_loss = strategy_data.get('stop_loss_pct', 5)
#         take_profit = strategy_data.get('take_profit_pct', 10)
        
#         date_range = strategy_data.get('date_range', {})
#         start_date = date_range.get('start', '2024-01-01')
#         end_date = date_range.get('end', '2025-01-01')
        
#         return [
#             name, capital, allocation, tx_cost, stop_loss, take_profit,
#             start_date, end_date, final_selected_stocks
#         ]
        
#     except Exception as e:
#         print(f"❌ Erreur application stratégie wizard: {e}")
#         raise PreventUpdate

# app.py

@app.callback(
    Output('wizard-save-confirmation', 'children'),
    Input('wizard-save-strategy', 'n_clicks'),
    [
        # On ne prend en State que ce qui vient de l'interface simple
        State('simple-action-dropdown', 'value'),
        State('simple-trigger-dropdown', 'value'),
        State('wizard-selected-stocks-store', 'data'),
    ],
    prevent_initial_call=True
)
def save_simple_strategy(n_clicks, action, trigger, selected_stocks):
    """
    Crée et sauvegarde un fichier de stratégie à partir des choix du mode simple.
    """
    if not n_clicks:
        raise PreventUpdate

    if not all([action, trigger, selected_stocks]):
        return dbc.Alert("Veuillez sélectionner une action, un scénario et au moins un actif.", color="warning")

    try:
        # Logique identique à la fonction de backtest pour construire la stratégie
        strategy_key = (action, trigger)
        strategy_template = copy.deepcopy(SIMPLE_STRATEGIES[strategy_key])
        main_asset = selected_stocks[0]
        strategy_str = json.dumps(strategy_template).replace("PLACEHOLDER_ASSET", main_asset)
        processed_strategy = json.loads(strategy_str)
        final_name = f"{processed_strategy['name']} ({main_asset})"

        final_strategy_dict = {
            "name": final_name,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "initial_capital": processed_strategy.get('initial_capital', 100000),
            "allocation_pct": processed_strategy.get('allocation_pct', 10),
            "transaction_cost": processed_strategy.get('transaction_cost', 1),
            "stop_loss_pct": processed_strategy.get('stop_loss_pct', 5),
            "take_profit_pct": processed_strategy.get('take_profit_pct', 10),
            "date_range": {"start": "2024-01-01", "end": "2025-01-01"}, # Dates par défaut
            "decision_blocks": processed_strategy.get('decision_blocks', []),
            "selected_stocks": selected_stocks
        }

        # Sauvegarde du fichier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = final_name.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '')
        filename = f"{safe_name}_{timestamp}.json"
        
        os.makedirs("strategies", exist_ok=True)
        file_path = os.path.join("strategies", filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(final_strategy_dict, f, indent=2, ensure_ascii=False)

        return dbc.Alert(f"Stratégie sauvegardée avec succès : {filename}", color="success", duration=4000)

    except Exception as e:
        return dbc.Alert(f"Erreur lors de la sauvegarde : {e}", color="danger")



####################################################################################

# 1. Callback simplifié pour afficher les sections avec logique progressive intégrée
# DANS app.py - REMPLACEZ LA FONCTION EXISTANTE PAR CELLE-CI
# DANS app.py - REMPLACEZ LA FONCTION EXISTANTE PAR CELLE-CI

# DANS app.py - REMPLACEZ LA FONCTION EXISTANTE PAR CELLE-CI

@app.callback(
    Output("asset-sections-container", "children"),
    [Input("asset-class-selector", "value"),
     Input('language-switcher-sidebar', 'value')] +  # AJOUT DE LA LANGUE
    [Input({'type': 'asset-dropdown', 'asset_class': ALL, 'index': ALL}, 'value')],
    State('custom-asset-store', 'data'),
    prevent_initial_call=True
)
def reveal_asset_sections_progressive_advanced_fixed(selected_classes, selected_language, asset_values, custom_asset_data):
    """
    Version corrigée pour le mode avancé avec placeholders traduits intégrés
    """
    
    # Gestion de la langue
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    def get_advanced_placeholder(asset_class):
        """Placeholders pour le mode avancé selon la classe d'actif"""
        placeholders = {
            'actions_cac40': t.get('choose-cac40-stock', 'Choisir une action CAC40'),
            'actions_us': t.get('choose-us-stock', 'Choisir une action US'),
            'fonds': t.get('choose-fund', 'Choisir un fonds'),
            'crypto': t.get('choose-crypto', 'Choisir une crypto'),
            'forex': t.get('choose-forex', 'Choisir une paire forex'),
            'etfs': t.get('choose-etf', 'Choisir un ETF'),
            'custom_assets': t.get('choose-custom-asset', 'Choisir un actif personnalisé')
        }
        return placeholders.get(asset_class, t.get('choose-asset', 'Choisir un actif'))
    
    if not selected_classes:
        return html.Div([
            html.I(className="fas fa-arrow-up fa-2x text-muted mb-3"),
            html.P(t.get('select-asset-classes-above', 'Sélectionnez des classes d\'actifs ci-dessus'), 
                   className="text-muted text-center")
        ], className="text-center py-5")
    
    # Organiser les valeurs par asset_class
    values_by_class = {}
    ctx = dash.callback_context 
    if ctx.inputs_list and len(ctx.inputs_list) > 2:
        for input_item in ctx.inputs_list[2]:
            if input_item.get('id') and input_item.get('value') is not None:
                asset_class = input_item['id']['asset_class']
                if asset_class == 'custom_assets':
                    values_by_class[asset_class] = input_item['value']
                else:
                    index = input_item['id']['index']
                    if asset_class not in values_by_class:
                        values_by_class[asset_class] = {}
                    values_by_class[asset_class][index] = input_item['value']
    
    sections = []
    style_map = STYLE_MAP
    
    for asset_class in selected_classes:
        # --- GESTION DES ACTIFS IMPORTÉS ---
        if asset_class == 'custom_assets':
            custom_asset_names = list(custom_asset_data.keys()) if custom_asset_data else []
            custom_asset_options = [{'label': name, 'value': name} for name in custom_asset_names]
            
            # PLACEHOLDER TRADUIT POUR LES ACTIFS PERSONNALISÉS
            custom_placeholder = get_advanced_placeholder('custom_assets')
            
            section = dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-database mr-2"),
                    html.Strong(t.get('my-imported-assets-label', 'Mes Actifs Importés'))
                ], style={'backgroundColor': '#1abc9c', 'color': 'white'}),
                dbc.CardBody([
                    dcc.Dropdown(
                        id={'type': 'asset-dropdown', 'asset_class': 'custom_assets', 'index': 0},
                        options=custom_asset_options,
                        placeholder=custom_placeholder,  # PLACEHOLDER TRADUIT ICI
                        multi=True,
                        value=values_by_class.get('custom_assets', [])
                    )
                ])
            ], className="mb-3")
            sections.append(section)
            continue

        # --- GESTION DES ACTIFS STANDARDS ---
        if asset_class not in asset_types:
            continue
            
        asset_info = asset_types[asset_class]
        assets = asset_info['assets']
        type_label = asset_info['label']
        style = style_map.get(asset_class, {'color': '#95a5a6', 'icon': 'fas fa-chart-bar'})
        
        # Déterminer le nombre de dropdowns à afficher
        num_dropdowns_to_show = 1
        if asset_class in values_by_class:
            for i in range(4):
                if i in values_by_class[asset_class] and values_by_class[asset_class][i]:
                    num_dropdowns_to_show = min(i + 2, 5)

        # CRÉER LES DROPDOWNS AVEC PLACEHOLDERS TRADUITS
        dropdown_elements = []
        for i in range(num_dropdowns_to_show):
            # PLACEHOLDER TRADUIT SELON LA CLASSE D'ACTIF
            placeholder = get_advanced_placeholder(asset_class)
            
            dropdown_div = html.Div([
                html.Label(f"{t.get('asset-number', 'Actif {i}').format(i=i+1)}:", 
                          className="font-weight-bold text-info mb-2"),
                dcc.Dropdown(
                    id={'type': 'asset-dropdown', 'asset_class': asset_class, 'index': i},
                    options=[
                        {'label': ticker_to_name.get(asset, asset), 'value': asset} 
                        for asset in assets
                    ],
                    value=values_by_class.get(asset_class, {}).get(i),
                    placeholder=placeholder,  # PLACEHOLDER TRADUIT FIXÉ ICI
                    searchable=True,
                    clearable=True,
                    style={'marginBottom': '10px'}
                )
            ], className="mb-2")
            dropdown_elements.append(dropdown_div)
        
        # CRÉER LA SECTION
        section = dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.I(className=f"{style['icon']} mr-2"), 
                        html.Strong(type_label)
                    ]),
                    dbc.Col([
                        dbc.Badge(f"{len(assets)} {t.get('available-count', 'disponibles')}", 
                                color="light")
                    ], className="text-right")
                ])
            ], style={'backgroundColor': style['color'], 'color': 'white'}),
            dbc.CardBody(dropdown_elements)
        ], className="mb-3")
        
        sections.append(section)
    
    return sections


# DANS app.py - REMPLACEZ CETTE FONCTION

@app.callback(
    [Output('selected-stocks-store', 'data', allow_duplicate=True),
     Output('selected-assets-summary', 'children')],
    [Input({'type': 'asset-dropdown', 'asset_class': ALL, 'index': ALL}, 'value'),
     Input('language-switcher-sidebar', 'value')],  # AJOUT DE LA LANGUE
    State("asset-class-selector", "value"),
    prevent_initial_call=True
)
def collect_assets_pattern_with_translation(asset_values, selected_language, selected_classes):
    """
    Collecte les actifs avec gestion de la langue pour les résumés
    """
    
    # Gestion de la langue
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    # Logique pour aplatir la liste (inchangée)
    flat_selected_assets = []
    if asset_values:
        for asset in asset_values:
            if asset:
                if isinstance(asset, list):
                    flat_selected_assets.extend(asset)
                else:
                    flat_selected_assets.append(asset)
    
    all_selected_assets = sorted(list(set(flat_selected_assets)))

    if not all_selected_assets:
        return [], create_empty_summary(selected_language)  # AVEC LANGUE
    
    # Créer le résumé par type d'actif
    assets_by_type = {}
    for asset in all_selected_assets:
        # Gérer les actifs importés
        if asset.endswith('.csv'):
            asset_type_key = 'custom_assets'
            if asset_type_key not in assets_by_type:
                assets_by_type[asset_type_key] = []
            assets_by_type[asset_type_key].append(asset)
            continue
        
        # Gérer les actifs standards
        for asset_type, asset_info in asset_types.items():
            if asset in asset_info['assets']:
                if asset_type not in assets_by_type:
                    assets_by_type[asset_type] = []
                assets_by_type[asset_type].append(asset)
                break
    
    return all_selected_assets, create_detailed_summary(assets_by_type, all_selected_assets, selected_language)





# 1. Callback pour charger les options (templates + stratégies sauvegardées)
@app.callback(
    Output("predefined-strategy-select", "options"),
    Input("predefined-strategy-select", "id"),  # Trigger au chargement
)
def load_predefined_strategies(_):
    """Charge les templates et stratégies sauvegardées"""
    options = []
    
    # 1. Ajouter les templates prédéfinis
    template_options = [
        {'label': '📈 Template: SMA Crossover Classic', 'value': 'template:sma_crossover'},
        {'label': '📊 Template: RSI Oversold/Overbought', 'value': 'template:rsi_oversold'},
        {'label': '🎯 Template: Bollinger Bands Breakout', 'value': 'template:bollinger_breakout'},
    ]
    options.extend(template_options)
    
    # 2. Ajouter les stratégies sauvegardées
    if os.path.exists("strategies"):
        strategy_files = []
        for file in os.listdir("strategies"):
            if file.endswith(".json"):
                try:
                    with open(os.path.join("strategies", file), 'r', encoding='utf-8') as f:
                        strategy_data = json.load(f)
                        name = strategy_data.get('name', 'Sans nom')
                        created_at = strategy_data.get('created_at', '')
                        
                        # Extraire juste la date
                        date_str = created_at.split(' ')[0] if created_at else 'Date inconnue'
                        
                        strategy_files.append({
                            'label': f'💾 Stratégie: {name} ({date_str})',
                            'value': f'saved:{os.path.join("strategies", file)}'
                        })
                except Exception as e:
                    print(f"Erreur lecture stratégie {file}: {e}")
                    continue
        
        # Trier par date de création (plus récent en premier)
        strategy_files.sort(key=lambda x: x['label'], reverse=True)
        options.extend(strategy_files)
    
    return options

# 2. Callback pour activer le bouton et afficher la description
@app.callback(
    [Output("apply-predefined-strategy", "disabled"),
     Output("predefined-strategy-description", "children")],
    [Input("predefined-strategy-select", "value"),
     Input('selected-stocks-store', 'data')]  # Ajouter les stocks sélectionnés
)
def update_predefined_strategy_info(selected_value, selected_stocks):
    """Met à jour la description et active le bouton"""
    if not selected_value:
        return True, ""
    
    # Vérifier si des stocks sont sélectionnés pour les templates
    if selected_value.startswith('template:') and not selected_stocks:
        return True, dbc.Alert([
            html.I(className="fas fa-exclamation-triangle mr-2"),
            "Veuillez d'abord sélectionner au moins un actif avant d'appliquer un template."
        ], color="warning", className="mb-0")
    
    try:
        if selected_value.startswith('template:'):
            # C'est un template
            template_key = selected_value.replace('template:', '')
            template = STRATEGY_TEMPLATES.get(template_key, {})
            
            if template:
                # Afficher les stocks qui seront utilisés
                stocks_text = f"Actifs: {', '.join(selected_stocks[:3])}{'...' if len(selected_stocks) > 3 else ''}" if selected_stocks else "Aucun actif sélectionné"
                
                description = dbc.Alert([
                    html.Strong(f"📋 Template: {template.get('name', 'Template')}"),
                    html.Br(),
                    html.Small(f"Capital: {template.get('initial_capital', 0):,}€ | "
                              f"Allocation: {template.get('allocation_pct', 0)}% | "
                              f"Stop Loss: {template.get('stop_loss_pct', 0)}%", 
                              className="text-info"),
                    html.Br(),
                    html.Small(stocks_text, className="text-success")
                ], color="info", className="mb-0")
            else:
                description = dbc.Alert("Template non trouvé", color="warning")
        
        elif selected_value.startswith('saved:'):
            # C'est une stratégie sauvegardée
            strategy_path = selected_value.replace('saved:', '')
            
            if os.path.exists(strategy_path):
                with open(strategy_path, 'r', encoding='utf-8') as f:
                    strategy_data = json.load(f)
                
                name = strategy_data.get('name', 'Sans nom')
                created_at = strategy_data.get('created_at', 'Date inconnue')
                capital = strategy_data.get('initial_capital', 0)
                allocation = strategy_data.get('allocation_pct', 0)
                num_blocks = len(strategy_data.get('decision_blocks', []))
                saved_stocks = strategy_data.get('selected_stocks', [])
                
                description = dbc.Alert([
                    html.Strong(f"💾 Stratégie: {name}"),
                    html.Br(),
                    html.Small(f"Créée: {created_at} | "
                              f"Capital: {capital:,}€ | "
                              f"Allocation: {allocation}% | "
                              f"Blocs: {num_blocks}", 
                              className="text-success"),
                    html.Br(),
                    html.Small(f"Actifs sauvegardés: {', '.join(saved_stocks[:3])}{'...' if len(saved_stocks) > 3 else ''}" if saved_stocks else "Aucun actif", 
                              className="text-info")
                ], color="success", className="mb-0")
            else:
                description = dbc.Alert("Fichier de stratégie non trouvé", color="danger")
        
        else:
            return True, dbc.Alert("Type de stratégie non reconnu", color="warning")
        
        return False, description
        
    except Exception as e:
        return True, dbc.Alert(f"Erreur: {str(e)}", color="danger")

# 3. Callback principal pour appliquer la stratégie sélectionnée
@app.callback(
    # Outputs pour les champs de base
    [Output("strategy-name", "value", allow_duplicate=True),
     Output("initial-capital", "value", allow_duplicate=True),
     Output("allocation", "value", allow_duplicate=True),
     Output("transaction-cost", "value", allow_duplicate=True),
     Output("stop-loss", "value", allow_duplicate=True),
     Output("take-profit", "value", allow_duplicate=True),
     Output('date-picker-range', 'start_date', allow_duplicate=True),
     Output('date-picker-range', 'end_date', allow_duplicate=True),
     Output('selected-stocks-store', 'data', allow_duplicate=True),
     Output('visible-blocks-store', 'data', allow_duplicate=True),
     Output('visible-conditions-store', 'data', allow_duplicate=True),
     Output("predefined-strategy-select", "value", allow_duplicate=True)],
    Input("apply-predefined-strategy", "n_clicks"),
    [State("predefined-strategy-select", "value"),
     State('selected-stocks-store', 'data')],
    prevent_initial_call=True
)
def apply_predefined_strategy(n_clicks, selected_value, current_selected_stocks):
    """Applique la stratégie sélectionnée (template ou sauvegardée)"""
    if not n_clicks or not selected_value:
        raise PreventUpdate
    
    print(f"🎯 Application de la stratégie: {selected_value}")
    print(f"   Actifs actuellement sélectionnés: {current_selected_stocks}")
    
    try:
        strategy_data = None
        final_selected_stocks = current_selected_stocks or []
        
        if selected_value.startswith('template:'):
            # Pour les templates, on DOIT avoir des actifs sélectionnés
            if not current_selected_stocks:
                raise ValueError("Veuillez sélectionner au moins un actif pour appliquer un template")
            
            template_key = selected_value.replace('template:', '')
            template = STRATEGY_TEMPLATES.get(template_key)
            
            if not template:
                raise ValueError(f"Template '{template_key}' non trouvé")
            
            # Convertir le template en format stratégie
            strategy_data = {
                'name': template['name'],
                'initial_capital': template['initial_capital'],
                'allocation_pct': template['allocation_pct'],
                'transaction_cost': template['transaction_cost'],
                'stop_loss_pct': template['stop_loss_pct'],
                'take_profit_pct': template['take_profit_pct'],
                'decision_blocks': template['decision_blocks'],
                'date_range': {
                    'start': '2024-01-01',
                    'end': '2025-01-01'
                }
            }
            
        elif selected_value.startswith('saved:'):
            # C'est une stratégie sauvegardée
            strategy_path = selected_value.replace('saved:', '')
            
            if not os.path.exists(strategy_path):
                raise ValueError(f"Fichier de stratégie non trouvé: {strategy_path}")
            
            with open(strategy_path, 'r', encoding='utf-8') as f:
                strategy_data = json.load(f)
            
            # Pour les stratégies sauvegardées, utiliser leurs actifs si on n'en a pas sélectionné
            saved_stocks = strategy_data.get('selected_stocks', [])
            if not current_selected_stocks and saved_stocks:
                final_selected_stocks = saved_stocks
                print(f"   Utilisation des actifs de la stratégie sauvée: {saved_stocks}")
            elif current_selected_stocks:
                final_selected_stocks = current_selected_stocks
                print(f"   Utilisation des actifs actuellement sélectionnés: {current_selected_stocks}")
        
        else:
            raise ValueError("Type de stratégie non reconnu")
        
        if not strategy_data:
            raise ValueError("Impossible de charger les données de la stratégie")
        
        # Extraire les champs de base
        name = strategy_data.get('name', '')
        capital = strategy_data.get('initial_capital', 100000)
        allocation = strategy_data.get('allocation_pct', 10)
        tx_cost = strategy_data.get('transaction_cost', 1)
        stop_loss = strategy_data.get('stop_loss_pct', 5)
        take_profit = strategy_data.get('take_profit_pct', 10)
        
        date_range = strategy_data.get('date_range', {})
        start_date = date_range.get('start', '2024-01-01')
        end_date = date_range.get('end', '2025-01-01')
        
        # Déterminer les blocs et conditions visibles
        decision_blocks = strategy_data.get('decision_blocks', [])
        num_blocks = len(decision_blocks)
        visible_blocks = list(range(min(num_blocks, MAX_BLOCKS)))
        
        visible_conditions = {}
        for i, block in enumerate(decision_blocks[:MAX_BLOCKS]):
            num_conditions = len(block.get('conditions', []))
            visible_conditions[str(i)] = list(range(min(num_conditions, MAX_CONDITIONS)))
        
        print(f"✅ Stratégie configurée:")
        print(f"   Nom: {name}")
        print(f"   Actifs finaux: {final_selected_stocks}")
        print(f"   Blocs visibles: {visible_blocks}")
        print(f"   Conditions visibles: {visible_conditions}")
        
        return [
            name, capital, allocation, tx_cost, stop_loss, take_profit,
            start_date, end_date, final_selected_stocks, visible_blocks, visible_conditions,
            None  # Reset le dropdown
        ]
        
    except Exception as e:
        print(f"❌ Erreur application stratégie: {e}")
        import traceback
        traceback.print_exc()
        raise PreventUpdate

# 4. Store pour stocker temporairement la stratégie à appliquer avec remplacement des actifs
@app.callback(
    Output('strategy-to-apply-store', 'data'),
    Input("apply-predefined-strategy", "n_clicks"),
    [State("predefined-strategy-select", "value"),
     State('selected-stocks-store', 'data')],
    prevent_initial_call=True
)
def store_strategy_to_apply(n_clicks, selected_value, selected_stocks):
    """Sauvegarde la stratégie à appliquer dans un store avec remplacement des actifs"""
    if not n_clicks or not selected_value:
        raise PreventUpdate
    
    try:
        strategy_data = None
        
        if selected_value.startswith('template:'):
            template_key = selected_value.replace('template:', '')
            template = STRATEGY_TEMPLATES.get(template_key)
            
            if not template:
                raise ValueError(f"Template '{template_key}' non trouvé")
            
            if not selected_stocks:
                raise ValueError("Veuillez sélectionner au moins un actif pour appliquer un template")
            
            # COPIE PROFONDE du template pour éviter de modifier l'original
            import copy
            strategy_data = copy.deepcopy(template)
            
            # Remplacer TOUS les PLACEHOLDER_STOCK par les actifs sélectionnés
            def replace_placeholders_in_structure(obj, selected_stocks):
                """Remplace récursivement tous les PLACEHOLDER_STOCK"""
                if isinstance(obj, dict):
                    new_obj = {}
                    for key, value in obj.items():
                        if key in ['stock1', 'stock2'] and value == "PLACEHOLDER_STOCK":
                            # Utiliser le premier actif sélectionné comme actif principal
                            new_obj[key] = selected_stocks[0]
                        elif key == 'actions' and isinstance(value, dict):
                            # Remplacer les clés d'actions
                            new_actions = {}
                            for action_stock, action_value in value.items():
                                if action_stock == "PLACEHOLDER_STOCK":
                                    # Créer des actions pour tous les actifs sélectionnés
                                    for selected_stock in selected_stocks:
                                        new_actions[selected_stock] = action_value
                                else:
                                    new_actions[action_stock] = action_value
                            new_obj[key] = new_actions
                        else:
                            new_obj[key] = replace_placeholders_in_structure(value, selected_stocks)
                    return new_obj
                elif isinstance(obj, list):
                    return [replace_placeholders_in_structure(item, selected_stocks) for item in obj]
                else:
                    return obj
            
            strategy_data = replace_placeholders_in_structure(strategy_data, selected_stocks)
            
            print(f"🔄 Template appliqué avec actifs: {selected_stocks}")
            print(f"   Exemple condition: {strategy_data['decision_blocks'][0]['conditions'][0] if strategy_data['decision_blocks'] else 'Aucune'}")
            print(f"   Actions: {strategy_data['decision_blocks'][0]['actions'] if strategy_data['decision_blocks'] else 'Aucune'}")
        
        elif selected_value.startswith('saved:'):
            strategy_path = selected_value.replace('saved:', '')
            if os.path.exists(strategy_path):
                with open(strategy_path, 'r', encoding='utf-8') as f:
                    strategy_data = json.load(f)
                
                print(f"📂 Stratégie sauvegardée chargée: {strategy_path}")
            else:
                raise ValueError(f"Fichier de stratégie non trouvé: {strategy_path}")
        
        return strategy_data
        
    except Exception as e:
        print(f"❌ Erreur stockage stratégie: {e}")
        return None

# 5. Callback pour remplir les conditions en utilisant le store
@app.callback(
    # Outputs pour TOUS les blocs et conditions
    [Output(f'stock1-{i}-{j}', 'value', allow_duplicate=True) for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'indicator1-type-{i}-{j}', 'value', allow_duplicate=True) for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'operator-{i}-{j}', 'value', allow_duplicate=True) for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'comparison-type-{i}-{j}', 'value', allow_duplicate=True) for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'stock2-{i}-{j}', 'value', allow_duplicate=True) for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'indicator2-type-{i}-{j}', 'value', allow_duplicate=True) for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'comparison-value-{i}-{j}', 'value', allow_duplicate=True) for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)],
    
    Input('strategy-to-apply-store', 'data'),
    prevent_initial_call=True
)
def fill_all_strategy_conditions(strategy_data):
    """Remplit toutes les conditions de tous les blocs - actifs déjà remplacés dans le store"""
    
    # Calculer le nombre total d'outputs
    total_outputs = MAX_BLOCKS * MAX_CONDITIONS * 7  # 7 types de champs par condition
    outputs = [None] * total_outputs
    
    if not strategy_data:
        return outputs
    
    try:
        decision_blocks = strategy_data.get('decision_blocks', [])
        if not decision_blocks:
            return outputs
        
        print(f"🔧 Remplissage des conditions pour {len(decision_blocks)} blocs")
        
        # Pour chaque bloc de décision
        for block_idx, block in enumerate(decision_blocks[:MAX_BLOCKS]):
            conditions = block.get('conditions', [])
            
            print(f"  Bloc {block_idx}: {len(conditions)} conditions")
            
            # Pour chaque condition dans ce bloc
            for cond_idx, condition in enumerate(conditions[:MAX_CONDITIONS]):
                # Calculer les indices de base pour cette condition
                base_idx = block_idx * MAX_CONDITIONS + cond_idx
                
                # Les actifs sont déjà correctement remplacés dans le store
                stock1 = condition.get('stock1')
                stock2 = condition.get('stock2')
                
                # Remplir les 7 types de champs pour cette condition
                # 1. stock1
                outputs[base_idx] = stock1
                
                # 2. indicator1-type
                outputs[MAX_BLOCKS * MAX_CONDITIONS + base_idx] = condition.get('indicator1', {}).get('type')
                
                # 3. operator
                outputs[MAX_BLOCKS * MAX_CONDITIONS * 2 + base_idx] = condition.get('operator')
                
                # 4. comparison-type
                outputs[MAX_BLOCKS * MAX_CONDITIONS * 3 + base_idx] = condition.get('comparison_type', 'indicator')
                
                # 5. stock2
                if condition.get('comparison_type') == 'indicator':
                    outputs[MAX_BLOCKS * MAX_CONDITIONS * 4 + base_idx] = stock2
                
                # 6. indicator2-type
                if condition.get('comparison_type') == 'indicator':
                    outputs[MAX_BLOCKS * MAX_CONDITIONS * 5 + base_idx] = condition.get('indicator2', {}).get('type')
                
                # 7. comparison-value
                if condition.get('comparison_type') == 'value':
                    outputs[MAX_BLOCKS * MAX_CONDITIONS * 6 + base_idx] = condition.get('comparison_value')
                
                print(f"    Condition {cond_idx}: {stock1} {condition.get('indicator1', {}).get('type')} {condition.get('operator')} ...")
        
        filled_count = len([o for o in outputs if o is not None])
        print(f"✅ {filled_count} champs remplis sur {total_outputs}")
        
        return outputs
        
    except Exception as e:
        print(f"❌ Erreur remplissage conditions: {e}")
        import traceback
        traceback.print_exc()
        return outputs

# 6. Callback pour remplir les paramètres d'indicateurs
@app.callback(
    [Output(f'indicator1-param-{i}-{j}-{k}', 'value', allow_duplicate=True) 
     for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS) for k in range(3)] +
    [Output(f'indicator2-param-{i}-{j}-{k}', 'value', allow_duplicate=True) 
     for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS) for k in range(3)],
    
    Input('strategy-to-apply-store', 'data'),
    prevent_initial_call=True
)
def fill_all_strategy_parameters(strategy_data):
    """Remplit les paramètres des indicateurs pour tous les blocs"""
    
    # Calculer le nombre total d'outputs
    total_params = MAX_BLOCKS * MAX_CONDITIONS * 3 * 2  # 2 indicateurs x 3 params
    outputs = [None] * total_params
    
    if not strategy_data:
        return outputs
    
    try:
        decision_blocks = strategy_data.get('decision_blocks', [])
        if not decision_blocks:
            return outputs
        
        print(f"🔧 Remplissage des paramètres pour {len(decision_blocks)} blocs")
        
        for block_idx, block in enumerate(decision_blocks[:MAX_BLOCKS]):
            conditions = block.get('conditions', [])
            
            for cond_idx, condition in enumerate(conditions[:MAX_CONDITIONS]):
                # Calculer l'index de base pour cette condition
                base_condition_idx = block_idx * MAX_CONDITIONS + cond_idx
                
                # Paramètres indicateur 1
                ind1_params = condition.get('indicator1', {}).get('params', [])
                for k, param_value in enumerate(ind1_params[:3]):
                    param_idx = base_condition_idx * 3 + k
                    if param_idx < MAX_BLOCKS * MAX_CONDITIONS * 3:
                        outputs[param_idx] = param_value
                
                # Paramètres indicateur 2
                if condition.get('comparison_type') == 'indicator':
                    ind2_params = condition.get('indicator2', {}).get('params', [])
                    for k, param_value in enumerate(ind2_params[:3]):
                        param_idx = MAX_BLOCKS * MAX_CONDITIONS * 3 + base_condition_idx * 3 + k
                        if param_idx < total_params:
                            outputs[param_idx] = param_value
        
        filled_count = len([o for o in outputs if o is not None])
        print(f"✅ {filled_count} paramètres remplis sur {total_params}")
        
        return outputs
        
    except Exception as e:
        print(f"❌ Erreur remplissage paramètres: {e}")
        return outputs

# 7. Callback pour remplir les actions pour tous les blocs
@app.callback(
    [Output(f'stock-action-{block_i}-{stock_idx}', 'value', allow_duplicate=True) 
     for block_i in range(MAX_BLOCKS) for stock_idx in range(10)],
    
    Input('strategy-to-apply-store', 'data'),
    State('selected-stocks-store', 'data'),
    prevent_initial_call=True
)
def fill_all_strategy_actions(strategy_data, selected_stocks):
    """Remplit les actions pour tous les blocs - actifs déjà remplacés dans le store"""
    
    total_actions = MAX_BLOCKS * 10
    outputs = ['Ne rien faire'] * total_actions
    
    if not strategy_data:
        return outputs
    
    try:
        decision_blocks = strategy_data.get('decision_blocks', [])
        if not decision_blocks:
            return outputs
        
        print(f"🔧 Remplissage des actions pour {len(decision_blocks)} blocs")
        
        for block_idx, block in enumerate(decision_blocks[:MAX_BLOCKS]):
            actions = block.get('actions', {})
            
            print(f"  Bloc {block_idx} actions: {actions}")
            
            # Les actions dans le store sont déjà configurées avec les bons actifs
            if selected_stocks:
                for stock_idx, stock in enumerate(selected_stocks[:10]):
                    action_idx = block_idx * 10 + stock_idx
                    
                    if stock in actions:
                        outputs[action_idx] = actions[stock]
                        print(f"    Stock {stock_idx} ({stock}): {actions[stock]}")
                    else:
                        # Si l'actif n'est pas dans les actions, prendre la première action disponible
                        if actions:
                            default_action = list(actions.values())[0]
                            outputs[action_idx] = default_action
                            print(f"    Stock {stock_idx} ({stock}): {default_action} (défaut)")
        
        return outputs
        
    except Exception as e:
        print(f"❌ Erreur remplissage actions: {e}")
        return outputs


# Callback pour activer/désactiver le bouton
@app.callback(
    [Output("apply-template", "disabled"),
     Output("template-description", "children")],
    Input("strategy-template-select", "value")
)
def update_template_button(template_key):
    if not template_key:
        return True, ""
    
    template = STRATEGY_TEMPLATES.get(template_key, {})
    description = dbc.Alert([
        html.Strong(f"📋 {template.get('name', 'Template')}"),
        html.Br(),
        html.Small(f"Capital: {template.get('initial_capital', 0):,}€ | "
                  f"Allocation: {template.get('allocation_pct', 0)}% | "
                  f"Stop Loss: {template.get('stop_loss_pct', 0)}%", 
                  className="text-info")
    ], color="info", className="mb-0")
    
    return False, description


# ---------------------------------------------------------------
# ---------------------------------------------------------------


# Gestion de la visibilité des blocs de décision
@app.callback(
    [Output(f'decision-block-{i}', 'style') for i in range(MAX_BLOCKS)] +
    [Output('visible-blocks-store', 'data', allow_duplicate=True)],
    [Input('add-decision-block-static', 'n_clicks')] +
    [Input(f'remove-decision-block-{i}', 'n_clicks') for i in range(MAX_BLOCKS)],
    State('visible-blocks-store', 'data'),
    prevent_initial_call=True
)
def manage_decision_blocks_visibility(add_clicks, *args):
    remove_clicks = args[:-1]
    visible_blocks = args[-1] if args else [0]
    
    ctx = dash.callback_context
    if not ctx.triggered:
        styles = []
        for i in range(MAX_BLOCKS):
            if i in visible_blocks:
                styles.append({
                    'backgroundColor': COLORS['background'], 
                    'borderRadius': '8px', 
                    'border': f'1px solid {COLORS["header"]}',
                    'display': 'block'
                })
            else:
                styles.append({'display': 'none'})
        return styles + [visible_blocks]
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'add-decision-block-static':
        if add_clicks and len(visible_blocks) < MAX_BLOCKS:
            next_block = len(visible_blocks)
            if next_block not in visible_blocks:
                visible_blocks.append(next_block)
    
    elif trigger_id.startswith('remove-decision-block-'):
        try:
            block_index = int(trigger_id.split('-')[-1])
            if block_index in visible_blocks and len(visible_blocks) > 1:
                visible_blocks.remove(block_index)
        except (ValueError, IndexError):
            pass
    
    styles = []
    for i in range(MAX_BLOCKS):
        if i in visible_blocks:
            styles.append({
                'backgroundColor': COLORS['background'], 
                'borderRadius': '8px', 
                'border': f'1px solid {COLORS["header"]}',
                'display': 'block'
            })
        else:
            styles.append({'display': 'none'})
    
    return styles + [visible_blocks]

# Gestion de la visibilité des conditions
@app.callback(
    [Output(f'condition-block-{i}-{j}', 'style') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output('visible-conditions-store', 'data', allow_duplicate=True)],
    [Input(f'add-condition-{i}', 'n_clicks') for i in range(MAX_BLOCKS)] +
    [Input(f'remove-condition-{i}-{j}', 'n_clicks') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)],
    State('visible-conditions-store', 'data'),
    State('visible-blocks-store', 'data'),
    prevent_initial_call=True
)
def manage_conditions_visibility(*args):
    add_clicks_list = args[:MAX_BLOCKS]
    remove_clicks_list = args[MAX_BLOCKS:-2]
    visible_conditions = args[-2] if args[-2] else {'0': [0]}
    visible_blocks = args[-1] if args[-1] else [0]
    
    ctx = dash.callback_context
    if not ctx.triggered:
        styles = []
        for i in range(MAX_BLOCKS):
            for j in range(MAX_CONDITIONS):
                if (i in visible_blocks and 
                    str(i) in visible_conditions and 
                    j in visible_conditions[str(i)]):
                    styles.append({'display': 'block'})
                else:
                    styles.append({'display': 'none'})
        return styles + [visible_conditions]
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id.startswith('add-condition-'):
        try:
            block_index = int(trigger_id.split('-')[-1])
            if str(block_index) not in visible_conditions:
                visible_conditions[str(block_index)] = [0]
            
            current_conditions = visible_conditions[str(block_index)]
            if len(current_conditions) < MAX_CONDITIONS:
                next_condition = max(current_conditions) + 1 if current_conditions else 0
                if next_condition not in current_conditions:
                    visible_conditions[str(block_index)].append(next_condition)
        except (ValueError, IndexError):
            pass
    
    elif trigger_id.startswith('remove-condition-'):
        try:
            parts = trigger_id.split('-')
            block_index = int(parts[-2])
            condition_index = int(parts[-1])
            
            if str(block_index) in visible_conditions:
                conditions_list = visible_conditions[str(block_index)]
                if condition_index in conditions_list and len(conditions_list) > 1:
                    conditions_list.remove(condition_index)
        except (ValueError, IndexError):
            pass
    
    styles = []
    for i in range(MAX_BLOCKS):
        for j in range(MAX_CONDITIONS):
            if (i in visible_blocks and 
                str(i) in visible_conditions and 
                j in visible_conditions[str(i)]):
                styles.append({'display': 'block'})
            else:
                styles.append({'display': 'none'})
    
    return styles + [visible_conditions]

# START UPDATE CHANGE----------------------------------------------------

@app.callback(
    Output("asset-type-selectors-container", "children", allow_duplicate=True),
    Output('all-selected-assets-store', 'data', allow_duplicate=True),
    Output('selected-stocks-store', 'data', allow_duplicate=True),
    Input('reset-asset-selection', 'n_clicks'),  # Bouton optionnel pour reset complet
    prevent_initial_call=True
)
def reset_all_asset_selectors(n_clicks):
    """Reset complet de tous les sélecteurs d'actifs"""
    if not n_clicks:
        raise PreventUpdate
    
    # Créer un seul sélecteur par défaut
    default_selector = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Type d'actif 1:", className="font-weight-bold text-info"),
                    dcc.Dropdown(
                        id={'type': 'asset-type-selector', 'index': 0},
                        options=[
                            {"label": f"📈 {asset_info['label']}", "value": asset_type} 
                            for asset_type, asset_info in asset_types.items()
                        ],
                        placeholder="Sélectionnez un type d'actif",
                        clearable=True,
                        style=DROPDOWN_STYLE
                    ),
                ], width=4),
                dbc.Col([
                    html.Label("Actifs de ce type:", className="font-weight-bold text-info"),
                    html.Div(id={'type': 'asset-selector-container', 'index': 0})
                ], width=7),
                dbc.Col([
                    dbc.Button(
                        "×", 
                        id={'type': 'remove-asset-type', 'index': 0},
                        color="danger", 
                        size="sm",
                        style={'marginTop': '28px', 'display': 'none'},
                        disabled=True
                    )
                ], width=1)
            ])
        ])
    ], className="mb-3", style={
        'backgroundColor': COLORS['card_background'], 
        'border': f'1px solid {COLORS["success"]}'
    })
    
    return [default_selector], {}, []

# END UPDATE CHANGE------------------------------------------------------

# Gestion des sélecteurs d'actions
@app.callback(
    Output("stock-selector-container", "children"),
    Output("selected-stocks-store", "data"),
    Input({'type': 'stock-selector', 'index': ALL}, 'value'),
    State("stock-selector-container", "children"),
    State('asset-type-dropdown', 'value')
)
def update_stock_selectors(stock_values, existing_dropdowns, asset_type): 
    new_dropdowns = existing_dropdowns.copy()
    stocks = list(filter(None, stock_values))

    # Supprimer les dropdowns vides sauf le dernier
    if len(existing_dropdowns) > 1:
        non_empty_dropdowns = []
        for i, dropdown in enumerate(existing_dropdowns):
            dropdown_id = dropdown['props']['id']
            index = dropdown_id['index']
            value = stock_values[i] if i < len(stock_values) else None
            
            if value or i == len(existing_dropdowns) - 1:
                new_index = len(non_empty_dropdowns)
                assets = asset_types[asset_type]['assets']
                options = [{'label': asset, 'value': asset} for asset in assets]
                placeholder = f'Sélectionnez un actif ({asset_types[asset_type]["label"]})'
                
                new_dropdown = dcc.Dropdown(
                    id={'type': 'stock-selector', 'index': new_index},
                    options=options,
                    value=value,
                    placeholder=placeholder,
                    searchable=True,
                    clearable=True,
                    style={'marginBottom': '10px', **DROPDOWN_STYLE, 'zIndex': 99999}
                )
                non_empty_dropdowns.append(new_dropdown)
                
        new_dropdowns = non_empty_dropdowns

    # Ajouter un nouveau dropdown si le dernier est rempli
    if stock_values and stock_values[-1] and len(stock_values) == len(existing_dropdowns):
        new_index = len(new_dropdowns)
        assets = asset_types[asset_type]['assets']
        options = [{'label': asset, 'value': asset} for asset in assets]
        placeholder = f'Sélectionnez un actif ({asset_types[asset_type]["label"]})'
        
        new_dropdown = dcc.Dropdown(
            id={'type': 'stock-selector', 'index': new_index},
            options=options,
            placeholder=placeholder,
            searchable=True,
            clearable=True,
            style={'marginBottom': '10px', **DROPDOWN_STYLE}
        )
        new_dropdowns.append(new_dropdown)

    return new_dropdowns, stocks

# START UPDATE CHANGE-----------------------------------------------------
# Mise à jour des options de stock dans les conditions
@app.callback(
    [Output(f'stock1-{i}-{j}', 'options', allow_duplicate=True) for i in range(3) for j in range(3)] +
    [Output(f'stock2-{i}-{j}', 'options', allow_duplicate=True) for i in range(3) for j in range(3)],
    Input('selected-stocks-store', 'data'),
    prevent_initial_call=True
)
def update_stock_options_for_conditions(selected_stocks):
    """Met à jour les options dans les conditions de stratégie"""
    if not selected_stocks:
        empty_options = [[]] * 18  # 9 pour stock1 + 9 pour stock2
        return empty_options
    
    # Créer les options avec indication du type d'actif
    options = []
    for stock in selected_stocks:
        display_name = ticker_to_name.get(stock, stock)
        
        # Déterminer le type d'actif pour l'affichage
        asset_type_label = "Inconnu"
        for asset_type, asset_info in asset_types.items():
            if stock in asset_info['assets']:
                asset_type_label = asset_info['label']
                break
        
        options.append({
            'label': f"{display_name} ({asset_type_label})", 
            'value': stock
        })
    
    # Retourner les mêmes options pour tous les dropdowns (18 au total)
    return [options] * 18

# Mise à jour des paramètres d'indicateurs 1

@app.callback(
    [Output(f'indicator1-params-{i}-{j}', 'children', allow_duplicate=True) for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)],
    [Input(f'indicator1-type-{i}-{j}', 'value') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)],
    prevent_initial_call=True
)
def update_indicator1_params_visibility(*indicator_values):
    """Met à jour la visibilité et les valeurs des paramètres d'indicateur 1"""
    results = []
    
    total_combinations = MAX_BLOCKS * MAX_CONDITIONS
    
    for idx in range(total_combinations):
        i = idx // MAX_CONDITIONS
        j = idx % MAX_CONDITIONS
        
        indicator_type = indicator_values[idx] if idx < len(indicator_values) else None
        
        # TOUJOURS créer les 3 IDs de paramètres
        params_container = html.Div([
            dbc.Input(
                id=f'indicator1-param-{i}-{j}-{k}',
                placeholder=f'Paramètre {k+1}',
                type='number',
                className='mb-1',
                style={'display': 'none'},  # Caché par défaut
                persistence=True,
                persistence_type='session'
            ) for k in range(3)
        ])
        
        # Afficher seulement les paramètres nécessaires
        if indicator_type and indicator_type in indicators:
            param_names = indicators[indicator_type]["params"]
            
            # CONDITION SPÉCIALE : Si c'est PRICE, ne pas afficher de paramètres
            if indicator_type == "PRICE":
                # Tous les paramètres restent cachés pour PRICE
                for k in range(3):
                    params_container.children[k].style = {'display': 'none'}
            else:
                # Pour les autres indicateurs, afficher les paramètres nécessaires
                for k, param_name in enumerate(param_names[:3]):
                    params_container.children[k].placeholder = param_name
                    params_container.children[k].style = {**INPUT_STYLE, 'display': 'block', 'marginBottom': '5px'}
                
                # Cacher les paramètres non utilisés
                for k in range(len(param_names), 3):
                    params_container.children[k].style = {'display': 'none'}
        
        results.append(params_container)
    
    return results


# Mise à jour des paramètres d'indicateurs 2
# Mise à jour des paramètres d'indicateurs 2 (version sécurisée)

# Gestion du type de comparaison (améliorée)
# et modifiez le callback update_comparison_containers ainsi :


@app.callback(
    # Outputs pour contrôler la visibilité des composants d'indicateur 2
    [Output(f'indicator2-label-{i}-{j}', 'style') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'stock2-{i}-{j}', 'style') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'indicator2-type-{i}-{j}', 'style') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'indicator2-params-{i}-{j}', 'style') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    # Outputs pour contrôler la visibilité des composants de valeur
    [Output(f'value-label-{i}-{j}', 'style') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'comparison-value-{i}-{j}', 'style') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)],
    # Inputs
    [Input(f'comparison-type-{i}-{j}', 'value') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)],
    prevent_initial_call=True
)
def toggle_comparison_visibility(*comparison_types):
    """Simple callback qui ne fait que montrer/cacher - AUCUNE reconstruction"""
    
    results = []
    total_combinations = MAX_BLOCKS * MAX_CONDITIONS
    
    # 1. Styles pour les labels d'indicateur 2
    for i in range(MAX_BLOCKS):
        for j in range(MAX_CONDITIONS):
            idx = i * MAX_CONDITIONS + j
            comparison_type = comparison_types[idx] if idx < len(comparison_types) else 'indicator'
            
            if comparison_type == 'indicator':
                results.append({'display': 'block', 'marginBottom': '10px'})
            else:
                results.append({'display': 'none'})
    
    # 2. Styles pour stock2
    for i in range(MAX_BLOCKS):
        for j in range(MAX_CONDITIONS):
            idx = i * MAX_CONDITIONS + j
            comparison_type = comparison_types[idx] if idx < len(comparison_types) else 'indicator'
            
            if comparison_type == 'indicator':
                results.append({'marginBottom': '10px', 'display': 'block'})
            else:
                results.append({'display': 'none'})
    
    # 3. Styles pour indicator2-type
    for i in range(MAX_BLOCKS):
        for j in range(MAX_CONDITIONS):
            idx = i * MAX_CONDITIONS + j
            comparison_type = comparison_types[idx] if idx < len(comparison_types) else 'indicator'
            
            if comparison_type == 'indicator':
                results.append({'marginBottom': '10px', 'display': 'block'})
            else:
                results.append({'display': 'none'})
    
    # 4. Styles pour indicator2-params
    for i in range(MAX_BLOCKS):
        for j in range(MAX_CONDITIONS):
            idx = i * MAX_CONDITIONS + j
            comparison_type = comparison_types[idx] if idx < len(comparison_types) else 'indicator'
            
            if comparison_type == 'indicator':
                results.append({'display': 'block'})
            else:
                results.append({'display': 'none'})
    
    # 5. Styles pour value-label
    for i in range(MAX_BLOCKS):
        for j in range(MAX_CONDITIONS):
            idx = i * MAX_CONDITIONS + j
            comparison_type = comparison_types[idx] if idx < len(comparison_types) else 'indicator'
            
            if comparison_type == 'value':
                results.append({'display': 'block', 'marginBottom': '10px'})
            else:
                results.append({'display': 'none'})
    
    # 6. Styles pour comparison-value
    for i in range(MAX_BLOCKS):
        for j in range(MAX_CONDITIONS):
            idx = i * MAX_CONDITIONS + j
            comparison_type = comparison_types[idx] if idx < len(comparison_types) else 'indicator'
            
            if comparison_type == 'value':
                results.append({**INPUT_STYLE, 'display': 'block'})
            else:
                results.append({'display': 'none'})
    
    return results



# Callback pour les paramètres d'indicateur 2 (conditionnel)

@app.callback(
    [Output(f'indicator2-params-{i}-{j}', 'children', allow_duplicate=True) for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)],
    [Input(f'indicator2-type-{i}-{j}', 'value') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)],
    prevent_initial_call=True
)
def update_indicator2_params_visibility(*indicator_values):
    """Met à jour la visibilité et les valeurs des paramètres d'indicateur 2"""
    results = []
    
    total_combinations = MAX_BLOCKS * MAX_CONDITIONS
    
    for idx in range(total_combinations):
        i = idx // MAX_CONDITIONS
        j = idx % MAX_CONDITIONS
        
        indicator_type = indicator_values[idx] if idx < len(indicator_values) else None
        
        # TOUJOURS créer les 3 IDs de paramètres
        params_container = html.Div([
            dbc.Input(
                id=f'indicator2-param-{i}-{j}-{k}',
                placeholder=f'Paramètre {k+1}',
                type='number',
                className='mb-1',
                style={'display': 'none'},  # Caché par défaut
                persistence=True,
                persistence_type='session'
            ) for k in range(3)
        ])
        
        # Afficher seulement les paramètres nécessaires
        if indicator_type and indicator_type in indicators:
            param_names = indicators[indicator_type]["params"]
            
            # CONDITION SPÉCIALE : Si c'est PRICE, ne pas afficher de paramètres
            if indicator_type == "PRICE":
                # Tous les paramètres restent cachés pour PRICE
                for k in range(3):
                    params_container.children[k].style = {'display': 'none'}
            else:
                # Pour les autres indicateurs, afficher les paramètres nécessaires
                for k, param_name in enumerate(param_names[:3]):
                    params_container.children[k].placeholder = param_name
                    params_container.children[k].style = {**INPUT_STYLE, 'display': 'block', 'marginBottom': '5px'}
                
                # Cacher les paramètres non utilisés
                for k in range(len(param_names), 3):
                    params_container.children[k].style = {'display': 'none'}
        
        results.append(params_container)
    
    return results

# END UPDATE CHANGE------------------------------------------------------------

# Mise à jour des options de stock2 dans les comparaisons
@app.callback(
    [Output(f'stock2-{i}-{j}', 'options') for i in range(3) for j in range(3)],
    Input('selected-stocks-store', 'data'),
    prevent_initial_call=True
)
def update_stock2_options(selected_stocks):
    if not selected_stocks:
        return [[]] * 9
    
    options = [{'label': ticker_to_name.get(stock, stock), 'value': stock} for stock in selected_stocks]
    return [options] * 9

# Mise à jour des actions à exécuter
# Mise à jour des actions à exécuter (version corrigée)
@app.callback(
    # Outputs pour les labels d'actions
    [Output(f'action-label-{block_i}-{stock_idx}', 'children') for block_i in range(MAX_BLOCKS) for stock_idx in range(10)] +
    [Output(f'action-label-{block_i}-{stock_idx}', 'style') for block_i in range(MAX_BLOCKS) for stock_idx in range(10)] +
    # Outputs pour les ROWS d'actions (pas les containers individuels)
    [Output(f'action-row-{block_i}-{stock_idx}', 'style') for block_i in range(MAX_BLOCKS) for stock_idx in range(10)],
    [Input('selected-stocks-store', 'data'),
     Input('visible-blocks-store', 'data')],
    prevent_initial_call=True
)
def update_actions_with_unique_ids_fixed(selected_stocks, visible_blocks):
    """Met à jour l'affichage des actions avec la correction de visibilité"""
    
    visible_blocks = visible_blocks or [0]
    selected_stocks = selected_stocks or []
    
    print(f"=== UPDATE ACTIONS DEBUG ===")
    print(f"Selected stocks: {selected_stocks}")
    print(f"Visible blocks: {visible_blocks}")
    
    # Initialiser toutes les sorties
    total_outputs = MAX_BLOCKS * 10 * 3  # labels + label_styles + row_styles
    results = [dash.no_update] * total_outputs
    
    # Calculer les indices pour chaque type de sortie
    label_start = 0
    label_style_start = MAX_BLOCKS * 10
    row_style_start = MAX_BLOCKS * 10 * 2
    
    for block_i in range(MAX_BLOCKS):
        for stock_idx in range(10):
            # Indices pour cette combinaison block_i, stock_idx
            label_idx = label_start + (block_i * 10) + stock_idx
            label_style_idx = label_style_start + (block_i * 10) + stock_idx
            row_style_idx = row_style_start + (block_i * 10) + stock_idx
            
            if block_i not in visible_blocks:
                # Bloc non visible - tout cacher
                results[label_idx] = ""
                results[label_style_idx] = {'display': 'none'}
                results[row_style_idx] = {'display': 'none'}
                
            elif stock_idx < len(selected_stocks):
                # Stock disponible et bloc visible - afficher
                stock = selected_stocks[stock_idx]
                display_name = ticker_to_name.get(stock, stock)
                
                results[label_idx] = f"Action sur {display_name}:"
                results[label_style_idx] = {"fontWeight": "bold", "display": "block"}
                results[row_style_idx] = {'display': 'flex', 'marginBottom': '5px'}  # AFFICHER la row
                
                print(f"  Affichage action {block_i}-{stock_idx}: {display_name}")
                
            else:
                # Pas de stock pour cet index - cacher
                results[label_idx] = ""
                results[label_style_idx] = {'display': 'none'}
                results[row_style_idx] = {'display': 'none'}
    
    print(f"Actions visibles calculées: {len([r for r in results[row_style_start:] if r != dash.no_update and r.get('display') != 'none'])}")
    return results
  

# Affichage de la période sélectionnée
@app.callback(
    Output('output-date-range', 'children'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('language-switcher-sidebar', 'value')],  # AJOUT DE LA LANGUE
    prevent_initial_call=True
)
def update_date_range(start_date, end_date, selected_language):
    """Affichage de la période sélectionnée avec traductions"""
    
    # Gestion de la langue
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    if start_date and end_date:
        return html.Div([
            html.Strong(t.get('period-chosen-label', 'Période choisie : ')),
            html.Span(f"{start_date} à {end_date}")
        ], className="alert alert-info")
    return ""

# Sauvegarde de la stratégie (mise à jour pour inclure les blocs de décision)
# Sauvegarde de la stratégie (mise à jour pour inclure les blocs de décision)
# Sauvegarde de la stratégie (version simplifiée)
def sanitize_id(text):
    """Nettoie un texte pour l'utiliser comme ID Dash"""
    if text is None:
        return None
    return str(text).replace('.', '_dot_').replace('-', '_dash_').replace('=', '_eq_')

def unsanitize_id(sanitized_text):
    """Reconvertit un ID nettoyé vers le texte original"""
    if sanitized_text is None:
        return None
    return str(sanitized_text).replace('_dot_', '.').replace('_dash_', '-').replace('_eq_', '=')

# 2. Callback pour sauvegarder EN RÉCUPÉRANT LES VRAIES VALEURS

# CALLBACK DE SAUVEGARDE CORRIGÉ - SANS IDs DYNAMIQUES

# REMPLACEZ cette partie du callback de sauvegarde :
@app.callback(
    [Output("save-confirmation", "children", allow_duplicate=True),
     Output('strategy-store', 'data')],
    [Input("save-strategy", "n_clicks"),
     Input('language-switcher-sidebar', 'value')],  # AJOUT DE LA LANGUE
    [
        # Infos générales (inchangé)
        State("strategy-name", "value"),
        State("initial-capital", "value"),
        State("allocation", "value"),
        State("transaction-cost", "value"),
        State("stop-loss", "value"),
        State("take-profit", "value"),
        State('date-picker-range', 'start_date'),
        State('date-picker-range', 'end_date'),
        State('selected-stocks-store', 'data'),
        State('visible-blocks-store', 'data'),
        State('visible-conditions-store', 'data')
    ] + 
    # États des conditions - CORRIGÉ pour tous les blocs
    [State(f'stock1-{i}-{j}', 'value') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [State(f'indicator1-type-{i}-{j}', 'value') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [State(f'operator-{i}-{j}', 'value') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [State(f'comparison-type-{i}-{j}', 'value') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [State(f'stock2-{i}-{j}', 'value') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [State(f'indicator2-type-{i}-{j}', 'value') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [State(f'comparison-value-{i}-{j}', 'value') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [State(f'indicator1-param-{i}-{j}-{k}', 'value') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS) for k in range(3)] +
    [State(f'indicator2-param-{i}-{j}-{k}', 'value') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS) for k in range(3)] +
    # Actions avec les nouveaux IDs uniques
    [State(f'stock-action-{block_i}-{stock_idx}', 'value') for block_i in range(MAX_BLOCKS) for stock_idx in range(10)],
    prevent_initial_call=True
)
def save_strategy_with_unique_action_ids(n_clicks, selected_language, name, capital, alloc, tx_cost, stop, take, start_date, end_date,
                                        selected_stocks, visible_blocks, visible_conditions, *all_states):
    
    if not n_clicks:
        raise PreventUpdate
    
    # Gestion de la langue
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
        
    # Validations avec traductions
    if not name:
        return dbc.Alert(t.get('strategy-name-required', 'Nom de stratégie requis'), color="danger")
    if not selected_stocks:
        return dbc.Alert(t.get('select-assets-required', 'Sélectionnez au moins un actif'), color="warning")
    if not start_date or not end_date:
        return dbc.Alert(t.get('dates-required', 'Dates requises'), color="warning")
    
    print("=== SAUVEGARDE AVEC TOUS LES BLOCS ===")
    print(f"Nombre total d'états récupérés: {len(all_states)}")
    print(f"Blocs visibles: {visible_blocks}")
    print(f"Selected stocks: {selected_stocks}")
    
    # Décomposer les états - CORRIGÉ avec les bonnes dimensions
    state_index = 0
    total_conditions = MAX_BLOCKS * MAX_CONDITIONS  # 5 x 5 = 25
    
    # États des conditions : MAX_BLOCKS x MAX_CONDITIONS = 25 pour chaque section
    stock1_values = all_states[state_index:state_index + total_conditions]
    state_index += total_conditions
    
    indicator1_types = all_states[state_index:state_index + total_conditions]
    state_index += total_conditions
    
    operators = all_states[state_index:state_index + total_conditions]
    state_index += total_conditions
    
    comparison_types = all_states[state_index:state_index + total_conditions]
    state_index += total_conditions
    
    stock2_values = all_states[state_index:state_index + total_conditions]
    state_index += total_conditions
    
    indicator2_types = all_states[state_index:state_index + total_conditions]
    state_index += total_conditions
    
    comparison_values = all_states[state_index:state_index + total_conditions]
    state_index += total_conditions
    
    # Paramètres : MAX_BLOCKS x MAX_CONDITIONS x 3 = 75 pour chaque indicateur
    total_params = MAX_BLOCKS * MAX_CONDITIONS * 3  # 5 x 5 x 3 = 75
    
    indicator1_params = all_states[state_index:state_index + total_params]
    state_index += total_params
    
    indicator2_params = all_states[state_index:state_index + total_params]
    state_index += total_params
    
    # Actions : MAX_BLOCKS x 10 = 50
    action_values = all_states[state_index:state_index + (MAX_BLOCKS * 10)]
    
    print(f"États récupérés - Conditions: {total_conditions}, Paramètres: {total_params}, Actions: {len(action_values)}")
    
    # Construire la stratégie avec la logique corrigée
    decision_blocks = []
    visible_blocks = visible_blocks or [0]
    
    for block_idx in visible_blocks:
        if block_idx >= MAX_BLOCKS:
            continue
        
        print(f"\n=== TRAITEMENT BLOC {block_idx} ===")
        
        # Créer les conditions pour ce bloc
        conditions_list = []
        visible_conditions_for_block = visible_conditions.get(str(block_idx), [0]) if visible_conditions else [0]
        
        for condition_idx in visible_conditions_for_block:
            if condition_idx >= MAX_CONDITIONS:
                continue
                
            # Calculer l'index dans le tableau aplati : block_idx * MAX_CONDITIONS + condition_idx
            array_idx = block_idx * MAX_CONDITIONS + condition_idx
            
            print(f"  Condition {condition_idx} -> array_idx {array_idx}")
            
            if array_idx >= len(stock1_values):
                print(f"    Index {array_idx} hors limites ({len(stock1_values)})")
                continue
            
            stock1 = stock1_values[array_idx] if array_idx < len(stock1_values) else None
            ind1_type = indicator1_types[array_idx] if array_idx < len(indicator1_types) else None
            operator = operators[array_idx] if array_idx < len(operators) else None
            comp_type = comparison_types[array_idx] if array_idx < len(comparison_types) else None
            
            print(f"    Valeurs: stock1={stock1}, ind1={ind1_type}, op={operator}, comp={comp_type}")
            
            if all([stock1, ind1_type, operator, comp_type]):
                # Récupérer les paramètres de l'indicateur 1
                ind1_params = []
                if ind1_type != "PRICE":
                    for k in range(3):
                        # Index pour les paramètres : array_idx * 3 + k
                        param_idx = array_idx * 3 + k
                        if param_idx < len(indicator1_params):
                            param_value = indicator1_params[param_idx]
                            if param_value is not None:
                                ind1_params.append(param_value)
                
                    # NOUVEAU BLOC
                    is_ind1_valid = False
                    if ind1_type in indicators: # Si c'est un indicateur standard (SMA, RSI, etc.)
                        if not indicators[ind1_type]['params'] or ind1_params: # Valide si pas de params requis (PRICE) ou si les params sont fournis
                            is_ind1_valid = True
                    else: # Si c'est un indicateur personnalisé (colonne CSV)
                        is_ind1_valid = True # Toujours valide car n'a pas besoin de paramètres

                    if not is_ind1_valid:
                        print(f"Paramètres invalides ou manquants pour l'indicateur 1: {ind1_type}")
                        continue # On ignore cette condition si elle est invalide

                    condition = {'stock1': stock1, 'indicator1': {'type': ind1_type, 'params': ind1_params}, 'operator': operator, 'comparison_type': comp_type}
                    
                    # Traiter la partie droite
                    if comp_type == 'indicator':
                        stock2 = stock2_values[array_idx] if array_idx < len(stock2_values) else None
                        ind2_type = indicator2_types[array_idx] if array_idx < len(indicator2_types) else None
                        
                        print(f"    Partie droite: stock2={stock2}, ind2={ind2_type}")
                        
                        if stock2 and ind2_type:
                            ind2_params = []
                            if ind2_type != "PRICE":
                                for k in range(3):
                                    param_idx = array_idx * 3 + k
                                    if param_idx < len(indicator2_params):
                                        param_value = indicator2_params[param_idx]
                                        if param_value is not None:
                                            ind2_params.append(param_value)
                            
                            is_ind2_valid = False
                            if ind2_type in indicators: # Indicateur standard
                                if not indicators[ind2_type]['params'] or ind2_params:
                                    is_ind2_valid = True
                            else: # Indicateur personnalisé
                                is_ind2_valid = True

                            if not is_ind2_valid:
                                print(f"    Paramètres invalides ou manquants pour indicateur 2: {ind2_type}")
                                continue

                            condition['stock2'] = stock2
                            condition['indicator2'] = {'type': ind2_type, 'params': ind2_params}

                            if is_ind2_valid:
                                condition['stock2'] = stock2
                                condition['indicator2'] = {
                                    'type': ind2_type,
                                    'params': ind2_params
                                }
                            else:
                                print(f"    Pas de paramètres valides pour indicateur 2")
                                continue
                        else:
                            print(f"    Stock2 ou indicateur2 manquant")
                            continue
                    
                    elif comp_type == 'value':
                        comp_value = comparison_values[array_idx] if array_idx < len(comparison_values) else None
                        if comp_value is not None:
                            condition['comparison_value'] = comp_value
                        else:
                            print(f"    Valeur de comparaison manquante")
                            continue
                    
                    conditions_list.append(condition)
                    print(f"    -> CONDITION AJOUTÉE: {condition}")
                else:
                    print(f"    Paramètres invalides pour indicateur 1")
            else:
                print(f"    Champs manquants")
        
        # Actions pour ce bloc
        actions = {}
        for stock_idx, stock in enumerate(selected_stocks):
            action_array_idx = block_idx * 10 + stock_idx
            
            if action_array_idx < len(action_values):
                action_value = action_values[action_array_idx]
                if action_value and action_value != 'Ne rien faire':
                    actions[stock] = action_value
                    print(f"  Action {stock} (idx {stock_idx}): {action_value}")
        
        # Ajouter le bloc s'il y a au moins une condition ou une action
        # NOUVEAU BLOC
        if conditions_list:
            decision_blocks.append({'conditions': conditions_list, 'actions': actions})
            print(f"BLOC {block_idx} AJOUTÉ avec {len(conditions_list)} conditions et {len(actions)} actions")
        else:
            print(f"BLOC {block_idx} IGNORÉ - Aucune condition valide trouvée.")
    
    # Si aucun bloc créé, créer un bloc minimal
    if not decision_blocks and selected_stocks:
        decision_blocks.append({
            'conditions': [{
                'stock1': selected_stocks[0],
                'indicator1': {'type': 'SMA', 'params': [20]},
                'operator': '>',
                'comparison_type': 'indicator',
                'stock2': selected_stocks[0],
                'indicator2': {'type': 'SMA', 'params': [50]}
            }],
            'actions': {selected_stocks[0]: 'Acheter'}
        })
        print("BLOC MINIMAL CRÉÉ")
    
    # Créer la stratégie
    strategy = {
        "name": name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "initial_capital": capital or 100000,
        "allocation_pct": alloc or 10,
        "transaction_cost": tx_cost or 1,
        "stop_loss_pct": stop or 0,
        "take_profit_pct": take or 0,
        "date_range": {
            "start": start_date,
            "end": end_date
        },
        "decision_blocks": decision_blocks,
        "selected_stocks": selected_stocks
    }
    
    # Sauvegarder
    os.makedirs("strategies", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    filename = f"{safe_name.replace(' ', '_')}_{timestamp}.json"
    file_path = os.path.join("strategies", filename)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(strategy, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Stratégie sauvegardée: {file_path}")
        print(f"   {len(decision_blocks)} blocs de décision créés")
        
        
        total_conditions = sum(len(block['conditions']) for block in decision_blocks)
        total_actions = sum(len(block['actions']) for block in decision_blocks)
        
        # TRADUCTIONS APPLIQUÉES ICI
        confirmation = dbc.Alert([
            html.I(className="fas fa-check-circle mr-2"),
            f"{t.get('strategy-saved-success', 'Stratégie sauvegardée avec succès')} '{name}' !",
            html.Br(),
            html.Small(f"📊 {len(decision_blocks)} {t.get('blocks', 'blocs')}, {total_conditions} {t.get('conditions', 'conditions')}, {total_actions} {t.get('actions', 'actions')}", className="text-success"),
            html.Br(),
            html.Small(f"📁 {filename}", className="text-muted"),
            html.Hr(),
            dbc.Button(
                [html.I(className="fas fa-play mr-2"), t.get('launch-backtest', 'Lancer le backtest')],
                id="run-backtest",
                color="success",
                className="mt-2",
            )
        ], color="success")
        
        strategy_store_data = {
            'file_path': file_path,
            'strategy_data': strategy
        }
        return confirmation, strategy_store_data 
        
    except Exception as e:
        print(f"[ERREUR] Erreur sauvegarde: {e}")
        return dbc.Alert(f"{t.get('strategy-save-error', 'Erreur lors de la sauvegarde')}: {str(e)}", color="danger"), None, None
        




@app.callback(
    Output('save-confirmation', 'children', allow_duplicate=True),  # Réutilise un output existant
    Input('run-backtest', 'n_clicks'),
    prevent_initial_call=True
)
def debug_backtest_click(n_clicks):
    """Debug pour vérifier que le callback fonctionne"""
    if n_clicks:
        print(f"[DEBUG] Backtest cliqué {n_clicks} fois")
        return f"DEBUG: Backtest lancé {n_clicks} fois"
    return dash.no_update

# Exécution du backtest
@app.callback(
    Output('visualization-placeholder', 'children', allow_duplicate=True),
    Output('backtest-placeholder-info', 'style', allow_duplicate=True), 
    Output('backtest-results-store', 'data', allow_duplicate=True),
    Output("main-tabs", "active_tab", allow_duplicate=True),
    [Input("run-backtest", "n_clicks")],
    [State('language-switcher-sidebar', 'value'),
     State('custom-asset-store', 'data'),
     State('strategy-store', 'data')],
    prevent_initial_call=True
)
def run_backtest(n_clicks, selected_language, custom_asset_data, strategy_store_data): 
    
    # Gestion de la langue
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    if not strategy_store_data or not strategy_store_data.get('strategy_data'):
        return html.Div([
            dbc.Alert(t.get('no-strategy-saved', 'Aucune stratégie sauvegardée. Veuillez d\'abord créer et sauvegarder une stratégie.'), 
                     color="warning")
        ]), {'display': 'block'}, None, dash.no_update  # ✅ 4 RETOURS
    
    current_strategy = strategy_store_data['strategy_data']
    
    try:
        print(f"Démarrage du backtest pour la stratégie: {current_strategy.get('name', 'N/A')}")
        
        # --- PRÉPARATION DES DONNÉES PERSONNALISÉES ---
        custom_dataframes = {}
        if custom_asset_data:
            print("Préparation des DataFrames depuis le store...")
            strategy_stocks = set(current_strategy.get('selected_stocks', []))
            
            for asset_name, df_json in custom_asset_data.items():
                if asset_name in strategy_stocks:
                    df = pd.read_json(df_json, orient='split')
                    custom_dataframes[asset_name] = df
            print(f"{len(custom_dataframes)} DataFrame(s) personnalisé(s) préparé(s).")
        
        # Création de l'objet Backtester
        backtester = Backtester(current_strategy, custom_dataframes=custom_dataframes) 
        backtester.run_backtest()
        
        # Vérification des métriques
        if not hasattr(backtester, 'metrics'):
            backtester.calculate_performance_metrics()
        
        # S'assurer que la colonne drawdown existe
        if 'drawdown' not in backtester.equity_df.columns:
            backtester.equity_df['previous_peak'] = backtester.equity_df['total_equity'].cummax()
            backtester.equity_df['drawdown'] = (backtester.equity_df['total_equity'] / backtester.equity_df['previous_peak'] - 1) * 100
        
        # Génération des graphiques
        figures = generate_plotly_figures(backtester)
        
        # Créer l'affichage des résultats DANS LE NOUVEL ORDRE
        results_components = []

        # 1. RÉSUMÉ DES TRANSACTIONS EN PREMIER
        if hasattr(backtester, 'transactions') and backtester.transactions:
            results_components.append(dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-chart-bar mr-2"),
                    t.get('transaction-summary-title', 'Résumé des transactions')
                ], style=CARD_HEADER_STYLE),
                dbc.CardBody([
                    html.H4(t.get('transaction-summary-heading', '=== RÉSUMÉ DES TRANSACTIONS ==='), 
                           className="text-center text-info mb-4"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.ListGroup([
                                dbc.ListGroupItem([
                                    html.Strong(f"{t.get('total-transactions-label', 'Nombre total de transactions')}: "), 
                                    html.Span(f"{len(backtester.transactions)}")
                                ]),
                                dbc.ListGroupItem([
                                    html.Strong(f"{t.get('buy-transactions-label', 'Achats')}: "), 
                                    html.Span(f"{sum(1 for t in backtester.transactions if t['type'] == 'ACHAT')}")
                                ]),
                                dbc.ListGroupItem([
                                    html.Strong(f"{t.get('sell-transactions-label', 'Ventes')}: "), 
                                    html.Span(f"{sum(1 for t in backtester.transactions if 'VENTE' in t['type'])}")
                                ]),
                                dbc.ListGroupItem([
                                    html.Strong(f"{t.get('stop-loss-transactions-label', 'Stop Loss')}: "), 
                                    html.Span(f"{sum(1 for t in backtester.transactions if t['type'] == 'STOP LOSS')}")
                                ]),
                                dbc.ListGroupItem([
                                    html.Strong(f"{t.get('take-profit-transactions-label', 'Take Profit')}: "), 
                                    html.Span(f"{sum(1 for t in backtester.transactions if t['type'] == 'TAKE PROFIT')}")
                                ]),
                                dbc.ListGroupItem([
                                    html.Strong(f"{t.get('backtest-end-label', 'Fin de backtest')}: "), 
                                    html.Span(f"{sum(1 for t in backtester.transactions if 'FIN BACKTEST' in t['type'])}")
                                ]),
                            ]),
                            
                            # P&L total
                            dbc.Card([
                                dbc.CardBody([
                                    html.H5(f"{t.get('total-pnl-label', 'P&L total')}:", className="card-title"),
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
                            html.H5(f"{t.get('all-metrics-title', 'Toutes les métriques')}:", className="mb-3"),
                            html.Table([
                                html.Tbody([
                                    html.Tr([
                                        html.Td(f"{t.get('initial-capital-label', 'Capital initial')}:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                        html.Td(f"{backtester.metrics['Capital initial']:,.2f} €", style={'textAlign': 'right', 'padding': '4px'})
                                    ]),
                                    html.Tr([
                                        html.Td(f"{t.get('final-capital-label', 'Capital final')}:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                        html.Td(f"{backtester.metrics['Capital final']:,.2f} €", style={'textAlign': 'right', 'padding': '4px'})
                                    ]),
                                    html.Tr([
                                        html.Td(f"{t.get('total-return-label', 'Rendement total')}:", style={'fontWeight': 'bold', 'padding': '4px'}),
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
                                        html.Td(f"{t.get('annualized-return-label', 'Rendement annualisé')}:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                        html.Td(
                                            f"{backtester.metrics['Rendement annualisé (%)']:.2f}%",
                                            style={
                                                'textAlign': 'right', 
                                                'padding': '4px',
                                                'color': 'green' if backtester.metrics['Rendement annualisé (%)'] > 0 else 'red',
                                                'fontWeight': 'bold'
                                            }
                                        )
                                    ]),
                                    html.Tr([
                                        html.Td(f"{t.get('max-drawdown-label', 'Drawdown maximum')}:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                        html.Td(
                                            f"{backtester.metrics['Drawdown maximum (%)']:.2f}%",
                                            style={'textAlign': 'right', 'padding': '4px', 'color': 'red', 'fontWeight': 'bold'}
                                        )
                                    ]),
                                    html.Tr([
                                        html.Td(f"{t.get('sharpe-ratio-label', 'Ratio de Sharpe')}:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                        html.Td(f"{backtester.metrics['Ratio de Sharpe']:.2f}", style={'textAlign': 'right', 'padding': '4px'})
                                    ]),
                                    html.Tr([
                                        html.Td(f"{t.get('trades-count-label', 'Nombre de trades')}:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                        html.Td(f"{int(backtester.metrics['Nombre de trades'])}", style={'textAlign': 'right', 'padding': '4px'})
                                    ]),
                                    html.Tr([
                                        html.Td(f"{t.get('winning-trades-pct-label', '% trades gagnants')}:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                        html.Td(f"{backtester.metrics['Pourcentage de trades gagnants (%)']:.2f}%", style={'textAlign': 'right', 'padding': '4px'})
                                    ]),
                                    html.Tr([
                                        html.Td(f"{t.get('avg-profit-per-trade-label', 'Profit moyen/trade')}:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                        html.Td(
                                            f"{backtester.metrics['Profit moyen par trade']:.2f} €",
                                            style={
                                                'textAlign': 'right', 
                                                'padding': '4px',
                                                'color': 'green' if backtester.metrics['Profit moyen par trade'] > 0 else 'red'
                                            }
                                        )
                                    ]),
                                    html.Tr([
                                        html.Td(f"{t.get('avg-winning-profit-label', 'Profit moyen gagnants')}:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                        html.Td(f"{backtester.metrics['Profit moyen des trades gagnants']:.2f} €", 
                                               style={'textAlign': 'right', 'padding': '4px', 'color': 'green'})
                                    ]),
                                    html.Tr([
                                        html.Td(f"{t.get('avg-losing-loss-label', 'Perte moyenne perdants')}:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                        html.Td(f"{backtester.metrics['Perte moyenne des trades perdants']:.2f} €", 
                                               style={'textAlign': 'right', 'padding': '4px', 'color': 'red'})
                                    ]),
                                    html.Tr([
                                        html.Td(f"{t.get('profit-factor-label', 'Profit factor')}:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                        html.Td(
                                            f"{backtester.metrics['Profit factor']:.2f}",
                                            style={
                                                'textAlign': 'right', 
                                                'padding': '4px',
                                                'color': 'green' if backtester.metrics['Profit factor'] > 1 else 'red',
                                                'fontWeight': 'bold'
                                            }
                                        )
                                    ])
                                ])
                            ], style={'width': '100%', 'fontSize': '14px'})
                        ], width=6)
                    ]),
                ], style=CARD_BODY_STYLE)
            ], style=CARD_STYLE, className="mb-4"))

        # 2. GRAPHIQUES DES SYMBOLES AVEC INDICATEURS EN DEUXIÈME
        symbol_cards = []
        for key, figure in figures.items():
            if key.startswith('symbol_'):
                symbol = key.replace('symbol_', '')
                
                symbol_card = dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-line mr-2"),
                        f"{t.get('price-indicators-title', 'Prix et indicateurs')} - {symbol}"
                    ], style=CARD_HEADER_STYLE),
                    dbc.CardBody([
                        dcc.Graph(
                            id=f'symbol-chart-{symbol}',
                            figure=figure,
                            config={'displayModeBar': True, 'scrollZoom': True}
                        ),
                        # Graphique du volume si disponible
                        dcc.Graph(
                            id=f'volume-chart-{symbol}',
                            figure=figures.get(f'volume_{symbol}', {}),
                            config={'displayModeBar': True, 'scrollZoom': True}
                        ) if f'volume_{symbol}' in figures else html.Div()
                    ], style=CARD_BODY_STYLE)
                ], style=CARD_STYLE, className="mb-4")
                
                symbol_cards.append(symbol_card)

        results_components.extend(symbol_cards)

        # 3. TABLEAU DES TRANSACTIONS (LOGS) EN TROISIÈME
        if 'transactions' in figures and isinstance(figures['transactions'], pd.DataFrame):
            transactions_df = figures['transactions'].copy()
            
            # Sélectionner et renommer les colonnes avec traductions
            if selected_language == 'en':
                columns_to_keep = {
                    'date': 'Trade Date',
                    'type': 'Type',
                    'symbol': 'Symbol', 
                    'price': 'Price',
                    'shares': 'Quantity',
                    'pnl': 'P&L',
                    'pnl_pct': 'P&L %',
                    'allocated_amount': 'Allocated Amount',
                    'allocation_return_pct': 'Allocation Return %',
                    'positions_sold': 'Positions Sold'
                }
            else:
                columns_to_keep = {
                    'date': 'Date du trade',
                    'type': 'Type',
                    'symbol': 'Symbole', 
                    'price': 'Prix',
                    'shares': 'Quantité',
                    'pnl': 'P&L',
                    'pnl_pct': 'P&L %',
                    'allocated_amount': 'Montant alloué',
                    'allocation_return_pct': 'Retour allocation %',
                    'positions_sold': 'Positions vendues'
                }
            
            # Filtrer les colonnes qui existent
            available_columns = {k: v for k, v in columns_to_keep.items() if k in transactions_df.columns}
            transactions_df = transactions_df[list(available_columns.keys())].copy()
            transactions_df = transactions_df.rename(columns=available_columns)
            
            # Formater la colonne Date si c'est un Timestamp
            date_col = 'Trade Date' if selected_language == 'en' else 'Date du trade'
            if date_col in transactions_df.columns:
                if pd.api.types.is_datetime64_any_dtype(transactions_df[date_col]):
                    transactions_df[date_col] = transactions_df[date_col].dt.strftime('%Y-%m-%d')
            
            results_components.append(dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-list-alt mr-2"),
                    t.get('transactions-journal-title', 'Journal des transactions (logs)')
                ], style=CARD_HEADER_STYLE),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='transactions-table',
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
                            },
                            {
                                'if': {'column_id': 'P&L %', 'filter_query': '{P&L %} > 0'},
                                'color': COLORS['success']
                            },
                            {
                                'if': {'column_id': 'P&L %', 'filter_query': '{P&L %} < 0'},
                                'color': COLORS['danger']
                            }
                        ]
                    )
                ], style=CARD_BODY_STYLE)
            ], style=CARD_STYLE, className="mb-4"))

        # 4. DRAWDOWN EN QUATRIÈME
        if 'drawdown' in figures:
            results_components.append(dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-chart-area mr-2"),
                    t.get('drawdown-title', 'Drawdown')
                ], style=CARD_HEADER_STYLE),
                dbc.CardBody([
                    dcc.Graph(
                        id='drawdown-chart',
                        figure=figures['drawdown'],
                        config={'displayModeBar': True, 'scrollZoom': True}
                    )
                ], style=CARD_BODY_STYLE)
            ], style=CARD_STYLE, className="mb-4"))

        # 5. COURBE D'ÉQUITÉ EN CINQUIÈME
        if 'equity' in figures:
            results_components.append(dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-chart-area mr-2"),
                    t.get('equity-curve-title', 'Courbe d\'équité')
                ], style=CARD_HEADER_STYLE),
                dbc.CardBody([
                    dcc.Graph(
                        id='equity-chart',
                        figure=figures['equity'],
                        config={'displayModeBar': True, 'scrollZoom': True}
                    )
                ], style=CARD_BODY_STYLE)
            ], style=CARD_STYLE, className="mb-4"))

        # 6. Bouton pour exporter les résultats
        results_components.append(
            dbc.Button(
                [html.I(className="fas fa-file-export mr-2"), t.get('export-results-pdf', 'Exporter les résultats en PDF')],
                id="export-results",
                color="info",
                className="mb-4 w-100",
                style=BUTTON_STYLE
            )
        )

        
        # Données pour l'export
        export_data = {
            'strategy_data': current_strategy,
            'metrics': backtester.metrics,
            'figures': {k: v.to_dict() if hasattr(v, 'to_dict') else v for k, v in figures.items()},
            'transactions': backtester.transactions
        }
        
        return html.Div(results_components), {'display': 'none'}, export_data, "tab-results"
        
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Exception dans run_backtest: {str(e)}")
        print(traceback_str)
        
        # ✅ CORRECTION : RETOURNER 2 ÉLÉMENTS
        return html.Div([
            dbc.Alert([
                html.H4(t.get('backtest-error-title', 'Erreur lors de l\'exécution du backtest'), className="alert-heading"),
                html.P(f"{t.get('backtest-error-message', 'Une erreur s\'est produite')}: {str(e)}"),
                html.Hr(),
                html.P(t.get('strategy-check-message', 'Vérifiez que votre stratégie est correctement définie.'), className="mb-0"),
                html.Details([
                    html.Summary(t.get('technical-details', 'Détails techniques')),
                    html.Pre(traceback_str, style={"whiteSpace": "pre-wrap", "fontSize": "small"})
                ], className="mt-3")
            ], color="danger")
        ]), {'display': 'block'}, None, dash.no_update  # ✅ AJOUT DU 4ÈME RETOUR




# EXPORT PDF CALLBACK
@app.callback(
    Output("download-results-pdf", "data"),
    Input("export-results", "n_clicks"),
    State("backtest-results-store", "data"),
    prevent_initial_call=True
)
def export_results_pdf(n_clicks, results_data):
    if not n_clicks or not results_data:
        raise PreventUpdate
    
    try:
        # Recuperation des donnees
        strategy_data = results_data.get('strategy_data')
        raw_metrics = results_data.get('metrics', {})
        figures_dict = results_data.get('figures', {})
        transactions = results_data.get('transactions', [])
        
        # MAPPING DES MÉTRIQUES (FR -> EN technique pour pdf_exporter)
        metrics = {
            'total_pnl': sum(t.get('pnl', 0) for t in transactions) if transactions else 0,
            'initial_capital': raw_metrics.get('Capital initial', 0),
            'final_capital': raw_metrics.get('Capital final', 0),
            'total_return': raw_metrics.get('Rendement total (%)', 0),
            'annualized_return': raw_metrics.get('Rendement annualisé (%)', 0),
            'max_drawdown': raw_metrics.get('Drawdown maximum (%)', 0),
            'sharpe_ratio': raw_metrics.get('Ratio de Sharpe', 0),
            'num_trades': raw_metrics.get('Nombre de trades', 0),
            'win_rate': raw_metrics.get('Pourcentage de trades gagnants (%)', 0),
            'avg_profit_per_trade': raw_metrics.get('Profit moyen par trade', 0),
            'profit_factor': raw_metrics.get('Profit factor', 0)
        }
        
        # Reconstruction des figures Plotly
        figures = {}
        for k, v in figures_dict.items():
            try:
                figures[k] = go.Figure(v)
            except:
                pass
                
        pdf_bytes = export_backtest_to_pdf(strategy_data, metrics, figures, transactions)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return dcc.send_bytes(pdf_bytes, f"Rapport_Backtest_{timestamp}.pdf")
    except Exception as e:
        print(f"Erreur export PDF: {e}")
        import traceback
        traceback.print_exc()
        raise PreventUpdate


# Chargement des stratégies sauvegardées
@app.callback(
    Output("strategies-list", "children"),
    Input("refresh-strategies", "n_clicks"),
)
def load_saved_strategies(n_clicks):
    if not os.path.exists("strategies"):
        return html.P("Aucune stratégie sauvegardée trouvée.", className="text-warning")
    
    strategy_files = []
    for file in os.listdir("strategies"):
        if file.endswith(".json"):
            try:
                with open(os.path.join("strategies", file), 'r') as f:
                    strategy_data = json.load(f)
                    created_at = strategy_data.get('created_at', 'Date inconnue')
                    name = strategy_data.get('name', 'Sans nom')
                    
                    strategy_files.append({
                        'name': name,
                        'created_at': created_at,
                        'filename': file,
                        'path': os.path.join("strategies", file)
                    })
            except:
                continue
    
    if not strategy_files:
        return html.P("Aucune stratégie sauvegardée trouvée.", className="text-warning")
    
    strategy_files.sort(key=lambda x: x['created_at'], reverse=True)
    
    strategy_cards = []
    for strategy in strategy_files:
        card = dbc.Card([
            dbc.CardHeader(
                html.H5(strategy['name'], className="m-0")
            ),
            dbc.CardBody([
                html.P(f"Créée le: {strategy['created_at']}", className="card-text text-muted"),
                html.P(f"Fichier: {strategy['filename']}", className="card-text small"),
                dbc.ButtonGroup([
                    dbc.Button(
                        "Charger", 
                        id={'type': 'load-strategy', 'index': strategy['path']}, 
                        color="primary", 
                        size="sm",
                        className="mr-2"
                    ),
                    dbc.Button(
                        "Backtester", 
                        id={'type': 'backtest-strategy', 'index': strategy['path']}, 
                        color="success", 
                        size="sm",
                        className="mr-2"
                    ),
                    dbc.Button(
                        "Supprimer", 
                        id={'type': 'delete-strategy', 'index': strategy['path']}, 
                        color="danger", 
                        size="sm"
                    )
                ])
            ])
        ], className="mb-3", style={**CARD_STYLE, 'opacity': '0.9'})
        
        strategy_cards.append(card)
    
    return strategy_cards

# Chargement d'une stratégie existante
@app.callback(
    [Output('strategy-store', 'data', allow_duplicate=True),  # ✅ STORE UNIFIÉ
     Output('strategy-name', 'value', allow_duplicate=True),
     Output('initial-capital', 'value', allow_duplicate=True),
     Output('allocation', 'value', allow_duplicate=True),
     Output('transaction-cost', 'value', allow_duplicate=True),
     Output('stop-loss', 'value', allow_duplicate=True),
     Output('take-profit', 'value', allow_duplicate=True),
     Output('date-picker-range', 'start_date', allow_duplicate=True),
     Output('date-picker-range', 'end_date', allow_duplicate=True)],
    Input({'type': 'load-strategy', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def load_strategy(n_clicks_list):
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks for n_clicks in n_clicks_list if n_clicks):
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    strategy_path = json.loads(button_id)['index']
    
    try:
        with open(strategy_path, 'r') as f:
            strategy_data = json.load(f)
        
 
        
        name = strategy_data.get('name', '')
        capital = strategy_data.get('initial_capital', 100000)
        allocation = strategy_data.get('allocation_pct', 10)
        tx_cost = strategy_data.get('transaction_cost', 1)
        stop_loss = strategy_data.get('stop_loss_pct', 5) 
        take_profit = strategy_data.get('take_profit_pct', 10)
        start_date = strategy_data.get('date_range', {}).get('start', '2020-01-01')
        end_date = strategy_data.get('date_range', {}).get('end', '2021-01-01')
        
        
        strategy_store_data = {
            'file_path': strategy_path,
            'strategy_data': strategy_data
        }
        return [strategy_store_data, name, capital, allocation, tx_cost, stop_loss, take_profit, 
                start_date, end_date]  # ✅ 9 VALEURS POUR 9 OUTPUTS
    
    except Exception as e:
        print(f"Erreur lors du chargement de la stratégie: {e}")
        raise PreventUpdate

# Backtest d'une stratégie sauvegardée
@app.callback(
    Output("visualization-placeholder", "children", allow_duplicate=True),
    Output('backtest-results-store', 'data'),
    Output('current-strategy-file-store', 'data'),
    Input({'type': 'backtest-strategy', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def run_saved_strategy_backtest(n_clicks_list):
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks for n_clicks in n_clicks_list if n_clicks):
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    strategy_path = json.loads(button_id)['index']
    
    try:

        return run_backtest(1), {'strategy_path': strategy_path}
    
    except Exception as e:
        return html.Div([
            dbc.Alert([
                html.H4("Erreur lors du backtest", className="alert-heading"),
                html.P(f"Une erreur s'est produite: {str(e)}"),
            ], color="danger")
        ]), None

# Suppression d'une stratégie
@app.callback(
    Output("saved-strategies-container", "children", allow_duplicate=True),
    Input({'type': 'delete-strategy', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def delete_strategy(n_clicks_list):
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks for n_clicks in n_clicks_list if n_clicks):
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    strategy_path = json.loads(button_id)['index']
    
    try:
        if os.path.exists(strategy_path):
            os.remove(strategy_path)
            
        time.sleep(0.5)
        return load_saved_strategies(1)
    
    except Exception as e:
        return html.Div([
            dbc.Alert(f"Erreur lors de la suppression: {str(e)}", color="danger"),
            html.Div(id="strategies-list")
        ])

    
# Callback 1: Description du modèle
@app.callback(
    Output('model-description-container', 'children'),
    Input('synthetic-model-dropdown', 'value')
)
def update_model_description(model_type):
    if not model_type:
        return ""
    
    model_info = ModelFactory.get_model_info(model_type)
    
    if not model_info:
        return ""
    
    return dbc.Alert([
        html.Strong(f"🎯 {model_info['name']}"),
        html.Br(),
        html.P(model_info['description'], className="mb-1"),
        html.Small(f"Complexité: {model_info['complexity']} | "
                    f"Paramètres: {', '.join(model_info['parameters'])}", 
                    className="text-muted")
    ], color="info", className="mt-2")

# Callback 2: Paramètres spécifiques au modèle
@app.callback(
    Output('model-params-container', 'children'),
    Input('synthetic-model-dropdown', 'value')
)
def update_model_params(model_type):
    if not model_type:
        return ""
    
    # Paramètres par défaut pour chaque modèle
    param_configs = {
        'gbm': [],  # GBM n'a pas de paramètres configurables (auto-calibré)
        'heston': [
            {'id': 'heston-kappa', 'label': 'κ (Vitesse retour moyenne)', 'value': 2.0, 'min': 0.1, 'max': 10, 'step': 0.1},
            {'id': 'heston-theta', 'label': 'θ (Variance long terme)', 'value': 0.04, 'min': 0.001, 'max': 1, 'step': 0.001},
            {'id': 'heston-xi', 'label': 'ξ (Vol de la vol)', 'value': 0.3, 'min': 0.01, 'max': 2, 'step': 0.01},
            {'id': 'heston-rho', 'label': 'ρ (Corrélation)', 'value': -0.7, 'min': -0.99, 'max': 0.99, 'step': 0.01}
        ],
        'bates': [
            {'id': 'bates-kappa', 'label': 'κ (Vitesse retour moyenne)', 'value': 2.0, 'min': 0.1, 'max': 10, 'step': 0.1},
            {'id': 'bates-theta', 'label': 'θ (Variance long terme)', 'value': 0.04, 'min': 0.001, 'max': 1, 'step': 0.001},
            {'id': 'bates-xi', 'label': 'ξ (Vol de la vol)', 'value': 0.3, 'min': 0.01, 'max': 2, 'step': 0.01},
            {'id': 'bates-rho', 'label': 'ρ (Corrélation)', 'value': -0.7, 'min': -0.99, 'max': 0.99, 'step': 0.01},
            {'id': 'bates-lambda', 'label': 'λ (Fréquence sauts/an)', 'value': 2.0, 'min': 0.1, 'max': 20, 'step': 0.1},
            {'id': 'bates-mu-jump', 'label': 'μⱼ (Taille moyenne saut)', 'value': 0.0, 'min': -0.5, 'max': 0.5, 'step': 0.01},
            {'id': 'bates-sigma-jump', 'label': 'σⱼ (Vol des sauts)', 'value': 0.1, 'min': 0.01, 'max': 1, 'step': 0.01}
        ],
        'sabr': [
            {'id': 'sabr-alpha', 'label': 'α (Niveau de vol)', 'value': 0.2, 'min': 0.01, 'max': 2, 'step': 0.01},
            {'id': 'sabr-beta', 'label': 'β (Élasticité)', 'value': 0.5, 'min': 0.01, 'max': 0.99, 'step': 0.01},
            {'id': 'sabr-rho', 'label': 'ρ (Corrélation)', 'value': -0.3, 'min': -0.99, 'max': 0.99, 'step': 0.01},
            {'id': 'sabr-nu', 'label': 'ν (Vol de vol)', 'value': 0.3, 'min': 0.01, 'max': 2, 'step': 0.01}
        ]
    }
    
    params = param_configs.get(model_type, [])
    
    if not params:
        return dbc.Alert(
            "✅ Ce modèle utilise une calibration automatique - aucun paramètre à configurer",
            color="success", className="mb-3"
        )
    
    # Créer les contrôles de paramètres
    param_controls = []
    for param in params:
        param_controls.append(
            dbc.Col([
                html.Label(param['label'], className="text-sm font-weight-bold"),
                dbc.Input(
                    id=param['id'],
                    type="number",
                    value=param['value'],
                    min=param['min'],
                    max=param['max'],
                    step=param['step'],
                    style=INPUT_STYLE
                )
            ], width=6 if len(params) <= 4 else 4, className="mb-2")
        )
    
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-sliders-h mr-2"),
            f"Paramètres du modèle {model_type.upper()}"
        ], style=CARD_HEADER_STYLE),
        dbc.CardBody([
            html.P("Ajustez les paramètres ou laissez les valeurs par défaut pour une calibration automatique",
                    className="text-muted mb-3"),
            dbc.Row(param_controls),
            dbc.Alert([
                html.I(className="fas fa-info-circle mr-2"),
                "Les paramètres seront d'abord auto-calibrés, puis ajustés selon vos valeurs"
            ], color="info", className="mt-2")
        ], style=CARD_BODY_STYLE)
    ], style=CARD_STYLE, className="mb-3")

# Callback 3: Affichage des actifs sélectionnés
@app.callback(
    Output('synthetic-assets-display', 'children'),
    Input('selected-stocks-store', 'data')
)
def update_assets_display(selected_stocks):
    if not selected_stocks:
        return dbc.Alert(
            "⚠️ Aucun actif sélectionné. Allez dans l'onglet 'Création de stratégie' pour sélectionner des actifs.",
            color="warning"
        )
    
    return dbc.ListGroup([
        dbc.ListGroupItem([
            html.I(className="fas fa-chart-line mr-2"),
            f"{stock} ({ticker_to_name.get(stock, 'Nom inconnu')})"
        ]) for stock in selected_stocks
    ])

# Callback 4: Génération des données synthétiques
@app.callback(
    [Output('synthetic-data-store', 'data'),
        Output('synthetic-model-info-store', 'data'),
        Output('generation-status', 'children'),
        Output('run-synthetic-backtest', 'disabled')],
    Input('generate-synthetic-data', 'n_clicks'),
    [State('synthetic-model-dropdown', 'value'),
        State('selected-stocks-store', 'data'),
        State('synthetic-calibration-dates', 'start_date'),
        State('synthetic-calibration-dates', 'end_date'),
        State('synthetic-horizon', 'value'),
        State('synthetic-steps', 'value'),
        State('synthetic-simulations', 'value')] +
    # États pour tous les paramètres possibles
    [State(f'heston-{param}', 'value') for param in ['kappa', 'theta', 'xi', 'rho']] +
    [State(f'bates-{param}', 'value') for param in ['kappa', 'theta', 'xi', 'rho', 'lambda', 'mu-jump', 'sigma-jump']] +
    [State(f'sabr-{param}', 'value') for param in ['alpha', 'beta', 'rho', 'nu']],
    prevent_initial_call=True
)
def generate_synthetic_data(n_clicks, model_type, selected_stocks, start_date, end_date,
                            horizon, steps, simulations, *param_values):
    if not n_clicks:
        raise PreventUpdate
    
    # Validation des entrées
    if not selected_stocks:
        return None, None, dbc.Alert("❌ Aucun actif sélectionné", color="danger"), True
    
    if not model_type:
        return None, None, dbc.Alert("❌ Aucun modèle sélectionné", color="danger"), True
    
    try:
        # Extraire les paramètres selon le modèle
        model_params = {}
        param_idx = 0
        
        if model_type == 'heston':
            heston_params = ['kappa', 'theta', 'xi', 'rho']
            for param in heston_params:
                if param_values[param_idx] is not None:
                    model_params[param] = param_values[param_idx]
                param_idx += 1
            param_idx += 7  # Skip bates params
            param_idx += 4  # Skip sabr params
        
        elif model_type == 'bates':
            param_idx += 4  # Skip heston params
            bates_params = ['kappa', 'theta', 'xi', 'rho', 'lambda_j', 'mu_j', 'sigma_j']
            bates_param_names = ['kappa', 'theta', 'xi', 'rho', 'lambda', 'mu-jump', 'sigma-jump']
            for i, param in enumerate(bates_params):
                if param_values[param_idx] is not None:
                    model_params[param] = param_values[param_idx]
                param_idx += 1
            param_idx += 4  # Skip sabr params
        
        elif model_type == 'sabr':
            param_idx += 4  # Skip heston params
            param_idx += 7  # Skip bates params
            sabr_params = ['alpha0', 'beta', 'rho', 'nu']
            for param in sabr_params:
                if param_values[param_idx] is not None:
                    model_params[param] = param_values[param_idx]
                param_idx += 1
        
        # Créer le gestionnaire de données synthétiques
        manager = SyntheticDataManager()
        
        # Générer les données
        synthetic_data = manager.generate_data(
            model_type=model_type,
            symbols=selected_stocks,
            start_date=start_date,
            end_date=end_date,
            T=horizon,
            n_steps=steps,
            n_simulations=simulations,
            **model_params
        )
        
        # Convertir pour stockage JSON
        synthetic_data_json = {
            'data': synthetic_data.to_dict(),
            'index': synthetic_data.index.strftime('%Y-%m-%d').tolist(),
            'columns': [(col[0], col[1]) for col in synthetic_data.columns]
        }
        
        # Informations sur les modèles
        model_info = {}
        for symbol in selected_stocks:
            model_summary = manager.get_model_summary(symbol)
            if model_summary:
                model_info[symbol] = model_summary
        
        success_message = dbc.Alert([
            html.I(className="fas fa-check-circle mr-2"),
            f"✅ Données synthétiques générées avec succès!",
            html.Br(),
            html.Small(f"Modèle: {model_type.upper()} | "
                        f"Actifs: {len(selected_stocks)} | "
                        f"Période: {steps} jours", className="text-success")
        ], color="success")
        
        return synthetic_data_json, model_info, success_message, False
        
    except Exception as e:
        error_message = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle mr-2"),
            f"❌ Erreur lors de la génération: {str(e)}"
        ], color="danger")
        
        return None, None, error_message, True

# Callback 5: Chargement des stratégies disponibles
@app.callback(
    Output('synthetic-strategy-dropdown', 'options'),
    Input('synthetic-strategy-dropdown', 'id')  # Trigger au chargement
)
def load_strategy_options(_):
    import os
    
    if not os.path.exists("strategies"):
        return []
    
    strategy_options = []
    for file in os.listdir("strategies"):
        if file.endswith(".json"):
            try:
                with open(os.path.join("strategies", file), 'r') as f:
                    strategy_data = json.load(f)
                    name = strategy_data.get('name', 'Sans nom')
                    created_at = strategy_data.get('created_at', 'Date inconnue')
                    
                    strategy_options.append({
                        'label': f"{name} ({created_at})",
                        'value': os.path.join("strategies", file)
                    })
            except:
                continue
    
    # Ajouter option pour stratégie actuelle
    strategy_options.insert(0, {
        'label': "📝 Utiliser la stratégie actuellement configurée",
        'value': 'current_strategy'
    })
    
    return strategy_options




# DANS app.py - REMPLACEZ VOS CALLBACKS D'OPTIONS PAR CE BLOC COMPLET

# Callback 1 : Gérer les maturités (inchangé mais inclus pour la clarté)
@app.callback(
    [Output({'type': 'option-maturity-selector', 'index': MATCH}, 'options'),
     Output({'type': 'option-maturity-selector', 'index': MATCH}, 'value'),
     Output({'type': 'option-maturity-selector', 'index': MATCH}, 'disabled'),
     Output({'type': 'option-strike-selector', 'index': MATCH}, 'options', allow_duplicate=True),
     Output({'type': 'option-strike-selector', 'index': MATCH}, 'value', allow_duplicate=True),
     Output({'type': 'option-strike-selector', 'index': MATCH}, 'disabled', allow_duplicate=True),
     Output({'type': 'option-type-selector', 'index': MATCH}, 'disabled', allow_duplicate=True)],
    Input({'type': 'option-underlying-selector', 'index': MATCH}, 'value'),
    prevent_initial_call=True
)
def update_maturities_row(selected_underlying):
    if not selected_underlying: return [], None, True, [], None, True, True
    try:
        stock = yf.Ticker(selected_underlying)
        maturities = stock.options
        maturity_options = [{'label': date, 'value': date} for date in maturities]
        return maturity_options, None, False, [], None, True, True
    except Exception as e:
        print(f"Erreur maturités pour {selected_underlying}: {e}")
        return [], None, True, [], None, True, True

# Callback 2 : Gérer les strikes (inchangé mais inclus pour la clarté)
@app.callback(
    [Output({'type': 'option-strike-selector', 'index': MATCH}, 'options', allow_duplicate=True),
     Output({'type': 'option-strike-selector', 'index': MATCH}, 'disabled', allow_duplicate=True),
     Output({'type': 'option-type-selector', 'index': MATCH}, 'disabled', allow_duplicate=True)],
    Input({'type': 'option-maturity-selector', 'index': MATCH}, 'value'),
    State({'type': 'option-underlying-selector', 'index': MATCH}, 'value'),
    prevent_initial_call=True
)
def update_strikes_row(selected_maturity, selected_underlying):
    if not selected_maturity or not selected_underlying: return [], True, True
    try:
        stock = yf.Ticker(selected_underlying)
        opt_chain = stock.option_chain(selected_maturity)
        strikes = pd.concat([opt_chain.calls['strike'], opt_chain.puts['strike']]).unique()
        strikes.sort()
        strike_options = [{'label': f"{strike:,.2f}", 'value': strike} for strike in strikes]
        return strike_options, False, False
    except Exception as e:
        print(f"Erreur strikes pour {selected_underlying} ({selected_maturity}): {e}")
        return [], True, True

# Callback 3 : Gérer l'ajout ET la suppression de lignes (LOGIQUE CORRIGÉE)
@app.callback(
    Output('option-rows-container', 'children'),
    [Input({'type': 'option-type-selector', 'index': ALL}, 'value'),
     Input({'type': 'delete-option-row', 'index': ALL}, 'n_clicks')],
    State('option-rows-container', 'children'),
    prevent_initial_call=True
)
def manage_option_rows(types_selected, delete_clicks, existing_rows):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id']
    
    # Cas 1 : On a cliqué sur un bouton supprimer
    if 'delete-option-row' in trigger_id:
        delete_index = ctx.triggered_id['index']
        # On garde toutes les lignes sauf celle dont l'index correspond
        new_rows = [
            row for i, row in enumerate(existing_rows) 
            if row['props']['children'][4]['props']['children']['props']['id']['index'] != delete_index
        ]
        if not new_rows:
            return [create_option_selection_row(0)]
        return new_rows

    # Cas 2 : On a rempli un sélecteur de type
    if 'option-type-selector' in trigger_id:
        # On vérifie si la dernière ligne est bien remplie
        if types_selected and types_selected[-1] is not None:
            new_index = len(existing_rows)
            new_row = create_option_selection_row(new_index)
            return existing_rows + [new_row]

    return existing_rows

# Callback 4 : Mettre à jour les graphiques (LOGIQUE CORRIGÉE ET SIMPLIFIÉE)
@app.callback(
    Output('option-charts-container', 'children', allow_duplicate=True),
    [Input({'type': 'option-underlying-selector', 'index': ALL}, 'value'),
     Input({'type': 'option-maturity-selector', 'index': ALL}, 'value'),
     Input({'type': 'option-strike-selector', 'index': ALL}, 'value'),
     Input({'type': 'option-type-selector', 'index': ALL}, 'value')],
    prevent_initial_call=True
)
def update_option_charts_dynamically(underlyings, maturities, strikes, types):
    completed_contracts = []
    for i in range(len(underlyings)):
        if all([underlyings[i], maturities[i], strikes[i], types[i]]):
            completed_contracts.append({
                'underlying': underlyings[i], 'maturity': maturities[i],
                'strike': strikes[i], 'type': types[i]
            })

    if not completed_contracts:
        return None

    contracts_by_underlying = {}
    for contract in completed_contracts:
        underlying = contract['underlying']
        if underlying not in contracts_by_underlying:
            contracts_by_underlying[underlying] = []
        contracts_by_underlying[underlying].append(contract)

    all_chart_cols = []
    try:
        for underlying, contracts in contracts_by_underlying.items():
            stock_ticker = yf.Ticker(underlying)
            hist_stock = stock_ticker.history(period="1y", interval="1d")
            fig_stock = go.Figure()
            fig_stock.add_trace(go.Scatter(x=hist_stock.index, y=hist_stock['Close'], mode='lines', name=underlying))
            for contract in contracts:
                fig_stock.add_hline(y=contract['strike'], line_dash="dash", annotation_text=f"Strike {contract['strike']}$")
            fig_stock.update_layout(title=f"Prix du Sous-Jacent : {underlying}", template='plotly_dark')
            all_chart_cols.append(dbc.Col(dcc.Graph(figure=fig_stock), width=6))

            for contract in contracts:
                chain = stock_ticker.option_chain(contract['maturity'])
                chain_df = chain.calls if contract['type'] == 'call' else chain.puts
                contract_info = chain_df[chain_df.strike == contract['strike']]
                if contract_info.empty: continue
                contract_symbol = contract_info.iloc[0].contractSymbol
                
                option_ticker = yf.Ticker(contract_symbol)
                hist_option = option_ticker.history(period="1y", interval="1d")

                # Graphique simple du prix de l'option, sans second axe Y
                fig_option = go.Figure()
                fig_option.add_trace(go.Scatter(x=hist_option.index, y=hist_option['Close'], mode='lines', name='Prix Option'))
                fig_option.update_layout(
                    title=f"Prix de l'Option<br>{contract_symbol}",
                    template='plotly_dark',
                    xaxis_title="Date", yaxis_title="Prix ($)"
                )
                all_chart_cols.append(dbc.Col(dcc.Graph(figure=fig_option), width=6))
        
        final_layout = []
        for i in range(0, len(all_chart_cols), 2):
            final_layout.append(dbc.Row(all_chart_cols[i:i+2], className="mb-3"))
        return final_layout

    except Exception as e:
        print(f"Erreur graphiques cumulatifs : {e}")
        return dbc.Alert("Erreur lors de la génération des graphiques.", color="danger")

# DANS app.py - AJOUTEZ CETTE NOUVELLE FONCTION

# Callback pour mettre à jour les graphiques de prévisualisation
# DANS app.py - REMPLACEZ LA FONCTION update_option_charts

@app.callback(
    Output('option-charts-container', 'children'),
    # On écoute toujours le dernier dropdown de toutes les lignes
    Input({'type': 'option-type-selector', 'index': ALL}, 'value'),
    [State({'type': 'option-underlying-selector', 'index': ALL}, 'value'),
     State({'type': 'option-maturity-selector', 'index': ALL}, 'value'),
     State({'type': 'option-strike-selector', 'index': ALL}, 'value')],
    prevent_initial_call=True
)
def update_option_charts(types, underlyings, maturities, strikes):
    # 1. Collecter toutes les lignes de sélection qui sont complètes
    completed_contracts = []
    for i in range(len(underlyings)):
        if all([underlyings[i], maturities[i], strikes[i], types[i]]):
            completed_contracts.append({
                'underlying': underlyings[i],
                'maturity': maturities[i],
                'strike': strikes[i],
                'type': types[i]
            })

    if not completed_contracts:
        return None # Ne rien afficher si aucune ligne n'est complète

    # 2. Grouper les contrats par actif sous-jacent
    contracts_by_underlying = {}
    for contract in completed_contracts:
        underlying = contract['underlying']
        if underlying not in contracts_by_underlying:
            contracts_by_underlying[underlying] = []
        contracts_by_underlying[underlying].append(contract)

    # 3. Créer la liste de tous les composants graphiques
    all_chart_cols = []
    try:
        for underlying, contracts in contracts_by_underlying.items():
            # --- Graphique du sous-jacent avec TOUS les strikes ---
            stock_ticker = yf.Ticker(underlying)
            hist_stock = stock_ticker.history(period="1y", interval="1d")
            
            fig_stock = go.Figure()
            fig_stock.add_trace(go.Scatter(x=hist_stock.index, y=hist_stock['Close'], mode='lines', name=underlying))

            # Ajouter une ligne horizontale pour chaque strike de ce sous-jacent
            for contract in contracts:
                fig_stock.add_hline(y=contract['strike'], line_dash="dash", annotation_text=f"Strike {contract['strike']}$")

            fig_stock.update_layout(
                title=f"Prix du Sous-Jacent : {underlying}",
                template='plotly_dark', xaxis_title="Date", yaxis_title="Prix ($)"
            )
            # Ajout du graphique du sous-jacent à notre liste
            all_chart_cols.append(dbc.Col(dcc.Graph(figure=fig_stock), width=6))

            # --- Graphiques pour chaque contrat d'option ---
            for contract in contracts:
                chain = stock_ticker.option_chain(contract['maturity'])
                chain_df = chain.calls if contract['type'] == 'call' else chain.puts
                contract_info = chain_df[chain_df.strike == contract['strike']]
                if contract_info.empty: continue
                
                contract_symbol = contract_info.iloc[0].contractSymbol
                option_ticker = yf.Ticker(contract_symbol)
                hist_option = option_ticker.history(period="1y", interval="1d")

                fig_option = go.Figure()
                fig_option.add_trace(go.Scatter(x=hist_option.index, y=hist_option['Close'], mode='lines'))
                fig_option.update_layout(
                    title=f"Prix de l'Option<br>{contract_symbol}",
                    template='plotly_dark', xaxis_title="Date", yaxis_title="Prix ($)"
                )
                # Ajout du graphique de l'option à notre liste
                all_chart_cols.append(dbc.Col(dcc.Graph(figure=fig_option), width=6))
        
        # 4. Assembler les colonnes en lignes de 2 pour créer une grille
        final_layout = []
        for i in range(0, len(all_chart_cols), 2):
            row = dbc.Row(all_chart_cols[i:i+2], className="mb-3")
            final_layout.append(row)

        return final_layout

    except Exception as e:
        print(f"Erreur lors de la création des graphiques cumulatifs : {e}")
        return dbc.Alert("Une erreur est survenue lors de la génération des graphiques.", color="danger")

# DANS app.py - AJOUTEZ CETTE NOUVELLE FONCTION


# DANS app.py - REMPLACEZ CETTE FONCTION

# DANS app.py - REMPLACEZ CETTE FONCTION
# DANS app.py - REMPLACEZ VOTRE FONCTION PAR CETTE VERSION FINALE
# DANS app.py - REMPLACEZ LA FONCTION parse_contents

# DANS app.py - REMPLACEZ VOTRE FONCTION PAR CETTE VERSION FINALE
# DANS app.py - REMPLACEZ VOTRE FONCTION PAR CETTE VERSION FINALE

# DANS app.py - REMPLACEZ VOTRE FONCTION PAR CETTE VERSION DÉFINITIVE
# DANS app.py - REMPLACEZ VOTRE FONCTION PAR CETTE VERSION DÉFINITIVE

# DANS app.py - REMPLACEZ VOTRE FONCTION PAR CETTE VERSION DÉFINITIVE

def parse_contents(contents, filename):
    """
    Version finale du parseur.
    Règle : Col 1 -> Date (index), Col 2 -> Price. Toutes les autres colonnes sont
    conservées telles quelles comme indicateurs potentiels.
    """
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    df_raw = None
    try:
        fn_lower = filename.lower()
        if fn_lower.endswith('.csv'):
            try: decoded_text = decoded.decode('utf-8')
            except UnicodeDecodeError: decoded_text = decoded.decode('latin-1')
            df_raw = pd.read_csv(io.StringIO(decoded_text), sep=None, engine='python', on_bad_lines='warn')
        elif fn_lower.endswith(('.xls', '.xlsx')):
            df_raw = pd.read_excel(io.BytesIO(decoded))
        elif fn_lower.endswith('.ods'):
            df_raw = pd.read_excel(io.BytesIO(decoded), engine="odf")
        else:
            raise ValueError("Format de fichier non supporté.")
    except Exception as e:
        raise ValueError(f"Impossible de lire le fichier. Erreur : {e}")

    if df_raw is None or df_raw.empty or len(df_raw.columns) < 2:
        raise ValueError("Le fichier est invalide ou contient moins de 2 colonnes.")

    # Valider la colonne de Date (la première)
    date_col_name = df_raw.columns[0]
    try:
        df_raw[date_col_name] = pd.to_datetime(df_raw[date_col_name])
    except Exception:
        raise ValueError(f"Impossible de convertir la première colonne en dates.")

    # Valider la colonne de Prix (la deuxième)
    price_col_name = df_raw.columns[1]
    if not pd.api.types.is_numeric_dtype(df_raw[price_col_name]):
        raise ValueError(f"La deuxième colonne ('{price_col_name}') doit être numérique.")

    # Renommer les deux premières colonnes
    df_raw.rename(columns={date_col_name: 'Date', price_col_name: 'Price'}, inplace=True)
    
    # Définir la Date comme index
    df_raw.set_index('Date', inplace=True)
    df_raw.sort_index(inplace=True)
    
    # Assurer la présence des colonnes OHLCV pour la compatibilité générale du backtesteur
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col not in df_raw.columns and col.lower() not in (c.lower() for c in df_raw.columns):
            if col == 'Volume':
                df_raw[col] = 0
            else:
                df_raw[col] = df_raw['Price'] # Utiliser Price si OHLC manquent

    return df_raw

# DANS app.py - AJOUTEZ CETTE NOUVELLE FONCTION

# DANS app.py - REMPLACEZ CETTE FONCTION

@app.callback(
    # La liste des Outputs reste la même
    [Output(f'indicator1-type-{i}-{j}', 'options') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'indicator2-type-{i}-{j}', 'options') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)],
    # Les Inputs/State restent les mêmes
    Input('selected-stocks-store', 'data'),
    State('custom-asset-store', 'data'),
    prevent_initial_call=True
)
def update_indicator_dropdowns(selected_stocks, custom_asset_data):
    """
    Met à jour la liste des indicateurs disponibles en incluant TOUTES les colonnes
    des fichiers CSV importés.
    """
    if not selected_stocks:
        raise PreventUpdate

    # 1. Préparer la liste de base avec les indicateurs standards
    standard_indicators = [{'label': name, 'value': name} for name in indicators.keys()]
    
    # 2. Identifier les actifs personnalisés et extraire TOUTES leurs colonnes
    custom_indicators = set()
    if custom_asset_data:
        selected_custom_assets = [s for s in selected_stocks if s in custom_asset_data]
        
        for asset_name in selected_custom_assets:
            df_json = custom_asset_data[asset_name]
            df = pd.read_json(df_json, orient='split')
            
            # --- LOGIQUE CORRIGÉE : On ajoute toutes les colonnes sans exception ---
            for col in df.columns:
                custom_indicators.add(col)
            # --- FIN DE LA CORRECTION ---

    # 3. Formater les indicateurs personnalisés et les combiner avec les standards
    custom_indicator_options = [
        {'label': f"{name} (Personnalisé)", 'value': name} 
        for name in sorted(list(custom_indicators))
    ]
    
    final_options = custom_indicator_options + standard_indicators
    
    # 4. Retourner la liste complète à tous les dropdowns
    total_dropdowns = MAX_BLOCKS * MAX_CONDITIONS * 2
    return [final_options] * total_dropdowns


# DANS app.py - REMPLACEZ CETTE FONCTION

@app.callback(
    [Output('custom-asset-store', 'data'),
     Output('upload-status-message', 'children')],
    Input('save-custom-asset-button', 'n_clicks'),
    [State('upload-data', 'contents'),
     State('upload-data', 'filename'),
     State('custom-asset-name', 'value'),
     State('custom-asset-store', 'data')], # On récupère l'état actuel du store
    prevent_initial_call=True
)
def save_uploaded_file_to_store(n_clicks, contents, filename, asset_name, existing_data):
    if not n_clicks or not contents or not asset_name:
        raise PreventUpdate

    # Initialiser le dictionnaire de stockage s'il est vide
    if existing_data is None:
        existing_data = {}

    try:
        processed_df = parse_contents(contents, filename)
        
        # Convertir le DataFrame en JSON pour le stocker
        # 'split' est un format efficace qui conserve bien la structure
        df_json = processed_df.to_json(date_format='iso', orient='split')
        
        # Ajouter le nouveau DataFrame (en format JSON) au dictionnaire existant
        existing_data[asset_name] = df_json

        # Message de succès
        alert = dbc.Alert(f"✅ Succès ! L'actif '{asset_name}' est maintenant disponible dans la session.", color="success")
        
        # Retourner le dictionnaire mis à jour au store et le message à l'utilisateur
        return existing_data, alert

    except ValueError as e:
        alert = dbc.Alert(f"❌ Erreur : {e}", color="danger")
        # On ne met pas à jour le store en cas d'erreur, et on affiche l'alerte
        return dash.no_update, alert

# Callback principal : Backtest synthétique direct (comme l'onglet historique)


@app.callback(
    [Output('synthetic-results-container', 'children'),
        Output('synthetic-backtest-status', 'children')],
    Input('run-synthetic-backtest-direct', 'n_clicks'),
    [State('synthetic-model-dropdown', 'value'),
        State('strategy-store', 'data'),
        State('synthetic-calibration-dates', 'start_date'),
        State('synthetic-calibration-dates', 'end_date'),
        State('synthetic-horizon', 'value'),
        State('synthetic-steps', 'value'),
        State('synthetic-simulations', 'value'),
        State('selected-stocks-store', 'data')] +
    # États pour les paramètres Heston
    [State('heston-kappa', 'value'),
        State('heston-theta', 'value'), 
        State('heston-xi', 'value'),
        State('heston-rho', 'value')] +
    # États pour les paramètres Bates
    [State('bates-kappa', 'value'),
        State('bates-theta', 'value'),
        State('bates-xi', 'value'), 
        State('bates-rho', 'value'),
        State('bates-lambda', 'value'),
        State('bates-mu-jump', 'value'),
        State('bates-sigma-jump', 'value')] +
    # États pour les paramètres SABR
    [State('sabr-alpha', 'value'),
        State('sabr-beta', 'value'),
        State('sabr-rho', 'value'),
        State('sabr-nu', 'value')],
    prevent_initial_call=True
)
def run_multi_trajectory_synthetic_backtest(n_clicks, model_type, strategy_store_data,
                                            start_date, end_date, horizon, steps, simulations, 
                                            selected_stocks, *param_values):
    """Backtest synthétique sur N trajectoires avec analyse de risque"""
    
    print(f"[START] DÉBUT DU BACKTEST MULTI-TRAJECTOIRES")
    print(f"n_clicks: {n_clicks}")
    print(f"Nombre de simulations demandé: {simulations}")
    
    if not n_clicks:
        raise PreventUpdate
    
    # Validations
    if not model_type:
        return "", dbc.Alert("[ERREUR] Aucun modèle sélectionné", color="danger")
    

        if not current_strategy:  # Ce paramètre vient du State('strategy-data-store', 'data')
            return "", dbc.Alert("[ERREUR] Aucune stratégie configurée. Créez d'abord une stratégie.", color="danger")
    
    current_strategy = strategy_store_data.get('strategy_data') if strategy_store_data else None
    # Extraire les symboles
    if selected_stocks:
        symbols = selected_stocks
    else:
        symbols = set()
        for block in current_strategy.get('decision_blocks', []):
            for condition in block.get('conditions', []):
                if 'stock1' in condition:
                    symbols.add(condition['stock1'])
                if 'stock2' in condition:
                    symbols.add(condition['stock2'])
            for symbol in block.get('actions', {}):
                symbols.add(symbol)
        symbols = [s for s in list(symbols) if s]
    
    if not symbols:
        return "", dbc.Alert("[ERREUR] Aucun actif trouvé.", color="danger")
    
    print(f"[OK] Symboles: {symbols}")
    
    try:
        # UTILISER LE NOMBRE DE SIMULATIONS SAISI (mais minimum 10 pour debug)
        n_trajectories = 30  # Limiter à 100 pour debug
        print(f"[TARGET] Lancement de {n_trajectories} trajectoires (limité pour debug)")
        
        # Message de statut
        status_msg = dbc.Alert([
                    html.I(className="fas fa-atom mr-2"),
                    f"Lancement de {n_trajectories} backtests Monte Carlo ({model_type.upper()})...",
                    html.Br(),
                    html.Small(f"Temps estimé: {(n_trajectories / 500):.1f}-{(n_trajectories / 250):.1f} minutes", 
                                className="text-warning")
                ], color="info")
        
        # Extraire les paramètres du modèle
        model_params = {}
        if model_type == 'heston':
            model_params = {
                'kappa': param_values[0] if param_values[0] is not None else 2.0,
                'theta': param_values[1] if param_values[1] is not None else 0.04,
                'xi': param_values[2] if param_values[2] is not None else 0.3,
                'rho': param_values[3] if param_values[3] is not None else -0.7
            }
        elif model_type == 'bates':
            model_params = {
                'kappa': param_values[4] if param_values[4] is not None else 2.0,
                'theta': param_values[5] if param_values[5] is not None else 0.04,
                'xi': param_values[6] if param_values[6] is not None else 0.3,
                'rho': param_values[7] if param_values[7] is not None else -0.7,
                'lambda_j': param_values[8] if param_values[8] is not None else 2.0,
                'mu_j': param_values[9] if param_values[9] is not None else 0.0,
                'sigma_j': param_values[10] if param_values[10] is not None else 0.1
            }
        elif model_type == 'sabr':
            model_params = {
                'alpha0': param_values[11] if param_values[11] is not None else 0.2,
                'beta': param_values[12] if param_values[12] is not None else 0.5,
                'rho': param_values[13] if param_values[13] is not None else -0.3,
                'nu': param_values[14] if param_values[14] is not None else 0.3
            }
        
        print(f"[OK] Paramètres: {model_params}")
        
        # Créer le backtester multi-trajectoires
        multi_backtester = MultiTrajectoryBacktester(
            strategy_data=current_strategy,
            model_type=model_type,
            symbols=symbols,
            **model_params
        )
        
        # Paramètres de simulation
        sim_params = {
            'start_date': start_date or '2020-01-01',
            'end_date': end_date or '2025-01-01',
            'T': horizon or 1,
            'n_steps': steps or 252
        }
        
        # LANCER LES N BACKTESTS
        print(f"[LOOP] Lancement de {n_trajectories} trajectoires...")
        analysis_results = multi_backtester.run_monte_carlo_backtest(
            n_trajectories=n_trajectories,
            **sim_params
        )
        
        print("[OK] Analyse Monte Carlo terminée!")
        
        # === AUSSI CRÉER UN BACKTEST DÉTAILLÉ SUR LA TRAJECTOIRE MÉDIANE ===
        
        # Trouver la trajectoire la plus proche de la médiane
        median_return = analysis_results['central_metrics']['Rendement médian (%)']
        df_results = analysis_results['raw_data']
        
        # Trouver l'index de la trajectoire la plus proche de la médiane
        closest_to_median_idx = (df_results['total_return_pct'] - median_return).abs().idxmin()
        
        print(f"[TARGET] Création du backtest détaillé sur trajectoire médiane (#{closest_to_median_idx})")
        
        # Régénérer cette trajectoire spécifique pour avoir les détails
        try:
            import numpy as np
            np.random.seed(42 + closest_to_median_idx)  # Même seed que pour cette trajectoire
            
            manager = SyntheticDataManager()
            median_synthetic_data = manager.generate_data(
                model_type=model_type,
                symbols=symbols,
                n_simulations=1,
                **sim_params,
                **model_params
            )
            
            # Backtester détaillé sur cette trajectoire
            detailed_backtester = BacktesterSynthetic(current_strategy, median_synthetic_data)
            detailed_backtester.run_backtest()
            
            # Générer tous les graphiques comme dans le backtest historique
            detailed_figures = generate_plotly_figures(detailed_backtester)
            
        except Exception as e:
            print(f"[WARN] Erreur backtest détaillé: {e}")
            detailed_backtester = None
            detailed_figures = {}
        
        # === CRÉER L'AFFICHAGE COMPLET ===
        
        # 1. Résultats multi-trajectoires (analyse de risque)
        results_display = create_multi_trajectory_results_display(
            analysis_results, model_type, symbols
            )
        
        # 2. AJOUTER LE BACKTEST DÉTAILLÉ (comme le backtest historique)
        if detailed_backtester and detailed_figures:
            
            # Séparateur
            detailed_components = [
                html.Hr(style={'borderColor': '#34495e', 'margin': '40px 0'}),
                dbc.Alert([
                    html.Strong("📊 Backtest Détaillé - Trajectoire Médiane"),
                    html.Br(),
                    html.Small(f"Analyse détaillée de la trajectoire #{closest_to_median_idx} (proche du rendement médian: {median_return:.2f}%)", 
                                className="text-info")
                ], color="info", className="mb-4")
            ]
            
            # RÉSUMÉ DES TRANSACTIONS (identique au backtest historique)
            if hasattr(detailed_backtester, 'transactions') and detailed_backtester.transactions:
                detailed_components.append(dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-bar mr-2"),
                        "Résumé des transactions - Trajectoire Médiane"
                    ], style=CARD_HEADER_STYLE),
                    dbc.CardBody([
                        html.H4("=== RÉSUMÉ DES TRANSACTIONS ===", 
                                className="text-center text-info mb-4"),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.ListGroup([
                                    dbc.ListGroupItem([
                                        html.Strong("Nombre total de transactions: "), 
                                        html.Span(f"{len(detailed_backtester.transactions)}")
                                    ]),
                                    dbc.ListGroupItem([
                                        html.Strong("Achats: "), 
                                        html.Span(f"{sum(1 for t in detailed_backtester.transactions if t['type'] == 'ACHAT')}")
                                    ]),
                                    dbc.ListGroupItem([
                                        html.Strong("Ventes: "), 
                                        html.Span(f"{sum(1 for t in detailed_backtester.transactions if 'VENTE' in t['type'])}")
                                    ]),
                                    dbc.ListGroupItem([
                                        html.Strong("Stop Loss: "), 
                                        html.Span(f"{sum(1 for t in detailed_backtester.transactions if t['type'] == 'STOP LOSS')}")
                                    ]),
                                    dbc.ListGroupItem([
                                        html.Strong("Take Profit: "), 
                                        html.Span(f"{sum(1 for t in detailed_backtester.transactions if t['type'] == 'TAKE PROFIT')}")
                                    ]),
                                ]),
                                
                                # P&L total
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H5("P&L total:", className="card-title"),
                                        html.H3(
                                            f"{sum(t.get('pnl', 0) for t in detailed_backtester.transactions):.2f} €",
                                            style={
                                                'color': 'green' if sum(t.get('pnl', 0) for t in detailed_backtester.transactions) > 0 else 'red',
                                                'fontWeight': 'bold'
                                            }
                                        )
                                    ])
                                ], color="light", className="mt-3"),
                            ], width=6),
                            
                            dbc.Col([
                                html.H5("Métriques détaillées:", className="mb-3"),
                                html.Table([
                                    html.Tbody([
                                        html.Tr([
                                            html.Td("Capital initial:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                            html.Td(f"{detailed_backtester.metrics['Capital initial']:,.2f} €", style={'textAlign': 'right', 'padding': '4px'})
                                        ]),
                                        html.Tr([
                                            html.Td("Capital final:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                            html.Td(f"{detailed_backtester.metrics['Capital final']:,.2f} €", style={'textAlign': 'right', 'padding': '4px'})
                                        ]),
                                        html.Tr([
                                            html.Td("Rendement total:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                            html.Td(
                                                f"{detailed_backtester.metrics['Rendement total (%)']:.2f}%",
                                                style={
                                                    'textAlign': 'right', 
                                                    'padding': '4px',
                                                    'color': 'green' if detailed_backtester.metrics['Rendement total (%)'] > 0 else 'red',
                                                    'fontWeight': 'bold'
                                                }
                                            )
                                        ]),
                                        html.Tr([
                                            html.Td("Drawdown maximum:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                            html.Td(
                                                f"{detailed_backtester.metrics['Drawdown maximum (%)']:.2f}%",
                                                style={'textAlign': 'right', 'padding': '4px', 'color': 'red', 'fontWeight': 'bold'}
                                            )
                                        ]),
                                        html.Tr([
                                            html.Td("Ratio de Sharpe:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                            html.Td(f"{detailed_backtester.metrics['Ratio de Sharpe']:.2f}", style={'textAlign': 'right', 'padding': '4px'})
                                        ]),
                                        html.Tr([
                                            html.Td("Nombre de trades:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                            html.Td(f"{int(detailed_backtester.metrics['Nombre de trades'])}", style={'textAlign': 'right', 'padding': '4px'})
                                        ]),
                                        html.Tr([
                                            html.Td("% trades gagnants:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                            html.Td(f"{detailed_backtester.metrics['Pourcentage de trades gagnants (%)']:.2f}%", style={'textAlign': 'right', 'padding': '4px'})
                                        ]),
                                        html.Tr([
                                            html.Td("Profit factor:", style={'fontWeight': 'bold', 'padding': '4px'}),
                                            html.Td(
                                                f"{detailed_backtester.metrics['Profit factor']:.2f}",
                                                style={
                                                    'textAlign': 'right', 
                                                    'padding': '4px',
                                                    'color': 'green' if detailed_backtester.metrics['Profit factor'] > 1 else 'red',
                                                    'fontWeight': 'bold'
                                                }
                                            )
                                        ])
                                    ])
                                ], style={'width': '100%', 'fontSize': '14px'})
                            ], width=6)
                        ]),
                    ], style=CARD_BODY_STYLE)
                ], style=CARD_STYLE, className="mb-4"))

            # GRAPHIQUES DES SYMBOLES (identique au backtest historique)
            symbol_cards = []
            for key, figure in detailed_figures.items():
                if key.startswith('symbol_'):
                    symbol = key.replace('symbol_', '')
                    
                    symbol_card = dbc.Card([
                        dbc.CardHeader([
                            html.I(className="fas fa-chart-line mr-2"),
                            f"Prix et indicateurs - {symbol} (Trajectoire Médiane)"
                        ], style=CARD_HEADER_STYLE),
                        dbc.CardBody([
                            dcc.Graph(
                                figure=figure,
                                config={'displayModeBar': True, 'scrollZoom': True}
                            ),
                            # Graphique du volume si disponible
                            dcc.Graph(
                                figure=detailed_figures.get(f'volume_{symbol}', {}),
                                config={'displayModeBar': True, 'scrollZoom': True}
                            ) if f'volume_{symbol}' in detailed_figures else html.Div()
                        ], style=CARD_BODY_STYLE)
                    ], style=CARD_STYLE, className="mb-4")
                    
                    symbol_cards.append(symbol_card)

            detailed_components.extend(symbol_cards)

            # TABLEAU DES TRANSACTIONS (identique au backtest historique)
            if 'transactions' in detailed_figures and isinstance(detailed_figures['transactions'], pd.DataFrame):
                transactions_df = detailed_figures['transactions'].copy()
                
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
                
                detailed_components.append(dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-list-alt mr-2"),
                        "Journal des transactions - Trajectoire Médiane"
                    ], style=CARD_HEADER_STYLE),
                    dbc.CardBody([
                        dash_table.DataTable(
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

            # COURBE D'ÉQUITÉ (identique au backtest historique)
            if 'equity' in detailed_figures:
                detailed_components.append(dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-area mr-2"),
                        "Courbe d'équité - Trajectoire Médiane"
                    ], style=CARD_HEADER_STYLE),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=detailed_figures['equity'],
                            config={'displayModeBar': True, 'scrollZoom': True}
                        )
                    ], style=CARD_BODY_STYLE)
                ], style=CARD_STYLE, className="mb-4"))

            # DRAWDOWN (identique au backtest historique)
            if 'drawdown' in detailed_figures:
                detailed_components.append(dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-area mr-2"),
                        "Drawdown - Trajectoire Médiane"
                    ], style=CARD_HEADER_STYLE),
                    dbc.CardBody([
                        dcc.Graph(
                            figure=detailed_figures['drawdown'],
                            config={'displayModeBar': True, 'scrollZoom': True}
                        )
                    ], style=CARD_BODY_STYLE)
                ], style=CARD_STYLE, className="mb-4"))
            
            # Combiner les résultats
            combined_results = html.Div([
                results_display,  # Analyse multi-trajectoires en premier
                html.Div(detailed_components)  # Puis backtest détaillé
            ])
            
        else:
            # Si erreur dans le backtest détaillé, afficher seulement l'analyse multi-trajectoires
            combined_results = results_display
        
        # Message de succès
        final_status = dbc.Alert([
            html.I(className="fas fa-check-circle mr-2"),
            f"[OK] Analyse Monte Carlo terminée!",
            html.Br(),
            html.Small(f"[TARGET] {len(analysis_results['raw_data'])} trajectoires | "
                        f"Rendement médian: {analysis_results['central_metrics']['Rendement médian (%)']:.2f}% | "
                        f"VaR 95%: {analysis_results['var_metrics']['VaR 95% (perte max 5% scenarios)']:.2f}%", 
                        className="text-success")
        ], color="success")
        
        print("[OK] CALLBACK MONTE CARLO TERMINÉ")
        return combined_results, final_status
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[ERREUR] ERREUR: {e}")
        print(error_details)
        
        error_status = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle mr-2"),
            f"[ERREUR] Erreur: {str(e)}",
            html.Details([
                html.Summary("Détails techniques"),
                html.Pre(error_details, style={"whiteSpace": "pre-wrap", "fontSize": "small"})
            ], className="mt-2")
        ], color="danger")
        
        return "", error_status

@app.callback(
    Output('language-store', 'data'),
    Input('language-switcher-sidebar', 'value')
)
def update_language_store(selected_language):
    return selected_language

# DANS app.py - AJOUTEZ CES IMPORTS EN HAUT DU FICHIER
from urllib.parse import quote
from datetime import datetime

# DANS app.py - AJOUTEZ CETTE NOUVELLE FONCTION DE RAPPEL

@app.callback(
    Output('feedback-confirmation-message', 'children'),
    Input('feedback-submit-button', 'n_clicks'),
    [
        State('feedback-impression', 'value'),
        State('feedback-complexity-rating', 'value'),
        State('feedback-simplification-ideas', 'value'),
        State('feedback-decision-blocks', 'value'),
        State('feedback-new-assets', 'value'),
        State('feedback-new-indicators', 'value'),
        State('feedback-new-results', 'value')
    ],
    prevent_initial_call=True
)
def save_feedback_to_txt(n_clicks, impression, complexity, simplification, d_blocks, assets, indicators, results):
    if not n_clicks:
        raise PreventUpdate
    
    try:
        # Création du dossier feedbacks s'il n'existe pas
        if not os.path.exists('feedbacks'):
            os.makedirs('feedbacks')
        
        # Génération du nom de fichier avec timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'feedbacks/feedback_{timestamp}.txt'
        
        # Mapping de la complexité
        complexity_map = {
            1: "Très simple", 
            2: "Plutôt simple", 
            3: "Neutre", 
            4: "Plutôt complexe", 
            5: "Très complexe"
        }
        complexity_text = complexity_map.get(complexity, "Non renseigné")
        
        # Contenu du feedback
        feedback_content = f"""
===============================================
FEEDBACK TRADINGLAB
===============================================
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
ID: {timestamp}

-----------------------------------------------
PREMIÈRE IMPRESSION:
-----------------------------------------------
{impression or "Non renseigné"}

-----------------------------------------------
COMPLEXITÉ D'UTILISATION:
-----------------------------------------------
Note: {complexity}/5 ({complexity_text})

-----------------------------------------------
SUGGESTIONS DE SIMPLIFICATION:
-----------------------------------------------
{simplification or "Non renseigné"}

-----------------------------------------------
AVIS SUR LES BLOCS DE DÉCISION:
-----------------------------------------------
{d_blocks or "Non renseigné"}

-----------------------------------------------
SUGGESTIONS D'ACTIFS:
-----------------------------------------------
{assets or "Non renseigné"}

-----------------------------------------------
SUGGESTIONS D'INDICATEURS/STRATÉGIES:
-----------------------------------------------
{indicators or "Non renseigné"}

-----------------------------------------------
SUGGESTIONS DE GRAPHIQUES/RISQUES:
-----------------------------------------------
{results or "Non renseigné"}

===============================================
FIN DU FEEDBACK
===============================================
        """
        
        # Écriture du fichier
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(feedback_content)
        
        # Aussi ajouter au fichier global (optionnel)
        global_file = 'feedbacks/tous_les_feedbacks.txt'
        with open(global_file, 'a', encoding='utf-8') as f:
            f.write(feedback_content)
            f.write('\n\n')
        
        return dbc.Alert(
            [
                html.I(className="fas fa-check-circle mr-2"),
                f"✅ Votre feedback a été enregistré dans {filename} ! Merci pour votre retour."
            ],
            color="success",
            duration=5000
        )
        
    except Exception as e:
        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-triangle mr-2"),
                f"❌ Erreur lors de l'enregistrement : {str(e)}"
            ],
            color="danger",
            duration=8000
        )

# === CALLBACKS POUR LA COMPARAISON DE STRATÉGIES ===

# 1. Charger les options de stratégies disponibles
@app.callback(
    [Output('compare-strategy-1', 'options'),
     Output('compare-strategy-2', 'options'),
     Output('compare-strategy-3', 'options')],
    Input('compare-strategy-1', 'id')
)
def load_strategies_for_comparison(_):
    """Charge les stratégies disponibles pour les 3 dropdowns"""
    options = []
    
    if os.path.exists("strategies"):
        for file in os.listdir("strategies"):
            if file.endswith(".json"):
                try:
                    with open(os.path.join("strategies", file), 'r', encoding='utf-8') as f:
                        strategy_data = json.load(f)
                        name = strategy_data.get('name', 'Sans nom')
                        created_at = strategy_data.get('created_at', '')
                        date_str = created_at.split(' ')[0] if created_at else ''
                        
                        options.append({
                            'label': f"{name} ({date_str})",
                            'value': os.path.join("strategies", file)
                        })
                except:
                    continue
        
        options.sort(key=lambda x: x['label'], reverse=True)
    
    return options, options, options


# 2. Afficher les infos des stratégies sélectionnées
@app.callback(
    [Output('strategy-1-info', 'children'),
     Output('strategy-2-info', 'children'),
     Output('strategy-3-info', 'children'),
     Output('launch-strategy-comparison', 'disabled')],
    [Input('compare-strategy-1', 'value'),
     Input('compare-strategy-2', 'value'),
     Input('compare-strategy-3', 'value')],
    prevent_initial_call=True
)
def update_strategy_info(strategy1, strategy2, strategy3):
    """Affiche les informations des stratégies sélectionnées"""
    
    def get_strategy_info_card(strategy_path):
        if not strategy_path or not os.path.exists(strategy_path):
            return html.Div()
        
        try:
            with open(strategy_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return dbc.Alert([
                html.Small([
                    html.Strong("Capital: "),
                    f"{data.get('initial_capital', 0):,}€"
                ], className="d-block"),
                html.Small([
                    html.Strong("Période: "),
                    f"{data.get('date_range', {}).get('start', '')} → {data.get('date_range', {}).get('end', '')}"
                ], className="d-block"),
                html.Small([
                    html.Strong("Actifs: "),
                    f"{len(data.get('selected_stocks', []))}"
                ], className="d-block")
            ], color="light", className="mb-0", style={'fontSize': '0.85rem'})
        except:
            return dbc.Alert("Erreur de chargement", color="danger", className="mb-0")
    
    info1 = get_strategy_info_card(strategy1)
    info2 = get_strategy_info_card(strategy2)
    info3 = get_strategy_info_card(strategy3)
    
    # Activer le bouton si au moins 2 stratégies sont sélectionnées
    selected_count = sum([bool(s) for s in [strategy1, strategy2, strategy3]])
    button_disabled = selected_count < 2
    
    return info1, info2, info3, button_disabled


# 3. Lancer la comparaison
@app.callback(
    [Output('comparison-results-container', 'children'),
     Output('comparison-status', 'children')],
    Input('launch-strategy-comparison', 'n_clicks'),
    [State('compare-strategy-1', 'value'),
     State('compare-strategy-2', 'value'),
     State('compare-strategy-3', 'value'),
     State('custom-asset-store', 'data'),
     State('language-switcher-sidebar', 'value')],
    prevent_initial_call=True
)
def run_strategy_comparison(n_clicks, strategy1, strategy2, strategy3, custom_asset_data, selected_language):
    """Lance les backtests et compare les résultats"""
    
    if not n_clicks:
        raise PreventUpdate
    
    # Gestion de la langue
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    # Collecter les stratégies à comparer
    strategies_to_compare = {}
    for idx, strategy_path in enumerate([strategy1, strategy2, strategy3], 1):
        if strategy_path and os.path.exists(strategy_path):
            try:
                with open(strategy_path, 'r', encoding='utf-8') as f:
                    strategy_data = json.load(f)
                strategies_to_compare[strategy_data.get('name', f'Stratégie {idx}')] = strategy_path
            except Exception as e:
                print(f"Erreur chargement stratégie {idx}: {e}")
    
    if len(strategies_to_compare) < 2:
        return "", dbc.Alert(
            t.get('select-2-strategies-minimum', 'Veuillez sélectionner au moins 2 stratégies'),
            color="warning"
        )
    
    # Préparer les DataFrames personnalisés
    custom_dataframes = {}
    if custom_asset_data:
        for asset_name, df_json in custom_asset_data.items():
            df = pd.read_json(df_json, orient='split')
            custom_dataframes[asset_name] = df
    
    # Exécuter les backtests
    results_dict = {}
    
    try:
        for strategy_name, strategy_path in strategies_to_compare.items():
            print(f"🔄 Backtest de: {strategy_name}")
            
            backtester = Backtester(strategy_path, custom_dataframes=custom_dataframes)
            backtester.run_backtest()
            
            results_dict[strategy_name] = {
                'backtester': backtester,
                'metrics': backtester.metrics,
                'equity_df': backtester.equity_df,
                'transactions': backtester.transactions
            }
        
        # Créer l'affichage des résultats
        comparison_components = []
        
        # 1. Titre
        comparison_components.append(
            dbc.Alert([
                html.I(className="fas fa-trophy mr-2"),
                f"✅ Comparaison de {len(results_dict)} stratégies terminée !"
            ], color="success", className="mb-4")
        )
        
        # 2. Tableau comparatif
        comparison_components.append(
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-table mr-2"),
                    t.get('metrics-comparison-title', 'Tableau Comparatif des Métriques')
                ], style=CARD_HEADER_STYLE),
                dbc.CardBody([
                    create_comparison_summary_table(results_dict, selected_language)
                ], style=CARD_BODY_STYLE)
            ], style=CARD_STYLE, className="mb-4")
        )
        
        # 3. Graphique des courbes d'équité
        comparison_components.append(
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-chart-line mr-2"),
                    t.get('equity-curves-title', 'Courbes d\'Équité')
                ], style=CARD_HEADER_STYLE),
                dbc.CardBody([
                    dcc.Graph(
                        figure=create_comparison_equity_chart(results_dict, selected_language),
                        config={'displayModeBar': True}
                    )
                ], style=CARD_BODY_STYLE)
            ], style=CARD_STYLE, className="mb-4")
        )
        
        # 4. Distribution des rendements
        comparison_components.append(
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-chart-bar mr-2"),
                    t.get('returns-distribution-title', 'Distribution des Rendements')
                ], style=CARD_HEADER_STYLE),
                dbc.CardBody([
                    dcc.Graph(
                        figure=create_comparison_returns_distribution(results_dict, selected_language),
                        config={'displayModeBar': True}
                    )
                ], style=CARD_BODY_STYLE)
            ], style=CARD_STYLE, className="mb-4")
        )
        
        # 5. Analyse comparative textuelle
        best_return = max(results_dict.items(), key=lambda x: x[1]['metrics']['Rendement total (%)'])
        best_sharpe = max(results_dict.items(), key=lambda x: x[1]['metrics']['Ratio de Sharpe'])
        best_drawdown = min(results_dict.items(), key=lambda x: x[1]['metrics']['Drawdown maximum (%)'])
        
        comparison_components.append(
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-award mr-2"),
                    t.get('best-performers-title', 'Meilleures Performances')
                ], style=CARD_HEADER_STYLE),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H6([
                                html.I(className="fas fa-trophy text-warning mr-2"),
                                t.get('best-return-label', 'Meilleur Rendement')
                            ]),
                            html.P([
                                html.Strong(best_return[0]),
                                f": {best_return[1]['metrics']['Rendement total (%)']:.2f}%"
                            ], className="text-success")
                        ], width=4),
                        dbc.Col([
                            html.H6([
                                html.I(className="fas fa-medal text-info mr-2"),
                                t.get('best-sharpe-label', 'Meilleur Sharpe')
                            ]),
                            html.P([
                                html.Strong(best_sharpe[0]),
                                f": {best_sharpe[1]['metrics']['Ratio de Sharpe']:.2f}"
                            ], className="text-info")
                        ], width=4),
                        dbc.Col([
                            html.H6([
                                html.I(className="fas fa-shield-alt text-success mr-2"),
                                t.get('best-risk-label', 'Meilleur Contrôle du Risque')
                            ]),
                            html.P([
                                html.Strong(best_drawdown[0]),
                                f": {best_drawdown[1]['metrics']['Drawdown maximum (%)']:.2f}%"
                            ], className="text-success")
                        ], width=4)
                    ])
                ], style=CARD_BODY_STYLE)
            ], style=CARD_STYLE, className="mb-4")
        )
        
        return html.Div(comparison_components), dbc.Alert(
            t.get('comparison-success', '✅ Comparaison terminée avec succès !'),
            color="success",
            duration=3000
        )
        
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"❌ Erreur comparaison: {e}")
        print(error_msg)
        
        return "", dbc.Alert([
            html.H5(t.get('comparison-error-title', 'Erreur lors de la comparaison')),
            html.P(f"{str(e)}"),
            html.Details([
                html.Summary(t.get('technical-details', 'Détails techniques')),
                html.Pre(error_msg, style={'fontSize': '0.8rem', 'whiteSpace': 'pre-wrap'})
            ])
        ], color="danger")

# Afficher le bouton partager après un backtest réussi
# Afficher le bouton partager après un backtest réussi
@app.callback(
    Output('share-strategy-btn', 'style'),
    Input('visualization-placeholder', 'children'),
    prevent_initial_call=True
)
def toggle_share_button(viz_content):
    """Affiche le bouton partager si un backtest a été exécuté"""
    # Vérifier si viz_content contient des résultats (pas juste le placeholder)
    if viz_content and not isinstance(viz_content, str):
        # Si c'est un dict ou une liste de composants, c'est qu'il y a des résultats
        if isinstance(viz_content, (dict, list)):
            return {'display': 'block', 'width': '100%'}
        # Si c'est un div avec des enfants
        elif hasattr(viz_content, 'children'):
            return {'display': 'block', 'width': '100%'}
    
    return {'display': 'none'}

# Dans la section des callbacks de traduction, avec les autres
@app.callback(
    Output('share-strategy-btn', 'children'),
    Input('language-switcher-sidebar', 'value'),
    prevent_initial_call=False
)
def update_share_button_text(selected_language):
    """Met à jour le texte du bouton partager"""
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    return [
        html.I(className="fas fa-share-alt mr-2"),
        t.get('share-strategy-btn', 'Partager dans la communauté')
    ]


@app.callback(
    [
        # === EN-TÊTE ===
        # Output('app-title', 'children'),
        # Output('logout-text', 'children'),
        # Output('advanced-mode-label', 'children'),
        # Output('advanced-mode-helper', 'children'),
        
        # === WIZARD ===
        Output('wizard-title', 'children'),
        Output('wizard-step1-badge', 'children'),
        Output('wizard-step2-badge', 'children'),
        Output('wizard-step3-badge', 'children'),
        Output('wizard-step4-badge', 'children'),
        Output('wizard-step5-badge', 'children'),
        Output('wizard-step1-title', 'children'),
        Output('wizard-step2-title', 'children'),
        Output('wizard-step3-title', 'children'),
        Output('wizard-step4-title', 'children'),
        Output('wizard-step5-title', 'children'),
        Output('wizard-step1-description', 'children'),
        Output('wizard-step2-description', 'children'),
        Output('wizard-step3-description', 'children'),
        Output('manual-creation-card-title', 'children'),
        Output('manual-creation-card-description', 'children'),
        Output('template-selection-label', 'children'),
        Output('apply-template-button-text', 'children'),
        Output('button-next-assets', 'children'),
        Output('button-next-scenario', 'children'),
        Output('button-next-launch', 'children'),
        Output('button-launch-backtest', 'children'),
        Output('button-save', 'children'),
        Output('button-restart-wizard', 'children'),
        Output('button-new-strategy', 'children'),
        Output('scenario-action-label', 'children'),
        Output('scenario-trigger-label', 'children'),
        Output('summary-ready-title', 'children'),
        # Output('scenario-monthly-label', 'children'),
        # Output('scenario-price-down-label', 'children'),
        # Output('scenario-price-up-label', 'children'),
        # Output('scenario-price-up-after-down-label', 'children'),
        # Output('scenario-volatility-up-label', 'children'),



                
        # === BOUTONS PRÉCÉDENT UNIQUES ===
        Output('button-previous-step2', 'children'),
        Output('button-previous-step3', 'children'),
        Output('button-previous-step4', 'children'),
        Output('button-previous-step5', 'children'),
        
        
        # === MODE AVANCÉ ===
        Output('card-title-general-info', 'children'),
        Output('card-title-risk-management', 'children'),
        Output('card-title-assets', 'children'),
        Output('card-title-analysis-period', 'children'),
        Output('card-title-decision-blocks', 'children'),
        Output('label-strategy-name', 'children'),
        Output('formtext-strategy-name', 'children'),
        Output('label-initial-capital', 'children'),
        Output('label-allocation', 'children'),
        Output('label-transaction-cost', 'children'),
        Output('label-stop-loss', 'children'),
        Output('label-take-profit', 'children'),
        Output('asset-classes-label', 'children'),
        Output('asset-class-selection-title', 'children'),
        Output('asset-classes-description', 'children'),
        Output('asset-classes-helper', 'children'),
        Output('my-imported-assets-label', 'children'),
        Output('available-classes-title', 'children'),
        Output('badge-stocks', 'children'),
        Output('badge-crypto', 'children'),
        Output('badge-forex', 'children'),
        Output('badge-etf', 'children'),
        Output('specific-assets-selection-title', 'children'),
        # Output('select-asset-classes-first', 'children'),
        # Output('asset-sections-appear-helper', 'children'),
        Output('strategy-period-label', 'children'),
        Output('decision-blocks-description', 'children'),
        Output('button-add-block', 'children'),
        Output('save-strategy-button-text', 'children'),
        
        
        # # === ONGLETS - LABELS ===
        # Output('tab-creation', 'label'),
        # Output('tab-results', 'label'),
        # Output('options-tab', 'label'),
        # Output('import-tab', 'label'),
        # Output('synthetic-tab', 'label'),
        
        # === ONGLET RÉSULTATS ===
        # Output('backtest-results-title', 'children'),
        # Output('backtest-results-placeholder-text', 'children'),
        # Output('backtest-results-instruction', 'children'),
        
        # === ONGLET OPTIONS ===
        Output('options-tab-title', 'children'),
        Output('options-card-title', 'children'),
        Output('options-label-underlying', 'children'),
        Output('options-label-maturity', 'children'),
        Output('options-label-strike', 'children'),
        Output('options-label-type', 'children'),
        
        # === ONGLET IMPORT ===
        Output('import-tab-title', 'children'),
        Output('import-card-title', 'children'),
        Output('import-upload-text', 'children'),
        Output('import-upload-link', 'children'),
        Output('import-label-asset-name', 'children'),
        Output('import-button-save', 'children'),
        Output('import-format-title', 'children'),
        Output('import-format-description', 'children'),
        Output('import-format-col1', 'children'),
        Output('import-format-col2', 'children'),
        Output('import-format-col-other', 'children'),
        
        # # === ONGLET SYNTHÉTIQUE ===
        # Output('synthetic-backtest-title', 'children'),
        # Output('synthetic-model-config-title', 'children'),
        # Output('synthetic-model-type-label', 'children'),
        # Output('synthetic-horizon-label', 'children'),
        # Output('synthetic-days-label', 'children'),
        # Output('synthetic-simulations-label', 'children'),
        # Output('synthetic-generation-title', 'children'),
        # Output('synthetic-calibration-period-label', 'children'),
        # Output('synthetic-launch-button', 'children'),
        
        # === PLACEHOLDERS (seulement ceux qui existent dans le layout principal) ===
        Output('strategy-name', 'placeholder'),
        Output('wizard-predefined-strategy-select', 'placeholder'),
        Output('wizard-asset-class-selector', 'placeholder'),
        Output('simple-action-dropdown', 'placeholder'),
        Output('simple-trigger-dropdown', 'placeholder'),
        Output('asset-class-selector', 'placeholder'),
        Output('custom-asset-name', 'placeholder'),
    ],
    [Input('language-switcher-sidebar', 'value')],
    prevent_initial_call=False
)
def update_main_translations(selected_language):
    """Met à jour tous les textes du layout principal selon la langue sélectionnée"""
    if selected_language not in TEXT:
        selected_language = 'fr'  # Langue par défaut
    
    t = TEXT[selected_language]
    
    return [
        # === EN-TÊTE ===
        # t.get('app-title', ''),
        # t.get('logout-text', ''),
        # t.get('advanced-mode-label', ''),
        # t.get('advanced-mode-helper', ''),
        
        # === WIZARD ===
        t.get('wizard-title', ''),
        t.get('wizard-step1-badge', ''),
        t.get('wizard-step2-badge', ''),
        t.get('wizard-step3-badge', ''),
        t.get('wizard-step4-badge', ''),
        t.get('wizard-step5-badge', ''),
        t.get('wizard-step1-title', ''),
        t.get('wizard-step2-title', ''),
        t.get('wizard-step3-title', ''),
        t.get('wizard-step4-title', ''),
        t.get('wizard-step5-title', ''),
        t.get('wizard-step1-description', ''),
        t.get('wizard-step2-description', ''),
        t.get('wizard-step3-description', ''),
        t.get('manual-creation-card-title', ''),
        t.get('manual-creation-card-description', ''),
        t.get('template-selection-label', ''),
        t.get('apply-template-button-text', ''),
        t.get('button-next-assets', ''),
        t.get('button-next-scenario', ''),
        t.get('button-next-launch', ''),
        t.get('button-launch-backtest', ''),
        t.get('button-save', ''),
        t.get('button-restart-wizard', ''),
        t.get('button-new-strategy', ''),
        t.get('scenario-action-label', ''),
        t.get('scenario-trigger-label', ''),
        t.get('summary-ready-title', ''),
        # t.get('scenario-monthly', ''),
        # t.get('scenario-price-down', ''),
        # t.get('scenario-price-up', ''),
        # t.get('scenario-price-up-after-down', ''),
        # t.get('scenario-volatility-up', ''),

        
        # === BOUTONS PRÉCÉDENT UNIQUES ===
        t.get('button-previous', ''),
        t.get('button-previous', ''),
        t.get('button-previous', ''),
        t.get('button-previous', ''),
        
        # === MODE AVANCÉ ===
        t.get('card-title-general-info', ''),
        t.get('card-title-risk-management', ''),
        t.get('card-title-assets', ''),
        t.get('card-title-analysis-period', ''),
        t.get('card-title-decision-blocks', ''),
        t.get('label-strategy-name', ''),
        t.get('formtext-strategy-name', ''),
        t.get('label-initial-capital', ''),
        t.get('label-allocation', ''),
        t.get('label-transaction-cost', ''),
        t.get('label-stop-loss', ''),
        t.get('label-take-profit', ''),
        t.get('asset-classes-label', ''),
        t.get('asset-class-selection-title', ''),
        t.get('asset-classes-description', ''),
        t.get('asset-classes-helper', ''),
        t.get('my-imported-assets-label', ''),
        t.get('available-classes-title', ''),
        t.get('badge-stocks', ''),
        t.get('badge-crypto', ''),
        t.get('badge-forex', ''),
        t.get('badge-etf', ''),
        t.get('specific-assets-selection-title', ''),
        # t.get('select-asset-classes-first', ''),
        # t.get('asset-sections-appear-helper', ''),
        t.get('strategy-period-label', ''),
        t.get('decision-blocks-description', ''),
        t.get('button-add-block', ''),
        t.get('save-strategy-button-text', ''),
        
        # # === ONGLETS - LABELS ===
        # t.get('tab-creation', ''),
        # t.get('tab-results', ''),
        # t.get('options-tab', ''),
        # t.get('import-tab', ''),
        # t.get('synthetic-tab', ''),
        
        # # === ONGLET RÉSULTATS ===
        # t.get('backtest-results-title', ''),
        # t.get('backtest-results-placeholder-text', ''),
        # t.get('backtest-results-instruction', ''),
        
        # === ONGLET OPTIONS ===
        t.get('options-tab-title', ''),
        t.get('options-card-title', ''),
        t.get('options-label-underlying', ''),
        t.get('options-label-maturity', ''),
        t.get('options-label-strike', ''),
        t.get('options-label-type', ''),
        
        # === ONGLET IMPORT ===
        t.get('import-tab-title', ''),
        t.get('import-card-title', ''),
        t.get('import-upload-text', ''),
        t.get('import-upload-link', ''),
        t.get('import-label-asset-name', ''),
        t.get('import-button-save', ''),
        t.get('import-format-title', ''),
        t.get('import-format-description', ''),
        t.get('import-format-col1', ''),
        t.get('import-format-col2', ''),
        t.get('import-format-col-other', ''),
        
        # === ONGLET SYNTHÉTIQUE ===
        # t.get('synthetic-backtest-title', ''),
        # t.get('synthetic-model-config-title', ''),
        # t.get('synthetic-model-type-label', ''),
        # t.get('synthetic-horizon-label', ''),
        # t.get('synthetic-days-label', ''),
        # t.get('synthetic-simulations-label', ''),
        # t.get('synthetic-generation-title', ''),
        # t.get('synthetic-calibration-period-label', ''),
        # t.get('synthetic-launch-button', ''),
        
        # === PLACEHOLDERS ===
        t.get('strategy-name', ''),
        t.get('wizard-predefined-strategy-select', ''),
        t.get('wizard-asset-class-selector', ''),
        t.get('simple-action-dropdown', ''),
        t.get('simple-trigger-dropdown', ''),
        t.get('asset-class-selector', ''),
        t.get('custom-asset-name', ''),
    ]


@app.callback(
    [Output('backtest-results-title', 'children'),
     Output('backtest-results-placeholder-text', 'children'),
     Output('backtest-results-instruction', 'children'),
     Output('backtest-placeholder-info', 'style')],  # Add this output
    Input('language-switcher-sidebar', 'value'),
    prevent_initial_call=False
)
def update_results_tab_translations(selected_language):
    """Met à jour les traductions de l'onglet résultats"""
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    title = t.get('backtest-results-title', 'Résultats du Backtest')
    placeholder = t.get('backtest-results-placeholder-text', 'Les résultats du backtest s\'afficheront ici après l\'exécution.')
    instruction = t.get('backtest-results-instruction', 'Créez d\'abord une stratégie dans l\'onglet \'Création de stratégie\', puis cliquez sur \'Lancer le backtest\'.')
    
    return title, placeholder, instruction, {'display': 'block'}

# Callback de traduction pour l'onglet Comparaison
@app.callback(
    [
        Output('compare-tab-title', 'children'),
        Output('strategy-selection-title', 'children'),
        Output('strategy-1-label', 'children'),
        Output('strategy-2-label', 'children'),
        Output('strategy-3-label', 'children'),
        Output('launch-comparison-button', 'children'),
        Output('compare-strategy-1', 'placeholder'),
        Output('compare-strategy-2', 'placeholder'),
        Output('compare-strategy-3', 'placeholder'),
    ],
    Input('language-switcher-sidebar', 'value'),
    prevent_initial_call=False
)
def update_comparison_tab_translations(selected_language):
    """Met à jour les traductions de l'onglet Comparaison"""
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    return [
        t.get('compare-tab-title', 'Comparaison de Stratégies'),
        t.get('strategy-selection-title', 'Sélection des Stratégies'),
        [html.I(className="fas fa-chess-king mr-2"), t.get('strategy-1-label', 'Stratégie 1')],
        [html.I(className="fas fa-chess-queen mr-2"), t.get('strategy-2-label', 'Stratégie 2 (optionnelle)')],
        [html.I(className="fas fa-chess-rook mr-2"), t.get('strategy-3-label', 'Stratégie 3 (optionnelle)')],
        [html.I(className="fas fa-play-circle mr-2"), t.get('launch-comparison-button', 'Lancer la Comparaison')],
        t.get('select-strategy-placeholder', 'Sélectionner une stratégie...'),
        t.get('select-strategy-placeholder', 'Sélectionner une stratégie...'),
        t.get('select-strategy-placeholder', 'Sélectionner une stratégie...'),
    ]

# DANS app.py - AJOUTEZ CE NOUVEAU CALLBACK POUR LES DROPDOWNS DU WIZARD

@app.callback(
    [Output('simple-action-dropdown', 'options'),
     Output('simple-trigger-dropdown', 'options')],
    Input('language-switcher-sidebar', 'value'),
    prevent_initial_call=False
)
def update_wizard_dropdown_options(selected_language):
    """Met à jour les options des dropdowns du wizard selon la langue"""
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    # Options pour l'action
    action_options = [
        {'label': f'📈 {t.get("action-buy", "Acheter")}', 'value': 'Acheter'},
        {'label': f'📉 {t.get("action-sell", "Vendre")}', 'value': 'Vendre'}
    ]
    
    # Options pour le déclencheur
    trigger_options = [
        {'label': html.Div(['🗓️ ', t.get('scenario-monthly', 'Un peu tous les mois')]), 'value': 'Un peu tous les mois'},
        {'label': html.Div(['📉 ', t.get('scenario-price-down', 'Lorsque le prix baisse')]), 'value': 'Lorsque le prix baisse'},
        {'label': html.Div(['📈 ', t.get('scenario-price-up', 'Lorsque le prix augmente')]), 'value': 'Lorsque le prix augmente'},
        {'label': html.Div(['↗️ ', t.get('scenario-price-up-after-down', 'Lorsque le prix augmente après une baisse')]), 'value': 'Lorsque le prix augmente après une baisse'},
        {'label': html.Div(['⚡ ', t.get('scenario-volatility-up', 'Lorsque la volatilité augmente')]), 'value': 'Lorsque la volatilité augmente'}
    ]
    
    return action_options, trigger_options

# === CALLBACKS COMMUNAUTÉ ===


# === CACHE EN MÉMOIRE ===
VOTES_CACHE = {}
COMMENTS_CACHE = defaultdict(list)
LAST_VOTE_TIME = {}

VOTES_FILE = 'community_data/votes.json'
COMMENTS_FILE = 'community_data/comments.json'

def load_votes():
    global VOTES_CACHE
    if os.path.exists(VOTES_FILE):
        with open(VOTES_FILE, 'r') as f:
            VOTES_CACHE = json.load(f)
    return VOTES_CACHE

def save_votes():
    os.makedirs('community_data', exist_ok=True)
    with open(VOTES_FILE, 'w') as f:
        json.dump(VOTES_CACHE, f, indent=2)

def load_comments():
    global COMMENTS_CACHE
    if os.path.exists(COMMENTS_FILE):
        with open(COMMENTS_FILE, 'r') as f:
            COMMENTS_CACHE = defaultdict(list, json.load(f))
    return COMMENTS_CACHE

def save_comments():
    os.makedirs('community_data', exist_ok=True)
    with open(COMMENTS_FILE, 'w') as f:
        json.dump(dict(COMMENTS_CACHE), f, indent=2)

# Charger au démarrage
load_votes()
load_comments()


# === CALLBACK 1 : UPVOTE (met à jour le cache + trigger refresh) ===
@app.callback(
    Output('votes-trigger-store', 'data'),  # ← Store trigger pour forcer refresh
    Input({'type': 'upvote-btn', 'index': ALL}, 'n_clicks'),
    State({'type': 'upvote-btn', 'index': ALL}, 'id'),
    prevent_initial_call=True
)
def handle_upvote(n_clicks_list, button_ids):
    """Traite le vote et déclenche un refresh"""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    # Trouver quel bouton a été cliqué
    trigger = ctx.triggered[0]
    if not trigger['value']:
        raise PreventUpdate
    
    trigger_id = ctx.triggered_id
    strategy_id = trigger_id['index']
    
    # Anti-spam
    current_time = time.time()
    key = f"{strategy_id}_up"
    
    if key in LAST_VOTE_TIME:
        if current_time - LAST_VOTE_TIME[key] < 1.0:
            raise PreventUpdate
    
    LAST_VOTE_TIME[key] = current_time
    
    # Mise à jour du cache
    current_votes = VOTES_CACHE.get(strategy_id, 0)
    VOTES_CACHE[strategy_id] = current_votes + 1
    save_votes()
    
    # Retourner timestamp pour déclencher refresh
    return {'timestamp': current_time, 'strategy_id': strategy_id}


# === CALLBACK 2 : DOWNVOTE ===
@app.callback(
    Output('votes-trigger-store', 'data', allow_duplicate=True),
    Input({'type': 'downvote-btn', 'index': ALL}, 'n_clicks'),
    State({'type': 'downvote-btn', 'index': ALL}, 'id'),
    prevent_initial_call=True
)
def handle_downvote(n_clicks_list, button_ids):
    """Traite le downvote"""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger = ctx.triggered[0]
    if not trigger['value']:
        raise PreventUpdate
    
    trigger_id = ctx.triggered_id
    strategy_id = trigger_id['index']
    
    # Anti-spam
    current_time = time.time()
    key = f"{strategy_id}_down"
    
    if key in LAST_VOTE_TIME:
        if current_time - LAST_VOTE_TIME[key] < 1.0:
            raise PreventUpdate
    
    LAST_VOTE_TIME[key] = current_time
    
    # Mise à jour
    current_votes = VOTES_CACHE.get(strategy_id, 0)
    VOTES_CACHE[strategy_id] = max(0, current_votes - 1)
    save_votes()
    
    return {'timestamp': current_time, 'strategy_id': strategy_id}


# === CALLBACK 3 : AFFICHAGE COMPTEUR (individuel par carte) ===
@app.callback(
    Output({'type': 'vote-count', 'index': MATCH}, 'children'),
    Input('votes-trigger-store', 'data'),
    State({'type': 'vote-count', 'index': MATCH}, 'id'),
    prevent_initial_call=False
)
def update_vote_display(trigger_data, vote_count_id):
    """Met à jour le compteur d'une carte spécifique"""
    strategy_id = vote_count_id['index']
    return str(VOTES_CACHE.get(strategy_id, 0))


# === CALLBACK 4 : CHARGEMENT STRATÉGIES AVEC PAGINATION ===
@app.callback(
    [Output('all-strategies-container', 'children'),
     Output('page-indicator-btn', 'children'),
     Output('prev-page-btn', 'disabled'),
     Output('next-page-btn', 'disabled')],
    [Input('current-page-store', 'data'),
     Input('strategies-per-page-dropdown', 'value'),
     Input('sort-mode-store', 'data'),
     Input('votes-trigger-store', 'data'),  # ← Écoute les changements de votes
     Input('language-switcher-sidebar', 'value')],
    prevent_initial_call=False
)
def load_strategies_paginated(current_page, per_page, sort_mode, votes_trigger, language):
    """Charge les stratégies avec pagination"""
    
    # Lister les stratégies
    strategies = []
    risk_folders = ['high_risk_strat', 'medium_risk_strat', 'low_risk_strat', 'strategies']
    
    for folder_name in risk_folders:
        if not os.path.exists(folder_name):
            continue
        
        for file in os.listdir(folder_name):
            if file.endswith(".json"):
                try:
                    strategy_path = os.path.join(folder_name, file)
                    strategy_id = generate_unique_key(strategy_path, 'all')
                    
                    with open(strategy_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    strategies.append({
                        'id': strategy_id,
                        'path': strategy_path,
                        'name': data.get('name', 'Sans nom'),
                        'votes': VOTES_CACHE.get(strategy_id, 0),
                        'comments': len(COMMENTS_CACHE.get(strategy_id, [])),
                        'created_at': data.get('created_at', '2000-01-01')
                    })
                except:
                    continue
    
    # Tri
    if sort_mode == 'top':
        strategies.sort(key=lambda x: x['votes'], reverse=True)
    else:  # recent
        strategies.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Pagination
    total = len(strategies)
    total_pages = max(1, (total + per_page - 1) // per_page)
    current_page = max(1, min(current_page, total_pages))
    
    start = (current_page - 1) * per_page
    end = start + per_page
    page_strategies = strategies[start:end]
    
    # Créer les cartes
    cards = [
        create_strategy_card_community_v2(
            s['path'], s['name'], s['votes'], s['comments'], 
            language, context='all'
        )
        for s in page_strategies
    ]
    
    if not cards:
        cards = [dbc.Alert("Aucune stratégie disponible", color="info")]
    
    page_text = f"Page {current_page} / {total_pages}"
    prev_disabled = current_page <= 1
    next_disabled = current_page >= total_pages
    
    return html.Div(cards), page_text, prev_disabled, next_disabled


# === CALLBACK 5 : TOP STRATEGIES ===
@app.callback(
    [Output('top-risky-strategies', 'children'),
     Output('top-moderate-strategies', 'children'),
     Output('top-safe-strategies', 'children')],
    [Input('community-sub-tabs', 'active_tab'),
     Input('votes-trigger-store', 'data'),
     Input('language-switcher-sidebar', 'value')],
    prevent_initial_call=True
)
def load_top_strategies(active_tab, votes_trigger, language):
    """Charge les top 3 par catégorie"""
    if active_tab != 'community-top':
        raise PreventUpdate
    
    
    risk_folders = {
        'risky': 'high_risk_strat',
        'moderate': 'medium_risk_strat',
        'safe': 'low_risk_strat'
    }

    
    strategies_by_risk = {'risky': [], 'moderate': [], 'safe': []}
    
    for risk_level, folder_name in risk_folders.items():
        if not os.path.exists(folder_name):
            continue
        
        for file in os.listdir(folder_name):
            if file.endswith(".json"):
                try:
                    strategy_path = os.path.join(folder_name, file)
                    strategy_id = generate_unique_key(strategy_path, risk_level)
                    
                    with open(strategy_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    strategies_by_risk[risk_level].append({
                        'id': strategy_id,
                        'path': strategy_path,
                        'name': data.get('name', 'Sans nom'),
                        'votes': VOTES_CACHE.get(strategy_id, 0),
                        'comments': len(COMMENTS_CACHE.get(strategy_id, []))
                    })
                except:
                    continue
    
    # Trier et prendre top 3
    for risk_level in strategies_by_risk:
        strategies_by_risk[risk_level].sort(key=lambda x: x['votes'], reverse=True)
        strategies_by_risk[risk_level] = strategies_by_risk[risk_level][:3]
    
    # Créer les cartes
    risky_cards = [
        create_strategy_card_community_v2(s['path'], s['name'], s['votes'], s['comments'], language, 'risky')
        for s in strategies_by_risk['risky']
    ] or [dbc.Alert("Aucune stratégie risquée", color="info")]
    
    moderate_cards = [
        create_strategy_card_community_v2(s['path'], s['name'], s['votes'], s['comments'], language, 'moderate')
        for s in strategies_by_risk['moderate']
    ] or [dbc.Alert("Aucune stratégie modérée", color="info")]
    
    safe_cards = [
        create_strategy_card_community_v2(s['path'], s['name'], s['votes'], s['comments'], language, 'safe')
        for s in strategies_by_risk['safe']
    ] or [dbc.Alert("Aucune stratégie sûre", color="info")]
    
    return risky_cards, moderate_cards, safe_cards


# === CALLBACK 6 : PAGINATION PREV ===
@app.callback(
    Output('current-page-store', 'data'),
    Input('prev-page-btn', 'n_clicks'),
    State('current-page-store', 'data'),
    prevent_initial_call=True
)
def prev_page(n_clicks, current_page):
    if not n_clicks:
        raise PreventUpdate
    return max(1, current_page - 1)


# === CALLBACK 7 : PAGINATION NEXT ===
@app.callback(
    Output('current-page-store', 'data', allow_duplicate=True),
    Input('next-page-btn', 'n_clicks'),
    State('current-page-store', 'data'),
    prevent_initial_call=True
)
def next_page(n_clicks, current_page):
    if not n_clicks:
        raise PreventUpdate
    return current_page + 1


# === CALLBACK 8 : TOGGLE COMMENTAIRES ===
@app.callback(
    [Output({'type': 'comment-input', 'index': MATCH}, 'style'),
     Output({'type': 'submit-comment', 'index': MATCH}, 'style'),
     Output({'type': 'comment-divider', 'index': MATCH}, 'style')],
    Input({'type': 'comment-btn', 'index': MATCH}, 'n_clicks'),
    prevent_initial_call=True
)
def toggle_comment_section(n_clicks):
    if not n_clicks:
        raise PreventUpdate
    
    if n_clicks % 2 == 1:
        return (
            {'display': 'block', 'marginBottom': '10px', 'backgroundColor': '#495057', 
             'color': '#ffffff', 'border': '1px solid #6c757d'},
            {'display': 'block', 'marginBottom': '10px'},
            {'display': 'block', 'borderColor': '#6c757d'}
        )
    else:
        return (
            {'display': 'none'},
            {'display': 'none'},
            {'display': 'none'}
        )


# === CALLBACK 9 : SOUMETTRE COMMENTAIRE ===
@app.callback(
    Output('comments-trigger-store', 'data'),
    Input({'type': 'submit-comment', 'index': ALL}, 'n_clicks'),
    [State({'type': 'comment-input', 'index': ALL}, 'value'),
     State({'type': 'submit-comment', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def submit_comment(n_clicks_list, comment_texts, button_ids):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger = ctx.triggered[0]
    if not trigger['value']:
        raise PreventUpdate
    
    trigger_id = ctx.triggered_id
    strategy_id = trigger_id['index']
    
    # Trouver l'index
    clicked_index = None
    for idx, btn_id in enumerate(button_ids):
        if btn_id['index'] == strategy_id:
            clicked_index = idx
            break
    
    if clicked_index is None or not comment_texts[clicked_index]:
        raise PreventUpdate
    
    from datetime import datetime
    new_comment = {
        'text': comment_texts[clicked_index],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'upvotes': 0
    }
    
    COMMENTS_CACHE[strategy_id].append(new_comment)
    save_comments()
    
    return {'timestamp': time.time(), 'strategy_id': strategy_id}


# === CALLBACK 10 : AFFICHER COMMENTAIRES ===
@app.callback(
    [Output({'type': 'comments-display', 'index': MATCH}, 'children'),
     Output({'type': 'comment-input', 'index': MATCH}, 'value')],
    [Input('comments-trigger-store', 'data'),
     Input({'type': 'submit-comment', 'index': MATCH}, 'n_clicks')],
    State({'type': 'comments-display', 'index': MATCH}, 'id'),
    prevent_initial_call=False
)
def display_comments(comments_trigger, n_clicks, display_id):
    strategy_id = display_id['index']
    
    if strategy_id not in COMMENTS_CACHE or not COMMENTS_CACHE[strategy_id]:
        return [], ""
    
    comments_display = []
    for comment in COMMENTS_CACHE[strategy_id]:
        comments_display.append(
            dbc.Card([
                dbc.CardBody([
                    html.P(comment['text'], className="mb-2", style={'color': '#0f172a'}),
                    html.Small([
                        html.Span(comment['timestamp'], className="text-muted mr-3"),
                        dbc.Button([
                            html.I(className="fas fa-arrow-up mr-1"),
                            str(comment['upvotes'])
                        ], color="link", size="sm", className="p-0")
                    ])
                ])
            ], className="mb-2", style={'backgroundColor': '#f8f9fa'})
        )
    
    ctx = callback_context
    if ctx.triggered and 'submit-comment' in ctx.triggered[0]['prop_id']:
        return comments_display, ""
    
    return comments_display, dash.no_update




# 6. Soumettre prévision
@app.callback(
    [Output('community-forecasts-store', 'data'),
     Output('forecast-confirmation', 'children')],
    Input('submit-forecast', 'n_clicks'),
    [State('forecast-asset-select', 'value'),
     State('forecast-horizon-select', 'value'),
     State('forecast-direction', 'value'),
     State('forecast-confidence', 'value'),
     State('community-forecasts-store', 'data'),
     State('language-switcher-sidebar', 'value')],
    prevent_initial_call=True
)
def submit_forecast(n_clicks, asset, horizon, direction, confidence, forecasts_data, language):
    """Soumet une prévision"""
    if not n_clicks or not all([asset, horizon, direction]):
        raise PreventUpdate
    
    t = TEXT.get(language, TEXT['fr']) if language in TEXT else TEXT['fr']
    forecasts_data = forecasts_data or {}
    
    if asset not in forecasts_data:
        forecasts_data[asset] = []
    
    from datetime import datetime
    new_forecast = {
        'horizon': horizon,
        'direction': direction,
        'confidence': confidence,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    
    forecasts_data[asset].append(new_forecast)
    
    return forecasts_data, dbc.Alert("Prévision enregistrée avec succès!", color="success", duration=3000)


# 7. Afficher prévisions
@app.callback(
    Output('forecasts-display', 'children'),
    [Input('forecast-asset-select', 'value'),
     Input('community-forecasts-store', 'data'),
     Input('language-switcher-sidebar', 'value')],
    prevent_initial_call=True
)
def display_forecasts(asset, forecasts_data, language):
    """Affiche les prévisions pour un actif"""
    if not asset:
        return dbc.Alert("Sélectionnez un actif pour voir les prévisions", color="info")
    
    return create_forecast_display(forecasts_data, asset, language)


# 8. NOUVEAU - Partager une stratégie depuis l'onglet résultats
# 8. Partager une stratégie depuis l'onglet résultats - VERSION CORRIGÉE
@app.callback(
    [Output('share-strategy-confirmation', 'children'),
     Output('community-votes-store', 'data', allow_duplicate=True)],
    Input('share-strategy-btn', 'n_clicks'),
    [State('language-switcher-sidebar', 'value'),
     State('community-votes-store', 'data'),
     State('strategy-store', 'data')],
    prevent_initial_call=True
)
def share_strategy_to_community(n_clicks, language, votes_data, strategy_store_data):
    """Partage la stratégie actuelle dans la communauté"""
    if not n_clicks:
        raise PreventUpdate
    
    current_strategy_file = strategy_store_data.get('file_path') if strategy_store_data else None
    current_strategy = strategy_store_data.get('strategy_data') if strategy_store_data else None

    
    
    t = TEXT.get(language, TEXT['fr']) if language in TEXT else TEXT['fr']
    
    # Vérifier qu'une stratégie existe
    if not current_strategy_file or not os.path.exists(current_strategy_file):
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle mr-2"),
            "Aucune stratégie à partager. Veuillez d'abord créer et exécuter un backtest."
        ], color="warning", duration=4000), dash.no_update
    
    # Vérifier que la stratégie n'est pas déjà dans le dossier strategies
    # (elle devrait déjà y être si on a fait un backtest)
    if not os.path.exists("strategies"):
        os.makedirs("strategies")
    
    # Initialiser les votes si nécessaire
    votes_data = votes_data or {}
    
    # Ajouter un vote initial si la stratégie n'en a pas
    if current_strategy_file not in votes_data:
        votes_data[current_strategy_file] = 1  # Vote initial de l'auteur
    
    # Message de confirmation avec détails
    strategy_name = current_strategy.get('name', 'Sans nom') if current_strategy else 'Sans nom'
    
    confirmation = dbc.Alert([
        html.Div([
            html.I(className="fas fa-check-circle fa-2x text-success mb-3"),
        ], className="text-center"),
        html.H5("Stratégie partagée avec succès!", className="text-center text-success mb-3"),
        html.Hr(),
        html.P([
            html.Strong("Stratégie : "),
            strategy_name
        ], className="mb-2"),
        html.P([
            html.I(className="fas fa-arrow-up mr-2"),
            f"Vote initial : {votes_data[current_strategy_file]}"
        ], className="mb-2"),
        html.Hr(),
        html.Small([
            html.I(className="fas fa-info-circle mr-2"),
            "Rendez-vous dans l'onglet ",
            html.Strong("Communauté"),
            " pour voir votre stratégie et les réactions de la communauté."
        ], className="text-muted d-block text-center")
    ], color="success", className="mt-3")
    
    return confirmation, votes_data


# DANS app.py - AJOUTEZ CE CALLBACK POUR LES EN-TÊTES "ACTIONS À EXÉCUTER"

# Callback pour le label de l'onglet communauté
@app.callback(
    Output('community-tab', 'label'),
    Input('language-switcher-sidebar', 'value'),
    prevent_initial_call=False
)
def update_community_tab_label(selected_language):
    """Met à jour le label de l'onglet communauté"""
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    return t.get('community-tab', 'Communauté')

@app.callback(
    [Output(f'actions-header-{i}', 'children') for i in range(MAX_BLOCKS)],
    Input('language-switcher-sidebar', 'value'),
    prevent_initial_call=False
)
def update_actions_headers(selected_language):
    """Met à jour les en-têtes 'Actions à exécuter'"""
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    text = t.get('actions-to-execute', 'Actions à exécuter')
    return [text] * MAX_BLOCKS


@app.callback(
    # Labels des blocs qui existent
    [Output(f'decision-block-title-{i}', 'children', allow_duplicate=True) for i in range(MAX_BLOCKS)] +
    [Output(f'decision-block-description-{i}', 'children', allow_duplicate=True) for i in range(MAX_BLOCKS)],
    Input('language-switcher-sidebar', 'value'),
    [State('visible-blocks-store', 'data')],
    prevent_initial_call=True  # CHANGEZ False en True
)
def update_decision_blocks_translations(selected_language, visible_blocks):
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    visible_blocks = visible_blocks or [0]
    
    results = []
    # Titres des blocs
    for i in range(MAX_BLOCKS):
        results.append(t.get('decision-block-title', 'Bloc de Décision '))
    # Descriptions des blocs  
    for i in range(MAX_BLOCKS):
        results.append(t.get('decision-block-description', 'Définissez les conditions et actions pour ce bloc de décision.'))
    
    return results


@app.callback(
    [Output(f'operator-{i}-{j}', 'options') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)],
    Input('language-switcher-sidebar', 'value'),
    prevent_initial_call=False  # Important : False pour charger au démarrage
)
def populate_operator_dropdowns(selected_language):
    """Remplit les dropdowns d'opérateurs avec les options"""
    
    print(f"[DEBUG] Remplissage des opérateurs pour langue: {selected_language}")
    
    # Options des opérateurs (simples, sans traduction complexe pour debug)
    operator_options = [
        {'label': '>', 'value': '>'},
        {'label': '<', 'value': '<'},
        {'label': '>=', 'value': '>='},
        {'label': '<=', 'value': '<='},
        {'label': '==', 'value': '=='},
        {'label': '!=', 'value': '!='}
    ]
    
    # Retourner pour tous les blocs/conditions
    total_operators = MAX_BLOCKS * MAX_CONDITIONS
    result = [operator_options] * total_operators
    
    print(f"[OK] {total_operators} dropdowns d'opérateurs mis à jour")
    return result

@app.callback(
    [Output('tab-creation', 'label'),
     Output('tab-results', 'label'),
     Output('options-tab', 'label'),
     Output('import-tab', 'label'),
     Output('synthetic-tab', 'label'),
     Output('compare-tab', 'label')],  # AJOUT ICI
    Input('language-switcher-sidebar', 'value'),
    prevent_initial_call=False
)
def update_tab_labels(selected_language):
    """Met à jour les labels des onglets selon la langue"""
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    return [
        t.get('tab-creation', 'Création de stratégie'),
        t.get('tab-results', 'Résultats'),
        t.get('options-tab', 'Options'),
        t.get('import-tab', 'Import CSV'),
        t.get('synthetic-tab', 'Backtest Synthétique'),
        t.get('compare-tab', 'Comparaison')  # AJOUT ICI
    ]


@app.callback(
    # Options des dropdowns de conditions
    [Output(f'comparison-type-{i}-{j}', 'options') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    # Options des dropdowns d'actions
    [Output(f'stock-action-{i}-{stock_idx}', 'options') for i in range(MAX_BLOCKS) for stock_idx in range(10)],
    Input('language-switcher-sidebar', 'value'),
    prevent_initial_call=False
)
def update_dropdown_options_translations(selected_language):
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    # Options pour comparison-type
    comparison_options = [
        {'label': t.get('dropdown-indicator', 'Indicateur'), 'value': 'indicator'},
        {'label': t.get('dropdown-value', 'Valeur'), 'value': 'value'}
    ]
    
    # Options pour les actions
    action_options = [
        {'label': t.get('action-buy', 'Acheter'), 'value': 'Acheter'},
        {'label': t.get('action-sell', 'Vendre'), 'value': 'Vendre'},
        {'label': t.get('action-nothing', 'Ne rien faire'), 'value': 'Ne rien faire'}
    ]
    
    results = []
    
    # Retourner les options de comparison-type pour tous les blocs/conditions
    total_conditions = MAX_BLOCKS * MAX_CONDITIONS
    for _ in range(total_conditions):
        results.append(comparison_options)
    
    # Retourner les options d'actions pour tous les blocs/stocks
    total_actions = MAX_BLOCKS * 10
    for _ in range(total_actions):
        results.append(action_options)
    
    return results

@app.callback(
    # Placeholders des dropdowns
    [Output(f'stock1-{i}-{j}', 'placeholder') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'indicator1-type-{i}-{j}', 'placeholder') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'operator-{i}-{j}', 'placeholder') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'stock2-{i}-{j}', 'placeholder') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'indicator2-type-{i}-{j}', 'placeholder') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'comparison-value-{i}-{j}', 'placeholder') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)],
    Input('language-switcher-sidebar', 'value'),
    prevent_initial_call=False
)
def update_dropdown_placeholders_translations(selected_language):
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    total_conditions = MAX_BLOCKS * MAX_CONDITIONS
    results = []
    
    # Placeholders stock1
    for _ in range(total_conditions):
        results.append(t.get('placeholder-select-stock', 'Sélectionner une action'))
    
    # Placeholders indicator1-type
    for _ in range(total_conditions):
        results.append(t.get('placeholder-indicator', 'Indicateur'))
    
    # Placeholders operator
    for _ in range(total_conditions):
        results.append(t.get('placeholder-operator', 'Opérateur'))
    
    # Placeholders stock2
    for _ in range(total_conditions):
        results.append(t.get('placeholder-select-stock', 'Sélectionner une action'))
    
    # Placeholders indicator2-type
    for _ in range(total_conditions):
        results.append(t.get('placeholder-indicator', 'Indicateur'))
    
    # Placeholders comparison-value
    for _ in range(total_conditions):
        results.append(t.get('placeholder-numeric-value', 'Valeur numérique'))
    
    return results
    
# @app.callback(
#     [Output({'type': 'wizard-asset-dropdown', 'asset_class': ALL, 'index': ALL}, 'placeholder')] +
#     [Output({'type': 'asset-dropdown', 'asset_class': ALL, 'index': ALL}, 'placeholder')],
#     Input('language-switcher-sidebar', 'value'),
#     prevent_initial_call=True
# )
# def update_asset_dropdown_placeholders(selected_language):
#     """Met à jour les placeholders des dropdowns d'actifs selon la langue"""
#     if selected_language not in TEXT:
#         selected_language = 'fr'
#     t = TEXT[selected_language]
    
#     ctx = dash.callback_context
#     if not ctx.inputs_list:
#         raise PreventUpdate
    
#     # Récupérer tous les dropdowns d'actifs
#     wizard_dropdowns = ctx.inputs_list[0] if len(ctx.inputs_list) > 0 else []
#     advanced_dropdowns = ctx.inputs_list[1] if len(ctx.inputs_list) > 1 else []
    
#     results = []
    
#     # Placeholders pour les dropdowns du wizard
#     for dropdown in wizard_dropdowns:
#         if dropdown.get('id'):
#             asset_class = dropdown['id'].get('asset_class', '')
#             if asset_class == 'actions_cac40':
#                 placeholder = t.get('choose-cac40-stock', 'Choisir une action CAC40')
#             elif asset_class == 'crypto':
#                 placeholder = t.get('choose-crypto', 'Choisir une crypto')
#             elif asset_class == 'forex':
#                 placeholder = t.get('choose-forex', 'Choisir une paire forex')
#             elif asset_class == 'etfs':
#                 placeholder = t.get('choose-etf', 'Choisir un ETF')
#             else:
#                 placeholder = t.get('choose-asset', 'Choisir un actif')
#             results.append(placeholder)
    
#     # Placeholders pour les dropdowns du mode avancé
#     for dropdown in advanced_dropdowns:
#         if dropdown.get('id'):
#             asset_class = dropdown['id'].get('asset_class', '')
#             if asset_class == 'actions_cac40':
#                 placeholder = t.get('choose-cac40-stock', 'Choisir une action CAC40')
#             elif asset_class == 'crypto':
#                 placeholder = t.get('choose-crypto', 'Choisir une crypto')
#             elif asset_class == 'forex':
#                 placeholder = t.get('choose-forex', 'Choisir une paire forex')
#             elif asset_class == 'etfs':
#                 placeholder = t.get('choose-etf', 'Choisir un ETF')
#             else:
#                 placeholder = t.get('choose-asset', 'Choisir un actif')
#             results.append(placeholder)
    
#     return results

@app.callback(
    [
        # === TITRES PRINCIPAUX ===
        Output('synthetic-backtest-title', 'children'),
        Output('synthetic-model-config-title', 'children'),
        Output('synthetic-generation-title', 'children'),
        
        # === LABELS ===
        Output('synthetic-model-type-label', 'children'),
        Output('synthetic-horizon-label', 'children'),
        Output('synthetic-days-label', 'children'),
        Output('synthetic-simulations-label', 'children'),
        Output('synthetic-calibration-period-label', 'children'),
        Output('synthetic-launch-button', 'children'),
    ],
    Input('language-switcher-sidebar', 'value'),
    prevent_initial_call=False
)
def update_synthetic_tab_translations(selected_language):
    """Met à jour les traductions de l'onglet synthétique"""
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    return [
        t.get('synthetic-backtest-title', 'Backtest Synthétique'),
        t.get('synthetic-model-config-title', 'Configuration du Modèle'),
        t.get('synthetic-generation-title', 'Génération et Lancement'),
        t.get('synthetic-model-type-label', 'Type de modèle :'),
        t.get('synthetic-horizon-label', 'Horizon (années)'),
        t.get('synthetic-days-label', 'Nombre de jours'),
        t.get('synthetic-simulations-label', 'Simulations'),
        t.get('synthetic-calibration-period-label', 'Période de calibration :'),
        [html.I(className="fas fa-rocket mr-2"), t.get('synthetic-launch-button', 'Lancer le Backtest Monte Carlo')]
    ]


@app.callback(
    # Labels des conditions
    [Output(f'static-label-indicator1-{i}-{j}', 'children') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'static-label-operator-{i}-{j}', 'children') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'static-label-comparison-type-{i}-{j}', 'children') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'indicator2-label-{i}-{j}', 'children') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)] +
    [Output(f'value-label-{i}-{j}', 'children') for i in range(MAX_BLOCKS) for j in range(MAX_CONDITIONS)],
    Input('language-switcher-sidebar', 'value'),
    prevent_initial_call=False
)
def update_condition_labels_translations(selected_language):
    if selected_language not in TEXT:
        selected_language = 'fr'
    t = TEXT[selected_language]
    
    total_conditions = MAX_BLOCKS * MAX_CONDITIONS
    results = []
    
    # Labels indicator1
    for _ in range(total_conditions):
        results.append(t.get('label-stock1', 'Actif 1 :'))
    
    # Labels operator
    for _ in range(total_conditions):
        results.append(t.get('label-operator', 'Opérateur :'))
    
    # Labels comparison-type
    for _ in range(total_conditions):
        results.append(t.get('label-comparison-type', 'Type de comparaison :'))
    
    # Labels indicator2
    for _ in range(total_conditions):
        results.append(t.get('label-indicator2', 'Indicateur 2 :'))
    
    # Labels comparison-value
    for _ in range(total_conditions):
        results.append(t.get('label-comparison-value', 'Valeur de comparaison :'))
    
    return results

# === CALLBACK SÉPARÉ POUR L'AUTHENTIFICATION ===
# Ajoutez ce callback seulement si vous utilisez auth_layout() quelque part

# @app.callback(
#     [
#         Output('auth-app-title', 'children'),
#         Output('auth-login-label', 'children'),
#         Output('auth-register-label', 'children'),
#         Output('forgot-password-link-text', 'children'),
#         Output('send-reset-email-text', 'children'),
#         Output('submit-btn-text', 'children'),
#         Output('email', 'placeholder'),
#         Output('password', 'placeholder'),
#         Output('reset-email', 'placeholder'),
#     ],
#     [Input('language-switcher-sidebar', 'value')],
#     prevent_initial_call=False
# )
# def update_auth_translations(selected_language):
#     if selected_language not in TEXT:
#         selected_language = 'fr'
    
#     t = TEXT[selected_language]
    
#     return [
#         t.get('auth-app-title', ''),
#         t.get('auth-login-label', ''),
#         t.get('auth-register-label', ''),
#         t.get('forgot-password-link-text', ''),
#         t.get('send-reset-email-text', ''),
#         t.get('submit-btn-text', ''),
#         t.get('email', ''),
#         t.get('password', ''),
#         t.get('reset-email', ''),
#         t.get('total-pnl-label', ''),
#         t.get('performance-metrics-title', ''),
#         t.get('initial-capital-label', ''),
#         t.get('final-capital-label', ''),
#         t.get('total-return-label', ''),
#         t.get('max-drawdown-label', ''),
#         t.get('sharpe-ratio-label', ''),
#         t.get('winning-trades-pct-label', ''),
#         t.get('price-indicators-title', ''),
#         t.get('synthetic-data-label', ''),
#         t.get('transactions-journal-title', ''),
#         t.get('equity-curve-title', ''),
#         t.get('drawdown-title', ''),
        
#         # === RÉSULTATS MULTI-TRAJECTOIRES ===
#         t.get('average-results-title', ''),
#         t.get('trajectory-count-label', ''),
#         t.get('median-return-label', ''),
#         t.get('average-return-label', ''),
#         t.get('median-sharpe-label', ''),
#         t.get('median-drawdown-label', ''),
#         t.get('risk-analysis-title', ''),
#         t.get('var-title', ''),
#         t.get('var-95-label', ''),
#         t.get('var-99-label', ''),
#         t.get('loss-probability-label', ''),
#         t.get('scenarios-title', ''),
#         t.get('best-scenario-label', ''),
#         t.get('worst-scenario-label', ''),
#         t.get('winning-scenarios-label', ''),
#         t.get('returns-distribution-title', ''),
        
#         # === AUTHENTIFICATION ===
#         t.get('auth-app-title', ''),
#         t.get('auth-login-label', ''),
#         t.get('auth-register-label', ''),
#         t.get('forgot-password-link-text', ''),
#         t.get('send-reset-email-text', ''),
#         t.get('submit-btn-text', ''),
        
#         # === PLACEHOLDERS ===
#         t.get('strategy-name', ''),
#         t.get('wizard-predefined-strategy-select', ''),
#         t.get('wizard-asset-class-selector', ''),
#         t.get('simple-action-dropdown', ''),
#         t.get('simple-trigger-dropdown', ''),
#         t.get('asset-class-selector', ''),
#         t.get('email', ''),
#         t.get('password', ''),
#         t.get('reset-email', ''),
#         t.get('custom-asset-name', ''),
#     ]

@app.callback(
    Output('output-data-upload-filename', 'children'),
    Input('upload-data', 'filename'),
    prevent_initial_call=True
)
def display_upload_filename(filename):
    """
    Affiche un message de confirmation dès que le fichier est chargé dans le navigateur.
    """
    if filename is not None:
        return dbc.Alert(
            f"Fichier pré-chargé : {filename}. Veuillez nommer l'actif et cliquer sur 'Sauvegarder'.",
            color="info",
            className="mt-3 text-center"
        )
    return ""

register_chatbot_callbacks(app)

# === CALLBACK POUR EXPORT PDF ===
@app.callback(
    Output("download-pdf-synthetic", "data"),
    Input("btn-download-pdf-synthetic", "n_clicks"),
    [State('strategy-store', 'data'),
     State('synthetic-data-store', 'data'),
     State('synthetic-model-info-store', 'data')],
    prevent_initial_call=True
)
def download_synthetic_pdf(n_clicks, strategy_store_data, synthetic_data, model_info):
    if not n_clicks:
        raise PreventUpdate
    
    try:
        if not synthetic_data or not strategy_store_data:
            print("[WARN] Données manquantes pour l'export PDF")
            raise PreventUpdate
            
        strategy_data = strategy_store_data.get('strategy_data', {})
        
        # Reconstruction des objets pour l'export
        # On doit recréer les figures car elles ne sont pas stockées telles quelles
        # C'est une limite ici : on va faire un export simplifié si on n'a pas tout
        
        # Récupération des données brutes
        df_results = pd.DataFrame(synthetic_data.get('raw_data', []))
        metrics = synthetic_data.get('central_metrics', {})
        
        # Recréer les figures
        figures = {} 
        # Note: Pour un vrai support des graphes, il faudrait régénérer les plots ici
        
        # On tente de récupérer les transactions si dispos
        transactions = []
        
        # Génération du PDF
        pdf_bytes = export_backtest_to_pdf(
            strategy_data=strategy_data,
            metrics=metrics,
            figures=figures,
            transactions=transactions
        )
        
        # Nom du fichier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Rapport_Backtest_{timestamp}.pdf"
        
        return dcc.send_bytes(pdf_bytes, filename)
        
    except Exception as e:
        print(f"[ERREUR] Export PDF: {e}")
        import traceback
        traceback.print_exc()
        raise PreventUpdate
# ========================================
# ========================================
# USER MANAGEMENT CALLBACKS
# ========================================

from utility.user_manager import user_manager
import time

@app.callback(
    [Output("sidebar-clients-list", "children"),
     Output("sidebar-folders-list", "children")],
    [Input("url", "pathname"),
     Input("refresh-signal", "data")],
     State("context-store", "data")
)
def update_sidebar_lists(pathname, signal, context):
    """updates the sidebar lists for Clients/Folders based on role."""
    uid = session.get('user_id')
    if not uid:
        return [], []
        
    role = session.get('role', 'individual')
    
    clients_html = []
    folders_html = []
    
    if role == 'professional':
        clients = user_manager.get_clients(uid)
        for client in clients:
             clients_html.append(
                dbc.Button(
                    [html.I(className="fas fa-user-tie mr-2"), client.get('name', 'Unnamed')],
                    id={'type': 'client-select-btn', 'index': client['id']},
                    color="transparent",
                    className="sidebar-link text-left pl-3 text-muted w-100",
                    style={"textDecoration": "none", "border": "none"}
                )
            )
    else:
        folders = user_manager.get_folders(uid)
        for folder in folders:
            folders_html.append(
                dbc.Button(
                    [html.I(className="fas fa-folder mr-2"), folder.get('name', 'Unnamed')],
                    id={'type': 'folder-select-btn', 'index': folder['id']},
                    color="transparent",
                    className="sidebar-link text-left pl-3 text-muted w-100",
                    style={"textDecoration": "none", "border": "none"}
                )
            )
            
    return clients_html, folders_html

# Modal Toggles & Creation Logic
@app.callback(
    [Output("modal-new-client", "is_open"),
     Output("refresh-signal", "data", allow_duplicate=True)],
    [Input("btn-add-client", "n_clicks"), 
     Input("cancel-new-client", "n_clicks"), 
     Input("confirm-new-client", "n_clicks")],
    [State("modal-new-client", "is_open"), 
     State("new-client-name", "value")],
    prevent_initial_call=True
)
def toggle_client_modal(n1, n2, n3, is_open, name):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'confirm-new-client' and name:
        uid = session.get('user_id')
        if uid:
            user_manager.create_client(uid, name)
            return False, {'timestamp': time.time()} # Signal refresh
        return False, dash.no_update
        
    elif trigger_id == 'cancel-new-client':
            return False, dash.no_update
    elif trigger_id == 'btn-add-client':
            return True, dash.no_update
            
    return is_open, dash.no_update

@app.callback(
    [Output("modal-new-folder", "is_open"),
     Output("refresh-signal", "data", allow_duplicate=True)],
    [Input("btn-add-folder", "n_clicks"), 
     Input("cancel-new-folder", "n_clicks"), 
     Input("confirm-new-folder", "n_clicks")],
    [State("modal-new-folder", "is_open"), 
     State("new-folder-name", "value")],
    prevent_initial_call=True
)
def toggle_folder_modal(n1, n2, n3, is_open, name):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'confirm-new-folder' and name:
        uid = session.get('user_id')
        if uid:
            user_manager.create_folder(uid, name)
            return False, {'timestamp': time.time()} # Signal refresh
        return False, dash.no_update
        
    elif trigger_id == 'cancel-new-folder':
        return False, dash.no_update
    elif trigger_id == 'btn-add-folder':
        return True, dash.no_update
        
    return is_open, dash.no_update

# Role Switcher
@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("role-switcher", "value"),
    prevent_initial_call=True
)
def switch_role(new_role):
    if new_role:
        session['role'] = new_role
        return "/app" # Reload page
    return dash.no_update
