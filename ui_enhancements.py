import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from PIL import Image, ImageTk
import os

class UIEnhancer:
    def __init__(self):
        self.icons = {}
        self.chart_cache = {}  # كاش للرسوم البيانية
        self.load_icons()
        
    def load_icons(self):
        """تحميل الأيقونات من مجلد الموارد"""
        icons_data = {
            'add': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 4V20M4 12H20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>''',
            'edit': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M11 4H4V20H20V13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M18.5 2.5L21.5 5.5L12 15H9V12L18.5 2.5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>''',
            'delete': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 6H21M19 6V20C19 21.1046 18.1046 22 17 22H7C5.89543 22 5 21.1046 5 20V6M8 6V4C8 2.89543 8.89543 2 10 2H14C15.1046 2 16 2.89543 16 4V6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>''',
            'calendar': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
                <path d="M3 10H21" stroke="currentColor" stroke-width="2"/>
                <path d="M8 2V6M16 2V6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>''',
            'report': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M14 2V8H20M8 13H16M8 17H16M8 9H10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>'''
        }
        
        for name, svg_data in icons_data.items():
            self.icons[name] = svg_data
    
    def create_chart_frame(self, parent, title="", width=400, height=300):
        frame = ttk.LabelFrame(parent, text=title)
        frame.configure(style='Chart.TFrame')  # إضافة أنماط مخصصة
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        return frame
    
    def create_pie_chart(self, frame, data, labels, title=""):
        try:
            """إنشاء رسم بياني دائري"""
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.pie(data, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            ax.set_title(title)
            
            canvas = FigureCanvasTkAgg(fig, frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            return canvas
        except Exception as e:
            print(f"خطأ في إنشاء المخطط الدائري: {str(e)}")
            return None
    
    def create_bar_chart(self, frame, data, labels, title="", xlabel="", ylabel=""):
        """إنشاء رسم بياني شريطي"""
        fig, ax = plt.subplots(figsize=(6, 4))
        x = np.arange(len(labels))
        ax.bar(x, data)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        canvas = FigureCanvasTkAgg(fig, frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        return canvas
    
    def create_line_chart(self, frame, data, labels, title="", xlabel="", ylabel=""):
        """إنشاء رسم بياني خطي"""
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(labels, data, marker='o')
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        plt.xticks(rotation=45)
        
        canvas = FigureCanvasTkAgg(fig, frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        return canvas
    
    def create_export_button(self, parent, chart_type, data):
        """زر لتصدير الرسوم البيانية"""
        btn = ttk.Button(parent, text="تصدير", command=lambda: self.export_chart(chart_type, data))
        return btn
    
    def get_icon(self, name, color="#000000"):
        """الحصول على أيقونة SVG مع لون محدد"""
        if name in self.icons:
            svg_data = self.icons[name].replace('currentColor', color)
            return svg_data
        return None
    
    def create_styled_button(self, parent, text, icon_name=None, command=None):
        """إنشاء زر مخصص مع أيقونة"""
        btn = ttk.Button(parent, text=text, command=command)
        if icon_name and icon_name in self.icons:
            icon_data = self.get_icon(icon_name)
            # تحويل SVG إلى صورة وإضافتها للزر
            # ... الكود المطلوب ...
        return btn
    
    def create_statistics_window(self, parent, title="الإحصائيات"):
        """إنشاء نافذة الإحصائيات مع الرسوم البيانية"""
        stats_window = tk.Toplevel(parent)
        stats_window.title(title)
        stats_window.geometry("800x600")
        
        # إنشاء إطارات للرسوم البيانية
        charts_frame = ttk.Frame(stats_window)
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # تقسيم الإطار إلى شبكة 2×2
        for i in range(2):
            charts_frame.grid_columnconfigure(i, weight=1)
            charts_frame.grid_rowconfigure(i, weight=1)
        
        return stats_window, charts_frame