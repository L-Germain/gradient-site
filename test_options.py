# test_specifique_ac_pa.py

import yfinance as yf

def test_options_pour_un_ticker(ticker_symbol):
    """
    Teste spécifiquement la récupération des dates d'expiration pour un ticker.
    """
    print(f"\n-------------------------------------------")
    print(f"--- Test de récupération pour : {ticker_symbol} ---")
    
    try:
        # Création de l'objet Ticker
        stock = yf.Ticker(ticker_symbol)

        # La ligne la plus importante : l'appel à .options
        expiration_dates = stock.options

        # Analyse du résultat
        if not expiration_dates:
            print(f"✅ RÉSULTAT : L'appel a réussi, mais Yahoo Finance ne retourne AUCUNE date d'expiration pour {ticker_symbol}.")
            print(f"   Valeur retournée : {expiration_dates}")
        else:
            print(f"✅ RÉSULTAT : SUCCÈS ! {len(expiration_dates)} dates d'expiration trouvées pour {ticker_symbol}.")
            print(f"   Aperçu : {expiration_dates[:3]}")

    except Exception as e:
        print(f"❌ RÉSULTAT : Une ERREUR est survenue lors de la tentative de récupération pour {ticker_symbol}.")
        print(f"   Message : {e}")
    print(f"-------------------------------------------")


# --- Point d'entrée du script ---
if __name__ == "__main__":
    print("Lancement du test spécifique pour les options du CAC 40...")
    
    # 1. Le ticker qui pose problème dans votre application
    test_options_pour_un_ticker("AC.PA")
    
    # 2. Un autre ticker du CAC 40 pour lequel les données existent
    test_options_pour_un_ticker("TTE.PA")