import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import json
import os

class AdvancedScheduler:
    def __init__(self):
        self.languages = {
            'ar': {
                'days': ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'],
                'months': ['يناير', 'فبراير', 'مارس', 'إبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'],
                'errors': {
                    'no_teachers': 'لا يوجد مراقبين متاحين',
                    'no_rooms': 'لا توجد قاعات متاحة',
                    'scheduling_conflict': 'تعارض في الجدول'
                }
            },
            'en': {
                'days': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
                'months': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
                'errors': {
                    'no_teachers': 'No available supervisors',
                    'no_rooms': 'No available rooms',
                    'scheduling_conflict': 'Schedule conflict'
                }
            }
        }
        self.current_language = 'ar'
        
    def set_language(self, lang_code: str) -> None:
        """تغيير لغة النظام"""
        if lang_code in self.languages:
            self.current_language = lang_code
    
    def get_text(self, category: str, key: str) -> str:
        """الحصول على النص بناءً على اللغة الحالية"""
        return self.languages[self.current_language][category][key]
    
    def calculate_workload(self, teachers: List[Dict]) -> Dict[int, int]:
        """حساب عبء العمل لكل مراقب"""
        workload = {}
        for teacher in teachers:
            teacher_id = teacher['id']
            # حساب عدد المراقبات السابقة
            previous_supervisions = teacher.get('previous_supervisions', 0)
            # حساب الإجازات
            leaves = teacher.get('leaves', 0)
            # حساب العبء الكلي
            workload[teacher_id] = previous_supervisions - leaves
        return workload
    
    def check_availability(self, teacher: Dict, date: datetime, existing_schedule: List[Dict]) -> bool:
        """التحقق من توفر المراقب في وقت محدد"""
        # التحقق من الإجازات
        if 'leaves' in teacher:
            for leave in teacher['leaves']:
                leave_date = datetime.strptime(leave['date'], '%Y-%m-%d')
                if leave_date.date() == date.date():
                    return False
        
        # التحقق من التعارضات في الجدول
        for schedule in existing_schedule:
            if schedule['teacher_id'] == teacher['id']:
                schedule_date = datetime.strptime(schedule['date'], '%Y-%m-%d')
                if schedule_date.date() == date.date():
                    return False
        
        return True
    
    def distribute_supervisors(self, exams: List[Dict], teachers: List[Dict], rooms: List[Dict]) -> List[Dict]:
        """توزيع المراقبين على القاعات بشكل متوازن"""
        distribution = []
        workload = self.calculate_workload(teachers)
        
        for exam in exams:
            exam_date = datetime.strptime(exam['date'], '%Y-%m-%d')
            available_teachers = [
                t for t in teachers 
                if self.check_availability(t, exam_date, distribution)
            ]
            
            if not available_teachers:
                raise ValueError(self.get_text('errors', 'no_teachers'))
            
            # ترتيب المراقبين حسب عبء العمل
            available_teachers.sort(key=lambda t: workload[t['id']])
            
            for room in rooms:
                # تعيين مراقبين للقاعة
                supervisors = []
                needed_supervisors = room.get('required_supervisors', 2)
                
                for _ in range(needed_supervisors):
                    if not available_teachers:
                        break
                    
                    # اختيار المراقب الأقل عبئاً
                    selected_teacher = available_teachers.pop(0)
                    supervisors.append(selected_teacher['id'])
                    workload[selected_teacher['id']] += 1
                
                if len(supervisors) == needed_supervisors:
                    distribution.append({
                        'exam_id': exam['id'],
                        'room_id': room['id'],
                        'date': exam['date'],
                        'supervisors': supervisors
                    })
        
        return distribution
    
    def optimize_schedule(self, distribution: List[Dict]) -> List[Dict]:
        """تحسين الجدول لتقليل التعارضات وتحقيق التوازن"""
        # تنفيذ خوارزمية التحسين
        optimized = distribution.copy()
        changes_made = True
        
        while changes_made:
            changes_made = False
            for i in range(len(optimized)):
                for j in range(i + 1, len(optimized)):
                    # محاولة تبديل المراقبين لتحسين التوزيع
                    if self._try_swap_supervisors(optimized[i], optimized[j]):
                        changes_made = True
        
        return optimized
    
    def _try_swap_supervisors(self, schedule1: Dict, schedule2: Dict) -> bool:
        """محاولة تبديل المراقبين بين جدولين"""
        if schedule1['date'] == schedule2['date']:
            return False
        
        original_score = self._calculate_schedule_score(schedule1) + self._calculate_schedule_score(schedule2)
        
        # تبديل المراقبين
        temp = schedule1['supervisors']
        schedule1['supervisors'] = schedule2['supervisors']
        schedule2['supervisors'] = temp
        
        new_score = self._calculate_schedule_score(schedule1) + self._calculate_schedule_score(schedule2)
        
        if new_score > original_score:
            return True
        else:
            # إعادة المراقبين إلى مواقعهم الأصلية
            temp = schedule1['supervisors']
            schedule1['supervisors'] = schedule2['supervisors']
            schedule2['supervisors'] = temp
            return False
    
    def _calculate_schedule_score(self, schedule: Dict) -> float:
        """حساب درجة جودة الجدول"""
        score = 0.0
        # يمكن إضافة المزيد من المعايير لحساب الدرجة
        return score