# NexaAI Issues and Fixes

## Current Issues

### 1. 3D Viewer Loading Forever ❌

**Problem:** The 3D viewer shows "Loading 3D model..." forever and never displays the model.

**Root Cause:** The GLB URL from Meshy.ai might be:
- Empty/null in the database
- Invalid or expired
- Blocked by CORS

**How to Debug:**
1. Open browser console (F12) when viewing a model
2. Look for errors related to Three.js or model loading
3. Check the console.log output: "Loading model from: [URL]"

**Potential Fixes:**
- If URL is empty: The Meshy.ai API call might have failed
- If URL is invalid: Check Meshy.ai API key in `.env`
- If CORS error: Meshy.ai URLs should work, but might need proxy

### 2. Background Worker Required Every Time ❌

**Problem:** You must manually run the background worker in a separate terminal:
```bash
python manage.py check_generation_status --loop --interval 10
```

**Solution:** Add frontend polling so status updates automatically without a background worker.

### 3. No Error Messages ❌

**Problem:** When generation fails, users don't see helpful error messages.

**Solution:** Add better error handling and display errors in the UI.

## Recommended Fixes

### Fix 1: Add Frontend Polling (No Background Worker Needed)

Add HTMX polling to automatically check status every 5 seconds:

**In `templates/history.html`:**
```html
<!-- Add to each model card with status="processing" -->
<div hx-get="/api/models/{{ model.id }}/status" 
     hx-trigger="every 5s" 
     hx-swap="outerHTML">
    <!-- Model card content -->
</div>
```

**Add new endpoint in `models/views.py`:**
```python
@login_required
def model_status(request, model_id):
    model = get_object_or_404(Model3D, id=model_id, user=request.user)
    
    # If still processing, check Meshy.ai
    if model.status == 'processing':
        from services.meshy_client import check_generation_status
        check_generation_status(model)
        model.refresh_from_db()
    
    # Return updated card HTML
    return render(request, 'partials/model_card.html', {'model': model})
```

### Fix 2: Better 3D Viewer Error Handling

**Update `templates/viewer.html`:**
```javascript
loader.load(
    modelUrl,
    function(gltf) {
        // Success
        model = gltf.scene;
        // ... existing code ...
        loadingOverlay.style.display = 'none';
    },
    function(xhr) {
        // Progress
        const percent = (xhr.loaded / xhr.total * 100).toFixed(0);
        console.log(percent + '% loaded');
    },
    function(error) {
        // Error
        console.error('Error loading model:', error);
        loadingOverlay.innerHTML = `
            <div class="text-center text-white p-6">
                <p class="text-lg font-bold mb-2">Failed to load 3D model</p>
                <p class="text-sm mb-4">The model file could not be loaded.</p>
                <p class="text-xs text-gray-300">Check browser console for details</p>
                <a href="/history" class="mt-4 inline-block bg-purple-600 px-4 py-2 rounded">
                    Back to History
                </a>
            </div>
        `;
    }
);
```

### Fix 3: Add Manual "Check Status" Button

**In `templates/history.html`:**
```html
{% if model.status == 'processing' %}
<button 
    hx-post="/api/models/{{ model.id }}/check-status"
    hx-target="#model-{{ model.id }}"
    hx-swap="outerHTML"
    class="bg-blue-500 text-white px-3 py-1 rounded text-sm">
    Check Status Now
</button>
{% endif %}
```

### Fix 4: Debug Meshy.ai Integration

**Check if API is working:**
```bash
cd /home/ubuntu/nexaai
source venv/bin/activate
python manage.py shell
```

```python
from services.meshy_client import MeshyClient
from django.conf import settings

client = MeshyClient(settings.MESHY_API_KEY)

# Test API connection
try:
    result = client.create_text_to_3d("test cube")
    print("API works! Task ID:", result.get('id'))
except Exception as e:
    print("API Error:", e)
```

## Quick Fixes to Apply Now

### 1. Check Your .env File

Make sure these are set:
```bash
MESHY_API_KEY=msy_your_actual_key
LLM_API_KEY=your_openai_key
```

### 2. Check Browser Console

When the 3D viewer is stuck:
1. Press F12
2. Go to Console tab
3. Look for errors
4. Share the error message

### 3. Check Model in Database

```bash
cd /home/ubuntu/nexaai
source venv/bin/activate
python manage.py shell
```

```python
from models.models import Model3D
m = Model3D.objects.last()  # Get most recent model
print(f"Status: {m.status}")
print(f"GLB URL: {m.glb_url}")
print(f"Meshy Task ID: {m.meshy_task_id}")
```

If `glb_url` is empty, the Meshy.ai API didn't return a URL.

## Production Deployment

For production, use supervisor to auto-start the background worker:

```ini
[program:nexaai-worker]
command=/home/ubuntu/nexaai/venv/bin/python manage.py check_generation_status --loop --interval 10
directory=/home/ubuntu/nexaai
user=ubuntu
autostart=true
autorestart=true
```

Or implement the frontend polling solution (recommended for simplicity).
