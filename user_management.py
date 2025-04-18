import tkinter as tk
from tkinter import ttk, messagebox
import bcrypt
from database import Database

class UserManagementWindow:
    def __init__(self, parent, db, current_user_id, logger):
        self.parent = parent
        self.db = db
        self.current_user_id = current_user_id
        self.logger = logger
        
        self.window = tk.Toplevel(parent)
        self.window.title("إدارة المستخدمين")
        self.window.geometry("800x600")
        
        self.create_widgets()
        self.load_users()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Users list
        list_frame = ttk.LabelFrame(main_frame, text="المستخدمون", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Treeview for users
        self.tree = ttk.Treeview(list_frame, columns=("username", "role", "email", "phone"), show="headings")
        self.tree.heading("username", text="اسم المستخدم")
        self.tree.heading("role", text="الدور")
        self.tree.heading("email", text="البريد الإلكتروني")
        self.tree.heading("phone", text="الهاتف")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="إضافة مستخدم", command=self.add_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="تعديل", command=self.edit_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="حذف", command=self.delete_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="تحديث", command=self.load_users).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="إغلاق", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def load_users(self):
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load users from database
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, username, role, email, phone FROM users ORDER BY username")
        
        for user in cursor.fetchall():
            self.tree.insert("", tk.END, values=user[1:], iid=user[0])
    
    def add_user(self):
        add_window = tk.Toplevel(self.window)
        add_window.title("إضافة مستخدم جديد")
        add_window.grab_set()  # جعل النافذة مودال
        
        # Form fields
        fields = [
            ("اسم المستخدم*", "username", ""),
            ("كلمة المرور*", "password", "", True),
            ("تأكيد كلمة المرور*", "confirm_password", "", True),
            ("البريد الإلكتروني*", "email", ""),
            ("رقم الهاتف", "phone", ""),
            ("الدور*", "role", "supervisor"),
            ("مستوى الخبرة*", "experience", "متوسط")
        ]
        
        entries = {}
        for i, (label, field, default, *options) in enumerate(fields):
            ttk.Label(add_window, text=label+":").grid(row=i, column=0, padx=5, pady=2, sticky="e")
            
            if field == "role":
                var = tk.StringVar(value=default)
                roles = [
                    ("مدير", "admin"),
                    ("مراقب", "supervisor"),
                    ("إداري", "staff"),
                    ("مشرف", "manager")
                ]
                
                for j, (text, value) in enumerate(roles):
                    ttk.Radiobutton(add_window, text=text, variable=var, value=value).grid(
                        row=i, column=1+j, padx=2, pady=2, sticky="w")
                
                entries[field] = var
            elif field == "experience":
                var = tk.StringVar(value=default)
                combo = ttk.Combobox(add_window, textvariable=var, 
                                    values=["مبتدئ", "متوسط", "خبير"])
                combo.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
                entries[field] = var
            else:
                var = tk.StringVar(value=default)
                show = "*" if "password" in field and options and options[0] else ""
                entry = ttk.Entry(add_window, textvariable=var, show=show)
                entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
                entries[field] = var
        
        # Submit button
        def submit():
            data = {k: v.get().strip() for k, v in entries.items()}
            
            # التحقق من صحة المدخلات
            if not all([data["username"], data["password"], data["confirm_password"], data["email"], data["role"], data["experience"]]):
                messagebox.showerror("خطأ", "يرجى ملء جميع الحقول المطلوبة (المميزة بعلامة *)")
                return


            # التحقق من تكرار اسم المستخدم
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (data["username"],))
            if cursor.fetchone():
                messagebox.showerror("خطأ", "اسم المستخدم موجود بالفعل")
                return

            # التحقق من قوة كلمة المرور
            if len(data["password"]) < 8:
                messagebox.showerror("خطأ", "يجب أن تكون كلمة المرور 8 أحرف على الأقل")
                return

            if not any(c.isupper() for c in data["password"]) or \
               not any(c.islower() for c in data["password"]) or \
               not any(c.isdigit() for c in data["password"]):
                messagebox.showerror("خطأ", "يجب أن تحتوي كلمة المرور على حروف كبيرة وصغيرة وأرقام")
                return
                
            if data["password"] != data["confirm_password"]:
                messagebox.showerror("خطأ", "كلمات المرور غير متطابقة")
                return

            # التحقق من صحة البريد الإلكتروني
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data["email"]):
                messagebox.showerror("خطأ", "البريد الإلكتروني غير صالح")
                return

            # التحقق من صحة رقم الهاتف (إذا تم إدخاله)
            if data["phone"] and not data["phone"].isdigit():
                messagebox.showerror("خطأ", "رقم الهاتف يجب أن يحتوي على أرقام فقط")
                return
                
            try:
                # Hash password using bcrypt
                hashed_password = bcrypt.hashpw(data["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                # Insert into database
                cursor = self.db.conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, password, role, email, phone, experience)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    data["username"],
                    hashed_password,
                    data["role"],
                    data["email"],
                    data["phone"],
                    data["experience"]
                ))
                
                self.db.conn.commit()
                self.logger.info(f"تمت إضافة مستخدم جديد: {data['username']}")
                messagebox.showinfo("نجاح", "تمت إضافة المستخدم بنجاح")
                
                # Add welcome notification
                new_user_id = cursor.lastrowid
                welcome_msg = f"مرحباً بك في نظام توزيع المراقبين. دورك: {data['role']}"
                cursor.execute("""
                    INSERT INTO notifications (user_id, message, level)
                    VALUES (?, ?, ?)
                """, (new_user_id, welcome_msg, "info"))
                
                self.db.conn.commit()
                add_window.destroy()
                self.load_users()
                
            except Exception as e:
                self.db.conn.rollback()
                messagebox.showerror("خطأ", f"فشل في إضافة المستخدم: {str(e)}")
        
        ttk.Button(add_window, text="حفظ", command=submit).grid(
            row=len(fields), column=0, columnspan=2, pady=10)
    
    def edit_user(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("خطأ", "يرجى اختيار مستخدم للتعديل")
            return
            
        user_id = selected[0]
        
        # التحقق من صلاحيات المستخدم
        if self.current_user_id != user_id and not self.is_admin():
            messagebox.showerror("خطأ", "ليس لديك صلاحية لتعديل هذا المستخدم")
            return
        
        # Get user data
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT username, role, email, phone, experience 
            FROM users WHERE id = ?
        """, (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            messagebox.showerror("خطأ", "لم يتم العثور على المستخدم")
            return
            
        edit_window = tk.Toplevel(self.window)
        edit_window.title("تعديل مستخدم")
        edit_window.grab_set()  # جعل النافذة مودال
        
        # Form fields
        fields = [
            ("اسم المستخدم*", "username", user_data[0], False, True),
            ("كلمة المرور الجديدة", "new_password", "", True),
            ("تأكيد كلمة المرور", "confirm_password", "", True),
            ("البريد الإلكتروني*", "email", user_data[2]),
            ("رقم الهاتف", "phone", user_data[3]),
            ("الدور*", "role", user_data[1]),
            ("مستوى الخبرة*", "experience", user_data[4])
        ]
        
        entries = {}
        for i, (label, field, default, *options) in enumerate(fields):
            ttk.Label(edit_window, text=label+":").grid(row=i, column=0, padx=5, pady=2, sticky="e")
            
            if field == "role":
                var = tk.StringVar(value=default)
                roles = [
                    ("مدير", "admin"),
                    ("مراقب", "supervisor"),
                    ("إداري", "staff"),
                    ("مشرف", "manager")
                ]
                
                for j, (text, value) in enumerate(roles):
                    ttk.Radiobutton(edit_window, text=text, variable=var, value=value).grid(
                        row=i, column=1+j, padx=2, pady=2, sticky="w")
                
                entries[field] = var
            elif field == "experience":
                var = tk.StringVar(value=default)
                combo = ttk.Combobox(edit_window, textvariable=var, 
                                    values=["مبتدئ", "متوسط", "خبير"])
                combo.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
                entries[field] = var
            else:
                var = tk.StringVar(value=default)
                show = "*" if "password" in field and options and options[0] else ""
                readonly = options[-1] if options else False
                
                if readonly:
                    entry = ttk.Label(edit_window, text=default)
                else:
                    entry = ttk.Entry(edit_window, textvariable=var, show=show)
                
                entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
                entries[field] = var
        
        # Submit button
        def submit():
            data = {k: v.get().strip() for k, v in entries.items()}
            
            # Password validation if changed
            if data["new_password"]:
                if data["new_password"] != data["confirm_password"]:
                    messagebox.showerror("خطأ", "كلمات المرور غير متطابقة")
                    return
            
            try:
                cursor = self.db.conn.cursor()
                
                if data["new_password"]:
                    # Update with new password
                    hashed_password = hashlib.sha256(data["new_password"].encode()).hexdigest()
                    cursor.execute("""
                        UPDATE users SET
                        role = ?,
                        email = ?,
                        phone = ?,
                        experience = ?,
                        password = ?
                        WHERE id = ?
                    """, (
                        data["role"],
                        data["email"],
                        data["phone"],
                        data["experience"],
                        hashed_password,
                        user_id
                    ))
                else:
                    # Update without password
                    cursor.execute("""
                        UPDATE users SET
                        role = ?,
                        email = ?,
                        phone = ?,
                        experience = ?
                        WHERE id = ?
                    """, (
                        data["role"],
                        data["email"],
                        data["phone"],
                        data["experience"],
                        user_id
                    ))
                
                self.db.conn.commit()
                self.logger.info(f"تم تعديل مستخدم: {data['username']}")
                messagebox.showinfo("نجاح", "تم تعديل بيانات المستخدم بنجاح")
                
                edit_window.destroy()
                self.load_users()
                
            except Exception as e:
                self.db.conn.rollback()
                messagebox.showerror("خطأ", f"فشل في تعديل المستخدم: {str(e)}")
        
        ttk.Button(edit_window, text="حفظ التغييرات", command=submit).grid(
            row=len(fields), column=0, columnspan=2, pady=10)
    
    def delete_user(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("خطأ", "يرجى اختيار مستخدم للحذف")
            return
            
        user_id = selected[0]
        username = self.tree.item(selected[0])["values"][0]
        
        if username == "admin":
            messagebox.showerror("خطأ", "لا يمكن حذف المستخدم الرئيسي")
            return
            
        if not messagebox.askyesno("تأكيد", f"هل أنت متأكد من حذف المستخدم {username}؟"):
            return
            
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            self.db.conn.commit()
            
            self.logger.info(f"تم حذف مستخدم: {username}")
            messagebox.showinfo("نجاح", f"تم حذف المستخدم {username}")
            self.load_users()
            
        except Exception as e:
            self.db.conn.rollback()
            messagebox.showerror("خطأ", f"فشل في حذف المستخدم: {str(e)}")


def validate_password(self, password):
    if len(password) < 8:
        return "كلمة المرور يجب أن تكون 8 أحرف على الأقل"
    if not any(char.isdigit() for char in password):
        return "كلمة المرور يجب أن تحتوي على رقم واحد على الأقل"
    if not any(char.isupper() for char in password):
        return "كلمة المرور يجب أن تحتوي على حرف كبير واحد على الأقل"
    return None
