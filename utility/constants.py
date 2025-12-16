# Définition des types d'actifs disponibles avec leurs noms complets
asset_types = {
    "actions_cac40": {
        "label": "Actions CAC 40",
        "assets": [
            "AC.PA", "ACA.PA", "AI.PA", "AIR.PA", "ALO.PA", "ATO.PA", "BN.PA", "BNP.PA", 
            "CA.PA", "CAP.PA", "CS.PA", "DG.PA", "DSY.PA", "EN.PA", "ENGI.PA", "ERF.PA", 
            "EL.PA", "TTE.PA", "GLE.PA", "HO.PA", "KER.PA", "LR.PA", "MC.PA", "ML.PA", 
            "ORA.PA", "OR.PA", "PUB.PA", "RI.PA", "RMS.PA", "RNO.PA", "SAF.PA", "SAN.PA", 
            "SGO.PA", "STLA.PA", "STM.PA", "SU.PA", "SW.PA", "TEP.PA", "VIE.PA", "VIV.PA"
        ]
    },
    "crypto": {
        "label": "Crypto-monnaies",
        "assets": [
            "BTC-USD", "ETH-USD", "XRP-USD", "BNB-USD", "ADA-USD", "SOL-USD", "DOGE-USD", 
            "DOT-USD", "LINK-USD", "MATIC-USD", "AVAX-USD", "UNI-USD", "ATOM-USD"
        ]
    },
    "actions_us": {
        "label": "Actions US (Top 50)",
        "assets": [
            "NVDA", "MSFT", "AAPL", "GOOGL", "AMZN", "META", "AVGO", "BRK-B", "TSLA", "JPM",
            "WMT", "LLY", "V", "ORCL", "MA", "NFLX", "XOM", "JNJ", "COST", "PLTR",
            "HD", "BAC", "ABBV", "PG", "CVX", "KO", "GE", "UNH", "AMD", "CSCO",
            "WFC", "PM", "CRM", "MS", "IBM", "GS", "ABT", "AXP", "LIN", "MCD",
            "PFE", "TXN", "SBUX", "TMUS", "CMCSA", "INTC", "VZ", "PEP", "ADBE", "DIS"
        ]
    },
    "fonds": {
        "label": "Fonds d'Investissement",
        "assets": [
            # Indices
            "SPY", "VOO", "QQQ", "VTI", "IWM",
            
            # Dividendes & Value
            "SCHD", "VYM", "VIG", "NOBL",
            
            # Obligations
            "BND", "TLT", "AGG", "HYG",
            
            # International
            "VXUS", "VWO", "VEA",
            
            # Secteurs & Thèmes
            "XLK", "XLV", "XLF", "XLE", "GLD", "ARKK", "SMH"
        ]
    },
    "forex": {
        "label": "Forex (FX)",
        "assets": [
            "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", "USDCHF=X", 
            "NZDUSD=X", "EURJPY=X", "GBPJPY=X", "EURGBP=X", "EURCAD=X", "EURAUD=X"
        ]
    },
    "etfs": {
        "label": "ETFs",
        "assets": [

            # Indices US principaux
            "SPY", "QQQ", "IWM", "VTI", "VOO", "VIG", "SCHD", "DGRO",
            
            # Indices internationaux
            "VEA", "VWO", "EFA", "EEM", "IEFA", "IEMG", "VXUS", "ACWI",
            
            # Obligations
            "AGG", "LQD", "HYG", "BND", "TLT", "IEF", "SHY", "VTEB", "EMB", "JNK",
            
            # Matières premières
            "GLD", "SLV", "USO", "UNG", "DBA", "DBC", "PDBC", "IAU", "GLTR",
            
            # Secteurs US
            "XLF", "XLE", "XLK", "XLV", "XLI", "XLP", "XLY", "XLU", "XLRE", "XLB", "XLC",
            
            # Croissance/Value US
            "VUG", "VTV", "IVW", "IVE", "MTUM", "QUAL", "USMV", "VMOT",
            
            # Dividendes US
            "VYM", "HDV", "NOBL", "DVY", "FDN", "SPHD", "PEY",
            
            # Thématiques US
            "ARK", "ARKK", "ARKQ", "ARKW", "ICLN", "PBW", "ESGU", "ESGD", "SMH", "XBI",
            
            # ETFs EUROPÉENS - Indices larges
            "CSPX.L", "VUSA.L", "SXR8.DE", "EUNL.DE", "MSCI.L", "VMID.L", "ZPRX.L",
            "IEUR.L", "IEUS.L", "XMME.DE", "XMMU.DE", "EXS1.DE", "EXXP.DE",
            
            # ETFs EUROPÉENS - Actions européennes
            "CSX1.L", "VEUR.L", "SX5E.DE", "EXS2.DE", "IESE.L", "VMEU.L", "ZPRV.L",
            "XESX.DE", "CSSX.L", "VGEU.L", "XMEU.DE", "EUMS.L", "IEAC.L",
            
            # ETFs EUROPÉENS - Pays spécifiques
            "VFEM.L", "XMWO.DE", "IEFM.L", "CSGR.L", "XMCH.DE", "IEMM.L", "XMJP.DE",
            "CSUK.L", "XMFR.DE", "XMIT.DE", "XMES.DE", "XMSE.DE", "XMNO.DE",
            
            # ETFs EUROPÉENS - Obligations
            "AGGU.L", "VGOV.L", "XGLE.DE", "IEAC.L", "CORP.L", "XMTG.DE", "IGLT.L",
            "SEML.L", "XMHB.DE", "XMGB.DE", "XMEB.DE", "XMFB.DE", "XMIB.DE",
            
            # ETFs EUROPÉENS - Secteurs
            "XMFN.DE", "XMEN.DE", "XMTE.DE", "XMHC.DE", "XMIN.DE", "XMCS.DE",
            "XMCD.DE", "XMUT.DE", "XMRE.DE", "XMMT.DE", "XMCM.DE",
            
            # ETFs EUROPÉENS - Matières premières et thématiques
            "PHAU.L", "PHAG.L", "CRUD.L", "XMCO.DE", "XMAG.DE", "XMEN.DE",
            "HEAL.L", "ECAR.L", "IDRV.L", "RBOT.L", "CLNE.L", "INRG.L"
        ]
    }
}

