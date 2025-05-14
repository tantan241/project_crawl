# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import mysql.connector
from scrapy.exceptions import NotConfigured
import scrapy
import logging
from tanvvtesst.items import ArticleItem, CategoryItem
import pika
import json

logger = logging.getLogger(__name__)

class MySQLPipeline:
    def __init__(self, mysql_host, mysql_user, mysql_password, mysql_database, mysql_port):
        self.mysql_host = mysql_host
        self.mysql_user = mysql_user
        self.mysql_password = mysql_password
        self.mysql_database = mysql_database
        self.mysql_port = mysql_port
        self.conn = None
        self.cur = None
        self.item_count = 0

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mysql_host=crawler.settings.get('MYSQL_HOST', 'localhost'),
            mysql_user=crawler.settings.get('MYSQL_USER', 'root'),
            mysql_password=crawler.settings.get('MYSQL_PASSWORD', 'root_password'),
            mysql_database=crawler.settings.get('MYSQL_DATABASE', 'test'),
            mysql_port=crawler.settings.get('MYSQL_PORT', 3306)
        )

    def open_spider(self, spider):
        logger.info("Đang mở kết nối MySQL...")
        try:
            self.conn = mysql.connector.connect(
                host=self.mysql_host,
                user=self.mysql_user,
                password=self.mysql_password,
                database=self.mysql_database,
                port=self.mysql_port
            )
            self.cur = self.conn.cursor()
            logger.info("Đã kết nối thành công đến MySQL!")
        except mysql.connector.Error as err:
            logger.error(f"Lỗi kết nối MySQL: {err}")
            raise

    def process_item(self, item, spider):
        # logger.error(f"TANVV {item}")
        self.item_count += 1
        if item.get('type') == 'only_insert_queue':
            return item
        if isinstance(item, dict) and item.get('type') == 'article':
            return self.process_article_dict(item['data'], spider)
        elif isinstance(item, CategoryItem):
            return self.process_category(item)
        elif isinstance(item, ArticleItem):
            return self.process_article(item)
        return item

    def process_category(self, item):
      
        try:
            sql = """
                INSERT INTO web_categories 
                (category_url, category_name, created, updated)
                VALUES (%s, %s, %s, %s)
            """
            values = (
                item['category_url'],
                item['category_name'],
                item['created'],
                item['updated']
            )

            self.cur.execute(sql, values)
            self.conn.commit()
            
            logger.info(f"Đã lưu category {item['category_name']} vào database")
        except mysql.connector.Error as err:
            logger.error(f"Lỗi khi lưu category: {err}")
            self.conn.rollback()
        return item

    def process_article(self, item):
        logger.info(f"Đang xử lý article: {item['title']}")
        try:
            sql = """
                INSERT INTO web_posts 
                (title, description, post_content, post_created, time_crawler, author)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (
                item['title'],
                item['description'],
                item['post_content'],
                item['post_created'],
                item['time_crawler'],
                item['author']
            )

            self.cur.execute(sql, values)
            self.conn.commit()
            
            logger.info(f"Đã lưu article {item['title']} vào database")
        except mysql.connector.Error as err:
            logger.error(f"Lỗi khi lưu article: {err}")
            self.conn.rollback()
        return item

    def process_article_dict(self, item, spider):
        logger.info(f"Đang xử lý article từ dict: {item['title']}")
        try:
            sql = """
                INSERT INTO web_posts 
                (title, description, post_content, post_created, time_crawler, author)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (
                item['title'],
                item['description'],
                item['post_content'],
                item['post_created'],
                item['time_crawler'],
                item['author']
            )

            self.cur.execute(sql, values)
            self.conn.commit()
            
            logger.info(f"Đã lưu article {item['title']} vào database")
        except mysql.connector.Error as err:
            logger.error(f"Lỗi khi lưu article: {err}")
            self.conn.rollback()
        return item

    def close_spider(self, spider):
        logger.info(f"Spider kết thúc. Đã xử lý tổng cộng {self.item_count} items")
        logger.info("Đang đóng kết nối MySQL...")
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        logger.info("Đã đóng kết nối MySQL!")

class RabbitMQPipeline:
    def __init__(self, rabbitmq_host, rabbitmq_port, rabbitmq_user, rabbitmq_password):
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_port = rabbitmq_port
        self.rabbitmq_user = rabbitmq_user
        self.rabbitmq_password = rabbitmq_password
        self.connection = None
        self.channel = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            rabbitmq_host=crawler.settings.get('RABBITMQ_HOST'),
            rabbitmq_port=crawler.settings.get('RABBITMQ_PORT'),
            rabbitmq_user=crawler.settings.get('RABBITMQ_USER'),
            rabbitmq_password=crawler.settings.get('RABBITMQ_PASSWORD')
        )
        
    def open_spider(self, spider):
        try:
            # Kết nối đến RabbitMQ
            credentials = pika.PlainCredentials(self.rabbitmq_user, self.rabbitmq_password)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.rabbitmq_host,
                    port=self.rabbitmq_port,
                    credentials=credentials
                )
            )
            self.channel = self.connection.channel()
            
            # Đảm bảo các queue tồn tại với cấu hình giống nhau
            queue_args = {
                'x-message-ttl': 86400000,  # TTL 24 giờ (tính bằng milliseconds)
                'x-max-length': 1000000  # Giới hạn số lượng message trong queue
            }
            
            self.channel.queue_declare(
                queue='ifollow_banking',
                durable=True,
                arguments=queue_args
            )
            self.channel.queue_declare(
                queue='ifollow_tele',
                durable=True,
                arguments=queue_args
            )
            
            logger.info("Đã kết nối thành công đến RabbitMQ!")
        except Exception as e:
            logger.error(f"Lỗi khi kết nối đến RabbitMQ: {str(e)}")
            raise
        
    def close_spider(self, spider):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Đã đóng kết nối RabbitMQ!")
            
    def process_item(self, item, spider):
        logger.info(f"TANVV-log-item : {item}")
        try:
            if isinstance(item, dict) and item.get('article'):
                # Chuyển đổi dữ liệu thành JSON
                message = json.dumps(item['data'], ensure_ascii=False)
                
                # Gửi message vào cả 2 queue
                for queue in ['ifollow_banking', 'ifollow_tele']:
                    self.channel.basic_publish(
                        exchange='',
                        routing_key=queue,
                        body=message.encode('utf-8'),
                        properties=pika.BasicProperties(
                            delivery_mode=2,  # Message sẽ được lưu trữ
                            content_type='application/json',
                            content_encoding='utf-8'
                        )
                    )
                   
                
        except Exception as e:
            logger.error(f"Lỗi khi gửi message vào RabbitMQ: {str(e)}")
            
        return item
