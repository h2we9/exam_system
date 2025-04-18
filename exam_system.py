import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkcalendar import Calendar, DateEntry
from database import Database
from reports import ReportGenerator
from datetime import datetime
import pandas as pd
import random
import json
import os
import hashlib
import pyarabic.araby as araby
import glob
import sys
from version_manager import VersionManager

class ExamSupervisionSystem:
    def sort_arabic(self, items):
        """فرز العناصر العربية بشكل صحيح"""
        return sorted(items, key=lambda x: araby.strip_tashkeel(araby.strip_tatweel(x)))

    def __init__(self, root, user_id, role):
        self.root = root
        self.user_id = user_id
        self.role = role

class ExamSupervisionSystem:
    def sort_arabic(self, items):
        """فرز العناصر العربية بشكل صحيح"""
        return sorted(items, key=lambda x: araby.strip_tashkeel(araby.strip_tatweel(x)))

    def __init__(self, root, user_id, role):
        self.root = root
        self.user_id = user_id
        self.role = role
        
        # تهيئة نظام تسجيل الأخطاء
        from logger import SystemLogger
        self.logger = SystemLogger()
        
        # تهيئة مدير الإصدارات
        self.version_manager = VersionManager()
        
        # تحميل إعدادات الشعار
        self.config_file = "config.json"
        self.school_logo = self.load_school_logo()
        
        self.root.title("نظام توزيع المراقبين")
        try:
            # استخدام الشعار من الإعدادات
            self.root.iconbitmap(self.school_logo)
        except Exception as e:
            self.logger.warning(f"لم يتم العثور على أيقونة النظام: {e}")
        
        self.root.geometry("1200x800")
        
        try:
            # إنشاء الاتصال بقاعدة البيانات
            self.db = Database()
            self.logger.info("تم الاتصال بقاعدة البيانات بنجاح")
            
            # تهيئة الواجهة
            self.create_widgets()
            self.logger.info("تم تهيئة واجهة المستخدم بنجاح")
            
            # تحديث القوائم
            self.update_lists()
            
            self.report_generator = ReportGenerator()
            self.logger.info("تم تهيئة نظام التقارير بنجاح")
        except Exception as e:
            self.logger.error(f"خطأ في تهيئة النظام: {e}")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء تهيئة النظام: {str(e)}")
        finally:
            self.logger.info("تم تهيئة النظام بنجاح")

    
    def create_widgets(self):
        try:
            # تهيئة مدير السمات
            from themes import ThemeManager
            self.theme_manager = ThemeManager()
            self.is_dark_theme = False
            
            # تكوين الشبكة الرئيسية
            self.root.grid_rowconfigure(0, weight=1)
            self.root.grid_columnconfigure(0, weight=1)
            
            # إنشاء الإطار الرئيسي
            main_frame = ttk.Frame(self.root)
            main_frame.grid(row=0, column=0, pady=10, padx=20, sticky='nsew')
            
            # تكوين الشبكة للإطار الرئيسي
            main_frame.grid_rowconfigure(0, weight=1)
            main_frame.grid_rowconfigure(1, weight=1)
            main_frame.grid_columnconfigure(0, weight=1)
            main_frame.grid_columnconfigure(1, weight=2)
            
            # تطبيق السمة الافتراضية
            self.theme_manager.apply_theme(self.root, self.is_dark_theme)
            
            # إنشاء إطارات الواجهة
            self.create_frames(main_frame)
            
            # إنشاء القوائم
            self.create_menus()
            
            self.logger.info("تم إنشاء واجهة المستخدم بنجاح")
            
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء عناصر الواجهة: {e}")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء إنشاء واجهة المستخدم: {str(e)}")
    
    def create_menus(self):
        try:
            # شريط القوائم
            self.menubar = tk.Menu(self.root)
            self.root.config(menu=self.menubar)
        
            # قائمة الملف
            file_menu = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label="ملف", menu=file_menu)
            file_menu.add_command(label="تصدير إلى Excel", command=lambda: self.safe_callback(self.export_to_excel))
            file_menu.add_command(label="استيراد من Excel", command=lambda: self.safe_callback(self.import_from_excel))
            file_menu.add_separator()

            file_menu.add_command(label="تسجيل خروج", command=lambda: self.safe_callback(self.secure_logout))
        
            # قائمة التقارير
            reports_menu = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label="تقارير", menu=reports_menu)
            reports_menu.add_command(label="تقرير التوزيع (PDF)", 
                               command=lambda: self.safe_callback(lambda: self.generate_report('distribution', 'pdf')))
            reports_menu.add_command(label="تقرير التوزيع (Word)", 
                               command=lambda: self.safe_callback(lambda: self.generate_report('distribution', 'word')))
            reports_menu.add_command(label="تقرير الإحصائيات", 
                               command=lambda: self.safe_callback(self.show_statistics))
            reports_menu.add_command(label="طباعة", command=lambda: self.safe_callback(self.print_current))
        
            # قائمة العرض
            view_menu = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label="عرض", menu=view_menu)
            view_menu.add_checkbutton(label="السمة الداكنة", 
                                command=lambda: self.safe_callback(self.toggle_theme))
        
            # قائمة الأدوات
            tools_menu = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label="أدوات", menu=tools_menu)
            tools_menu.add_command(label="التحقق من التحديثات", 
                             command=lambda: self.safe_callback(self.check_for_updates))
            tools_menu.add_command(label="إدارة الإجازات", 
                             command=lambda: self.safe_callback(self.show_leaves_management))
            tools_menu.add_command(label="النسخ الاحتياطي", 
                             command=lambda: self.safe_callback(self.create_backup))
            tools_menu.add_command(label="تغيير شعار المدرسة", 
                             command=lambda: self.safe_callback(self.change_school_logo))
            if self.role == 'admin':
                tools_menu.add_separator()
            tools_menu.add_command(label="إدارة المستخدمين", 
                                 command=lambda: self.safe_callback(self.show_user_management))
        
            # قائمة المساعدة
            help_menu = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label="مساعدة", menu=help_menu)
            help_menu.add_command(label="دليل المستخدم", 
                            command=lambda: self.safe_callback(self.show_help))
            help_menu.add_command(label="حول", 
                            command=lambda: self.safe_callback(self.show_about))
        
            self.logger.info("تم إنشاء القوائم بنجاح")
        
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء القوائم: {e}")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء إنشاء القوائم: {str(e)}")

      
          
    def toggle_theme(self):
        """تبديل بين السمة الفاتحة والداكنة"""
        try:
            self.is_dark_theme = not self.is_dark_theme
            self.theme_manager.apply_theme(self.root, self.is_dark_theme)
            theme_name = "الداكنة" if self.is_dark_theme else "الفاتحة"
            self.logger.info(f"تم تغيير السمة إلى {theme_name}")
        except Exception as e:
            self.logger.error(f"خطأ في تغيير السمة: {e}")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء تغيير السمة: {str(e)}")
            
    def check_for_updates(self):
        """التحقق من وجود تحديثات للنظام"""
        try:
            if self.version_manager.check_for_updates():
                self.root.quit()
                return True
            return False
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من التحديثات: {e}")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء التحقق من التحديثات: {str(e)}")
            return False

    def safe_callback(self, callback):
        """تنفيذ الدالة بشكل آمن مع معالجة الأخطاء"""
        try:
            if self.root.winfo_exists():
                callback()
            else:
                self.logger.warning("محاولة تنفيذ دالة على نافذة تم تدميرها")
        except Exception as e:
            self.logger.error(f"خطأ في تنفيذ الدالة: {e}")
            if self.root.winfo_exists():
                messagebox.showerror("خطأ", f"حدث خطأ غير متوقع: {str(e)}")
    
    def load_school_logo(self):
        """قراءة مسار الشعار من ملف الإعدادات"""
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("school_logo", "school_logo.ico")
        return "school_logo.ico"
        
    def save_school_logo(self, logo_path):
        """حفظ مسار الشعار في ملف الإعدادات"""
        config = {}
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        config["school_logo"] = logo_path
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
            
    def change_school_logo(self):
        """نافذة اختيار صورة الشعار"""
        logo_path = filedialog.askopenfilename(
            title="اختر شعار المدرسة",
            filetypes=[("ICO files", "*.ico"), ("All files", "*.*")]
        )
        if logo_path:
            self.save_school_logo(logo_path)
            try:
                # تحديث الأيقونة في النافذة الرئيسية وجميع النوافذ الفرعية
                self.root.iconbitmap(logo_path)
                for child in self.root.winfo_children():
                    if isinstance(child, tk.Toplevel):
                        try:
                            child.iconbitmap(logo_path)
                        except:
                            pass
                messagebox.showinfo("نجاح", "تم تغيير شعار المدرسة بنجاح!")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء تعيين الشعار: {e}")
                
    def secure_logout(self):
        """تسجيل خروج آمن مع إغلاق اتصال قاعدة البيانات وتنظيف الموارد"""
        try:
            # تسجيل الحدث قبل إغلاق قاعدة البيانات
            if hasattr(self, 'db') and self.db.conn:
                try:
                    cursor = self.db.conn.cursor()
                    cursor.execute('SELECT id FROM users WHERE id = ?', (self.user_id,))
                    user_exists = cursor.fetchone() is not None
                    
                    if user_exists:
                        try:
                            self.db.log_action(self.user_id, "تسجيل خروج", "تم تسجيل الخروج بنجاح")
                            self.db.conn.commit()
                        except Exception as log_error:
                            self.logger.error(f"خطأ في تسجيل عملية الخروج: {log_error}")
                    else:
                        self.logger.warning(f"محاولة تسجيل خروج لمستخدم غير موجود (ID: {self.user_id})")
                    
                    # إغلاق الاتصال بقاعدة البيانات
                    try:
                        self.db.conn.close()
                        self.logger.info("تم إغلاق الاتصال بقاعدة البيانات بنجاح")
                    except Exception as close_error:
                        self.logger.error(f"خطأ في إغلاق قاعدة البيانات: {close_error}")
                        
                except Exception as db_error:
                    self.logger.error(f"خطأ في التحقق من المستخدم: {db_error}")

            # إلغاء تسجيل جميع الدوال المرتبطة بالأحداث وتنظيف الموارد
            if hasattr(self, 'root') and self.root.winfo_exists():
                try:
                    for widget in self.root.winfo_children():
                        widget.destroy()
                    self.root.unbind_all('<All>')
                    
                    # إيقاف حلقة الأحداث وتدمير النافذة
                    self.root.quit()
                    self.root.update()
                    self.root.destroy()
                    self.logger.info("تم إغلاق النافذة وتنظيف الموارد بنجاح")
                except Exception as ui_error:
                    self.logger.error(f"خطأ في تنظيف واجهة المستخدم: {ui_error}")
                    
        except Exception as e:
            self.logger.error(f"خطأ في تسجيل الخروج: {e}")
            # محاولة أخيرة لتدمير النافذة
            try:
                if hasattr(self, 'root') and self.root.winfo_exists():
                    self.root.destroy()
            except Exception as final_error:
                self.logger.error(f"فشل في المحاولة الأخيرة لتدمير النافذة: {final_error}")
        finally:
            from login import LoginSystem
            login_system = LoginSystem()
            login_system.show_login_window()

    def show_user_management(self):
        """عرض نافذة إدارة المستخدمين"""
        if not self.role or self.role.lower() != 'admin':
            messagebox.showerror("خطأ", "يجب أن تكون مديراً للوصول إلى هذه الميزة")
            return
        
        try:
            # إنشاء نافذة جديدة
            user_window = tk.Toplevel(self.root)
            user_window.title("إدارة المستخدمين - نظام توزيع المراقبين")
            try:
                user_window.iconbitmap(self.school_logo)
            except Exception as e:
                self.logger.warning(f"لم يتم العثور على أيقونة النظام للنافذة الفرعية: {e}")
            try:
                user_window.iconbitmap(self.school_logo)
            except Exception as e:
                self.logger.warning(f"لم يتم العثور على أيقونة النظام للنافذة الفرعية: {e}")
            
            # تهيئة النافذة في وسط الشاشة
            window_width = 1000
            window_height = 700
            screen_width = user_window.winfo_screenwidth()
            screen_height = user_window.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            user_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # تكوين الشبكة
            user_window.grid_rowconfigure(0, weight=1)
            user_window.grid_columnconfigure(0, weight=1)
            
            # إطار رئيسي
            main_frame = ttk.Frame(user_window)
            main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
            
            # عنوان
            title_label = ttk.Label(main_frame, text="إدارة المستخدمين", font=("Cairo", 24, "bold"))
            title_label.grid(row=0, column=0, pady=(0, 20), columnspan=3)
            
            # إطار البحث والتصفية
            filter_frame = ttk.LabelFrame(main_frame, text="البحث والتصفية")
            filter_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
            
            # حقل البحث
            search_var = tk.StringVar()
            search_var.trace('w', lambda *args: self._filter_users(tree, search_var.get(), role_filter_var.get()))
            ttk.Label(filter_frame, text="بحث:").pack(side="left", padx=5)
            ttk.Entry(filter_frame, textvariable=search_var).pack(side="left", padx=5)
            
            # تصفية حسب الدور
            role_filter_var = tk.StringVar(value="الكل")
            ttk.Label(filter_frame, text="تصفية حسب الدور:").pack(side="left", padx=5)
            role_combo = ttk.Combobox(filter_frame, textvariable=role_filter_var,
                                     values=["الكل", "admin", "supervisor", "staff", "manager"])
            role_combo.pack(side="left", padx=5)
            role_combo.bind('<<ComboboxSelected>>', 
                           lambda *args: self._filter_users(tree, search_var.get(), role_filter_var.get()))
            
            # إطار جدول المستخدمين
            tree_frame = ttk.Frame(main_frame)
            tree_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
            main_frame.grid_rowconfigure(2, weight=1)
            
            # إنشاء جدول المستخدمين
            columns = ("username", "role", "email", "phone", "experience", "last_login")
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
            
            # تعيين عناوين الأعمدة
            headers = {
                "username": "اسم المستخدم",
                "role": "الدور",
                "email": "البريد الإلكتروني",
                "phone": "رقم الهاتف",
                "experience": "مستوى الخبرة",
                "last_login": "آخر تسجيل دخول"
            }
            
            for col in columns:
                tree.heading(col, text=headers[col],
                           command=lambda c=col: self._sort_treeview(tree, c, False))
                tree.column(col, width=100, anchor="center")
            
            # شريط التمرير
            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # إطار الأزرار
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=3, column=0, columnspan=3, pady=10)
            
            # أزرار العمليات
            ttk.Button(button_frame, text="إضافة مستخدم",
                      command=lambda: self._add_user_dialog(tree)).pack(side="left", padx=5)
            ttk.Button(button_frame, text="تعديل المستخدم",
                      command=lambda: self._edit_user_dialog(tree)).pack(side="left", padx=5)
            ttk.Button(button_frame, text="حذف المستخدم",
                      command=lambda: self._delete_user_dialog(tree)).pack(side="left", padx=5)
            ttk.Button(button_frame, text="تحديث",
                      command=lambda: self._refresh_users(tree)).pack(side="left", padx=5)
            
            # تحميل بيانات المستخدمين
            self._refresh_users(tree)
            
        except Exception as e:
            self.logger.error(f"خطأ في فتح نافذة إدارة المستخدمين: {str(e)}")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء فتح نافذة الإدارة: {str(e)}")

    def _filter_users(self, tree, search_text, role_filter):
        """تصفية المستخدمين حسب النص والدور"""
        for item in tree.get_children():
            tree.delete(item)
        
        try:
            cursor = self.db.conn.cursor()
            query = """SELECT username, role, email, phone, experience, last_login 
                      FROM users WHERE 1=1"""
            params = []
            
            if search_text:
                query += """ AND (username LIKE ? OR email LIKE ? OR phone LIKE ?)"""
                search_pattern = f"%{search_text}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            if role_filter and role_filter != "الكل":
                query += " AND role = ?"
                params.append(role_filter)
            
            cursor.execute(query, params)
            for row in cursor.fetchall():
                tree.insert("", "end", values=row)
                
        except Exception as e:
            self.logger.error(f"خطأ في تصفية المستخدمين: {str(e)}")

    def _sort_treeview(self, tree, col, reverse):
        """فرز جدول المستخدمين حسب العمود"""
        l = [(tree.set(k, col), k) for k in tree.get_children('')]
        l.sort(reverse=reverse)
        for index, (_, k) in enumerate(l):
            tree.move(k, '', index)
        tree.heading(col, command=lambda: self._sort_treeview(tree, col, not reverse))

    def _refresh_users(self, tree):
        """تحديث قائمة المستخدمين"""
        for item in tree.get_children():
            tree.delete(item)
        
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT username, role, email, phone, experience, 
                       datetime(last_login, 'localtime') as last_login
                FROM users ORDER BY username
            """)
            
            for row in cursor.fetchall():
                tree.insert("", "end", values=row)
                
        except Exception as e:
            self.logger.error(f"خطأ في تحديث قائمة المستخدمين: {str(e)}")

    def _add_user_dialog(self, tree):
        """نافذة إضافة مستخدم جديد"""
        dialog = tk.Toplevel(self.root)
        dialog.title("إضافة مستخدم جديد")
        dialog.geometry("400x500")
        dialog.grab_set()
        
        # حقول النموذج
        ttk.Label(dialog, text="اسم المستخدم:").pack(pady=5)
        username_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=username_var).pack(pady=5)
        
        ttk.Label(dialog, text="كلمة المرور:").pack(pady=5)
        password_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=password_var, show="*").pack(pady=5)
        
        ttk.Label(dialog, text="البريد الإلكتروني:").pack(pady=5)
        email_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=email_var).pack(pady=5)
        
        ttk.Label(dialog, text="رقم الهاتف:").pack(pady=5)
        phone_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=phone_var).pack(pady=5)
        
        ttk.Label(dialog, text="الدور:").pack(pady=5)
        role_var = tk.StringVar(value="supervisor")
        ttk.Combobox(dialog, textvariable=role_var,
                    values=["admin", "supervisor", "staff", "manager"]).pack(pady=5)
        
        ttk.Label(dialog, text="مستوى الخبرة:").pack(pady=5)
        experience_var = tk.StringVar(value="متوسط")
        ttk.Combobox(dialog, textvariable=experience_var,
                    values=["مبتدئ", "متوسط", "خبير"]).pack(pady=5)
        
        def save_user():
            try:
                # التحقق من صحة المدخلات
                if not all([username_var.get(), password_var.get(), email_var.get(), role_var.get()]):
                    messagebox.showerror("خطأ", "يرجى ملء جميع الحقول المطلوبة")
                    return
                
                # التحقق من عدم وجود المستخدم مسبقاً
                cursor = self.db.conn.cursor()
                cursor.execute('SELECT username FROM users WHERE username = ?', (username_var.get(),))
                if cursor.fetchone():
                    messagebox.showerror("خطأ", "اسم المستخدم موجود مسبقاً")
                    return
                    
                # إضافة المستخدم باستخدام bcrypt للتشفير
                import bcrypt
                hashed_password = bcrypt.hashpw(password_var.get().encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                cursor.execute("""
                    INSERT INTO users (username, password, email, phone, role, experience)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    username_var.get(),
                    hashed_password,
                    email_var.get(),
                    phone_var.get(),
                    role_var.get(),
                    experience_var.get()
                ))
                self.db.conn.commit()
                
                # تسجيل العملية
                self.logger.info(f"تم إضافة مستخدم جديد: {username_var.get()}")
                
                self._refresh_users(tree)
                dialog.destroy()
                messagebox.showinfo("نجاح", "تم إضافة المستخدم بنجاح")
                
            except Exception as e:
                self.logger.error(f"خطأ في إضافة مستخدم: {str(e)}")
                messagebox.showerror("خطأ", str(e))
        
        ttk.Button(dialog, text="حفظ", command=save_user).pack(pady=20)

    def _edit_user_dialog(self, tree):
        """نافذة تعديل المستخدم"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("تنبيه", "الرجاء اختيار مستخدم للتعديل")
            return
        
        # الحصول على بيانات المستخدم المحدد
        user_data = tree.item(selection[0])['values']
        
        dialog = tk.Toplevel(self.root)
        dialog.title("تعديل المستخدم")
        dialog.geometry("400x500")
        dialog.grab_set()
        
        # حقول النموذج
        ttk.Label(dialog, text="اسم المستخدم:").pack(pady=5)
        username_var = tk.StringVar(value=user_data[0])
        ttk.Entry(dialog, textvariable=username_var, state="readonly").pack(pady=5)
        
        ttk.Label(dialog, text="البريد الإلكتروني:").pack(pady=5)
        email_var = tk.StringVar(value=user_data[2])
        ttk.Entry(dialog, textvariable=email_var).pack(pady=5)
        
        ttk.Label(dialog, text="رقم الهاتف:").pack(pady=5)
        phone_var = tk.StringVar(value=user_data[3])
        ttk.Entry(dialog, textvariable=phone_var).pack(pady=5)
        
        ttk.Label(dialog, text="الدور:").pack(pady=5)
        role_var = tk.StringVar(value=user_data[1])
        role_combo = ttk.Combobox(dialog, textvariable=role_var,
                                 values=["admin", "supervisor", "staff", "manager"])
        role_combo.pack(pady=5)
        
        ttk.Label(dialog, text="مستوى الخبرة:").pack(pady=5)
        experience_var = tk.StringVar(value=user_data[4])
        ttk.Combobox(dialog, textvariable=experience_var,
                    values=["مبتدئ", "متوسط", "خبير"]).pack(pady=5)
        
        def save_changes():
            try:
                # التحقق من صحة المدخلات
                if not all([email_var.get(), role_var.get()]):
                    messagebox.showerror("خطأ", "يرجى ملء جميع الحقول المطلوبة")
                    return
                
                # تحديث بيانات المستخدم
                cursor = self.db.conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET email = ?, phone = ?, role = ?, experience = ?
                    WHERE username = ?
                """, (
                    email_var.get(),
                    phone_var.get(),
                    role_var.get(),
                    experience_var.get(),
                    username_var.get()
                ))
                self.db.conn.commit()
                
                self._refresh_users(tree)
                dialog.destroy()
                messagebox.showinfo("نجاح", "تم تحديث بيانات المستخدم بنجاح")
                
            except Exception as e:
                self.logger.error(f"خطأ في تحديث بيانات المستخدم: {str(e)}")
                messagebox.showerror("خطأ", str(e))
        
        ttk.Button(dialog, text="حفظ التغييرات", command=save_changes).pack(pady=20)

    def _delete_user_dialog(self, tree):
        """حذف المستخدم المحدد"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("تنبيه", "الرجاء اختيار مستخدم للحذف")
            return
        
        username = tree.item(selection[0])['values'][0]
        if username == 'admin':
            messagebox.showerror("خطأ", "لا يمكن حذف المستخدم الرئيسي")
            return
        
        if messagebox.askyesno("تأكيد", f"هل أنت متأكد من حذف المستخدم {username}؟"):
            try:
                cursor = self.db.conn.cursor()
                
                # الحصول على معرف المستخدم
                cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
                user_id = cursor.fetchone()[0]
                
                # حذف السجلات المرتبطة في جدول logs
                cursor.execute('DELETE FROM logs WHERE user_id = ?', (user_id,))
                
                # تحديث حقل approved_by في جدول leaves
                cursor.execute('UPDATE leaves SET approved_by = NULL WHERE approved_by = ?', (user_id,))
                
                # حذف المستخدم
                cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
                
                self.db.conn.commit()
                self._refresh_users(tree)
                messagebox.showinfo("نجاح", "تم حذف المستخدم بنجاح")
                
            except Exception as e:
                self.db.conn.rollback()
                self.logger.error(f"خطأ في حذف المستخدم: {str(e)}")
                messagebox.showerror("خطأ", "لا يمكن حذف المستخدم لوجود بيانات مرتبطة به")
            
    def create_frames(self, main_frame):
        # إطار المراقبين
        teacher_frame = ttk.LabelFrame(main_frame, text="المراقبون", padding=10)
        teacher_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        
        # التركيز التلقائي على حقل الإدخال بعد كل إجراء
        self.root.after(100, lambda: self.teacher_entry.focus_set())
        
        # تكوين الشبكة لإطار المراقبين
        teacher_frame.grid_rowconfigure(1, weight=1)
        for i in range(5):
            teacher_frame.grid_columnconfigure(i, weight=1)
        
        ttk.Label(teacher_frame, text="اسم المراقب:").grid(row=0, column=0, padx=5, sticky='e')
        self.teacher_entry = ttk.Entry(teacher_frame)
        self.teacher_entry.grid(row=0, column=1, padx=5, sticky='ew')
        self.teacher_entry.bind('<Return>', lambda e: self.add_teacher())
        
        ttk.Button(teacher_frame, text="إضافة", command=self.add_teacher).grid(row=0, column=2, padx=5, sticky='ew')
        ttk.Button(teacher_frame, text="تعديل", command=self.edit_teacher).grid(row=0, column=3, padx=5, sticky='ew')
        ttk.Button(teacher_frame, text="حذف", command=self.delete_teacher).grid(row=0, column=4, padx=5, sticky='ew')
        
        # إطار للقائمة مع شريط التمرير
        list_frame = ttk.Frame(teacher_frame)
        list_frame.grid(row=1, column=0, columnspan=5, sticky='nsew', pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        self.teacher_listbox = tk.Listbox(list_frame)
        self.teacher_listbox.grid(row=0, column=0, sticky='nsew')
        self.teacher_listbox.bind('<Delete>', lambda e: self.delete_teacher())
        
        teacher_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.teacher_listbox.yview)
        teacher_scrollbar.grid(row=0, column=1, sticky='ns')
        self.teacher_listbox.configure(yscrollcommand=teacher_scrollbar.set)
        
        # إطار القاعات
        room_frame = ttk.LabelFrame(main_frame, text="القاعات", padding=10)
        room_frame.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
        
        # تكوين الشبكة لإطار القاعات
        room_frame.grid_rowconfigure(1, weight=1)
        for i in range(5):
            room_frame.grid_columnconfigure(i, weight=1)
        
        ttk.Label(room_frame, text="اسم القاعة:").grid(row=0, column=0, padx=5, sticky='e')
        self.room_entry = ttk.Entry(room_frame)
        self.room_entry.grid(row=0, column=1, padx=5, sticky='ew')
        self.room_entry.bind('<Return>', lambda e: self.add_room())
        
        ttk.Button(room_frame, text="إضافة", command=self.add_room).grid(row=0, column=2, padx=5, sticky='ew')
        ttk.Button(room_frame, text="تعديل", command=self.edit_room).grid(row=0, column=3, padx=5, sticky='ew')
        ttk.Button(room_frame, text="حذف", command=self.delete_room).grid(row=0, column=4, padx=5, sticky='ew')
        
        # إطار للقائمة مع شريط التمرير
        room_list_frame = ttk.Frame(room_frame)
        room_list_frame.grid(row=1, column=0, columnspan=5, sticky='nsew', pady=5)
        room_list_frame.grid_rowconfigure(0, weight=1)
        room_list_frame.grid_columnconfigure(0, weight=1)
        
        self.room_listbox = tk.Listbox(room_list_frame)
        self.room_listbox.grid(row=0, column=0, sticky='nsew')
        self.room_listbox.bind('<Delete>', lambda e: self.delete_room())
        
        room_scrollbar = ttk.Scrollbar(room_list_frame, orient="vertical", command=self.room_listbox.yview)
        room_scrollbar.grid(row=0, column=1, sticky='ns')
        self.room_listbox.configure(yscrollcommand=room_scrollbar.set)
        
        # إطار التواريخ
        date_frame = ttk.LabelFrame(main_frame, text="تواريخ الامتحانات", padding=10)
        date_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky='nsew')
        
        # تكوين الشبكة لإطار التواريخ
        date_frame.grid_rowconfigure(1, weight=1)
        for i in range(4):
            date_frame.grid_columnconfigure(i, weight=1)
        
        # إنشاء إطار لحقل التاريخ والتقويم
        date_input_frame = ttk.Frame(date_frame)
        date_input_frame.grid(row=0, column=0, columnspan=2, padx=5, sticky='ew')
        
        ttk.Label(date_input_frame, text="التاريخ:").pack(side='left', padx=5)
        
        # إنشاء حقل إدخال التاريخ مع التقويم المنسدل
        self.date_entry = DateEntry(date_input_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                                  locale='ar')
        self.date_entry.pack(side='left', padx=5)
        
        ttk.Button(date_frame, text="إضافة", command=self.add_date).grid(row=0, column=2, padx=5, sticky='ew')
        ttk.Button(date_frame, text="حذف", command=self.delete_date).grid(row=0, column=3, padx=5, sticky='ew')
        
        # إطار للقائمة مع شريط التمرير
        date_list_frame = ttk.Frame(date_frame)
        date_list_frame.grid(row=1, column=0, columnspan=4, sticky='nsew', pady=5)
        date_list_frame.grid_rowconfigure(0, weight=1)
        date_list_frame.grid_columnconfigure(0, weight=1)
        
        self.date_listbox = tk.Listbox(date_list_frame)
        self.date_listbox.grid(row=0, column=0, sticky='nsew')
        self.date_listbox.bind('<Delete>', lambda e: self.delete_date())
        
        date_scrollbar = ttk.Scrollbar(date_list_frame, orient="vertical", command=self.date_listbox.yview)
        date_scrollbar.grid(row=0, column=1, sticky='ns')
        self.date_listbox.configure(yscrollcommand=date_scrollbar.set)
        
        # أزرار التوزيع
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky='ew')
        control_frame.grid_columnconfigure(0, weight=1)
        
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0)
        
        ttk.Button(button_frame, text="توزيع المراقبين", command=self.distribute_supervisors).pack(side='left', padx=5)
        ttk.Button(button_frame, text="تعديل التوزيع", command=self.edit_distribution).pack(side='left', padx=5)
        ttk.Button(button_frame, text="عرض الجدول", command=self.show_table).pack(side='left', padx=5)
        ttk.Button(button_frame, text="حفظ التوزيع", command=self.save_distribution).pack(side='left', padx=5)
    
    def update_lists(self):
        try:
            # تحديث قائمة المراقبين
            if hasattr(self, 'teacher_listbox'):
                self.teacher_listbox.delete(0, 'end')
                teachers = self.db.get_all_teachers()
                for teacher_id, name in teachers:
                    self.teacher_listbox.insert('end', name)
            
            # تحديث قائمة القاعات
            if hasattr(self, 'room_listbox'):
                self.room_listbox.delete(0, 'end')
                rooms = self.db.get_all_rooms()
                # ترتيب القاعات: أرقام أولاً ثم أسماء أبجدياً
                rooms.sort(key=lambda x: (int(x[1]) if x[1].isdigit() else float('inf'), x[1]))
                for room in rooms:
                    self.room_listbox.insert('end', room[1])
            
            # تحديث قائمة التواريخ
            if hasattr(self, 'date_listbox'):
                self.date_listbox.delete(0, 'end')
                dates = self.db.get_all_exam_dates()
                for date_id, date in dates:
                    self.date_listbox.insert('end', date)
                    
        except Exception as e:
            print(f"خطأ في تحديث القوائم: {e}")
            if hasattr(self, 'logger'):
                self.logger.error(f"خطأ في تحديث القوائم: {e}")

        # تحديث قائمة المراقبين
        if hasattr(self, 'teacher_listbox'):
            teachers = self.teacher_listbox.get(0, tk.END)
            self.teacher_listbox.delete(0, tk.END)
            for teacher in self.sort_arabic(teachers):
                self.teacher_listbox.insert(tk.END, teacher)

        # تحديث قائمة القاعات
        if hasattr(self, 'room_listbox'):
            rooms = self.room_listbox.get(0, tk.END)
            self.room_listbox.delete(0, tk.END)
            
            # فرز القاعات: أرقام أولاً ثم أسماء أبجدياً
            def sort_key(room):
                try:
                    return (0, int(room.strip()))  # إذا كانت رقماً
                except ValueError:
                    return (1, room.strip())      # إذا كانت اسماً
            
            rooms = sorted(rooms, key=sort_key)
            for room in rooms:
                self.room_listbox.insert(tk.END, room)

        # تحديث قائمة التواريخ
        if hasattr(self, 'date_listbox'):
            dates = self.date_listbox.get(0, tk.END)
            self.date_listbox.delete(0, tk.END)
            for date in sorted(dates):
                self.date_listbox.insert(tk.END, date)
        # تحديث قائمة المراقبين
        self.teacher_listbox.delete(0, 'end')
        teachers = self.db.get_all_teachers()
        for teacher_id, name in teachers:
            self.teacher_listbox.insert('end', name)
        
        # تحديث قائمة القاعات
        self.room_listbox.delete(0, 'end')
        rooms = self.db.get_all_rooms()
        # ترتيب القاعات: أرقام أولاً ثم أسماء أبجدياً
        rooms.sort(key=lambda x: (int(x[1]) if x[1].isdigit() else float('inf'), x[1]))
        for room in rooms:
            self.room_listbox.insert('end', room[1])
        
        # تحديث قائمة التواريخ
        self.date_listbox.delete(0, 'end')
        dates = self.db.get_all_exam_dates()
        for date_id, date in dates:
            self.date_listbox.insert('end', date)
    
    def add_teacher(self):
        name = self.teacher_entry.get().strip()
        if not name:
            messagebox.showerror("خطأ", "يرجى إدخال اسم المراقب")
            return
            
        try:
            if self.db.add_teacher(name):
                self.teacher_entry.delete(0, 'end')
                self.update_lists()
                messagebox.showinfo("نجاح", f"تم إضافة المراقب: {name}")
                self.teacher_entry.focus_set()  # التركيز التلقائي بعد الإضافة
            else:
                messagebox.showerror("خطأ", "فشل في إضافة المراقب. قد يكون الاسم مستخدماً بالفعل.")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء إضافة المراقب: {str(e)}")
            print(f"خطأ في إضافة المراقب: {e}")

    
    def edit_teacher(self):
        selection = self.teacher_listbox.curselection()
        if not selection:
            messagebox.showerror("خطأ", "يرجى اختيار مراقب للتعديل")
            return
        
        teacher_name = self.teacher_listbox.get(selection[0])
        
        # الحصول على بيانات المراقب
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT id, name FROM teachers WHERE name = ?', (teacher_name,))
        teacher = cursor.fetchone()
        
        if not teacher:
            messagebox.showerror("خطأ", "لم يتم العثور على بيانات المراقب")
            return
        
        teacher_id, name = teacher
        
        # طلب الاسم الجديد
        new_name = simpledialog.askstring("تعديل المراقب", "أدخل اسم المراقب الجديد:", initialvalue=name)
        
        if new_name:
            new_name = new_name.strip()
            if not new_name:
                messagebox.showerror("خطأ", "يرجى إدخال اسم المراقب")
                return
            
            try:
                # تحديث بيانات المراقب
                cursor.execute('UPDATE teachers SET name = ? WHERE id = ?', (new_name, teacher_id))
                self.db.conn.commit()
                
                self.update_lists()
                self.db.log_action(self.user_id, "تعديل مراقب", 
                                  f"تم تعديل بيانات المراقب من: {name} إلى: {new_name}")
                messagebox.showinfo("نجاح", f"تم تعديل بيانات المراقب بنجاح")
            
            except Exception as e:
                self.db.conn.rollback()
                messagebox.showerror("خطأ", f"حدث خطأ أثناء تعديل بيانات المراقب: {str(e)}")
                print(f"خطأ في تعديل المراقب: {e}")
    
    def delete_teacher(self):
        selection = self.teacher_listbox.curselection()
        if not selection:
            messagebox.showerror("خطأ", "يرجى اختيار مراقب للحذف")
            return
        
        name = self.teacher_listbox.get(selection[0])
        if messagebox.askyesno("تأكيد", f"هل أنت متأكد من حذف المراقب {name}؟"):
            try:
                cursor = self.db.conn.cursor()
                # الحصول على معرف المراقب
                cursor.execute('SELECT id FROM teachers WHERE name = ?', (name,))
                teacher_id = cursor.fetchone()[0]
                
                # حذف السجلات المرتبطة في جدول التوزيعات
                cursor.execute('DELETE FROM distributions WHERE teacher1_id = ? OR teacher2_id = ?', 
                              (teacher_id, teacher_id))
                
                # حذف السجلات المرتبطة في جدول الإجازات
                cursor.execute('DELETE FROM leaves WHERE teacher_id = ?', (teacher_id,))
                
                # حذف المراقب
                cursor.execute('DELETE FROM teachers WHERE id = ?', (teacher_id,))
                self.db.conn.commit()
                
                self.update_lists()
                self.db.log_action(self.user_id, "حذف مراقب", f"تم حذف المراقب: {name}")
                messagebox.showinfo("نجاح", f"تم حذف المراقب: {name}")
            except Exception as e:
                self.db.conn.rollback()
                messagebox.showerror("خطأ", f"حدث خطأ أثناء حذف المراقب: {str(e)}")
                print(f"خطأ في حذف المراقب: {e}")

    
    def add_room(self):
        name = self.room_entry.get().strip()
        if not name:
            messagebox.showerror("خطأ", "يرجى إدخال اسم القاعة")
            return
        
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO rooms (name)
                VALUES (?)
            ''', (name,))
            self.db.conn.commit()
            
            self.room_entry.delete(0, 'end')
            self.update_lists()
            messagebox.showinfo("نجاح", f"تم إضافة القاعة: {name}")
            self.room_entry.focus_set()  # التركيز التلقائي بعد الإضافة
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء إضافة القاعة: {str(e)}")
            print(f"خطأ في إضافة القاعة: {e}")
    
    def edit_room(self):
        selection = self.room_listbox.curselection()
        if not selection:
            messagebox.showerror("خطأ", "يرجى اختيار قاعة للتعديل")
            return
        
        room_name = self.room_listbox.get(selection[0])
        
        # الحصول على بيانات القاعة
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT id, name FROM rooms WHERE name = ?', (room_name,))
        room = cursor.fetchone()
        
        if not room:
            messagebox.showerror("خطأ", "لم يتم العثور على بيانات القاعة")
            return
        
        room_id, name = room
        
        # طلب الاسم الجديد
        new_name = simpledialog.askstring("تعديل القاعة", "أدخل اسم القاعة الجديد:", initialvalue=name)
        
        if new_name:
            new_name = new_name.strip()
            if not new_name:
                messagebox.showerror("خطأ", "يرجى إدخال اسم القاعة")
                return
            
            try:
                # تحديث بيانات القاعة
                cursor.execute('UPDATE rooms SET name = ? WHERE id = ?', (new_name, room_id))
                self.db.conn.commit()
                
                self.update_lists()
                self.db.log_action(self.user_id, "تعديل قاعة", 
                                  f"تم تعديل بيانات القاعة من: {name} إلى: {new_name}")
                messagebox.showinfo("نجاح", f"تم تعديل بيانات القاعة بنجاح")
            
            except Exception as e:
                self.db.conn.rollback()
                messagebox.showerror("خطأ", f"حدث خطأ أثناء تعديل بيانات القاعة: {str(e)}")
                print(f"خطأ في تعديل القاعة: {e}")
    
    def delete_room(self):
        selection = self.room_listbox.curselection()
        if not selection:
            messagebox.showwarning("تحذير", "يرجى اختيار قاعة للحذف")
            return

        room_name = self.room_listbox.get(selection[0])
        if messagebox.askyesno("تأكيد", f"هل أنت متأكد من حذف القاعة {room_name}؟"):
            try:
                cursor = self.db.conn.cursor()
                # حذف السجلات المرتبطة في جدول التوزيعات
                cursor.execute('DELETE FROM distributions WHERE room_id IN (SELECT id FROM rooms WHERE name = ?)', (room_name,))
                # حذف القاعة
                cursor.execute('DELETE FROM rooms WHERE name = ?', (room_name,))
                self.db.conn.commit()
                
                self.room_listbox.delete(selection[0])
                self.logger.info(f"تم حذف القاعة: {room_name}")
                messagebox.showinfo("نجاح", f"تم حذف القاعة {room_name} بنجاح")
            except Exception as e:
                self.db.conn.rollback()
                self.logger.error(f"خطأ أثناء حذف القاعة: {e}")
                messagebox.showerror("خطأ", f"حدث خطأ أثناء حذف القاعة: {str(e)}")
                
    def add_date(self):
        """إضافة تاريخ امتحان جديد مع اختيار القاعات"""
        try:
            # إنشاء نافذة اختيار القاعات
            room_window = tk.Toplevel(self.root)
            room_window.title("اختيار القاعات")
            try:
                room_window.iconbitmap(self.school_logo)
            except Exception as e:
                self.logger.warning(f"لم يتم العثور على أيقونة النظام للنافذة الفرعية: {e}")
            room_window.geometry("400x400")
            
            # إطار القائمة
            list_frame = ttk.Frame(room_window)
            list_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            # قائمة القاعات مع مربعات اختيار
            self.room_vars = {}
            for room in self.room_listbox.get(0, tk.END):
                var = tk.BooleanVar()
                chk = ttk.Checkbutton(list_frame, text=room, variable=var)
                chk.pack(anchor='w')
                self.room_vars[room] = var
            
            # إطار الأزرار
            button_frame = ttk.Frame(room_window)
            button_frame.pack(fill='x', padx=10, pady=10)
            
            # زر اختيار الكل
            ttk.Button(button_frame, text="اختيار الكل", command=self.select_all_rooms).pack(side='left', padx=5)
            
            # زر إضافة التاريخ
            ttk.Button(button_frame, text="إضافة", command=lambda: self.add_date_with_rooms(room_window)).pack(side='right', padx=5)
            
        except Exception as e:
            self.logger.error(f"خطأ في فتح نافذة اختيار القاعات: {e}")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء فتح نافذة اختيار القاعات: {str(e)}")

    def select_all_rooms(self):
        """اختيار جميع القاعات"""
        for room, var in self.room_vars.items():
            var.set(True)

    def add_date_with_rooms(self, window):
        """إضافة التاريخ مع القاعات المختارة"""
        try:
            selected_date = self.date_entry.get_date().strftime('%Y-%m-%d')
            
            # إضافة التاريخ إلى قاعدة البيانات
            cursor = self.db.conn.cursor()
            cursor.execute('INSERT INTO exam_dates (date) VALUES (?)', (selected_date,))
            date_id = cursor.lastrowid
            
            # إضافة القاعات المختارة
            for room, var in self.room_vars.items():
                if var.get():
                    cursor.execute('SELECT id FROM rooms WHERE name = ?', (room,))
                    room_id = cursor.fetchone()[0]
                    cursor.execute('INSERT INTO distributions (date_id, room_id) VALUES (?, ?)', (date_id, room_id))
            
            self.db.conn.commit()
            window.destroy()
            self.update_lists()
            messagebox.showinfo("نجاح", f"تم إضافة تاريخ الامتحان: {selected_date} مع القاعات المختارة")
            self.date_entry.focus_set()  # التركيز التلقائي بعد الإضافة
            
        except Exception as e:
            self.logger.error(f"خطأ في إضافة التاريخ مع القاعات: {e}")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء إضافة التاريخ: {str(e)}")
            
    def delete_date(self):
        selection = self.date_listbox.curselection()
        if not selection:
            messagebox.showerror("خطأ", "يرجى اختيار تاريخ للحذف")
            return
        
        date = self.date_listbox.get(selection[0])
        if messagebox.askyesno("تأكيد", f"هل أنت متأكد من حذف التاريخ {date}؟"):
            cursor = self.db.conn.cursor()
            # First delete related distributions
            cursor.execute('DELETE FROM distributions WHERE date_id IN (SELECT id FROM exam_dates WHERE date = ?)', (date,))
            # Then delete the exam date
            cursor.execute('DELETE FROM exam_dates WHERE date = ?', (date,))
            self.db.conn.commit()
            
            self.update_lists()
            self.db.log_action(self.user_id, "حذف تاريخ", f"تم حذف التاريخ: {date}")
            messagebox.showinfo("نجاح", f"تم حذف التاريخ: {date}")
    
    def distribute_supervisors(self):
        # التحقق من وجود بيانات كافية
        if not self.teacher_listbox.size() or not self.room_listbox.size() or not self.date_listbox.size():
            messagebox.showerror("خطأ", "يرجى التأكد من وجود مراقبين وقاعات وتواريخ")
            return
        
        try:
            cursor = self.db.conn.cursor()
            
            # الحصول على جميع التواريخ مرتبة
            cursor.execute('SELECT id, date FROM exam_dates ORDER BY date')
            dates = cursor.fetchall()
            
            # التحقق من عدد المراقبين المتاحين
            cursor.execute('SELECT COUNT(*) FROM teachers')
            total_teachers = cursor.fetchone()[0]
            if total_teachers < 2:
                raise ValueError("يجب وجود مراقبين على الأقل لإتمام التوزيع")
            
            # إنشاء قواميس لتتبع عدد المراقبات وآخر تاريخ مراقبة لكل معلم
            supervision_count = {}
            last_supervision_date = {}
            
            # تهيئة القواميس
            cursor.execute('SELECT id FROM teachers')
            for (teacher_id,) in cursor.fetchall():
                supervision_count[teacher_id] = 0
                last_supervision_date[teacher_id] = None
            
            # حذف التوزيعات السابقة
            cursor.execute('UPDATE distributions SET teacher1_id = NULL, teacher2_id = NULL')
            
            # توزيع المراقبين لكل تاريخ
            for date_id, exam_date in dates:
                # الحصول على المراقبين المتاحين (غير في إجازة)
                cursor.execute('''
                    SELECT t.id, t.name, t.experience
                    FROM teachers t
                    WHERE t.id NOT IN (
                        SELECT l.teacher_id FROM leaves l
                        WHERE l.status = 'approved'
                        AND ? BETWEEN l.start_date AND l.end_date
                    )
                    ORDER BY t.experience DESC
                ''', (exam_date,))
                available_teachers = cursor.fetchall()
                
                # التحقق من وجود مراقبين كافيين
                if len(available_teachers) < 2:
                    raise ValueError(f"عدد المراقبين المتاحين ({len(available_teachers)}) غير كافٍ في تاريخ {exam_date}")
                
                # الحصول على القاعات المحددة لهذا التاريخ
                cursor.execute('SELECT room_id FROM distributions WHERE date_id = ?', (date_id,))
                selected_rooms = cursor.fetchall()
                
                # التحقق من وجود قاعات كافية
                if len(selected_rooms) == 0:
                    raise ValueError(f"لا توجد قاعات محددة في تاريخ {exam_date}")
                
                # التحقق من وجود عدد كافٍ من المراقبين
                if len(available_teachers) < len(selected_rooms) * 2:
                    raise ValueError(f"عدد المراقبين المتاحين ({len(available_teachers)}) غير كافٍ للقاعات ({len(selected_rooms)}) في {exam_date}. يجب توفر مراقبين لكل قاعة.")
                
                # ترتيب المراقبين حسب عدد المراقبات وتاريخ آخر مراقبة
                def teacher_priority(teacher):
                    teacher_id = teacher[0]
                    days_since_last = float('inf')
                    if last_supervision_date[teacher_id]:
                        last_date = datetime.strptime(last_supervision_date[teacher_id], '%Y-%m-%d')
                        current_date = datetime.strptime(exam_date, '%Y-%m-%d')
                        days_since_last = (current_date - last_date).days
                    return (supervision_count[teacher_id], -days_since_last)
                
                # توزيع المراقبين
                for room_id, in selected_rooms:
                    # ترتيب المراقبين المتاحين حسب الأولوية
                    sorted_teachers = sorted(available_teachers, key=teacher_priority)
                    
                    # تحديد مجموعة المراقبين المؤهلين (الذين لديهم أقل عدد من المراقبات)
                    min_supervisions = supervision_count[sorted_teachers[0][0]]
                    eligible_teachers = [t for t in sorted_teachers if supervision_count[t[0]] <= min_supervisions + 1]
                    
                    # اختيار المراقب الأول بشكل عشوائي من المجموعة المؤهلة
                    teacher1 = random.choice(eligible_teachers[:max(3, len(eligible_teachers)//3)])
                    cursor.execute('UPDATE distributions SET teacher1_id = ? WHERE date_id = ? AND room_id = ?',
                                  (teacher1[0], date_id, room_id))
                    
                    # تحديث إحصائيات المراقب الأول
                    supervision_count[teacher1[0]] += 1
                    last_supervision_date[teacher1[0]] = exam_date
                    available_teachers.remove(teacher1)
                    
                    # إعادة ترتيب المراقبين المتبقين وتحديد المؤهلين للمراقبة الثانية
                    sorted_teachers = sorted(available_teachers, key=teacher_priority)
                    min_supervisions = supervision_count[sorted_teachers[0][0]]
                    eligible_teachers = [t for t in sorted_teachers if supervision_count[t[0]] <= min_supervisions + 1]
                    
                    # اختيار المراقب الثاني بشكل عشوائي من المجموعة المؤهلة
                    teacher2 = random.choice(eligible_teachers[:max(3, len(eligible_teachers)//3)])
                    cursor.execute('UPDATE distributions SET teacher2_id = ? WHERE date_id = ? AND room_id = ?',
                                  (teacher2[0], date_id, room_id))
                    
                    # تحديث إحصائيات المراقب الثاني
                    supervision_count[teacher2[0]] += 1
                    last_supervision_date[teacher2[0]] = exam_date
                    available_teachers.remove(teacher2)
            
            self.db.conn.commit()
            self.db.log_action(self.user_id, "توزيع المراقبين", "تم توزيع المراقبين بشكل عادل")
            
            messagebox.showinfo("نجاح", "تم توزيع المراقبين بشكل عادل")
            
        except ValueError as e:
            messagebox.showerror("خطأ", str(e))
            return
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء التوزيع: {str(e)}")
            return
    
    def show_table(self):
        # إنشاء نافذة جديدة
        table_window = tk.Toplevel(self.root)
        table_window.title("جدول التوزيع")
        table_window.geometry("800x600")
        
        # إنشاء جدول
        tree = ttk.Treeview(table_window, columns=("التاريخ", "القاعة", "المراقب الأول", "المراقب الثاني"), show="headings")
        
        # تعيين العناوين
        for col in ("التاريخ", "القاعة", "المراقب الأول", "المراقب الثاني"):
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        # إضافة شريط التمرير
        scrollbar = ttk.Scrollbar(table_window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # تعبئة البيانات
        distributions = self.db.get_distributions()
        for dist in distributions:
            tree.insert("", "end", values=dist[1:])
        
        # تنسيق النافذة
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def save_distribution(self):
        self.create_backup()
        messagebox.showinfo("حفظ", "تم حفظ التوزيع وإنشاء نسخة احتياطية")
    
    def create_backup(self):
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'data_backup_{timestamp}.json')
        
        # استخراج البيانات من قاعدة البيانات
        cursor = self.db.conn.cursor()
        
        # جمع البيانات من جميع الجداول
        backup_data = {}
        
        # المراقبون
        cursor.execute('SELECT * FROM teachers')
        backup_data['teachers'] = cursor.fetchall()
        
        # القاعات
        cursor.execute('SELECT * FROM rooms')
        backup_data['rooms'] = cursor.fetchall()
        
        # تواريخ الامتحانات
        cursor.execute('SELECT * FROM exam_dates')
        backup_data['exam_dates'] = cursor.fetchall()
        
        # التوزيعات
        cursor.execute('SELECT * FROM distributions')
        backup_data['distributions'] = cursor.fetchall()
        
        # حفظ البيانات في ملف JSON
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=4)
        
        messagebox.showinfo("نجاح", "تم إنشاء نسخة احتياطية بنجاح")
        self.db.log_action(self.user_id, "نسخ احتياطي", f"تم إنشاء نسخة احتياطية: {backup_file}")
    
    def restore_backup(self):
        # اختيار ملف النسخة الاحتياطية
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            messagebox.showerror("خطأ", "لا توجد نسخ احتياطية متاحة")
            return
        
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith('data_backup_') and f.endswith('.json')]
        if not backup_files:
            messagebox.showerror("خطأ", "لا توجد نسخ احتياطية متاحة")
            return
        
        # إنشاء نافذة لاختيار النسخة الاحتياطية
        restore_window = tk.Toplevel(self.root)
        restore_window.title("استعادة نسخة احتياطية")
        restore_window.geometry("400x300")
        
        ttk.Label(restore_window, text="اختر النسخة الاحتياطية:").pack(pady=10)
        
        # إنشاء قائمة النسخ الاحتياطية
        backup_listbox = tk.Listbox(restore_window, width=50)
        backup_listbox.pack(pady=10, padx=10)
        
        # ترتيب الملفات حسب التاريخ (الأحدث أولاً)
        backup_files.sort(reverse=True)
        for file in backup_files:
            # تحويل اسم الملف إلى تاريخ مقروء
            date_str = file.replace('data_backup_', '').replace('.json', '')
            date_str = f"{date_str[:8]} {date_str[9:]}"
            backup_listbox.insert('end', date_str + ' - ' + file)
        
        def do_restore():
            selection = backup_listbox.curselection()
            if not selection:
                messagebox.showerror("خطأ", "يرجى اختيار نسخة احتياطية")
                return
            
            file_name = backup_files[selection[0]]
            backup_file = os.path.join(backup_dir, file_name)
            
            try:
                # قراءة البيانات من ملف النسخة الاحتياطية
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                # حذف البيانات الحالية
                cursor = self.db.conn.cursor()
                cursor.execute('DELETE FROM distributions')
                cursor.execute('DELETE FROM exam_dates')
                cursor.execute('DELETE FROM rooms')
                cursor.execute('DELETE FROM teachers')
                
                # استعادة البيانات
                for teacher in backup_data['teachers']:
                    cursor.execute('INSERT INTO teachers VALUES (?, ?, ?, ?)', teacher)
                
                for room in backup_data['rooms']:
                    cursor.execute('INSERT INTO rooms VALUES (?, ?, ?)', room)
                
                for date in backup_data['exam_dates']:
                    cursor.execute('INSERT INTO exam_dates VALUES (?, ?)', date)
                
                for dist in backup_data['distributions']:
                    cursor.execute('INSERT INTO distributions VALUES (?, ?, ?, ?, ?)', dist)
                
                self.db.conn.commit()
                self.update_lists()
                
                messagebox.showinfo("نجاح", "تم استعادة النسخة الاحتياطية بنجاح")
                self.db.log_action(self.user_id, "استعادة نسخة احتياطية", f"تم استعادة النسخة الاحتياطية: {file_name}")
                restore_window.destroy()
                
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء استعادة النسخة الاحتياطية: {str(e)}")
        
        ttk.Button(restore_window, text="استعادة", command=do_restore).pack(pady=10)
        ttk.Button(restore_window, text="إلغاء", command=restore_window.destroy).pack(pady=5)
    
    def export_to_excel(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                              filetypes=[("Excel files", "*.xlsx")])
        if filename:
            distributions = self.db.get_distributions()
            df = pd.DataFrame(distributions, columns=["ID", "التاريخ", "القاعة", "المراقب الأول", "المراقب الثاني"])
            df = df.drop("ID", axis=1)
            df.to_excel(filename, index=False)
            
            self.db.log_action(self.user_id, "تصدير Excel", f"تم تصدير البيانات إلى: {filename}")
            messagebox.showinfo("تصدير", "تم تصدير البيانات بنجاح")

    def print_current(self):
        """طباعة البيانات الحالية مباشرة"""
        try:
            # إنشاء تقرير Word وطباعته مباشرة
            self.generate_report('distribution', 'word')
            latest_report = max(glob.glob(os.path.join('reports', 'distribution_*.docx')), key=os.path.getctime)
            os.startfile(latest_report, 'print')
            self.db.log_action(self.user_id, "طباعة", "تم إرسال الملف للطباعة مباشرة")
            messagebox.showinfo("طباعة", "تم إرسال الملف للطباعة")
        except Exception as e:
            self.logger.error(f"خطأ في الطباعة: {e}")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء محاولة الطباعة: {str(e)}")
    
    def import_from_excel(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if filename:
            try:
                df = pd.read_excel(filename)
                
                # حذف البيانات الحالية
                cursor = self.db.conn.cursor()
                cursor.execute('DELETE FROM distributions')
                cursor.execute('DELETE FROM teachers')
                cursor.execute('DELETE FROM rooms')
                cursor.execute('DELETE FROM exam_dates')
                
                # إضافة البيانات الجديدة
                for _, row in df.iterrows():
                    self.db.add_teacher(row["المراقب الأول"])
                    self.db.add_teacher(row["المراقب الثاني"])
                    self.db.add_room(row["القاعة"])
                    self.db.add_exam_date(row["التاريخ"])
                
                self.db.conn.commit()
                self.update_lists()
                
                self.db.log_action(self.user_id, "استيراد Excel", f"تم استيراد البيانات من: {filename}")
                messagebox.showinfo("استيراد", "تم استيراد البيانات بنجاح")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء الاستيراد: {str(e)}")
    
    def generate_report(self, report_type, format_type):
        try:
            if format_type == 'pdf':
                filename = self.report_generator.create_pdf_report(report_type)
            else:
                filename = self.report_generator.create_word_report(report_type)
            
            self.db.log_action(self.user_id, "إنشاء تقرير",
                              f"تم إنشاء تقرير {report_type} بتنسيق {format_type}")
            messagebox.showinfo("تقرير", f"تم إنشاء التقرير بنجاح\n{filename}")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء إنشاء التقرير: {str(e)}")
    
    def show_statistics(self):
        stats_window = tk.Toplevel(self.root)
        stats_window.title("إحصائيات التوزيع")
        stats_window.geometry("600x400")
        
        notebook = ttk.Notebook(stats_window)
        notebook.pack(fill='both', expand=True)
        
        # إحصائيات المراقبين
        teacher_frame = ttk.Frame(notebook)
        notebook.add(teacher_frame, text="المراقبون")
        
        teacher_tree = ttk.Treeview(teacher_frame,
                                   columns=("المراقب", "عدد المراقبات"),
                                   show="headings")
        teacher_tree.heading("المراقب", text="المراقب")
        teacher_tree.heading("عدد المراقبات", text="عدد المراقبات")
        
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT t.name, COUNT(*) as count
            FROM teachers t
            LEFT JOIN (
                SELECT teacher1_id as teacher_id FROM distributions
                UNION ALL
                SELECT teacher2_id FROM distributions
            ) d ON t.id = d.teacher_id
            GROUP BY t.id, t.name
            ORDER BY count DESC
        ''')
        
        for row in cursor.fetchall():
            teacher_tree.insert("", "end", values=row)
        
        teacher_tree.pack(fill='both', expand=True)
    
    def show_notification_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title('إعدادات الإشعارات')
        settings_window.geometry('600x600')
        settings_window.resizable(False, False)
        
        # إطار إعدادات البريد الإلكتروني
        smtp_frame = ttk.LabelFrame(settings_window, text='إعدادات البريد الإلكتروني')
        smtp_frame.pack(padx=10, pady=5, fill='x')
        
        # إطار إعدادات الرسائل القصيرة
        sms_frame = ttk.LabelFrame(settings_window, text='إعدادات الرسائل القصيرة')
        sms_frame.pack(padx=10, pady=5, fill='x')
        
        ttk.Label(sms_frame, text='مفتاح API:').pack(padx=5, pady=2)
        sms_api_entry = ttk.Entry(sms_frame, width=40)
        sms_api_entry.pack(padx=5, pady=2)
        
        # إطار إعدادات الواتساب
        whatsapp_frame = ttk.LabelFrame(settings_window, text='إعدادات الواتساب')
        whatsapp_frame.pack(padx=10, pady=5, fill='x')
        
        ttk.Label(whatsapp_frame, text='مفتاح API:').pack(padx=5, pady=2)
        whatsapp_api_entry = ttk.Entry(whatsapp_frame, width=40)
        whatsapp_api_entry.pack(padx=5, pady=2)
        
        ttk.Label(smtp_frame, text='البريد الإلكتروني:').pack(padx=5, pady=2)
        email_entry = ttk.Entry(smtp_frame, width=40)
        email_entry.pack(padx=5, pady=2)
        email_entry.insert(0, self.notification_system.config['email'])
        
        ttk.Label(smtp_frame, text='كلمة المرور:').pack(padx=5, pady=2)
        password_entry = ttk.Entry(smtp_frame, width=40, show='*')
        password_entry.pack(padx=5, pady=2)
        password_entry.insert(0, self.notification_system.config['password'])
        
        def save_smtp_settings():
            try:
                self.notification_system.setup_email(
                    email_entry.get().strip(),
                    password_entry.get().strip()
                )
                messagebox.showinfo('نجاح', 'تم حفظ إعدادات البريد الإلكتروني بنجاح')
            except ValueError as e:
                messagebox.showerror('خطأ', str(e))
        
        def test_connection():
            success, message = self.notification_system.test_smtp_connection()
            if success:
                messagebox.showinfo('نجاح', message)
            else:
                messagebox.showerror('خطأ', message)
        
        ttk.Button(smtp_frame, text='حفظ الإعدادات', command=save_smtp_settings).pack(padx=5, pady=5)
        ttk.Button(smtp_frame, text='اختبار الاتصال', command=test_connection).pack(padx=5, pady=5)
    
    def show_smtp_settings(self):
        from smtp_settings import SMTPSettingsWindow
        SMTPSettingsWindow(self.root)
    
    def show_leaves_management(self):
        leaves_window = tk.Toplevel(self.root)
        leaves_window.title('إدارة الإجازات')
        leaves_window.geometry('600x500')
        
        # إطار إضافة إجازة جديدة
        add_frame = ttk.LabelFrame(leaves_window, text='إضافة إجازة جديدة')
        add_frame.pack(padx=10, pady=5, fill='x')
        
        # اختيار المراقب
        teacher_frame = ttk.Frame(add_frame)
        teacher_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(teacher_frame, text='المراقب:').pack(side='left')
        teacher_var = tk.StringVar()
        teacher_combo = ttk.Combobox(teacher_frame, textvariable=teacher_var)
        teacher_combo['values'] = [t[1] for t in self.db.get_all_teachers()]
        teacher_combo.pack(side='left', padx=5)
        
        # تاريخ البداية
        start_frame = ttk.Frame(add_frame)
        start_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(start_frame, text='تاريخ البداية:').pack(side='left')
        start_entry = DateEntry(start_frame, width=12, background='darkblue',
                               foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                               locale='ar')
        start_entry.pack(side='left', padx=5)
        
        # تاريخ النهاية
        end_frame = ttk.Frame(add_frame)
        end_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(end_frame, text='تاريخ النهاية:').pack(side='left')
        end_entry = DateEntry(end_frame, width=12, background='darkblue',
                             foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
                             locale='ar')
        end_entry.pack(side='left', padx=5)
        
        # السبب
        reason_frame = ttk.Frame(add_frame)
        reason_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(reason_frame, text='السبب:').pack(side='left')
        reason_entry = ttk.Entry(reason_frame, width=40)
        reason_entry.pack(side='left', padx=5)
        
        def add_leave():
            teacher_name = teacher_var.get()
            start_date = start_entry.get().strip()
            end_date = end_entry.get().strip()
            reason = reason_entry.get().strip()
            
            if not all([teacher_name, start_date, end_date, reason]):
                messagebox.showerror('خطأ', 'يرجى ملء جميع الحقول')
                return
            
            try:
                # التحقق من صحة التواريخ
                datetime.strptime(start_date, '%Y-%m-%d')
                datetime.strptime(end_date, '%Y-%m-%d')
                
                # إضافة الإجازة
                cursor = self.db.conn.cursor()
                cursor.execute('SELECT id FROM teachers WHERE name = ?', (teacher_name,))
                teacher_id = cursor.fetchone()[0]
                
                cursor.execute('''
                    INSERT INTO leaves (teacher_id, start_date, end_date, reason)
                    VALUES (?, ?, ?, ?)
                ''', (teacher_id, start_date, end_date, reason))
                self.db.conn.commit()
                
                # تحديث القائمة
                update_leaves_list()
                
                # مسح الحقول
                teacher_combo.set('')
                start_entry.delete(0, 'end')
                end_entry.delete(0, 'end')
                reason_entry.delete(0, 'end')
                
                messagebox.showinfo('نجاح', 'تمت إضافة الإجازة بنجاح')
            except ValueError:
                messagebox.showerror('خطأ', 'صيغة التاريخ غير صحيحة')
        
        ttk.Button(add_frame, text='إضافة إجازة', command=add_leave).pack(pady=5)
        
        # إطار عرض الإجازات
        list_frame = ttk.LabelFrame(leaves_window, text='الإجازات الحالية')
        list_frame.pack(padx=10, pady=5, fill='both', expand=True)
        
        # جدول الإجازات
        columns = ('المراقب', 'تاريخ البداية', 'تاريخ النهاية', 'السبب')
        leaves_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        for col in columns:
            leaves_tree.heading(col, text=col)
            leaves_tree.column(col, width=100)
        
        def update_leaves_list():
            for item in leaves_tree.get_children():
                leaves_tree.delete(item)
            
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT t.name, l.start_date, l.end_date, l.reason
                FROM leaves l
                JOIN teachers t ON l.teacher_id = t.id
                ORDER BY l.start_date DESC
            ''')
            
            for row in cursor.fetchall():
                leaves_tree.insert('', 'end', values=row)
        
        update_leaves_list()
        
        # شريط التمرير
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=leaves_tree.yview)
        leaves_tree.configure(yscrollcommand=scrollbar.set)
        
        # تنظيم عناصر الجدول
        leaves_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def show_internal_notifications(self):
        from internal_notifications import NotificationWindow
        NotificationWindow(self.root, self.user_id)
    
    def check_notifications(self):
        # التحقق من الإشعارات غير المقروءة
        notifications = self.notification_system.get_user_notifications(self.user_id)
        unread = [n for n in notifications if not n[4]]  # n[4] هو حقل is_read
        
        if unread:
            messagebox.showinfo("إشعارات جديدة",
                              f"لديك {len(unread)} إشعارات غير مقروءة")
    
    def edit_distribution(self):
        # إنشاء نافذة جديدة لتعديل التوزيع
        edit_window = tk.Toplevel(self.root)
        edit_window.title("تعديل التوزيع")
        edit_window.geometry("800x600")
        
        # إطار التعديل
        edit_frame = ttk.Frame(edit_window, padding="10")
        edit_frame.pack(fill='both', expand=True)
        
        # عرض التوزيع الحالي في جدول
        tree = ttk.Treeview(edit_frame, columns=("التاريخ", "القاعة", "المراقب الأول", "المراقب الثاني"), show='headings')
        tree.heading("التاريخ", text="التاريخ")
        tree.heading("القاعة", text="القاعة")
        tree.heading("المراقب الأول", text="المراقب الأول")
        tree.heading("المراقب الثاني", text="المراقب الثاني")
        
        # تحميل البيانات
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT ed.date, r.name, t1.name, t2.name
            FROM distributions d
            JOIN exam_dates ed ON d.date_id = ed.id
            JOIN rooms r ON d.room_id = r.id
            LEFT JOIN teachers t1 ON d.teacher1_id = t1.id
            LEFT JOIN teachers t2 ON d.teacher2_id = t2.id
            ORDER BY ed.date, r.name
        """)
        
        for row in cursor.fetchall():
            tree.insert("", "end", values=row)
        
        tree.pack(fill='both', expand=True)
        
        # إضافة شريط التمرير
        scrollbar = ttk.Scrollbar(edit_frame, orient='vertical', command=tree.yview)
        scrollbar.pack(side='right', fill='y')
        tree.configure(yscrollcommand=scrollbar.set)
        
        # إطار التعديل اليدوي
        manual_edit_frame = ttk.LabelFrame(edit_frame, text="تعديل يدوي", padding="10")
        manual_edit_frame.pack(fill='x', pady=10)
        
        # حقول التعديل
        ttk.Label(manual_edit_frame, text="المراقب الأول:").grid(row=0, column=0, padx=5)
        teacher1_var = tk.StringVar()
        teacher1_combo = ttk.Combobox(manual_edit_frame, textvariable=teacher1_var)
        teacher1_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(manual_edit_frame, text="المراقب الثاني:").grid(row=0, column=2, padx=5)
        teacher2_var = tk.StringVar()
        teacher2_combo = ttk.Combobox(manual_edit_frame, textvariable=teacher2_var)
        teacher2_combo.grid(row=0, column=3, padx=5)
        
        # تحميل أسماء المراقبين
        cursor.execute("SELECT name FROM teachers ORDER BY name")
        teachers = [row[0] for row in cursor.fetchall()]
        teacher1_combo['values'] = teachers
        teacher2_combo['values'] = teachers
        
        def update_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showerror("خطأ", "يرجى اختيار صف للتعديل")
                return
            
            item = tree.item(selected[0])
            date, room = item['values'][:2]
            teacher1 = teacher1_var.get()
            teacher2 = teacher2_var.get()
            
            try:
                cursor = self.db.conn.cursor()
                # تحديث المراقبين
                cursor.execute("""
                    UPDATE distributions
                    SET teacher1_id = (SELECT id FROM teachers WHERE name = ?),
                        teacher2_id = (SELECT id FROM teachers WHERE name = ?)
                    WHERE date_id = (SELECT id FROM exam_dates WHERE date = ?)
                    AND room_id = (SELECT id FROM rooms WHERE name = ?)
                """, (teacher1, teacher2, date, room))
                
                self.db.conn.commit()
                self.db.log_action(self.user_id, "تعديل التوزيع", f"تم تعديل المراقبين في {room} بتاريخ {date}")
                
                # تحديث العرض
                tree.set(selected[0], "المراقب الأول", teacher1)
                tree.set(selected[0], "المراقب الثاني", teacher2)
                
                messagebox.showinfo("نجاح", "تم تحديث التوزيع بنجاح")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء التحديث: {str(e)}")
        
        ttk.Button(manual_edit_frame, text="تحديث", command=update_selected).grid(row=0, column=4, padx=10)
        
        # عند اختيار صف
        def on_select(event):
            selected = tree.selection()
            if selected:
                item = tree.item(selected[0])
                teacher1_var.set(item['values'][2] or "")
                teacher2_var.set(item['values'][3] or "")
        
        tree.bind('<<TreeviewSelect>>', on_select)
    
    def show_help(self):
        help_text = """
        دليل المستخدم:
        
1. إدارة المراقبين:
   - إضافة مراقب: أدخل اسم المراقب واضغط "إضافة"
   - حذف مراقب: اختر المراقب من القائمة واضغط "حذف"

2. إدارة القاعات:
   - إضافة قاعة: أدخل اسم القاعة واضغط "إضافة"
   - حذف قاعة: اختر القاعة من القائمة واضغط "حذف"

3. إدارة التواريخ:
   - إضافة تاريخ: أدخل التاريخ بصيغة YYYY-MM-DD واضغط "إضافة"
   - حذف تاريخ: اختر التاريخ من القائمة واضغط "حذف"

4. توزيع المراقبين:
   - اضغط "توزيع المراقبين" لإجراء التوزيع التلقائي
   - اضغط "عرض الجدول" لمشاهدة التوزيع
   - اضغط "حفظ التوزيع" لحفظ التغييرات

5. التقارير:
   - يمكن تصدير التقارير بصيغة PDF أو Word
   - يمكن عرض الإحصائيات المختلفة

6. النسخ الاحتياطي:
   - يتم إنشاء نسخة احتياطية تلقائياً عند حفظ التوزيع
   - يمكن استعادة النسخ الاحتياطية من قائمة الأدوات
        """
        messagebox.showinfo("دليل المستخدم", help_text)
    
    def show_about(self):
        about_text = """
        نظام توزيع المراقبين
الإصدار 1.0

نظام متكامل لإدارة وتوزيع المراقبين في الامتحانات المدرسية
يتميز بواجهة مستخدم سهلة الاستخدام وقاعدة بيانات آمنة

تم تطوير هذا المشروع بواسطة:
الطالب يوسف محمد عبد علي الاوسي
إعدادية الحسين بن الروح العلمية للبنين

للتواصل:
البريد الإلكتروني: yousif.alawsi@outlook.com
الهاتف: 07815035986

جميع الحقوق محفوظة © 2025
        """
        messagebox.showinfo("حول البرنامج", about_text)

if __name__ == "__main__":
    from login import LoginSystem
    login = LoginSystem()
    login.run()