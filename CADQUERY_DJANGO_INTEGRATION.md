# CadQuery Django Integration Documentation

## Overview

This document describes the integration of the CadQuery AI system with the Django web interface, allowing users to generate precise parametric CAD models directly from the website.

## What Was Integrated

The CadQuery AI system (previously only accessible via command line) is now fully integrated into the Django web application's 3-stage design workflow.

### Key Features

- **Dual Generation Options**: Users can choose between CadQuery (precise CAD) or Meshy (artistic 3D models)
- **Fast Generation**: 5-10 seconds per part (vs 10-20 minutes for Meshy)
- **Manufacturing-Ready Files**: Exports STEP (for CAD software) and STL (for 3D printing)
- **Editable Code**: Generated Python code is displayed and can be edited by users
- **Part-by-Part Control**: Users can generate parts individually or all at once

## Architecture

### Files Modified/Created

1. **models/design_schemas.py** (Modified)
   - Added CadQuery-specific fields to `PartSchema`:
     - `cadquery_code`: Stores generated Python code
     - `step_file_path`: Path to STEP file
     - `stl_file_path`: Path to STL file
     - `generation_error`: Error message if generation fails

2. **models/cadquery_views.py** (New)
   - `api_generate_part_cadquery`: Generates a single part using CadQuery
   - `api_approve_parts_cadquery`: Starts CadQuery generation workflow

3. **models/urls.py** (Modified)
   - Added CadQuery view imports
   - Added URL routes for CadQuery endpoints

4. **models/design_views.py** (Modified)
   - Updated part approval screen to show both CadQuery and Meshy options

5. **templates/design_projects.html** (Modified)
   - Updated Stage 3 description to mention CadQuery option

### Data Flow

```
User Request
    ↓
Django View (api_generate_part_cadquery)
    ↓
CadQueryAgent.generate_code(description)
    ↓
OpenAI GPT-4 (generates Python code)
    ↓
CadQueryExecutor.execute_and_export(code)
    ↓
CadQuery Library (generates 3D geometry)
    ↓
Export STEP and STL files
    ↓
Update MongoDB with results
    ↓
Return HTML with download links
```

## User Workflow

### 3-Stage Design Process

**Stage 1: Design Concept**
1. User enters design description (e.g., "a model rocket with parachute recovery system")
2. AI generates detailed design concept
3. User approves or requests refinement

**Stage 2: Part Breakdown**
1. AI splits design into manufacturable parts
2. AI recommends 3D printing or CNC for each part
3. User reviews part breakdown
4. **NEW:** User chooses generation method:
   - **CadQuery (Recommended)**: Precise parametric CAD
   - **Meshy-6 (Artistic)**: Textured 3D models

**Stage 3: CAD Generation (CadQuery)**
1. Each part shows a "Generate CAD Model" button
2. User clicks button for each part (or all at once)
3. CadQuery AI generates Python code (5-10 seconds)
4. Code is executed and STEP/STL files are exported
5. User can:
   - Download STEP file (for CAD software like FreeCAD, SolidWorks)
   - Download STL file (for 3D printing)
   - View/edit the generated Python code
   - Re-run generation with modifications

## API Endpoints

### CadQuery Generation Endpoints

#### Approve Parts for CadQuery Generation
```
POST /api/design/cadquery/approve-parts/<project_id>/
```

**Description**: Approves the part breakdown and prepares for CadQuery generation.

**Response**: HTML with individual "Generate CAD Model" buttons for each part.

#### Generate Individual Part
```
POST /api/design/cadquery/generate/<project_id>/<part_number>/
```

**Description**: Generates a single part using CadQuery AI.

**Process**:
1. Retrieves part data from MongoDB
2. Builds description from part metadata
3. Calls CadQueryAgent to generate Python code
4. Executes code with CadQueryExecutor
5. Exports STEP and STL files
6. Updates MongoDB with results
7. Returns HTML with download links and code viewer

**Response**: HTML with:
- Success/error message
- Download buttons for STEP and STL files
- Collapsible code viewer with generated Python code
- Progress indicator (X/Y parts completed)

## MongoDB Schema Updates

### PartSchema Fields

```python
{
    'part_number': int,
    'name': str,
    'description': str,
    'manufacturing_method': str,  # '3d_print' or 'cnc'
    'material_recommendation': str,
    'estimated_dimensions': dict,  # {x, y, z} in mm
    'complexity': str,  # 'low', 'medium', 'high'
    'quantity': int,
    'notes': str,
    'refined_prompt': str,
    'model_id': str,  # For Meshy generation
    
    # NEW: CadQuery generation data
    'cadquery_code': str,  # Generated Python code
    'step_file_path': str,  # Path to STEP file
    'stl_file_path': str,  # Path to STL file
    'generation_error': str,  # Error message if failed
    
    'status': str  # 'pending', 'generating', 'completed', 'failed'
}
```

## File Storage

### Directory Structure

```
/home/ubuntu/nexaai/media/cadquery_models/
    project_<project_id>/
        part_1_<safe_name>.step
        part_1_<safe_name>.stl
        part_2_<safe_name>.step
        part_2_<safe_name>.stl
        ...
```

