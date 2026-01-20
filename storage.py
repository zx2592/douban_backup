"""
数据存储模块
支持保存为JSON和Excel格式
"""
import json
import os
import pandas as pd
from datetime import datetime
from config import DATA_DIR


class DataStorage:
    def __init__(self):
        self.backup_dir = os.path.join(DATA_DIR, 'backup')
        os.makedirs(self.backup_dir, exist_ok=True)

    def save_json(self, data, filename):
        """保存为JSON文件"""
        filepath = os.path.join(self.backup_dir, f"{filename}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✓ 已保存: {filepath}")
        return filepath

    def save_excel(self, data, filename):
        """保存为Excel文件"""
        filepath = os.path.join(self.backup_dir, f"{filename}.xlsx")

        all_items = []
        for category, items in data.items():
            if isinstance(items, dict):
                for collection, item_list in items.items():
                    for item in item_list:
                        item_copy = item.copy()
                        item_copy['category'] = category
                        item_copy['collection'] = collection
                        all_items.append(item_copy)
            else:
                for item in items:
                    item_copy = item.copy()
                    item_copy['category'] = category
                    all_items.append(item_copy)

        if all_items:
            df = pd.DataFrame(all_items)
            columns = ['type', 'collection', 'title', 'douban_id', 'rating', 'comment', 'author', 'artist', 'year', 'date', 'cover', 'info', 'tags']
            df = df[[col for col in columns if col in df.columns]]
            df.to_excel(filepath, index=False)
            print(f"✓ 已保存: {filepath}")

        return filepath

    def save_movies_json(self, movies_data):
        """保存电影数据"""
        return self.save_json(movies_data, 'movies')

    def save_books_json(self, books_data):
        """保存书籍数据"""
        return self.save_json(books_data, 'books')

    def save_all_json(self, all_data):
        """保存所有数据"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"douban_backup_{timestamp}"
        return self.save_json(all_data, filename)

    def save_all_excel(self, all_data):
        """导出所有数据为Excel"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"douban_backup_{timestamp}"
        return self.save_excel(all_data, filename)

    def get_backup_list(self):
        """获取已备份的文件列表"""
        files = []
        for f in os.listdir(self.backup_dir):
            if f.endswith(('.json', '.xlsx')):
                filepath = os.path.join(self.backup_dir, f)
                files.append({
                    'name': f,
                    'path': filepath,
                    'size': os.path.getsize(filepath),
                    'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                })
        return sorted(files, key=lambda x: x['modified'], reverse=True)
