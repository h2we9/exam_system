import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt

class ThemeManager:
    def __init__(self):
        self.light_theme = {
            'bg': '#f2f2f2',
            'fg': '#000000',
            'button_bg': '#e0e0e0',
            'button_fg': '#000000',
            'entry_bg': '#ffffff',
            'entry_fg': '#000000',
            'treeview_bg': '#ffffff',
            'treeview_fg': '#000000',
            'treeview_selected_bg': '#0078d7',
            'treeview_selected_fg': '#ffffff',
            'menu_bg': '#f0f0f0',
            'menu_fg': '#000000'
        }
        
        self.dark_theme = {
            'bg': '#1a1a1a',
            'fg': '#ffffff',
            'button_bg': '#333333',
            'button_fg': '#ffffff',
            'entry_bg': '#2a2a2a',
            'entry_fg': '#ffffff',
            'treeview_bg': '#2a2a2a',
            'treeview_fg': '#ffffff',
            'treeview_selected_bg': '#0078d7',
            'treeview_selected_fg': '#ffffff',
            'menu_bg': '#333333',
            'menu_fg': '#ffffff'
        }
        self.current_theme = None
        self.themes = {
            'light': self.light_theme,
            'dark': self.dark_theme
        }
    
    def apply_theme(self, root, theme_name='light'):
        try:
            theme = self.themes.get(theme_name, self.light_theme)
            # تطبيق السمة على النافذة الرئيسية
            root.configure(bg=theme['bg'])
            
            # تطبيق السمة على عناصر ttk
            style = ttk.Style()
            
            # تكوين نمط الأزرار
            style.configure('TButton',
                            background=theme['button_bg'],
                            foreground=theme['button_fg'])
            
            # تكوين نمط الإدخال
            style.configure('TEntry',
                            fieldbackground=theme['entry_bg'],
                            foreground=theme['entry_fg'])
            
            # تكوين نمط عرض الشجرة
            style.configure('Treeview',
                            background=theme['treeview_bg'],
                            foreground=theme['treeview_fg'],
                            fieldbackground=theme['treeview_bg'])
            
            style.map('Treeview',
                      background=[('selected', theme['treeview_selected_bg'])],
                      foreground=[('selected', theme['treeview_selected_fg'])])
            
            # تكوين نمط الإطارات
            style.configure('TFrame', background=theme['bg'])
            style.configure('TLabel', background=theme['bg'], foreground=theme['fg'])
            
            # تحديث القوائم
            self._update_menus(root, theme)
        except Exception as e:
            print(f"خطأ في تطبيق السمة: {str(e)}")
    
    def _update_menus(self, root, theme):
        try:
            menubar = root.nametowidget(root.winfo_parent()).nametowidget('!menu')
            self._configure_menu(menubar, theme)
        except Exception:
            pass
    
    def _configure_menu(self, menu, theme):
        menu.configure(bg=theme['menu_bg'], fg=theme['menu_fg'])
        for item in menu.winfo_children():
            if isinstance(item, tk.Menu):
                item.configure(bg=theme['menu_bg'], fg=theme['menu_fg'])
                self._configure_menu(item, theme)
    
    def configure_chart_theme(self, theme):
        plt.style.use('dark_background' if theme == 'dark' else 'default')
    
    def add_custom_theme(self, name, colors):
        self.themes[name] = colors