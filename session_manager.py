import time
import jwt
import logging
from datetime import datetime, timedelta
from functools import wraps
from security_monitor import SecurityMonitor

class SessionManager:
    def __init__(self, secret_key=None, session_timeout=3600):
        # قراءة المفتاح السري من متغيرات البيئة أو ملف التكوين
        self.secret_key = secret_key or self._load_secret_key()
        self.session_timeout = session_timeout
        self.active_sessions = {}
        self.logger = logging.getLogger('session_manager')
        self._setup_logging()
        self.security_monitor = SecurityMonitor()
        
    def _load_secret_key(self):
        """تحميل المفتاح السري من متغيرات البيئة أو ملف التكوين"""
        import os
        import json
        
        # محاولة قراءة المفتاح من متغيرات البيئة
        secret_key = os.getenv('SECRET_KEY')
        if secret_key:
            return secret_key
            
        # محاولة قراءة المفتاح من ملف التكوين
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                return config.get('secret_key', 'default-secret-key')
        except:
            return 'default-secret-key'
    
    def _setup_logging(self):
        """إعداد نظام التسجيل"""
        if not self.logger.handlers:
            handler = logging.FileHandler('logs/session.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def create_session(self, user_id, username, role, permissions, ip_address=None):
        """إنشاء جلسة جديدة للمستخدم"""
        try:
            # التحقق من القائمة السوداء
            if ip_address and not self.security_monitor.check_ip(ip_address):
                raise Exception('عنوان IP محظور')
                
            payload = {
                'user_id': user_id,
                'username': username,
                'role': role,
                'permissions': permissions,
                'exp': datetime.utcnow() + timedelta(seconds=self.session_timeout),
                'ip_address': ip_address,
                'last_activity': datetime.utcnow().isoformat()
            }
            token = jwt.encode(payload, self.secret_key, algorithm='HS256')
            self.active_sessions[token] = payload
            self.logger.info(f'تم إنشاء جلسة جديدة للمستخدم: {username}')
            return token
        except Exception as e:
            self.logger.error(f'خطأ في إنشاء الجلسة: {str(e)}')
            raise
    
    def validate_session(self, token, request_info=None):
        """التحقق من صلاحية الجلسة وتجديدها تلقائياً عند الحاجة"""
        try:
            if token not in self.active_sessions:
                return False
            
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            exp_time = datetime.fromtimestamp(payload['exp'])
            
            # التحقق من وقت انتهاء الصلاحية
            if datetime.utcnow() > exp_time:
                self.end_session(token)
                return False
            
            # تحليل النشاط للكشف عن الأنماط المشبوهة
            if request_info:
                if not self.security_monitor.analyze_session_activity(self.active_sessions[token], request_info):
                    self.end_session(token)
                    return False
                
                # تحديث معلومات النشاط
                self.active_sessions[token]['last_activity'] = datetime.utcnow().isoformat()
                self.active_sessions[token]['last_ip'] = request_info.get('ip')
            
            # تجديد الجلسة تلقائياً إذا بقي أقل من 5 دقائق على انتهائها
            if (exp_time - datetime.utcnow()) < timedelta(minutes=5):
                new_token = self.refresh_session(token)
                if new_token:
                    return new_token
            
            return True
        except jwt.ExpiredSignatureError:
            self.end_session(token)
            return False
        except Exception as e:
            self.logger.error(f'خطأ في التحقق من الجلسة: {str(e)}')
            return False
    
    def end_session(self, token):
        """إنهاء جلسة المستخدم"""
        try:
            if token in self.active_sessions:
                username = self.active_sessions[token]['username']
                del self.active_sessions[token]
                self.logger.info(f'تم إنهاء جلسة المستخدم: {username}')
        except Exception as e:
            self.logger.error(f'خطأ في إنهاء الجلسة: {str(e)}')
    
    def get_session_info(self, token):
        """الحصول على معلومات الجلسة"""
        try:
            if self.validate_session(token):
                return self.active_sessions.get(token)
            return None
        except Exception as e:
            self.logger.error(f'خطأ في استرجاع معلومات الجلسة: {str(e)}')
            return None
    
    def refresh_session(self, token):
        """تجديد مدة صلاحية الجلسة"""
        try:
            if not self.validate_session(token):
                return None
            
            current_session = self.active_sessions[token]
            new_payload = current_session.copy()
            new_payload['exp'] = datetime.utcnow() + timedelta(seconds=self.session_timeout)
            
            new_token = jwt.encode(new_payload, self.secret_key, algorithm='HS256')
            self.active_sessions[new_token] = new_payload
            del self.active_sessions[token]
            
            self.logger.info(f'تم تجديد جلسة المستخدم: {new_payload["username"]}')
            return new_token
        except Exception as e:
            self.logger.error(f'خطأ في تجديد الجلسة: {str(e)}')
            return None
    
    def require_session(self, func):
        """مزخرف للتحقق من وجود جلسة صالحة"""
        @wraps(func)
        def wrapper(token, *args, **kwargs):
            if not self.validate_session(token):
                raise Exception('جلسة غير صالحة')
            return func(token, *args, **kwargs)
        return wrapper
    
    def require_permission(self, required_permission):
        """مزخرف للتحقق من الصلاحيات"""
        def decorator(func):
            @wraps(func)
            def wrapper(token, *args, **kwargs):
                session_info = self.get_session_info(token)
                if not session_info:
                    raise Exception('جلسة غير صالحة')
                
                if required_permission not in session_info['permissions']:
                    raise Exception('ليس لديك الصلاحية المطلوبة')
                
                return func(token, *args, **kwargs)
            return wrapper
        return decorator