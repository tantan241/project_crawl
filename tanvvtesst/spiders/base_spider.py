# spiders/base_news_spider.py
import scrapy
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from ..configs.sites_config import SITES_CONFIG
from tanvvtesst.items import VnExpressItem, VnExpressCategoryItem

class BaseNewsSpider(scrapy.Spider):
    name = "base_spider"
    def __init__(self, site_name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not site_name:
            raise ValueError("site_name is required")
        self.site_name = site_name
        self.config = SITES_CONFIG[site_name]
        self.allowed_domains = self.config['allowed_domains']
        self.start_urls = self.config['start_urls']
        self.xpath = self.config['xpath']

    def start_requests(self):
        if self.config.get('get_categories_from_db', False):
        # Lấy categories từ DB
            categories = self.get_categories_from_db()
            for category in categories:
                yield scrapy.Request(
                    url=category['url'],
                    callback=self.parse_article_list,
                    meta={
                        'category_name': category['name'],
                        'has_sub_cate': True,
                        'page': 1
                    }
                )
        else:
            # Giữ nguyên code cũ parse từ trang
            for url in self.start_urls:
                yield scrapy.Request(url, callback=self.parse_categories)
    def get_categories_from_db(self):
        import mysql.connector
        from mysql.connector import pooling
        
        try:
            connection = mysql.connector.connect(
                host=self.crawler.settings.get('MYSQL_HOST'),
                database=self.crawler.settings.get('MYSQL_DATABASE'),
                user=self.crawler.settings.get('MYSQL_USER'),
                password=self.crawler.settings.get('MYSQL_PASSWORD')
            )
            
            cursor = connection.cursor(dictionary=True)
            table_name = self.config.get('category_table')
            
            cursor.execute(f"SELECT category_name as name, category_url as url FROM {table_name} ")
            categories = cursor.fetchall()
            return categories
            
        except Exception as e:
            self.logger.error(f"Error getting categories from DB: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()

    def parse_categories(self, response):
        ua = response.request.headers.get('User-Agent').decode()
        self.logger.info(f"User-Agent đang dùng: {ua}")
        self.logger.info(f"TANVV-parse_categories_meta: {response.meta}")
        
        xpath = self.xpath['categories']
        main_categories = response.xpath(xpath['main_menu'])
        
        for category in main_categories:
            category_name = category.xpath(xpath['category_name']).get().strip()
            category_url = category.xpath(xpath['category_url']).get()
            
            if category_url and not category_url.startswith(('#', 'javascript:')):
                category_url = urljoin(response.url, category_url)
                yield self.create_category_item(category_name, category_url)
                
                yield scrapy.Request(
                    url=category_url,
                    callback=self.parse_article_list,
                    meta={
                        'category_name': category_name, 
                        'has_sub_cate': True,
                        'page': 1
                    }
                )

    def get_next_page(self, response):
        pagination_config = self.config.get('pagination', {})
        page_type = pagination_config.get('type')
        url = ''
        
        if page_type == 'xpath':
            url = self.handle_get_url_next_page_xpath(response, pagination_config)
        elif page_type == 'thanhnien':
            page = response.meta.get('page')
            if page:
                url = self.handle_get_url_next_page_thanh_nien(response, pagination_config, page)
        if url:
            return url
        return None

    def handle_get_url_next_page_xpath(self, response, config):
        next_url = response.xpath(config['xpath']).get()
        if next_url:
            return urljoin(response.url, next_url)
        else:
            return None
    def handle_get_url_next_page_thanh_nien(self, response, config,page):
        # https://thanhnien.vn/timelinelist/18549/2.htm
        current_url = response.url
        xpath_id_cate = response.xpath(config['xpath_id_cate']).get()
        self.logger.info(f"TANVV-handle_get_url_next_page_thanh_nien: {page}")
        if xpath_id_cate:
            return self.start_urls[0] + '/timelinelist/' + xpath_id_cate + f'/{page}.htm'
        
        return None

    def add_page_param(self, url, param, value):
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        params[param] = [str(value)]
        parsed = parsed._replace(query=urlencode(params, doseq=True))
        return parsed.geturl()

    def parse_article_list(self, response):
        xpath = self.xpath['article_list']
        articles = response.xpath(xpath['articles'])
        
        for article in articles:
            article_url = article.xpath(xpath['article_url']).get()
            
            if article_url:
                if article_url.startswith(('javascript:', '#')):
                    continue
                article_url = urljoin(response.url, article_url)
                
                yield scrapy.Request(
                    url=article_url,
                    callback=self.parse_article_detail,
                    meta=response.meta
                )
        
        # Xử lý next page động
        
        next_page = self.get_next_page(response)
        self.logger.info(f"TANVV-parse-article-list: {next_page}")
        if next_page:
            yield scrapy.Request(
                url=next_page,
                callback=self.parse_article_list,
                meta={
                    **response.meta,
                    'page': response.meta.get('page', 1) + 1
                }
            )

    def parse_article_detail(self, response):
        
        xpath = self.xpath['article']
        return self.create_article_item(response, xpath)

    def create_category_item(self, name, url):
        category_item = VnExpressCategoryItem()
        category_item['category_name'] = name
        category_item['category_url'] = url
        category_item['created'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        category_item['updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return category_item

    def create_article_item(self, response, xpath):
        
        item = VnExpressItem()
        
        item['title'] = response.xpath(xpath['title']).get()
        item['description'] = response.xpath(xpath['description']).get()
        
        content_parts = []
        
        main_content = response.xpath(xpath['content']).get()
        if main_content:
            content_parts.append(main_content)
            
        item['post_content'] = main_content if main_content else ''
        
        item['post_created'] = response.xpath(xpath['date']).get()
        item['time_crawler'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        item['author'] = response.xpath(xpath['author']).get()
        
        if item['title']:
            self.logger.info(f"Đã parse xong bài viết: {item['title']}")
            return item