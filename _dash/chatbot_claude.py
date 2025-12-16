# """
# Module pour le chatbot Claude intégré
# Widget flottant sobre à gauche avec gradient bleu
# """

# import dash
# from dash import html, dcc, Input, Output, State, callback_context
# from dash.exceptions import PreventUpdate
# import dash_bootstrap_components as dbc
# from anthropic import Anthropic
# import os

# # Initialiser le client Anthropic
# try:
#     api_key = os.environ.get("ANTHROPIC_API_KEY")
#     if api_key:
#         anthropic_client = Anthropic(api_key=api_key)
#         CLAUDE_AVAILABLE = True
#         print("✅ Client Claude initialisé avec succès")
#     else:
#         print("❌ ANTHROPIC_API_KEY non trouvée")
#         anthropic_client = None
#         CLAUDE_AVAILABLE = False
# except Exception as e:
#     print(f"❌ Erreur initialisation Claude: {e}")
#     anthropic_client = None
#     CLAUDE_AVAILABLE = False


# def create_chatbot_layout():
#     """Crée le layout du chatbot flottant sobre à gauche"""
    
#     return html.Div([
#         # Bouton pour ouvrir/fermer le chatbot (flottant en bas à GAUCHE)
#         html.Div([
#             dbc.Button(
#                 [html.I(className="fas fa-robot fa-lg")],
#                 id="chatbot-toggle-btn",
#                 className="shadow",
#                 style={
#                     'width': '55px',
#                     'height': '55px',
#                     'padding': '0',
#                     'border': 'none',
#                     'borderRadius': '50%',
#                     'background': 'linear-gradient(135deg, #2196F3 0%, #1976D2 100%)',
#                     'color': 'white'
#                 }
#             )
#         ], style={
#             'position': 'fixed',
#             'bottom': '20px',
#             'left': '20px',  # À GAUCHE
#             'zIndex': '9999',
#             'cursor': 'pointer'
#         }),
        
#         # Fenêtre du chatbot (masquée par défaut)
#         html.Div([
#             dbc.Card([
#                 # En-tête sobre avec gradient bleu
#                 dbc.CardHeader([
#                     dbc.Row([
#                         dbc.Col([
#                             html.I(className="fas fa-robot mr-2", style={'color': 'white'}),
#                             html.Strong("Assistant IA", style={'color': 'white'})
#                         ], width=9),
#                         dbc.Col([
#                             dbc.Button(
#                                 html.I(className="fas fa-times", style={'color': 'white'}),
#                                 id="chatbot-close-btn",
#                                 color="link",
#                                 size="sm",
#                                 className="p-0"
#                             )
#                         ], width=3, className="text-right")
#                     ])
#                 ], style={
#                     'background': 'linear-gradient(135deg, #2196F3 0%, #1976D2 100%)',
#                     'borderBottom': 'none',
#                     'padding': '12px 20px'
#                 }),
                
#                 # Corps du chatbot
#                 dbc.CardBody([
#                     # Zone d'affichage des messages
#                     html.Div(
#                         id="chatbot-messages",
#                         children=[
#                             html.Div([
#                                 html.P([
#                                     "👋 Bonjour ! Je suis votre assistant IA.",
#                                     html.Br(), html.Br(),
#                                     "Je peux vous aider avec :",
#                                     html.Br(),
#                                     "• Explication des indicateurs",
#                                     html.Br(),
#                                     "• Conseils stratégiques",
#                                     html.Br(),
#                                     "• Gestion des risques"
#                                 ], style={
#                                     'color': '#000000',
#                                     'fontSize': '14px',
#                                     'margin': '0'
#                                 })
#                             ], style={
#                                 'padding': '12px',
#                                 'backgroundColor': '#E3F2FD',
#                                 'borderRadius': '8px',
#                                 'marginBottom': '10px',
#                                 'border': '1px solid #2196F3'
#                             })
#                         ],
#                         style={
#                             'height': '380px',
#                             'overflowY': 'auto',
#                             'padding': '15px',
#                             'backgroundColor': '#ffffff',
#                             'borderRadius': '5px',
#                             'marginBottom': '15px',
#                             'border': '1px solid #e0e0e0'
#                         }
#                     ),
                    
#                     # Suggestions rapides sobres
#                     html.Div([
#                         dbc.Button(
#                             "📚 Expliquer",
#                             id="quick-explain",
#                             size="sm",
#                             outline=True,
#                             color="primary",
#                             className="mr-2 mb-2",
#                             style={'color': '#1976D2', 'borderColor': '#2196F3'}
#                         ),
#                         dbc.Button(
#                             "💡 Idées",
#                             id="quick-ideas",
#                             size="sm",
#                             outline=True,
#                             color="primary",
#                             className="mr-2 mb-2",
#                             style={'color': '#1976D2', 'borderColor': '#2196F3'}
#                         ),
#                         dbc.Button(
#                             "🛡️ Risques",
#                             id="quick-risks",
#                             size="sm",
#                             outline=True,
#                             color="primary",
#                             className="mb-2",
#                             style={'color': '#1976D2', 'borderColor': '#2196F3'}
#                         ),
#                     ], className="mb-3"),
                    
