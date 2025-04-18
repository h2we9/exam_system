import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import bcrypt
import pyotp
import smtplib
from email.message import EmailMessage
import random
from database import Database
from PIL import Image, ImageTk
import os
import json
from version_manager import VersionManager

class LoginSystem:
    def __init__(self, root=None):
        self.root = root if root else tk.Tk()
        self.window = self.root
        self.version_manager = VersionManager()
        self.check_for_updates()
        self.setup_login_window()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def check_for_updates(self):
        """التحقق من وجود تحديثات"""
        if self.version_manager.check_for_updates():
            self.root.quit()
            return
    
    def on_close(self):
        """معالج لإغلاق النافذة بشكل صحيح"""
        self.root.quit()
        self.root.destroy()
        os._exit(0)
        
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
                self.window.iconbitmap(logo_path)
                messagebox.showinfo("نجاح", "تم تغيير شعار المدرسة بنجاح!")
            except Exception as e:
                messagebox.showerror("خطأ", f"حدث خطأ أثناء تعيين الشعار: {e}")
    
    def setup_login_window(self):
        self.window.title("تسجيل الدخول - نظام توزيع المراقبين")
        self.config_file = "config.json"
        self.school_logo = self.load_school_logo()
        try:
            self.window.iconbitmap(self.school_logo)
        except:
            pass

        # تعيين حجم ثابت للنافذة
        window_width = 1000  # حجم ثابت مناسب
        window_height = 700  # حجم ثابت مناسب
        
        # تمركز النافذة
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.configure(bg="#f0f2f5")
        self.window.resizable(True, True)
        
        # إعداء نظام الشبكة
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
        # خلفية متدرجة حديثة
        self.canvas = tk.Canvas(self.window)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self._create_gradient("#0052D4", "#65C7F7", "#9CECFB")
        
        # إطار المحتوى الرئيسي
        self.main_frame = tk.Frame(self.window, bg="white", bd=0, highlightthickness=0)
        frame_width = 800  # حجم ثابت مناسب
        frame_height = 600  # حجم ثابت مناسب
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center",
                            width=frame_width, height=frame_height)

        # تمكين خاصية التكيف مع تغيير الحجم
        self.window.bind("<Configure>", self.on_window_resize)
        
        # تخصيئ المظهر
        style = ttk.Style()
        style.configure("Custom.TFrame", background="white")
        style.configure("Title.TLabel", font=("Amiri", 32, "bold"), foreground="#2d3436")
        style.configure("Custom.TLabel", font=("NotoNaskhArabic", 14))
        style.configure("Custom.TButton", font=("Cairo", 14, "bold"), padding=12)
        
        # إنشاء قاعدة البيانات
        self.db = Database()
        
        self.create_widgets()
    
    def create_default_admin(self):
        # تحقق من وجود المدير أولاً
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ? AND role = ?', ('admin', 'admin'))
        if cursor.fetchone():
            print("✅ حساب المدير موجود بالفعل")
            return
            
        # إذا لم يكن موجود، أنشئه
        hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        self.db.create_user('admin', hashed_password.decode('utf-8'), 'admin')
        print("✅ تم إنشاء حساب المدير بنجاح")
    
    def _create_gradient(self, *colors):
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        for i, color in enumerate(colors):
            ratio = i / (len(colors) - 1)
            y0 = height * ratio
            y1 = height * ((i + 1) / (len(colors) - 1))
            self.canvas.create_rectangle(0, y0, width, y1, fill=color, outline="", tags="gradient")
    
    def on_window_resize(self, event=None):
        # احصل على الأبعاد الجديدة
        new_width = max(800, self.window.winfo_width())
        new_height = max(600, self.window.winfo_height())
        
        # تحديث حجم الكانفاس
        self.canvas.configure(width=new_width, height=new_height)
        
        # إعادة رسم التدرج
        self.canvas.delete("gradient")
        self._create_gradient("#1a237e", "#0d47a1", "#1565c0", "#1976d2", "#1e88e5")
        
        # حدد حجم الإطار بنسبة 80% من النافذة أو أقل
        frame_width = min(int(new_width * 0.8), 800)
        frame_height = min(int(new_height * 0.8), 600)
        
        # ضع الإطار في المنتصف
        self.main_frame.place(
            relx=0.5, rely=0.5,
            anchor="center",
            width=frame_width,
            height=frame_height
        )

    def create_widgets(self):
        # تعريف الأنماط المشتركة للأزرار
        button_style = {
            'font': ("Cairo", 14),
            'bd': 0,
            'padx': 20,
            'pady': 12,
            'relief': "flat",
            'cursor': "hand2"
        }

        # الشعار
        try:
            logo_img = Image.open(self.school_logo)
            logo_img = logo_img.resize((80, 80), Image.Resampling.LANCZOS)
            self.logo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(self.main_frame, image=self.logo, bg="white")
            logo_label.pack(pady=(20, 15))
        except Exception as e:
            print(f"خطأ في تحميل الشعار: {e}")
        
        # العنوان
        title_label = tk.Label(self.main_frame, text="تسجيل الدخول", 
                             font=("Amiri", 32, "bold"), bg="white", fg="#1a237e")
        title_label.pack(pady=(0, 15))
        
        # النموذج
        form_frame = tk.Frame(self.main_frame, bg="white")
        form_frame.pack(pady=20, padx=30, fill="x", expand=True)
        
        # حقول الإدخال
        self._create_input_field(form_frame, "اسم المستخدم", "username")
        self._create_input_field(form_frame, "كلمة المرور", "password", show="*")
        
        # إطار الأزرار
        buttons_frame = tk.Frame(form_frame, bg="white")
        buttons_frame.pack(fill="x", pady=(10, 5), expand=True)

        # زر تسجيل الدخول
        login_btn = tk.Button(buttons_frame, text="تسجيل الدخول", 
                            bg="#1a237e", fg="white",
                            activebackground="#0d47a1",
                            command=self.login,
                            **button_style)
        login_btn.pack(fill="x", pady=5)

        # إضافة تأثير الظل للزر
        shadow_frame = tk.Frame(buttons_frame, bg="#1565c0", bd=0)
        shadow_frame.place(in_=login_btn, relx=0, rely=0.05,
                          relwidth=1, relheight=1)
        login_btn.lift()

        # زر استعادة كلمة المرور
        reset_password_btn = tk.Button(buttons_frame, text="نسيت كلمة المرور؟",
                                     bg="white", fg="#1976d2",
                                     activebackground="#e3f2fd",
                                     command=self.reset_password,
                                     **button_style)
        reset_password_btn.pack(fill="x", pady=5)

        # زر تسجيل الدخول كمدير
        admin_login_btn = tk.Button(buttons_frame, text="تسجيل الدخول كمدير",
                                  bg="#2196f3", fg="white",
                                  activebackground="#1976d2",
                                  command=self.login_as_admin,
                                  **button_style)
        admin_login_btn.pack(fill="x", pady=5)

        # إضافة تأثير الانتقال السلس
        def smooth_transition(widget, from_color, to_color, duration=200):
            # تحقق من صحة الألوان
            def is_valid_hex(color):
                return isinstance(color, str) and len(color) == 7 and color.startswith('#')
            
            if not is_valid_hex(from_color) or not is_valid_hex(to_color):
                print(f"خطأ: لون غير صالح - from: {from_color}, to: {to_color}")
                return
                
            steps = 20
            try:
                r1, g1, b1 = int(from_color[1:3], 16), int(from_color[3:5], 16), int(from_color[5:7], 16)
                r2, g2, b2 = int(to_color[1:3], 16), int(to_color[3:5], 16), int(to_color[5:7], 16)
                
                for i in range(steps + 1):
                    r = r1 + (r2 - r1) * i // steps
                    g = g1 + (g2 - g1) * i // steps
                    b = b1 + (b2 - b1) * i // steps
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    widget.after(i * (duration // steps), lambda c=color: widget.config(bg=c))
            except Exception as e:
                print(f"خطأ في تحويل الألوان: {e}")

        # إضافة تأثيرات للأزرار
        for btn, colors in [
            (login_btn, ("#1a237e", "#0d47a1")),
            (reset_password_btn, ("white", "#e3f2fd")),
            (admin_login_btn, ("#2196f3", "#1976d2"))
        ]:
            btn.bind("<Enter>", lambda e, b=btn, c=colors: smooth_transition(b, c[0], c[1]))
            btn.bind("<Leave>", lambda e, b=btn, c=colors: smooth_transition(b, c[1], c[0]))
            btn.bind("<Button-1>", lambda e, b=btn: b.config(relief="sunken"))
            btn.bind("<ButtonRelease-1>", lambda e, b=btn: b.config(relief="flat"))

        # التذييل
        footer_label = tk.Label(self.main_frame, 
                              text="© 2024 نظام توزيع المراقبين\nإعدادية الحسين بن الروح العلمية للبنين",
                              font=("NotoNaskhArabic", 11), bg="white", fg="#1a237e")
        footer_label.pack(side="bottom", pady=10)
    
    def _show_validation_error(self, entry, message):
        entry.config(highlightbackground="#f44336", highlightcolor="#f44336")
        tooltip = tk.Label(entry.master, text=message, fg="white", bg="#f44336",
                          font=("NotoNaskhArabic", 10), padx=5, pady=3)
        tooltip.place(in_=entry, relx=1, rely=0, x=10, anchor="w")
        entry.after(3000, lambda: (tooltip.destroy(), 
                                  entry.config(highlightbackground="#e3f2fd", 
                                              highlightcolor="#1976d2")))
    
    def _clear_validation_error(self, entry):
        entry.config(highlightbackground="#e3f2fd", highlightcolor="#1976d2")
        for widget in entry.master.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget("bg") == "#f44336":
                widget.destroy()
    
    def login_as_admin(self):
        """تسجيل الدخول كمدير النظام"""
        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, 'admin')
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, 'admin123')
        self.login()
    
    def reset_password(self):
        """إعادة تعيين كلمة المرور"""
        username = self.username_entry.get().strip()
        if not username:
            self._show_validation_error(self.username_entry, "يرجى إدخال اسم المستخدم أولاً")
            return
            
        # التحقق من وجود المستخدم
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT id, email FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if not user:
            self._show_validation_error(self.username_entry, "اسم المستخدم غير موجود")
            return
            
        if not user[1]:
            messagebox.showerror("خطأ", "لا يوجد بريد إلكتروني مسجل لهذا الحساب")
            return
        
        # إنشاء رمز تحقق عشوائي
        verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.db.set_verification_code(username, verification_code)
        
        # إرسال رمز التحقق عبر البريد الإلكتروني
        # TODO: تنفيذ إرسال البريد الإلكتروني
        
        # عرض رسالة نجاح
        messagebox.showinfo("إرسال رمز التحقق",
                          "تم إرسال رمز التحقق إلى بريدك الإلكتروني")
        
        # تسجيل العملية
        self.db.log_action(user[0], "طلب إعادة تعيين كلمة المرور", "تم إرسال رمز التحقق")
    
    def _create_input_field(self, parent, label, var_name, show=None):
        frame = tk.Frame(parent, bg="white")
        frame.pack(fill="x", pady=5)
        
        # تسمية الحقل
        label = tk.Label(frame, text=label, font=("NotoNaskhArabic", 12),
                        bg="white", fg="#1a237e")
        label.pack(side="top", anchor="w", padx=5)
        
        # حقل الإدخال
        entry = tk.Entry(frame, font=("Cairo", 12), show=show,
                        bd=0, highlightthickness=1,
                        highlightbackground="#e3f2fd",
                        highlightcolor="#1976d2")
        entry.pack(fill="x", padx=5, pady=3)
        
        # تخزين الإشارة إلى حقل الإدخال
        setattr(self, f"{var_name}_entry", entry)
    
    def login(self):
        try:
            # تعطيل زر تسجيل الدخول مؤقتاً
            login_btn = None
            for widget in self.window.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Frame):
                            for btn in child.winfo_children():
                                if isinstance(btn, tk.Button) and btn.cget('text') == 'تسجيل الدخول':
                                    login_btn = btn
                                    break
            if login_btn:
                login_btn['state'] = 'disabled'
                self.window.config(cursor="wait")
                self.window.update()
            
            # التحقق من المدخلات
            username = self.username_entry.get().strip()
            password = self.password_entry.get().strip()
            
            if not username:
                self._show_validation_error(self.username_entry, "يرجى إدخال اسم المستخدم")
                return
            
            if not password:
                self._show_validation_error(self.password_entry, "يرجى إدخال كلمة المرور")
                return

            try:
                # التحقق من المستخدم
                result = self.db.verify_user(username, password)
                
                if result is None:
                    messagebox.showerror("خطأ", "اسم المستخدم أو كلمة المرور غير صحيحة")
                    self.password_entry.delete(0, tk.END)  # مسح كلمة المرور
                    self.password_entry.focus()
                    return
                    
                user_id, role = result
                
                # تسجيل نجاح تسجيل الدخول
                self.db.log_action(user_id, "تسجيل دخول", f"تم تسجيل الدخول بنجاح كـ {role}")
                
                # فتح النظام الرئيسي
                from exam_system import ExamSupervisionSystem
                new_window = tk.Toplevel(self.window)
                new_window.withdraw()
                
                # تهيئة النظام
                app = ExamSupervisionSystem(new_window, user_id, role)
                
                # إخفاء نافذة تسجيل الدخول
                self.window.withdraw()
                new_window.deiconify()
                
                # تعيين إجراء الإغلاق
                def on_closing():
                    if messagebox.askokcancel("تأكيد", "هل تريد إغلاق النظام؟"):
                        self.db.log_action(user_id, "تسجيل خروج", "تم الخروج من النظام")
                        new_window.destroy()
                        self.window.destroy()
                        
                new_window.protocol("WM_DELETE_WINDOW", on_closing)
                
            except ValueError as ve:
                messagebox.showerror("خطأ", str(ve))
                self.password_entry.delete(0, tk.END)  # مسح كلمة المرور
                return
                
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ غير متوقع: {str(e)}")
            self.db.logger.error(f"خطأ في تسجيل الدخول: {e}")
        finally:
            # إعادة تفعيل زر تسجيل الدخول
            if login_btn:
                login_btn['state'] = 'normal'
            self.window.config(cursor="")
            self.window.update()

    def show_register_window(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        result = self.db.verify_user(username, password)
        
        if not result or result[1] != 'admin':
            messagebox.showerror("خطأ", "يجب تسجيل الدخول كمدير لإنشاء حساب جديد")
            return
        
        register_window = tk.Toplevel(self.window)
        register_window.title("إنشاء حساب جديد")
        try:
            register_window.iconbitmap("school_logo.ico")
        except:
            pass
        
        # تهيئة نافذة التسجيل في وسط الشاشة
        window_width = 400
        window_height = 500
        screen_width = register_window.winfo_screenwidth()
        screen_height = register_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        register_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # تكوين الشبكة
        register_window.grid_rowconfigure(0, weight=1)
        register_window.grid_columnconfigure(0, weight=1)
        
        # إطار التسجيل
        register_frame = ttk.Frame(register_window, style="Custom.TFrame")
        register_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # عنوان
        title_label = ttk.Label(register_frame, text="إنشاء حساب جديد", style="Title.TLabel")
        title_label.pack(pady=(0, 20))
        
        # حقول التسجيل
        form_frame = ttk.Frame(register_frame, style="Custom.TFrame")
        form_frame.pack(fill="x", padx=10)
        
        ttk.Label(form_frame, text="اسم المستخدم:", style="Custom.TLabel").pack(anchor="w")
        username_entry = ttk.Entry(form_frame, width=30, font=("Arial", 12))
        username_entry.pack(pady=(0, 10), fill="x")
        
        ttk.Label(form_frame, text="كلمة المرور:", style="Custom.TLabel").pack(anchor="w")
        password_entry = ttk.Entry(form_frame, show="*", width=30, font=("Arial", 12))
        password_entry.pack(pady=(0, 10), fill="x")
        
        ttk.Label(form_frame, text="تأكيد كلمة المرور:", style="Custom.TLabel").pack(anchor="w")
        confirm_password_entry = ttk.Entry(form_frame, show="*", width=30, font=("Arial", 12))
        confirm_password_entry.pack(pady=(0, 20), fill="x")
        
        # اختيار الدور
        ttk.Label(form_frame, text="الدور:", style="Custom.TLabel").pack(anchor="w")
        role_var = tk.StringVar(value="supervisor")
        
        roles = [
            ("مدير", "admin", "جميع الصلاحيات"),
            ("مراقب", "supervisor", "عرض التوزيعات وإدارة الإشعارات"),
            ("إداري", "staff", "إدارة المراقبين والقاعات والتوزيعات"),
            ("مشرف", "manager", "إدارة التوزيعات والإجازات والتقارير")
        ]
        
        for role_text, role_value, role_desc in roles:
            role_frame = ttk.Frame(form_frame)
            role_frame.pack(fill="x", pady=2)
            ttk.Radiobutton(role_frame, text=f"{role_text} - {role_desc}", 
                           value=role_value, variable=role_var).pack(anchor="w")
        
        def register(self):
            new_username = username_entry.get()
            new_password = password_entry.get()
            confirm_password = confirm_password_entry.get()
            role = role_var.get()
            
            if not all([new_username, new_password, confirm_password]):
                messagebox.showerror("خطأ", "يرجى ملء جميع الحقول")
                return
            
            if new_password != confirm_password:
                messagebox.showerror("خطأ", "كلمات المرور غير متطابقة")
                return
            
            # هنا يجب تشفير كلمة المرور قبل حفظها
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            if self.db.create_user(new_username, hashed_password.decode('utf-8'), role):
                # تسجيل الإجراء
                self.db.log_action(user_id, "إضافة مستخدم", f"تمت إضافة المستخدم: {new_username} ({role})")
                
                # إضافة إشعار للمستخدم الجديد
                cursor = self.db.conn.cursor()
                cursor.execute('SELECT id FROM users WHERE username = ?', (new_username,))
                new_user_id = cursor.fetchone()[0]
                
                welcome_message = f"مرحباً بك في نظام توزيع المراقبين. دورك: {role}"
                cursor.execute('INSERT INTO notifications (user_id, message, level) VALUES (?, ?, ?)',
                              (new_user_id, welcome_message, 'info'))
                
                self.db.conn.commit()
                messagebox.showinfo("نجاح", "تم إنشاء المستخدم بنجاح")
                register_window.destroy()
                refresh_users_list()
            else:
                messagebox.showerror("خطأ", "اسم المستخدم موجود بالفعل")
        
        ttk.Button(form_frame, text="إنشاء الحساب", command=register, 
                   style="Custom.TButton").pack(pady=20)
    
        def register(self):
            new_username = username_entry.get()
            new_password = password_entry.get()
            confirm_password = confirm_password_entry.get()
            role = role_var.get()
            
            if not all([new_username, new_password, confirm_password]):
                messagebox.showerror("خطأ", "يرجى ملء جميع الحقول")
                return
            
            if new_password != confirm_password:
                messagebox.showerror("خطأ", "كلمات المرور غير متطابقة")
                return
            
            # تشفير كلمة المرور باستخدام bcrypt
            try:
                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل في تشفير كلمة المرور: {str(e)}")
                return
                
            if self.db.create_user(new_username, hashed_password.decode('utf-8'), role):
                # تسجيل الإجراء
                self.db.log_action(user_id, "إضافة مستخدم", f"تمت إضافة المستخدم: {new_username} ({role})")
                
                # إضافة إشعار للمستخدم الجديد
                cursor = self.db.conn.cursor()
                cursor.execute('SELECT id FROM users WHERE username = ?', (new_username,))
                new_user_id = cursor.fetchone()[0]
                
                welcome_message = f"مرحباً بك في نظام توزيع المراقبين. دورك: {role}"
                cursor.execute('INSERT INTO notifications (user_id, message, level) VALUES (?, ?, ?)',
                              (new_user_id, welcome_message, 'info'))
                
                self.db.conn.commit()
                messagebox.showinfo("نجاح", "تم إنشاء المستخدم بنجاح")
                register_window.destroy()
                refresh_users_list()
            else:
                messagebox.showerror("خطأ", "اسم المستخدم موجود بالفعل")
        
        ttk.Button(form_frame, text="إنشاء الحساب", command=register, 
                   style="Custom.TButton").pack(pady=20)
    
    def _create_input_field(self, parent, label, var_name, show=None):
        frame = tk.Frame(parent, bg="white")
        frame.pack(fill="x", pady=8)
        
        # التسمية
        lbl = tk.Label(frame, text=label, font=("NotoNaskhArabic", 14, "bold"), bg="white", fg="#1a237e")
        lbl.pack(anchor="w")
        
        # حقل الإدخال
        entry = tk.Entry(frame, font=("NotoNaskhArabic", 14), bd=1, relief="solid",
                        highlightthickness=2, highlightbackground="#e3f2fd",
                        highlightcolor="#1976d2", insertbackground="#1a237e",
                        bg="white", fg="#000000", show=show)
        entry.pack(fill="x", pady=8, ipady=8)
        
        # إضافة تأثيرات تفاعلية
        def on_focus_in(event):
            entry.config(highlightbackground="#1976d2", highlightcolor="#1976d2")
            frame.config(bg="#f5f5f5")
            lbl.config(bg="#f5f5f5")
        
        def on_focus_out(event):
            entry.config(highlightbackground="#e3f2fd", highlightcolor="#1976d2")
            frame.config(bg="white")
            lbl.config(bg="white")
            
            # التحقق من صحة الحقل
            if var_name == "username" and entry.get():
                if len(entry.get()) < 3:
                    self._show_validation_error(entry, "اسم المستخدم يجب أن يكون 3 أحرف على الأقل")
                else:
                    self._clear_validation_error(entry)
            elif var_name == "password" and entry.get():
                if len(entry.get()) < 6:
                    self._show_validation_error(entry, "كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                else:
                    self._clear_validation_error(entry)
        
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        
        setattr(self, f"{var_name}_entry", entry)
    
    def run(self):
        self.window.mainloop()
    
    def show_login_window(self):
        """عرض نافذة تسجيل الدخول"""
        if not self.root.winfo_exists():
            self.root = tk.Tk()
            self.setup_login_window()
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.deiconify()
        self.root.mainloop()

if __name__ == "__main__":
    login_system = LoginSystem()
    login_system.run()


    def login_as_admin(self):
        # تعيين بيانات المدير الافتراضية
        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, 'admin')
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, 'admin123')
        # تنفيذ تسجيل الدخول
        self.login()