# spiders/base_news_spider.py
import scrapy
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from ..configs.sites_config import SITES_CONFIG
from tanvvtesst.items import ArticleItem, CategoryItem

class BaseNewsSpider(scrapy.Spider):

    def __init__(self, site_name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not site_name:
            raise ValueError("site_name is required")
        self.site_name = site_name
        self.config = SITES_CONFIG[site_name]
        self.allowed_domains = self.config['allowed_domains']
        self.start_urls = self.config['start_urls']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse_categories)

    def parse_categories(self, response):
        # Implementation mặc định dùng xpath từ config
        xpath = self.config['xpath']['categories']
        categories = response.xpath(xpath['main_menu'])
        for category in categories:
            name = category.xpath(xpath['category_name']).get().strip()
            url = category.xpath(xpath['category_url']).get()
            if url and not url.startswith(('#', 'javascript:')):
                url = urljoin(response.url, url)
                yield self.create_category_item({'name': name, 'url': url})
                yield self.get_article_list_request({
                            'name': name,
                            'url': url
                        })
                
    def get_article_list_request(self, category):
        return scrapy.Request(
            url=category['url'],
            callback=self.parse_article_list,
            meta={
                'category_name': category['name'],
                'page': 1
            }
        )

    def parse_article_list(self, response):
        # Implementation mặc định
        xpath = self.config['xpath']['article_list']
        articles = response.xpath(xpath['articles'])
        for article in articles:
            url = article.xpath(xpath['article_url']).get()
            if url and not url.startswith(('#', 'javascript:')):
                url = urljoin(response.url, url)
                
                yield scrapy.Request(url, callback=self.parse_article_detail)
        
        next_page = self.get_next_page(response)
        
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse_article_list)

    def parse_article_detail(self, response):
        xpath = self.config['xpath']['article']
        yield self.create_article_item({
            'title': response.xpath(xpath['title']).get(),
            'description': response.xpath(xpath['description']).get(),
            'content': response.xpath(xpath['content']).get(),
            'date': response.xpath(xpath['date']).get(),
            'author': response.xpath(xpath['author']).get()
        })

    def get_next_page(self, response):
        
        return None
    
    def create_category_item(self, category):
        category_item = CategoryItem()
        category_item['category_name'] = category['name']
        category_item['category_url'] = category['url']
        category_item['created'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        category_item['updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return category_item
    
    def create_article_item(self, article):
        item = ArticleItem()
        item['title'] = article['title']
        item['description'] = article['description']
        item['post_content'] = article['content']
        item['post_created'] = article['date']
        item['author'] = article['author']
        item['time_crawler'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        return item

class ThanhNienDBSpider(BaseNewsSpider):
    name = 'thanhnien_spider'
    def __init__(self, *args, **kwargs):
        super().__init__(site_name='thanhnien', *args, **kwargs)

    def start_requests(self):
        # Gọi danh sách chuyên mục từ DB
        for category in self.get_categories_from_db():
            yield self.get_article_list_request(category)

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
            table_name = 'web_categories'
            
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


class VNEpressSpider(BaseNewsSpider):
    name = 'vnexpress_spider'
    def __init__(self, *args, **kwargs):
        super().__init__(site_name='vnexpress', *args, **kwargs)