### File Naming Convention

- Format: `part_<number>_<safe_name>.<extension>`
- Safe name: Lowercase, spaces and hyphens replaced with underscores
- Example: `part_1_nose_cone.step`, `part_2_body_tube.stl`

## UI Components

### Part Approval Screen

Shows two generation method options:

**CadQuery (Recommended)**
- Precise parametric CAD
- STEP/STL files
- Fast (5-10s/part)
- Editable code

**Meshy-6 (Artistic)**
- Textured 3D models
- Artistic style
- Slow (10-20min/part)
- GLB files

### Part Generation Cards

Each part displays:
- Part number and name
- Manufacturing method badge (3D Print / CNC)
- Description
- Material and dimensions
- "Generate CAD Model" button
- After generation:
  - Success message
  - Download buttons (STEP, STL)
  - Code viewer (collapsible)
  - Progress indicator

## Error Handling

### Generation Errors

If CadQuery generation fails:
1. Error is logged to Django logger
2. Part status set to 'failed'
3. Error message stored in `generation_error` field
4. User sees error message in UI
5. User can retry generation

### Common Errors

- **Code Generation Failed**: OpenAI API error or invalid response
- **Code Execution Failed**: Syntax error or CadQuery runtime error
- **File Export Failed**: Permission error or disk space issue

## Dependencies

### Python Packages (venv_cadquery)

```
cadquery==2.4.0
cadquery-ocp==7.7.2
Django==5.0.1
pymongo==4.10.1
djangorestframework==3.14.0
django-cors-headers==4.3.1
django-htmx==1.17.2
requests==2.32.5
python-dotenv==1.2.1
openai==2.9.0
```

### System Requirements

- Python 3.11
- MongoDB (for data storage)
- OpenAI API key (for code generation)
- CadQuery with OCP backend (for CAD generation)

## Deployment Notes

### Virtual Environment Setup

The application now uses `venv_cadquery` which includes both Django and CadQuery:

```bash
cd /home/ubuntu/nexaai
source venv_cadquery/bin/activate
pip install -r requirements.txt
pip install cadquery==2.4.0
```

### Running the Server

```bash
cd /home/ubuntu/nexaai
source venv_cadquery/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### Production Deployment

1. Install CadQuery on production server
2. Update virtual environment with all dependencies
3. Configure media file serving for STEP/STL downloads
4. Set up proper file permissions for media directory
5. Configure NGINX to serve media files
6. Update ALLOWED_HOSTS in settings.py

## Testing

### Manual Testing Checklist

- [ ] Create new design project
- [ ] Approve design concept
- [ ] Review part breakdown
- [ ] Select CadQuery generation method
- [ ] Generate individual part
- [ ] Verify STEP file downloads
- [ ] Verify STL file downloads
- [ ] View generated Python code
- [ ] Check MongoDB updates
- [ ] Verify progress tracking
- [ ] Test error handling (invalid description)
- [ ] Test multi-part generation

### Test Cases

See `/home/ubuntu/test_cadquery_ai.py` for automated tests of the core CadQuery system.

## Future Enhancements

### Potential Improvements

1. **Code Editing**: Allow users to edit generated code and re-run
2. **CAD Preview**: Render STEP files in browser using Three.js
3. **Design Versioning**: Track code changes and file versions
4. **Batch Generation**: Generate all parts with one click
5. **Assembly Instructions**: Generate assembly guide from parts
6. **Material Calculator**: Estimate material costs and print time
7. **Quality Presets**: Low/Medium/High detail options
8. **Custom Parameters**: Let users specify exact dimensions
9. **Design Templates**: Library of common CAD patterns
10. **Export Formats**: Add IGES, BREP, DXF support

## Troubleshooting

### Common Issues

**Issue**: "ModuleNotFoundError: No module named 'cadquery'"
- **Solution**: Activate venv_cadquery before running Django

**Issue**: "Failed to connect to MongoDB"
- **Solution**: Start MongoDB service

**Issue**: "Generation takes too long"
- **Solution**: Check OpenAI API rate limits, simplify description

**Issue**: "STEP file not found"
- **Solution**: Check media directory permissions, verify file paths

**Issue**: "Code execution failed"
- **Solution**: Check CadQuery installation, review generated code for errors

## Support

For issues or questions:
- Check Django logs: `/tmp/django.log`
- Check CadQuery test script: `/home/ubuntu/test_cadquery_ai.py`
- Review AI CAD system docs: `/home/ubuntu/nexaai/AI_CAD_SYSTEM_SUMMARY.md`
- Check GitHub issues: https://github.com/NexaFood/nexaai/issues

## Changelog

### Version 1.0 (December 2024)

- Initial integration of CadQuery AI system with Django
- Added dual generation options (CadQuery vs Meshy)
- Implemented part-by-part generation workflow
- Added STEP/STL file export and download
- Added code viewer for generated Python code
- Updated MongoDB schemas for CadQuery data
- Created comprehensive documentation

## License

Same as parent project (NexaAI).
