#!/usr/bin/env python3
"""
Skill Initializer - Creates a new skill from template

Usage:
    init_skill.py <skill-name> --path <path> [--unity]

Examples:
    init_skill.py my-new-skill --path skills/public
    init_skill.py my-api-helper --path skills/private
    init_skill.py my-unity-ops --path skills --unity

Options:
    --unity    Create Unity skill structure (SkillsPlugin/Editor/, templates/)
"""

import sys
from pathlib import Path


SKILL_TEMPLATE = """---
name: {skill_name}
description: [TODO: Complete and informative explanation of what the skill does and when to use it. Include WHEN to use this skill - specific scenarios, file types, or tasks that trigger it.]
---

# {skill_title}

## Overview

[TODO: 1-2 sentences explaining what this skill enables]

## Structuring This Skill

[TODO: Choose the structure that best fits this skill's purpose. Common patterns:

**1. Workflow-Based** (best for sequential processes)
- Works well when there are clear step-by-step procedures
- Example: DOCX skill with "Workflow Decision Tree" → "Reading" → "Creating" → "Editing"
- Structure: ## Overview → ## Workflow Decision Tree → ## Step 1 → ## Step 2...

**2. Task-Based** (best for tool collections)
- Works well when the skill offers different operations/capabilities
- Example: PDF skill with "Quick Start" → "Merge PDFs" → "Split PDFs" → "Extract Text"
- Structure: ## Overview → ## Quick Start → ## Task Category 1 → ## Task Category 2...

**3. Reference/Guidelines** (best for standards or specifications)
- Works well for brand guidelines, coding standards, or requirements
- Example: Brand styling with "Brand Guidelines" → "Colors" → "Typography" → "Features"
- Structure: ## Overview → ## Guidelines → ## Specifications → ## Usage...

**4. Capabilities-Based** (best for integrated systems)
- Works well when the skill provides multiple interrelated features
- Example: Product Management with "Core Capabilities" → numbered capability list
- Structure: ## Overview → ## Core Capabilities → ### 1. Feature → ### 2. Feature...

Patterns can be mixed and matched as needed. Most skills combine patterns (e.g., start with task-based, add workflow for complex operations).

Delete this entire "Structuring This Skill" section when done - it's just guidance.]

## [TODO: Replace with the first main section based on chosen structure]

[TODO: Add content here. See examples in existing skills:
- Code samples for technical skills
- Decision trees for complex workflows
- Concrete examples with realistic user requests
- References to scripts/templates/references as needed]

## Resources

This skill includes example resource directories that demonstrate how to organize different types of bundled resources:

### scripts/
Executable code (Python/Bash/etc.) that can be run directly to perform specific operations.

**Examples from other skills:**
- PDF skill: `fill_fillable_fields.py`, `extract_form_field_info.py` - utilities for PDF manipulation
- DOCX skill: `document.py`, `utilities.py` - Python modules for document processing

**Appropriate for:** Python scripts, shell scripts, or any executable code that performs automation, data processing, or specific operations.

**Note:** Scripts may be executed without loading into context, but can still be read by Claude for patching or environment adjustments.

### references/
Documentation and reference material intended to be loaded into context to inform Claude's process and thinking.

**Examples from other skills:**
- Product management: `communication.md`, `context_building.md` - detailed workflow guides
- BigQuery: API reference documentation and query examples
- Finance: Schema documentation, company policies

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Claude should reference while working.

### assets/
Files not intended to be loaded into context, but rather used within the output Claude produces.

**Examples from other skills:**
- Brand styling: PowerPoint template files (.pptx), logo files
- Frontend builder: HTML/React boilerplate project directories
- Typography: Font files (.ttf, .woff2)

**Appropriate for:** Templates, boilerplate code, document templates, images, icons, fonts, or any files meant to be copied or used in the final output.

---

**Any unneeded directories can be deleted.** Not every skill requires all three types of resources.
"""

EXAMPLE_SCRIPT = '''#!/usr/bin/env python3
"""
Example helper script for {skill_name}

This is a placeholder script that can be executed directly.
Replace with actual implementation or delete if not needed.

Example real scripts from other skills:
- pdf/scripts/fill_fillable_fields.py - Fills PDF form fields
- pdf/scripts/convert_pdf_to_images.py - Converts PDF pages to images
"""

def main():
    print("This is an example script for {skill_name}")
    # TODO: Add actual script logic here
    # This could be data processing, file conversion, API calls, etc.

if __name__ == "__main__":
    main()
'''

