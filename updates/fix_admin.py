from database import Database
import time
import sqlite3

def main():
    max_retries = 3
    retry_delay = 1  # ثانية
    
    for attempt in range(max_retries):
        try:
            db = Database()
            
            print("\n0. جارٍ إنشاء الجداول الأساسية...")
            db.create_tables()
            
            # إضافة البيانات الأساسية
            print("\n0.1 جارٍ إضافة البيانات الأساسية...")
            try:
                db.create_initial_data()
            except Exception as e:
                print(f"❌ فشل إضافة البيانات الأساسية: {str(e)}")
                db.fix_foreign_keys()
                db.create_initial_data()
            
            print("\n1. جارٍ التحقق من حساب المدير...")
            if not db.check_admin_account():
                print("\n2. جارٍ إعادة إنشاء حساب المدير...")
                try:
                    db.create_default_admin()
                except Exception as e:
                    print(f"❌ فشل إنشاء المدير: {str(e)}")
                    # حاول إصلاح القيود الخارجية
                    db.fix_foreign_keys()
                    # حاول مرة أخرى
                    db.create_default_admin()
            
            print("\n3. التحقق النهائي:")
            db.check_admin_account()
            print("\n✅ تم الإصلاح. جرب تسجيل الدخول الآن بـ:")
            print("اسم المستخدم: admin")
            print("كلمة المرور: admin123")
            break
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                print(f"فشل المحاولة {attempt + 1}. قاعدة البيانات مقفلة، جاري إعادة المحاولة...")
                time.sleep(retry_delay)
                continue
            raise
        finally:
            if 'db' in locals():
                db.close()

if __name__ == "__main__":
    main()