# Ajoutez ceci dans votre fichier principal après les imports

STRATEGY_TEMPLATES = {
    "sma_crossover": {
        "name": "SMA Crossover Classic",
        "initial_capital": 100000,
        "allocation_pct": 20,
        "transaction_cost": 5,
        "stop_loss_pct": 5,
        "take_profit_pct": 10,
        "decision_blocks": [
            {
                "conditions": [
                    {
                        "stock1": "PLACEHOLDER_STOCK",  # Sera remplacé par l'actif sélectionné
                        "indicator1": {"type": "SMA", "params": [20]},
                        "operator": ">",
                        "comparison_type": "indicator",
                        "stock2": "PLACEHOLDER_STOCK",
                        "indicator2": {"type": "SMA", "params": [50]}
                    }
                ],
                "actions": {"PLACEHOLDER_STOCK": "Acheter"}
            }
        ]
    },
    
    "rsi_oversold": {
        "name": "RSI Oversold/Overbought",
        "initial_capital": 100000,
        "allocation_pct": 15,
        "transaction_cost": 3,
        "stop_loss_pct": 8,
        "take_profit_pct": 15,
        "decision_blocks": [
            {
                "conditions": [
                    {
                        "stock1": "PLACEHOLDER_STOCK",
                        "indicator1": {"type": "RSI", "params": [14]},
                        "operator": "<",
                        "comparison_type": "value",
                        "comparison_value": 30
                    }
                ],
                "actions": {"PLACEHOLDER_STOCK": "Acheter"}
            },
            {
                "conditions": [
                    {
                        "stock1": "PLACEHOLDER_STOCK",
                        "indicator1": {"type": "RSI", "params": [14]},
                        "operator": ">",
                        "comparison_type": "value",
                        "comparison_value": 70
                    }
                ],
                "actions": {"PLACEHOLDER_STOCK": "Vendre"}
            }
        ]
    },
    
    "bollinger_breakout": {
        "name": "Bollinger Bands Breakout",
        "initial_capital": 100000,
        "allocation_pct": 25,
        "transaction_cost": 4,
        "stop_loss_pct": 6,
        "take_profit_pct": 12,
        "decision_blocks": [
            {
                "conditions": [
                    {
                        "stock1": "PLACEHOLDER_STOCK",
                        "indicator1": {"type": "PRICE", "params": []},
                        "operator": ">",
                        "comparison_type": "indicator",
                        "stock2": "PLACEHOLDER_STOCK",
                        "indicator2": {"type": "BBAND_UPPER", "params": [20, 2]}
                    }
                ],
                "actions": {"PLACEHOLDER_STOCK": "Acheter"}
            }
        ]
    }
}


