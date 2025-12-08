# Meshy 2-Step Workflow: Preview → Refine → Download

## Overview

NexaAI now implements the complete Meshy.ai workflow to generate **best quality textured 3D models** automatically.

## The Workflow

### Step 1: Preview Task (Untextured Geometry)

When you click "Generate 3D Model":

1. **API Request** sent to Meshy with:
   - `mode: "preview"`
   - `prompt: "refined AI prompt"`
   - `target_polycount: 10k/30k/60k/100k` (based on quality selection)

2. **Preview Generation** (2-5 minutes):
   - Creates base 3D geometry
   - No textures applied
   - Fast generation
   - Lower cost

3. **Status**: Model shows as "Processing" in your history

### Step 2: Refine Task (Add Textures) - AUTOMATIC

When preview completes, the background job **automatically**:

1. **Calls Refine API**:
   ```python
   meshy_client.refine_task(preview_task_id)
   ```

2. **Refine Generation** (5-10 minutes):
   - Adds high-quality textures
   - Applies PBR materials
   - Enhances details
   - Production-ready quality

3. **Status**: Model continues showing "Processing" (now in refine stage)

### Step 3: Download GLB - AUTOMATIC

When refine completes, the background job **automatically**:

1. **Downloads GLB file**:
   ```python
   meshy_client.download_model(glb_url, local_path)
   ```

2. **Saves to**: `/media/models/{model_id}.glb`

3. **Updates MongoDB**:
   - `status: "completed"`
   - `glb_url: "https://meshy.ai/..."`
   - `glb_file_path: "/path/to/local/file.glb"`
   - `thumbnail_url: "..."`

4. **Status**: Model shows as "Completed" with download button

## Background Job

The background job checker runs continuously and:

- **Checks every 10 seconds** for model status updates
- **Detects stage** (preview or refine)
- **Triggers refine** when preview completes
- **Downloads GLB** when refine completes
- **Handles errors** at each stage

### Running the Background Job

**Development:**
```bash
python manage.py check_generation_status --loop --interval 10
```

**Production (systemd service):**
```bash
sudo systemctl start nexaai-job-checker
sudo systemctl enable nexaai-job-checker  # Auto-start on boot
```

### Systemd Service File

Create `/etc/systemd/system/nexaai-job-checker.service`:

```ini
[Unit]
Description=NexaAI Generation Job Checker
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/nexaai
Environment="DJANGO_SETTINGS_MODULE=nexaai.settings"
ExecStart=/usr/bin/python3 manage.py check_generation_status --loop --interval 10
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl start nexaai-job-checker
sudo systemctl enable nexaai-job-checker
```

## Database Schema

### GenerationJob Document

```python
{
    'model_id': ObjectId('...'),
    'meshy_task_id': '018a210d-...',  # Current task ID (preview or refine)
    'stage': 'preview' | 'refine',    # Current stage
    'preview_task_id': '018a210d-...', # Original preview task (set after refine starts)
    'meshy_status': 'PENDING' | 'IN_PROGRESS' | 'SUCCEEDED' | 'FAILED',
    'progress': 0-100,
    'last_checked_at': datetime,
    'created_at': datetime
}
```

### Model3D Document

```python
{
    'user_id': 'user_id_string',
    'prompt': 'original user prompt',
    'refined_prompt': 'AI-enhanced prompt',
    'quality': 'preview' | 'standard' | 'high' | 'ultra',
    'polygon_count': 10000 | 30000 | 60000 | 100000,
    'status': 'processing' | 'completed' | 'failed',
    'glb_url': 'https://meshy.ai/...',      # Meshy CDN URL
    'glb_file_path': '/media/models/...glb', # Local file path
    'thumbnail_url': 'https://meshy.ai/...',
    'created_at': datetime,
    'completed_at': datetime
}
```

## Timeline Example

**User generates "robot arm" at 10:00 AM**

