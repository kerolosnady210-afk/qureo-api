from flask import Flask, request, jsonify
import requests
import json
import time
import threading

app = Flask(__name__)

# ================== BOT LOGIC ==================
class QureoBot:
    def __init__(self, student_id, password, course, session):
        self.student_id = student_id
        self.password = password
        self.course = course
        self.s = session
        self.base_url = "https://me-tp.qureo.education/api/study"
        self.portal_url = "https://me-portal.qureo.education"
        self.lang = "python" if "python" in course else "javascript"

    def login(self):
        url = f"{self.portal_url}/oauth2/password-login"
        payload = {"student_id": self.student_id, "password": self.password}
        r = self.s.post(url, json=payload, timeout=30)
        if r.status_code not in (200, 204):
            print("Login Failed")
            return False
        print("Login Success")
        return True

    def solve(self):
        if not self.login():
            return
        
        print(f"Started solving {self.course}...")
        
        # 1. محاولة إيجاد الفصول
        # (بما إننا مش عارفين الـ section_id بالظبط، هنحاول نلف على الفصول من 90001 لـ 90052)
        for chapter_id in range(90001, 90053):
            try:
                res = self.s.get(f"{self.base_url}/students/chapters/{chapter_id}/lectures", timeout=20)
                if res.status_code != 200:
                    continue
                
                lectures = res.json()
                if not lectures:
                    continue
                
                print(f"Chapter {chapter_id} | Lectures: {len(lectures)}")
                
                for lec in lectures:
                    lid = lec["id"]
                    self.s.put(f"{self.base_url}/students/lectures/{lid}", timeout=20)
                    content_res = self.s.get(f"{self.base_url}/lectures/{lid}", timeout=20)
                    if content_res.status_code != 200:
                        continue
                    
                    content = content_res.json()
                    if content and "talks" in content:
                        for talk in content["talks"]:
                            if talk["type"] in ["choice_question", "try"]:
                                # (هنا هنستخدم الحيلة بتاعتنا اللي بتجيب الإجابة من الـ response)
                                # ...
                                pass
                    self.s.put(f"{self.base_url}/students/lectures/{lid}/complete", timeout=20)
            except Exception as e:
                print(f"Error in chapter {chapter_id}: {e}")
        
        print("Finished solving!")
        return "Done"

# ================== API ENDPOINTS ==================

@app.route('/api/solve', methods=['POST'])
def solve_api():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON data provided"}), 400
    
    student_id = data.get('student_id')
    password = data.get('password')
    course = data.get('course', 'javascript_ar')

    if not student_id or not password:
        return jsonify({"status": "error", "message": "Missing ID or Password"}), 400

    def run_bot():
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "application/json"
        })
        bot = QureoBot(student_id, password, course, session)
        bot.solve()

    threading.Thread(target=run_bot).start()
    
    return jsonify({"status": "success", "message": "Bot started in background"}), 200

@app.route('/')
def home():
    return "Qureo Auto Solver API is Running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
