import pandas as pd



def print_crossover_summary(obj):
    """
    Affiche un résumé des crossovers détectés
    """
    print("\n=== RÉSUMÉ DES CROSSOVERS DÉTECTÉS ===")
    
    total_crossovers = 0
    for history_key, history in obj.condition_history.items():
        crossover_count = 0
        for i in range(1, len(history)):
            if not history[i-1] and history[i]:  # False → True
                crossover_count += 1
        
        if crossover_count > 0:
            block_idx, condition_idx = history_key.split('_')
            print(f"Bloc {block_idx}, Condition {condition_idx}: {crossover_count} crossovers")
            total_crossovers += crossover_count
    
    print(f"TOTAL: {total_crossovers} crossovers détectés")
    
    # Comparer avec le nombre d'achats
    buy_transactions = [t for t in obj.transactions if t['type'] == 'ACHAT']
    print(f"ACHATS EXÉCUTÉS: {len(buy_transactions)}")
    
    if total_crossovers > 0:
        efficiency = (len(buy_transactions) / total_crossovers) * 100
        print(f"EFFICACITÉ: {efficiency:.1f}% (achats/crossovers)")


def get_performance_metrics_table(obj):
    """
    Retourne les métriques de performance sous forme de tableau pour l'affichage
    """
    if not hasattr(obj, 'metrics'):
        return None
    
    # Formater les métriques pour le tableau
    metrics_table = pd.DataFrame([
        {"Métrique": "Capital initial", "Valeur": f"{obj.metrics['Capital initial']:,.2f} €"},
        {"Métrique": "Capital final", "Valeur": f"{obj.metrics['Capital final']:,.2f} €"},
        {"Métrique": "Rendement total", "Valeur": f"{obj.metrics['Rendement total (%)']:.2f}%"},
        {"Métrique": "Rendement annualisé", "Valeur": f"{obj.metrics['Rendement annualisé (%)']:.2f}%"},
        {"Métrique": "Drawdown maximum", "Valeur": f"{obj.metrics['Drawdown maximum (%)']:.2f}%"},
        {"Métrique": "Ratio de Sharpe", "Valeur": f"{obj.metrics['Ratio de Sharpe']:.2f}"},
        {"Métrique": "Nombre de trades", "Valeur": f"{int(obj.metrics['Nombre de trades'])}"},
        {"Métrique": "Pourcentage de trades gagnants", "Valeur": f"{obj.metrics['Pourcentage de trades gagnants (%)']:.2f}%"},
        {"Métrique": "Profit moyen par trade", "Valeur": f"{obj.metrics['Profit moyen par trade']:.2f} €"},
        {"Métrique": "Profit moyen des trades gagnants", "Valeur": f"{obj.metrics['Profit moyen des trades gagnants']:.2f} €"},
        {"Métrique": "Perte moyenne des trades perdants", "Valeur": f"{obj.metrics['Perte moyenne des trades perdants']:.2f} €"},
        {"Métrique": "Profit factor", "Valeur": f"{obj.metrics['Profit factor']:.2f}"}
    ])
    
    return metrics_table