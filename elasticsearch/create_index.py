from elasticsearch import Elasticsearch
import json

def create_website_index():
    # Kết nối đến Elasticsearch trong Docker
    es = Elasticsearch(['http://localhost:9200'])
    
    try:
        # Kiểm tra kết nối
        if not es.ping():
            raise Exception("Không thể kết nối đến Elasticsearch")
            
        # Đọc file mapping
        with open('elasticsearch/website_mapping.json', 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        
        # Kiểm tra xem index đã tồn tại chưa
        if es.indices.exists(index='website'):
            print("Index 'website' đã tồn tại. Xóa index cũ...")
            es.indices.delete(index='website')
        
        # Tạo index mới với mapping
        es.indices.create(index='website', body=mapping)
        print("Đã tạo index 'website' thành công!")
        
        # Hiển thị thông tin về index
        indices = es.cat.indices(format='json')
        print("\nDanh sách các indices:")
        print(indices)
        
    except Exception as e:
        print(f"Lỗi: {str(e)}")
        
if __name__ == '__main__':
    create_website_index() 