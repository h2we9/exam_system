import requests
import json
import os
from tkinter import messagebox

class VersionManager:
    def __init__(self):
        self.current_version = "1.0.0"
        self.update_url = "https://raw.githubusercontent.com/h2we9/exam_system/main/updates"
        self.config_file = "config.json"
    
    def check_for_updates(self):
        try:
            response = requests.get(f"{self.update_url}/version.json")
            response.raise_for_status()
            
            try:
                version_data = response.json()
                latest_version = version_data['version']
                
                if self._compare_versions(latest_version, self.current_version) > 0:
                    if messagebox.askyesno("تحديث متوفر", 
                        f"يوجد إصدار جديد ({latest_version}). هل تريد التحديث الآن؟"):
                        self.download_update()
                        return True
                return False
            except json.JSONDecodeError as e:
                print(f"خطأ في تحليل بيانات التحديث: {e}")
                return False
        except Exception as e:
            print(f"خطأ في التحقق من التحديثات: {e}")
            return False
    
    def download_update(self):
        try:
            version_info = requests.get(f"{self.update_url}/version.json").json()
            response = requests.get(version_info['download_url'])
            with open("update.zip", "wb") as f:
                f.write(response.content)
            self._install_update()
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تحميل التحديث: {e}")
    
    def _install_update(self):
        # هنا يتم تنفيذ عملية التثبيت
        pass
    
    def _compare_versions(self, v1, v2):
        v1_parts = [int(x) for x in v1.split('.')]
        v2_parts = [int(x) for x in v2.split('.')]
        
        for i in range(3):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
        return 0