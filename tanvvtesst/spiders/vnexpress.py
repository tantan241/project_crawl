import scrapy
from datetime import datetime
from tanvvtesst.items import ArticleItem


class VnexpressSpider(scrapy.Spider):
    name = "vnexpress"
    allowed_domains = ["vnexpress.net"]
    start_urls = ["https://vnexpress.net/my-trung-quoc-dung-ap-thue-90-ngay-4884780.html"]

    def parse(self, response):
        item = ArticleItem()
        item['title'] = response.xpath('//h1[@class="title-detail"]/text()').get()
        item['description'] = response.xpath('//p[@class="description"]/text()').get()
        item['post_content'] = ' '.join(response.xpath('//article[@class="fck_detail"]//p/text()').getall())
        item['post_created'] = response.xpath('//span[@class="date"]/text()').get()
        item['time_crawler'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        item['author'] = response.xpath('//p[@class="Normal"][last()]/strong/text()').get()
        return item