#                     # Zone de saisie
#                     dbc.InputGroup([
#                         dbc.Input(
#                             id="chatbot-user-input",
#                             placeholder="Posez votre question...",
#                             type="text",
#                             style={
#                                 'backgroundColor': '#ffffff',
#                                 'color': '#000000',
#                                 'border': '1px solid #2196F3'
#                             }
#                         ),
#                         dbc.Button(
#                             html.I(className="fas fa-paper-plane"),
#                             id="chatbot-send-message",
#                             style={
#                                 'background': 'linear-gradient(135deg, #2196F3 0%, #1976D2 100%)',
#                                 'border': 'none',
#                                 'color': 'white'
#                             }
#                         )
#                     ])
#                 ], style={'padding': '20px', 'backgroundColor': '#fafafa'}),
                
#                 # Pied de page sobre
#                 dbc.CardFooter([
#                     html.Small([
#                         html.I(className="fas fa-info-circle mr-1", style={'color': '#1976D2'}),
#                         html.Span("Propulsé par Claude AI", style={'color': '#666666'})
#                     ])
#                 ], style={
#                     'textAlign': 'center',
#                     'padding': '10px',
#                     'backgroundColor': '#ffffff',
#                     'borderTop': '1px solid #e0e0e0'
#                 })
#             ], style={
#                 'width': '380px',
#                 'maxHeight': '600px',
#                 'boxShadow': '0 4px 20px rgba(0,0,0,0.15)',
#                 'borderRadius': '10px',
#                 'overflow': 'hidden',
#                 'border': '1px solid #2196F3'
#             })
#         ], id="chatbot-window", style={
#             'position': 'fixed',
#             'bottom': '85px',
#             'left': '20px',  # À GAUCHE
#             'zIndex': '9998',
#             'display': 'none'
#         }),
        
#         # Stores
#         dcc.Store(id='chatbot-history-store', data=[]),
#         dcc.Store(id='chatbot-state-store', data={'is_open': False})
#     ])


# def register_chatbot_callbacks(app):
#     """Enregistre tous les callbacks du chatbot"""
    
#     # Callback 1: Toggle ouvrir/fermer
#     @app.callback(
#         [Output('chatbot-window', 'style'),
#          Output('chatbot-state-store', 'data')],
#         [Input('chatbot-toggle-btn', 'n_clicks'),
#          Input('chatbot-close-btn', 'n_clicks')],
#         State('chatbot-state-store', 'data'),
#         prevent_initial_call=True
#     )
#     def toggle_chatbot(toggle_clicks, close_clicks, state):
#         """Ouvre ou ferme la fenêtre du chatbot"""
#         current_state = state.get('is_open', False)
#         new_state = not current_state
        
#         if new_state:
#             window_style = {
#                 'position': 'fixed',
#                 'bottom': '85px',
#                 'left': '20px',  # À GAUCHE
#                 'zIndex': '9998',
#                 'display': 'block'
#             }
#         else:
#             window_style = {
#                 'position': 'fixed',
#                 'bottom': '85px',
#                 'left': '20px',  # À GAUCHE
#                 'zIndex': '9998',
#                 'display': 'none'
#             }
        
#         return window_style, {'is_open': new_state}
    
    
#     # Callback 2: Gérer les messages
#     @app.callback(
#         [Output('chatbot-messages', 'children'),
#          Output('chatbot-history-store', 'data'),
#          Output('chatbot-user-input', 'value')],
#         [Input('chatbot-send-message', 'n_clicks'),
#          Input('chatbot-user-input', 'n_submit'),
#          Input('quick-explain', 'n_clicks'),
#          Input('quick-ideas', 'n_clicks'),
#          Input('quick-risks', 'n_clicks')],
#         [State('chatbot-user-input', 'value'),
#          State('chatbot-history-store', 'data'),
#          State('strategy-store', 'data')],
#         prevent_initial_call=True
#     )
#     def handle_chatbot_message(send_clicks, input_submit, explain_clicks, ideas_clicks, 
#                                 risks_clicks, user_input, history, strategy_data):
#         """Traite les messages du chatbot"""
        
#         if not CLAUDE_AVAILABLE:
#             error_bubble = html.Div([
#                 html.P("❌ L'API Claude n'est pas configurée.", style={
#                     'color': '#000000',
#                     'fontSize': '14px',
#                     'margin': '0'
#                 })
#             ], style={
#                 'padding': '12px',
#                 'backgroundColor': '#FFEBEE',
#                 'borderRadius': '8px',
#                 'marginBottom': '10px',
#                 'border': '1px solid #EF5350'
#             })
#             return [error_bubble], history or [], ""
        
