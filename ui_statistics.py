import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.font_manager as fm
import numpy as np
from babel.dates import format_date
from babel.numbers import format_decimal
from babel import Locale

class StatisticsUI:
    def __init__(self, db):
        self.db = db
        self.cache = {}  # إضافة كاش للبيانات
        # تهيئة الخط العربي لـ Matplotlib
        font_path = 'fonts/Cairo-Regular.ttf'
        self.arabic_font = fm.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = self.arabic_font.get_name()
    
    def create_statistics_window(self, parent):
        stats_window = tk.Toplevel(parent)
        stats_window.title("إحصائيات النظام")
        stats_window.geometry("1200x900")  # زيادة الحجم
        stats_window.configure(bg='#f0f0f0')  # إضافة لون خلفية
        
        # إطار رئيسي
        main_frame = ttk.Frame(stats_window, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # تكوين الشبكة
        stats_window.grid_rowconfigure(0, weight=1)
        stats_window.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # عنوان
        title_label = ttk.Label(main_frame, text="إحصائيات النظام", font=("Cairo", 18, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # إطار للرسوم البيانية
        charts_frame = ttk.Frame(main_frame)
        charts_frame.grid(row=1, column=0, sticky="nsew")
        charts_frame.grid_columnconfigure(0, weight=1)
        charts_frame.grid_columnconfigure(1, weight=1)
        
        # إنشاء الرسوم البيانية
        self.create_pie_chart(charts_frame)
        self.create_bar_chart(charts_frame)
        self.create_line_chart(charts_frame)
        refresh_btn = ttk.Button(main_frame, text="تحديث", command=self.refresh_charts)
        refresh_btn.grid(row=2, column=0, pady=10)
    
    def create_pie_chart(self, parent):
        """إنشاء رسم بياني دائري لتوزيع المراقبين"""
        fig, ax = plt.subplots(figsize=(5, 4))
        
        # الحصول على البيانات من قاعدة البيانات
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT role, COUNT(*) FROM users GROUP BY role')
        data = cursor.fetchall()
        
        labels = [row[0] for row in data]
        sizes = [row[1] for row in data]
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
        
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.set_title('توزيع المستخدمين حسب الدور', fontproperties=self.arabic_font)
        
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, padx=10, pady=10)
    
    def create_bar_chart(self, parent):
        """إنشاء رسم بياني شريطي لعدد المراقبين في كل قاعة"""
        fig, ax = plt.subplots(figsize=(5, 4))
        
        # الحصول على البيانات من قاعدة البيانات
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT room_name, COUNT(DISTINCT teacher_id) FROM assignments GROUP BY room_name')
        data = cursor.fetchall()
        
        rooms = [row[0] for row in data]
        counts = [row[1] for row in data]
        
        ax.bar(rooms, counts, color='#66b3ff')
        ax.set_title('عدد المراقبين في كل قاعة', fontproperties=self.arabic_font)
        ax.set_xlabel('القاعات', fontproperties=self.arabic_font)
        ax.set_ylabel('عدد المراقبين', fontproperties=self.arabic_font)
        plt.xticks(rotation=45)
        
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=1, padx=10, pady=10)
    
    def create_line_chart(self, parent):
        """إنشاء رسم بياني خطي لتوزيع المراقبين على مدار الأيام"""
        fig, ax = plt.subplots(figsize=(10, 4))
        
        # الحصول على البيانات من قاعدة البيانات
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT exam_date, COUNT(DISTINCT teacher_id) FROM assignments GROUP BY exam_date ORDER BY exam_date')
        data = cursor.fetchall()
        
        dates = [row[0] for row in data]
        counts = [row[1] for row in data]
        
        ax.plot(dates, counts, marker='o', color='#99ff99')
        ax.set_title('توزيع المراقبين على مدار الأيام', fontproperties=self.arabic_font)
        ax.set_xlabel('التاريخ', fontproperties=self.arabic_font)
        ax.set_ylabel('عدد المراقبين', fontproperties=self.arabic_font)
        plt.xticks(rotation=45)
        
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().grid(row=1, column=0, columnspan=2, padx=10, pady=10)
    
    def create_pie_chart(self, parent):
        try:
            """إنشاء رسم بياني دائري لتوزيع المراقبين"""
            fig, ax = plt.subplots(figsize=(5, 4))
            
            # الحصول على البيانات من قاعدة البيانات
            cursor = self.db.conn.cursor()
            cursor.execute('SELECT role, COUNT(*) FROM users GROUP BY role')
            data = cursor.fetchall()
            
            labels = [row[0] for row in data]
            sizes = [row[1] for row in data]
            colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
            
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title('توزيع المستخدمين حسب الدور', fontproperties=self.arabic_font)
            
            canvas = FigureCanvasTkAgg(fig, parent)
            canvas.draw()
            canvas.get_tk_widget().grid(row=0, column=0, padx=10, pady=10)
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء إنشاء المخطط الدائري: {str(e)}")
    
    def add_export_button(self, parent):
        export_btn = ttk.Button(parent, text="تصدير البيانات", command=self.export_data)
        export_btn.grid(row=3, column=0, pady=10)