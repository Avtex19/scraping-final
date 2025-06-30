"""
Integration tests for the complete scraping pipeline.
Tests end-to-end functionality from scraping to analysis and reporting.
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path
import sqlite3
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.scrapers.static_scraper import StaticScraper
from src.data.database import Database
from analysis import DataStatistics, TrendAnalyzer, ReportGenerator


class TestFullPipeline:
    """Integration tests for the complete scraping and analysis pipeline."""

    @pytest.fixture
    def temp_environment(self):
        """Create temporary environment for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / 'data_output'
            logs_dir = Path(temp_dir) / 'logs'
            data_dir.mkdir(parents=True)
            logs_dir.mkdir(parents=True)

            db_path = Path(temp_dir) / 'test.db'

            yield {
                'temp_dir': temp_dir,
                'data_dir': str(data_dir),
                'logs_dir': str(logs_dir),
                'db_path': str(db_path)
            }

    @pytest.fixture
    def sample_scraper_config(self):
        """Create sample configuration for testing static scraper."""
        return {
            'name': 'TestScraper',
            'base_url': 'http://books.toscrape.com/catalogue/page-{}.html',
            'start_page': 1,
            'max_pages': 1,
            'delay_range': (0.1, 0.2),
            'selectors': {
                'container': 'article.product_pod',
                'name': 'h3 a',
                'price': 'p.price_color',
                'link': 'h3 a',
                'image': 'img',
                'availability': 'p.instock.availability'
            }
        }

    def test_static_scraping_to_database(self, temp_environment, sample_scraper_config):
        """Test static scraping with database storage."""
        db_path = temp_environment['db_path']

        db = Database(db_path)

        try:
            scraper = StaticScraper(
                sample_scraper_config,
                log_file=None
            )

            results = scraper.scrape()

            assert isinstance(results, list)

            with db as database:
                job_id = database.queue_job('test_scraping')

                for result in results:
                    result['source'] = 'TestSource'
                    result['search_term'] = 'test'

                database.insert_products(results, job_id=job_id)
                database.mark_job_complete(job_id)

                cursor = database.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM products")
                product_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'completed'")
                completed_jobs = cursor.fetchone()[0]

                assert completed_jobs >= 1

        except Exception as e:
            if "network" in str(e).lower() or "timeout" in str(e).lower():
                pytest.skip(f"Network-related test failure: {e}")
            else:
                raise

    def test_analysis_pipeline(self, temp_environment):
        """Test analysis pipeline with sample data."""
        db_path = temp_environment['db_path']

        self._create_sample_database(db_path)

        stats = DataStatistics(db_path)

        data = stats.load_data()
        assert not data.empty

        quality_report = stats.data_quality_checks()
        assert 'total_records' in quality_report
        assert quality_report['total_records'] > 0

        summaries = stats.statistical_summaries()
        assert 'overall' in summaries
        assert 'by_source' in summaries

        trends = TrendAnalyzer(db_path)
        trend_report = trends.generate_trend_report()

        assert 'report_metadata' in trend_report
        assert 'price_trends' in trend_report
        assert 'source_comparison' in trend_report

    def test_report_generation_pipeline(self, temp_environment):
        """Test complete report generation pipeline."""
        db_path = temp_environment['db_path']
        output_dir = temp_environment['data_dir']

        self._create_sample_database(db_path)

        reports = ReportGenerator(db_path)

        report_path = reports.generate_comprehensive_report(output_dir)

        assert os.path.exists(report_path)
        assert report_path.endswith('.html')

        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'E-Commerce Scraping Analysis Report' in content
            assert 'Total Products Scraped' in content

    def test_export_pipeline(self, temp_environment):
        """Test data export pipeline."""
        db_path = temp_environment['db_path']
        output_dir = temp_environment['data_dir']

        self._create_sample_database(db_path)

        reports = ReportGenerator(db_path)
        exported_files = reports.export_data_formats(output_dir)

        assert 'csv' in exported_files
        assert 'json' in exported_files
        assert 'excel' in exported_files

        for format_type, file_path in exported_files.items():
            assert os.path.exists(file_path)

        json_path = exported_files['json']
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            assert isinstance(json_data, list)
            assert len(json_data) > 0

    def test_error_handling_pipeline(self, temp_environment):
        """Test pipeline error handling."""
        db_path = temp_environment['db_path']

        db = Database(db_path)

        with db as database:
            pass

        stats = DataStatistics(db_path)
        data = stats.load_data()
        assert data.empty

        quality_report = stats.data_quality_checks()
        assert quality_report['total_records'] == 0

        summaries = stats.statistical_summaries()
        assert 'overall' in summaries

    def test_configuration_integration(self, temp_environment, sample_scraper_config):
        """Test configuration management integration."""
        from cli.commands import CommandProcessor

        config_path = Path(temp_environment['temp_dir']) / 'config.yaml'

        processor = CommandProcessor(str(config_path))

        is_valid = processor.validate_configuration()
        assert is_valid

        template_path = Path(temp_environment['temp_dir']) / 'template.yaml'
        processor.export_configuration_template(str(template_path))

        assert os.path.exists(template_path)

    def test_cli_integration(self, temp_environment):
        """Test CLI integration with core functionality."""
        from cli.interface import ScrapingCLI

        cli_app = ScrapingCLI()

        assert cli_app.db is not None
        assert cli_app.stats is not None
        assert cli_app.trends is not None
        assert cli_app.reports is not None

    def _create_sample_database(self, db_path):
        """Create database with sample data for testing."""
        conn = sqlite3.connect(db_path)

        conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                price TEXT,
                link TEXT,
                image TEXT,
                availability TEXT,
                search_term TEXT,
                scrape_time TEXT,
                job_id INTEGER
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_term TEXT,
                status TEXT,
                created_at TEXT,
                completed_at TEXT
            )
        ''')

        sample_products = [
            ('Product A', '$10.99', 'http://example.com/1', 'http://example.com/img1.jpg', 'In Stock', 'books',
             '2024-01-01T10:00:00', 1),
            ('Product B', '$25.50', 'http://example.com/2', 'http://example.com/img2.jpg', 'Out of Stock', 'books',
             '2024-01-01T11:00:00', 1),
            ('Product C', '$99.99', 'http://example.com/3', 'http://example.com/img3.jpg', 'In Stock', 'electronics',
             '2024-01-01T12:00:00', 2),
            ('Product D', '$5.00', 'http://example.com/4', 'http://example.com/img4.jpg', 'In Stock', 'electronics',
             '2024-01-01T13:00:00', 2),
            ('Product E', '$15.99', 'http://example.com/5', 'http://example.com/img5.jpg', 'In Stock', 'books',
             '2024-01-02T10:00:00', 3),
        ]

        conn.executemany('''
            INSERT INTO products (name, price, link, image, availability, search_term, scrape_time, job_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_products)

        sample_jobs = [
            ('books', 'completed', '2024-01-01T09:00:00', '2024-01-01T09:30:00'),
            ('electronics', 'completed', '2024-01-01T10:00:00', '2024-01-01T10:45:00'),
            ('books', 'completed', '2024-01-02T09:00:00', '2024-01-02T09:25:00'),
        ]

        conn.executemany('''
            INSERT INTO jobs (search_term, status, created_at, completed_at)
            VALUES (?, ?, ?, ?)
        ''', sample_jobs)

        conn.commit()
        conn.close()


if __name__ == '__main__':
    pytest.main([__file__])
