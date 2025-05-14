# configs/sites_config.py
SITES_CONFIG = {
    'vnexpress': {
        'allowed_domains': ['vnexpress.net'],
        'start_urls': ['https://vnexpress.net'],
        'pagination': {
            'type': 'xpath',
            'xpath': '//a[contains(@class, "btn-page next-page") or contains(@class, "next-page")]/@href'
        },
        'xpath': {
            'categories': {
                'main_menu': '//nav[@class="main-nav"]/ul[@class="parent"]/li/a',
                'category_name': 'text()',
                'category_url': '@href',
                'sub_categories': '//ul[class="ul-nav-folder"]/li/h1/a',
                'sub_category_name': '@title',
                'sub_category_url': '@href'
            },
            'article_list': {
                'articles': '//article[contains(@class, "item-news")]',
                'article_url': './/a[1]/@href',
                'article_title': '//a[1]/text()'
            },
            'article': {
                'title': '//h1[@class="title-detail"]/text()',
                'description_no_text': '//p[@class="description"]',
                'description': '//p[@class="description"]/text()',
                'content': '//article[@class="fck_detail"]',
                'date': '//span[@class="date"]/text()',
                'author': '//p[@class="Normal"][last()]/strong/text()'
            }
        }
    },
    'thanhnien': {
        'allowed_domains': ['thanhnien.vn'],
        'start_urls': ['https://thanhnien.vn'],
        'get_categories_from_db': True,  
        'category_table': 'web_categories',  
        'pagination': {
            'type': 'thanhnien',
            'xpath_id_cate': '//input[@id="hdZoneId"]/@value'
        },
        'xpath': {
            'categories': {
                'main_menu': '//ul[@class="menu-nav"]/li/a',
                'category_name': 'text()',
                'category_url': '@href',
                'sub_categories': '//div[class="sub-menu"]/div/div/div/a',
                'sub_category_name': '@title',
                'sub_category_url': '@href'
            },
            'article_list': {
                'articles': '//div[contains(@class, "box-category-item")]',
                'article_url': './/a[1]/@href',
                'article_title': '//a[1]/text()'
            },
            'article': {
                'title': '//h1[@class="detail-title"]/span/text()',
                'description_no_text': '//meta[@name="description"]',
                'description': '//meta[@name="description"]/@content',
                'content': '//div[contains(@class, "detail-content")]',
                'date': '//div[@class="detail-time"]/div/text()',
                'author': '//div[@class="author-info"][1]/div/a/text()'
            }
        }
    }
}