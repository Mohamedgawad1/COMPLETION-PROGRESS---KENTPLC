# KENT PLC - Power BI Dashboard Guide
## PS5 Tanzania Pre-Commissioning | Oil & Gas World-Class Specs

---

## STEP 1: IMPORT DATA

Open Power BI Desktop → **Get Data → Text/CSV** → Import all 6 files:

| File | Table Name in Power BI | Rows |
|------|----------------------|------|
| `01_Milestones.csv` | Milestones | 9 |
| `02_Subsystems.csv` | Subsystems | 123 |
| `03_PunchList.csv` | PunchList | 2,908 |
| `04_PL_Cross.csv` | PL_Cross | 4 |
| `05_Tasks_by_Milestone.csv` | Tasks_by_Milestone | 9 |
| `06_Discipline_Summary.csv` | Discipline_Summary | 8 |

---

## STEP 2: DATA MODEL

In **Model View**, create relationships:

```
Milestones[Letter] ←→ Tasks_by_Milestone[Milestone Letter]
Milestones[Letter] ←→ Subsystems[Milestone Letter]
```

> Note: You may need to create a **Milestone Letter column** in Tasks_by_Milestone using DAX:
> ```
> Milestone Letter = RIGHT(Tasks_by_Milestone[Milestone], 1)
> ```

---

## STEP 3: DAX MEASURES

Create these measures in **Modeling → New Measure**:

### KPIs
```dax
Total Tasks = SUM(Milestones[Total Tasks])
```
```dax
Closed Tasks = SUM(Milestones[Closed Tasks])
```
```dax
Open Tasks = SUM(Milestones[Open Tasks])
```
```dax
Overall Completion % = DIVIDE([Closed Tasks], [Total Tasks], 0) * 100
```

### Punch List
```dax
Total PL = SUM(PunchList[PL ID])  -- or COUNTROWS(PunchList)
```
```dax
Originated PL = CALCULATE(COUNTROWS(PunchList), PunchList[Status] = "Originated")
```
```dax
Closed PL = CALCULATE(COUNTROWS(PunchList), PunchList[Status] = "Closed")
```
```dax
Completed PL = CALCULATE(COUNTROWS(PunchList), PunchList[Status] = "Completed")
```

### Tasks by Discipline
```dax
Elec Tasks = CALCULATE(SUM(Tasks_by_Milestone[Total]), LEFT(Tasks_by_Milestone[Milestone], 2) = "E")
```
```dax
Instr Tasks = CALCULATE(SUM(Tasks_by_Milestone[Total]), LEFT(Tasks_by_Milestone[Milestone], 2) = "I")
```

---

## STEP 4: REPORT PAGES

Create **5 pages** (tabs):

---

### PAGE 1: OVERVIEW (Executive Summary)

**Layout:** 2 rows

**Row 1 - KPI Cards (5 across):**
| Visual | Data | Style |
|--------|------|-------|
| Card | `Total Tasks` | Gold `#C8940A` |
| Card | `Closed Tasks` | Green `#1A8A4A` |
| Card | `Open Tasks` | Red `#C53030` |
| Card | `123 Subsystems` | Cyan `#0891B2` |
| Card | `Total PL` | Purple `#7C3AED` |

**Row 2 - Charts (3 across):**
| Visual | Data |
|--------|------|
| **Donut Chart** | Task Status: Closed vs Open (Green/Red) |
| **Donut Chart** | PL Status: Originated vs Closed vs Completed |
| **100% Stacked Bar** | Completion % by Milestone |

---

### PAGE 2: MILESTONES

**Layout:**

**Top:** **Stacked Bar Chart**
- Axis: `Milestones[Milestone]`
- Legend: Closed (Green) / Open (Red)
- Values: `Milestones[Closed Tasks]`, `Milestones[Open Tasks]`
- Sort by: Letter A→I

**Bottom:** **9x KPI Cards Grid (3x3)**
Each card for one milestone showing:
- Milestone Name
- Total / Closed / Open
- Completion % progress bar (use **Dynamic background** with measure)

---

### PAGE 3: SUBSYSTEMS

**Layout:**

