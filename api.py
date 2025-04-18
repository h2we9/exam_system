from flask import Flask, request, jsonify
from database import Database
from session_manager import SessionManager
from security_monitor import SecurityMonitor
from functools import wraps
import logging
import json

app = Flask(__name__)
db = Database()
session_manager = SessionManager()
logger = logging.getLogger('api')

def setup_logging():
    """إعداد نظام التسجيل"""
    if not logger.handlers:
        handler = logging.FileHandler('logs/api.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

setup_logging()

def require_token(f):
    """مزخرف للتحقق من وجود رمز الجلسة"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'رمز الجلسة مطلوب'}), 401
        
        request_info = {
            'ip': request.remote_addr,
            'method': request.method,
            'path': request.path
        }
        
        if not session_manager.validate_session(token, request_info):
            return jsonify({'error': 'جلسة غير صالحة'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/login', methods=['POST'])
def login():
    """تسجيل الدخول وإنشاء جلسة"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        ip_address = request.remote_addr
        
        if not username or not password:
            return jsonify({'error': 'اسم المستخدم وكلمة المرور مطلوبان'}), 400
        
        # التحقق من القائمة السوداء
        if not session_manager.security_monitor.check_ip(ip_address):
            return jsonify({'error': 'تم حظر عنوان IP الخاص بك'}), 403
        
        user_id, role = db.verify_user(username, password)
        if not user_id:
            # تسجيل محاولة فاشلة
            if not session_manager.security_monitor.record_failed_attempt(username, ip_address):
                return jsonify({'error': 'تم حظر حسابك مؤقتاً بسبب محاولات متكررة'}), 403
            return jsonify({'error': 'اسم المستخدم أو كلمة المرور غير صحيحة'}), 401
        
        # الحصول على صلاحيات المستخدم
        permissions = db.get_user_permissions(role)
        
        # إنشاء جلسة جديدة
        token = session_manager.create_session(user_id, username, role, permissions, ip_address)
        
        return jsonify({
            'token': token,
            'user': {
                'id': user_id,
                'username': username,
                'role': role,
                'permissions': permissions
            }
        })
    except Exception as e:
        logger.error(f'خطأ في تسجيل الدخول: {str(e)}')
        return jsonify({'error': 'حدث خطأ أثناء تسجيل الدخول'}), 500

@app.route('/api/logout', methods=['POST'])
@require_token
def logout():
    """تسجيل الخروج وإنهاء الجلسة"""
    try:
        token = request.headers.get('Authorization')
        session_manager.end_session(token)
        return jsonify({'message': 'تم تسجيل الخروج بنجاح'})
    except Exception as e:
        logger.error(f'خطأ في تسجيل الخروج: {str(e)}')
        return jsonify({'error': 'حدث خطأ أثناء تسجيل الخروج'}), 500

@app.route('/api/users', methods=['GET'])
@require_token
def get_users():
    """الحصول على قائمة المستخدمين"""
    try:
        token = request.headers.get('Authorization')
        session_info = session_manager.get_session_info(token)
        
        if 'manage_users' not in session_info['permissions']:
            return jsonify({'error': 'ليس لديك صلاحية لعرض المستخدمين'}), 403
        
        users = db.get_all_users()
        return jsonify({'users': users})
    except Exception as e:
        logger.error(f'خطأ في استرجاع المستخدمين: {str(e)}')
        return jsonify({'error': 'حدث خطأ أثناء استرجاع المستخدمين'}), 500

@app.route('/api/users', methods=['POST'])
@require_token
def create_user():
    """إنشاء مستخدم جديد"""
    try:
        token = request.headers.get('Authorization')
        session_info = session_manager.get_session_info(token)
        
        if 'manage_users' not in session_info['permissions']:
            return jsonify({'error': 'ليس لديك صلاحية لإنشاء مستخدمين'}), 403
        
        data = request.get_json()
        required_fields = ['username', 'password', 'role']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'جميع الحقول المطلوبة غير متوفرة'}), 400
        
        success = db.create_user(
            data['username'],
            data['password'],
            data['role'],
            data.get('email'),
            data.get('phone'),
            data.get('experience')
        )
        
        if success:
            return jsonify({'message': 'تم إنشاء المستخدم بنجاح'})
        return jsonify({'error': 'فشل في إنشاء المستخدم'}), 500
    except Exception as e:
        logger.error(f'خطأ في إنشاء مستخدم: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@require_token
def delete_user(user_id):
    """حذف مستخدم"""
    try:
        token = request.headers.get('Authorization')
        session_info = session_manager.get_session_info(token)
        
        if 'manage_users' not in session_info['permissions']:
            return jsonify({'error': 'ليس لديك صلاحية لحذف المستخدمين'}), 403
        
        success = db.delete_user(user_id)
        if success:
            return jsonify({'message': 'تم حذف المستخدم بنجاح'})
        return jsonify({'error': 'فشل في حذف المستخدم'}), 500
    except Exception as e:
        logger.error(f'خطأ في حذف مستخدم: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/teachers', methods=['GET'])
@require_token
def get_teachers():
    """الحصول على قائمة المراقبين"""
    try:
        teachers = db.get_all_teachers()
        return jsonify({'teachers': teachers})
    except Exception as e:
        logger.error(f'خطأ في استرجاع المراقبين: {str(e)}')
        return jsonify({'error': 'حدث خطأ أثناء استرجاع المراقبين'}), 500

@app.route('/api/export', methods=['GET'])
@require_token
def export_data():
    """تصدير البيانات"""
    try:
        token = request.headers.get('Authorization')
        session_info = session_manager.get_session_info(token)
        
        if 'manage_users' not in session_info['permissions']:
            return jsonify({'error': 'ليس لديك صلاحية لتصدير البيانات'}), 403
        
        data = {
            'teachers': db.get_all_teachers(),
            'rooms': db.get_all_rooms(),
            'exam_dates': db.get_all_exam_dates(),
            'distributions': db.get_distributions()
        }
        
        return jsonify(data)
    except Exception as e:
        logger.error(f'خطأ في تصدير البيانات: {str(e)}')
        return jsonify({'error': 'حدث خطأ أثناء تصدير البيانات'}), 500

@app.route('/api/import', methods=['POST'])
@require_token
def import_data():
    """استيراد البيانات"""
    try:
        token = request.headers.get('Authorization')
        session_info = session_manager.get_session_info(token)
        
        if 'manage_users' not in session_info['permissions']:
            return jsonify({'error': 'ليس لديك صلاحية لاستيراد البيانات'}), 403
        
        data = request.get_json()
        
        # التحقق من صحة البيانات
        required_sections = ['teachers', 'rooms', 'exam_dates', 'distributions']
        if not all(section in data for section in required_sections):
            return jsonify({'error': 'البيانات غير مكتملة'}), 400
        
        # استيراد البيانات
        for teacher in data['teachers']:
            db.add_teacher(teacher['name'], teacher.get('experience', 'متوسط'))
        
        for room in data['rooms']:
            db.add_room(room['name'], room.get('capacity', 0))
        
        for date in data['exam_dates']:
            db.add_exam_date(date['date'])
        
        for dist in data['distributions']:
            db.add_distribution(
                dist['date_id'],
                dist['room_id'],
                dist['teacher1_id'],
                dist['teacher2_id']
            )
        
        return jsonify({'message': 'تم استيراد البيانات بنجاح'})
    except Exception as e:
        logger.error(f'خطأ في استيراد البيانات: {str(e)}')
        return jsonify({'error': 'حدث خطأ أثناء استيراد البيانات'}), 500

if __name__ == '__main__':
    app.run(debug=True)