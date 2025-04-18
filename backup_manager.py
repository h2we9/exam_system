import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime
import sqlite3

class BackupManager:
    def __init__(self, db_path='exam_system.db'):
        self.db_path = db_path
        self.default_backup_dir = 'backups'
        
        # إنشاء مجلد النسخ الاحتياطي إذا لم يكن موجوداً
        if not os.path.exists(self.default_backup_dir):
            os.makedirs(self.default_backup_dir)
    
    def create_backup(self, custom_path=None):
        """إنشاء نسخة احتياطية من قاعدة البيانات"""
        try:
            # اتصال بقاعدة البيانات
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # استخراج البيانات من الجداول
            data = {}
            
            # جدول المستخدمين (بدون كلمات المرور)
            cursor.execute('SELECT id, username, role, created_at FROM users')
            data['users'] = [{'id': row[0], 'username': row[1], 'role': row[2], 'created_at': row[3]} 
                            for row in cursor.fetchall()]
            
            # جدول المراقبين
            cursor.execute('SELECT id, name, experience, specialization, created_at FROM teachers')
            data['teachers'] = [{'id': row[0], 'name': row[1], 'experience': row[2], 
                               'specialization': row[3], 'created_at': row[4]} 
                              for row in cursor.fetchall()]
            
            # جدول القاعات
            cursor.execute('SELECT id, name, capacity, created_at FROM rooms')
            data['rooms'] = [{'id': row[0], 'name': row[1], 'capacity': row[2], 'created_at': row[3]} 
                            for row in cursor.fetchall()]
            
            # جدول التواريخ
            cursor.execute('SELECT id, date, created_at FROM exam_dates')
            data['exam_dates'] = [{'id': row[0], 'date': row[1], 'created_at': row[2]} 
                                 for row in cursor.fetchall()]
            
            # جدول التوزيعات
            cursor.execute('''SELECT id, date_id, room_id, teacher1_id, teacher2_id, created_at 
                            FROM distributions''')
            data['distributions'] = [{'id': row[0], 'date_id': row[1], 'room_id': row[2], 
                                    'teacher1_id': row[3], 'teacher2_id': row[4], 'created_at': row[5]} 
                                   for row in cursor.fetchall()]
            
            # إغلاق الاتصال
            conn.close()
            
            # إنشاء اسم الملف
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data_backup_{timestamp}.json'
            
            # تحديد مسار الحفظ
            if custom_path:
                # استخدام المسار المخصص
                if os.path.isdir(custom_path):
                    backup_path = os.path.join(custom_path, filename)
                else:
                    backup_path = custom_path
            else:
                # استخدام المسار الافتراضي
                backup_path = os.path.join(self.default_backup_dir, filename)
            
            # حفظ البيانات في ملف JSON
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            return True, backup_path
        
        except Exception as e:
            return False, str(e)
    
    def restore_backup(self, backup_file):
        """استعادة قاعدة البيانات من نسخة احتياطية"""
        try:
            # قراءة ملف النسخة الاحتياطية
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # اتصال بقاعدة البيانات
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # حفظ النسخة الاحتياطية الحالية قبل الاستعادة
            self.create_backup()
            
            # حذف البيانات الحالية (بترتيب عكسي للعلاقات)
            cursor.execute('DELETE FROM distributions')
            cursor.execute('DELETE FROM exam_dates')
            cursor.execute('DELETE FROM rooms')
            cursor.execute('DELETE FROM teachers')
            # لا نحذف المستخدمين للحفاظ على حسابات الدخول
            
            # استعادة البيانات
            # المراقبين
            for teacher in data.get('teachers', []):
                cursor.execute('''
                    INSERT OR IGNORE INTO teachers (id, name, experience, specialization, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (teacher['id'], teacher['name'], teacher['experience'], 
                       teacher['specialization'], teacher['created_at']))
            
            # القاعات
            for room in data.get('rooms', []):
                cursor.execute('''
                    INSERT OR IGNORE INTO rooms (id, name, capacity, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (room['id'], room['name'], room['capacity'], room['created_at']))
            
            # التواريخ
            for date in data.get('exam_dates', []):
                cursor.execute('''
                    INSERT OR IGNORE INTO exam_dates (id, date, created_at)
                    VALUES (?, ?, ?)
                ''', (date['id'], date['date'], date['created_at']))
            
            # التوزيعات
            for dist in data.get('distributions', []):
                cursor.execute('''
                    INSERT OR IGNORE INTO distributions 
                    (id, date_id, room_id, teacher1_id, teacher2_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (dist['id'], dist['date_id'], dist['room_id'], 
                       dist['teacher1_id'], dist['teacher2_id'], dist['created_at']))
            
            # حفظ التغييرات
            conn.commit()
            conn.close()
            
            return True, "تمت استعادة النسخة الاحتياطية بنجاح"
        
        except Exception as e:
            return False, str(e)

class BackupWindow(tk.Toplevel):
    def __init__(self, parent, user_id):
        super().__init__(parent)
        self.title('إدارة النسخ الاحتياطي')
        self.geometry('600x500')
        self.resizable(True, True)
        
        self.user_id = user_id
        self.backup_manager = BackupManager()
        
        self.create_widgets()
        self.load_backups()
    
    def create_widgets(self):
        # إطار رئيسي
        main_frame = ttk.Frame(self, padding='10')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # عنوان
        title_label = ttk.Label(main_frame, text='إدارة النسخ الاحتياطي', font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # أزرار التحكم
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text='إنشاء نسخة احتياطية', 
                  command=self.create_backup).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text='استعادة نسخة احتياطية', 
                  command=self.restore_backup).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text='تحديد مسار مخصص', 
                  command=self.select_custom_path).pack(side=tk.LEFT, padx=5)
        
        # قائمة النسخ الاحتياطية
        list_frame = ttk.LabelFrame(main_frame, text='النسخ الاحتياطية المتوفرة')
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # إنشاء قائمة بالنسخ الاحتياطية
        columns = ('الملف', 'التاريخ', 'الحجم')
        self.backup_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        for col in columns:
            self.backup_tree.heading(col, text=col)
        
        self.backup_tree.column('الملف', width=250)
        self.backup_tree.column('التاريخ', width=150)
        self.backup_tree.column('الحجم', width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=scrollbar.set)
        
        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # معلومات إضافية
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=10)
        
        self.info_label = ttk.Label(info_frame, text='', font=('Arial', 9))
        self.info_label.pack(side=tk.LEFT)
        
        # زر الإغلاق
        ttk.Button(main_frame, text='إغلاق', command=self.destroy).pack(pady=10)
    
    def load_backups(self):
        # حذف العناصر الحالية
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        # البحث عن ملفات النسخ الاحتياطية
        backup_dir = self.backup_manager.default_backup_dir
        if os.path.exists(backup_dir):
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
            
            for file in backup_files:
                file_path = os.path.join(backup_dir, file)
                file_stat = os.stat(file_path)
                
                # استخراج التاريخ من اسم الملف
                try:
                    date_str = file.split('_')[2].split('.')[0]
                    year = date_str[:4]
                    month = date_str[4:6]
                    day = date_str[6:8]
                    formatted_date = f'{year}-{month}-{day}'
                except:
                    formatted_date = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d')
                
                # حساب حجم الملف
                size_kb = file_stat.st_size / 1024
                size_str = f'{size_kb:.1f} KB'
                
                self.backup_tree.insert('', 'end', values=(file, formatted_date, size_str), tags=(file_path,))
        
        # تحديث معلومات إضافية
        total_backups = len(self.backup_tree.get_children())
        self.info_label.config(text=f'إجمالي النسخ الاحتياطية: {total_backups}')
    
    def create_backup(self):
        # إنشاء نسخة احتياطية في المسار الافتراضي
        success, result = self.backup_manager.create_backup()
        
        if success:
            messagebox.showinfo('نجاح', f'تم إنشاء النسخة الاحتياطية بنجاح في:\n{result}')
            self.load_backups()
        else:
            messagebox.showerror('خطأ', f'فشل إنشاء النسخة الاحتياطية:\n{result}')
    
    def select_custom_path(self):
        # اختيار مسار مخصص لحفظ النسخة الاحتياطية
        options = {
            'defaultextension': '.json',
            'filetypes': [('ملفات JSON', '*.json')],
            'initialdir': os.getcwd(),
            'title': 'حفظ النسخة الاحتياطية'
        }
        
        file_path = filedialog.asksaveasfilename(**options)
        
        if file_path:
            success, result = self.backup_manager.create_backup(file_path)
            
            if success:
                messagebox.showinfo('نجاح', f'تم إنشاء النسخة الاحتياطية بنجاح في:\n{result}')
                self.load_backups()
            else:
                messagebox.showerror('خطأ', f'فشل إنشاء النسخة الاحتياطية:\n{result}')
    
    def restore_backup(self):
        # استعادة نسخة احتياطية محددة
        selection = self.backup_tree.selection()
        
        if not selection:
            messagebox.showwarning('تنبيه', 'يرجى اختيار نسخة احتياطية لاستعادتها')
            return
        
        # تأكيد الاستعادة
        if not messagebox.askyesno('تأكيد', 'هل أنت متأكد من استعادة هذه النسخة الاحتياطية؟\n' +
                                  'سيتم استبدال البيانات الحالية بالبيانات من النسخة الاحتياطية.'):
            return
        
        # الحصول على مسار الملف
        file_path = self.backup_tree.item(selection[0], 'tags')[0]
        
        # استعادة النسخة الاحتياطية
        success, message = self.backup_manager.restore_backup(file_path)
        
        if success:
            messagebox.showinfo('نجاح', message)
        else:
            messagebox.showerror('خطأ', f'فشل استعادة النسخة الاحتياطية:\n{message}')