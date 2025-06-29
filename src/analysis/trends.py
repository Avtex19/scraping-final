"""
Trend analysis module for scraped e-commerce data.
Provides time-based trend analysis and comparative analysis across sources.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any
import logging
from datetime import datetime
import sqlite3
from pathlib import Path


class TrendAnalyzer:
    """
    Advanced trend analysis for e-commerce data.
    Analyzes price trends, availability patterns, and cross-source comparisons.
    """
    
    def __init__(self, db_path: str = "scraped_data.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.data = None
        
    def load_data(self) -> pd.DataFrame:
        """Load data with temporal processing for trend analysis."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT 
                p.*,
                j.search_term as job_search_term,
                j.created_at as job_created_at
            FROM products p
            LEFT JOIN jobs j ON p.job_id = j.job_id
            WHERE p.name IS NOT NULL
            ORDER BY p.scrape_time
            """
            self.data = pd.read_sql_query(query, conn)
            conn.close()
            
            self.data['price_numeric'] = pd.to_numeric(
                self.data['price'].astype(str).str.replace(r'[£$,]', '', regex=True),
                errors='coerce'
            )
            self.data['scrape_time'] = pd.to_datetime(self.data['scrape_time'], errors='coerce')
            self.data['scrape_date'] = self.data['scrape_time'].dt.date
            self.data['scrape_hour'] = self.data['scrape_time'].dt.hour
            
            self.logger.info(f"Loaded {len(self.data)} records for trend analysis")
            return self.data
            
        except Exception as e:
            self.logger.error(f"Error loading data for trends: {e}")
            return pd.DataFrame()
    
    def analyze_price_trends(self) -> Dict[str, Any]:
        """
        Analyze price trends over time, including daily averages and patterns.
        """
        if self.data is None or self.data.empty:
            self.load_data()
        
        trends = {
            'overall_trends': {},
            'trends_by_source': {},
            'temporal_patterns': {}
        }
        
        daily_prices = self.data.groupby('scrape_date')['price_numeric'].agg([
            'count', 'mean', 'median', 'std', 'min', 'max'
        ]).reset_index()
        
        if len(daily_prices) > 1:
            price_correlation = daily_prices['mean'].corr(range(len(daily_prices)))
            
            trends['overall_trends'] = {
                'total_days': len(daily_prices),
                'avg_daily_products': float(daily_prices['count'].mean()),
                'price_trend_correlation': float(price_correlation),
                'trend_direction': 'increasing' if price_correlation > 0.1 else 'decreasing' if price_correlation < -0.1 else 'stable',
                'daily_averages': daily_prices.to_dict('records')
            }
        
        for source in self.data['search_term'].unique():
            if pd.notna(source):
                source_data = self.data[self.data['search_term'] == source]
                source_daily = source_data.groupby('scrape_date')['price_numeric'].agg([
                    'count', 'mean', 'median'
                ]).reset_index()
                
                if len(source_daily) > 1:
                    source_correlation = source_daily['mean'].corr(range(len(source_daily)))
                    
                    trends['trends_by_source'][source] = {
                        'days_tracked': len(source_daily),
                        'price_trend_correlation': float(source_correlation),
                        'trend_direction': 'increasing' if source_correlation > 0.1 else 'decreasing' if source_correlation < -0.1 else 'stable',
                        'avg_daily_products': float(source_daily['count'].mean()),
                        'price_volatility': float(source_daily['mean'].std()) if len(source_daily) > 1 else 0
                    }
        
        hourly_patterns = self.data.groupby('scrape_hour')['price_numeric'].agg([
            'count', 'mean'
        ]).reset_index()
        
        trends['temporal_patterns'] = {
            'hourly_activity': hourly_patterns.to_dict('records'),
            'peak_scraping_hour': int(hourly_patterns.loc[hourly_patterns['count'].idxmax()]['scrape_hour']),
            'price_variation_by_hour': float(hourly_patterns['mean'].std())
        }
        
        return trends
    
    def comparative_source_analysis(self) -> Dict[str, Any]:
        """
        Compare performance and characteristics across different sources.
        """
        if self.data is None or self.data.empty:
            self.load_data()
        
        comparison = {
            'source_performance': {},
            'cross_source_insights': {},
            'market_positioning': {}
        }
        
        for source in self.data['search_term'].unique():
            if pd.notna(source):
                source_data = self.data[self.data['search_term'] == source]
                source_prices = source_data['price_numeric'].dropna()
                
                comparison['source_performance'][source] = {
                    'total_products': len(source_data),
                    'products_with_prices': len(source_prices),
                    'data_completeness': len(source_prices) / len(source_data) * 100,
                    'avg_price': float(source_prices.mean()) if len(source_prices) > 0 else None,
                    'price_std': float(source_prices.std()) if len(source_prices) > 0 else None,
                    'price_range': {
                        'min': float(source_prices.min()) if len(source_prices) > 0 else None,
                        'max': float(source_prices.max()) if len(source_prices) > 0 else None
                    },
                    'unique_products': source_data['name'].nunique()
                }
        
        if len(comparison['source_performance']) > 1:
            all_prices = []
            all_sources = []
            
            for source, data in comparison['source_performance'].items():
                if data['avg_price'] is not None:
                    all_prices.append(data['avg_price'])
                    all_sources.append(source)
            
            if len(all_prices) > 1:
                price_variance = np.var(all_prices)
                cheapest_source = all_sources[np.argmin(all_prices)]
                most_expensive_source = all_sources[np.argmax(all_prices)]
                
                comparison['cross_source_insights'] = {
                    'price_variance_across_sources': float(price_variance),
                    'cheapest_source': cheapest_source,
                    'most_expensive_source': most_expensive_source,
                    'price_difference': float(max(all_prices) - min(all_prices)),
                    'coefficient_of_variation': float(np.std(all_prices) / np.mean(all_prices))
                }
        
        all_products = self.data['price_numeric'].dropna()
        if len(all_products) > 0:
            percentiles = [25, 50, 75, 90]
            price_segments = {f'p{p}': float(all_products.quantile(p/100)) for p in percentiles}
            
            for source in comparison['source_performance'].keys():
                source_data = self.data[self.data['search_term'] == source]
                source_prices = source_data['price_numeric'].dropna()
                
                if len(source_prices) > 0:
                    avg_price = source_prices.mean()
                    if avg_price <= price_segments['p25']:
                        segment = 'budget'
                    elif avg_price <= price_segments['p50']:
                        segment = 'mid-low'
                    elif avg_price <= price_segments['p75']:
                        segment = 'mid-high'
                    else:
                        segment = 'premium'
                    
                    comparison['market_positioning'][source] = {
                        'market_segment': segment,
                        'percentile_position': float((all_products < avg_price).mean() * 100)
                    }
        
        return comparison
    
    def generate_trend_visualizations(self, output_dir: str = "data_output/reports") -> List[str]:
        """
        Generate comprehensive trend visualizations.
        """
        if self.data is None or self.data.empty:
            self.load_data()
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        generated_files = []
        
        plt.style.use('seaborn-v0_8')
        
        if len(self.data) > 0:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('E-Commerce Data Trend Analysis', fontsize=16, fontweight='bold')
            
            daily_data = self.data.groupby('scrape_date')['price_numeric'].mean().reset_index()
            if len(daily_data) > 1:
                axes[0, 0].plot(daily_data['scrape_date'], daily_data['price_numeric'], marker='o')
                axes[0, 0].set_title('Average Daily Prices')
                axes[0, 0].set_xlabel('Date')
                axes[0, 0].set_ylabel('Average Price')
                axes[0, 0].tick_params(axis='x', rotation=45)
            
            sources = self.data['search_term'].unique()
            if len(sources) > 1:
                self.data.boxplot(column='price_numeric', by='search_term', ax=axes[0, 1])
                axes[0, 1].set_title('Price Distribution by Source')
                axes[0, 1].set_xlabel('Source')
                axes[0, 1].set_ylabel('Price')
            
            hourly_activity = self.data.groupby('scrape_hour').size()
            axes[1, 0].bar(hourly_activity.index, hourly_activity.values)
            axes[1, 0].set_title('Scraping Activity by Hour')
            axes[1, 0].set_xlabel('Hour of Day')
            axes[1, 0].set_ylabel('Number of Products Scraped')
            
            source_counts = self.data['search_term'].value_counts()
            axes[1, 1].pie(source_counts.values, labels=source_counts.index, autopct='%1.1f%%')
            axes[1, 1].set_title('Products Distribution by Source')
            
            plt.tight_layout()
            trend_file = Path(output_dir) / f"trend_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(trend_file, dpi=300, bbox_inches='tight')
            plt.close()
            generated_files.append(str(trend_file))
        
        if len(self.data) > 0:
            pivot_data = self.data.pivot_table(
                values='price_numeric', 
                index='search_term', 
                columns=self.data['scrape_time'].dt.date,
                aggfunc='mean'
            )
            
            if not pivot_data.empty:
                plt.figure(figsize=(12, 8))
                sns.heatmap(pivot_data, annot=True, fmt='.1f', cmap='YlOrRd')
                plt.title('Price Heatmap: Sources vs Days')
                plt.xlabel('Scrape Date')
                plt.ylabel('Source')
                plt.xticks(rotation=45)
                
                heatmap_file = Path(output_dir) / f"price_heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                plt.savefig(heatmap_file, dpi=300, bbox_inches='tight')
                plt.close()
                generated_files.append(str(heatmap_file))
        
        self.logger.info(f"Generated {len(generated_files)} trend visualization files")
        return generated_files
    
    def generate_trend_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive trend analysis report.
        """
        price_trends = self.analyze_price_trends()
        source_comparison = self.comparative_source_analysis()
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'analysis_period': {
                    'start': str(self.data['scrape_time'].min()) if self.data is not None else None,
                    'end': str(self.data['scrape_time'].max()) if self.data is not None else None
                },
                'total_records_analyzed': len(self.data) if self.data is not None else 0
            },
            'price_trends': price_trends,
            'source_comparison': source_comparison
        }
        
        return report
    
    def export_trends(self, output_dir: str = "data_output/processed") -> str:
        """Export trend analysis to JSON and Excel formats."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        report = self.generate_trend_report()
        
        import json
        json_path = Path(output_dir) / f"trend_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Trend analysis exported to {json_path}")
        return str(json_path)
    
    def analyze_trends(self) -> Dict[str, Any]:
        """
        Main method for trend analysis called by CLI.
        Combines price trends and temporal patterns.
        """
        if self.data is None or self.data.empty:
            self.load_data()
        
        price_trends = self.analyze_price_trends()
        source_comparison = self.comparative_source_analysis()
        
        temporal_trends = {}
        if self.data is not None and len(self.data) > 0:
            temporal_trends = {
                'date_range': f"{self.data['scrape_time'].min().strftime('%Y-%m-%d')} to {self.data['scrape_time'].max().strftime('%Y-%m-%d')}",
                'peak_hour': int(self.data.groupby('scrape_hour').size().idxmax()),
                'total_data_points': len(self.data),
                'days_with_data': self.data['scrape_date'].nunique()
            }
        
        return {
            'temporal_trends': temporal_trends,
            'price_trends': price_trends,
            'source_comparison': source_comparison
        }
    
    def compare_sources(self) -> Dict[str, Any]:
        """
        Main method for source comparison called by CLI.
        Returns source performance data in CLI-friendly format.
        """
        if self.data is None or self.data.empty:
            self.load_data()
        
        comparison = self.comparative_source_analysis()
        
        sources_summary = {}
        
        for source, perf in comparison.get('source_performance', {}).items():
            sources_summary[source] = {
                'total_products': perf['total_products'],
                'avg_price': perf['avg_price'],
                'data_quality_score': perf['data_completeness']
            }
        
        return sources_summary 