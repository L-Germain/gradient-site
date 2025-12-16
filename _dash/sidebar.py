import dash_bootstrap_components as dbc
from dash import html, dcc

def create_sidebar(user_role='individual'):
    """
    Creates the vertical sidebar for navigation.
    """
    return html.Div(
        [
            # --- LOGO AREA ---
            html.Div(
                [
                    html.Img(src="/assets/logo.png", style={"width": "100%", "maxWidth": "180px", "marginBottom": "20px"}),
                    html.Hr(style={"borderColor": "var(--border-light)"}),
                ],
                className="text-center p-3"
            ),
            
            # --- NAVIGATION ---
            html.Div(
                [
                    # Creation
                    dbc.NavLink(
                        [html.I(className="fas fa-magic mr-3"), html.Span(id="nav-creation", children="Création")],
                        href="#",
                        id="nav-btn-creation",
                        className="sidebar-link active",
                        n_clicks=0
                    ),
                    # Results
                    dbc.NavLink(
                        [html.I(className="fas fa-chart-bar mr-3"), html.Span(id="nav-results", children="Résultats")],
                        href="#",
                        id="nav-btn-results",
                        className="sidebar-link",
                        n_clicks=0
                    ),
                    
                    html.Hr(style={"borderColor": "var(--border-light)", "margin": "10px 0"}),
                    
                    # --- DYNAMIC SECTION ---
                    html.Div([
                        # Professional View: Clients
                        html.Div([
                            html.H6("MES CLIENTS", className="sidebar-heading px-3 mt-4 mb-1 text-muted", style={"fontSize": "0.75rem"}),
                            dbc.Button(
                                [html.I(className="fas fa-plus-circle mr-2"), "Nouveau Client"],
                                id="btn-add-client",
                                color="link",
                                className="sidebar-link text-left pl-3",
                                style={"textDecoration": "none", "color": "var(--primary)"}
                            ),
                            html.Div(id="sidebar-clients-list") # Populated by callback
                        ], style={"display": "block" if user_role == 'professional' else "none"}),

                        # Individual View: Folders
                        html.Div([
                            html.H6("MES DOSSIERS", className="sidebar-heading px-3 mt-4 mb-1 text-muted", style={"fontSize": "0.75rem"}),
                            dbc.Button(
                                [html.I(className="fas fa-folder-plus mr-2"), "Nouveau Dossier"],
                                id="btn-add-folder",
                                color="link", 
                                className="sidebar-link text-left pl-3",
                                style={"textDecoration": "none", "color": "var(--primary)"}
                            ),
                            html.Div(id="sidebar-folders-list") # Populated by callback
                        ], style={"display": "block" if user_role == 'individual' else "none"})
                    ]),

                    html.Hr(style={"borderColor": "var(--border-light)", "margin": "10px 0"}),

                    # Options
                    dbc.NavLink(
                        [html.I(className="fas fa-chart-area mr-3"), html.Span(id="nav-options", children="Options")],
                        href="#",
                        id="nav-btn-options",
                        className="sidebar-link",
                        n_clicks=0
                    ),
                    # Compare
                    dbc.NavLink(
                        [html.I(className="fas fa-balance-scale mr-3"), html.Span(id="nav-compare", children="Comparaison")],
                        href="#",
                        id="nav-btn-compare",
                        className="sidebar-link",
                        n_clicks=0
                    ),
                    # Synthetic
                    dbc.NavLink(
                        [html.I(className="fas fa-atom mr-3"), html.Span(id="nav-synthetic", children="Synthétique")],
                        href="#",
                        id="nav-btn-synthetic",
                        className="sidebar-link",
                        n_clicks=0
                    ),
                    # Import
                    dbc.NavLink(
                        [html.I(className="fas fa-file-upload mr-3"), html.Span(id="nav-import", children="Import")],
                        href="#",
                        id="nav-btn-import",
                        className="sidebar-link",
                        n_clicks=0
                    ),
                ],
                id="sidebar-nav-container",
                className="my-4"
            ),
            
            # --- CONTROLS FOOTER (Consolidated) ---
            html.Div(
                [
                    html.Hr(style={"borderColor": "var(--border-light)"}),
                    
                    dbc.DropdownMenu(
                        [
                            dbc.DropdownMenuItem("Mon Compte", header=True),
                            dbc.DropdownMenuItem([html.I(className="fas fa-user-circle mr-2"), "Profil"], href="#", disabled=True),
                            dbc.DropdownMenuItem([html.I(className="fas fa-credit-card mr-2"), "Abonnement"], href="#", disabled=True),
                            dbc.DropdownMenuItem(divider=True),
                            
                            dbc.DropdownMenuItem("Interface", header=True),
                            
                            # Language
                            dbc.DropdownMenuItem(
                                html.Div([
                                    html.Span([html.I(className="fas fa-globe mr-2"), "Langue"], className="mr-3"),
                                    dbc.RadioItems(
                                        id='language-switcher-sidebar',
                                        options=[
                                            {'label': 'FR', 'value': 'fr'},
                                            {'label': 'EN', 'value': 'en'},
                                        ],
                                        value='fr',
                                        inline=True,
                                        inputClassName="mr-1",
                                    ),
                                ], className="d-flex align-items-center justify-content-between w-100"),
                                toggle=False
                            ),
                            
                            # Theme
                            dbc.DropdownMenuItem(
                                dbc.Checklist(
                                    options=[{"label": "Mode Sombre", "value": True}],
                                    value=[],
                                    id="theme-toggle-wrapper", # Wrapper to match switch logic if needed, but easier to use Switch directly
                                    switch=True,
                                    style={"width": "100%"}
                                ),
                                toggle=False,
                                style={"display": "none"} # Hiding this complex wrap attempt, using simpler below
                            ),
                             dbc.DropdownMenuItem(
                                html.Div([
                                    html.Span([html.I(className="fas fa-moon mr-2"), "Mode Sombre"]),
                                    dbc.Switch(id="theme-toggle", value=False, className="ml-auto")
                                ], className="d-flex align-items-center justify-content-between w-100"),
                                toggle=False
                            ),
                            
                            # Advanced Mode
                             dbc.DropdownMenuItem(
                                html.Div([
                                    html.Span([html.I(className="fas fa-sliders-h mr-2"), "Mode Avancé"]),
                                    dbc.Switch(id="advanced-mode-toggle-sidebar", value=False, className="ml-auto")
                                ], className="d-flex align-items-center justify-content-between w-100"),
                                toggle=False
                            ),

                            dbc.DropdownMenuItem(divider=True),
                            
                            # Role Switcher (Dev)
                            dbc.DropdownMenuItem("Développeur", header=True),
                             dbc.DropdownMenuItem(
                                html.Div([
                                    dbc.Select(
                                        id="role-switcher",
                                        options=[
                                            {"label": "Role: Partic.", "value": "individual"},
                                            {"label": "Role: Pro", "value": "professional"},
                                        ],
                                        value=user_role,
                                        size="sm"
                                    )
                                ]),
                                toggle=False
                            ),
                        ],
                        label="Paramètres",
                        nav=False,
                        # in_navbar=False,
                        direction="up",
                        toggle_style={
                            "backgroundColor": "transparent", 
                            "border": "none", 
                            "color": "var(--text-secondary)",
                            "width": "100%",
                            "textAlign": "left",
                            "padding": "0"
                        },
                        style={"width": "100%"},
                        className="w-100 custom-settings-dropdown"
                    )
                ],
                className="mt-auto p-3"
            )
        ],
        className="sidebar",
        id="sidebar"
    )
