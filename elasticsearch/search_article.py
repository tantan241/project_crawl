from elasticsearch import Elasticsearch
import json

def search_article(title):
    # Kết nối đến Elasticsearch
    es = Elasticsearch(['http://localhost:9200'])
    
    try:
        # Kiểm tra kết nối
        if not es.ping():
            raise Exception("Không thể kết nối đến Elasticsearch")
        
        # Tạo query tìm kiếm chính xác theo title
        query = {
            "query": {
                "bool": {
                    "should": [
                        # Tìm kiếm chính xác
                        {
                            "match_phrase": {
                                "title": title
                            }
                        },
                        # Tìm kiếm mềm hơn
                        {
                            "match": {
                                "title": {
                                    "query": title,
                                    "fuzziness": "AUTO"
                                }
                            }
                        }
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "description": {},
                    "post_content": {}
                }
            }
        }
        
        # Thực hiện tìm kiếm
        result = es.search(index="website", body=query)
        
        # In kết quả
        print(f"\nTìm thấy {result['hits']['total']['value']} kết quả:")
        
        for hit in result['hits']['hits']:
            print("\n=== Bài viết ===")
            print(f"Score: {hit['_score']}")
            source = hit['_source']
            print(f"Tiêu đề: {source.get('title', 'N/A')}")
            print(f"Mô tả: {source.get('description', 'N/A')}")
            print(f"Tác giả: {source.get('author', 'N/A')}")
            print(f"Ngày đăng: {source.get('post_created', 'N/A')}")
            
            if 'highlight' in hit:
                print("\nĐoạn văn có chứa từ khóa:")
                for field, highlights in hit['highlight'].items():
                    print(f"{field}: {' ... '.join(highlights)}")
            
    except Exception as e:
        print(f"Lỗi: {str(e)}")

if __name__ == '__main__':
    title = "4 cánh tay robot mổ u bảo tồn thận người bệnh"
    search_article(title) 