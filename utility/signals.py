import pandas as pd
from indicators import calculate_indicator


def check_condition_crossover_with_tolerance(data, condition, date_idx, block_index, condition_index, tolerance=0.001):
    """
    Version avec tolérance pour éviter les faux crossovers dus au bruit
    """
    # Calculer les valeurs actuelles et précédentes
    current_state = check_condition(data, condition, date_idx)
    
    if date_idx == 0:
        return False
    
    previous_state = check_condition(data, condition, date_idx - 1)
    
    # Crossover simple
    if not previous_state and current_state:
        # Vérifier la "force" du crossover pour éviter les faux signaux
        if condition['comparison_type'] == 'indicator':
            # Calculer la différence entre les indicateurs
            stock1 = condition['stock1']
            stock2 = condition['stock2']
            
            ind1_type = condition['indicator1']['type']
            ind1_params = condition['indicator1']['params']
            ind2_type = condition['indicator2']['type']
            ind2_params = condition['indicator2']['params']
            
            try:
                # value1_current = self.calculate_indicator(stock1, ind1_type, ind1_params, date_idx)
                # value2_current = self.calculate_indicator(stock2, ind2_type, ind2_params, date_idx)

                value1_current = calculate_indicator(data, stock1, ind1_type, ind1_params, date_idx)
                value2_current = calculate_indicator(data, stock2, ind2_type, ind2_params, date_idx)
                
                # Calculer la différence relative - A VERIFIER 
                diff_pct = abs((value1_current - value2_current) / value2_current)
                
                # Crossover valide seulement si la différence est significative
                if diff_pct >= tolerance:
                    print(f"🔄 CROSSOVER CONFIRMÉ - Différence: {diff_pct:.4f} > {tolerance}")
                    return True
                else:
                    print(f"❌ Crossover ignoré - Différence trop faible: {diff_pct:.4f}")
                    return False
                    
            except Exception as e:
                print(f"Erreur calcul tolérance: {e}")
                return True  # Fallback au crossover simple
        
        return True  # Pour les comparaisons avec valeurs fixes
    
    return False

def check_condition(data, condition, date_idx):
    """
    Vérifie si une condition est remplie à une date donnée
    (Version existante inchangée)
    """
    if 'comparison_type' not in condition:
        condition['comparison_type'] = 'indicator'
    
    comp_type = condition['comparison_type']
    stock1 = condition['stock1']
    operator = condition['operator']
    
    # Calculer la valeur de l'indicateur 1
    ind_type1 = condition['indicator1']['type']
    params1 = condition['indicator1']['params'] if 'params' in condition['indicator1'] else []
    
    try:
        # value1 = self.calculate_indicator(stock1, ind_type1, params1, date_idx)
        value1 = calculate_indicator(data, stock1, ind_type1, params1, date_idx)
    except Exception as e:
        print(f"Erreur lors du calcul de l'indicateur 1 ({ind_type1}) pour {stock1}: {e}")
        return False
    
    # Vérifier le type de comparaison
    if comp_type == 'indicator':
        stock2 = condition['stock2']
        ind_type2 = condition['indicator2']['type']
        params2 = condition['indicator2']['params'] if 'params' in condition['indicator2'] else []
        
        try:
            # value2 = self.calculate_indicator(stock2, ind_type2, params2, date_idx)
            value2 = calculate_indicator(data, stock2, ind_type2, params2, date_idx)
        except Exception as e:
            print(f"Erreur lors du calcul de l'indicateur 2 ({ind_type2}) pour {stock2}: {e}")
            return False
    elif comp_type == 'value':
        value2 = condition['comparison_value']
    else:
        raise ValueError(f"Type de comparaison non pris en charge: {comp_type}")
    
    # Vérifier si la condition est remplie
    if operator == ">":
        return value1 > value2
    elif operator == "<":
        return value1 < value2
    elif operator == "==":
        return value1 == value2
    elif operator == ">=":
        return value1 >= value2
    elif operator == "<=":
        return value1 <= value2
    elif operator == "!=":
        return value1 != value2
    else:
        raise ValueError(f"Opérateur non pris en charge: {operator}")
    

def get_indicator_series(asset_data, indicator_name, indicator_params):
    """
    Retourne la série de données pour un indicateur.
    - Si le nom de l'indicateur correspond à une colonne dans les données de l'actif,
      utilise cette colonne (indicateur pré-calculé).
    - Sinon, calcule l'indicateur à la volée.
    """
    
    # Cas 1 : L'indicateur est pré-calculé et existe comme colonne dans le CSV
    if indicator_name in asset_data.columns:
        print(f"INFO: Utilisation de l'indicateur pré-calculé depuis la colonne : '{indicator_name}'")
        return asset_data[indicator_name]

    # Cas 2 : L'indicateur doit être calculé à la volée
    else:
        print(f"INFO: Calcul de l'indicateur standard : '{indicator_name}' avec les paramètres {indicator_params}")
        
        # C'est ici que vous appelez vos fonctions de calcul existantes.
        # L'exemple ci-dessous est une illustration. Adaptez-le avec VOS propres fonctions.
        
        if indicator_name.upper() == 'SMA':
            # return calculate_sma(asset_data['Close'], period=indicator_params[0])
            return asset_data['Close'].rolling(window=indicator_params[0]).mean()
            
        elif indicator_name.upper() == 'RSI':
            # return calculate_rsi(asset_data['Close'], period=indicator_params[0])
            # (Exemple de calcul RSI simplifié)
            delta = asset_data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=indicator_params[0]).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=indicator_params[0]).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
            
        elif indicator_name.upper() == 'PRICE':
            return asset_data['Close']
            
        # Ajoutez ici d'autres 'elif' pour tous vos indicateurs standards (EMA, BBAND, etc.)
        
        else:
            # Si l'indicateur n'est ni dans les colonnes, ni calculable, on lève une erreur.
            raise ValueError(f"Indicateur inconnu ou non calculable : '{indicator_name}'")