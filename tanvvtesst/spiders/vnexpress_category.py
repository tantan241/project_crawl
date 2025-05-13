import scrapy
import mysql.connector
from datetime import datetime
from urllib.parse import urljoin
import json
import logging

class VnexpressCategorySpider(scrapy.Spider):
    name = "vnexpress_category"
    allowed_domains = ["vnexpress.net"]
    
    custom_settings = {
        'ITEM_PIPELINES': {
            'tanvvtesst.pipelines.MySQLPipeline': 300,
            'tanvvtesst.pipelines.RabbitMQPipeline': 400,
        }
    }
    
    def __init__(self, *args, **kwargs):
        super(VnexpressCategorySpider, self).__init__(*args, **kwargs)
        # Kết nối MySQL
        self.conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root_password',
            database='test'
        )
        self.cursor = self.conn.cursor(dictionary=True)
    
    def start_requests(self):
        # Đọc danh sách danh mục từ database
        self.cursor.execute("SELECT * FROM web_categories")
        categories = self.cursor.fetchall()
        
        for category in categories:
            self.logger.info(f"Bắt đầu crawl danh mục: {category['category_name']} - {category['category_url']}")
            yield scrapy.Request(
                url=category['category_url'],
                callback=self.parse_category,
                meta={'category': category}
            )
    
    def parse_category(self, response):
        category = response.meta['category']
        
        # Lấy danh sách bài viết trong trang đầu tiên
        articles = response.xpath('//article[contains(@class, "item-news")]')
        self.logger.info(f"Tìm thấy {len(articles)} bài viết trong danh mục {category['category_name']}")
        
        for article in articles:
            article_url = article.xpath('.//a[1]/@href').get()
            if article_url:
                article_url = urljoin(response.url, article_url)
                self.logger.info(f"Tìm thấy bài viết: {article_url}")
                
                yield scrapy.Request(
                    url=article_url,
                    callback=self.parse_article,
                    meta={
                        'category': category,
                        'article_url': article_url
                    }
                )
    
    def parse_article(self, response):
        category = response.meta['category']
        article_url = response.meta['article_url']
        
        # Thu thập thông tin bài viết
        article_data = {
            'url': article_url,
            'category_id': category['id'],
            'category_name': category['category_name'],
            'title': response.xpath('//h1[@class="title-detail"]/text()').get(),
            'description': response.xpath('//p[@class="description"]/text()').get(),
            'author': response.xpath('//p[@class="Normal"][last()]/strong/text()').get(),
            'post_created': response.xpath('//span[@class="date"]/text()').get(),
            'time_crawler': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Lấy nội dung HTML của bài viết
        content_parts = []
        description = response.xpath('//p[@class="description"]').get()
        if description:
            content_parts.append(description)
        
        main_content = response.xpath('//article[@class="fck_detail"]').get()
        if main_content:
            content_parts.append(main_content)
        
        article_data['post_content'] = '\n'.join(content_parts) if content_parts else ''
        
        # Gửi dữ liệu vào pipeline để xử lý
        yield {
            'type': 'only_insert_queue',
            'article': True,
            'data': article_data
        }
    
    def closed(self, reason):
        # Đóng kết nối MySQL khi spider kết thúc
        if self.conn:
            self.conn.close() 