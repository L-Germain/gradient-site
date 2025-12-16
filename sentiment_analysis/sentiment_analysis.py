import requests
import pandas as pd
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import nltk
from datetime import datetime, timedelta
import time
import json
from typing import List, Dict, Optional
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsSentimentAnalyzer:
    def __init__(self):
        """
        Initialise l'analyseur de sentiment d'actualités
        """
        # Télécharger les ressources NLTK nécessaires
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('vader_lexicon', quiet=True)
        except:
            logger.warning("Impossible de télécharger les ressources NLTK")
        
        # Initialiser VADER
        self.vader_analyzer = SentimentIntensityAnalyzer()
        
        # APIs gratuites disponibles
        self.news_apis = {
            'newsapi': {
                'url': 'https://newsapi.org/v2/everything',
                'key': None,  # À remplacer par votre clé API
                'limit': 100  # Limite quotidienne gratuite
            },
            'gnews': {
                'url': 'https://gnews.io/api/v4/search',
                'key': None,  # À remplacer par votre clé API
                'limit': 100
            }
        }
    
    def set_api_key(self, service: str, api_key: str):
        """
        Configure une clé API pour un service donné
        
        Args:
            service (str): 'newsapi' ou 'gnews'
            api_key (str): Clé API
        """
        if service in self.news_apis:
            self.news_apis[service]['key'] = api_key
            logger.info(f"Clé API configurée pour {service}")
        else:
            logger.error(f"Service {service} non reconnu")
    
    def fetch_news_newsapi(self, query: str = "france", language: str = "fr", 
                          days_back: int = 1) -> List[Dict]:
        """
        Récupère les actualités via NewsAPI
        
        Args:
            query (str): Terme de recherche
            language (str): Langue des articles
            days_back (int): Nombre de jours en arrière
            
        Returns:
            List[Dict]: Liste des articles
        """
        if not self.news_apis['newsapi']['key']:
            logger.error("Clé API NewsAPI non configurée")
            return []
        
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        params = {
            'q': query,
            'language': language,
            'from': from_date,
            'sortBy': 'publishedAt',
            'apiKey': self.news_apis['newsapi']['key'],
            'pageSize': 100
        }
        
        try:
            response = requests.get(self.news_apis['newsapi']['url'], params=params)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for article in data.get('articles', []):
                if article['title'] and article['description']:
                    articles.append({
                        'title': article['title'],
                        'description': article['description'],
                        'content': article.get('content', ''),
                        'url': article['url'],
                        'published_at': article['publishedAt'],
                        'source': article['source']['name']
                    })
            
            logger.info(f"Récupéré {len(articles)} articles via NewsAPI")
            return articles
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la récupération NewsAPI: {e}")
            return []
    
    def fetch_news_gnews(self, query: str = "actualités france", language: str = "fr") -> List[Dict]:
        """
        Récupère les actualités via GNews
        
        Args:
            query (str): Terme de recherche
            language (str): Langue des articles
            
        Returns:
            List[Dict]: Liste des articles
        """
        if not self.news_apis['gnews']['key']:
            logger.error("Clé API GNews non configurée")
            return []
        
        params = {
            'q': query,
            'lang': language,
            'country': 'fr',
            'max': 100,
            'apikey': self.news_apis['gnews']['key']
        }
        
        try:
            response = requests.get(self.news_apis['gnews']['url'], params=params)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for article in data.get('articles', []):
                articles.append({
                    'title': article['title'],
                    'description': article['description'],
                    'content': article.get('content', ''),
                    'url': article['url'],
                    'published_at': article['publishedAt'],
                    'source': article['source']['name']
                })
            
            logger.info(f"Récupéré {len(articles)} articles via GNews")
            return articles
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la récupération GNews: {e}")
            return []
    
    def fetch_news_rss(self, rss_urls: List[str]) -> List[Dict]:
        """
        Récupère les actualités via RSS (gratuit, sans API)
        
        Args:
            rss_urls (List[str]): Liste des URLs RSS
            
        Returns:
            List[Dict]: Liste des articles
        """
        try:
            import feedparser
        except ImportError:
            logger.error("Installez feedparser: pip install feedparser")
            return []
        
        articles = []
        
        for rss_url in rss_urls:
            try:
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries[:20]:  # Limite à 20 par flux
                    articles.append({
                        'title': entry.get('title', ''),
                        'description': entry.get('summary', ''),
                        'content': entry.get('content', [{}])[0].get('value', '') if entry.get('content') else '',
                        'url': entry.get('link', ''),
                        'published_at': entry.get('published', ''),
                        'source': feed.feed.get('title', 'RSS Feed')
                    })
                
                time.sleep(1)  # Respecter les serveurs RSS
                
            except Exception as e:
                logger.error(f"Erreur RSS pour {rss_url}: {e}")
        
        logger.info(f"Récupéré {len(articles)} articles via RSS")
        return articles
    
    def analyze_sentiment_textblob(self, text: str) -> Dict:
        """
        Analyse le sentiment avec TextBlob
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            Dict: Résultats d'analyse
        """
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Classification du sentiment
        if polarity > 0.1:
            sentiment = 'positive'
        elif polarity < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'method': 'TextBlob',
            'polarity': polarity,
            'subjectivity': subjectivity,
            'sentiment': sentiment,
            'confidence': abs(polarity)
        }
    
    def analyze_sentiment_vader(self, text: str) -> Dict:
        """
        Analyse le sentiment avec VADER
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            Dict: Résultats d'analyse
        """
        scores = self.vader_analyzer.polarity_scores(text)
        
        # Déterminer le sentiment dominant
        if scores['compound'] >= 0.05:
            sentiment = 'positive'
        elif scores['compound'] <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'method': 'VADER',
            'compound': scores['compound'],
            'positive': scores['pos'],
            'negative': scores['neg'],
            'neutral': scores['neu'],
            'sentiment': sentiment,
            'confidence': abs(scores['compound'])
        }
    
    def analyze_article_sentiment(self, article: Dict) -> Dict:
        """
        Analyse le sentiment d'un article complet
        
        Args:
            article (Dict): Article à analyser
            
        Returns:
            Dict: Article avec analyse de sentiment
        """
        # Combiner titre et description pour l'analyse
        full_text = f"{article.get('title', '')} {article.get('description', '')}"
        
        # Analyses avec les deux méthodes
        textblob_result = self.analyze_sentiment_textblob(full_text)
        vader_result = self.analyze_sentiment_vader(full_text)
        
        # Sentiment consensus
        sentiments = [textblob_result['sentiment'], vader_result['sentiment']]
        consensus_sentiment = max(set(sentiments), key=sentiments.count)
        
        # Confiance moyenne
        avg_confidence = (textblob_result['confidence'] + vader_result['confidence']) / 2
        
        # Ajouter les résultats à l'article
        article_with_sentiment = article.copy()
        article_with_sentiment.update({
            'textblob_analysis': textblob_result,
            'vader_analysis': vader_result,
            'consensus_sentiment': consensus_sentiment,
            'confidence_score': avg_confidence,
            'analysis_timestamp': datetime.now().isoformat()
        })
        
        return article_with_sentiment
    
    def process_news_batch(self, query: str = "actualités", language: str = "fr", 
                          use_rss: bool = True) -> pd.DataFrame:
        """
        Traite un lot d'actualités complètes
        
        Args:
            query (str): Terme de recherche
            language (str): Langue
            use_rss (bool): Utiliser les flux RSS gratuits
            
        Returns:
            pd.DataFrame: DataFrame avec analyses de sentiment
        """
        all_articles = []
        
        # Flux RSS français gratuits
        if use_rss:
            rss_feeds = [
                'https://www.lemonde.fr/rss/une.xml',
                'https://www.lefigaro.fr/rss/figaro_actualites.xml',
                'https://www.liberation.fr/arc/outboundfeeds/rss-all/',
                'https://www.francetvinfo.fr/titres.rss',
                'https://www.20minutes.fr/feeds/rss-actu.xml'
            ]
            rss_articles = self.fetch_news_rss(rss_feeds)
            all_articles.extend(rss_articles)
        
        # APIs payantes si configurées
        if self.news_apis['newsapi']['key']:
            newsapi_articles = self.fetch_news_newsapi(query, language)
            all_articles.extend(newsapi_articles)
        
        if self.news_apis['gnews']['key']:
            gnews_articles = self.fetch_news_gnews(query, language)
            all_articles.extend(gnews_articles)
        
        if not all_articles:
            logger.warning("Aucun article récupéré")
            return pd.DataFrame()
        
        # Supprimer les doublons par URL
        unique_articles = []
        seen_urls = set()
        for article in all_articles:
            if article['url'] not in seen_urls:
                unique_articles.append(article)
                seen_urls.add(article['url'])
        
        logger.info(f"Traitement de {len(unique_articles)} articles uniques")
        
        # Analyser le sentiment de chaque article
        analyzed_articles = []
        for i, article in enumerate(unique_articles):
            try:
                analyzed_article = self.analyze_article_sentiment(article)
                analyzed_articles.append(analyzed_article)
                
                if (i + 1) % 50 == 0:
                    logger.info(f"Analysé {i + 1}/{len(unique_articles)} articles")
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse de l'article {i}: {e}")
        
        # Créer DataFrame
        df = pd.DataFrame(analyzed_articles)
        
        if not df.empty:
            # Ajouter des colonnes pratiques pour le dashboard
            df['sentiment_score'] = df.apply(
                lambda row: row['vader_analysis']['compound'], axis=1
            )
            df['publication_date'] = pd.to_datetime(df['published_at'], errors='coerce')
            
            logger.info(f"Analyse terminée: {len(df)} articles traités")
            
            # Statistiques rapides
            sentiment_counts = df['consensus_sentiment'].value_counts()
            logger.info(f"Répartition des sentiments: {sentiment_counts.to_dict()}")
        
        return df
    
    def get_sentiment_summary(self, df: pd.DataFrame) -> Dict:
        """
        Génère un résumé des analyses de sentiment
        
        Args:
            df (pd.DataFrame): DataFrame avec les analyses
            
        Returns:
            Dict: Résumé statistique
        """
        if df.empty:
            return {}
        
        summary = {
            'total_articles': len(df),
            'sentiment_distribution': df['consensus_sentiment'].value_counts().to_dict(),
            'average_sentiment_score': df['sentiment_score'].mean(),
            'most_positive_article': df.loc[df['sentiment_score'].idxmax()]['title'] if not df.empty else None,
            'most_negative_article': df.loc[df['sentiment_score'].idxmin()]['title'] if not df.empty else None,
            'sources_count': df['source'].nunique(),
            'analysis_date': datetime.now().isoformat()
        }
        
        return summary