# Dictionnaire associant les tickers à leurs noms complets
ticker_to_name = {
    # CAC 40
    "AC.PA": "Accor SA",
    "ACA.PA": "Crédit Agricole SA",
    "AI.PA": "Air Liquide SA",
    "AIR.PA": "Airbus SE",
    "ALO.PA": "Alstom SA",
    "ATO.PA": "Atos SE",
    "BN.PA": "Danone SA",
    "BNP.PA": "BNP Paribas SA",
    "CA.PA": "Carrefour SA",
    "CAP.PA": "Capgemini SE",
    "CS.PA": "AXA SA",
    "DG.PA": "Vinci SA",
    "DSY.PA": "Dassault Systèmes SE",
    "EN.PA": "Bouygues SA",
    "ENGI.PA": "Engie SA",
    "ERF.PA": "Eurofins Scientific SE",
    "EL.PA": "EssilorLuxottica SA",
    "TTE.PA": "TotalEnergies SE",
    "GLE.PA": "Société Générale SA",
    "HO.PA": "Thales SA",
    "KER.PA": "Kering SA",
    "LR.PA": "Legrand SA",
    "MC.PA": "LVMH Moët Hennessy Louis Vuitton SE",
    "ML.PA": "Michelin SCA",
    "ORA.PA": "Orange SA",
    "OR.PA": "L'Oréal SA",
    "PUB.PA": "Publicis Groupe SA",
    "RI.PA": "Pernod Ricard SA",
    "RMS.PA": "Hermès International SA",
    "RNO.PA": "Renault SA",
    "SAF.PA": "Safran SA",
    "SAN.PA": "Sanofi SA",
    "SGO.PA": "Compagnie de Saint-Gobain SA",
    "STLA.PA": "Stellantis NV",
    "STM.PA": "STMicroelectronics NV",
    "SU.PA": "Schneider Electric SE",
    "SW.PA": "Sodexo SA",
    "TEP.PA": "Teleperformance SE",
    "VIE.PA": "Veolia Environnement SA",
    "VIV.PA": "Vivendi SE",
    
    # Crypto-monnaies
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "XRP-USD": "Ripple",
    "BNB-USD": "Binance Coin",
    "ADA-USD": "Cardano",
    "SOL-USD": "Solana",
    "DOGE-USD": "Dogecoin",
    "DOT-USD": "Polkadot",
    "LINK-USD": "Chainlink",
    "MATIC-USD": "Polygon",
    "AVAX-USD": "Avalanche",
    "UNI-USD": "Uniswap",
    "ATOM-USD": "Cosmos",
    
    # Forex
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "USDJPY=X": "USD/JPY",
    "AUDUSD=X": "AUD/USD",
    "USDCAD=X": "USD/CAD",
    "USDCHF=X": "USD/CHF",
    "NZDUSD=X": "NZD/USD",
    "EURJPY=X": "EUR/JPY",
    "GBPJPY=X": "GBP/JPY",
    "EURGBP=X": "EUR/GBP",
    "EURCAD=X": "EUR/CAD",
    "EURAUD=X": "EUR/AUD",

    #ETFs
    "SPY": "SPDR S&P 500",
    "QQQ": "Invesco NASDAQ 100", 
    "IWM": "iShares Russell 2000",
    "VTI": "Vanguard Total Stock Market",
    "VOO": "Vanguard S&P 500",
    "VIG": "Vanguard Dividend Appreciation",
    "SCHD": "Schwab US Dividend Equity",
    "DGRO": "iShares Core Dividend Growth",
    
    # Indices internationaux
    "VEA": "Vanguard FTSE Developed Markets",
    "VWO": "Vanguard FTSE Emerging Markets",
    "EFA": "iShares MSCI EAFE",
    "EEM": "iShares MSCI Emerging Markets",
    "IEFA": "iShares Core MSCI EAFE",
    "IEMG": "iShares Core MSCI Emerging Markets",
    "VXUS": "Vanguard Total International Stock",
    "ACWI": "iShares MSCI ACWI",
    
    # Obligations
    "AGG": "iShares Core Aggregate Bond",
    "LQD": "iShares Investment Grade Corporate Bond",
    "HYG": "iShares High Yield Corporate Bond",
    "BND": "Vanguard Total Bond Market",
    "TLT": "iShares 20+ Year Treasury Bond",
    "IEF": "iShares 7-10 Year Treasury Bond",
    "SHY": "iShares 1-3 Year Treasury Bond",
    "VTEB": "Vanguard Tax-Exempt Bond",
    "EMB": "iShares Emerging Markets Bond",
    "JNK": "SPDR Bloomberg High Yield Bond",
    
    # Matières premières
    "GLD": "SPDR Gold Trust",
    "SLV": "iShares Silver Trust",
    "USO": "United States Oil Fund",
    "UNG": "United States Natural Gas Fund",
    "DBA": "Invesco DB Agriculture Fund",
    "DBC": "Invesco DB Commodity Index Tracking Fund",
    "PDBC": "Invesco Optimum Yield Diversified Commodity",
    "IAU": "iShares Gold Trust",
    "GLTR": "abrdn Physical Precious Metals Basket Shares",
    
    # Secteurs
    "XLF": "Financial Select Sector SPDR",
    "XLE": "Energy Select Sector SPDR",
    "XLK": "Technology Select Sector SPDR",
    "XLV": "Health Care Select Sector SPDR",
    "XLI": "Industrial Select Sector SPDR",
    "XLP": "Consumer Staples Select Sector SPDR",
    "XLY": "Consumer Discretionary Select Sector SPDR",
    "XLU": "Utilities Select Sector SPDR",
    "XLRE": "Real Estate Select Sector SPDR",
    "XLB": "Materials Select Sector SPDR",
    "XLC": "Communication Services Select Sector SPDR",
    
    # Croissance/Value
    "VUG": "Vanguard Growth",
    "VTV": "Vanguard Value",
    "IVW": "iShares S&P 500 Growth",
    "IVE": "iShares S&P 500 Value",
    "MTUM": "iShares MSCI USA Momentum Factor",
    "QUAL": "iShares MSCI USA Quality Factor",
    "USMV": "iShares MSCI USA Min Vol Factor",
    "VMOT": "Vanguard Russell 1000 Momentum",
    
    # Dividendes
    "VYM": "Vanguard High Dividend Yield",
    "HDV": "iShares Core High Dividend",
    "NOBL": "ProShares S&P 500 Dividend Aristocrats",
    "DVY": "iShares Select Dividend",
    "FDN": "First Trust Dow Jones Internet",
    "SPHD": "Invesco S&P 500 High Dividend Low Volatility",
    "PEY": "Invesco High Yield Equity Dividend Achievers",
    
    # Thématiques
    "ARK": "ARK Innovation ETF",
    "ARKK": "ARK Innovation ETF",
    "ARKQ": "ARK Autonomous Technology & Robotics",
    "ARKW": "ARK Next Generation Internet",
    "ICLN": "iShares Global Clean Energy",
    "PBW": "Invesco WilderHill Clean Energy",
    "ESGU": "iShares MSCI USA ESG Optimized",
    "ESGD": "iShares MSCI EAFE ESG Optimized",
    "SMH": "VanEck Semiconductor",
    "XBI": "SPDR S&P Biotech",

        # ETFs EUROPÉENS - Indices larges
    "CSPX.L": "iShares Core S&P 500 UCITS ETF",
    "VUSA.L": "Vanguard S&P 500 UCITS ETF",
    "SXR8.DE": "iShares Core S&P 500 UCITS ETF",
    "EUNL.DE": "iShares Core MSCI World UCITS ETF",
    "MSCI.L": "iShares MSCI World UCITS ETF",
    "VMID.L": "Vanguard FTSE Developed World UCITS ETF",
    "ZPRX.L": "SPDR MSCI World UCITS ETF",
    "IEUR.L": "iShares Core EURO STOXX 50 UCITS ETF",
    "IEUS.L": "iShares Core MSCI Europe UCITS ETF",
    "XMME.DE": "Xtrackers MSCI Emerging Markets UCITS ETF",
    "XMMU.DE": "Xtrackers MSCI USA UCITS ETF",
    "EXS1.DE": "iShares Core EURO STOXX 50 UCITS ETF",
    "EXXP.DE": "iShares Core MSCI Europe UCITS ETF",
    
    # ETFs EUROPÉENS - Actions européennes
    "CSX1.L": "iShares Core EURO STOXX 50 UCITS ETF",
    "VEUR.L": "Vanguard FTSE Europe UCITS ETF",
    "SX5E.DE": "SPDR EURO STOXX 50 UCITS ETF",
    "EXS2.DE": "iShares EURO STOXX 50 UCITS ETF",
    "IESE.L": "iShares MSCI Europe UCITS ETF",
    "VMEU.L": "Vanguard FTSE Europe UCITS ETF",
    "ZPRV.L": "SPDR MSCI Europe UCITS ETF",
    "XESX.DE": "Xtrackers EURO STOXX 50 UCITS ETF",
    "CSSX.L": "iShares EURO STOXX Small Cap UCITS ETF",
    "VGEU.L": "Vanguard FTSE Europe ex-UK UCITS ETF",
    "XMEU.DE": "Xtrackers MSCI Europe UCITS ETF",
    "EUMS.L": "iShares MSCI Europe Small Cap UCITS ETF",
    "IEAC.L": "iShares Euro Aggregate Bond UCITS ETF",
    
    # ETFs EUROPÉENS - Pays spécifiques
    "VFEM.L": "Vanguard FTSE Emerging Markets UCITS ETF",
    "XMWO.DE": "Xtrackers MSCI World UCITS ETF",
    "IEFM.L": "iShares MSCI EM UCITS ETF",
    "CSGR.L": "iShares MSCI Germany UCITS ETF",
    "XMCH.DE": "Xtrackers MSCI China UCITS ETF",
    "IEMM.L": "iShares MSCI EM UCITS ETF",
    "XMJP.DE": "Xtrackers MSCI Japan UCITS ETF",
    "CSUK.L": "iShares MSCI UK UCITS ETF",
    "XMFR.DE": "Xtrackers MSCI France UCITS ETF",
    "XMIT.DE": "Xtrackers MSCI Italy UCITS ETF",
    "XMES.DE": "Xtrackers MSCI Spain UCITS ETF",
    "XMSE.DE": "Xtrackers MSCI Sweden UCITS ETF",
    "XMNO.DE": "Xtrackers MSCI Norway UCITS ETF",
    
    # ETFs EUROPÉENS - Obligations
    "AGGU.L": "iShares Core Global Aggregate Bond UCITS ETF",
    "VGOV.L": "Vanguard Global Bond Index Fund",
    "XGLE.DE": "Xtrackers Global Government Bond UCITS ETF",
    "CORP.L": "iShares Euro Corporate Bond UCITS ETF",
    "XMTG.DE": "Xtrackers German Government Bond UCITS ETF",
    "IGLT.L": "iShares Euro Government Bond UCITS ETF",
    "SEML.L": "SPDR Bloomberg EM Bond UCITS ETF",
    "XMHB.DE": "Xtrackers High Yield Corporate Bond UCITS ETF",
    "XMGB.DE": "Xtrackers Global Government Bond UCITS ETF",
    "XMEB.DE": "Xtrackers Euro Government Bond UCITS ETF",
    "XMFB.DE": "Xtrackers French Government Bond UCITS ETF",
    "XMIB.DE": "Xtrackers Italian Government Bond UCITS ETF",
    
    # ETFs EUROPÉENS - Secteurs
    "XMFN.DE": "Xtrackers MSCI World Financials UCITS ETF",
    "XMEN.DE": "Xtrackers MSCI World Energy UCITS ETF",
    "XMTE.DE": "Xtrackers MSCI World Technology UCITS ETF",
    "XMHC.DE": "Xtrackers MSCI World Health Care UCITS ETF",
    "XMIN.DE": "Xtrackers MSCI World Industrials UCITS ETF",
    "XMCS.DE": "Xtrackers MSCI World Consumer Staples UCITS ETF",
    "XMCD.DE": "Xtrackers MSCI World Consumer Discretionary UCITS ETF",
    "XMUT.DE": "Xtrackers MSCI World Utilities UCITS ETF",
    "XMRE.DE": "Xtrackers MSCI World Real Estate UCITS ETF",
    "XMMT.DE": "Xtrackers MSCI World Materials UCITS ETF",
    "XMCM.DE": "Xtrackers MSCI World Communication Services UCITS ETF",
    
    # ETFs EUROPÉENS - Matières premières et thématiques
    "PHAU.L": "WisdomTree Physical Gold",
    "PHAG.L": "WisdomTree Physical Silver",
    "CRUD.L": "WisdomTree WTI Crude Oil",
    "XMCO.DE": "Xtrackers MSCI World Commodities UCITS ETF",
    "XMAG.DE": "Xtrackers Agriculture UCITS ETF",
    "HEAL.L": "iShares Healthcare Innovation UCITS ETF",
    "ECAR.L": "iShares Electric Vehicles UCITS ETF",
    "IDRV.L": "iShares Autonomous Driving UCITS ETF",
    "RBOT.L": "iShares Automation & Robotics UCITS ETF",
    "CLNE.L": "iShares Global Clean Energy UCITS ETF",
    "INRG.L": "iShares Global Clean Energy UCITS ETF",

    # Actions US (Top 50)
    "NVDA": "NVIDIA Corporation",
    "MSFT": "Microsoft Corporation",
    "AAPL": "Apple Inc.",
    "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.",
    "META": "Meta Platforms Inc.",
    "AVGO": "Broadcom Inc.",
    "BRK-B": "Berkshire Hathaway Inc.",
    "TSLA": "Tesla Inc.",
    "JPM": "JPMorgan Chase & Co.",
    "WMT": "Walmart Inc.",
    "LLY": "Eli Lilly and Company",
    "V": "Visa Inc.",
    "ORCL": "Oracle Corporation",
    "MA": "Mastercard Incorporated",
    "NFLX": "Netflix Inc.",
    "XOM": "Exxon Mobil Corporation",
    "JNJ": "Johnson & Johnson",
    "COST": "Costco Wholesale Corporation",
    "PLTR": "Palantir Technologies Inc.",
    "HD": "The Home Depot Inc.",
    "BAC": "Bank of America Corporation",
    "ABBV": "AbbVie Inc.",
    "PG": "The Procter & Gamble Company",
    "CVX": "Chevron Corporation",
    "KO": "The Coca-Cola Company",
    "GE": "General Electric Company",
    "UNH": "UnitedHealth Group Incorporated",
    "AMD": "Advanced Micro Devices Inc.",
    "CSCO": "Cisco Systems Inc.",
    "WFC": "Wells Fargo & Company",
    "PM": "Philip Morris International Inc.",
    "CRM": "Salesforce Inc.",
    "MS": "Morgan Stanley",
    "IBM": "International Business Machines Corporation",
    "GS": "The Goldman Sachs Group Inc.",
    "ABT": "Abbott Laboratories",
    "AXP": "American Express Company",
    "LIN": "Linde plc",
    "MCD": "McDonald's Corporation",
    "PFE": "Pfizer Inc.",
    "TXN": "Texas Instruments Incorporated",
    "SBUX": "Starbucks Corporation",
    "TMUS": "T-Mobile US Inc.",
    "CMCSA": "Comcast Corporation",
    "INTC": "Intel Corporation",
    "VZ": "Verizon Communications Inc.",
    "PEP": "PepsiCo Inc.",
    "ADBE": "Adobe Inc.",
    "DIS": "The Walt Disney Company",

    # Fonds & ETFs (Complément)
    "SCHD": "Schwab US Dividend Equity ETF",
    "ARKK": "ARK Innovation ETF"
}


