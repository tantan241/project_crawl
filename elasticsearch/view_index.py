from elasticsearch import Elasticsearch
import json

def view_index():
    # Kết nối đến Elasticsearch
    es = Elasticsearch(['http://localhost:9200'])
    
    try:
        # Kiểm tra kết nối
        if not es.ping():
            raise Exception("Không thể kết nối đến Elasticsearch")
        
        # 1. Xem danh sách indices
        indices = es.cat.indices(format='json')
        print("\n=== Danh sách các indices ===")
        print(json.dumps(indices, indent=2, ensure_ascii=False))
        
        # 2. Xem mapping của index website
        if es.indices.exists(index='website'):
            mapping = es.indices.get_mapping(index='website')
            print("\n=== Mapping của index website ===")
            print(json.dumps(mapping, indent=2, ensure_ascii=False))
            
            # 3. Xem settings của index website
            settings = es.indices.get_settings(index='website')
            print("\n=== Settings của index website ===")
            print(json.dumps(settings, indent=2, ensure_ascii=False))
        else:
            print("\nIndex 'website' không tồn tại!")
            
    except Exception as e:
        print(f"Lỗi: {str(e)}")

if __name__ == '__main__':
    view_index() 