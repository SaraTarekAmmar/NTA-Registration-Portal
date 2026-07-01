import os

fnames = ['trainer/trainer-courses.html', 'trainer/trainer-attendance.html']
for fname in fnames:
    if os.path.exists(fname):
        with open(fname, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace('trainerFetch("/api/courses/trainer/id/" + trainerId)', 'trainerFetch("/api/courses/trainer/me/courses")')
        
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {fname}")