| Time | Stage | Status | Action |
|------|-------|--------|--------|
| 10:00:00 | - | User clicks "Generate" | API creates preview task |
| 10:00:01 | Preview | PENDING | Background job starts monitoring |
| 10:00:10 | Preview | IN_PROGRESS | Job checker: "Preview 15% complete" |
| 10:02:30 | Preview | SUCCEEDED | Job checker detects completion |
| 10:02:31 | Refine | PENDING | Job checker calls refine API automatically |
| 10:02:40 | Refine | IN_PROGRESS | Job checker: "Refine 10% complete" |
| 10:08:15 | Refine | SUCCEEDED | Job checker detects completion |
| 10:08:16 | Download | - | Job checker downloads GLB (5.2 MB) |
| 10:08:20 | Complete | - | Model marked as completed |

**Total time**: ~8 minutes for high-quality textured model

## Quality Levels & Costs

| Quality | Polygons | Preview Cost | Refine Cost | Total Time |
|---------|----------|--------------|-------------|------------|
| Preview | 10,000 | 20 credits | 30 credits | ~5 min |
| Standard | 30,000 | 20 credits | 50 credits | ~8 min |
| High | 60,000 | 20 credits | 80 credits | ~12 min |
| Ultra | 100,000 | 20 credits | 120 credits | ~18 min |

*Note: Costs are estimates based on Meshy pricing. Check Meshy dashboard for actual costs.*

## Error Handling

### Preview Fails
- Model marked as `status: "failed"`
- Error message: "preview failed: {reason}"
- No refine attempted
- User notified

### Refine Fails
- Model marked as `status: "failed"`
- Error message: "refine failed: {reason}"
- Preview GLB may still be available (untextured)
- User notified

### Download Fails
- Model marked as `status: "failed"`
- Error message: "download failed: {reason}"
- GLB URL still available for manual download
- Retry mechanism can be implemented

## Monitoring

### Check Job Status
```bash
# View logs
tail -f /var/log/nexaai/job-checker.log

# Check service status
sudo systemctl status nexaai-job-checker

# View recent activity
journalctl -u nexaai-job-checker -n 50 -f
```

### MongoDB Queries

**Check processing models:**
```javascript
db.models.find({status: 'processing'}).pretty()
```

**Check generation jobs:**
```javascript
db.generation_jobs.find().sort({created_at: -1}).limit(10).pretty()
```

**Find models in refine stage:**
```javascript
db.generation_jobs.find({stage: 'refine'}).pretty()
```

## Troubleshooting

### Models Stuck in "Processing"

**Check if background job is running:**
```bash
ps aux | grep check_generation_status
```

**If not running, start it:**
```bash
python manage.py check_generation_status --loop --interval 10
```

### Refine Not Triggering

**Check job document:**
```javascript
db.generation_jobs.findOne({model_id: ObjectId('...')})
```

**Look for:**
- `stage: 'preview'` and `meshy_status: 'SUCCEEDED'` → Should trigger refine
- Check logs for errors in refine API call

### Download Failing

**Check permissions:**
```bash
ls -la /media/models/
```

**Create directory if missing:**
```bash
mkdir -p /media/models
chmod 755 /media/models
```

**Check disk space:**
```bash
df -h
```

## API Reference

### MeshyClient Methods

```python
from services.meshy_client import MeshyClient

client = MeshyClient()

# Create preview task
result = client.create_text_to_3d_task(
    prompt="a robot arm",
    art_style="realistic",
    target_polycount=30000
)
preview_task_id = result['result']

# Check status
status = client.get_task_status(preview_task_id)

# Refine (after preview completes)
refine_result = client.refine_task(preview_task_id)
refine_task_id = refine_result['result']

# Download GLB
client.download_model(
    url="https://meshy.ai/models/xyz.glb",
    output_path="/media/models/model_id.glb"
)
```

## Future Enhancements

Planned improvements:

- [ ] **Retry mechanism** for failed downloads
- [ ] **Webhook integration** for instant status updates (no polling)
- [ ] **Preview-only mode** option (skip refine for faster results)
- [ ] **Batch processing** for multiple models
- [ ] **Progress notifications** via WebSocket
- [ ] **Automatic cleanup** of old GLB files
- [ ] **CDN integration** for faster downloads
- [ ] **Thumbnail generation** from local GLB files

## Support

For issues:
1. Check logs: `tail -f /var/log/nexaai/job-checker.log`
2. Verify background job is running
3. Check MongoDB for job status
4. Review Meshy API dashboard for credits/errors
5. Submit feedback at https://help.manus.im