EXAMPLE_REFERENCE = """# Reference Documentation for {skill_title}

This is a placeholder for detailed reference documentation.
Replace with actual reference content or delete if not needed.

Example real reference docs from other skills:
- product-management/references/communication.md - Comprehensive guide for status updates
- product-management/references/context_building.md - Deep-dive on gathering context
- bigquery/references/ - API references and query examples

## When Reference Docs Are Useful

Reference docs are ideal for:
- Comprehensive API documentation
- Detailed workflow guides
- Complex multi-step processes
- Information too lengthy for main SKILL.md
- Content that's only needed for specific use cases

## Structure Suggestions

### API Reference Example
- Overview
- Authentication
- Endpoints with examples
- Error codes
- Rate limits

### Workflow Guide Example
- Prerequisites
- Step-by-step instructions
- Common patterns
- Troubleshooting
- Best practices
"""

EXAMPLE_ASSET = """# Example Asset File

This placeholder represents where asset files would be stored.
Replace with actual asset files (templates, images, fonts, etc.) or delete if not needed.

Asset files are NOT intended to be loaded into context, but rather used within
the output Claude produces.

Example asset files from other skills:
- Brand guidelines: logo.png, slides_template.pptx
- Frontend builder: hello-world/ directory with HTML/React boilerplate
- Typography: custom-font.ttf, font-family.woff2
- Data: sample_data.csv, test_dataset.json

## Common Asset Types

- Templates: .pptx, .docx, boilerplate directories
- Images: .png, .jpg, .svg, .gif
- Fonts: .ttf, .otf, .woff, .woff2
- Boilerplate code: Project directories, starter files
- Icons: .ico, .svg
- Data files: .csv, .json, .xml, .yaml

Note: This is a text placeholder. Actual assets can be any file type.
"""

# Unity-specific templates
UNITY_SKILL_TEMPLATE = """---
name: {skill_name}
description: [TODO: Complete and informative explanation of what the skill does and when to use it. Include WHEN to use this skill - specific scenarios, Unity operations, or tasks that trigger it.]
---

# {skill_title}

## Overview

[TODO: 1-2 sentences explaining what this Unity skill enables]

## Requirements

- Unity Editor with Command Server window open
- WebSocket connection to ws://127.0.0.1:8766

## Quick Start

### 1. Open Unity Command Server
In Unity Editor: `Tools > ClaudeAgent > Unity Command Server`

### 2. Send Command
```bash
python send_message.py '{{"operation":"your_operation","params":{{}}}}'
```

## Supported Operations

[TODO: List your skill's operations here]

| Operation | Description |
|-----------|-------------|
| `operation_name` | Description of what it does |

## Resources

### SkillsPlugin/
Contains C# scripts that run in Unity Editor. This folder is symlinked into Unity projects.

- `Editor/` subfolder contains Editor-only scripts
- `.gitignore` excludes *.meta files (Unity generates these locally)

### templates/
Sample scripts that users can copy into their projects.

### references/
Documentation for operations and workflows.

---

**See references/unity-skills.md in skill-creator for Unity skill conventions.**
"""

UNITY_SEND_MESSAGE = '''#!/usr/bin/env python3
"""
WebSocket client for sending commands to Unity Command Server.

Usage:
    python send_message.py '<json_command>'

Example:
    python send_message.py '{{"operation":"get_scene_hierarchy","params":{{}}}}'
"""

import sys
import json
import asyncio

try:
    import websockets
except ImportError:
    print("Error: websockets library not installed")
    print("Install with: pip install websockets")
    sys.exit(1)


async def send_command(command_json: str):
    uri = "ws://127.0.0.1:8766"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {{uri}}")
            print(f"Sending: {{command_json}}")
            await websocket.send(command_json)
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            result = json.loads(response)
            if result.get("success"):
                print(f"Success: {{result.get('result', 'OK')}}")
            else:
                print(f"Error: {{result.get('error', 'Unknown error')}}")
            return result
    except asyncio.TimeoutError:
        print("Error: Command timed out (10s)")
        sys.exit(1)
    except ConnectionRefusedError:
        print("Error: Cannot connect to Unity Command Server")
        print("Make sure Unity is running and Command Server is open")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python send_message.py '<json_command>'")
        sys.exit(1)

    command = sys.argv[1]
    asyncio.run(send_command(command))


if __name__ == "__main__":
    main()
'''

UNITY_GITIGNORE = """# Unity generates .meta files locally
# Each Unity project/version may create slightly different .meta files
*.meta
"""

