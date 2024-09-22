from flask import Flask, render_template, request, send_file, redirect, url_for
from moviepy.editor import VideoFileClip
import os
import pandas as pd
from io import BytesIO
import datetime

app = Flask(__name__)

# متغيرات لتخزين البيانات
video_data = []
study_schedule = []
goals = []

def calculate_video_durations(folder_path):
    global video_data
    video_data.clear()  # مسح البيانات السابقة

    total_duration_seconds = 0

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')):
                try:
                    clip = VideoFileClip(file_path)
                    duration = clip.duration  # المدة بالثواني
                    total_duration_seconds += duration  # جمع المدة الإجمالية
                    minutes = int(duration // 60)
                    seconds = int(duration % 60)
                    formatted_duration = f"{minutes:02}:{seconds:02}"  # صيغة MM:SS
                    video_name = os.path.splitext(file)[0]  # استخراج اسم الفيديو بدون الامتداد
                    video_data.append({'path': file_path, 'name': video_name, 'duration': formatted_duration, 'progress': 0})  # حفظ البيانات للفيديو مع التقدم 0%
                    clip.close()
                except Exception as e:
                    print(f"خطأ أثناء معالجة الملف {file_path}: {e}")

    # حساب المدة الإجمالية بالساعات والدقائق والثواني
    total_hours = int(total_duration_seconds // 3600)
    total_minutes = int((total_duration_seconds % 3600) // 60)
    total_seconds = int(total_duration_seconds % 60)
    total_duration_formatted = f"{total_hours}:{total_minutes:02}:{total_seconds:02}"

    return video_data, total_duration_formatted

def create_study_schedule(videos):
    global study_schedule
    schedule = []
    start_date = datetime.datetime.now().date()
    daily_duration_limit = 60
    current_day_videos = []
    current_day_duration = 0
    day_counter = 0

    for video in videos:
        duration_minutes = int(video['duration'].split(":")[0]) + int(video['duration'].split(":")[1]) / 60

        if current_day_duration + duration_minutes <= daily_duration_limit:
            current_day_videos.append({'name': video['name'], 'progress': video['progress'], 'duration': video['duration'], 'path': video['path']})
            current_day_duration += duration_minutes
        else:
            for vid in current_day_videos:
                vid['date'] = (start_date + datetime.timedelta(days=day_counter)).strftime("%Y-%m-%d")
                vid['day_name'] = (start_date + datetime.timedelta(days=day_counter)).strftime("%A")
            schedule.extend(current_day_videos)
            current_day_videos = [{'name': video['name'], 'progress': video['progress'], 'duration': video['duration'], 'path': video['path']}]
            current_day_duration = duration_minutes
            day_counter += 1

    if current_day_videos:
        for vid in current_day_videos:
            vid['date'] = (start_date + datetime.timedelta(days=day_counter)).strftime("%Y-%m-%d")
            vid['day_name'] = (start_date + datetime.timedelta(days=day_counter)).strftime("%A")
        schedule.extend(current_day_videos)

    study_schedule = schedule  # تحديث الدراسة بالجدول الزمني
    return schedule

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        folder_path = request.form['folder']
        video_data, total_duration = calculate_video_durations(folder_path)
        schedule = create_study_schedule(video_data)
        return render_template('results.html', video_data=video_data, total_duration=total_duration, schedule=schedule, goals=goals)
    return render_template('index.html')

@app.route('/download_excel', methods=['POST'])
def download_excel():
    global study_schedule
    # تأكد من أن الجدول الزمني يحتوي على البيانات قبل إنشاء Excel
    df = pd.DataFrame(study_schedule)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Study Schedule')
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='study_schedule.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/open_video', methods=['POST'])
def open_video():
    video_path = request.form['video_path']
    try:
        os.startfile(video_path)
    except Exception as e:
        print(f"خطأ أثناء فتح الفيديو {video_path}: {e}")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
