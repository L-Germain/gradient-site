"""
Module d'export PDF professionnel pour Gradient Systems
Génère un rapport complet avec tous les graphiques et métriques
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, Image, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import plotly.io as pio
import io
from datetime import datetime
from PIL import Image as PILImage


class PDFExporter:
    """Classe pour générer des PDFs professionnels des backtests"""
    
    # Couleurs du site Gradient Systems - MODE CLAIR (LIGHT MODE PRO)
    COLOR_BG = colors.HexColor('#FFFFFF')
    COLOR_PRIMARY = colors.HexColor('#0066ff')
    COLOR_ACCENT = colors.HexColor('#00f2ff')
    
    # Texte sombre pour fond clair
    COLOR_TEXT = colors.HexColor('#050a14')
    COLOR_TEXT_MUTED = colors.HexColor('#64748b')
    
    # Grille claire
    COLOR_GRID = colors.HexColor('#e2e8f0') # Slate-200
    COLOR_ROW_EVEN = colors.HexColor('#f8fafc') # Slate-50
    COLOR_ROW_ODD = colors.HexColor('#FFFFFF')
    
    # Couleurs Spécifiques (Pro Gradients simulated flat for PDF text)
    COLOR_GAIN = colors.HexColor('#00bfa5') # Teal/Mint Darker for text readability on white
    COLOR_LOSS = colors.HexColor('#d50000') # Deep Red for text readability

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configure les styles personnalisés"""
        # Titre principal (Style Gradient System)
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=self.COLOR_ACCENT,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Sous-titre
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=16,
            textColor=self.COLOR_TEXT_MUTED,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Section heading
        self.section_style = ParagraphStyle(
            'SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=self.COLOR_PRIMARY,
            spaceAfter=15,
            spaceBefore=15,
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderColor=self.COLOR_PRIMARY,
            borderPadding=5
        )
        
        # Sous-section
        self.subsection_style = ParagraphStyle(
            'SubsectionHeading',
            parent=self.styles['Heading3'],
            fontSize=13,
            textColor=self.COLOR_ACCENT,
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        # Normal Text Overrides
        self.styles['Normal'].textColor = self.COLOR_TEXT
        self.styles['Italic'].textColor = self.COLOR_TEXT_MUTED
    
    def _draw_background(self, canvas, doc):
        """Dessine le fond clair avec filigrane subtil"""
        canvas.saveState()
        canvas.setFillColor(self.COLOR_BG)
        canvas.rect(0, 0, A4[0], A4[1], fill=True, stroke=False)
        
        # Filigrane léger (Blob simulation très subtile en mode clair)
        # Blob 1 (Haut Gauche - Bleu Primary - Très transparent)
        cx1, cy1 = 0, A4[1]
        max_r1 = 15*cm
        steps = 20
        for i in range(steps):
            r = max_r1 * (1 - i/steps)
            alpha = 0.005 * (i/steps) # Très subtil
            color = self.COLOR_PRIMARY
            canvas.setFillColor(color, alpha=alpha)
            canvas.circle(cx1, cy1, r, stroke=False, fill=True)

        canvas.restoreState()

    def _on_page(self, canvas, doc):
        """Callback pour chaque page"""
        self._draw_background(canvas, doc)
        self._create_header(canvas, doc)
        self._create_footer(canvas, doc)

    def _create_header(self, canvas, doc):
        """Crée le header de chaque page"""
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(self.COLOR_TEXT_MUTED)
        canvas.drawString(2*cm, A4[1] - 1.5*cm, "Gradient Systems - Rapport de Backtest")
        canvas.drawRightString(A4[0] - 2*cm, A4[1] - 1.5*cm, 
                              datetime.now().strftime('%d/%m/%Y %H:%M'))
        canvas.setStrokeColor(self.COLOR_GRID)
        canvas.line(2*cm, A4[1] - 1.7*cm, A4[0] - 2*cm, A4[1] - 1.7*cm)
        canvas.restoreState()
    
    def _create_footer(self, canvas, doc):
        """Crée le footer de chaque page"""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(self.COLOR_TEXT_MUTED)
        canvas.setStrokeColor(self.COLOR_GRID)
        canvas.line(2*cm, 1.5*cm, A4[0] - 2*cm, 1.5*cm)
        canvas.drawCentredString(A4[0] / 2, 1*cm, f"Page {doc.page}")
        canvas.restoreState()
    
    def _add_cover_page(self, story, strategy_name):
        """Ajoute une page de couverture"""
        story.append(Spacer(1, 6*cm))
        
        # Logo / Titre principal
        story.append(Paragraph("GRADIENT SYSTEMS", self.title_style))
        story.append(Spacer(1, 1*cm))
        
        # Titre du rapport
        story.append(Paragraph("RAPPORT DE BACKTEST", self.subtitle_style))
        story.append(Spacer(1, 2*cm))
        
        # Nom de la stratégie
        strategy_style = ParagraphStyle(
            'StrategyName',
            parent=self.styles['Normal'],
            fontSize=20,
            textColor=colors.HexColor('#2196F3'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph(strategy_name, strategy_style))
        story.append(Spacer(1, 4*cm))
        
        # Date de génération
        date_style = ParagraphStyle(
            'DateStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        story.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", 
            date_style
        ))
        
        story.append(PageBreak())
    
    def _add_parameters_section(self, story, strategy_data):
        """Ajoute la section des paramètres"""
        story.append(Paragraph("PARAMÈTRES DE LA STRATÉGIE", self.section_style))
        
        # Informations générales
        story.append(Paragraph("Informations Générales", self.subsection_style))
        
        params_data = [
            ['Paramètre', 'Valeur'],
            ['Nom de la stratégie', strategy_data.get('name', 'Sans nom')],
            ['Capital initial', f"{strategy_data.get('initial_capital', 0):,.2f} €"],
            ['Allocation par trade', f"{strategy_data.get('allocation_pct', 0)}%"],
            ['Frais de transaction', f"{strategy_data.get('transaction_cost', 0):.2f} €"],
        ]
        
        params_table = Table(params_data, colWidths=[9*cm, 7*cm])
        params_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLOR_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.COLOR_TEXT),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), self.COLOR_BG),
            ('GRID', (0, 0), (-1, -1), 1, self.COLOR_GRID),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.COLOR_ROW_EVEN, self.COLOR_ROW_ODD]),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.COLOR_TEXT),
        ]))
        story.append(params_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Gestion du risque
        story.append(Paragraph("Gestion du Risque", self.subsection_style))
        
        risk_data = [
            ['Paramètre', 'Valeur'],
            ['Stop-Loss', f"{strategy_data.get('stop_loss_pct', 0)}%"],
            ['Take-Profit', f"{strategy_data.get('take_profit_pct', 0)}%"],
        ]
        
        risk_table = Table(risk_data, colWidths=[9*cm, 7*cm])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLOR_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.COLOR_TEXT),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, self.COLOR_GRID),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.COLOR_ROW_EVEN, self.COLOR_ROW_ODD]),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.COLOR_TEXT),
        ]))
        story.append(risk_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Période d'analyse
        story.append(Paragraph("Période d'Analyse", self.subsection_style))
        
        date_range = strategy_data.get('date_range', {})
        period_data = [
            ['Type', 'Date'],
            ['Date de début', date_range.get('start', 'N/A')],
            ['Date de fin', date_range.get('end', 'N/A')],
        ]
        
        period_table = Table(period_data, colWidths=[9*cm, 7*cm])
        period_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLOR_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.COLOR_TEXT),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, self.COLOR_GRID),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.COLOR_ROW_EVEN, self.COLOR_ROW_ODD]),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.COLOR_TEXT),
        ]))
        story.append(period_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Actifs
        story.append(Paragraph("Actifs Traités", self.subsection_style))
        selected_stocks = strategy_data.get('selected_stocks', [])
        
        if selected_stocks:
            # Diviser en lignes de 4 actifs max
            actifs_rows = [['Actifs Sélectionnés']]
            for i in range(0, len(selected_stocks), 4):
                chunk = selected_stocks[i:i+4]
                actifs_rows.append([', '.join(chunk)])
            
            actifs_table = Table(actifs_rows, colWidths=[16*cm])
            actifs_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), self.COLOR_PRIMARY),
                ('TEXTCOLOR', (0, 0), (0, 0), self.COLOR_TEXT),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (0, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, self.COLOR_GRID),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.COLOR_ROW_ODD]),
                ('TEXTCOLOR', (0, 1), (-1, -1), self.COLOR_TEXT),
            ]))
            story.append(actifs_table)
        else:
            story.append(Paragraph("Aucun actif sélectionné", self.styles['Normal']))
        
        story.append(PageBreak())
    
    def _add_metrics_section(self, story, metrics):
        """Ajoute la section des métriques de performance"""
        story.append(Paragraph("MÉTRIQUES DE PERFORMANCE", self.section_style))
        
        # Résumé P&L en grand (Utilisation des couleurs Pro)
        pnl = metrics.get('total_pnl', 0)
        pnl_color = self.COLOR_GAIN if pnl >= 0 else self.COLOR_LOSS
        
        pnl_style = ParagraphStyle(
            'PnLStyle',
            parent=self.styles['Normal'],
            fontSize=32,
            textColor=pnl_color,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=20
        )
        
        story.append(Paragraph(f"P&L Total: {pnl:,.2f} €", pnl_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Tableau des métriques principales
        metrics_data = [
            ['Métrique', 'Valeur', 'Interprétation'],
            ['Capital Initial', f"{metrics.get('initial_capital', 0):,.2f} €", 'Montant de départ'],
            ['Capital Final', f"{metrics.get('final_capital', 0):,.2f} €", 'Valeur finale du portefeuille'],
            ['Rendement Total', f"{metrics.get('total_return', 0):.2f}%", 'Performance brute'],
            ['Rendement Annualisé', f"{metrics.get('annualized_return', 0):.2f}%", 'Performance ramenée à l\'année'],
            ['Drawdown Maximum', f"{metrics.get('max_drawdown', 0):.2f}%", 'Plus grosse perte temporaire'],
            ['Ratio de Sharpe', f"{metrics.get('sharpe_ratio', 0):.2f}", '>1 = Bon, >2 = Excellent'],
            ['Nombre de Trades', f"{metrics.get('num_trades', 0)}", 'Total d\'opérations'],
            ['% Trades Gagnants', f"{metrics.get('win_rate', 0):.2f}%", 'Taux de réussite'],
            ['Profit Moyen/Trade', f"{metrics.get('avg_profit_per_trade', 0):.2f} €", 'Gain moyen par opération'],
            ['Profit Factor', f"{metrics.get('profit_factor', 0):.2f}", '>1 = Rentable, >2 = Excellent'],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[6*cm, 4*cm, 6*cm])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLOR_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.COLOR_TEXT),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.COLOR_GRID),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.COLOR_ROW_EVEN, self.COLOR_ROW_ODD]),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.COLOR_TEXT),
        ]))
        story.append(metrics_table)
        
        story.append(PageBreak())
    
    def _plotly_to_image(self, fig, width=1200, height=600):
        """Convertit une figure Plotly en image PIL"""
        try:
            # Assurez-vous que le template est appliqué à la figure avant cet appel si nécessaire
            img_bytes = pio.to_image(fig, format='png', width=width, height=height)
            return PILImage.open(io.BytesIO(img_bytes))
        except Exception as e:
            print(f"Erreur conversion Plotly: {e}")
            return None
    
    def _add_charts_section(self, story, figures):
        """Ajoute la section des graphiques"""
        story.append(Paragraph("GRAPHIQUES D'ANALYSE", self.section_style))
        
        # Liste des graphiques à inclure
        charts = [
            ('equity', 'Courbe d\'Équité', 'Évolution du capital dans le temps'),
            ('drawdown', 'Drawdown', 'Perte depuis le dernier pic'),
        ]
        
        for fig_key, title, description in charts:
            if fig_key in figures and figures[fig_key]:
                story.append(Paragraph(title, self.subsection_style))
                story.append(Paragraph(description, self.styles['Italic']))
                story.append(Spacer(1, 0.3*cm))
                
                try:
                    # Convertir Plotly en image
                    img = self._plotly_to_image(figures[fig_key], width=1400, height=700)
                    
                    if img:
                        # Sauvegarder en buffer
                        img_buffer = io.BytesIO()
                        img.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        
                        # Ajouter au PDF
                        story.append(Image(img_buffer, width=17*cm, height=8.5*cm))
                        story.append(Spacer(1, 0.5*cm))
                    else:
                        story.append(Paragraph("Graphique non disponible", self.styles['Italic']))
                        story.append(Spacer(1, 0.5*cm))
                        
                except Exception as e:
                    print(f"Erreur ajout graphique {fig_key}: {e}")
                    story.append(Paragraph(f"Erreur: Graphique non disponible", self.styles['Italic']))
                    story.append(Spacer(1, 0.5*cm))
        
        # Graphiques par actif (limiter à 3 premiers)
        symbol_charts = [k for k in figures.keys() if k not in ['equity', 'drawdown', 'transactions']]
        
        if symbol_charts:
            story.append(PageBreak())
            story.append(Paragraph("GRAPHIQUES PAR ACTIF", self.section_style))
            
            for i, symbol_key in enumerate(symbol_charts[:3]):  # Max 3 actifs
                if figures[symbol_key]:
                    symbol = symbol_key.split('_')[-1] if '_' in symbol_key else symbol_key
                    story.append(Paragraph(f"Prix et Signaux - {symbol}", self.subsection_style))
                    
                    try:
                        img = self._plotly_to_image(figures[symbol_key], width=1400, height=700)
                        
                        if img:
                            img_buffer = io.BytesIO()
                            img.save(img_buffer, format='PNG')
                            img_buffer.seek(0)
                            
                            story.append(Image(img_buffer, width=17*cm, height=8.5*cm))
                            story.append(Spacer(1, 0.5*cm))
                    except Exception as e:
                        print(f"Erreur graphique actif {symbol}: {e}")
        
        story.append(PageBreak())
    
    def _add_transactions_section(self, story, transactions):
        """Ajoute la section du journal des transactions"""
        story.append(Paragraph("JOURNAL DES TRANSACTIONS", self.section_style))
        
        if not transactions or len(transactions) == 0:
            story.append(Paragraph("Aucune transaction enregistrée", self.styles['Normal']))
            return
        
        # Limiter à 30 transactions
        trans_subset = transactions[:30]
        
        story.append(Paragraph(
            f"Affichage des {len(trans_subset)} premières transactions sur {len(transactions)} au total",
            self.styles['Italic']
        ))
        story.append(Spacer(1, 0.3*cm))
        
        # Créer le tableau
        trans_data = [['Date', 'Type', 'Symbole', 'Prix', 'Qté', 'P&L (€)', 'P&L (%)']]
        
        # Styles row-by-row
        table_styles = [
            ('BACKGROUND', (0, 0), (-1, 0), self.COLOR_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), # Header toujours blanc sur bleu
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, self.COLOR_GRID),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.COLOR_ROW_EVEN, self.COLOR_ROW_ODD]),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.COLOR_TEXT),
        ]

        for i, t in enumerate(trans_subset):
            # Formater les données
            pnl_val = t.get('pnl', 0)
            pnl_pct_val = t.get('pnl_pct', 0)
            
            row_data = [
                str(t.get('date', 'N/A'))[:10],
                str(t.get('type', 'N/A')),
                str(t.get('symbol', 'N/A')),
                f"{t.get('price', 0):.2f}",
                f"{t.get('shares', 0):.2f}",
                f"{pnl_val:.2f}",
                f"{pnl_pct_val:.2f}%" if t.get('pnl_pct') is not None else 'N/A'
            ]
            trans_data.append(row_data)
            
            # Coloration conditionnelle (Lignes 1-indexed dans trans_data)
            row_idx = i + 1
            if pnl_val > 0:
                table_styles.append(('TEXTCOLOR', (5, row_idx), (6, row_idx), self.COLOR_GAIN))
            elif pnl_val < 0:
                table_styles.append(('TEXTCOLOR', (5, row_idx), (6, row_idx), self.COLOR_LOSS))

        trans_table = Table(trans_data, colWidths=[2.2*cm, 2.2*cm, 2.2*cm, 2*cm, 2*cm, 2.5*cm, 2.5*cm])
        trans_table.setStyle(TableStyle(table_styles))
        story.append(trans_table)
    
    def generate_pdf(self, strategy_data, metrics, figures, transactions):
        """
        Génère le PDF complet
        
        Args:
            strategy_data: Dict avec les paramètres de la stratégie
            metrics: Dict avec les métriques de performance
            figures: Dict avec les figures Plotly (clés: 'equity', 'drawdown', etc.)
            transactions: Liste des transactions
        
        Returns:
            bytes: Contenu du PDF
        """
        buffer = io.BytesIO()
        
        # Créer le document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=2.5*cm,
            bottomMargin=2*cm,
            leftMargin=2*cm,
            rightMargin=2*cm
        )
        
        story = []
        
        # Ajouter les sections
        strategy_name = strategy_data.get('name', 'Sans nom')
        self._add_cover_page(story, strategy_name)
        self._add_parameters_section(story, strategy_data)
        
        if metrics:
            self._add_metrics_section(story, metrics)
        
        if figures:
            self._add_charts_section(story, figures)
        
        if transactions:
            self._add_transactions_section(story, transactions)
        
        # Construire le PDF
        doc.build(story, onFirstPage=self._on_page, onLaterPages=self._on_page)
        
        buffer.seek(0)
        return buffer.getvalue()


# Fonction simple d'export
def export_backtest_to_pdf(strategy_data, metrics, figures, transactions):
    """
    Fonction utilitaire pour exporter un backtest en PDF
    
    Args:
        strategy_data: Données de la stratégie
        metrics: Métriques de performance
        figures: Graphiques Plotly
        transactions: Liste des transactions
    
    Returns:
        bytes: Contenu du PDF
    """
    exporter = PDFExporter()
    return exporter.generate_pdf(strategy_data, metrics, figures, transactions)
