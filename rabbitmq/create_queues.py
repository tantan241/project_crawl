import pika

def create_queues():
    try:
        # Kết nối đến RabbitMQ
        credentials = pika.PlainCredentials('guest', 'guest')
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='localhost',
                port=5672,
                credentials=credentials
            )
        )
        
        # Tạo channel
        channel = connection.channel()
        
        # Tạo queue ifollow_banking
        channel.queue_declare(
            queue='ifollow_banking',
            durable=True,  # Queue sẽ tồn tại sau khi restart RabbitMQ
            arguments={
                'x-message-ttl': 86400000,  # TTL 24 giờ (tính bằng milliseconds)
                'x-max-length': 1000000  # Giới hạn số lượng message trong queue
            }
        )
        print("Đã tạo queue 'ifollow_banking' thành công!")
        
        # Tạo queue ifollow_tele
        channel.queue_declare(
            queue='ifollow_tele',
            durable=True,  # Queue sẽ tồn tại sau khi restart RabbitMQ
            arguments={
                'x-message-ttl': 86400000,  # TTL 24 giờ
                'x-max-length': 1000000  # Giới hạn số lượng message
            }
        )
        print("Đã tạo queue 'ifollow_tele' thành công!")
        
        # Đóng kết nối
        connection.close()
        print("\nĐã tạo các queue thành công!")
        
    except Exception as e:
        print(f"Lỗi: {str(e)}")

if __name__ == '__main__':
    create_queues() 