import logging
from functools import wraps
from collections import defaultdict

class PermissionManager:
    def __init__(self):
        self.logger = logging.getLogger('permission_manager')
        self._setup_logging()
        self.role_permissions = {
            'admin': {
                'manage_users': True,
                'manage_roles': True,
                'manage_permissions': True,
                'view_logs': True,
                'manage_system': True,
                'manage_teachers': True,
                'manage_rooms': True,
                'manage_schedules': True,
                'generate_reports': True,
                'manage_backups': True,
                'view_statistics': True
            },
            'manager': {
                'manage_teachers': True,
                'manage_rooms': True,
                'manage_schedules': True,
                'generate_reports': True,
                'view_statistics': True,
                'view_logs': True
            },
            'supervisor': {
                'view_schedules': True,
                'view_rooms': True,
                'submit_preferences': True,
                'view_reports': True
            },
            'staff': {
                'view_schedules': True,
                'view_rooms': True,
                'generate_reports': True
            }
        }
        
        self.custom_permissions = defaultdict(dict)
    
    def _setup_logging(self):
        """إعداد نظام التسجيل"""
        if not self.logger.handlers:
            handler = logging.FileHandler('logs/permissions.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def get_role_permissions(self, role):
        """الحصول على صلاحيات الدور"""
        return self.role_permissions.get(role, {})
    
    def get_user_permissions(self, user_id, role):
        """الحصول على صلاحيات المستخدم (الدور + المخصصة)"""
        permissions = self.get_role_permissions(role).copy()
        custom = self.custom_permissions.get(user_id, {})
        permissions.update(custom)
        return permissions
    
    def add_custom_permission(self, user_id, permission, value=True):
        """إضافة صلاحية مخصصة لمستخدم"""
        try:
            self.custom_permissions[user_id][permission] = value
            self.logger.info(f'تم إضافة صلاحية {permission} للمستخدم {user_id}')
            return True
        except Exception as e:
            self.logger.error(f'خطأ في إضافة صلاحية: {str(e)}')
            return False
    
    def remove_custom_permission(self, user_id, permission):
        """إزالة صلاحية مخصصة من مستخدم"""
        try:
            if permission in self.custom_permissions[user_id]:
                del self.custom_permissions[user_id][permission]
                self.logger.info(f'تم إزالة صلاحية {permission} من المستخدم {user_id}')
            return True
        except Exception as e:
            self.logger.error(f'خطأ في إزالة صلاحية: {str(e)}')
            return False
    
    def check_permission(self, user_id, role, required_permission):
        """التحقق من وجود صلاحية محددة"""
        permissions = self.get_user_permissions(user_id, role)
        return permissions.get(required_permission, False)
    
    def require_permission(self, required_permission):
        """مزخرف للتحقق من الصلاحيات"""
        def decorator(func):
            @wraps(func)
            def wrapper(user_id, role, *args, **kwargs):
                if not self.check_permission(user_id, role, required_permission):
                    raise PermissionError(f'ليس لديك صلاحية: {required_permission}')
                return func(user_id, role, *args, **kwargs)
            return wrapper
        return decorator
    
    def add_role(self, role_name, permissions):
        """إضافة دور جديد"""
        try:
            if role_name in self.role_permissions:
                raise ValueError('الدور موجود بالفعل')
            self.role_permissions[role_name] = permissions
            self.logger.info(f'تم إضافة دور جديد: {role_name}')
            return True
        except Exception as e:
            self.logger.error(f'خطأ في إضافة دور: {str(e)}')
            return False
    
    def modify_role_permissions(self, role_name, permissions):
        """تعديل صلاحيات دور"""
        try:
            if role_name not in self.role_permissions:
                raise ValueError('الدور غير موجود')
            self.role_permissions[role_name].update(permissions)
            self.logger.info(f'تم تحديث صلاحيات الدور: {role_name}')
            return True
        except Exception as e:
            self.logger.error(f'خطأ في تعديل صلاحيات الدور: {str(e)}')
            return False
    
    def remove_role(self, role_name):
        """حذف دور"""
        try:
            if role_name in ['admin', 'manager', 'supervisor', 'staff']:
                raise ValueError('لا يمكن حذف الأدوار الأساسية')
            if role_name in self.role_permissions:
                del self.role_permissions[role_name]
                self.logger.info(f'تم حذف الدور: {role_name}')
            return True
        except Exception as e:
            self.logger.error(f'خطأ في حذف الدور: {str(e)}')
            return False