#         ctx = callback_context
#         if not ctx.triggered:
#             raise PreventUpdate
        
#         trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
#         # Suggestions rapides
#         if trigger_id == 'quick-explain':
#             user_input = "Explique-moi comment créer une stratégie de trading efficace"
#         elif trigger_id == 'quick-ideas':
#             user_input = "Donne-moi 3 idées de stratégies pour débutants"
#         elif trigger_id == 'quick-risks':
#             user_input = "Comment gérer les risques avec stop-loss et take-profit ?"
        
#         if not user_input or not user_input.strip():
#             raise PreventUpdate
        
#         history = history or []
        
#         # Contexte de la stratégie
#         context = ""
#         if strategy_data and strategy_data.get('strategy_data'):
#             strategy = strategy_data['strategy_data']
#             context = f"\n\n[Contexte: Stratégie '{strategy.get('name', 'Sans nom')}' avec {strategy.get('initial_capital', 0):,}€]"
        
#         history.append({
#             "role": "user",
#             "content": user_input + context
#         })
        
#         try:
#             response = anthropic_client.messages.create(
#                 model="claude-sonnet-4-5-20250929",
#                 max_tokens=1024,
#                 system="""Tu es un assistant IA expert en trading pour TradingLab.

# Ton rôle :
# - Aider à créer des stratégies de trading
# - Expliquer les indicateurs (SMA, RSI, MACD, Bollinger, etc.)
# - Conseiller sur la gestion du risque

# Style :
# - Concis (max 150 mots)
# - Pédagogique
# - Utilise des emojis : 📊📈📉💡⚠️
# - Exemples concrets

# Important :
# - Reste dans le trading/finance
# - Pas de conseils d'investissement spécifiques""",
#                 messages=history
#             )
            
#             assistant_message = response.content[0].text
#             history.append({
#                 "role": "assistant",
#                 "content": assistant_message
#             })
            
#         except Exception as e:
#             assistant_message = f"❌ Erreur API: {str(e)}"
#             print(f"Erreur Claude: {e}")
        
#         # Affichage des messages
#         messages_display = [
#             html.Div([
#                 html.P([
#                     "👋 Bonjour ! Je suis votre assistant IA.",
#                     html.Br(), html.Br(),
#                     "Je peux vous aider avec :",
#                     html.Br(),
#                     "• Explication des indicateurs",
#                     html.Br(),
#                     "• Conseils stratégiques",
#                     html.Br(),
#                     "• Gestion des risques"
#                 ], style={
#                     'color': '#000000',
#                     'fontSize': '14px',
#                     'margin': '0'
#                 })
#             ], style={
#                 'padding': '12px',
#                 'backgroundColor': '#E3F2FD',
#                 'borderRadius': '8px',
#                 'marginBottom': '10px',
#                 'border': '1px solid #2196F3'
#             })
#         ]
        
#         for msg in history:
#             content = msg["content"].split("\n\n[Contexte:")[0]
            
#             if msg["role"] == "user":
#                 messages_display.append(
#                     html.Div([
#                         html.P(content, style={
#                             'color': '#000000',
#                             'fontSize': '14px',
#                             'margin': '0'
#                         })
#                     ], style={
#                         'padding': '12px',
#                         'backgroundColor': '#BBDEFB',
#                         'borderRadius': '8px',
#                         'marginBottom': '10px',
#                         'marginLeft': '20%',
#                         'border': '1px solid #2196F3'
#                     })
#                 )
#             else:
#                 messages_display.append(
#                     html.Div([
#                         dcc.Markdown(content, style={
#                             'color': '#000000',
#                             'fontSize': '14px'
#                         })
#                     ], style={
#                         'padding': '12px',
#                         'backgroundColor': '#E3F2FD',
#                         'borderRadius': '8px',
#                         'marginBottom': '10px',
#                         'marginRight': '20%',
#                         'border': '1px solid #2196F3'
#                     })
#                 )
        
#         return messages_display, history, ""
    
    
#     # Callback 3: Auto-scroll
#     app.clientside_callback(
#         """
#         function(children) {
#             setTimeout(function() {
#                 var msgContainer = document.getElementById('chatbot-messages');
#                 if (msgContainer) {
#                     msgContainer.scrollTop = msgContainer.scrollHeight;
#                 }
#             }, 100);
#             return window.dash_clientside.no_update;
#         }
#         """,
#         Output('chatbot-messages', 'data-scroll'),
#         Input('chatbot-messages', 'children'),
#         prevent_initial_call=True
#     )