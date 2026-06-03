# 2026-06-03 Uma Moe to Uma Guide Agenda Converter Design

## Goal
Create a Python desktop utility tool that converts the JSON race plan exported by `uma.moe` into the JSON format expected by `uma.guide/agenda-planner`.

## Design Details

### Directory Structure
```
h:\Antigravity Repos\umamusume-sweepy-enhanced\uma_moe_converter\
├── races_database.json     # 350 races database extracted from uma.guide
├── converter_gui.py        # Tkinter GUI script
└── run.bat                 # Helper script to launch the GUI
```

### Data Mappings
The converter maps fields between formats:
- **Year Map:**
  - `"Junior Year"` / `"Junior"` -> `"First Year"`
  - `"Classic Year"` / `"Classic"` -> `"Second Year"`
  - `"Senior Year"` / `"Senior"` -> `"Third Year"`
- **Matching Rules:**
  - Races are matched against `races_database.json` by combining the normalized name and turn.
  - Normalized name is lowercase, alphanumeric only (whitespaces, dashes, quotes removed).
- **Races Database:**
  - Extracted from `uma.guide/agenda-planner` assets. Contains full metadata such as `grade`, `type`, `location`, `length`, and `lengthM`.

### GUI Specifications (Tkinter)
- **Window Size:** 600x400 (centered).
- **Input File Picker:** File selection via `filedialog.askopenfilename`. Default folder is the user's `Downloads` folder.
- **Output Folder Picker:** Folder selection via `filedialog.askdirectory`.
- **Output Filename Entry:** Pre-filled automatically upon input selection with the name `converted-<original-filename>.json`.
- **Action button:** "Convert" trigger button.
- **Status log:** Scrolled text or label indicating details of matched races and warnings.
- **Pop-up dialog:** Summary popup showing total matched and unmatched races.
