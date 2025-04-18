import sqlite3

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

try:
    # إضافة عمود الخبرة إلى جدول المستخدمين
    cursor.execute("ALTER TABLE users ADD COLUMN experience TEXT DEFAULT 'متوسط'")
    conn.commit()
    print("✅ تم إضافة عمود الخبرة بنجاح")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print("ℹ️ عمود الخبرة موجود بالفعل")
    else:
        print(f"❌ خطأ: {e}")
finally:
    conn.close()