import scrapy
from tanvvtesst.items import VnExpressItem, VnExpressCategoryItem
from datetime import datetime
from urllib.parse import urljoin
import logging


class Vnexpress2Spider(scrapy.Spider):
    name = "vnexpress2"
    allowed_domains = ["vnexpress.net"]
    start_urls = ["https://vnexpress.net"]

    def parse(self, response):
        main_categories = response.xpath('//nav[@class="main-nav"]/ul[@class="parent"]/li/a')
        self.logger.info(f"Tổng số category chính: {len(main_categories)}")
        
        for category in main_categories:
            category_name = category.xpath('text()').get().strip()
            category_url = category.xpath('@href').get()
            
            if category_url and not category_url.startswith(('#', 'javascript:')):
                category_url = urljoin(response.url, category_url)
                
                # Tạo category item
                category_item = VnExpressCategoryItem()
                category_item['category_name'] = category_name
                category_item['category_url'] = category_url
                category_item['created'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                category_item['updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                self.logger.info(f"Đã tìm thấy category: {category_name} - {category_url}")
                yield category_item
                
                # Crawl trang danh sách bài viết của category
                yield scrapy.Request(
                    url=category_url,
                    callback=self.parse_article_list,
                    meta={'category_name': category_name, 'has_sub_cate': True}
                )

    def parse_article_list(self, response):
        """Parse trang danh sách bài viết của category"""
        category_name = response.meta['category_name']
        has_sub_cate = response.meta.get('has_sub_cate')

        if has_sub_cate:
            sub_cate_list = response.xpath('//ul[class="ul-nav-folder"]/li/h1/a')
            for sub_cate_it in sub_cate_list:
                sub_cate_url = 'https://vnexpress.net' + '/' + sub_cate_it.xpath('@href').get()
                sub_cate_name = sub_cate_it.xpath('@title').get()
                category_item = VnExpressCategoryItem()
                category_item['category_name'] = sub_cate_name
                category_item['category_url'] = sub_cate_url
                category_item['created'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                category_item['updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                yield category_item
                
                # Crawl trang danh sách bài viết của category
                yield scrapy.Request(
                    url=sub_cate_url,
                    callback=self.parse_article_list,
                    meta={'category_name': category_name, 'has_sub_cate': False}
                )

        self.logger.info(f"Đang parse danh sách bài viết của category: {category_name}")
        
        # Lấy tất cả các article trong trang hiện tại
        articles = response.xpath('//article[contains(@class, "item-news")]')
        self.logger.info(f"Tìm thấy {len(articles)} bài viết trong trang")
        
        for article in articles:
            # Lấy URL của bài viết
            article_url = article.xpath('.//a[1]/@href').get()
            if article_url:
                article_url = urljoin(response.url, article_url)
                # Lấy tiêu đề để log
                article_title = article.xpath('//a[1]/text()').get().strip()
                self.logger.info(f"Tìm thấy bài viết: {article_title}")
                
                # Request chi tiết bài viết
                yield scrapy.Request(
                    url=article_url,
                    callback=self.parse_article_detail,
                    meta={
                        'category_name': category_name,
                        'article_url': article_url
                    }
                )
        
        # Xử lý phân trang - tìm nút "Xem thêm" hoặc trang tiếp theo
        next_page = response.xpath('//a[contains(@class, "btn-page next-page") or contains(@class, "next-page")]/@href').get()
        if next_page:
            next_page_url = urljoin(response.url, next_page)
            self.logger.info(f"Tìm thấy trang tiếp theo: {next_page_url}")
            
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse_article_list,
                meta={'category_name': category_name}
            )

    def parse_article_detail(self, response):
        """Parse chi tiết một bài viết"""
        category_name = response.meta['category_name']
        article_url = response.meta['article_url']
        
        self.logger.info(f"Đang parse chi tiết bài viết: {article_url}")
        
        item = VnExpressItem()
        
        # Lấy tiêu đề và mô tả
        item['title'] = response.xpath('//h1[@class="title-detail"]/text()').get()
        item['description'] = response.xpath('//p[@class="description"]/text()').get()
        
        # Lấy toàn bộ nội dung HTML của bài viết
        content_parts = []
        
        # Lấy description đầu tiên
        description = response.xpath('//p[@class="description"]').get()
        if description:
            content_parts.append(description)
        
        # Lấy nội dung chính với đầy đủ HTML
        main_content = response.xpath('//article[@class="fck_detail"]').get()
        if main_content:
            content_parts.append(main_content)
            
        # Ghép nội dung lại
        item['post_content'] = '\n'.join(content_parts) if content_parts else ''
        
        # Lấy các thông tin khác
        item['post_created'] = response.xpath('//span[@class="date"]/text()').get()
        item['time_crawler'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        item['author'] = response.xpath('//p[@class="Normal"][last()]/strong/text()').get()
        
        if item['title']:
            self.logger.info(f"Đã parse xong bài viết: {item['title']}")
            yield item
        else:
            self.logger.warning(f"Không parse được bài viết: {article_url}")
