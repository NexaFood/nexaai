import json
import time
import re
import urllib.request
import urllib.parse
import http.cookiejar
import socket

BASE_URL = "http://localhost:8000"
USERNAME = "antigravity"
PASSWORD = "test1234"

# Setup Opener with CookieJar
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

def get_csrf_token():
    for cookie in cookie_jar:
        if cookie.name == 'csrftoken':
            return cookie.value
    return None

def make_request(url, method='GET', data=None, headers=None, use_json=False):
    if headers is None:
        headers = {}
    
    # Add common headers
    csrf_token = get_csrf_token()
    if csrf_token:
        headers['X-CSRFToken'] = csrf_token
    
    headers['Referer'] = f"{BASE_URL}/design/projects/"
    
    encoded_data = None
    if data:
        if use_json:
            encoded_data = json.dumps(data).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        else:
            encoded_data = urllib.parse.urlencode(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    
    try:
        with opener.open(req, timeout=30) as response:
            return response.read().decode('utf-8'), response.getcode()
    except urllib.error.URLError as e:
         if isinstance(e.reason, socket.timeout):
             print("  Request Timeout")
             return None, 408
         print(f"  URL Error: {e.reason}")
         return None, 0
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code}: {e.reason}")
        return e.read().decode('utf-8'), e.code
    except Exception as e:
        print(f"  Request Exception: {e}")
        return None, 0

def login():
    print("Logging in...")
    # 1. Get Log in page to set CSRF cookie
    _, _ = make_request(f"{BASE_URL}/login/")
    
    csrf_token = get_csrf_token()
    if not csrf_token:
        print("  Failed to get CSRF token")
        return False
    
    # 2. Post credentials
    login_data = {
        'username': USERNAME,
        'password': PASSWORD,
        'csrfmiddlewaretoken': csrf_token
    }
    
    # We need to set Referer for login specifically
    headers = {'Referer': f"{BASE_URL}/login/"}
    
    body, code = make_request(f"{BASE_URL}/login/", method='POST', data=login_data, headers=headers)
    
    # Login redirect check
    if code != 200:
        print(f"  Login POST status: {code}")
        
    return True

def check_status(project_id):
    url = f"{BASE_URL}/design/projects/{project_id}/"
    body, code = make_request(url)
    if not body: return "pending"
    
    if "Overall model generated successfully" in body:
        return "completed"
    if "Overall model generation failed" in body:
        return "failed"
    return "pending"

def process_item(item_index, prompt, correct_code):
    print(f"\nProcessing Item {item_index}: {prompt}")
    
    # 1. Create Project
    body, code = make_request(
        f"{BASE_URL}/api/design/create-project/",
        method='POST',
        data={'prompt': prompt}
    )
    if code != 200:
        print(f"  Error creating project: {code}")
        return False
    
    match = re.search(r'id="concept-([a-f0-9]+)"', body)
    if not match:
        print("  Could not find project ID in response.")
        return False
    project_id = match.group(1)
    print(f"  Created Project ID: {project_id}")
    
    # 2. Approve Concept
    body, code = make_request(
        f"{BASE_URL}/api/design/approve-concept/{project_id}/",
        method='POST'
    )
    if code != 200:
        print(f"  Error approving concept: {code}")
        return False
        
    # 3. Generate Overall Model
    print("  Generating overall model...")
    body, code = make_request(
        f"{BASE_URL}/api/design/generate-overall-model/{project_id}/",
        method='POST'
    )
    
    # 4. Wait for completion
    start_time = time.time()
    status = "pending"
    while time.time() - start_time < 120:
        status = check_status(project_id)
        if status in ['completed', 'failed']:
            print(f"  Generation finished with status: {status}")
            break
        time.sleep(5)
    
    if status not in ['completed', 'failed']:
         print("  Timeout waiting for generation.")
    
    # 5. Submit Correction
    print("  Submitting correction...")
    feedback_data = {
        'model_type': 'overall_model',
        'rating': 'corrected',
        'corrected_code': correct_code,
        'correction_type': 'model_improvement',
        'feedback_text': ''
    }
    
    body, code = make_request(
        f"{BASE_URL}/api/design/feedback/{project_id}/",
        method='POST',
        data=feedback_data,
        use_json=True
    )
    
    if code == 200:
        print("  Correction submitted successfully.")
        return True
    else:
         print(f"  Error submitting feedback: {code}")
         print(f"  Response: {body}")
         return False

def main():
    try:
        with open('training_plan.json', 'r') as f:
            plan = json.load(f)
    except FileNotFoundError:
        print("training_plan.json not found.")
        return
    
    # Start from Item 32 (Index 31)
    items_to_process = plan[31:] 
    
    print(f"Resuming API automation (urllib) for {len(items_to_process)} items (Items 32-100)...")
    
    if not login():
        print("Could not login.")
        return

    success_count = 0
    for i, item in enumerate(items_to_process):
        item_index = i + 32
        if process_item(item_index, item['prompt'], item['code']):
            success_count += 1
        else:
            print(f"Failed item {item_index}")
        
        time.sleep(1)

    print(f"Finished. Success: {success_count}/{len(items_to_process)}")

if __name__ == "__main__":
    main()
