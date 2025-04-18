import json
import os
from typing import Dict, Optional

class LanguageManager:
    def __init__(self, default_language='ar'):
        self.default_language = default_language
        self.current_language = default_language
        self.translations: Dict[str, Dict[str, str]] = {}
        self.load_translations()
    
    def load_translations(self):
        """تحميل ملفات الترجمة"""
        translations_dir = 'translations'
        if not os.path.exists(translations_dir):
            os.makedirs(translations_dir)
            self._create_default_translations()
        
        for filename in os.listdir(translations_dir):
            if filename.endswith('.json'):
                language_code = filename.split('.')[0]
                with open(os.path.join(translations_dir, filename), 'r', encoding='utf-8') as f:
                    self.translations[language_code] = json.load(f)
    
    def _create_default_translations(self):
        """إنشاء ملفات الترجمة الافتراضية"""
        default_translations = {
            'ar': {
                'login': 'تسجيل الدخول',
                'username': 'اسم المستخدم',
                'password': 'كلمة المرور',
                'submit': 'إرسال',
                'cancel': 'إلغاء',
                'welcome': 'مرحباً بك',
                'logout': 'تسجيل الخروج',
                'settings': 'الإعدادات',
                'language': 'اللغة',
                'theme': 'المظهر',
                'dark_mode': 'الوضع الليلي',
                'light_mode': 'الوضع النهاري',
                'notifications': 'الإشعارات',
                'profile': 'الملف الشخصي',
                'help': 'المساعدة',
                'about': 'حول',
                'error': 'خطأ',
                'success': 'نجاح',
                'warning': 'تحذير',
                'info': 'معلومات',
                'save': 'حفظ',
                'edit': 'تعديل',
                'delete': 'حذف',
                'add': 'إضافة',
                'search': 'بحث',
                'filter': 'تصفية',
                'sort': 'ترتيب',
                'export': 'تصدير',
                'import': 'استيراد',
                'print': 'طباعة',
                'refresh': 'تحديث',
                'close': 'إغلاق',
                'confirm': 'تأكيد',
                'teachers': 'المراقبون',
                'rooms': 'القاعات',
                'schedules': 'الجداول',
                'reports': 'التقارير',
                'statistics': 'الإحصائيات',
                'backup': 'النسخ الاحتياطي',
                'restore': 'استعادة',
                'settings': 'الإعدادات',
                'permissions': 'الصلاحيات',
                'roles': 'الأدوار',
                'users': 'المستخدمون',
                'logs': 'السجلات'
            },
            'en': {
                'login': 'Login',
                'username': 'Username',
                'password': 'Password',
                'submit': 'Submit',
                'cancel': 'Cancel',
                'welcome': 'Welcome',
                'logout': 'Logout',
                'settings': 'Settings',
                'language': 'Language',
                'theme': 'Theme',
                'dark_mode': 'Dark Mode',
                'light_mode': 'Light Mode',
                'notifications': 'Notifications',
                'profile': 'Profile',
                'help': 'Help',
                'about': 'About',
                'error': 'Error',
                'success': 'Success',
                'warning': 'Warning',
                'info': 'Information',
                'save': 'Save',
                'edit': 'Edit',
                'delete': 'Delete',
                'add': 'Add',
                'search': 'Search',
                'filter': 'Filter',
                'sort': 'Sort',
                'export': 'Export',
                'import': 'Import',
                'print': 'Print',
                'refresh': 'Refresh',
                'close': 'Close',
                'confirm': 'Confirm',
                'teachers': 'Teachers',
                'rooms': 'Rooms',
                'schedules': 'Schedules',
                'reports': 'Reports',
                'statistics': 'Statistics',
                'backup': 'Backup',
                'restore': 'Restore',
                'settings': 'Settings',
                'permissions': 'Permissions',
                'roles': 'Roles',
                'users': 'Users',
                'logs': 'Logs'
            }
        }
        
        for lang, translations in default_translations.items():
            with open(f'translations/{lang}.json', 'w', encoding='utf-8') as f:
                json.dump(translations, f, ensure_ascii=False, indent=4)
    
    def set_language(self, language_code: str) -> bool:
        """تغيير اللغة الحالية"""
        if language_code in self.translations:
            self.current_language = language_code
            return True
        return False
    
    def get_text(self, key: str, language: Optional[str] = None) -> str:
        """الحصول على النص المترجم"""
        lang = language or self.current_language
        translations = self.translations.get(lang, self.translations[self.default_language])
        return translations.get(key, key)
    
    def add_translation(self, language_code: str, translations: Dict[str, str]) -> bool:
        """إضافة ترجمات جديدة"""
        try:
            if language_code not in self.translations:
                self.translations[language_code] = {}
            
            self.translations[language_code].update(translations)
            
            # حفظ الترجمات في الملف
            with open(f'translations/{language_code}.json', 'w', encoding='utf-8') as f:
                json.dump(self.translations[language_code], f, ensure_ascii=False, indent=4)
            
            return True
        except Exception:
            return False
    
    def get_available_languages(self) -> list:
        """الحصول على قائمة اللغات المتاحة"""
        return list(self.translations.keys())
    
    def get_language_name(self, language_code: str) -> str:
        """الحصول على اسم اللغة"""
        language_names = {
            'ar': 'العربية',
            'en': 'English',
            'fr': 'Français',
            'es': 'Español',
            'de': 'Deutsch'
        }
        return language_names.get(language_code, language_code)