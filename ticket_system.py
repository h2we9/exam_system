import logging
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum

class TicketStatus(Enum):
    OPEN = 'open'
    IN_PROGRESS = 'in_progress'
    RESOLVED = 'resolved'
    CLOSED = 'closed'

class TicketPriority(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'

class TicketSystem:
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger('ticket_system')
        self._setup_logging()
        self._setup_database()
    
    def _setup_logging(self):
        """إعداد نظام التسجيل"""
        if not self.logger.handlers:
            handler = logging.FileHandler('logs/tickets.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _setup_database(self):
        """إعداد جداول قاعدة البيانات"""
        cursor = self.db.conn.cursor()
        
        # جدول التذاكر
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                assigned_to INTEGER,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users (id),
                FOREIGN KEY (assigned_to) REFERENCES users (id)
            )
        """)
        
        # جدول التعليقات على التذاكر
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticket_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                comment TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # جدول المرفقات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticket_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                uploaded_by INTEGER NOT NULL,
                uploaded_at TIMESTAMP NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets (id),
                FOREIGN KEY (uploaded_by) REFERENCES users (id)
            )
        """)
        
        self.db.conn.commit()
    
    def create_ticket(self, title: str, description: str, created_by: int,
                      priority: TicketPriority = TicketPriority.MEDIUM) -> Optional[int]:
        """إنشاء تذكرة جديدة"""
        try:
            cursor = self.db.conn.cursor()
            now = datetime.now()
            
            cursor.execute("""
                INSERT INTO tickets (title, description, status, priority, created_by,
                                  created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title, description, TicketStatus.OPEN.value, priority.value,
                  created_by, now, now))
            
            self.db.conn.commit()
            ticket_id = cursor.lastrowid
            
            self.logger.info(f'تم إنشاء تذكرة جديدة: {ticket_id}')
            return ticket_id
        except Exception as e:
            self.logger.error(f'خطأ في إنشاء تذكرة: {str(e)}')
            return None
    
    def update_ticket_status(self, ticket_id: int, status: TicketStatus,
                            updated_by: int) -> bool:
        """تحديث حالة التذكرة"""
        try:
            cursor = self.db.conn.cursor()
            now = datetime.now()
            
            cursor.execute("""
                UPDATE tickets
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (status.value, now, ticket_id))
            
            self.db.conn.commit()
            self.logger.info(f'تم تحديث حالة التذكرة {ticket_id} إلى {status.value}')
            return True
        except Exception as e:
            self.logger.error(f'خطأ في تحديث حالة التذكرة: {str(e)}')
            return False
    
    def assign_ticket(self, ticket_id: int, assigned_to: int) -> bool:
        """تعيين التذكرة لمستخدم"""
        try:
            cursor = self.db.conn.cursor()
            now = datetime.now()
            
            cursor.execute("""
                UPDATE tickets
                SET assigned_to = ?, status = ?, updated_at = ?
                WHERE id = ?
            """, (assigned_to, TicketStatus.IN_PROGRESS.value, now, ticket_id))
            
            self.db.conn.commit()
            self.logger.info(f'تم تعيين التذكرة {ticket_id} للمستخدم {assigned_to}')
            return True
        except Exception as e:
            self.logger.error(f'خطأ في تعيين التذكرة: {str(e)}')
            return False
    
    def add_comment(self, ticket_id: int, user_id: int, comment: str) -> Optional[int]:
        """إضافة تعليق على التذكرة"""
        try:
            cursor = self.db.conn.cursor()
            now = datetime.now()
            
            cursor.execute("""
                INSERT INTO ticket_comments (ticket_id, user_id, comment, created_at)
                VALUES (?, ?, ?, ?)
            """, (ticket_id, user_id, comment, now))
            
            self.db.conn.commit()
            comment_id = cursor.lastrowid
            
            self.logger.info(f'تم إضافة تعليق جديد على التذكرة {ticket_id}')
            return comment_id
        except Exception as e:
            self.logger.error(f'خطأ في إضافة تعليق: {str(e)}')
            return None
    
    def add_attachment(self, ticket_id: int, file_name: str, file_path: str,
                      uploaded_by: int) -> Optional[int]:
        """إضافة مرفق للتذكرة"""
        try:
            cursor = self.db.conn.cursor()
            now = datetime.now()
            
            cursor.execute("""
                INSERT INTO ticket_attachments (ticket_id, file_name, file_path,
                                             uploaded_by, uploaded_at)
                VALUES (?, ?, ?, ?, ?)
            """, (ticket_id, file_name, file_path, uploaded_by, now))
            
            self.db.conn.commit()
            attachment_id = cursor.lastrowid
            
            self.logger.info(f'تم إضافة مرفق جديد للتذكرة {ticket_id}')
            return attachment_id
        except Exception as e:
            self.logger.error(f'خطأ في إضافة مرفق: {str(e)}')
            return None
    
    def get_ticket(self, ticket_id: int) -> Optional[Dict]:
        """الحصول على معلومات التذكرة"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("""
                SELECT t.*, u1.username as creator_name, u2.username as assignee_name
                FROM tickets t
                LEFT JOIN users u1 ON t.created_by = u1.id
                LEFT JOIN users u2 ON t.assigned_to = u2.id
                WHERE t.id = ?
            """, (ticket_id,))
            
            ticket = cursor.fetchone()
            if not ticket:
                return None
            
            # الحصول على التعليقات
            cursor.execute("""
                SELECT c.*, u.username
                FROM ticket_comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.ticket_id = ?
                ORDER BY c.created_at
            """, (ticket_id,))
            comments = cursor.fetchall()
            
            # الحصول على المرفقات
            cursor.execute("""
                SELECT a.*, u.username
                FROM ticket_attachments a
                JOIN users u ON a.uploaded_by = u.id
                WHERE a.ticket_id = ?
                ORDER BY a.uploaded_at
            """, (ticket_id,))
            attachments = cursor.fetchall()
            
            return {
                'ticket': ticket,
                'comments': comments,
                'attachments': attachments
            }
        except Exception as e:
            self.logger.error(f'خطأ في استرجاع معلومات التذكرة: {str(e)}')
            return None
    
    def get_user_tickets(self, user_id: int, status: Optional[TicketStatus] = None) -> List[Dict]:
        """الحصول على تذاكر المستخدم"""
        try:
            cursor = self.db.conn.cursor()
            query = """
                SELECT t.*, u1.username as creator_name, u2.username as assignee_name
                FROM tickets t
                LEFT JOIN users u1 ON t.created_by = u1.id
                LEFT JOIN users u2 ON t.assigned_to = u2.id
                WHERE t.created_by = ? OR t.assigned_to = ?
            """
            
            params = [user_id, user_id]
            if status:
                query += " AND t.status = ?"
                params.append(status.value)
            
            query += " ORDER BY t.created_at DESC"
            cursor.execute(query, params)
            
            return cursor.fetchall()
        except Exception as e:
            self.logger.error(f'خطأ في استرجاع تذاكر المستخدم: {str(e)}')
            return []