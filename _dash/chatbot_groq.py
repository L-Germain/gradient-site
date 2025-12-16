"""
Module chatbot avec API Groq (100% GRATUIT)
Widget sobre à gauche, gradient bleu, textes noirs
"""

import dash
from dash import html, dcc, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import os
# Import du system prompt depuis fichier séparé
from _dash.chatbot_system_prompt import SYSTEM_PROMPT

# Client Groq
AI_AVAILABLE = False
ai_client = None

try:
    from groq import Groq
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        ai_client = Groq(api_key=api_key)
        AI_AVAILABLE = True
        print("[OK] Groq initialise (API GRATUITE)")
    else:
        print("[X] GROQ_API_KEY manquante")
except ImportError:
    print("[!] Installez groq: pip install groq")
except Exception as e:
    print(f"[X] Erreur Groq: {e}")




def create_chatbot_layout():
    """Layout du chatbot flottant"""
    
    return html.Div([
        # Bouton toggle
        html.Div([
            dbc.Button(
                [
                    html.Img(src="/assets/new_logo.png", style={'width': '80%', 'height': '80%', 'objectFit': 'contain'}),
                    html.Div(className="chatbot-pulse")
                ],
                id="chatbot-toggle-btn",
                className="shadow",
                style={
                    'width': '65px',
                    'height': '65px',
                    'padding': '0',
                    'border': 'none',
                    'borderRadius': '50%',
                    'background': 'var(--gradient-gain)',  # Use the Gain gradient
                    'color': 'white',
                    'position': 'relative',
                    'display': 'flex',
                    'justifyContent': 'center',
                    'alignItems': 'center',
                    'overflow': 'visible',
                    'boxShadow': '0 4px 15px rgba(0, 227, 150, 0.4)' # Adjusted shadow color to match gain
                }
            )
        ], style={
            'position': 'fixed',
            'bottom': '60px',
            'left': '40px',
            'zIndex': '9999',
            'cursor': 'pointer'
        }),
        
        # Fenêtre chatbot
        html.Div([
            dbc.Card([
                # Header
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.I(className="fas fa-robot mr-2", style={'color': 'white'}),
                            html.Strong("Assistant IA", style={'color': 'white'}),
                        ], width=9),
                        dbc.Col([
                            dbc.Button(
                                html.I(className="fas fa-times", style={'color': 'white'}),
                                id="chatbot-close-btn",
                                color="link",
                                size="sm",
                                className="p-0"
                            )
                        ], width=3, className="text-right")
                    ])
                ], style={
                    'background': 'var(--gradient-gain)',
                    'borderBottom': 'none',
                    'padding': '12px 20px'
                }),
                
                # Body
                dbc.CardBody([
                    # Messages
                    html.Div(
                        id="chatbot-messages",
                        children=[
                            html.Div([
                                html.P([
                                    "👋 Bonjour ! Je suis votre assistant TradingLab.",
                                    html.Br(), html.Br(),
                                    "💡 Posez-moi des questions sur :",
                                    html.Br(),
                                    "• Comment utiliser l'application",
                                    html.Br(),
                                    "• Les indicateurs techniques",
                                    html.Br(),
                                    "• La création de stratégies"
                                ], style={'color': 'var(--text-primary)', 'fontSize': '14px', 'margin': '0'})
                            ], style={
                                'padding': '12px',
                                'backgroundColor': 'var(--bg-secondary)',
                                'borderRadius': '8px',
                                'marginBottom': '10px',
                                'border': '1px solid var(--border-light)'
                            })
                        ],
                        style={
                            'height': '450px',
                            'overflowY': 'auto',
                            'padding': '15px',
                            'backgroundColor': 'var(--bg-primary)',
                            'borderRadius': '5px',
                            'marginBottom': '15px',
                            'border': '1px solid var(--border-light)'
                        }
                    ),
                    
                    # Input
                    dbc.InputGroup([
                        dbc.Input(
                            id="chatbot-user-input",
                            placeholder="Posez votre question...",
                            type="text",
                            style={
                                'backgroundColor': 'var(--bg-secondary)',
                                'color': 'var(--text-primary)',
                                'border': '1px solid var(--border-light)'
                            }
                        ),
                        dbc.Button(
                            html.I(className="fas fa-paper-plane"),
                            id="chatbot-send-message",
                            className="btn-success", # Should pick up gradient
                            style={
                                'border': 'none',
                                'color': 'white'
                            }
                        )
                    ])
                ], style={'padding': '20px', 'backgroundColor': 'var(--bg-card)'}),
                
                # Footer
                dbc.CardFooter([
                    html.Small([
                        html.I(className="fas fa-zap mr-1", style={'color': 'var(--color-accent)'}),
                        html.Span("Groq - Gratuit & Rapide", style={'color': 'var(--text-secondary)'})
                    ])
                ], style={
                    'textAlign': 'center',
                    'padding': '10px',
                    'backgroundColor': 'var(--bg-card)',
                    'borderTop': '1px solid var(--border-light)'
                })
            ], style={
                'width': '380px',
                'maxHeight': '600px',
                'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
                'borderRadius': '10px',
                'overflow': 'hidden',
                'border': '1px solid var(--border-light)'
            })
        ], id="chatbot-window", style={
            'position': 'fixed',
            'bottom': '85px',
            'left': '20px',
            'zIndex': '9998',
            'display': 'none'
        }),
        
        # Stores
        dcc.Store(id='chatbot-history-store', data=[]),
        dcc.Store(id='chatbot-state-store', data={'is_open': False})
    ])


