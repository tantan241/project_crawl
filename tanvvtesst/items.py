# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ArticleItem(scrapy.Item):
    title = scrapy.Field()
    description = scrapy.Field()
    post_content = scrapy.Field()
    post_created = scrapy.Field()
    time_crawler = scrapy.Field()
    author = scrapy.Field()
    category_id = scrapy.Field()  # FK tới bảng category

class CategoryItem(scrapy.Item):
    id = scrapy.Field()
    category_url = scrapy.Field()
    category_name = scrapy.Field()
    created = scrapy.Field()
    updated = scrapy.Field()
