"""
Statistical analysis module for scraped e-commerce data.
Provides comprehensive data quality checks, statistical summaries, and distributions.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from datetime import datetime
import sqlite3
from pathlib import Path


class DataStatistics:
    """
    Comprehensive statistical analysis for scraped e-commerce data.
    Implements data quality checks, statistical summaries, and distributions.
    """
    
    def __init__(self, db_path: str = "scraped_data.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.data = None
        
    def load_data(self) -> pd.DataFrame:
        """Load all scraped data from database into pandas DataFrame."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT 
                p.*,
                j.search_term as job_search_term,
                j.status as job_status,
                j.created_at as job_created_at
            FROM products p
            LEFT JOIN jobs j ON p.job_id = j.job_id
            WHERE p.name IS NOT NULL
            """
            self.data = pd.read_sql_query(query, conn)
            conn.close()
            
            self.data['price_numeric'] = pd.to_numeric(
                self.data['price'].astype(str).str.replace(r'[£$,]', '', regex=True),
                errors='coerce'
            )
            
            self.data['scrape_time'] = pd.to_datetime(self.data['scrape_time'], errors='coerce')
            
            self.logger.info(f"Loaded {len(self.data)} records for analysis")
            return self.data
            
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def data_quality_checks(self) -> Dict[str, Any]:
        """
        Comprehensive data quality assessment.
        Returns metrics on completeness, validity, and consistency.
        """
        if self.data is None or self.data.empty:
            self.load_data()
        
        total_records = len(self.data)
        
        quality_report = {
            'total_records': total_records,
            'completeness': {
                'name_complete': (self.data['name'].notna().sum() / total_records * 100),
                'price_complete': (self.data['price_numeric'].notna().sum() / total_records * 100),
                'link_complete': (self.data['link'].notna().sum() / total_records * 100),
                'availability_complete': (self.data['availability'].notna().sum() / total_records * 100)
            },
            'validity': {
                'valid_prices': (self.data['price_numeric'] > 0).sum(),
                'invalid_prices': (self.data['price_numeric'] <= 0).sum(),
                'missing_prices': self.data['price_numeric'].isna().sum(),
                'valid_links': self.data['link'].str.startswith('http', na=False).sum(),
                'duplicate_products': self.data.duplicated(subset=['name', 'search_term']).sum()
            },
            'consistency': {
                'sources': self.data['search_term'].value_counts().to_dict(),
                'price_ranges_by_source': {}
            }
        }
        
        for source in self.data['search_term'].unique():
            if pd.notna(source):
                source_data = self.data[self.data['search_term'] == source]
                prices = source_data['price_numeric'].dropna()
                if len(prices) > 0:
                    quality_report['consistency']['price_ranges_by_source'][source] = {
                        'min': float(prices.min()),
                        'max': float(prices.max()),
                        'mean': float(prices.mean()),
                        'count': len(prices)
                    }
        
        return quality_report
    
    def statistical_summaries(self) -> Dict[str, Any]:
        """
        Generate comprehensive statistical summaries including distributions.
        """
        if self.data is None or self.data.empty:
            self.load_data()
        
        summaries = {
            'overall': {},
            'by_source': {},
            'price_distributions': {},
            'temporal_analysis': {}
        }
        
        prices = self.data['price_numeric'].dropna()
        if len(prices) > 0:
            summaries['overall'] = {
                'total_products': len(self.data),
                'products_with_prices': len(prices),
                'price_statistics': {
                    'mean': float(prices.mean()),
                    'median': float(prices.median()),
                    'std': float(prices.std()),
                    'min': float(prices.min()),
                    'max': float(prices.max()),
                    'q25': float(prices.quantile(0.25)),
                    'q75': float(prices.quantile(0.75))
                }
            }
        
        for source in self.data['search_term'].unique():
            if pd.notna(source):
                source_data = self.data[self.data['search_term'] == source]
                source_prices = source_data['price_numeric'].dropna()
                
                summaries['by_source'][source] = {
                    'total_products': len(source_data),
                    'products_with_prices': len(source_prices),
                    'avg_price': float(source_prices.mean()) if len(source_prices) > 0 else None,
                    'price_range': {
                        'min': float(source_prices.min()) if len(source_prices) > 0 else None,
                        'max': float(source_prices.max()) if len(source_prices) > 0 else None
                    }
                }
        
        if len(prices) > 0:
            summaries['price_distributions'] = {
                'bins': np.histogram(prices, bins=10)[1].tolist(),
                'counts': np.histogram(prices, bins=10)[0].tolist(),
                'percentiles': {
                    f'p{p}': float(prices.quantile(p/100)) 
                    for p in [5, 10, 25, 50, 75, 90, 95]
                }
            }
        
        if 'scrape_time' in self.data.columns:
            self.data['scrape_hour'] = self.data['scrape_time'].dt.hour
            self.data['scrape_day'] = self.data['scrape_time'].dt.day_name()
            
            summaries['temporal_analysis'] = {
                'scraping_by_hour': self.data['scrape_hour'].value_counts().to_dict(),
                'scraping_by_day': self.data['scrape_day'].value_counts().to_dict(),
                'date_range': {
                    'earliest': str(self.data['scrape_time'].min()),
                    'latest': str(self.data['scrape_time'].max())
                }
            }
        
        return summaries
    
    def generate_price_analysis(self) -> Dict[str, Any]:
        """
        Advanced price analysis including outlier detection and price patterns.
        """
        if self.data is None or self.data.empty:
            self.load_data()
        
        prices = self.data['price_numeric'].dropna()
        analysis = {}
        
        if len(prices) > 0:
            Q1 = prices.quantile(0.25)
            Q3 = prices.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = prices[(prices < lower_bound) | (prices > upper_bound)]
            
            price_ranges = {
                'budget': {'min': 0, 'max': prices.quantile(0.25), 'count': 0, 'percentage': 0},
                'mid-range': {'min': prices.quantile(0.25), 'max': prices.quantile(0.75), 'count': 0, 'percentage': 0},
                'premium': {'min': prices.quantile(0.75), 'max': prices.max(), 'count': 0, 'percentage': 0}
            }
            
            for range_name, range_info in price_ranges.items():
                count = ((prices >= range_info['min']) & (prices <= range_info['max'])).sum()
                price_ranges[range_name]['count'] = int(count)
                price_ranges[range_name]['percentage'] = float(count / len(prices) * 100)
            
            analysis = {
                'outliers': outliers.tolist(),
                'price_ranges': price_ranges,
                'outlier_detection': {
                    'total_outliers': len(outliers),
                    'outlier_percentage': len(outliers) / len(prices) * 100,
                    'outlier_values': outliers.tolist(),
                    'bounds': {
                        'lower': float(lower_bound),
                        'upper': float(upper_bound)
                    }
                },
                'price_patterns': {
                    'ending_in_99': (prices.astype(str).str.endswith('.99')).sum(),
                    'round_numbers': (prices % 1 == 0).sum(),
                    'price_clustering': self._analyze_price_clustering(prices)
                }
            }
        
        return analysis
    
    def _analyze_price_clustering(self, prices: pd.Series) -> Dict[str, Any]:
        """Analyze price clustering patterns."""
        price_counts = prices.value_counts()
        
        return {
            'most_common_prices': price_counts.head(10).to_dict(),
            'unique_prices': len(price_counts),
            'avg_products_per_price': float(price_counts.mean())
        }
    
    def export_statistics(self, output_dir: str = "data_output/processed", format: str = "json") -> str:
        """Export statistical analysis to specified format."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        quality = self.data_quality_checks()
        summaries = self.statistical_summaries()
        price_analysis = self.generate_price_analysis()
        
        full_report = {
            'generated_at': datetime.now().isoformat(),
            'data_quality': quality,
            'statistical_summaries': summaries,
            'price_analysis': price_analysis
        }
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format.lower() == 'json':
            import json
            import numpy as np
            
            def convert_numpy_types(obj):
                if isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(v) for v in obj]
                elif isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                else:
                    return obj
            
            full_report = convert_numpy_types(full_report)
            
            output_path = Path(output_dir) / f"statistics_report_{timestamp}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(full_report, f, indent=2, ensure_ascii=False)
                
        elif format.lower() == 'excel':
            output_path = Path(output_dir) / f"statistics_report_{timestamp}.xlsx"
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                if self.data is not None:
                    self.data.to_excel(writer, sheet_name='Raw_Data', index=False)
                
                quality_df = pd.DataFrame([quality['completeness']]).T
                quality_df.columns = ['Percentage_Complete']
                quality_df.to_excel(writer, sheet_name='Data_Quality')
                
                if summaries['by_source']:
                    stats_df = pd.DataFrame(summaries['by_source']).T
                    stats_df.to_excel(writer, sheet_name='Stats_by_Source')
                    
        elif format.lower() == 'csv':
            output_path = Path(output_dir) / f"statistics_report_{timestamp}.csv"
            if self.data is not None:
                self.data.to_csv(output_path, index=False)
        else:
            import json
            import numpy as np
            
            def convert_numpy_types(obj):
                if isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(v) for v in obj]
                elif isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                else:
                    return obj
            
            full_report = convert_numpy_types(full_report)
            
            output_path = Path(output_dir) / f"statistics_report_{timestamp}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(full_report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Statistics exported to {output_path}")
        return str(output_path) 