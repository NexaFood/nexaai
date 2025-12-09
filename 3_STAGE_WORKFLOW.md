# 3-Stage Design Workflow Documentation

## Overview

NexaAI now features a comprehensive **3-stage design workflow** that takes you from a simple idea to a complete set of manufacturable 3D models with AI-powered assistance at every step.

## The Workflow

### Stage 1: Design Concept Generation

**What happens:**
1. You enter a design idea (e.g., "model rocket", "quadcopter drone", "robot arm")
2. AI (GPT-4.1-mini) generates a detailed design concept including:
   - Comprehensive description (2-3 paragraphs)
   - Design type/category
   - Key features and components (5-10 major features)
   - Estimated complexity (low/medium/high)
   - Estimated parts count

**User action:**
- **Approve** → Move to Stage 2 (Part Breakdown)
- **Refine** → Request changes to the concept (coming soon)

**Example output for "model rocket":**
```
Design Type: Vehicle
Complexity: Medium
Estimated Parts: 45

Description:
A model rocket designed for stable flight and parachute recovery. The design features
a streamlined nose cone for aerodynamic efficiency, multiple body tube sections for
structural integrity, and a fin assembly for flight stability. The rocket includes
a motor mount system, parachute deployment mechanism, and electronics bay for
tracking and telemetry...

Key Features:
- Aerodynamic nose cone with shock cord attachment
- Multi-section body tube (4 sections)
- Fin assembly (4 fins) with through-the-wall mounting
- Motor mount with centering rings
- Parachute compartment with deployment system
- Electronics bay for altimeter/GPS
- Launch lug system
- Recovery harness and shock cord
```

---

### Stage 2: Part Breakdown & Manufacturing Recommendations

**What happens:**
1. AI analyzes the approved concept
2. Breaks it down into **individual manufacturable parts** (can be 50-200+ parts!)
3. For each part, determines:
   - **Manufacturing method** (3D Print or CNC)
   - Material recommendation
   - Estimated dimensions
   - Complexity level
   - Quantity needed
   - Assembly notes

**Manufacturing Decision Logic:**

**3D Print** - Best for:
- Complex geometries, curves, organic shapes
- Internal structures, hollow parts
- Lightweight components
- Parts with intricate details
- Brackets, mounts, enclosures
- Prototyping parts

**CNC** - Best for:
- Flat plates, structural frames
- High-precision parts
- Load-bearing components
- Metal parts
- Parts requiring tight tolerances
- Gears, shafts (if simple geometry)

**User action:**
- **Approve** → Move to Stage 3 (3D Generation)
- **Refine** → Request changes to part breakdown (coming soon)

**Example output for "model rocket":**

| # | Part Name | Method | Material | Dimensions | Qty |
|---|-----------|--------|----------|------------|-----|
| 1 | Nose Cone | 3D Print | PLA | 120×50×50mm | 1 |
| 2 | Body Tube Section 1 | 3D Print | PLA | 200×50×50mm | 1 |
| 3 | Body Tube Section 2 | 3D Print | PLA | 200×50×50mm | 1 |
| 4 | Body Tube Section 3 | 3D Print | PLA | 200×50×50mm | 1 |
| 5 | Body Tube Section 4 | 3D Print | PLA | 200×50×50mm | 1 |
| 6 | Fin (Main) | CNC | Plywood | 150×100×3mm | 4 |
| 7 | Motor Mount Tube | 3D Print | ABS | 100×30×30mm | 1 |
| 8 | Centering Ring (Forward) | CNC | Plywood | 60×60×3mm | 1 |
| 9 | Centering Ring (Middle) | CNC | Plywood | 60×60×3mm | 2 |
| 10 | Centering Ring (Aft) | CNC | Plywood | 60×60×3mm | 1 |
| ... | ... | ... | ... | ... | ... |
| 45 | Launch Lug | 3D Print | PLA | 50×10×10mm | 3 |

**Summary:**
- Total Parts: 45
- 3D Print: 28 parts
- CNC: 17 parts

---

### Stage 3: 3D Model Generation

**What happens:**
1. System generates 3D models for **ALL approved parts** automatically
2. Uses **Meshy-6** (latest model) for best quality
3. Each part goes through the complete workflow:
   - **Preview generation** (5-10 min) - Creates base geometry
   - **Automatic refine** (10-15 min) - Adds textures and details
   - **Automatic download** - Saves GLB file locally

**User action:**
- Monitor progress in History page
- Download completed models
- View in 3D viewer

**Technical details:**
- AI model: Meshy-6 (via `ai_model='latest'`)
- Quality: High (60,000 polygons)
- Cost: ~100 credits per part (20 for preview + 80 for refine)
- Time: ~15-20 minutes per part
- Output: Textured GLB files with PBR materials

---

## How to Use

### 1. Access Design Projects

Click **🚀 Design Projects** in the navigation menu

