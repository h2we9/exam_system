import sqlite3
import bcrypt
from datetime import datetime
import threading
import queue
import time
import logging
from backup_utils import BackupManager
from functools import lru_cache
import re

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('exam_system.db', timeout=30)
        self.conn.execute('PRAGMA foreign_keys = ON')
        self.conn.execute('PRAGMA defer_foreign_keys = OFF')
        self.create_tables()
        self.conn.execute('PRAGMA foreign_keys = ON')
        self.conn.execute('PRAGMA defer_foreign_keys = OFF')
        self.conn.execute('PRAGMA journal_mode = WAL')
        self.create_tables()
        self._create_indexes()
        self.create_initial_data()
        self.create_default_admin()
        self.backup_manager = BackupManager()
        self.backup_manager.start_backup_thread()
        self.logger = logging.getLogger('database')
        self._setup_logging()

    def create_initial_data(self):
        cursor = self.conn.cursor()
        try:
            # إضافة البيانات الأساسية للجداول
            cursor.execute('PRAGMA foreign_keys = OFF')
            
            # إضافة الصلاحيات الافتراضية
            default_permissions = [
                ('admin', 'manage_users'),
                ('admin', 'manage_teachers'),
                ('admin', 'manage_rooms'),
                ('admin', 'manage_distributions'),
                ('admin', 'manage_leaves'),
                ('admin', 'view_reports'),
                ('manager', 'manage_distributions'),
                ('manager', 'manage_leaves'),
                ('manager', 'view_reports'),
                ('staff', 'manage_teachers'),
                ('staff', 'manage_rooms'),
                ('staff', 'manage_distributions'),
                ('supervisor', 'view_distributions'),
                ('supervisor', 'manage_notifications')
            ]
            
            for role, permission in default_permissions:
                cursor.execute('INSERT OR IGNORE INTO permissions (role, permission) VALUES (?, ?)',
                              (role, permission))
            
            self.conn.commit()
            cursor.execute('PRAGMA foreign_keys = ON')
        except Exception as e:
            self.conn.rollback()
            raise e

    def check_admin_account(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, username, role FROM users WHERE username='admin'")
        admin = cursor.fetchone()
        
        if not admin:
            print("! خطأ: لا يوجد حساب مدير")
            return False
        
        print(f"بيانات المدير الحالية: ID={admin[0]}, Username='{admin[1]}', Role='{admin[2]}'")
        return admin[2].strip().lower() == 'admin'

    def create_default_admin(self):
        try:
            # بداية transaction جديدة
            self.conn.execute("BEGIN TRANSACTION")
            
            # تعطيل FOREIGN KEY مؤقتاً
            self.conn.execute("PRAGMA foreign_keys = OFF")
            
            # حذف أي حساب مدير قديم (إذا وجد)
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username='admin'")
            admin_exists = cursor.fetchone()
            
            if admin_exists:
                # حذف السجلات المرتبطة أولاً
                cursor.execute("DELETE FROM logs WHERE user_id=?", (admin_exists[0],))
                cursor.execute("UPDATE leaves SET approved_by=NULL WHERE approved_by=?", (admin_exists[0],))
                cursor.execute("DELETE FROM users WHERE username='admin'")
            
            # إنشاء مدير جديد
            hashed_pw = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
            cursor.execute('''
                INSERT INTO users (username, password, role, email, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                'admin',
                hashed_pw.decode('utf-8'),
                'admin',
                'admin@school.com',
                'active'
            ))
            
            # إعادة تفعيل FOREIGN KEY
            self.conn.execute("PRAGMA foreign_keys = ON")
            
            # تأكيد التغييرات
            self.conn.commit()
            print("✅ تم إعادة إنشاء حساب المدير بنجاح")
        except Exception as e:
            self.conn.rollback()
            print(f"❌ فشل إنشاء المدير: {e}")
        self.conn = sqlite3.connect('exam_system.db', timeout=30)
        self.conn.execute('PRAGMA foreign_keys = ON')
        self.conn.execute('PRAGMA defer_foreign_keys = OFF')
        self.create_tables()
        self.conn.execute('PRAGMA foreign_keys = ON')
        self.conn.execute('PRAGMA defer_foreign_keys = OFF')
        self.conn.execute('PRAGMA journal_mode = WAL')  # تحسين الأداء باستخدام WAL
        self.create_tables()
        self._create_indexes()
        
        # إعداد نظام النسخ الاحتياطي
        self.backup_manager = BackupManager()
        self.backup_manager.start_backup_thread()
        
        # إعداد التسجيل
        self.logger = logging.getLogger('database')
        self._setup_logging()
    
    def _create_indexes(self):
        """إنشاء فهارس للحقول المستخدمة بكثرة في عمليات البحث"""
        cursor = self.conn.cursor()
        # فهارس للجداول الرئيسية
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_teachers_name ON teachers(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rooms_name ON rooms(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_exam_dates_date ON exam_dates(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_distributions_date ON distributions(date_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_leaves_teacher ON leaves(teacher_id, start_date, end_date)')
        self.conn.commit()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # جدول المستخدمين
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            last_login TIMESTAMP,
            status TEXT DEFAULT 'active',
            experience TEXT DEFAULT 'متوسط',
            email TEXT,
            phone TEXT,
            failed_attempts INTEGER DEFAULT 0,
            last_attempt TIMESTAMP,
            account_locked_until TIMESTAMP DEFAULT NULL,
            verification_code TEXT,
            verification_code_expiry TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # جدول الصلاحيات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            permission TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(role, permission)
        )
        ''')
        
        # إضافة الصلاحيات الافتراضية
        default_permissions = [
            ('admin', 'manage_users'),
            ('admin', 'manage_teachers'),
            ('admin', 'manage_rooms'),
            ('admin', 'manage_distributions'),
            ('admin', 'manage_leaves'),
            ('admin', 'view_reports'),
            ('manager', 'manage_distributions'),
            ('manager', 'manage_leaves'),
            ('manager', 'view_reports'),
            ('staff', 'manage_teachers'),
            ('staff', 'manage_rooms'),
            ('staff', 'manage_distributions'),
            ('supervisor', 'view_distributions'),
            ('supervisor', 'manage_notifications')
        ]
        
        for role, permission in default_permissions:
            try:
                cursor.execute('INSERT OR IGNORE INTO permissions (role, permission) VALUES (?, ?)',
                              (role, permission))
            except sqlite3.IntegrityError:
                pass
        
        # جدول المراقبين
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            experience TEXT DEFAULT 'متوسط',
            specialization TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # جدول القاعات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            capacity INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # جدول التواريخ
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_dates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # جدول توزيع المراقبين
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS distributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_id INTEGER,
            room_id INTEGER,
            teacher1_id INTEGER,
            teacher2_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (date_id) REFERENCES exam_dates (id),
            FOREIGN KEY (room_id) REFERENCES rooms (id),
            FOREIGN KEY (teacher1_id) REFERENCES teachers (id),
            FOREIGN KEY (teacher2_id) REFERENCES teachers (id)
        )
        ''')
        
        # جدول السجلات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')


        
        # جدول الإجازات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            reason TEXT NOT NULL,
            status TEXT DEFAULT 'قيد المراجعة',
            approved_by INTEGER,
            rejection_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id),
            FOREIGN KEY (approved_by) REFERENCES users (id)
        )
        ''')
        
        self.conn.commit()
    
    def _setup_logging(self):
        """إعداد نظام التسجيل"""
        if not self.logger.handlers:
            handler = logging.FileHandler('logs/database.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def record_failed_login(self, username):
        """تسجيل محاولة تسجيل دخول فاشلة"""
        cursor = self.conn.cursor()
        try:
            # الحصول على عدد المحاولات الفاشلة الحالية
            cursor.execute('SELECT failed_attempts FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            failed_attempts = result[0] if result else 0
            
            # تحديث عدد المحاولات الفاشلة
            cursor.execute('''
                UPDATE users 
                SET failed_attempts = ?,
                    last_attempt = CURRENT_TIMESTAMP
                WHERE username = ?
            ''', (failed_attempts + 1, username))
            
            # قفل الحساب بعد 5 محاولات فاشلة
            if failed_attempts + 1 >= 5:
                cursor.execute('''
                    UPDATE users
                    SET account_locked_until = datetime('now', '+30 minutes')
                    WHERE username = ?
                ''', (username,))
            
            self.conn.commit()
            self.logger.warning(f'محاولة تسجيل دخول فاشلة للمستخدم: {username}')
        except Exception as e:
            self.logger.error(f'خطأ في تسجيل محاولة الدخول الفاشلة: {e}')
            self.conn.rollback()
            raise
    
    def reset_failed_login_attempts(self, username):
        """إعادة تعيين عداد محاولات تسجيل الدخول الفاشلة"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                UPDATE users
                SET failed_login_attempts = 0,
                    account_locked_until = NULL
                WHERE username = ?
            ''', (username,))
            self.conn.commit()
        except Exception as e:
            self.logger.error(f'خطأ في إعادة تعيين محاولات تسجيل الدخول: {e}')
            raise
    
    def is_account_locked(self, username):
        """التحقق مما إذا كان الحساب مقفلاً"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                SELECT account_locked_until
                FROM users
                WHERE username = ?
            ''', (username,))
            result = cursor.fetchone()
            if result and result[0]:
                lock_time = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
                return lock_time > datetime.now()
            return False
        except Exception as e:
            self.logger.error(f'خطأ في التحقق من حالة قفل الحساب: {e}')
            raise
    
    def set_verification_code(self, username, code):
        """تعيين رمز التحقق للمستخدم"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                UPDATE users
                SET verification_code = ?,
                    verification_code_expiry = datetime('now', '+30 minutes')
                WHERE username = ?
            ''', (code, username))
            self.conn.commit()
        except Exception as e:
            self.logger.error(f'خطأ في تعيين رمز التحقق: {e}')
            raise
    
    def verify_code(self, username, code):
        """التحقق من صحة رمز التحقق"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                SELECT verification_code, verification_code_expiry
                FROM users
                WHERE username = ?
            ''', (username,))
            result = cursor.fetchone()
            if not result:
                return False
            
            stored_code, expiry = result
            if not stored_code or not expiry:
                return False
            
            expiry_time = datetime.strptime(expiry, '%Y-%m-%d %H:%M:%S')
            if expiry_time < datetime.now():
                return False
                
            return stored_code == code
        except Exception as e:
            self.logger.error(f'خطأ في التحقق من رمز التحقق: {e}')
            raise
    
    def activate_user(self, user_id):
        """تفعيل حساب المستخدم"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('UPDATE users SET status = "active" WHERE id = ?', (user_id,))
            self.conn.commit()
            self.logger.info(f'تم تفعيل حساب المستخدم: {user_id}')
        except Exception as e:
            self.logger.error(f'خطأ في تفعيل حساب المستخدم: {e}')
            raise
    
    def deactivate_user(self, user_id):
        """إيقاف حساب المستخدم"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('UPDATE users SET status = "inactive" WHERE id = ?', (user_id,))
            self.conn.commit()
            self.logger.info(f'تم إيقاف حساب المستخدم: {user_id}')
        except Exception as e:
            self.logger.error(f'خطأ في إيقاف حساب المستخدم: {e}')
            raise
    
    def delete_user(self, user_id):
        """حذف حساب المستخدم"""
        cursor = self.conn.cursor()
        try:
            # التحقق من عدم حذف المستخدم الرئيسي
            cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            if result and result[0] == 'admin':
                raise ValueError('لا يمكن حذف حساب المستخدم الرئيسي')
            
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            self.conn.commit()
            self.logger.info(f'تم حذف حساب المستخدم: {user_id}')
        except Exception as e:
            self.logger.error(f'خطأ في حذف حساب المستخدم: {e}')
            raise
    
    def _sanitize_input(self, value):
        """تنظيف المدخلات لمنع حقن SQL"""
        if isinstance(value, str):
            # إزالة الأحرف الخاصة والتعليمات البرمجية المحتملة
            return re.sub(r'[;\\\"\'\-\#]', '', value)
        return value
    
    @lru_cache(maxsize=128)
    def _get_cached_query(self, query, params=None):
        """تنفيذ الاستعلام مع التخزين المؤقت"""
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f'خطأ في تنفيذ الاستعلام: {str(e)}')
            return None
    
    def create_user(self, username, password, role, email=None, phone=None, experience=None):
        cursor = self.conn.cursor()
        
        # تنظيف المدخلات
        username = self._sanitize_input(username)
        role = self._sanitize_input(role)
        email = self._sanitize_input(email) if email else None
        phone = self._sanitize_input(phone) if phone else None
        experience = self._sanitize_input(experience) if experience else None
        try:
            # التحقق من عدم وجود المستخدم
            cursor.execute('SELECT id, role FROM users WHERE LOWER(username) = LOWER(?)', (username,))
            existing_user = cursor.fetchone()
            
            # إذا كان المستخدم موجود وليس المستخدم الافتراضي admin
            if existing_user and not (username.lower() == 'admin' and role == 'admin'):
                raise ValueError("اسم المستخدم موجود بالفعل")
            
            # إذا كان المستخدم هو admin وموجود بالفعل، نتخطى الإنشاء
            if existing_user and username.lower() == 'admin' and role == 'admin':
                return True
            
            # تشفير كلمة المرور
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # تخزين المستخدم مع كلمة المرور المشفرة والمعلومات الإضافية
            cursor.execute('''
                INSERT OR REPLACE INTO users (username, password, role, experience, email, phone, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, hashed_password.decode('utf-8'), role, experience or 'متوسط', email, phone, 'active'))
            self.conn.commit()
            return True
        except ValueError as ve:
            raise ve
        except sqlite3.IntegrityError:
            # تجاهل خطأ التكرار للمستخدم الافتراضي
            if username.lower() == 'admin' and role == 'admin':
                return True
            raise ValueError("اسم المستخدم موجود بالفعل")
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء المستخدم: {e}")
            raise ValueError(f"خطأ في إنشاء المستخدم: {str(e)}")

    
    def verify_user(self, username, password):
        cursor = self.conn.cursor()
        try:
            username = self._sanitize_input(username)
            
            cursor.execute('''
                SELECT id, password, role, status, failed_attempts, account_locked_until 
                FROM users 
                WHERE LOWER(username) = LOWER(?)
            ''', (username,))
            result = cursor.fetchone()
            
            if not result:
                self.logger.warning(f'محاولة تسجيل دخول لمستخدم غير موجود: {username}')
                return None
            
            user_id, stored_password, role, status, failed_attempts, locked_until = result
            
            if status != 'active':
                self.logger.warning(f'محاولة تسجيل دخول لحساب غير نشط: {username}')
                raise ValueError("هذا الحساب غير نشط")
            
            if locked_until and datetime.strptime(locked_until, '%Y-%m-%d %H:%M:%S') > datetime.now():
                remaining_time = datetime.strptime(locked_until, '%Y-%m-%d %H:%M:%S') - datetime.now()
                minutes = int(remaining_time.total_seconds() / 60)
                self.logger.warning(f'محاولة تسجيل دخول لحساب مقفل: {username}')
                raise ValueError(f"تم قفل الحساب مؤقتاً. يرجى المحاولة بعد {minutes} دقيقة")
            
            # التحقق من كلمة المرور
            if isinstance(password, str):
                password = password.encode('utf-8')
            
            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')
            
            if bcrypt.checkpw(password, stored_password):
                # إعادة تعيين محاولات تسجيل الدخول الفاشلة
                cursor.execute('''
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP,
                        failed_attempts = 0,
                        account_locked_until = NULL,
                        last_attempt = NULL
                    WHERE id = ?
                ''', (user_id,))
                self.conn.commit()
                self.logger.info(f'تسجيل دخول ناجح للمستخدم: {username}')
                return user_id, role
            else:
                # تسجيل محاولة فاشلة
                new_failed_attempts = (failed_attempts or 0) + 1
                lock_account = new_failed_attempts >= 5
                
                if lock_account:
                    lock_until = datetime.now() + timedelta(minutes=30)
                    cursor.execute('''
                        UPDATE users 
                        SET failed_attempts = ?,
                            last_attempt = CURRENT_TIMESTAMP,
                            account_locked_until = ?
                        WHERE id = ?
                    ''', (new_failed_attempts, lock_until.strftime('%Y-%m-%d %H:%M:%S'), user_id))
                    self.conn.commit()
                    self.logger.warning(f'تم قفل حساب {username} بعد {new_failed_attempts} محاولات فاشلة')
                    raise ValueError("تم قفل الحساب مؤقتاً بسبب كثرة المحاولات الفاشلة. يرجى المحاولة بعد 30 دقيقة")
                else:
                    cursor.execute('''
                        UPDATE users 
                        SET failed_attempts = ?,
                            last_attempt = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (new_failed_attempts, user_id))
                    self.conn.commit()
                    self.logger.warning(f'محاولة تسجيل دخول فاشلة للمستخدم: {username} (المحاولة {new_failed_attempts})')
                    raise ValueError("اسم المستخدم أو كلمة المرور غير صحيحة")
                
        except ValueError as ve:
            raise ve
        except Exception as e:
            self.logger.error(f'خطأ في التحقق من المستخدم: {e}')
            raise ValueError(f"حدث خطأ أثناء التحقق من المستخدم: {str(e)}")
    def delete_user(self, user_id):
        """حذف مستخدم مع التحقق من الصلاحيات والعلاقات
        
        Args:
            user_id: معرف المستخدم المراد حذفه
            
        Returns:
            bool: True إذا تم الحذف بنجاح
            
        Raises:
            Exception: في حالة وجود خطأ أثناء عملية الحذف
        """
        cursor = self.conn.cursor()
        try:
            # التحقق من وجود المستخدم
            cursor.execute('SELECT username, role FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if not user:
                raise Exception('المستخدم غير موجود')
            
            username, role = user
            
            # لا يمكن حذف المستخدم الرئيسي
            if username.lower() == 'admin':
                raise Exception('لا يمكن حذف المستخدم الرئيسي')
            
            # حذف سجلات المستخدم من الجداول المرتبطة
            cursor.execute('DELETE FROM logs WHERE user_id = ?', (user_id,))
            cursor.execute('UPDATE leaves SET approved_by = NULL WHERE approved_by = ?', (user_id,))
            
            # حذف المستخدم
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            self.conn.commit()
            
            # تسجيل عملية الحذف
            self.log_action(user_id, 'حذف مستخدم', f'تم حذف المستخدم {username}')
            self.logger.info(f'تم حذف المستخدم: {username} (ID: {user_id})')
            
            return True
            
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f'خطأ في حذف المستخدم {user_id}: {str(e)}')
            raise Exception(f'خطأ في حذف المستخدم: {str(e)}')
            
        finally:
            cursor.close()
    
    def add_teacher(self, name, experience='متوسط'):
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO teachers (name, experience) VALUES (?, ?)', 
                         (name, experience))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def add_room(self, name, capacity=0):
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO rooms (name, capacity) VALUES (?, ?)',
                          (name, capacity))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def add_exam_date(self, date):
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO exam_dates (date) VALUES (?)', (date,))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def add_distribution(self, date_id, room_id, teacher1_id, teacher2_id):
        cursor = self.conn.cursor()
        try:
            with self.conn:
                # التحقق من عدم وجود تعارض في التوزيع
                cursor.execute('''
                    SELECT 1 FROM distributions 
                    WHERE date_id = ? AND (room_id = ? OR teacher1_id IN (?, ?) OR teacher2_id IN (?, ?))
                ''', (date_id, room_id, teacher1_id, teacher2_id, teacher1_id, teacher2_id))
                
                if cursor.fetchone():
                    return False
                
                cursor.execute('''
                    INSERT INTO distributions (date_id, room_id, teacher1_id, teacher2_id)
                    VALUES (?, ?, ?, ?)
                ''', (date_id, room_id, teacher1_id, teacher2_id))
                return True
        except sqlite3.IntegrityError:
            return False
    
    def log_action(self, user_id, action, details=None):
        cursor = self.conn.cursor()
        try:
            # التحقق من وجود المستخدم قبل تسجيل الإجراء
            cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
            if not cursor.fetchone():
                self.logger.warning(f'محاولة تسجيل إجراء لمستخدم غير موجود: {user_id}')
                return
                
            cursor.execute('INSERT INTO logs (user_id, action, details) VALUES (?, ?, ?)',
                          (user_id, action, details))
            self.conn.commit()
        except Exception as e:
            self.logger.error(f'خطأ في تسجيل الإجراء: {e}')
            raise
    
    def get_all_teachers(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name FROM teachers')
        return cursor.fetchall()
    
    def get_all_rooms(self):
        cursor = self.conn.cursor()
        # إضافة عمود required_supervisors إذا لم يكن موجوداً
        # التحقق من وجود العمود قبل إضافته
        cursor.execute('PRAGMA table_info(rooms)')
        columns = [column[1] for column in cursor.fetchall()]
        if 'required_supervisors' not in columns:
            cursor.execute('ALTER TABLE rooms ADD COLUMN required_supervisors INTEGER DEFAULT 2')
        self.conn.commit()
        cursor.execute('SELECT id, name, capacity, required_supervisors FROM rooms')
        return cursor.fetchall()
    
    def get_all_exam_dates(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, date FROM exam_dates')
        return cursor.fetchall()
    
    def get_distributions(self, date_id=None, page=1, per_page=50):
        cursor = self.conn.cursor()
        offset = (page - 1) * per_page
        
        # استخدام Common Table Expression لتحسين الأداء
        base_query = '''
            WITH distribution_details AS (
                SELECT 
                    d.id,
                    ed.date,
                    r.name as room,
                    t1.name as teacher1,
                    t2.name as teacher2,
                    ROW_NUMBER() OVER (ORDER BY ed.date, r.name) as row_num
                FROM distributions d
                JOIN exam_dates ed ON d.date_id = ed.id
                JOIN rooms r ON d.room_id = r.id
                JOIN teachers t1 ON d.teacher1_id = t1.id
                JOIN teachers t2 ON d.teacher2_id = t2.id
                {where_clause}
            )
            SELECT id, date, room, teacher1, teacher2
            FROM distribution_details
            WHERE row_num > ? AND row_num <= ?
        '''
        
        where_clause = 'WHERE d.date_id = ?' if date_id else ''
        query = base_query.format(where_clause=where_clause)
        
        if date_id:
            cursor.execute(query, (date_id, offset, offset + per_page))
        else:
            cursor.execute(query, (offset, offset + per_page))
        return cursor.fetchall()
    
    def update_teacher(self, teacher_id, name=None, experience=None, specialization=None):
        cursor = self.conn.cursor()
        update_fields = []
        params = []
        
        if name is not None:
            update_fields.append("name = ?")
            params.append(name)
        
        if experience is not None:
            update_fields.append("experience = ?")
            params.append(experience)
        
        if specialization is not None:
            update_fields.append("specialization = ?")
            params.append(specialization)
        
        if not update_fields:
            return False
        
        query = f"UPDATE teachers SET {', '.join(update_fields)} WHERE id = ?"
        params.append(teacher_id)
        
        try:
            cursor.execute(query, params)
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_room(self, room_id, name=None, capacity=None):
        cursor = self.conn.cursor()
        update_fields = []
        params = []
        
        if name is not None:
            update_fields.append("name = ?")
            params.append(name)
        
        if capacity is not None:
            update_fields.append("capacity = ?")
            params.append(capacity)
        
        if not update_fields:
            return False
        
        query = f"UPDATE rooms SET {', '.join(update_fields)} WHERE id = ?"
        params.append(room_id)
        
        try:
            cursor.execute(query, params)
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_exam_date(self, date_id, new_date):
        cursor = self.conn.cursor()
        try:
            cursor.execute('UPDATE exam_dates SET date = ? WHERE id = ?', (new_date, date_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_distribution(self, distribution_id, date_id=None, room_id=None, teacher1_id=None, teacher2_id=None):
        cursor = self.conn.cursor()
        update_fields = []
        params = []
        
        if date_id is not None:
            update_fields.append("date_id = ?")
            params.append(date_id)
        
        if room_id is not None:
            update_fields.append("room_id = ?")
            params.append(room_id)
        
        if teacher1_id is not None:
            update_fields.append("teacher1_id = ?")
            params.append(teacher1_id)
        
        if teacher2_id is not None:
            update_fields.append("teacher2_id = ?")
            params.append(teacher2_id)
        
        if not update_fields:
            return False
        
        query = f"UPDATE distributions SET {', '.join(update_fields)} WHERE id = ?"
        params.append(distribution_id)
        
        try:
            cursor.execute(query, params)
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_teacher_by_id(self, teacher_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name, experience, specialization FROM teachers WHERE id = ?', (teacher_id,))
        return cursor.fetchone()
    
    def get_room_by_id(self, room_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name, capacity FROM rooms WHERE id = ?', (room_id,))
        return cursor.fetchone()
    
    def get_exam_date_by_id(self, date_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, date FROM exam_dates WHERE id = ?', (date_id,))
        return cursor.fetchone()
    
    def get_distribution_by_id(self, distribution_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT d.id, d.date_id, d.room_id, d.teacher1_id, d.teacher2_id,
                   ed.date, r.name as room_name, 
                   t1.name as teacher1_name, t2.name as teacher2_name
            FROM distributions d
            JOIN exam_dates ed ON d.date_id = ed.id
            JOIN rooms r ON d.room_id = r.id
            JOIN teachers t1 ON d.teacher1_id = t1.id
            JOIN teachers t2 ON d.teacher2_id = t2.id
            WHERE d.id = ?
        ''', (distribution_id,))
        return cursor.fetchone()
    
    def add_leave(self, teacher_id, start_date, end_date, reason=None):
        cursor = self.conn.cursor()
        try:
            with self.conn:
                # التحقق من عدم وجود إجازات متداخلة
                cursor.execute('''
                    SELECT 1 FROM leaves 
                    WHERE teacher_id = ? AND status = 'approved'
                    AND (
                        (start_date <= ? AND end_date >= ?) OR
                        (start_date <= ? AND end_date >= ?) OR
                        (start_date >= ? AND end_date <= ?)
                    )
                ''', (teacher_id, start_date, start_date, end_date, end_date, start_date, end_date))
                
                if cursor.fetchone():
                    return False
                
                cursor.execute('''
                    INSERT INTO leaves (teacher_id, start_date, end_date, reason)
                    VALUES (?, ?, ?, ?)
                ''', (teacher_id, start_date, end_date, reason))
                return True
        except sqlite3.IntegrityError:
            return False
    
    def get_teacher_leaves(self, teacher_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, start_date, end_date, reason, status
            FROM leaves
            WHERE teacher_id = ?
            ORDER BY start_date DESC
        ''', (teacher_id,))
        return cursor.fetchall()
    
    def update_leave_status(self, leave_id, status):
        cursor = self.conn.cursor()
        try:
            cursor.execute('UPDATE leaves SET status = ? WHERE id = ?', (status, leave_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_teachers_on_leave(self, date):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT DISTINCT t.id, t.name
            FROM teachers t
            JOIN leaves l ON t.id = l.teacher_id
            WHERE l.status = 'approved'
            AND ? BETWEEN l.start_date AND l.end_date
        ''', (date,))
        return cursor.fetchall()
    

    
    def close(self):
        self.conn.close()