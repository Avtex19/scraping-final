"""
Command processor for advanced CLI operations and automation.
Handles scheduling, batch processing, and configuration management.
"""

import os
import sys
import json
import yaml
import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import click

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.scrapers import StaticScraper, EbayScraper, AmazonScrapyRunner
from src.data.database import Database
from src.analysis import DataStatistics, TrendAnalyzer, ReportGenerator


class CommandProcessor:
    """
    Advanced command processor for automation and batch operations.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or "../config/settings.yaml"
        self.config = self._load_configuration()
        self.db = Database()
        
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return yaml.safe_load(f)
            else:
                # Create default configuration
                default_config = self._create_default_config()
                self._save_configuration(default_config)
                return default_config
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration."""
        return {
            'scraping': {
                'sources': {
                    'static': {
                        'enabled': True,
                        'max_pages': 3,
                        'delay_range': [1, 2]
                    },
                    'dynamic': {
                        'enabled': True,
                        'max_pages': 2,
                        'search_terms': ['iphone', 'laptop'],
                        'headless': True
                    },
                    'framework': {
                        'enabled': True,
                        'max_pages': 1,
                        'search_terms': ['laptop']
                    }
                },
                'protection': {
                    'rate_limiting': True,
                    'user_agent_rotation': True,
                    'retry_attempts': 3,
                    'captcha_detection': True
                }
            },
            'analysis': {
                'auto_generate_reports': True,
                'export_formats': ['json', 'csv', 'excel'],
                'chart_generation': True
            },
            'scheduling': {
                'enabled': False,
                'frequency': 'daily',
                'time': '02:00',
                'auto_cleanup': True,
                'max_data_age_days': 30
            },
            'output': {
                'base_directory': 'data_output',
                'organize_by_date': True,
                'compress_old_files': True
            }
        }
    
    def _save_configuration(self, config: Dict[str, Any]):
        """Save configuration to YAML file."""
        try:
            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
                
            self.logger.info(f"Configuration saved to {config_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
    
    def run_batch_scraping(self, sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run batch scraping operations based on configuration.
        """
        sources = sources or ['static', 'dynamic', 'framework']
        results = {'total_items': 0, 'sources': {}}
        
        click.echo(click.style("🚀 Starting Batch Scraping Operation", fg='blue', bold=True))
        
        # Static scraping
        if 'static' in sources and self.config['scraping']['sources']['static']['enabled']:
            click.echo("\n📚 Running static scraping...")
            try:
                from src.utils.config import static_config
                
                # Update config with settings
                static_config['max_pages'] = self.config['scraping']['sources']['static']['max_pages']
                static_config['delay_range'] = tuple(self.config['scraping']['sources']['static']['delay_range'])
                
                static_scraper = StaticScraper(static_config)
                static_results = static_scraper.scrape()
                
                for r in static_results:
                    r['source'] = 'BooksToScrape'
                    r['search_term'] = 'books'
                
                # Save to database
                job_id = self.db.queue_job('books_batch')
                self.db.insert_products(static_results, job_id=job_id)
                self.db.mark_job_complete(job_id)
                
                results['sources']['static'] = len(static_results)
                results['total_items'] += len(static_results)
                
                click.echo(f"✅ Static scraping completed: {len(static_results)} items")
                
            except Exception as e:
                click.echo(click.style(f"❌ Static scraping failed: {e}", fg='red'))
                results['sources']['static'] = 0
        
        # Dynamic scraping
        if 'dynamic' in sources and self.config['scraping']['sources']['dynamic']['enabled']:
            click.echo("\n🛍️ Running dynamic scraping...")
            try:
                search_terms = self.config['scraping']['sources']['dynamic']['search_terms']
                max_pages = self.config['scraping']['sources']['dynamic']['max_pages']
                headless = self.config['scraping']['sources']['dynamic']['headless']
                
                total_dynamic_items = 0
                
                with EbayScraper(headless=headless) as scraper:
                    for term in search_terms:
                        dynamic_results = scraper.scrape(term, max_pages=max_pages)
                        
                        for r in dynamic_results:
                            r['search_term'] = term
                            r['source'] = 'eBay'
                            r['scrape_time'] = datetime.now().isoformat()
                        
                        # Save to database
                        job_id = self.db.queue_job(f'{term}_batch')
                        self.db.insert_products(dynamic_results, job_id=job_id)
                        self.db.mark_job_complete(job_id)
                        
                        total_dynamic_items += len(dynamic_results)
                        click.echo(f"  ✅ {term}: {len(dynamic_results)} items")
                
                results['sources']['dynamic'] = total_dynamic_items
                results['total_items'] += total_dynamic_items
                
            except Exception as e:
                click.echo(click.style(f"❌ Dynamic scraping failed: {e}", fg='red'))
                results['sources']['dynamic'] = 0
        
        # Framework scraping
        if 'framework' in sources and self.config['scraping']['sources']['framework']['enabled']:
            click.echo("\n🕸️ Running framework scraping...")
            try:
                search_terms = self.config['scraping']['sources']['framework']['search_terms']
                max_pages = self.config['scraping']['sources']['framework']['max_pages']
                
                amazon_runner = AmazonScrapyRunner()
                framework_results = amazon_runner.run_scraper(search_terms, max_pages=max_pages)
                
                results['sources']['framework'] = len(framework_results)
                results['total_items'] += len(framework_results)
                
                click.echo(f"✅ Framework scraping completed: {len(framework_results)} items")
                
            except Exception as e:
                click.echo(click.style(f"❌ Framework scraping failed: {e}", fg='red'))
                results['sources']['framework'] = 0
        
        # Auto-generate reports if enabled
        if self.config['analysis']['auto_generate_reports']:
            self._auto_generate_reports()
        
        return results
    
    def _auto_generate_reports(self):
        """Automatically generate reports after scraping."""
        click.echo("\n📊 Auto-generating reports...")
        
        try:
            report_generator = ReportGenerator()
            
            # Generate comprehensive report
            if self.config['analysis']['chart_generation']:
                report_path = report_generator.generate_comprehensive_report()
                click.echo(f"📄 HTML report: {report_path}")
            
            # Export in configured formats
            if self.config['analysis']['export_formats']:
                exported = report_generator.export_data_formats()
                for fmt, path in exported.items():
                    if fmt in self.config['analysis']['export_formats']:
                        click.echo(f"💾 {fmt.upper()} export: {path}")
                        
        except Exception as e:
            click.echo(click.style(f"❌ Auto-report generation failed: {e}", fg='red'))
    
    def setup_scheduling(self):
        """Setup automated scheduling based on configuration."""
        if not self.config['scheduling']['enabled']:
            click.echo("⏰ Scheduling is disabled in configuration")
            return
        
        frequency = self.config['scheduling']['frequency']
        time_str = self.config['scheduling']['time']
        
        if frequency == 'daily':
            schedule.every().day.at(time_str).do(self._scheduled_run)
        elif frequency == 'weekly':
            schedule.every().week.at(time_str).do(self._scheduled_run)
        elif frequency == 'hourly':
            schedule.every().hour.do(self._scheduled_run)
        
        click.echo(f"⏰ Scheduled {frequency} scraping at {time_str}")
        
        # Run scheduler
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _scheduled_run(self):
        """Execute scheduled scraping run."""
        self.logger.info("Starting scheduled scraping run")
        
        try:
            results = self.run_batch_scraping()
            
            # Data cleanup if enabled
            if self.config['scheduling']['auto_cleanup']:
                self._cleanup_old_data()
            
            self.logger.info(f"Scheduled run completed: {results['total_items']} items")
            
        except Exception as e:
            self.logger.error(f"Scheduled run failed: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old data based on configuration."""
        max_age_days = self.config['scheduling']['max_data_age_days']
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        try:
            with self.db as db:
                conn = db.conn
                cursor = conn.cursor()
                
                # Delete old products
                cursor.execute(
                    "DELETE FROM products WHERE scrape_time < ?",
                    (cutoff_date.isoformat(),)
                )
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old records")
                
        except Exception as e:
            self.logger.error(f"Data cleanup failed: {e}")
    
    def configure_sources(self, source_config: Dict[str, Any]):
        """Update source configuration."""
        self.config['scraping']['sources'].update(source_config)
        self._save_configuration(self.config)
        click.echo("✅ Source configuration updated")
    
    def show_configuration(self):
        """Display current configuration."""
        click.echo(click.style("\n⚙️ CURRENT CONFIGURATION", fg='blue', bold=True))
        
        # Format configuration for display
        config_yaml = yaml.dump(self.config, default_flow_style=False, indent=2)
        click.echo(config_yaml)
    
    def validate_configuration(self) -> bool:
        """Validate current configuration."""
        errors = []
        
        # Check required sections
        required_sections = ['scraping', 'analysis', 'scheduling', 'output']
        for section in required_sections:
            if section not in self.config:
                errors.append(f"Missing section: {section}")
        
        # Check scraping sources
        if 'scraping' in self.config and 'sources' in self.config['scraping']:
            sources = self.config['scraping']['sources']
            for source_name, source_config in sources.items():
                if 'enabled' not in source_config:
                    errors.append(f"Missing 'enabled' in {source_name} source config")
        
        if errors:
            click.echo(click.style("❌ Configuration Errors:", fg='red', bold=True))
            for error in errors:
                click.echo(f"  • {error}")
            return False
        else:
            click.echo(click.style("✅ Configuration is valid", fg='green'))
            return True
    
    def export_configuration_template(self, output_path: str = "config/template.yaml"):
        """Export a configuration template."""
        template = self._create_default_config()
        
        # Add comments to template
        template['_comments'] = {
            'scraping': 'Configure scraping sources and protection mechanisms',
            'analysis': 'Set up automatic analysis and reporting options',
            'scheduling': 'Configure automated scheduling and cleanup',
            'output': 'Manage output directories and file organization'
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(template, f, default_flow_style=False, indent=2)
        
        click.echo(f"📁 Configuration template exported to: {output_path}")
    
    def run_diagnostics(self):
        """Run system diagnostics and checks."""
        click.echo(click.style("\n🔍 RUNNING SYSTEM DIAGNOSTICS", fg='blue', bold=True))
        
        diagnostics = {
            'configuration': self.validate_configuration(),
            'database': self._check_database_connection(),
            'dependencies': self._check_dependencies(),
            'output_directories': self._check_output_directories(),
            'disk_space': self._check_disk_space()
        }
        
        # Display results
        for check, status in diagnostics.items():
            icon = "✅" if status else "❌"
            click.echo(f"{icon} {check.replace('_', ' ').title()}")
        
        return all(diagnostics.values())
    
    def _check_database_connection(self) -> bool:
        """Check database connectivity."""
        try:
            with self.db as db:
                cursor = db.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM products")
                return True
        except Exception as e:
            click.echo(f"  Database error: {e}")
            return False
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        required_modules = [
            'pandas', 'numpy', 'matplotlib', 'seaborn', 
            'beautifulsoup4', 'selenium', 'scrapy', 'click'
        ]
        
        missing = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing.append(module)
        
        if missing:
            click.echo(f"  Missing dependencies: {', '.join(missing)}")
            return False
        return True
    
    def _check_output_directories(self) -> bool:
        """Check if output directories exist and are writable."""
        directories = [
            'data_output/raw',
            'data_output/processed', 
            'data_output/reports',
            'logs'
        ]
        
        for directory in directories:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            
            if not path.is_dir() or not os.access(path, os.W_OK):
                click.echo(f"  Directory issue: {directory}")
                return False
        return True
    
    def _check_disk_space(self) -> bool:
        """Check available disk space."""
        try:
            import shutil
            free_bytes = shutil.disk_usage('.').free
            free_gb = free_bytes / (1024**3)
            
            if free_gb < 1:  # Less than 1GB
                click.echo(f"  Low disk space: {free_gb:.1f}GB available")
                return False
            return True
        except Exception:
            return True  # Can't check, assume OK 