### 2. Start New Project

```
What do you want to design?
┌─────────────────────────────────────────────┐
│ A model rocket with parachute recovery     │
│ system                                      │
└─────────────────────────────────────────────┘
         [🚀 Start Design Project]
```

### 3. Review Design Concept

The AI will generate a detailed concept. Review it and click:
- **✓ Approve & Continue to Part Breakdown** → Proceed to Stage 2
- **↻ Refine Concept** → Request changes (coming soon)

### 4. Review Part Breakdown

The AI will show a complete parts list with manufacturing recommendations. Review and click:
- **✓ Approve & Start 3D Generation** → Proceed to Stage 3
- **↻ Refine Part Breakdown** → Request changes (coming soon)

### 5. Monitor Generation

All parts will start generating automatically. Check progress in:
- **History** page → See all models
- **Design Project Detail** page → See project-specific models

### 6. Download & Use

When generation completes:
- Download GLB files
- View in 3D viewer
- Send to 3D printers or CNC machines

---

## Examples

### Example 1: Model Rocket

**Input:** "A model rocket with parachute recovery system"

**Stage 1 Output:**
- Design Type: Vehicle
- Complexity: Medium
- Parts: 45

**Stage 2 Output:**
- Nose cone (3D Print)
- Body tubes ×4 (3D Print)
- Fins ×4 (CNC)
- Motor mount (3D Print)
- Centering rings ×6 (CNC)
- Parachute compartment (3D Print)
- Electronics bay (3D Print)
- Launch lugs ×3 (3D Print)
- Bulkheads ×4 (CNC)
- ... and 27 more parts

**Stage 3 Output:**
- 45 textured GLB files ready for manufacturing

---

### Example 2: Quadcopter Drone

**Input:** "A quadcopter drone frame for FPV racing"

**Stage 1 Output:**
- Design Type: Vehicle
- Complexity: High
- Parts: 68

**Stage 2 Output:**
- Center plate (CNC - carbon fiber)
- Motor arms ×4 (CNC - carbon fiber)
- Motor mounts ×4 (3D Print)
- Landing gear legs ×4 (3D Print)
- Camera gimbal base (3D Print)
- Camera gimbal arms ×2 (3D Print)
- Battery tray (CNC - aluminum)
- Electronics enclosure (3D Print)
- Antenna mounts ×2 (3D Print)
- Prop guards ×4 (3D Print)
- ... and 48 more parts

**Stage 3 Output:**
- 68 textured GLB files ready for manufacturing

---

### Example 3: Robot Arm

**Input:** "A 6-axis robot arm for desktop use"

**Stage 1 Output:**
- Design Type: Robot
- Complexity: High
- Parts: 92

**Stage 2 Output:**
- Base plate (CNC - aluminum)
- Shoulder joint housing (3D Print)
- Upper arm segment (3D Print)
- Elbow joint housing (3D Print)
- Forearm segment (3D Print)
- Wrist joint housing (3D Print)
- Gripper base (3D Print)
- Gripper fingers ×2 (3D Print)
- Servo mounts ×6 (3D Print)
- Cable routing clips ×10 (3D Print)
- Bearing housings ×6 (CNC - aluminum)
- ... and 62 more parts

**Stage 3 Output:**
- 92 textured GLB files ready for manufacturing

---

## Technical Architecture

### MongoDB Collections

**design_projects**
```javascript
{
  _id: ObjectId,
  user_id: "string",
  original_prompt: "model rocket",
  stage: "concept" | "parts" | "generation" | "completed",
  status: "pending" | "approved" | "generating" | "completed",
  concept_description: "...",
  concept_approved_at: datetime,
  parts_approved_at: datetime,
  total_parts: 45,
  generated_parts: 0,
  failed_parts: 0,
  created_at: datetime,
  updated_at: datetime
}
```

**design_concepts**
```javascript
{
  _id: ObjectId,
  project_id: ObjectId,
  original_prompt: "model rocket",
  refined_description: "...",
  design_type: "vehicle",
  key_features: ["...", "..."],
  estimated_complexity: "medium",
  estimated_parts_count: 45,
  status: "pending" | "approved",
  created_at: datetime,
  approved_at: datetime
}
```

**part_breakdowns**
```javascript
{
  _id: ObjectId,
  project_id: ObjectId,
  parts: [
    {
      part_number: 1,
      name: "Nose Cone",
      description: "...",
      manufacturing_method: "3d_print",
      material_recommendation: "PLA",
      estimated_dimensions: {x: 120, y: 50, z: 50},
      complexity: "medium",
      quantity: 1,
      notes: "...",
      refined_prompt: "...",
      model_id: ObjectId | null,
      status: "pending" | "generating" | "completed" | "failed"
    },
    ...
  ],
  total_parts: 45,
  parts_by_method: {
    "3d_print": 28,
    "cnc": 17
  },
  status: "pending" | "approved",
  created_at: datetime,
  approved_at: datetime
}
```

