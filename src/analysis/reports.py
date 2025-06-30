"""
Report generation module for scraped e-commerce data.
Creates HTML reports with charts, tables, and automated insights.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Any
import logging
from datetime import datetime
from pathlib import Path
from jinja2 import Template


from .statistics import DataStatistics
from .trends import TrendAnalyzer


class ReportGenerator:
    """
    Comprehensive report generator for e-commerce scraping analysis.
    Creates HTML reports with visualizations and automated insights.
    """
    
    def __init__(self, db_path: str = "scraped_data.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.stats_analyzer = DataStatistics(db_path)
        self.trend_analyzer = TrendAnalyzer(db_path)
        
    def generate_comprehensive_report(self, output_dir: str = "../data_output/reports") -> str:
        """Generate a comprehensive HTML report with all analyses."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        self.stats_analyzer.load_data()
        quality_report = self.stats_analyzer.data_quality_checks()
        statistical_summaries = self.stats_analyzer.statistical_summaries()
        price_analysis = self.stats_analyzer.generate_price_analysis()
        trend_report = self.trend_analyzer.generate_trend_report()
        
        charts = self._generate_charts_for_report(output_dir)
        
        report_data = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_products': quality_report.get('total_records', 0),
            'quality_report': quality_report,
            'statistical_summaries': statistical_summaries,
            'price_analysis': price_analysis,
            'trend_report': trend_report,
            'charts': charts,
            'insights': self._generate_automated_insights(quality_report, statistical_summaries, trend_report)
        }
        
        html_content = self._create_html_report(report_data)
        
        report_file = Path(output_dir) / f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Comprehensive report generated: {report_file}")
        return str(report_file)
    
    def _generate_charts_for_report(self, output_dir: str) -> Dict[str, str]:
        """Generate chart images for the HTML report."""
        import matplotlib
        matplotlib.use('Agg')
        
        charts = {}
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        data = self.stats_analyzer.data
        if data is None or data.empty:
            return charts

        if 'price_numeric' in data.columns:
            plt.figure(figsize=(10, 6))
            prices = data['price_numeric'].dropna()
            if len(prices) > 0:
                plt.hist(prices, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
                plt.title('Price Distribution Across All Products')
                plt.xlabel('Price')
                plt.ylabel('Frequency')
                plt.grid(True, alpha=0.3)
                
                chart_path = Path(output_dir) / 'price_distribution.png'
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                # Convert to relative path for browser compatibility
                relative_path = self._convert_to_relative_path(chart_path, output_dir)
                charts['price_distribution'] = relative_path
        
        if 'search_term' in data.columns:
            source_stats = data.groupby('search_term').agg({
                'price_numeric': ['count', 'mean', 'median']
            }).round(2)
            
            if not source_stats.empty:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
                
                counts = data['search_term'].value_counts()
                ax1.bar(counts.index, counts.values, color='lightcoral')
                ax1.set_title('Product Count by Source')
                ax1.set_xlabel('Source')
                ax1.set_ylabel('Number of Products')
                ax1.tick_params(axis='x', rotation=45)
                
                avg_prices = data.groupby('search_term')['price_numeric'].mean().dropna()
                if not avg_prices.empty:
                    ax2.bar(avg_prices.index, avg_prices.values, color='lightgreen')
                    ax2.set_title('Average Price by Source')
                    ax2.set_xlabel('Source')
                    ax2.set_ylabel('Average Price')
                    ax2.tick_params(axis='x', rotation=45)
                
                plt.tight_layout()
                chart_path = Path(output_dir) / 'source_comparison.png'
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                # Convert to relative path for browser compatibility
                relative_path = self._convert_to_relative_path(chart_path, output_dir)
                charts['source_comparison'] = relative_path
        
        return charts
    
    def _generate_automated_insights(self, quality_report: Dict, summaries: Dict, trends: Dict) -> List[str]:
        """Generate automated insights based on analysis results."""
        insights = []
        
        completeness = quality_report.get('completeness', {})
        if completeness.get('price_complete', 0) < 80:
            insights.append(f"⚠️ Price data completeness is {completeness.get('price_complete', 0):.1f}% - consider improving data extraction")
        
        if quality_report.get('validity', {}).get('duplicate_products', 0) > 10:
            insights.append(f"📊 Found {quality_report['validity']['duplicate_products']} duplicate products - deduplication recommended")
        
        overall_stats = summaries.get('overall', {})
        if overall_stats.get('price_statistics'):
            price_stats = overall_stats['price_statistics']
            if price_stats['std'] > price_stats['mean']:
                insights.append("💰 High price variance detected - market shows significant price diversity")
            
            if price_stats['max'] > price_stats['mean'] * 10:
                insights.append("🔍 Potential outliers detected - some products significantly more expensive than average")
        
        if trends.get('price_trends', {}).get('overall_trends'):
            trend_direction = trends['price_trends']['overall_trends'].get('trend_direction')
            if trend_direction == 'increasing':
                insights.append("📈 Price trend analysis shows increasing prices over time")
            elif trend_direction == 'decreasing':
                insights.append("📉 Price trend analysis shows decreasing prices over time")
        
        source_comparison = trends.get('source_comparison', {}).get('cross_source_insights', {})
        if source_comparison.get('cheapest_source') and source_comparison.get('most_expensive_source'):
            cheapest = source_comparison['cheapest_source']
            most_expensive = source_comparison['most_expensive_source']
            price_diff = source_comparison.get('price_difference', 0)
            insights.append(f"💸 {cheapest} offers the lowest average prices, while {most_expensive} has the highest (difference: ${price_diff:.2f})")
        
        return insights if insights else ["✅ All metrics appear normal"]
    
    def _create_html_report(self, report_data: Dict) -> str:
        """Create HTML report using template."""
        template_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-Commerce Scraping Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px; }
        h3 { color: #7f8c8d; }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
        .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; margin-bottom: 5px; }
        .metric-label { font-size: 0.9em; opacity: 0.9; }
        .insight { background-color: #e8f4fd; border-left: 4px solid #3498db; padding: 15px; margin: 10px 0; border-radius: 4px; }
        .chart-container { text-align: center; margin: 20px 0; }
        .chart-container img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: bold; }
        .status-complete { color: #27ae60; font-weight: bold; }
        .status-incomplete { color: #e74c3c; font-weight: bold; }
        .footer { text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🕷️ E-Commerce Scraping Analysis Report</h1>
        <p style="text-align: center; color: #7f8c8d;">Generated on {{ generated_at }}</p>
        
        <div class="summary-grid">
            <div class="metric-card">
                <div class="metric-value">{{ total_products }}</div>
                <div class="metric-label">Total Products Scraped</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ quality_report.completeness.price_complete|round(1) }}%</div>
                <div class="metric-label">Price Data Completeness</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ quality_report.consistency.sources|length }}</div>
                <div class="metric-label">Data Sources</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${{ statistical_summaries.overall.price_statistics.mean|round(2) if statistical_summaries.overall.price_statistics else 'N/A' }}</div>
                <div class="metric-label">Average Price</div>
            </div>
        </div>
        
        <h2>🔍 Key Insights</h2>
        {% for insight in insights %}
        <div class="insight">{{ insight }}</div>
        {% endfor %}
        
        <h2>📊 Data Quality Assessment</h2>
        <table>
            <thead>
                <tr><th>Metric</th><th>Completeness %</th><th>Status</th></tr>
            </thead>
            <tbody>
                <tr>
                    <td>Product Names</td>
                    <td>{{ quality_report.completeness.name_complete|round(1) }}%</td>
                    <td class="{% if quality_report.completeness.name_complete >= 90 %}status-complete{% else %}status-incomplete{% endif %}">
                        {% if quality_report.completeness.name_complete >= 90 %}✅ Excellent{% else %}⚠️ Needs Improvement{% endif %}
                    </td>
                </tr>
                <tr>
                    <td>Product Prices</td>
                    <td>{{ quality_report.completeness.price_complete|round(1) }}%</td>
                    <td class="{% if quality_report.completeness.price_complete >= 80 %}status-complete{% else %}status-incomplete{% endif %}">
                        {% if quality_report.completeness.price_complete >= 80 %}✅ Good{% else %}⚠️ Needs Improvement{% endif %}
                    </td>
                </tr>
                <tr>
                    <td>Product Links</td>
                    <td>{{ quality_report.completeness.link_complete|round(1) }}%</td>
                    <td class="{% if quality_report.completeness.link_complete >= 90 %}status-complete{% else %}status-incomplete{% endif %}">
                        {% if quality_report.completeness.link_complete >= 90 %}✅ Excellent{% else %}⚠️ Needs Improvement{% endif %}
                    </td>
                </tr>
            </tbody>
        </table>
        
        {% if charts.price_distribution %}
        <h2>💰 Price Analysis</h2>
        <div class="chart-container">
            <img src="{{ charts.price_distribution }}" alt="Price Distribution Chart">
        </div>
        {% endif %}
        
        {% if charts.source_comparison %}
        <h2>📈 Source Comparison</h2>
        <div class="chart-container">
            <img src="{{ charts.source_comparison }}" alt="Source Comparison Chart">
        </div>
        {% endif %}
        
        <h2>📋 Statistical Summary</h2>
        <table>
            <thead>
                <tr><th>Source</th><th>Products</th><th>Avg Price</th><th>Price Range</th></tr>
            </thead>
            <tbody>
                {% for source, stats in statistical_summaries.by_source.items() %}
                <tr>
                    <td>{{ source }}</td>
                    <td>{{ stats.total_products }}</td>
                    <td>${{ stats.avg_price|round(2) if stats.avg_price else 'N/A' }}</td>
                    <td>${{ stats.price_range.min|round(2) if stats.price_range.min else 'N/A' }} - ${{ stats.price_range.max|round(2) if stats.price_range.max else 'N/A' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <div class="footer">
            <p>Generated by Advanced Web Scraping Framework | {{ generated_at }}</p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_html)
        return template.render(**report_data)
    
    def export_data_formats(self, output_dir: str = "../data_output/processed") -> Dict[str, str]:
        """Export data in multiple formats (CSV, JSON, Excel)."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        data = self.stats_analyzer.load_data()
        
        if not data.empty:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            csv_path = Path(output_dir) / f"scraped_data_{timestamp}.csv"
            data.to_csv(csv_path, index=False, encoding='utf-8')
            exported_files['csv'] = str(csv_path)
            
            json_path = Path(output_dir) / f"scraped_data_{timestamp}.json"
            data.to_json(json_path, orient='records', indent=2, force_ascii=False)
            exported_files['json'] = str(json_path)
            
            excel_path = Path(output_dir) / f"scraped_data_{timestamp}.xlsx"
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                data.to_excel(writer, sheet_name='All_Data', index=False)
                
                for source in data['search_term'].unique():
                    if pd.notna(source):
                        source_data = data[data['search_term'] == source]
                        sheet_name = str(source).replace(' ', '_')[:31]  # Excel sheet name limit
                        source_data.to_excel(writer, sheet_name=sheet_name, index=False)
                        
            exported_files['excel'] = str(excel_path)
        
        self.logger.info(f"Data exported in {len(exported_files)} formats")
        return exported_files
    
    def generate_custom_report(self, config: Dict, output_dir: str = "../data_output/reports") -> str:
        """Generate a custom report based on user configuration."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.logger.info("🔧 Generating custom report with user configuration...")
        
        report_data = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'config': config
        }
        
        data = self.stats_analyzer.load_data()
        if data.empty:
            self.logger.warning("No data available for custom report")
            return ""
        
        report_data['total_products'] = len(data)
        
        if config.get('include_stats', True):
            try:
                quality_report = self.stats_analyzer.data_quality_checks()
                summaries = self.stats_analyzer.statistical_summaries()
                report_data['quality_report'] = quality_report
                report_data['statistical_summaries'] = summaries
                self.logger.info("✅ Statistical analysis included in custom report")
            except Exception as e:
                self.logger.error(f"Error including statistics: {e}")
                report_data['quality_report'] = {}
                report_data['statistical_summaries'] = {}
        
        if config.get('include_trends', True):
            try:
                trends = self.trend_analyzer.analyze_trends()
                report_data['trends'] = trends
                self.logger.info("✅ Trend analysis included in custom report")
            except Exception as e:
                self.logger.error(f"Error including trends: {e}")
                report_data['trends'] = {}
        
        if config.get('include_charts', True):
            try:
                charts = self._generate_charts_for_report(output_dir)
                report_data['charts'] = charts
                self.logger.info("✅ Charts included in custom report")
            except Exception as e:
                self.logger.error(f"Error generating charts: {e}")
                report_data['charts'] = {}
        
        if config.get('include_stats', True) and config.get('include_trends', True):
            try:
                insights = self._generate_automated_insights(
                    report_data.get('quality_report', {}),
                    report_data.get('statistical_summaries', {}),
                    report_data.get('trends', {})
                )
                report_data['insights'] = insights
            except Exception as e:
                self.logger.error(f"Error generating insights: {e}")
                report_data['insights'] = ["Unable to generate insights due to data issues"]
        else:
            report_data['insights'] = ["Custom report generated with limited analysis"]
        
        output_format = config.get('format', 'html').lower()
        
        if output_format == 'html':
            html_content = self._create_custom_html_report(report_data, config)
            output_file = Path(output_dir) / f"custom_report_{timestamp}.html"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
        elif output_format == 'json':
            output_file = Path(output_dir) / f"custom_report_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str, ensure_ascii=False)
                
        elif output_format == 'pdf':
            html_content = self._create_custom_html_report(report_data, config)
            output_file = Path(output_dir) / f"custom_report_{timestamp}.html"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info("📝 PDF generation requires additional setup - HTML version created")
        
        self.logger.info(f"✅ Custom report generated: {output_file}")
        return str(output_file)
    
    def _create_custom_html_report(self, report_data: Dict, config: Dict) -> str:
        """Create custom HTML report based on configuration."""
        template_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Custom Scraping Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f8f9fa; }
        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 15px; }
        h2 { color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 8px; margin-top: 30px; }
        .config-summary { background-color: #e8f5e8; padding: 15px; border-radius: 6px; margin: 20px 0; }
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 6px; text-align: center; }
        .metric-value { font-size: 1.8em; font-weight: bold; margin-bottom: 5px; }
        .metric-label { font-size: 0.9em; opacity: 0.9; }
        .insight { background-color: #e8f4fd; border-left: 4px solid #3498db; padding: 12px; margin: 8px 0; border-radius: 4px; }
        .chart-container { text-align: center; margin: 15px 0; }
        .chart-container img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 6px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: bold; }
        .footer { text-align: center; margin-top: 30px; color: #6c757d; font-size: 0.9em; }
        .section { margin: 25px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Custom Analysis Report</h1>
        <p style="text-align: center; color: #6c757d;">Generated on {{ generated_at }}</p>
        
        <div class="config-summary">
            <h3>📋 Report Configuration</h3>
            <p><strong>Statistics:</strong> {{ '✅ Included' if config.include_stats else '❌ Excluded' }}</p>
            <p><strong>Trends:</strong> {{ '✅ Included' if config.include_trends else '❌ Excluded' }}</p>
            <p><strong>Charts:</strong> {{ '✅ Included' if config.include_charts else '❌ Excluded' }}</p>
            <p><strong>Format:</strong> {{ config.format.upper() }}</p>
        </div>
        
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{{ total_products }}</div>
                <div class="metric-label">Total Products</div>
            </div>
            {% if quality_report %}
            <div class="metric-card">
                <div class="metric-value">{{ quality_report.completeness.price_complete|round(1) if quality_report.completeness else 'N/A' }}%</div>
                <div class="metric-label">Data Quality</div>
            </div>
            {% endif %}
        </div>
        
        {% if insights %}
        <div class="section">
            <h2>💡 Key Insights</h2>
            {% for insight in insights %}
            <div class="insight">{{ insight }}</div>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if config.include_stats and statistical_summaries %}
        <div class="section">
            <h2>📊 Statistical Summary</h2>
            <table>
                <thead>
                    <tr><th>Source</th><th>Products</th><th>Avg Price</th></tr>
                </thead>
                <tbody>
                    {% for source, stats in statistical_summaries.by_source.items() %}
                    <tr>
                        <td>{{ source }}</td>
                        <td>{{ stats.total_products }}</td>
                        <td>${{ stats.avg_price|round(2) if stats.avg_price else 'N/A' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        {% if config.include_charts and charts %}
        <div class="section">
            <h2>📈 Visualizations</h2>
            {% if charts.price_distribution %}
            <div class="chart-container">
                <h3>Price Distribution</h3>
                <img src="{{ charts.price_distribution }}" alt="Price Distribution">
            </div>
            {% endif %}
            {% if charts.source_comparison %}
            <div class="chart-container">
                <h3>Source Comparison</h3>
                <img src="{{ charts.source_comparison }}" alt="Source Comparison">
            </div>
            {% endif %}
        </div>
        {% endif %}
        
        <div class="footer">
            <p>Custom Report Generated by Advanced Web Scraping Framework</p>
            <p>{{ generated_at }}</p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_html)
        return template.render(**report_data)
    
    def generate_statistical_report(self, output_dir: str = "../data_output/reports") -> str:
        """Generate a focused statistical analysis report."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.logger.info("📊 Generating statistical analysis report...")
        
        self.stats_analyzer.load_data()
        quality_report = self.stats_analyzer.data_quality_checks()
        summaries = self.stats_analyzer.statistical_summaries()
        price_analysis = self.stats_analyzer.generate_price_analysis()
        
        charts = self._generate_charts_for_report(output_dir)
        
        relative_charts = {}
        for chart_name, chart_path in charts.items():
            relative_charts[chart_name] = self._convert_to_relative_path(chart_path, output_dir)
        
        report_data = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_products': quality_report.get('total_records', 0),
            'quality_report': quality_report,
            'statistical_summaries': summaries,
            'price_analysis': price_analysis,
            'charts': relative_charts
        }
        
        html_content = self._create_statistical_html_report(report_data)
        
        report_file = Path(output_dir) / f"statistical_report_{timestamp}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"✅ Statistical report generated: {report_file}")
        return str(report_file)
    
    def generate_trend_report(self, output_dir: str = "../data_output/reports") -> str:
        """Generate a focused trend analysis report."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.logger.info("📈 Generating trend analysis report...")
        
        self.trend_analyzer.load_data()
        trends = self.trend_analyzer.analyze_trends()
        price_trends = self.trend_analyzer.analyze_price_trends()
        source_comparison = self.trend_analyzer.comparative_source_analysis()
        
        charts = self.trend_analyzer.generate_trend_visualizations(output_dir)
        
        relative_charts = []
        if isinstance(charts, list):
            for chart_path in charts:
                relative_charts.append(self._convert_to_relative_path(chart_path, output_dir))
        else:
            relative_charts = charts
        
        report_data = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'trends': trends,
            'price_trends': price_trends,
            'source_comparison': source_comparison,
            'charts': relative_charts
        }
        
        html_content = self._create_trend_html_report(report_data)
        
        report_file = Path(output_dir) / f"trend_report_{timestamp}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"✅ Trend report generated: {report_file}")
        return str(report_file)
    
    def export_charts(self, output_dir: str = "../data_output/charts") -> str:
        """Export all charts and visualizations to a dedicated directory."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.logger.info("📊 Exporting charts and visualizations...")
        
        stats_charts = self._generate_charts_for_report(output_dir)
        
        trend_charts = self.trend_analyzer.generate_trend_visualizations(output_dir)
        
        relative_stats_charts = {}
        for chart_name, chart_path in stats_charts.items():
            relative_stats_charts[chart_name] = self._convert_to_relative_path(chart_path, output_dir)
        
        all_charts = relative_stats_charts.copy()
        if isinstance(trend_charts, dict):
            for chart_name, chart_path in trend_charts.items():
                all_charts[chart_name] = self._convert_to_relative_path(chart_path, output_dir)
        elif isinstance(trend_charts, list):
            for i, chart_path in enumerate(trend_charts):
                all_charts[f'trend_chart_{i+1}'] = self._convert_to_relative_path(chart_path, output_dir)
        
        index_html = self._create_charts_index(all_charts)
        index_file = Path(output_dir) / f"charts_index_{timestamp}.html"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        self.logger.info(f"✅ Charts exported to: {output_dir}")
        self.logger.info(f"✅ Chart index created: {index_file}")
        
        return str(output_dir)
    
    def _create_statistical_html_report(self, report_data: Dict) -> str:
        """Create HTML report focused on statistical analysis."""
        template_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Statistical Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f8f9fa; }
        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 15px; }
        h2 { color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 8px; margin-top: 30px; }
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 6px; text-align: center; }
        .metric-value { font-size: 1.8em; font-weight: bold; margin-bottom: 5px; }
        .metric-label { font-size: 0.9em; opacity: 0.9; }
        .chart-container { text-align: center; margin: 20px 0; }
        .chart-container img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: bold; }
        .footer { text-align: center; margin-top: 30px; color: #6c757d; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Statistical Analysis Report</h1>
        <p style="text-align: center; color: #6c757d;">Generated on {{ generated_at }}</p>
        
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{{ total_products }}</div>
                <div class="metric-label">Total Products</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ quality_report.completeness.price_complete|round(1) if quality_report.completeness else 'N/A' }}%</div>
                <div class="metric-label">Price Data Quality</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ statistical_summaries.overall.price_statistics.mean|round(2) if statistical_summaries.overall and statistical_summaries.overall.price_statistics else 'N/A' }}</div>
                <div class="metric-label">Average Price</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ price_analysis.outliers|length if price_analysis.outliers else 0 }}</div>
                <div class="metric-label">Price Outliers</div>
            </div>
        </div>
        
        <h2>📈 Statistical Summary by Source</h2>
        <table>
            <thead>
                <tr><th>Source</th><th>Products</th><th>Avg Price</th><th>Min Price</th><th>Max Price</th></tr>
            </thead>
            <tbody>
                {% for source, stats in statistical_summaries.by_source.items() %}
                <tr>
                    <td>{{ source }}</td>
                    <td>{{ stats.total_products }}</td>
                    <td>${{ stats.avg_price|round(2) if stats.avg_price else 'N/A' }}</td>
                    <td>${{ stats.price_range.min|round(2) if stats.price_range.min else 'N/A' }}</td>
                    <td>${{ stats.price_range.max|round(2) if stats.price_range.max else 'N/A' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        {% if price_analysis.price_ranges %}
        <h2>💰 Price Distribution Analysis</h2>
        <table>
            <thead>
                <tr><th>Price Range</th><th>Count</th><th>Percentage</th></tr>
            </thead>
            <tbody>
                {% for range_name, data in price_analysis.price_ranges.items() %}
                <tr>
                    <td>{{ range_name|title }}</td>
                    <td>{{ data.count }}</td>
                    <td>{{ data.percentage|round(1) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
        
        {% if charts.price_distribution %}
        <h2>💰 Price Distribution Analysis</h2>
        <div class="chart-container">
            <img src="{{ charts.price_distribution }}" alt="Price Distribution Chart">
        </div>
        {% endif %}
        
        {% if charts.source_comparison %}
        <h2>📈 Source Comparison Analysis</h2>
        <div class="chart-container">
            <img src="{{ charts.source_comparison }}" alt="Source Comparison Chart">
        </div>
        {% endif %}
        
        <div class="footer">
            <p>Statistical Report Generated by Advanced Web Scraping Framework</p>
            <p>{{ generated_at }}</p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_html)
        return template.render(**report_data)
    
    def _create_trend_html_report(self, report_data: Dict) -> str:
        """Create HTML report focused on trend analysis."""
        template_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trend Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f8f9fa; }
        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 15px; }
        h2 { color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 8px; margin-top: 30px; }
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .metric-card { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 20px; border-radius: 6px; text-align: center; }
        .metric-value { font-size: 1.8em; font-weight: bold; margin-bottom: 5px; }
        .metric-label { font-size: 0.9em; opacity: 0.9; }
        .chart-container { text-align: center; margin: 15px 0; }
        .chart-container img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 6px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: bold; }
        .footer { text-align: center; margin-top: 30px; color: #6c757d; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 Trend Analysis Report</h1>
        <p style="text-align: center; color: #6c757d;">Generated on {{ generated_at }}</p>
        
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{{ trends.temporal_trends.total_data_points if trends.temporal_trends else 'N/A' }}</div>
                <div class="metric-label">Data Points Analyzed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ trends.temporal_trends.days_with_data if trends.temporal_trends else 'N/A' }}</div>
                <div class="metric-label">Days Tracked</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ trends.temporal_trends.peak_hour if trends.temporal_trends else 'N/A' }}</div>
                <div class="metric-label">Peak Activity Hour</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ source_comparison.source_performance|length if source_comparison.source_performance else 0 }}</div>
                <div class="metric-label">Sources Compared</div>
            </div>
        </div>
        
        {% if charts %}
        <h2>📊 Trend Visualizations</h2>
        {% for chart_path in charts %}
        <div class="chart-container">
            <img src="{{ chart_path }}" alt="Trend Chart">
        </div>
        {% endfor %}
        {% endif %}
        
        {% if source_comparison.source_performance %}
        <h2>🔍 Source Performance Comparison</h2>
        <table>
            <thead>
                <tr><th>Source</th><th>Products</th><th>Avg Price</th><th>Data Completeness</th></tr>
            </thead>
            <tbody>
                {% for source, perf in source_comparison.source_performance.items() %}
                <tr>
                    <td>{{ source }}</td>
                    <td>{{ perf.total_products }}</td>
                    <td>${{ perf.avg_price|round(2) if perf.avg_price else 'N/A' }}</td>
                    <td>{{ perf.data_completeness|round(1) if perf.data_completeness else 'N/A' }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
        
        <div class="footer">
            <p>Trend Analysis Report Generated by Advanced Web Scraping Framework</p>
            <p>{{ generated_at }}</p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_html)
        return template.render(**report_data)
    
    def _create_charts_index(self, charts: Dict[str, str]) -> str:
        """Create an index page for all exported charts."""
        template_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Charts & Visualizations Index</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f8f9fa; }
        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 15px; }
        .chart-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin: 20px 0; }
        .chart-card { border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }
        .chart-card img { width: 100%; height: auto; }
        .chart-title { padding: 15px; background-color: #f8f9fa; font-weight: bold; text-align: center; }
        .footer { text-align: center; margin-top: 30px; color: #6c757d; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Charts & Visualizations</h1>
        <p style="text-align: center; color: #6c757d;">Generated on {{ generated_at }}</p>
        
        <div class="chart-grid">
            {% for chart_name, chart_path in charts.items() %}
            <div class="chart-card">
                <div class="chart-title">{{ chart_name|replace('_', ' ')|title }}</div>
                <img src="{{ chart_path }}" alt="{{ chart_name }}">
            </div>
            {% endfor %}
        </div>
        
        <div class="footer">
            <p>Charts Index Generated by Advanced Web Scraping Framework</p>
            <p>Total Charts: {{ charts|length }}</p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_html)
        return template.render(charts=charts, generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    def _convert_to_relative_path(self, chart_path, report_dir):
        """Copy chart to report directory and return relative path for browser compatibility."""
        import shutil
        from pathlib import Path
        import time
        
        chart_path = Path(chart_path)
        report_dir = Path(report_dir)
        
        target_path = report_dir / chart_path.name
        
        if chart_path.exists() and not target_path.exists():
            try:
                time.sleep(0.1)
                shutil.copy2(chart_path, target_path)
            except PermissionError:
                for attempt in range(3):
                    time.sleep(0.2)
                    try:
                        shutil.copy2(chart_path, target_path)
                        break
                    except PermissionError:
                        if attempt == 2:
                            return str(chart_path)
        
        return chart_path.name