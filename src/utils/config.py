# Enhanced static scraper configuration
static_config = {
    'name': 'BooksToScrape',
    'base_url': 'http://books.toscrape.com/catalogue/page-{}.html',
    'start_page': 1,
    'max_pages': 3,
    'delay_range': (1, 2),
    'selectors': {
        'container': 'article.product_pod',
        'name': 'h3 a',
        'price': 'p.price_color',
        'availability': 'p.instock.availability',
        'link': 'h3 a',
        'image': 'div.image_container img'
    }
}

# Cross-platform ChromeDriver configuration
def get_chromedriver_config():
    """Get platform-specific ChromeDriver configuration."""
    import platform
    import shutil
    import os
    
    system = platform.system().lower()
    
    config = {
        'headless': True,  # Default to headless for better compatibility
        'timeout': 10,
        'options': []
    }
    
    # Linux-specific configuration
    if system == 'linux':
        config.update({
            'headless': True,  # Force headless on Linux
            'options': [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--disable-gpu',
                '--no-first-run',
                '--disable-default-apps'
            ]
        })
    
    # Try to detect ChromeDriver path
    chromedriver_cmd = 'chromedriver.exe' if system == 'windows' else 'chromedriver'
    chromedriver_path = shutil.which(chromedriver_cmd)
    
    if chromedriver_path:
        config['chromedriver_path'] = chromedriver_path
    else:
        # Platform-specific fallback paths
        fallback_paths = {
            'linux': ['/usr/bin/chromedriver', '/usr/local/bin/chromedriver'],
            'darwin': ['/usr/local/bin/chromedriver', '/opt/homebrew/bin/chromedriver'],
            'windows': ['./chromedriver.exe']
        }
        
        for path in fallback_paths.get(system, []):
            if os.path.exists(path):
                config['chromedriver_path'] = path
                break
    
    return config

