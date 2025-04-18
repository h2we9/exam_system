import unittest
from database import Database
from backup_manager import BackupManager
import os
import tempfile
import json
import sqlite3
from datetime import datetime, timedelta
import tkinter as tk  # إضافة استيراد tkinter
from exam_system import ExamSupervisionSystem  # إضافة استيراد ExamSupervisionSystem

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # استخدام قاعدة بيانات مؤقتة للاختبارات
        self.test_db_path = 'test_exam_system.db'
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.db = Database()
        self.db.conn = sqlite3.connect(self.test_db_path)
        self.db.create_tables()
    
    def tearDown(self):
        # إغلاف الاتصال وحذف قاعدة البيانات المؤقتة
        self.db.conn.close()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_create_user(self):
        # اختبار إنشاء مستخدم جديد
        self.db.create_user('testuser', 'password123', 'admin')
        
        # التحقق من وجود المستخدم
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT username FROM users WHERE username = ?', ('testuser',))
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'testuser')
    
    def test_add_teacher(self):
        # اختبار إضافة مراقب
        name = 'مراقب اختبار'
        cursor = self.db.conn.cursor()
        cursor.execute('INSERT INTO teachers (name, experience) VALUES (?, ?)', (name, 'متوسط'))
        self.db.conn.commit()
        
        # التحقق من إضافة المراقب
        cursor.execute('SELECT name FROM teachers WHERE name = ?', (name,))
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], name)

class TestBackupManager(unittest.TestCase):
    def setUp(self):
        self.test_db_path = 'test_backup_system.db'
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.backup_manager = BackupManager(self.test_db_path)
        
        # إنشاء بيانات اختبار
        self.db = Database()
        self.db.conn = sqlite3.connect(self.test_db_path)
        self.db.create_tables()
        cursor = self.db.conn.cursor()
        cursor.execute('INSERT INTO teachers (name, experience) VALUES (?, ?)', ('مراقب اختبار', 'متوسط'))
        self.db.conn.commit()
    
    def tearDown(self):
        self.db.conn.close()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_backup_restore(self):
        # إنشاء نسخة احتياطية
        success, backup_path = self.backup_manager.create_backup()
        self.assertTrue(success)
        self.assertTrue(os.path.exists(backup_path))
        
        # حذف البيانات الحالية
        cursor = self.db.conn.cursor()
        cursor.execute('DELETE FROM teachers')
        self.db.conn.commit()
        
        # التحقق من حذف البيانات
        cursor.execute('SELECT COUNT(*) FROM teachers')
        count = cursor.fetchone()[0]
        self.assertEqual(count, 0)
        
        # استعادة النسخة الاحتياطية
        success, message = self.backup_manager.restore_backup(backup_path)
        self.assertTrue(success)
        
        # التحقق من استعادة البيانات
        cursor.execute('SELECT name FROM teachers')
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'مراقب اختبار')
        
        # تنظيف
        os.remove(backup_path)

class TestExamSupervisionSystem(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.system = ExamSupervisionSystem(self.root, user_id=1, role='admin')
    
    def test_add_teacher(self):
        initial_count = len(self.system.teacher_listbox.get(0, 'end'))
        self.system.teacher_entry.insert(0, "مراقب جديد")  # إدخال اسم مراقب جديد
        self.system.add_teacher()  # استدعاء الدالة
        new_count = len(self.system.teacher_listbox.get(0, 'end'))
        self.assertEqual(new_count, initial_count + 1)  # التحقق من زيادة العدد بمقدار 1
    
    def test_invalid_date(self):
        with self.assertRaises(ValueError):
            self.system.date_entry.insert(0, "invalid-date")  # إدخال تاريخ غير صحيح
            self.system.add_date()  # استدعاء الدالة
    
    def tearDown(self):
        self.root.destroy()

class TestGUI(unittest.TestCase):
    def test_window_creation(self):
        root = tk.Tk()
        system = ExamSupervisionSystem(root, user_id=1, role='admin')
        self.assertIsNotNone(system.root)
        root.destroy()
if __name__ == '__main__':
    unittest.main()