UNITY_EXAMPLE_EDITOR_SCRIPT = """// Example Unity Editor script for {skill_name}
// Place your CommandExecutor or Editor scripts here

using UnityEngine;
using UnityEditor;

public class Example{class_name}Editor : EditorWindow
{{
    [MenuItem("Tools/{skill_title}/Example Window")]
    public static void ShowWindow()
    {{
        GetWindow<Example{class_name}Editor>("{skill_title}");
    }}

    void OnGUI()
    {{
        GUILayout.Label("Example Editor Window", EditorStyles.boldLabel);
        // TODO: Add your Editor UI here
    }}
}}
"""

UNITY_EXAMPLE_TEMPLATE = """// Example template script for {skill_name}
// Users can copy this to their project and modify as needed

using UnityEngine;

public class Example{class_name}Behavior : MonoBehaviour
{{
    void Start()
    {{
        Debug.Log("{skill_title} template script started");
    }}

    void Update()
    {{
        // TODO: Add behavior logic here
    }}
}}
"""


def title_case_skill_name(skill_name):
    """Convert hyphenated skill name to Title Case for display."""
    return ' '.join(word.capitalize() for word in skill_name.split('-'))


def to_class_name(skill_name):
    """Convert hyphenated skill name to PascalCase for C# class names."""
    return ''.join(word.capitalize() for word in skill_name.split('-'))


def init_unity_skill(skill_name, path):
    """
    Initialize a new Unity skill directory with SkillsPlugin structure.

    Args:
        skill_name: Name of the skill
        path: Path where the skill directory should be created

    Returns:
        Path to created skill directory, or None if error
    """
    # Determine skill directory path
    skill_dir = Path(path).resolve() / skill_name

    # Check if directory already exists
    if skill_dir.exists():
        print(f"Error: Skill directory already exists: {skill_dir}")
        return None

    # Create skill directory
    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        print(f"Created skill directory: {skill_dir}")
    except Exception as e:
        print(f"Error creating directory: {e}")
        return None

    # Create SKILL.md from Unity template
    skill_title = title_case_skill_name(skill_name)
    class_name = to_class_name(skill_name)
    skill_content = UNITY_SKILL_TEMPLATE.format(
        skill_name=skill_name,
        skill_title=skill_title
    )

    skill_md_path = skill_dir / 'SKILL.md'
    try:
        skill_md_path.write_text(skill_content)
        print("Created SKILL.md")
    except Exception as e:
        print(f"Error creating SKILL.md: {e}")
        return None

    # Create send_message.py
    try:
        send_message_path = skill_dir / 'send_message.py'
        send_message_path.write_text(UNITY_SEND_MESSAGE)
        print("Created send_message.py")
    except Exception as e:
        print(f"Error creating send_message.py: {e}")
        return None

    # Create Unity-specific directories
    try:
        # Create SkillsPlugin/Editor/ directory
        editor_dir = skill_dir / 'SkillsPlugin' / 'Editor'
        editor_dir.mkdir(parents=True, exist_ok=True)
        print("Created SkillsPlugin/Editor/")

        # Create .gitignore in SkillsPlugin
        gitignore_path = skill_dir / 'SkillsPlugin' / '.gitignore'
        gitignore_path.write_text(UNITY_GITIGNORE)
        print("Created SkillsPlugin/.gitignore")

        # Create example Editor script
        example_editor = editor_dir / f'Example{class_name}Editor.cs'
        example_editor.write_text(UNITY_EXAMPLE_EDITOR_SCRIPT.format(
            skill_name=skill_name,
            skill_title=skill_title,
            class_name=class_name
        ))
        print(f"Created SkillsPlugin/Editor/Example{class_name}Editor.cs")

        # Create templates/ directory
        templates_dir = skill_dir / 'templates'
        templates_dir.mkdir(exist_ok=True)
        example_template = templates_dir / f'Example{class_name}Behavior.cs'
        example_template.write_text(UNITY_EXAMPLE_TEMPLATE.format(
            skill_name=skill_name,
            skill_title=skill_title,
            class_name=class_name
        ))
        print(f"Created templates/Example{class_name}Behavior.cs")

        # Create references/ directory
        references_dir = skill_dir / 'references'
        references_dir.mkdir(exist_ok=True)
        example_reference = references_dir / 'operations.md'
        example_reference.write_text(f"""# {skill_title} Operations

## Operation Reference

[TODO: Document your operations here]

### operation_name

**Description:** What this operation does

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| param1 | string | Yes | Description |

**Example:**
```json
{{"operation": "operation_name", "params": {{"param1": "value"}}}}
```
""")
        print("Created references/operations.md")

    except Exception as e:
        print(f"Error creating Unity directories: {e}")
        return None

    # Print next steps
    print(f"\nUnity skill '{skill_name}' initialized successfully at {skill_dir}")
    print("\nNext steps:")
    print("1. Edit SKILL.md to complete the TODO items and update the description")
    print("2. Add your C# Editor scripts to SkillsPlugin/Editor/")
    print("3. Add sample scripts to templates/ for users to copy")
    print("4. Document operations in references/operations.md")
    print("\nTo use in Unity project:")
    print(f"  mklink /D Assets\\ClaudePlugin {skill_dir}\\SkillsPlugin")

    return skill_dir


