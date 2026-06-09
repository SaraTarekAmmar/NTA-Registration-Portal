import sys

file_path = r'd:\Work\NTA\NTA-Regestration-Portal - Final\admin\admin-profile.html'
name = "محمد أحمد علي"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    if name in content:
        print("MATCH_FULL_NAME_FOUND")
    else:
        print("MATCH_FULL_NAME_NOT_FOUND")

partial = "محمد"
if partial in content:
    print("PARTIAL_NAME_FOUND")
else:
    print("PARTIAL_NAME_NOT_FOUND")
