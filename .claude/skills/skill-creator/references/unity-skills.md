# Unity Skills Convention

This document defines the folder structure and setup for skills that integrate with Unity Editor.

## Folder Structure

Unity skills that require C# code in Unity Editor:

```
skill-name/
├── SKILL.md
├── send_message.py          # WebSocket client (if needed)
├── SkillsPlugin/            # Essential C# files (symlinked to Unity)
│   ├── .gitignore           # Contains: *.meta
│   └── Editor/              # Unity Editor scripts
│       └── *.cs
├── templates/               # Sample scripts (copied, not symlinked)
│   └── *.cs
└── references/
    └── *.md
```

## File Types

### SkillsPlugin/ (Essential - Symlinked)

Files REQUIRED for the skill to function in Unity.

- Symlinked into Unity project's Assets folder
- Must contain `Editor/` subfolder for Editor-only scripts
- Include `.gitignore` with `*.meta` (Unity generates .meta files locally)
- Examples: CommandExecutor.cs, UnityCommandServer.cs

### templates/ (Samples - Copied)

Reusable sample/template scripts for users to copy and modify.

- COPIED into projects, not symlinked
- No .meta files needed (generated when copied to project)
- Examples: FollowCamera.cs, AutoRunner.cs

### Generated (NEVER in skill folder)

Output created during skill usage belongs to the PROJECT, not the skill.

- Location: Unity project's `Assets/Generated/`
- Examples: Runtime-created scripts, terrain data, prefabs

## .meta Files

Unity uses .meta files for asset GUIDs. For skills used across multiple Unity versions:

- Add `.gitignore` with `*.meta` in SkillsPlugin folder
- Each Unity project generates its own .meta files locally
- Scripts work across Unity versions - only .meta formatting differs

## Unity Project Setup

When using Unity skills, create ONE symlink from Unity project to the skill folder:

```cmd
# Windows (run as Administrator)
cd YourUnityProject\Assets

# Single symlink - that's it!
mklink /D ClaudePlugin D:\Claude\SKILLS\unity-editor-operations\SkillsPlugin
```

### Resulting Unity Project Structure

```
YourUnityProject/
├── Assets/
│   ├── ClaudePlugin/         → symlink to unity-editor-operations/SkillsPlugin
│   │   └── Editor/           ← Unity recognizes as Editor scripts
│   │       ├── CommandExecutor.cs
│   │       └── ...
│   └── Generated/            # Project's own output (NOT symlinked)
│       ├── Scripts/
│       └── Terrains/
└── ...
```

### Why Only One Symlink?

- `unity-editor-operations` contains ALL the plugin code (including Runtime operations)
- `unity-runtime-operations` is documentation-only (explains how to use runtime features)
- Other skills are templates/docs only

## Partial Classes

If your skill uses C# partial classes (like CommandExecutor), keep ALL parts together in the same skill's SkillsPlugin folder. Splitting partial classes across skills will break compilation.

## Creating a New Unity Skill

Use the init_skill.py script with --unity flag:

```bash
python scripts/init_skill.py my-unity-skill --path D:\Claude\SKILLS --unity
```

This creates the appropriate folder structure for Unity integration.
