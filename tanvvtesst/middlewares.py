# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import redis
from scrapy.exceptions import DropItem
import hashlib
import random
from scrapy.item import Item 

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class TanvvtesstSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # maching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class TanvvtesstDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

class CustomProxyAndUserAgentMiddleware:
    def __init__(self):
        # Danh sách proxy (có thể có user:pass hoặc không)
        self.proxies = [
            'http://113.160.132.195:8000', #VN
            # 'http://47.236.224.32:8080', #SING
        ]

        # Danh sách user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/90.0.4430.212 Safari/537.36',
        ]

    def process_request(self, request, spider):
        # Gán random user-agent
        user_agent = random.choice(self.user_agents)
        request.headers['User-Agent'] = user_agent

        # Gán random proxy
        # proxy = random.choice(self.proxies)
        # request.meta['proxy'] = proxy
class RedisDeduplicationMiddleware:
    def __init__(self, redis_host, redis_port, redis_db, redis_key_prefix, redis_expire_time):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        self.redis_key_prefix = redis_key_prefix
        self.redis_expire_time = redis_expire_time

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            redis_host=crawler.settings.get('REDIS_HOST', 'localhost'),
            redis_port=crawler.settings.get('REDIS_PORT', 6379),
            redis_db=crawler.settings.get('REDIS_DB', 0),
            redis_key_prefix=crawler.settings.get('REDIS_KEY_PREFIX', 'scrapy:'),
            redis_expire_time=crawler.settings.get('REDIS_EXPIRE_TIME', 86400)
        )

    def process_spider_output(self, response, result, spider):
        for item in result:
            if isinstance(item, (dict, Item)):  # Nếu là item (không phải Request)
                if not self._is_duplicate(item, spider):
                    # Nếu không trùng thì yield item
                    yield item
                else:
                    # Log lại item bị trùng
                    spider.logger.info(f"Duplicate item found - Site: {spider.site_name}, title: {item.get('title', '')}")
            else:
                yield item  #

    def _is_duplicate(self, item, spider):
        key = self._generate_key(item, spider)
        
        # Nếu key đã tồn tại
        if self.redis_client.get(key):
            spider.logger.debug(f"Duplicate item found: {key}")
            return True
            
        # Nếu key chưa tồn tại, set key với expire time
        self.redis_client.setex(key, self.redis_expire_time, 1)
        return False

    def _generate_key(self, item, spider):
        site_name = spider.site_name
        
        unique_id =  item.get('category_url', '') or item.get('title', '') 
        
        hashed_id = hashlib.md5(unique_id.encode()).hexdigest()
         # Tạo key theo format: prefix:site_name:hashed_id
        key = f"{self.redis_key_prefix}:{site_name}:{hashed_id}"
        
        return key