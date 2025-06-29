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
        'link': 'h3 a',
        'image': 'img',
        'availability': 'p.instock.availability'
    }
}

