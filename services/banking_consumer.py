import pika
import json
import mysql.connector
from elasticsearch import Elasticsearch
import logging
from datetime import datetime
import time
import os
import sys

# Cấu hình logging với encoding UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/banking_consumer.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  # Sử dụng stdout với encoding mặc định là utf-8
    ]
)
logger = logging.getLogger(__name__)

class BankingConsumer:
    def __init__(self):
        # Khởi tạo kết nối MySQL
        self.mysql_conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', 'root_password'),
            database=os.getenv('MYSQL_DATABASE', 'test')
        )
        self.mysql_cursor = self.mysql_conn.cursor()

        # Khởi tạo kết nối Elasticsearch với scheme
        es_host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
        es_port = int(os.getenv('ELASTICSEARCH_PORT', 9200))
        self.es = Elasticsearch(
            hosts=[{
                'host': es_host,
                'port': es_port,
                'scheme': 'http'
            }]
        )

        # Khởi tạo kết nối RabbitMQ
        credentials = pika.PlainCredentials(
            os.getenv('RABBITMQ_USER', 'guest'),
            os.getenv('RABBITMQ_PASSWORD', 'guest')
        )
        self.rabbitmq_conn = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv('RABBITMQ_HOST', 'localhost'),
                port=int(os.getenv('RABBITMQ_PORT', 5672)),
                credentials=credentials
            )
        )
        self.channel = self.rabbitmq_conn.channel()

    def save_to_mysql(self, data):  
        article_data = data   
        try:
            article_data = data
            sql = """
                INSERT INTO web_posts 
                (title, description, post_content, post_created, time_crawler, author)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (
                article_data['title'],
                article_data['description'],
                article_data['post_content'],
                article_data['post_created'],
                article_data['time_crawler'],
                article_data['author']
            )

            self.mysql_cursor.execute(sql, values)
            self.mysql_conn.commit()
            logger.info(f"Đã lưu bài viết '{article_data['title']}' vào MySQL")
            return self.mysql_cursor.lastrowid
        except Exception as e:
            logger.error(f"Lỗi khi lưu vào MySQL: {str(e)}")
            self.mysql_conn.rollback()
            raise

    def save_to_elasticsearch(self, data, mysql_id):
        try:
            
            article_data = data
           
            doc = {
                'mysql_id': mysql_id,
                'title': article_data['title'],
                'description': article_data['description'],
                'content': article_data['post_content'],
                'author': article_data['author'],
                'post_created': article_data['post_created'],
                'time_crawler': article_data['time_crawler'],
                'category_name': article_data['category_name'],
                'url': article_data['url'],
                'indexed_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            result = self.es.index(index='website', document=doc)
            logger.info(f"Đã lưu bài viết '{article_data['title']}' vào Elasticsearch")
            return result['_id']
        except Exception as e:
            logger.error(f"Lỗi khi lưu vào Elasticsearch: {str(e)}")
            raise

    def process_message(self, ch, method, properties, body):
        try:
            # Decode và parse JSON message
            data = json.loads(body.decode('utf-8'))
            title = data['title'] if data['title'] and data['title'] != 'None' and data['title'] != 'null' else ''
            data['title'] = title
          
            if title:
                # Lưu vào MySQL
                mysql_id = self.save_to_mysql(data)

                # Lưu vào Elasticsearch
                es_id = self.save_to_elasticsearch(data, mysql_id)

                # Xác nhận đã xử lý message
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
                logger.info(f"Đã xử lý xong bài viết. MySQL ID: {mysql_id}, ES ID: {es_id}")
        except Exception as e:
            logger.error(f"Lỗi khi xử lý message: {str(e)}")
            # Từ chối message và đẩy lại vào queue để xử lý lại sau
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self):
        try:
            # Đảm bảo queue tồn tại
            self.channel.queue_declare(
                queue='ifollow_banking',
                durable=True,
                arguments={
                    'x-message-ttl': 86400000,
                    'x-max-length': 1000000
                }
            )

            # Chỉ xử lý 1 message tại một thời điểm
            self.channel.basic_qos(prefetch_count=1)

            # Bắt đầu consume
            self.channel.basic_consume(
                queue='ifollow_banking',
                on_message_callback=self.process_message
            )

            logger.info("Bắt đầu lắng nghe queue ifollow_banking...")
            self.channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("Đã nhận tín hiệu dừng service...")
        except Exception as e:
            logger.error(f"Lỗi không mong muốn: {str(e)}")
        finally:
            self.cleanup()

    def cleanup(self):
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.rabbitmq_conn and not self.rabbitmq_conn.is_closed:
                self.rabbitmq_conn.close()
            if self.mysql_cursor:
                self.mysql_cursor.close()
            if self.mysql_conn:
                self.mysql_conn.close()
            logger.info("Đã đóng tất cả kết nối")
        except Exception as e:
            logger.error(f"Lỗi khi đóng kết nối: {str(e)}")

if __name__ == "__main__":
    # Cấu hình encoding cho stdout
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    
    # Tạo thư mục logs nếu chưa tồn tại
    os.makedirs('logs', exist_ok=True)
    
    while True:
        try:
            consumer = BankingConsumer()
            consumer.start_consuming()
        except Exception as e:
            logger.error(f"Service gặp lỗi: {str(e)}")
            logger.info("Thử kết nối lại sau 5 giây...")
            time.sleep(5) 