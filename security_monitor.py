import logging
from datetime import datetime, timedelta
from collections import defaultdict
import json

class SecurityMonitor:
    def __init__(self):
        self.logger = logging.getLogger('security_monitor')
        self._setup_logging()
        self.failed_attempts = defaultdict(list)
        self.suspicious_activities = defaultdict(int)
        self.ip_blacklist = set()
        self.load_blacklist()
        
    def _setup_logging(self):
        """إعداد نظام التسجيل"""
        if not self.logger.handlers:
            handler = logging.FileHandler('logs/security.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def load_blacklist(self):
        """تحميل القائمة السوداء من الملف"""
        try:
            with open('security/blacklist.json', 'r') as f:
                data = json.load(f)
                self.ip_blacklist = set(data.get('ip_addresses', []))
        except FileNotFoundError:
            self.save_blacklist()
    
    def save_blacklist(self):
        """حفظ القائمة السوداء إلى ملف"""
        try:
            with open('security/blacklist.json', 'w') as f:
                json.dump({'ip_addresses': list(self.ip_blacklist)}, f)
        except Exception as e:
            self.logger.error(f'خطأ في حفظ القائمة السوداء: {str(e)}')
    
    def check_ip(self, ip_address):
        """التحقق من عنوان IP"""
        return ip_address not in self.ip_blacklist
    
    def record_failed_attempt(self, username, ip_address):
        """تسجيل محاولة فاشلة لتسجيل الدخول"""
        current_time = datetime.now()
        self.failed_attempts[username].append(current_time)
        self.suspicious_activities[ip_address] += 1
        
        # حذف المحاولات القديمة (أكثر من ساعة)
        self.failed_attempts[username] = [
            attempt for attempt in self.failed_attempts[username]
            if current_time - attempt < timedelta(hours=1)
        ]
        
        # التحقق من عدد المحاولات الفاشلة
        if len(self.failed_attempts[username]) >= 5:
            self.logger.warning(f'محاولات فاشلة متكررة للمستخدم: {username} من العنوان: {ip_address}')
            self.ip_blacklist.add(ip_address)
            self.save_blacklist()
            return False
        
        return True
    
    def record_suspicious_activity(self, ip_address, activity_type):
        """تسجيل نشاط مشبوه"""
        self.suspicious_activities[ip_address] += 1
        self.logger.warning(f'نشاط مشبوه من العنوان {ip_address}: {activity_type}')
        
        if self.suspicious_activities[ip_address] >= 10:
            self.ip_blacklist.add(ip_address)
            self.save_blacklist()
            return False
        
        return True
    
    def analyze_session_activity(self, session_info, current_request):
        """تحليل نشاط الجلسة للكشف عن الأنماط المشبوهة"""
        suspicious = False
        reasons = []
        
        # التحقق من تغيير العنوان IP
        if 'last_ip' in session_info and session_info['last_ip'] != current_request['ip']:
            suspicious = True
            reasons.append('تغيير عنوان IP')
        
        # التحقق من الوقت بين الطلبات
        if 'last_activity' in session_info:
            time_diff = datetime.now() - datetime.fromisoformat(session_info['last_activity'])
            if time_diff.total_seconds() < 0.1:  # طلبات سريعة جداً
                suspicious = True
                reasons.append('طلبات متكررة بسرعة')
        
        # التحقق من نوع الطلب والمسار
        if current_request['method'] == 'POST' and 'admin' in current_request['path']:
            if session_info['role'] != 'admin':
                suspicious = True
                reasons.append('محاولة وصول غير مصرح')
        
        if suspicious:
            self.logger.warning(
                f'نشاط مشبوه للمستخدم {session_info["username"]} '
                f'من العنوان {current_request["ip"]}: {", ".join(reasons)}'
            )
            return False
        
        return True
    
    def clear_old_records(self):
        """تنظيف السجلات القديمة"""
        current_time = datetime.now()
        for username in list(self.failed_attempts.keys()):
            self.failed_attempts[username] = [
                attempt for attempt in self.failed_attempts[username]
                if current_time - attempt < timedelta(hours=24)
            ]
            if not self.failed_attempts[username]:
                del self.failed_attempts[username]
        
        # إعادة تعيين عداد النشاطات المشبوهة كل 24 ساعة
        self.suspicious_activities.clear()