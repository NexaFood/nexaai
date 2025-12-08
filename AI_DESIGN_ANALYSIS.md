# AI-Powered Design Analysis & Manufacturing Recommendations

## Overview

NexaAI now features intelligent design analysis that automatically refines prompts, splits designs into manufacturable parts, and recommends the best manufacturing method for each component.

## How It Works

### 1. Prompt Refinement

When you enter a simple prompt like **"a robot arm"**, the AI enhances it to:

```
Detailed robotic arm with articulated joints, servo motor mounts, 
precision ball bearings, cable routing channels, and modular end-effector 
mounting plate. Industrial-grade finish with mounting holes for base attachment.
```

### 2. Part Splitting Analysis

The AI analyzes the design and breaks it down into logical, manufacturable parts:

**Example: Robot Arm**
- **Base Platform** → CNC machining (high precision, load-bearing)
- **Arm Segments** → 3D printing (complex geometry, lightweight)
- **Joint Housings** → 3D printing (internal channels for wiring)
- **Gripper Assembly** → 3D printing with flexible material

### 3. Manufacturing Method Selection

For each part, the AI considers:

**3D Printing is recommended for:**
- Complex geometries and organic shapes
- Internal structures and channels
- Lightweight components
- Prototypes and custom parts
- Parts with intricate details

**CNC Machining is recommended for:**
- High precision requirements
- Flat surfaces and simple geometries
- Metal parts
- Structural and load-bearing components
- Parts requiring tight tolerances

### 4. Material & Dimension Suggestions

Each part includes:
- **Material recommendation** (PLA, ABS, aluminum, steel, etc.)
- **Estimated dimensions** for build volume planning
- **Complexity rating** (low/medium/high)
- **Manufacturing reasoning** explaining the choice

## Using the Feature

### Enable AI Analysis (Default)

On the Generate page, the **AI-Powered Design Analysis** checkbox is enabled by default:

```
✓ 🤖 AI-Powered Design Analysis (Recommended)
```

This will:
- ✨ Refine your prompt for optimal 3D generation
- 🔧 Split into manufacturable parts that fit your printers/CNC
- 🏭 Recommend manufacturing methods for each part
- 📐 Suggest materials and dimensions

### Quick Mode (Simple Refinement)

Uncheck the AI Analysis box for simple prompt refinement without part splitting:
- Faster generation (single API call)
- Single-part output
- Still gets prompt enhancement

## Viewing Results

### In History Page

Each generated part shows:
- **Part name badge** (e.g., "🔧 Base Platform")
- **Manufacturing method** (🖨️ 3D Print or ⚙️ CNC)
- **Material suggestion** (🧱 Aluminum)
- **Dimensions** (📏 150x150x20mm)

### In Model Details

Click on any model to see:
- Original user prompt
- Refined AI-generated prompt
- Part description and function
- Manufacturing reasoning
- Full design analysis

## Example Workflows

### Simple Object: Coffee Mug

**User Input:** `a coffee mug`

**AI Analysis:**
- **Single part**: Main Body
- **Method**: 3D Print
- **Material**: Food-safe PLA or ceramic-filled filament
- **Refined Prompt**: "Ergonomic coffee mug with smooth interior surface, comfortable handle with finger groove, 350ml capacity, and stable base. Modern minimalist design with slight taper."

### Complex Assembly: Drone Frame

**User Input:** `quadcopter drone frame`

**AI Analysis:**
- **Part 1**: Center Plate (CNC, carbon fiber, structural rigidity)
- **Part 2**: Motor Arms (CNC, aluminum, vibration resistance)
- **Part 3**: Landing Gear (3D Print, TPU, shock absorption)
- **Part 4**: Camera Mount (3D Print, PLA, adjustable angle)
- **Part 5**: Battery Tray (3D Print, ABS, heat resistance)

Each part gets:
- Optimized 3D generation prompt
- Specific manufacturing recommendation
- Material and dimension guidance

### Mechanical Assembly: Gearbox

**User Input:** `planetary gearbox`

**AI Analysis:**
- **Part 1**: Housing (CNC, aluminum, precision fit)
- **Part 2**: Sun Gear (CNC, steel, high strength)
- **Part 3**: Planet Gears (3D Print, nylon, complex teeth)
- **Part 4**: Ring Gear (CNC, steel, internal teeth)
- **Part 5**: Carrier Plate (CNC, aluminum, bearing mounts)

## Technical Details

### LLM Model

- **Model**: GPT-4.1-mini (fast and cost-effective)
- **Temperature**: 0.7 (balanced creativity and consistency)
- **Response Format**: Structured JSON

### Analysis Factors

The AI considers:
- **Geometry complexity**: Simple vs. complex shapes
- **Structural requirements**: Load-bearing vs. decorative
- **Precision needs**: Tight tolerances vs. general fit
- **Material properties**: Strength, flexibility, heat resistance
- **Manufacturing constraints**: Build volume, support structures
- **Assembly considerations**: How parts fit together

### Fallback Behavior

If the AI service fails:
- Falls back to simple prompt refinement
- Creates single-part design
- Defaults to 3D printing
- Generation continues without interruption

## Benefits

### For Designers
- 🎯 Better 3D models from improved prompts
- 🧩 Automatic part breakdown for complex designs
- 📋 Manufacturing guidance for each component
- 💡 Learn best practices through AI recommendations

### For Manufacturers
- 🏭 Clear manufacturing method for each part
- 📐 Dimension estimates for planning
- 🧱 Material recommendations
- ⚙️ Optimized for your equipment (3D printer vs CNC)

### For Production
- 🔧 Parts designed to fit your build volumes
- 📦 Assembly instructions included
- 🎨 Consistent quality through refined prompts
- ⚡ Faster iteration with intelligent splitting

## Future Enhancements

Planned features:
- [ ] Integration with printer/CNC capabilities
- [ ] Cost estimation per part
- [ ] Assembly instruction generation
- [ ] Support structure optimization
- [ ] Multi-material recommendations
- [ ] Strength analysis and FEA integration
- [ ] Automatic CAD file generation
- [ ] BOM (Bill of Materials) export

## API Reference

### DesignAnalyzer Class

```python
from services.design_analyzer import DesignAnalyzer

analyzer = DesignAnalyzer()

# Full analysis with part splitting
analysis = analyzer.analyze_and_refine("robot arm")

# Simple prompt refinement
refined = analyzer.refine_prompt_simple("coffee mug")
```

### Analysis Response Format

```json
{
  "original_prompt": "user's input",
  "analysis": "brief design analysis",
  "parts": [
    {
      "name": "Part Name",
      "description": "what this part does",
      "refined_prompt": "detailed 3D generation prompt",
      "manufacturing_method": "3d_print" | "cnc",
      "reasoning": "why this method",
      "material_suggestion": "PLA / Aluminum / etc",
      "estimated_dimensions": "100x50x20mm",
      "complexity": "low" | "medium" | "high"
    }
  ],
  "assembly_notes": "how parts fit together"
}
```

## Troubleshooting

### AI Analysis Not Working
- Check OpenAI API key in environment variables
- Verify internet connectivity
- Check logs for API errors
- Falls back to simple mode automatically

### Too Many Parts Generated
- Use simpler, more specific prompts
- Disable AI Analysis for single-part designs
- Manually specify "single piece" in prompt

### Wrong Manufacturing Method
- AI makes best guess based on description
- You can override in production planning
- Provide more details in prompt for better accuracy

## Support

For issues or questions:
- Check application logs: `tail -f logs/django.log`
- Review design analysis in model details
- Submit feedback at https://help.manus.im