indicators = {
    "SMA": {
        "name": "Simple Moving Average",
        "params": ["Période"]
    },
    "EMA": {
        "name": "Exponential Moving Average",
        "params": ["Période"]
    },
    "RSI": {
        "name": "Relative Strength Index",
        "params": ["Période"]
    },
    "BBAND_UPPER": {
        "name": "Bollinger Band (Upper)",
        "params": ["Période", "Écart-Type"]
    },
    "BBAND_LOWER": {
        "name": "Bollinger Band (Lower)",
        "params": ["Période", "Écart-Type"]
    },
    "MACD": {
        "name": "MACD",
        "params": ["Période rapide", "Période lente", "Signal"]
    },
        "DCA": {  
        "name": "DCA (Investissement périodique)",
        "params": ["Période (jours)"]
    },
    "PRICE": {
        "name": "Prix",
        "params": []
    }
}
# constants.py

# ... (gardez vos autres constantes comme operators, indicators, etc.)

# MISE À JOUR : Dictionnaire des stratégies simples complètes avec un nom pour chaque
SIMPLE_STRATEGIES = {
    # --- ACHETER ---
    ('Acheter', 'Lorsque le prix baisse'): {
        "name": "Achat sur Baisse de Prix (SMA)",
        "initial_capital": 100000, "allocation_pct": 10, "transaction_cost": 1, "stop_loss_pct": 5, "take_profit_pct": 10,
        "decision_blocks": [{"conditions": [{"stock1": "PLACEHOLDER_ASSET", "indicator1": {"type": "SMA", "params": [10]}, "operator": "<", "comparison_type": "indicator", "stock2": "PLACEHOLDER_ASSET", "indicator2": {"type": "SMA", "params": [20]}}], "actions": {"PLACEHOLDER_ASSET": "Acheter"}}]
    },
    ('Acheter', 'Lorsque le prix augmente'): {
        "name": "Achat sur Hausse de Prix (SMA)",
        "initial_capital": 100000, "allocation_pct": 10, "transaction_cost": 1, "stop_loss_pct": 5, "take_profit_pct": 10,
        "decision_blocks": [{"conditions": [{"stock1": "PLACEHOLDER_ASSET", "indicator1": {"type": "SMA", "params": [10]}, "operator": ">", "comparison_type": "indicator", "stock2": "PLACEHOLDER_ASSET", "indicator2": {"type": "SMA", "params": [20]}}], "actions": {"PLACEHOLDER_ASSET": "Acheter"}}]
    },
    ('Acheter', 'Lorsque le prix augmente après une baisse'): {
        "name": "Achat sur Rebond (RSI)",
        "initial_capital": 100000, "allocation_pct": 15, "transaction_cost": 1, "stop_loss_pct": 8, "take_profit_pct": 12,
        "decision_blocks": [{"conditions": [{"stock1": "PLACEHOLDER_ASSET", "indicator1": {"type": "RSI", "params": [14]}, "operator": ">", "comparison_type": "value", "comparison_value": 30}], "actions": {"PLACEHOLDER_ASSET": "Acheter"}}]
    },
    ('Acheter', 'Lorsque la volatilité augmente'): {
        "name": "Achat sur Eruption de Volatilité (BB)",
        "initial_capital": 100000, "allocation_pct": 12, "transaction_cost": 1, "stop_loss_pct": 6, "take_profit_pct": 15,
        "decision_blocks": [{"conditions": [{"stock1": "PLACEHOLDER_ASSET", "indicator1": {"type": "PRICE", "params": []}, "operator": ">", "comparison_type": "indicator", "stock2": "PLACEHOLDER_ASSET", "indicator2": {"type": "BBAND_UPPER", "params": [20, 2]}}], "actions": {"PLACEHOLDER_ASSET": "Acheter"}}]
    },
    ('Acheter', 'Un peu tous les mois'): {
        "name": "Achat Périodique (DCA)",
        "initial_capital": 100000, "allocation_pct": 5, "transaction_cost": 1, "stop_loss_pct": 0, "take_profit_pct": 0,
        "decision_blocks": [{
            "conditions": [{
                "stock1": "PLACEHOLDER_ASSET",
                "indicator1": {"type": "DCA", "params": [30]},
                "operator": "==",
                "comparison_type": "value",
                "comparison_value": 1
            }],
            "actions": {"PLACEHOLDER_ASSET": "Acheter"}
        }]
    },

    # --- VENDRE ---
    ('Vendre', 'Lorsque le prix baisse'): {
        "name": "Vente sur Baisse de Prix (SMA)",
        "initial_capital": 100000, "allocation_pct": 10, "transaction_cost": 1, "stop_loss_pct": 5, "take_profit_pct": 10,
        "decision_blocks": [{"conditions": [{"stock1": "PLACEHOLDER_ASSET", "indicator1": {"type": "SMA", "params": [10]}, "operator": "<", "comparison_type": "indicator", "stock2": "PLACEHOLDER_ASSET", "indicator2": {"type": "SMA", "params": [20]}}], "actions": {"PLACEHOLDER_ASSET": "Vendre"}}]
    },
    ('Vendre', 'Lorsque le prix augmente'): {
        "name": "Vente sur Hausse de Prix (SMA)",
        "initial_capital": 100000, "allocation_pct": 10, "transaction_cost": 1, "stop_loss_pct": 5, "take_profit_pct": 10,
        "decision_blocks": [{"conditions": [{"stock1": "PLACEHOLDER_ASSET", "indicator1": {"type": "SMA", "params": [10]}, "operator": ">", "comparison_type": "indicator", "stock2": "PLACEHOLDER_ASSET", "indicator2": {"type": "SMA", "params": [20]}}], "actions": {"PLACEHOLDER_ASSET": "Vendre"}}]
    },
    ('Vendre', 'Lorsque le prix augmente après une baisse'): {
        "name": "Vente sur Pic (RSI)",
        "initial_capital": 100000, "allocation_pct": 15, "transaction_cost": 1, "stop_loss_pct": 8, "take_profit_pct": 12,
        "decision_blocks": [{"conditions": [{"stock1": "PLACEHOLDER_ASSET", "indicator1": {"type": "RSI", "params": [14]}, "operator": "<", "comparison_type": "value", "comparison_value": 70}], "actions": {"PLACEHOLDER_ASSET": "Vendre"}}]
    },
    ('Vendre', 'Lorsque la volatilité augmente'): {
        "name": "Vente sur Eruption de Volatilité (BB)",
        "initial_capital": 100000, "allocation_pct": 12, "transaction_cost": 1, "stop_loss_pct": 6, "take_profit_pct": 15,
        "decision_blocks": [{"conditions": [{"stock1": "PLACEHOLDER_ASSET", "indicator1": {"type": "PRICE", "params": []}, "operator": ">", "comparison_type": "indicator", "stock2": "PLACEHOLDER_ASSET", "indicator2": {"type": "BBAND_UPPER", "params": [20, 2]}}], "actions": {"PLACEHOLDER_ASSET": "Vendre"}}]
    },
    ('Vendre', 'Un peu tous les mois'): {
        "name": "Vente Périodique (DCA)",
        "initial_capital": 100000, "allocation_pct": 10, "transaction_cost": 1, "stop_loss_pct": 0, "take_profit_pct": 0,
        "decision_blocks": [{
            "conditions": [{
                "stock1": "PLACEHOLDER_ASSET",
                "indicator1": {"type": "DCA", "params": [30]},
                "operator": "==",
                "comparison_type": "value",
                "comparison_value": 1
            }],
            "actions": {"PLACEHOLDER_ASSET": "Vendre"}
        }]
    }
}

