import unittest
from leaves import LeaveManager
from database import Database
from datetime import datetime, timedelta
import sqlite3
import os

class TestLeaveManager(unittest.TestCase):
    def setUp(self):
        # إنشاء قاعدة بيانات مؤقتة للاختبارات
        self.test_db_path = 'test_leaves.db'
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
            
        self.db = Database()
        self.db.conn = sqlite3.connect(self.test_db_path)
        self.db.create_tables()
        
        self.leave_manager = LeaveManager(self.db)
        self.test_user_id = 1
        
        # إضافة مراقب للاختبار
        cursor = self.db.conn.cursor()
        cursor.execute('INSERT INTO teachers (name, experience) VALUES (?, ?)',
                      ('مراقب اختبار', 'متوسط'))
        self.test_teacher_id = cursor.lastrowid
        self.db.conn.commit()
    
    def tearDown(self):
        self.db.conn.close()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_request_leave(self):
        # اختبار طلب إجازة
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=5)
        reason = 'إجازة مرضية'
        
        leave_id = self.leave_manager.request_leave(
            self.test_teacher_id,
            'sick',  # نوع الإجازة
            start_date,
            end_date,
            reason
        )
        
        self.assertIsNotNone(leave_id)
        
        # التحقق من تسجيل الإجازة
        leave = self.leave_manager.get_leave(leave_id)
        self.assertEqual(leave['teacher_id'], self.test_teacher_id)
        self.assertEqual(leave['status'], 'قيد المراجعة')
    
    def test_approve_leave(self):
        # إنشاء طلب إجازة
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=3)
        leave_id = self.leave_manager.request_leave(
            self.test_teacher_id,
            'annual',  # نوع الإجازة
            start_date,
            end_date,
            'إجازة عادية'
        )
        
        # الموافقة على الإجازة
        self.leave_manager.approve_leave(leave_id, self.test_user_id)
        
        # التحقق من حالة الإجازة
        leave = self.leave_manager.get_leave(leave_id)
        self.assertEqual(leave['status'], 'موافق عليها')
        self.assertEqual(leave['approved_by'], self.test_user_id)
    
    def test_reject_leave(self):
        # إنشاء طلب إجازة
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=2)
        leave_id = self.leave_manager.request_leave(
            self.test_teacher_id,
            'emergency',  # نوع الإجازة
            start_date,
            end_date,
            'إجازة طارئة'
        )
        
        # رفض الإجازة
        rejection_reason = 'عدم توفر البديل'
        self.leave_manager.reject_leave(leave_id, self.test_user_id, rejection_reason)
        
        # التحقق من حالة الإجازة
        leave = self.leave_manager.get_leave(leave_id)
        self.assertEqual(leave['status'], 'مرفوضة')
        self.assertEqual(leave['rejection_reason'], rejection_reason)
    
    def test_get_teacher_leaves(self):
        # إنشاء عدة طلبات إجازة
        start_date = datetime.now().date()
        
        for i in range(3):
            self.leave_manager.request_leave(
                self.test_teacher_id,
                'annual',  # نوع الإجازة
                start_date + timedelta(days=i*7),
                start_date + timedelta(days=i*7+2),
                f'إجازة {i+1}'
            )
        
        # استرجاع إجازات المراقب
        leaves = self.leave_manager.get_teacher_leaves(self.test_teacher_id)
        self.assertEqual(len(leaves), 3)
    
    def test_cancel_leave(self):
        # إنشاء طلب إجازة
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=1)
        leave_id = self.leave_manager.request_leave(
            self.test_teacher_id,
            'annual',  # نوع الإجازة
            start_date,
            end_date,
            'إجازة للإلغاء'
        )
        
        # إلغاء الإجازة
        self.leave_manager.cancel_leave(leave_id)
        
        # التحقق من حالة الإجازة
        leave = self.leave_manager.get_leave(leave_id)
        self.assertEqual(leave['status'], 'ملغاة')
    
    def test_leave_overlap(self):
        # إنشاء إجازة أولى
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=5)
        self.leave_manager.request_leave(
            self.test_teacher_id,
            'annual',  # نوع الإجازة
            start_date,
            end_date,
            'إجازة أولى'
        )
        
        # محاولة إنشاء إجازة متداخلة
        overlap_start = start_date + timedelta(days=2)
        overlap_end = start_date + timedelta(days=7)
        
        with self.assertRaises(ValueError):
            self.leave_manager.request_leave(
                self.test_teacher_id,
                'annual',  # نوع الإجازة
                overlap_start,
                overlap_end,
                'إجازة متداخلة'
            )
    
    def test_leave_statistics(self):
        # إنشاء إجازات متنوعة
        start_date = datetime.now().date()
        
        # إجازة موافق عليها
        leave_id1 = self.leave_manager.request_leave(
            self.test_teacher_id,
            'annual',  # نوع الإجازة
            start_date,
            start_date + timedelta(days=2),
            'إجازة 1'
        )
        self.leave_manager.approve_leave(leave_id1, self.test_user_id)
        
        # إجازة مرفوضة
        leave_id2 = self.leave_manager.request_leave(
            self.test_teacher_id,
            'sick',  # نوع الإجازة
            start_date + timedelta(days=10),
            start_date + timedelta(days=12),
            'إجازة 2'
        )
        self.leave_manager.reject_leave(leave_id2, self.test_user_id, 'سبب الرفض')
        
        # إجازة قيد المراجعة
        self.leave_manager.request_leave(
            self.test_teacher_id,
            'emergency',  # نوع الإجازة
            start_date + timedelta(days=20),
            start_date + timedelta(days=22),
            'إجازة 3'
        )
        
        # الحصول على الإحصائيات
        stats = self.leave_manager.get_leave_statistics(self.test_teacher_id)
        
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['approved'], 1)
        self.assertEqual(stats['rejected'], 1)
        self.assertEqual(stats['pending'], 1)

if __name__ == '__main__':
    unittest.main()