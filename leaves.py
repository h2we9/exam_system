from datetime import datetime, timedelta
from database import Database

class LeaveManager:
    # أنواع الإجازات المتاحة
    LEAVE_TYPES = {
        'annual': 'سنوية',
        'sick': 'مرضية',
        'emergency': 'طارئة',
        'other': 'أخرى'
    }
    
    # الحد الأقصى للإجازات حسب النوع (بالأيام)
    MAX_LEAVE_DAYS = {
        'annual': 30,
        'sick': 14,
        'emergency': 7,
        'other': 5
    }
    
    def __init__(self, db):
        self.db = db
        self.setup_database()
    
    def setup_database(self):
        cursor = self.db.conn.cursor()
        # حذف الجدول القديم إذا كان موجوداً
        cursor.execute('DROP TABLE IF EXISTS leaves')
        
        # إنشاء الجدول مع العمود الجديد leave_type
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                leave_type TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'قيد المراجعة',
                approved_by INTEGER,
                rejection_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES teachers (id),
                FOREIGN KEY (approved_by) REFERENCES users (id)
            )
        ''')
        self.db.conn.commit()
    
    def request_leave(self, teacher_id, leave_type, start_date, end_date, reason):
        # التحقق من نوع الإجازة
        if leave_type not in self.LEAVE_TYPES:
            raise ValueError('نوع الإجازة غير صالح')
            
        # حساب عدد أيام الإجازة
        leave_days = (end_date - start_date).days + 1
        
        # التحقق من الحد الأقصى للإجازة
        if leave_days > self.MAX_LEAVE_DAYS[leave_type]:
            raise ValueError(f'عدد أيام الإجازة يتجاوز الحد الأقصى المسموح به ({self.MAX_LEAVE_DAYS[leave_type]} يوم)')
            
        # التحقق من الرصيد المتبقي
        remaining_days = self.get_remaining_leave_days(teacher_id, leave_type)
        if remaining_days < leave_days:
            raise ValueError(f'رصيد الإجازات المتبقي غير كافٍ ({remaining_days} يوم)')

        # التحقق من تداخل الإجازات
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM leaves
            WHERE teacher_id = ? AND status != 'مرفوضة'
            AND ((start_date <= ? AND end_date >= ?) OR
                 (start_date <= ? AND end_date >= ?) OR
                 (start_date >= ? AND end_date <= ?))
        ''', (teacher_id, end_date, start_date, start_date, end_date, start_date, end_date))
        
        if cursor.fetchone()[0] > 0:
            raise ValueError('يوجد تداخل مع إجازة أخرى لنفس المراقب')
        
        cursor.execute('''
            INSERT INTO leaves (teacher_id, leave_type, start_date, end_date, reason)
            VALUES (?, ?, ?, ?, ?)
        ''', (teacher_id, leave_type, start_date, end_date, reason))
        self.db.conn.commit()
        
        return cursor.lastrowid
    
    def get_leave(self, leave_id):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT id, teacher_id, start_date, end_date, reason, status,
                   approved_by, rejection_reason, created_at
            FROM leaves
            WHERE id = ?
        ''', (leave_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'teacher_id': row[1],
                'start_date': row[2],
                'end_date': row[3],
                'reason': row[4],
                'status': row[5],
                'approved_by': row[6],
                'rejection_reason': row[7],
                'created_at': row[8]
            }
        return None
    
    def approve_leave(self, leave_id, approved_by):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            UPDATE leaves
            SET status = 'موافق عليها', approved_by = ?
            WHERE id = ?
        ''', (approved_by, leave_id))
        self.db.conn.commit()
    
    def reject_leave(self, leave_id, rejected_by, rejection_reason):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            UPDATE leaves
            SET status = 'مرفوضة', approved_by = ?, rejection_reason = ?
            WHERE id = ?
        ''', (rejected_by, rejection_reason, leave_id))
        self.db.conn.commit()
    
    def cancel_leave(self, leave_id):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            UPDATE leaves
            SET status = 'ملغاة'
            WHERE id = ?
        ''', (leave_id,))
        self.db.conn.commit()
    
    def get_teacher_leaves(self, teacher_id):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT id, start_date, end_date, reason, status,
                   approved_by, rejection_reason, created_at
            FROM leaves
            WHERE teacher_id = ?
            ORDER BY created_at DESC
        ''', (teacher_id,))
        
        leaves = []
        for row in cursor.fetchall():
            leaves.append({
                'id': row[0],
                'start_date': row[1],
                'end_date': row[2],
                'reason': row[3],
                'status': row[4],
                'approved_by': row[5],
                'rejection_reason': row[6],
                'created_at': row[7]
            })
        return leaves
    
    def get_remaining_leave_days(self, teacher_id, leave_type):
        # حساب إجمالي أيام الإجازات المستخدمة
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT SUM(julianday(end_date) - julianday(start_date) + 1)
            FROM leaves
            WHERE teacher_id = ? AND leave_type = ? 
            AND status = 'موافق عليها'
            AND start_date >= date('now', 'start of year')
        ''', (teacher_id, leave_type))
        
        used_days = cursor.fetchone()[0] or 0
        return self.MAX_LEAVE_DAYS[leave_type] - int(used_days)
    
    def get_leave_statistics(self, teacher_id):
        # إحصائيات مفصلة حسب نوع الإجازة
        cursor = self.db.conn.cursor()
        stats = {}
        
        # الإحصائيات الإجمالية
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'موافق عليها' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status = 'مرفوضة' THEN 1 ELSE 0 END) as rejected,
                SUM(CASE WHEN status = 'قيد المراجعة' THEN 1 ELSE 0 END) as pending
            FROM leaves
            WHERE teacher_id = ?
        ''', (teacher_id,))
        
        row = cursor.fetchone()
        stats['total'] = row[0] or 0
        stats['approved'] = row[1] or 0
        stats['rejected'] = row[2] or 0
        stats['pending'] = row[3] or 0
        
        # إحصائيات مفصلة لكل نوع إجازة
        for leave_type in self.LEAVE_TYPES:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'موافق عليها' THEN 1 ELSE 0 END) as approved,
                    SUM(CASE WHEN status = 'مرفوضة' THEN 1 ELSE 0 END) as rejected,
                    SUM(CASE WHEN status = 'قيد المراجعة' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'موافق عليها' THEN
                        julianday(end_date) - julianday(start_date) + 1
                    ELSE 0 END) as days_taken
                FROM leaves
                WHERE teacher_id = ? AND leave_type = ?
                AND start_date >= date('now', 'start of year')
            ''', (teacher_id, leave_type))
            
            row = cursor.fetchone()
            stats[leave_type] = {
                'total': row[0] or 0,
                'approved': row[1] or 0,
                'rejected': row[2] or 0,
                'pending': row[3] or 0,
                'days_taken': int(row[4] or 0),
                'days_remaining': self.get_remaining_leave_days(teacher_id, leave_type)
            }
        
        return stats