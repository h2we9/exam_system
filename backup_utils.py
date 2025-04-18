import json
import sqlite3
import os
import time
from datetime import datetime
import threading
import queue
import logging
from functools import lru_cache

class BackupManager:
    def __init__(self, db_path='exam_system.db', backup_dir='backups'):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.backup_queue = queue.Queue()
        self.backup_thread = None
        self.is_running = False
        self.logger = logging.getLogger('backup_manager')
        self._setup_logging()
        self._setup_backup_directory()
        
    def _setup_logging(self):
        """إعداد نظام التسجيل"""
        if not self.logger.handlers:
            handler = logging.FileHandler('logs/backup.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _setup_backup_directory(self):
        """إنشاء مجلد النسخ الاحتياطي إذا لم يكن موجوداً"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def start_backup_thread(self):
        """بدء خيط النسخ الاحتياطي التلقائي"""
        if not self.backup_thread or not self.backup_thread.is_alive():
            self.is_running = True
            self.backup_thread = threading.Thread(target=self._backup_worker)
            self.backup_thread.daemon = True
            self.backup_thread.start()
            self.logger.info('تم بدء خيط النسخ الاحتياطي')
    
    def stop_backup_thread(self):
        """إيقاف خيط النسخ الاحتياطي"""
        self.is_running = False
        if self.backup_thread and self.backup_thread.is_alive():
            self.backup_queue.put(None)  # إشارة للتوقف
            self.backup_thread.join()
            self.logger.info('تم إيقاف خيط النسخ الاحتياطي')
    
    def _backup_worker(self):
        """وظيفة العامل للنسخ الاحتياطي التلقائي"""
        while self.is_running:
            try:
                # انتظار مهمة جديدة أو إشارة التوقف
                task = self.backup_queue.get(timeout=3600)  # نسخة احتياطية كل ساعة
                if task is None:  # إشارة التوقف
                    break
                    
                self.create_backup()
                self.cleanup_old_backups()
                
            except queue.Empty:
                # إنشاء نسخة احتياطية تلقائية
                self.create_backup()
                self.cleanup_old_backups()
            except Exception as e:
                self.logger.error(f'خطأ في خيط النسخ الاحتياطي: {str(e)}')
    
    @lru_cache(maxsize=128)
    def get_table_data(self, table_name):
        """الحصول على بيانات الجدول مع التخزين المؤقت"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f'SELECT * FROM {table_name}')
            columns = [description[0] for description in cursor.description]
            data = cursor.fetchall()
            return {'columns': columns, 'data': data}
        except Exception as e:
            self.logger.error(f'خطأ في قراءة بيانات الجدول {table_name}: {str(e)}')
            return None
        finally:
            if conn:
                conn.close()
    
    def create_backup(self):
        """إنشاء نسخة احتياطية من قاعدة البيانات"""
        try:
            backup_data = {}
            tables = ['users', 'permissions', 'teachers', 'rooms', 'exam_dates', 
                     'distributions', 'logs', 'leaves']
            
            for table in tables:
                table_data = self.get_table_data(table)
                if table_data:
                    backup_data[table] = table_data
            
            # إنشاء اسم الملف بالتاريخ والوقت
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f'data_backup_{timestamp}.json')
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f'تم إنشاء نسخة احتياطية بنجاح: {backup_file}')
            return backup_file
            
        except Exception as e:
            self.logger.error(f'خطأ في إنشاء النسخة الاحتياطية: {str(e)}')
            return None
    
    def restore_backup(self, backup_file):
        """استعادة قاعدة البيانات من نسخة احتياطية"""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # تعطيل القيود الخارجية مؤقتاً
            cursor.execute('PRAGMA foreign_keys = OFF')
            
            for table, data in backup_data.items():
                # حذف البيانات الحالية
                cursor.execute(f'DELETE FROM {table}')
                
                if data['data']:
                    # إعادة إدخال البيانات
                    placeholders = ','.join(['?' for _ in data['columns']])
                    insert_query = f"INSERT INTO {table} ({','.join(data['columns'])}) VALUES ({placeholders})"
                    cursor.executemany(insert_query, data['data'])
            
            # إعادة تفعيل القيود الخارجية
            cursor.execute('PRAGMA foreign_keys = ON')
            conn.commit()
            
            self.logger.info(f'تم استعادة النسخة الاحتياطية بنجاح: {backup_file}')
            return True
            
        except Exception as e:
            self.logger.error(f'خطأ في استعادة النسخة الاحتياطية: {str(e)}')
            return False
        finally:
            if conn:
                conn.close()
    
    def cleanup_old_backups(self, keep_days=7):
        """حذف النسخ الاحتياطية القديمة"""
        try:
            current_time = time.time()
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('data_backup_') and filename.endswith('.json'):
                    filepath = os.path.join(self.backup_dir, filename)
                    file_time = os.path.getmtime(filepath)
                    
                    # حذف الملفات الأقدم من keep_days
                    if (current_time - file_time) > (keep_days * 86400):
                        os.remove(filepath)
                        self.logger.info(f'تم حذف نسخة احتياطية قديمة: {filename}')
                        
        except Exception as e:
            self.logger.error(f'خطأ في تنظيف النسخ الاحتياطية القديمة: {str(e)}')
    
    def get_backup_list(self):
        """الحصول على قائمة النسخ الاحتياطية المتوفرة"""
        try:
            backups = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('data_backup_') and filename.endswith('.json'):
                    filepath = os.path.join(self.backup_dir, filename)
                    backup_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    backups.append({
                        'filename': filename,
                        'path': filepath,
                        'timestamp': backup_time,
                        'size': os.path.getsize(filepath)
                    })
            return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
        except Exception as e:
            self.logger.error(f'خطأ في قراءة قائمة النسخ الاحتياطية: {str(e)}')
            return []