**Left Panel (40%):** **Slicer**
- Field: `Subsystems[Milestone]`
- Style: Dropdown or List

**Right Panel (60%):** **Table Visual**
| Column | Field | Format |
|--------|-------|--------|
| # | Auto-number | - |
| System | `Subsystems[System]` | - |
| Subsystem | `Subsystems[Subsystem]` | - |
| Milestone | `Subsystems[Milestone]` | - |
| Total | `Subsystems[Total]` | Number |
| Closed | `Subsystems[Closed]` | Number |
| E-Open | `Subsystems[Elec Open]` | Number |
| I-Open | `Subsystems[Instr Open]` | Number |
| % | `Subsystems[Completion %]` | % (conditional: <20% Red, 20-50% Gold, >50% Green) |
| Punch A | `Subsystems[Punch A]` | Number |
| Punch B | `Subsystems[Punch B]` | Number |
| Punch C | `Subsystems[Punch C]` | Number |
| Progress | Data Bar (conditional) | Green bar |

**Bottom:** **Bar Chart**
- Axis: `Subsystems[System]`
- Values: `Subsystems[Total]`, `Subsystems[Closed]`

---

### PAGE 4: PUNCH LIST

**Layout:**

**Row 1 - KPI Cards (4 across):**
| Card | Data | Color |
|------|------|-------|
| Total Punch | `2,908` | Purple |
| Originated | `2,243` | Red |
| Closed | `633` | Green |
| Completed | `32` | Blue |

**Row 2 - Charts (2 across):**
| Visual | Data |
|--------|------|
| **Donut** | Punch by Category: A (Critical)=991 Red, B (Major)=1390 Gold, C (Minor)=523 Cyan |
| **Stacked Bar** | PL by Milestone: Originated/Closed/Completed |

**Row 3:**
| Visual | Data |
|--------|------|
| **Matrix** | Milestone × Category (A/B/C) cross table |
| **Treemap** | PL by Discipline |

---

### PAGE 5: ANALYTICS

**Layout (2x2 grid):**

| Visual | Data | Notes |
|--------|------|-------|
| **Radar Chart** | Milestones[Completion %] | Dark background `#1A1A2E`, Gold lines |
| **Stacked Column** | Tasks by Milestone (Closed/Started/Pending) | Grouped by milestone |
| **Donut Chart** | Discipline Split (E/I/B/H/M/P/S/T) | 8 slices |
| **Waterfall Chart** | Completion flow: Total → Closed → Open | Shows progress |

---

## STEP 5: THEME & COLORS

### Oil & Gas Professional Theme

Go to **View → Themes → Customize Current Theme**:

```json
{
  "name": "KENT Oil & Gas",
  "dataColors": [
    "#C8940A",
    "#1A8A4A",
    "#C53030",
    "#2563EB",
    "#7C3AED",
    "#0891B2",
    "#D97706",
    "#EC4899",
    "#6366F1"
  ],
  "background": "#F5F0E8",
  "foreground": "#2C2416",
  "tableAccent": "#C8940A",
  "visualStyles": {
    "*": {
      "*": {
        "title": [{
          "fontFamily": "Segoe UI Semibold",
          "fontSize": 12,
          "color": "#6B5E4D"
        }],
        "background": [{
          "color": "#FFFCF7"
        }],
        "border": [{
          "color": "#D9D0C1"
        }],
        "borderRadius": 8
      }
    }
  }
}
```

### Background Color Codes
| Element | Color | Hex |
|---------|-------|-----|
| Page Background | Beige | `#F5F0E8` |
| Card Background | Cream | `#FFFCF7` |
| Card Top Border | Gold | `#C8940A` |
| Primary Text | Dark Brown | `#2C2416` |
| Secondary Text | Medium Brown | `#6B5E4D` |
| Tertiary Text | Light Brown | `#9A8D7C` |
| Green (Good) | Oil Green | `#1A8A4A` |
| Red (Alert) | Alarm Red | `#C53030` |
| Gold (Active) | Process Gold | `#C8940A` |
| Blue (Info) | Steel Blue | `#2563EB` |
| Radar BG | Dark Navy | `#1A1A2E` |

