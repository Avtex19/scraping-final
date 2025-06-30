"""
Unit tests for the statistics analysis module.
Tests data quality checks, statistical summaries, and price analysis.
"""

import pytest
import pandas as pd
import numpy as np
import sqlite3
import tempfile
import os
from unittest.mock import Mock, patch
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from analysis.statistics import DataStatistics


class TestDataStatistics:
    """Test suite for DataStatistics class."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return pd.DataFrame({
            'product_id': [1, 2, 3, 4, 5],
            'name': ['Product A', 'Product B', '', 'Product D', 'Product E'],
            'price': ['$10.99', '£25.50', '', '$99.99', '$5.00'],
            'price_numeric': [10.99, 25.50, np.nan, 99.99, 5.00],
            'link': ['http://example.com/1', 'http://example.com/2', '', 'http://example.com/4',
                     'http://example.com/5'],
            'availability': ['In Stock', 'Out of Stock', 'In Stock', '', 'In Stock'],
            'search_term': ['books', 'books', 'electronics', 'electronics', 'books'],
            'scrape_time': ['2024-01-01T10:00:00', '2024-01-01T11:00:00', '2024-01-01T12:00:00', '2024-01-01T13:00:00',
                            '2024-01-01T14:00:00']
        })

    @pytest.fixture
    def temp_db(self, sample_data):
        """Create temporary database with sample data."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)

        conn.execute('''
            CREATE TABLE products (
                product_id INTEGER PRIMARY KEY,
                name TEXT,
                price TEXT,
                link TEXT,
                availability TEXT,
                search_term TEXT,
                scrape_time TEXT,
                job_id INTEGER
            )
        ''')

        conn.execute('''
            CREATE TABLE jobs (
                job_id INTEGER PRIMARY KEY,
                search_term TEXT,
                status TEXT,
                created_at TEXT
            )
        ''')

        for _, row in sample_data.iterrows():
            conn.execute('''
                INSERT INTO products (product_id, name, price, link, availability, search_term, scrape_time, job_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (row['product_id'], row['name'], row['price'], row['link'],
                  row['availability'], row['search_term'], row['scrape_time'], 1))

        conn.execute('''
            INSERT INTO jobs (job_id, search_term, status, created_at)
            VALUES (1, 'test', 'completed', '2024-01-01T10:00:00')
        ''')

        conn.commit()
        conn.close()

        yield db_path

        os.unlink(db_path)

    def test_initialization(self, temp_db):
        """Test DataStatistics initialization."""
        stats = DataStatistics(temp_db)
        assert stats.db_path == temp_db
        assert stats.data is None

    def test_load_data(self, temp_db, sample_data):
        """Test data loading from database."""
        stats = DataStatistics(temp_db)
        loaded_data = stats.load_data()

        assert not loaded_data.empty
        assert len(loaded_data) == len(sample_data)
        assert 'price_numeric' in loaded_data.columns
        assert 'scrape_time' in loaded_data.columns

    def test_data_quality_checks(self, temp_db):
        """Test data quality assessment."""
        stats = DataStatistics(temp_db)
        stats.load_data()

        quality_report = stats.data_quality_checks()

        assert 'total_records' in quality_report
        assert 'completeness' in quality_report
        assert 'validity' in quality_report
        assert 'consistency' in quality_report

        completeness = quality_report['completeness']
        assert 'name_complete' in completeness
        assert 'price_complete' in completeness
        assert 'link_complete' in completeness
        assert 'availability_complete' in completeness

        validity = quality_report['validity']
        assert 'valid_prices' in validity
        assert 'invalid_prices' in validity
        assert 'missing_prices' in validity
        assert 'valid_links' in validity
        assert 'duplicate_products' in validity

    def test_statistical_summaries(self, temp_db):
        """Test statistical summary generation."""
        stats = DataStatistics(temp_db)
        stats.load_data()

        summaries = stats.statistical_summaries()

        assert 'overall' in summaries
        assert 'by_source' in summaries
        assert 'price_distributions' in summaries
        assert 'temporal_analysis' in summaries

        if summaries['overall']:
            overall = summaries['overall']
            assert 'total_products' in overall
            assert 'products_with_prices' in overall

            if 'price_statistics' in overall:
                price_stats = overall['price_statistics']
                assert 'mean' in price_stats
                assert 'median' in price_stats
                assert 'std' in price_stats
                assert 'min' in price_stats
                assert 'max' in price_stats

    def test_generate_price_analysis(self, temp_db):
        """Test price analysis functionality."""
        stats = DataStatistics(temp_db)
        stats.load_data()

        analysis = stats.generate_price_analysis()

        if analysis:
            assert 'outlier_detection' in analysis
            assert 'price_patterns' in analysis

            outlier_detection = analysis['outlier_detection']
            assert 'total_outliers' in outlier_detection
            assert 'outlier_percentage' in outlier_detection
            assert 'bounds' in outlier_detection

    def test_export_statistics(self, temp_db):
        """Test statistics export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stats = DataStatistics(temp_db)

            export_path = stats.export_statistics(temp_dir)

            assert os.path.exists(export_path)
            assert export_path.endswith('.json')

    def test_price_clustering_analysis(self, temp_db):
        """Test price clustering analysis."""
        stats = DataStatistics(temp_db)
        stats.load_data()

        prices = pd.Series([10.99, 25.50, 99.99, 5.00, 10.99, 25.50])

        clustering = stats._analyze_price_clustering(prices)

        assert 'most_common_prices' in clustering
        assert 'unique_prices' in clustering
        assert 'avg_products_per_price' in clustering

    def test_empty_database(self):
        """Test behavior with empty database."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        conn.execute('''
            CREATE TABLE products (
                product_id INTEGER PRIMARY KEY,
                name TEXT,
                price TEXT,
                link TEXT,
                availability TEXT,
                search_term TEXT,
                scrape_time TEXT,
                job_id INTEGER
            )
        ''')
        conn.execute('''
            CREATE TABLE jobs (
                job_id INTEGER PRIMARY KEY,
                search_term TEXT,
                status TEXT,
                created_at TEXT
            )
        ''')
        conn.commit()
        conn.close()

        try:
            stats = DataStatistics(db_path)
            loaded_data = stats.load_data()

            assert loaded_data.empty

            quality_report = stats.data_quality_checks()
            assert quality_report['total_records'] == 0

        finally:
            os.unlink(db_path)

    def test_invalid_database_path(self):
        """Test behavior with invalid database path."""
        stats = DataStatistics('nonexistent.db')
        loaded_data = stats.load_data()

        assert loaded_data.empty

    @patch('analysis.statistics.pd.read_sql_query')
    def test_database_error_handling(self, mock_read_sql):
        """Test error handling during database operations."""
        mock_read_sql.side_effect = Exception("Database error")

        stats = DataStatistics('test.db')
        loaded_data = stats.load_data()

        assert loaded_data.empty


if __name__ == '__main__':
    pytest.main([__file__])
