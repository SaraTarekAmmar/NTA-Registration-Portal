import urllib.request
import urllib.parse
import json
import os

def test_reports():
    # Admin is port 8002
    url = "http://localhost:8002/api/admin/auth/login"
    data = {"email": "admin@nta.edu.eg", "password": "NTA@Admin2026", "national_id": "29001011234567"}
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        resp = urllib.request.urlopen(req)
        token = json.loads(resp.read())['access_token']
        
        req2 = urllib.request.Request("http://localhost:8002/api/admin/reports", headers={'Authorization': f'Bearer {token}'})
        resp2 = urllib.request.urlopen(req2)
        print("Admin Reports /api/admin/reports status:", resp2.status)
        print("Admin Reports Data Snippet:", str(resp2.read()[:200]) + "...")
    except Exception as e:
        print("Admin Reports error:", e)

def test_trainer():
    # Trainer is port 8006
    url = "http://localhost:8006/api/auth/login"
    data = {"email": "trainer1@nta.edu.eg", "password": "NTA@Trainer2026", "national_id": "29001011234568"}
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        resp = urllib.request.urlopen(req)
        token = json.loads(resp.read())['access_token']
        
        req2 = urllib.request.Request("http://localhost:8006/api/courses/trainer/me/courses", headers={'Authorization': f'Bearer {token}'})
        resp2 = urllib.request.urlopen(req2)
        print("Trainer Courses /api/courses/trainer/me/courses status:", resp2.status)
        print("Trainer Courses Data Snippet:", str(resp2.read()[:200]) + "...")
    except Exception as e:
        # We might not have a seeded trainer1@nta.edu.eg, let's just show it works or fails cleanly
        print("Trainer error:", e)

def test_interviews():
    # Admission is port 7776
    url = "http://localhost:7776/api/admin/auth/login"
    # Actually admission doesn't have its own login, it shares admin db. Let's see if admin token works on 7776.
    pass

test_reports()
test_trainer()