def register_chatbot_callbacks(app):
    """Callbacks du chatbot"""
    
    # Toggle
    @app.callback(
        [Output('chatbot-window', 'style'),
         Output('chatbot-state-store', 'data')],
        [Input('chatbot-toggle-btn', 'n_clicks'),
         Input('chatbot-close-btn', 'n_clicks')],
        State('chatbot-state-store', 'data'),
        prevent_initial_call=True
    )
    def toggle_chatbot(toggle_clicks, close_clicks, state):
        current_state = state.get('is_open', False)
        new_state = not current_state
        
        if new_state:
            window_style = {
                'position': 'fixed',
                'bottom': '85px',
                'left': '20px',
                'zIndex': '9998',
                'display': 'block'
            }
        else:
            window_style = {
                'position': 'fixed',
                'bottom': '85px',
                'left': '20px',
                'zIndex': '9998',
                'display': 'none'
            }
        
        return window_style, {'is_open': new_state}
    
    
    # Messages
    @app.callback(
        [Output('chatbot-messages', 'children'),
         Output('chatbot-history-store', 'data'),
         Output('chatbot-user-input', 'value')],
        [Input('chatbot-send-message', 'n_clicks'),
         Input('chatbot-user-input', 'n_submit')],
        [State('chatbot-user-input', 'value'),
         State('chatbot-history-store', 'data'),
         State('strategy-store', 'data')],
        prevent_initial_call=True
    )
    def handle_message(send_clicks, input_submit, user_input, history, strategy_data):
        
        if not AI_AVAILABLE:
            error = html.Div([
                html.P("❌ API Groq non configurée. Ajoutez GROQ_API_KEY dans .env", 
                       style={'color': '#000000', 'fontSize': '14px', 'margin': '0'})
            ], style={
                'padding': '12px',
                'backgroundColor': '#FFEBEE',
                'borderRadius': '8px',
                'marginBottom': '10px',
                'border': '1px solid #EF5350'
            })
            return [error], history or [], ""
        
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        if not user_input or not user_input.strip():
            raise PreventUpdate
        
        history = history or []
        
        # Contexte stratégie
        context = ""
        if strategy_data and strategy_data.get('strategy_data'):
            strategy = strategy_data['strategy_data']
            context = f"\n[L'utilisateur travaille sur : {strategy.get('name', 'Sans nom')}]"
        
        history.append({
            "role": "user",
            "content": user_input + context
        })
        
        try:
            # Appel Groq
            response = ai_client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Modèle gratuit le plus performant
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *history
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            assistant_message = response.choices[0].message.content
            
            history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
        except Exception as e:
            assistant_message = f"❌ Erreur: {str(e)}"
            print(f"Erreur Groq: {e}")
        
        # Affichage
        # Affichage
        messages_display = [
            html.Div([
                html.P([
                    "👋 Bonjour ! Je suis votre assistant Gradient Systems.",
                    html.Br(), html.Br(),
                    "💡 Posez-moi des questions sur :",
                    html.Br(),
                    "• Comment utiliser l'application",
                    html.Br(),
                    "• Les indicateurs techniques",
                    html.Br(),
                    "• La création de stratégies"
                ], style={'color': 'var(--text-primary)', 'fontSize': '14px', 'margin': '0'})
            ], style={
                'padding': '12px',
                'backgroundColor': 'var(--bg-secondary)',
                'borderRadius': '8px',
                'marginBottom': '10px',
                'border': '1px solid var(--border-light)'
            })
        ]
        
        for msg in history:
            content = msg["content"].split("\n[L'utilisateur")[0]
            
            if msg["role"] == "user":
                messages_display.append(
                    html.Div([
                        html.P(content, style={'color': 'var(--text-primary)', 'fontSize': '14px', 'margin': '0'})
                    ], style={
                        'padding': '12px',
                        'backgroundColor': 'rgba(0, 102, 255, 0.1)', # Low opacity accent
                        'borderRadius': '8px',
                        'marginBottom': '10px',
                        'marginLeft': '20%',
                        'border': '1px solid var(--color-accent)'
                    })
                )
            else:
                messages_display.append(
                    html.Div([
                        dcc.Markdown(content, style={'color': 'var(--text-primary)', 'fontSize': '14px'})
                    ], style={
                        'padding': '12px',
                        'backgroundColor': 'var(--bg-secondary)',
                        'borderRadius': '8px',
                        'marginBottom': '10px',
                        'marginRight': '20%',
                        'border': '1px solid var(--border-light)'
                    })
                )
        
        return messages_display, history, ""
    
    
    # Auto-scroll
    app.clientside_callback(
        """
        function(children) {
            setTimeout(function() {
                var el = document.getElementById('chatbot-messages');
                if (el) { el.scrollTop = el.scrollHeight; }
            }, 100);
            return window.dash_clientside.no_update;
        }
        """,
        Output('chatbot-messages', 'data-scroll'),
        Input('chatbot-messages', 'children'),
        prevent_initial_call=True
    )