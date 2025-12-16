import sys
import os

# Ajouter le dossier parent au path pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utility.pdf_exporter import export_backtest_to_pdf
import pandas as pd
import plotly.graph_objects as go
import datetime

# Mock Data
strategy_data = {
    'name': 'Test Gradient StyleStrategy',
    'initial_capital': 10000,
    'allocation_pct': 20,
    'transaction_cost': 2.50,
    'stop_loss_pct': 5,
    'take_profit_pct': 10,
    'date_range': {'start': '2023-01-01', 'end': '2023-12-31'},
    'selected_stocks': ['AAPL', 'TSLA', 'MSFT', 'NVDA']
}

metrics = {
    'total_pnl': 1500.50,
    'initial_capital': 10000,
    'final_capital': 11500.50,
    'total_return': 15.01,
    'annualized_return': 15.01,
    'max_drawdown': -5.2,
    'sharpe_ratio': 1.8,
    'num_trades': 42,
    'win_rate': 65.5,
    'avg_profit_per_trade': 35.72,
    'profit_factor': 1.5
}

# Mock Chart
fig = go.Figure(data=[go.Scatter(x=[1, 2, 3, 4], y=[10, 11, 12, 13])])
fig.update_layout(title="Equity Curve Test", template="plotly_dark")

figures = {
    'equity': fig,
    'drawdown': fig,
    'AAPL_chart': fig
}

transactions = [
    {'date': '2023-01-05', 'type': 'BUY', 'symbol': 'AAPL', 'price': 150, 'shares': 10, 'pnl': 0, 'pnl_pct': 0},
    {'date': '2023-01-10', 'type': 'SELL', 'symbol': 'AAPL', 'price': 160, 'shares': 10, 'pnl': 100, 'pnl_pct': 6.66}
]

print("Generating PDF...")
try:
    pdf_bytes = export_backtest_to_pdf(strategy_data, metrics, figures, transactions)
    
    output_path = "test_report_gradient.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
    
    print(f"PDF successfully generated at: {os.path.abspath(output_path)}")
except Exception as e:
    print(f"Error generating PDF: {e}")