def init_skill(skill_name, path):
    """
    Initialize a new skill directory with template SKILL.md.

    Args:
        skill_name: Name of the skill
        path: Path where the skill directory should be created

    Returns:
        Path to created skill directory, or None if error
    """
    # Determine skill directory path
    skill_dir = Path(path).resolve() / skill_name

    # Check if directory already exists
    if skill_dir.exists():
        print(f"❌ Error: Skill directory already exists: {skill_dir}")
        return None

    # Create skill directory
    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        print(f"✅ Created skill directory: {skill_dir}")
    except Exception as e:
        print(f"❌ Error creating directory: {e}")
        return None

    # Create SKILL.md from template
    skill_title = title_case_skill_name(skill_name)
    skill_content = SKILL_TEMPLATE.format(
        skill_name=skill_name,
        skill_title=skill_title
    )

    skill_md_path = skill_dir / 'SKILL.md'
    try:
        skill_md_path.write_text(skill_content)
        print("✅ Created SKILL.md")
    except Exception as e:
        print(f"❌ Error creating SKILL.md: {e}")
        return None

    # Create resource directories with example files
    try:
        # Create scripts/ directory with example script
        scripts_dir = skill_dir / 'scripts'
        scripts_dir.mkdir(exist_ok=True)
        example_script = scripts_dir / 'example.py'
        example_script.write_text(EXAMPLE_SCRIPT.format(skill_name=skill_name))
        example_script.chmod(0o755)
        print("✅ Created scripts/example.py")

        # Create references/ directory with example reference doc
        references_dir = skill_dir / 'references'
        references_dir.mkdir(exist_ok=True)
        example_reference = references_dir / 'api_reference.md'
        example_reference.write_text(EXAMPLE_REFERENCE.format(skill_title=skill_title))
        print("✅ Created references/api_reference.md")

        # Create assets/ directory with example asset placeholder
        assets_dir = skill_dir / 'assets'
        assets_dir.mkdir(exist_ok=True)
        example_asset = assets_dir / 'example_asset.txt'
        example_asset.write_text(EXAMPLE_ASSET)
        print("✅ Created assets/example_asset.txt")
    except Exception as e:
        print(f"❌ Error creating resource directories: {e}")
        return None

    # Print next steps
    print(f"\n✅ Skill '{skill_name}' initialized successfully at {skill_dir}")
    print("\nNext steps:")
    print("1. Edit SKILL.md to complete the TODO items and update the description")
    print("2. Customize or delete the example files in scripts/, references/, and assets/")
    print("3. Run the validator when ready to check the skill structure")

    return skill_dir


def main():
    # Parse arguments
    args = sys.argv[1:]
    unity_mode = '--unity' in args
    if unity_mode:
        args.remove('--unity')

    # Check for required arguments
    if len(args) < 3 or args[1] != '--path':
        print("Usage: init_skill.py <skill-name> --path <path> [--unity]")
        print("\nSkill name requirements:")
        print("  - Hyphen-case identifier (e.g., 'data-analyzer')")
        print("  - Lowercase letters, digits, and hyphens only")
        print("  - Max 40 characters")
        print("  - Must match directory name exactly")
        print("\nOptions:")
        print("  --unity    Create Unity skill structure (SkillsPlugin/Editor/, templates/)")
        print("\nExamples:")
        print("  init_skill.py my-new-skill --path skills/public")
        print("  init_skill.py my-api-helper --path skills/private")
        print("  init_skill.py my-unity-ops --path skills --unity")
        sys.exit(1)

    skill_name = args[0]
    path = args[2]

    if unity_mode:
        print(f"Initializing Unity skill: {skill_name}")
    else:
        print(f"Initializing skill: {skill_name}")
    print(f"   Location: {path}")
    print()

    if unity_mode:
        result = init_unity_skill(skill_name, path)
    else:
        result = init_skill(skill_name, path)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