### API Endpoints

**POST /api/design/create-project/**
- Creates new design project
- Generates Stage 1 concept
- Returns: Concept card HTML (HTMX)

**POST /api/design/approve-concept/<project_id>/**
- Approves concept
- Generates Stage 2 part breakdown
- Returns: Parts table HTML (HTMX)

**POST /api/design/approve-parts/<project_id>/**
- Approves parts
- Starts Stage 3 generation for all parts
- Returns: Generation started confirmation HTML (HTMX)

### AI Services

**services/enhanced_design_analyzer.py**

```python
# Stage 1: Generate concept
generate_design_concept(original_prompt) → {
  refined_description: str,
  design_type: str,
  key_features: list,
  estimated_complexity: str,
  estimated_parts_count: int
}

# Stage 2: Break down into parts
break_down_into_parts(design_concept, original_prompt) → [
  {
    part_number: int,
    name: str,
    description: str,
    manufacturing_method: str,
    material_recommendation: str,
    estimated_dimensions: dict,
    complexity: str,
    quantity: int,
    notes: str
  },
  ...
]

# Stage 3: Generate prompts for 3D generation
generate_part_prompts(parts_list, design_concept) → parts_list_with_prompts
```

---

## Cost Estimation

### Per Project

**AI Analysis (Stages 1 & 2):**
- Concept generation: ~$0.01
- Part breakdown: ~$0.02
- Prompt generation: ~$0.01 per part
- **Total AI cost:** ~$0.04 + ($0.01 × parts)

**3D Generation (Stage 3):**
- Meshy-6 preview: 20 credits per part
- Meshy-6 refine: 80 credits per part
- **Total Meshy cost:** 100 credits per part

**Example: 45-part rocket**
- AI: $0.04 + ($0.01 × 45) = $0.49
- Meshy: 100 × 45 = 4,500 credits (~$45)
- **Total: ~$45.50**

---

## Limitations & Future Enhancements

### Current Limitations

1. **No iterative refinement** - "Refine" buttons are placeholders
2. **No assembly instructions** - Parts list only, no assembly guide
3. **No BOM export** - Can't export bill of materials
4. **No cost estimation** - No per-part cost calculation
5. **No print time estimation** - No time estimates for manufacturing

### Planned Enhancements

- [ ] **Iterative refinement** - Allow users to request changes to concept/parts
- [ ] **Assembly instructions** - AI-generated step-by-step assembly guide
- [ ] **BOM export** - Export parts list as CSV/PDF
- [ ] **Cost estimation** - Calculate material costs per part
- [ ] **Print time estimation** - Estimate manufacturing time
- [ ] **Part dependencies** - Show which parts must be printed first
- [ ] **Assembly visualization** - 3D exploded view of assembly
- [ ] **Quality presets** - Low/Medium/High quality options per part
- [ ] **Batch generation** - Generate all parts in parallel
- [ ] **Progress tracking** - Real-time generation progress
- [ ] **Email notifications** - Notify when all parts complete

---

## Troubleshooting

### Issue: Concept generation fails

**Cause:** OpenAI API error or invalid prompt

**Solution:**
1. Check OpenAI API key in environment
2. Ensure prompt is descriptive (min 10 characters)
3. Check logs for error details

### Issue: Part breakdown has too few parts

**Cause:** AI underestimated complexity

**Solution:**
1. Use "Refine Part Breakdown" button (coming soon)
2. Or manually request more detailed breakdown in prompt
3. Example: "A model rocket with ALL components including fasteners"

### Issue: Part breakdown has wrong manufacturing methods

**Cause:** AI misunderstood part requirements

**Solution:**
1. Use "Refine Part Breakdown" button (coming soon)
2. Or provide more specific requirements in prompt
3. Example: "A robot arm with CNC aluminum structural parts"

### Issue: 3D generation fails for some parts

**Cause:** Meshy API error or invalid prompt

**Solution:**
1. Check Meshy API credits
2. Check background job is running
3. Review failed part prompts in MongoDB
4. Regenerate failed parts manually

---

## Support

For issues or questions:
1. Check logs: `tail -f /var/log/nexaai/django.log`
2. Check MongoDB: `db.design_projects.find().pretty()`
3. Submit feedback: https://help.manus.im

---

## Changelog

### Version 1.0 (Current)
- ✅ 3-stage workflow implementation
- ✅ AI-powered concept generation
- ✅ Intelligent part breakdown (up to 200+ parts)
- ✅ Manufacturing method recommendations
- ✅ Meshy-6 integration
- ✅ Automatic preview → refine → download
- ✅ HTMX-powered interactive UI
- ✅ Complete MongoDB schema
- ⏳ Iterative refinement (planned)
- ⏳ Assembly instructions (planned)
- ⏳ BOM export (planned)