# Exemple d'utilisation
if __name__ == "__main__":
    # Initialiser l'analyseur
    analyzer = NewsSentimentAnalyzer()
    
    # Optionnel: configurer les clés API (payantes mais avec limites gratuites)
    # analyzer.set_api_key('newsapi', 'VOTRE_CLE_NEWSAPI')
    # analyzer.set_api_key('gnews', 'VOTRE_CLE_GNEWS')
    
    # Analyser les actualités
    print("🔍 Récupération et analyse des actualités...")
    df_news = analyzer.process_news_batch(
        query="France actualités",
        language="fr",
        use_rss=True  # Utilise les flux RSS gratuits
    )
    
    if not df_news.empty:
        # Afficher le résumé
        summary = analyzer.get_sentiment_summary(df_news)
        print("\n📊 Résumé de l'analyse:")
        print(f"Total d'articles: {summary['total_articles']}")
        print(f"Répartition: {summary['sentiment_distribution']}")
        print(f"Score moyen: {summary['average_sentiment_score']:.2f}")
        
        # Sauvegarder les résultats
        df_news.to_csv('news_sentiment_analysis.csv', index=False, encoding='utf-8')
        print("\n💾 Résultats sauvegardés dans 'news_sentiment_analysis.csv'")
        
        # Afficher quelques exemples
        print("\n📰 Exemples d'articles analysés:")
        for _, row in df_news.head(3).iterrows():
            print(f"- {row['title'][:100]}...")
            print(f"  Sentiment: {row['consensus_sentiment']} (score: {row['sentiment_score']:.2f})")
            print(f"  Source: {row['source']}")
            print()
    else:
        print("❌ Aucun article récupéré")