---

## STEP 6: FORMATTING TIPS

### KPI Cards
- **Font:** Segoe UI Bold, 28pt for values
- **Top Border:** 3px solid Gold `#C8940A`
- **Background:** `#FFFCF7`
- **Border Radius:** 8px

### Charts
- **Grid Lines:** `#EDE7DB` (light beige)
- **Axis Labels:** `#6B5E4D`, 10pt
- **Data Labels:** Bold, inside bars
- **Legend:** Bottom, circle markers

### Tables
- **Header:** Gold background `#C8940A`, white text, 10pt uppercase
- **Row Hover:** Light gold `rgba(200,148,10,0.04)`
- **Alternating Rows:** Slightly different cream
- **Conditional Formatting:**
  - % column: Red <20%, Gold 20-50%, Green >50%
  - Data bars for Closed vs Open

### Radar Chart (Special)
- **Background:** `#1A1A2E` (dark navy)
- **Grid Lines:** `rgba(255,255,255,0.1)`
- **Point Labels:** `#D1D5DB`, Bold 12pt
- **Line Color:** `#F59E0B` (gold)
- **Point Color:** `#F59E0B`
- **Fill:** `rgba(200,148,10,0.25)`

---

## STEP 7: INTERACTIVITY

### Cross-filtering
- Enable **Edit Interactions** on every page
- Slicers filter ALL visuals on the page
- Charts cross-filter each other
- KPI cards are NOT filtered by other visuals (set interaction to None)

### Drill-through
- Right-click any bar in milestone charts → **Drill through → Subsystems**
- This shows filtered subsystem table for that milestone

### Bookmarks (Optional)
Create bookmarks for quick navigation:
- `Show All Milestones`
- `Show Only PS5` (filter Subsystems table)
- `Show Critical Punch Only` (filter PL to Category A)

---

## STEP 8: PUBLISH

1. **File → Publish** to Power BI Service
2. Create a **Workspace** called "KENT PLC Dashboard"
3. **Set Refresh Schedule:** Daily at 06:00
4. **Pin to Dashboard:** Pin each page as a tile
5. **Share** with team via workspace permissions

---

## REAL DATA SUMMARY

| Metric | Value |
|--------|-------|
| **Total Tasks (PS5)** | 23,254 |
| **Closed Tasks** | 6,649 |
| **Completion** | 28.6% |
| **Subsystems** | 123 |
| **Total Punch List** | 2,908 |
| **Originated PL** | 2,243 |
| **Closed PL** | 633 |
| **Milestones** | 9 (A through I) |
| **Disciplines** | 8 (B/E/H/I/M/P/S/T) |

### Milestone Breakdown
| Milestone | Subsystems | Total | Closed | Completion |
|-----------|-----------|-------|--------|------------|
| A | 2 | 2,497 | 1,855 | **74.29%** |
| B | 13 | 2,240 | 813 | **36.29%** |
| C | 8 | 1,999 | 637 | **31.87%** |
| D | 11 | 4,295 | 1,151 | **26.80%** |
| E | 17 | 2,074 | 404 | **19.48%** |
| F | 14 | 3,014 | 411 | **13.64%** |
| G | 15 | 1,378 | 387 | **28.08%** |
| H | 32 | 4,706 | 909 | **19.32%** |
| I | 11 | 1,051 | 82 | **7.80%** |

### Discipline Breakdown
| Discipline | Total | Closed | Completion |
|------------|-------|--------|------------|
| E - Electrical | 11,585 | 3,455 | **29.82%** |
| I - Instrumentation | 9,722 | 2,827 | **29.08%** |
| P - Piping | 4,051 | 2,172 | **53.62%** |
| T - Telecommunications | 5,221 | 1,160 | **22.22%** |
| M - Mechanical | 819 | 416 | **50.79%** |
| H - HVAC | 278 | 110 | **39.57%** |
| B - Building | 118 | 11 | **9.32%** |
| S - Structural | 232 | 15 | **6.47%** |

---

*Generated for KENT PLC | PS5 Tanzania | Pumping Station 5*
*Data Source: COMPLETION PROGRESS - KENTPLC.xlsx*