indicator_functions = {
    "SMA": lambda df, params: df['Close'].rolling(params[0]).mean(),
    "EMA": lambda df, params: df['Close'].ewm(span=params[0]).mean(),
    "RSI": lambda df, params: 100 - (100 / (1 + df['Return'].rolling(params[0]).mean() / df['Return'].rolling(params[0]).std())),
    "Volatility": lambda df, params: df['Return'].rolling(params[0]).std(),
    "Volume": lambda df, params: df['Volume'].rolling(params[0]).mean(),
    "MACD": lambda df, params: df['Close'].ewm(span=params[0]).mean() - df['Close'].ewm(span=params[1]).mean(),
    "BollingerHigh": lambda df, params: df['Close'].rolling(params[0]).mean() + (df['Close'].rolling(params[0]).std() * params[1]),
    "BollingerLow": lambda df, params: df['Close'].rolling(params[0]).mean() - (df['Close'].rolling(params[0]).std() * params[1])
}

operators = ['<', '>', '==', '<=', '>=']


COLORS = {
    'background': 'var(--bg-primary)',
    'card_background': 'var(--bg-secondary)', 
    'header': 'var(--card-header-bg)',
    'success': 'var(--success-magenta)',
    'warning': 'var(--warning-orange)',
    'danger': 'var(--danger-cyan)',
    'buy': 'var(--success-magenta)',
    'sell': 'var(--danger-cyan)',
    'neutral': 'var(--neutral-purple)',
    'text': 'var(--text-primary)',
    'text_secondary': 'var(--text-secondary)',
    'accent': 'var(--accent-blue)',
    'dropdown_bg': 'var(--bg-card)',
    'dropdown_hover': 'var(--border-color)',
    'dropdown_text': 'var(--text-primary)'
}

