import requests
import re
import time
import random

BASE_URL = "http://127.0.0.1:8000"
USERNAME = "antigravity"
PASSWORD = "test1234"

# Setup session
session = requests.Session()

def get_csrf_token(response):
    if 'csrftoken' in session.cookies:
        return session.cookies['csrftoken']
    match = re.search(r'name="csrfmiddlewaretoken" value="(.+?)"', response.text)
    if match:
        return match.group(1)
    return None

def login():
    print(f"Logging in as {USERNAME}...")
    r = session.get(f"{BASE_URL}/login/")
    csrf = get_csrf_token(r)
    
    login_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "csrfmiddlewaretoken": csrf
    }
    
    headers = {"Referer": f"{BASE_URL}/login/"}
    r = session.post(f"{BASE_URL}/login/", data=login_data, headers=headers)
    
    if r.url == f"{BASE_URL}/login/":
        print("Login failed!")
        return False
    print("Login successful!")
    return True

def create_and_correct(prompt, correct_code):
    print(f"\nProcessing: '{prompt}'")
    
    # 1. Create Project
    r = session.get(f"{BASE_URL}/design/projects/")
    csrf = get_csrf_token(r)
    
    data = {
        "prompt": prompt,
        "csrfmiddlewaretoken": csrf
    }
    headers = {
        "Referer": f"{BASE_URL}/design/projects/",
        "X-CSRFToken": csrf
    }
    
    print("  Creating project...")
    r = session.post(f"{BASE_URL}/api/design/create-project/", data=data, headers=headers)
    if r.status_code != 200:
        print(f"  Failed to create project: {r.status_code}")
        return
    
    # Extract Project ID from response (it returns HTML with id="concept-{project_id}")
    match = re.search(r'id="concept-([a-f0-9]+)"', r.text)
    if not match:
        print("  Could not find project ID")
        return
    project_id = match.group(1)
    print(f"  Project ID: {project_id}")
    
    # 2. Approve Concept
    print("  Approving concept...")
    r = session.post(f"{BASE_URL}/api/design/approve-concept/{project_id}/", headers=headers)
    if r.status_code != 200:
        print(f"  Failed to approve concept: {r.status_code}")
        return
        
    # 3. Generate Overall Model
    print("  Generating overall model...")
    r = session.post(f"{BASE_URL}/api/design/generate-overall-model/{project_id}/", headers=headers)
    
    # This might take a few seconds usually, simulating wait or assuming synchronous return
    # The view seems synchronous based on code (it calls generate_overall_model and returns HttpResponse)
    if r.status_code != 200:
        print(f"  Generation request failed: {r.status_code}")
        # Proceed anyway to correct it?
    
    # 4. Submit Correction
    print("  Submitting correction...")
    feedback_data = {
        "model_type": "overall_model",
        "rating": "corrected",
        "corrected_code": correct_code,
        "correction_type": "code_fix",
        "feedback_text": "Auto-generated training example"
    }
    
    # Need to send as JSON
    headers['Content-Type'] = 'application/json'
    import json
    r = session.post(
        f"{BASE_URL}/api/design/feedback/{project_id}/", 
        data=json.dumps(feedback_data), 
        headers=headers
    )
    
    if r.status_code == 200:
        print("  ✓ Correction submitted successfully!")
    else:
        print(f"  ✗ Failed to submit correction: {r.status_code} - {r.text}")

def main():
    if not login():
        return

    examples = []
    
    # Spheres
    for d in [10, 20, 30, 40, 50, 100, 150, 200, 5, 25]:
        examples.append((
            f"A sphere with diameter {d}mm",
            f"""import cadquery as cq
result = cq.Workplane("XY").sphere({d/2})
"""
        ))
        
    # Cylinders
    for d, h in [(10, 20), (20, 10), (50, 100), (100, 50), (10, 100), (5, 10), (30, 30), (15, 45), (60, 10), (100, 200)]:
        examples.append((
            f"A cylinder with diameter {d}mm and height {h}mm",
            f"""import cadquery as cq
result = cq.Workplane("XY").circle({d/2}).extrude({h})
"""
        ))
        
    random.shuffle(examples)
    
    for i, (prompt, code) in enumerate(examples):
        print(f"--- Example {i+1}/20 ---")
        create_and_correct(prompt, code)
        time.sleep(1) # Be nice to the server

if __name__ == "__main__":
    main()