CARD_STYLE = {
    'backgroundColor': 'var(--card-bg)',
    'borderRadius': 'var(--card-radius)',
    'boxShadow': 'var(--card-shadow)',
    'marginBottom': '24px',
    'border': '1px solid var(--card-border)'
}

CARD_HEADER_STYLE = {
    'background': 'var(--card-header-bg)',
    'color': 'var(--text-primary)',
    'fontWeight': 'bold',
    'borderTopLeftRadius': 'var(--card-radius)',
    'borderTopRightRadius': 'var(--card-radius)',
    'padding': '12px 15px'
}

CARD_BODY_STYLE = {
    'padding': '15px 20px'
}

INPUT_STYLE = {
    'backgroundColor': 'var(--input-bg)',
    'borderColor': 'var(--input-border)',
    'color': 'var(--text-primary)',
    'borderRadius': 'var(--input-radius)'
}

BUTTON_STYLE = {
    'borderRadius': 'var(--button-radius)',
    'fontWeight': 'bold',
    'boxShadow': 'var(--button-shadow)'
}

DROPDOWN_STYLE = {
    'backgroundColor': 'var(--input-bg)',
    'color': 'var(--text-primary)',
    'borderColor': 'var(--input-border)',
    'borderRadius': 'var(--input-radius)'
}

# Constantes
MAX_BLOCKS = 5
MAX_CONDITIONS = 5

FIREBASE_API_KEY = "AIzaSyCqSixDgx_6PBRYVm2F_YVWwdyf6WShuzk" 

STYLE_MAP = {
    'actions_cac40': {'color': '#3498db', 'icon': 'fas fa-chart-line'},
    'actions_us': {'color': '#e74c3c', 'icon': 'fas fa-flag-usa'},
    'crypto': {'color': '#f39c12', 'icon': 'fab fa-bitcoin'},
    'forex': {'color': '#2ecc71', 'icon': 'fas fa-dollar-sign'},
    'etfs': {'color': '#9b59b6', 'icon': 'fas fa-layer-group'},
    'fonds': {'color': '#1abc9c', 'icon': 'fas fa-university'}
}