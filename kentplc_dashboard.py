#!/usr/bin/env python3
"""KENT PLC Completion Progress Dashboard - Beige Professional Theme"""

import pandas as pd
import json
import os

EXCEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'COMPLETION PROGRESS - KENTPLC.xlsx')
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'index.html')


def extract_data():
    xls = pd.ExcelFile(EXCEL_PATH)
    precom = pd.read_excel(xls, sheet_name='PRECOM STATUS', header=None)
    subsys_df = pd.read_excel(xls, sheet_name='SUBSYSTEMS PROGRESS', header=None)
    tasks = pd.read_excel(xls, sheet_name='EXPORTED TASKS', header=0)
    pl = pd.read_excel(xls, sheet_name='EXPORTED PL', header=0)

    milestones = []
    for i in range(7, 34):
        row = precom.iloc[i]
        name = str(row[1]) if pd.notna(row[1]) else ''
        if name.startswith('PS5 - Milestone'):
            open_val = int(row[5]) if pd.notna(row[5]) else (int(row[3]) - int(row[4]))
            ms = {
                'name': name,
                'letter': name.replace('PS5 - Milestone ', ''),
                'subsystems': int(row[2]) if pd.notna(row[2]) else 0,
                'totalTasks': int(row[3]) if pd.notna(row[3]) else 0,
                'closedTasks': int(row[4]) if pd.notna(row[4]) else 0,
                'openTasks': open_val,
                'completion': round(float(row[14]) * 100, 2) if pd.notna(row[14]) else 0,
                'disciplines': []
            }
            for j in range(i + 1, min(i + 3, 34)):
                drow = precom.iloc[j]
                dname = str(drow[1]) if pd.notna(drow[1]) else ''
                if dname.startswith('E -') or dname.startswith('I -'):
                    ms['disciplines'].append({
                        'name': dname,
                        'totalTasks': int(drow[3]) if pd.notna(drow[3]) else 0,
                        'closedTasks': int(drow[4]) if pd.notna(row[4]) else 0,
                        'openTasks': int(drow[5]) if pd.notna(drow[5]) else 0,
                    })
            milestones.append(ms)

    subsystems = []
    for i in range(5, 128):
        row = subsys_df.iloc[i]
        if pd.notna(row[0]) and str(row[0]).startswith('PS5'):
            total = int(row[4]) if pd.notna(row[4]) else 0
            closed = int(row[5]) if pd.notna(row[5]) else 0
            subsystems.append({
                'system': str(row[0]),
                'subsystem': str(row[1]),
                'mantrac': str(row[2]) if pd.notna(row[2]) else '',
                'milestone': str(row[3]) if pd.notna(row[3]) else '',
                'total': total, 'closed': closed,
                'elecOpen': int(row[6]) if pd.notna(row[6]) else 0,
                'instrOpen': int(row[7]) if pd.notna(row[7]) else 0,
                'pct': round(closed / total * 100, 1) if total > 0 else 0,
                'punchA': int(row[9]) if pd.notna(row[9]) else 0,
                'punchB': int(row[10]) if pd.notna(row[10]) else 0,
                'punchC': int(row[11]) if pd.notna(row[11]) else 0,
            })

    task_by_ms = tasks.groupby('Subsystem Priority').agg(
        total=('Task ID', 'count'),
        closed=('Task State', lambda x: (x == 'Closed').sum()),
        started=('Task State', lambda x: (x == 'Started (not Completed)').sum()),
        pending=('Task State', lambda x: (x == 'To be completed').sum())
    ).reset_index().to_dict('records')

    pl_by_ms = pl.groupby('Priority').agg(
        total=('Punchlist ID', 'count'),
        originated=('Status', lambda x: (x == 'Originated').sum()),
        closed=('Status', lambda x: (x == 'Closed').sum()),
        completed=('Status', lambda x: (x == 'Completed').sum())
    ).reset_index().to_dict('records')

    pl_by_cat_raw = pl['Punchlist Category (Name)'].value_counts().to_dict()
    ct = pd.crosstab(pl['Priority'], pl['Punchlist Category (Name)'])
    pl_cross = {}
    for ms_name in ct.index:
        letter = ms_name.replace('PS5 - Milestone ', '')
        pl_cross[letter] = {
            'A': int(ct.loc[ms_name, 'A']) if 'A' in ct.columns else 0,
            'B': int(ct.loc[ms_name, 'B']) if 'B' in ct.columns else 0,
            'C': int(ct.loc[ms_name, 'C']) if 'C' in ct.columns else 0,
        }

    sys_groups = {}
    for s in subsystems:
        sys = s['system']
        if sys not in sys_groups:
            sys_groups[sys] = {'total': 0, 'closed': 0, 'count': 0}
        sys_groups[sys]['total'] += s['total']
        sys_groups[sys]['closed'] += s['closed']
        sys_groups[sys]['count'] += 1
    sys_summary = [{'system': k, **v, 'pct': round(v['closed'] / v['total'] * 100, 1) if v['total'] > 0 else 0}
                   for k, v in sorted(sys_groups.items())]

    return {
        'totalTasks': 851, 'closedTasks': 3, 'openTasks': 848,
        'totalSubsystems': 123, 'completeSubsystems': 0,
        'milestones': milestones, 'subsystems': subsystems,
        'taskByMilestone': task_by_ms, 'plByMilestone': pl_by_ms,
        'plByCategory': {'A - Critical': pl_by_cat_raw.get('A', 0), 'B - Major': pl_by_cat_raw.get('B', 0), 'C - Minor': pl_by_cat_raw.get('C', 0)},
        'plCross': pl_cross,
        'totalPL': len(pl), 'closedPL': int((pl['Status'] == 'Closed').sum()),
        'completedPL': int((pl['Status'] == 'Completed').sum()),
        'originatedPL': int((pl['Status'] == 'Originated').sum()),
        'elecTasks': 538, 'elecClosed': 3, 'instrTasks': 313, 'instrClosed': 0,
        'sysSummary': sys_summary,
    }


HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KENT PLC - Completion Progress Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#f5f0e8;--bg2:#ede7db;--card:#fffcf7;--card2:#faf6ee;--card3:#f0ead9;
  --border:#d9d0c1;--border2:#c4b9a7;
  --text:#2c2416;--text2:#6b5e4d;--text3:#9a8d7c;
  --gold:#c8940a;--gold2:#a67808;--gold-bg:rgba(200,148,10,0.1);
  --green:#1a8a4a;--green2:#15803d;--green-bg:rgba(26,138,74,0.08);
  --red:#c53030;--red2:#b91c1c;--red-bg:rgba(197,48,48,0.08);
  --blue:#2563eb;--blue2:#1d4ed8;--blue-bg:rgba(37,99,235,0.08);
  --cyan:#0891b2;--purple:#7c3aed;
  --shadow:0 1px 4px rgba(44,36,22,0.06);
  --shadow-lg:0 8px 30px rgba(44,36,22,0.1);
}
body{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;-webkit-font-smoothing:antialiased}

.header{
  background:linear-gradient(135deg,#fffcf7 0%,#faf6ee 50%,#f5f0e8 100%);
  padding:0;border-bottom:3px solid var(--gold);position:sticky;top:0;z-index:100;
  box-shadow:0 2px 12px rgba(44,36,22,0.08);
}
.header-top{display:flex;align-items:center;justify-content:space-between;padding:20px 36px 10px}
.header h1{font-size:22px;font-weight:800;color:var(--text)}
.header h1 span{color:var(--gold)}
.header-badge{display:flex;gap:8px;align-items:center}
.header-badge .tag{background:var(--gold-bg);color:var(--gold);font-size:10px;font-weight:700;padding:4px 12px;border-radius:20px;border:1px solid rgba(200,148,10,0.25)}
.header-badge .live{background:var(--green-bg);color:var(--green);font-size:10px;font-weight:700;padding:4px 12px;border-radius:20px;border:1px solid rgba(26,138,74,0.25);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.5}}
.header .subtitle{color:var(--text2);font-size:13px;padding:0 36px 8px}
.header .meta{display:flex;gap:8px;padding:0 36px 14px;flex-wrap:wrap}
.header .meta span{font-size:10px;color:var(--text2);background:var(--card2);padding:4px 12px;border-radius:6px;border:1px solid var(--border);font-weight:600}
.header.searching-mode{border-bottom-color:var(--blue)}
.header.searching-mode .meta span{border-color:rgba(37,99,235,0.3);background:var(--blue-bg);color:var(--blue)}

.container{max-width:1600px;margin:0 auto;padding:24px 20px}

.tabs{display:flex;gap:4px;margin-bottom:24px;background:var(--card);padding:5px;border-radius:14px;border:1px solid var(--border);flex-wrap:wrap;box-shadow:var(--shadow)}
.tab{padding:10px 20px;border-radius:10px;cursor:pointer;font-size:12px;font-weight:700;color:var(--text3);transition:all .25s;border:none;background:none;text-transform:uppercase;letter-spacing:0.8px}
.tab:hover{background:var(--card2);color:var(--text2)}
.tab.active{background:var(--gold);color:#fff;box-shadow:0 2px 10px rgba(200,148,10,0.3)}

.panel{display:none;animation:panelIn .3s ease}
.panel.active{display:block}
@keyframes panelIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}

.grid{display:grid;gap:16px}
.g2{grid-template-columns:repeat(2,1fr)}
.g3{grid-template-columns:repeat(3,1fr)}
.g4{grid-template-columns:repeat(4,1fr)}
.g5{grid-template-columns:repeat(5,1fr)}
@media(max-width:1200px){.g4,.g5{grid-template-columns:repeat(2,1fr)}}
@media(max-width:768px){.g2,.g3,.g4,.g5{grid-template-columns:1fr}}

.card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:22px;transition:all .25s;box-shadow:var(--shadow)}
.card:hover{box-shadow:var(--shadow-lg);transform:translateY(-1px)}
.card h3{font-size:11px;color:var(--text3);margin-bottom:14px;font-weight:700;text-transform:uppercase;letter-spacing:1px}

.stat-card{position:relative;overflow:hidden}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.stat-card.gold::before{background:linear-gradient(90deg,#c8940a,#eab308)}
.stat-card.green::before{background:linear-gradient(90deg,#1a8a4a,#22c55e)}
.stat-card.red::before{background:linear-gradient(90deg,#c53030,#ef4444)}
.stat-card.blue::before{background:linear-gradient(90deg,#2563eb,#3b82f6)}
.stat-card.cyan::before{background:linear-gradient(90deg,#0891b2,#06b6d4)}
.stat-card.purple::before{background:linear-gradient(90deg,#7c3aed,#8b5cf6)}
.stat-card .value{font-size:34px;font-weight:900;letter-spacing:-1px;line-height:1}
.stat-card .label{font-size:11px;color:var(--text3);margin-top:6px;font-weight:600}
.stat-card.gold .value{color:var(--gold)}
.stat-card.green .value{color:var(--green)}
.stat-card.red .value{color:var(--red)}
.stat-card.blue .value{color:var(--blue)}
.stat-card.cyan .value{color:var(--cyan)}
.stat-card.purple .value{color:var(--purple)}

.progress-bar{height:8px;background:var(--card3);border-radius:6px;overflow:hidden;margin-top:10px}
.progress-bar .fill{height:100%;border-radius:6px;transition:width 1s ease}
.progress-bar .fill.green{background:linear-gradient(90deg,#1a8a4a,#22c55e)}
.progress-bar .fill.blue{background:linear-gradient(90deg,#2563eb,#60a5fa)}
.progress-bar .fill.gold{background:linear-gradient(90deg,#c8940a,#eab308)}
.progress-bar .fill.red{background:linear-gradient(90deg,#c53030,#ef4444)}
.progress-bar .fill.cyan{background:linear-gradient(90deg,#0891b2,#22d3ee)}
.progress-bar .fill.purple{background:linear-gradient(90deg,#7c3aed,#a78bfa)}

.chart-container{position:relative;height:300px}
.chart-container.tall{height:420px}

table{width:100%;border-collapse:collapse;font-size:12px}
table th{text-align:left;padding:12px 14px;background:var(--card2);color:var(--gold);font-weight:700;border-bottom:2px solid var(--gold);position:sticky;top:0;z-index:1;font-size:10px;text-transform:uppercase;letter-spacing:0.8px}
table td{padding:10px 14px;border-bottom:1px solid var(--border);transition:background .2s}
table tr{transition:all .2s}
table tr:hover td{background:rgba(200,148,10,0.04)}
.table-scroll{max-height:520px;overflow-y:auto;border-radius:12px;border:1px solid var(--border);box-shadow:var(--shadow)}
.table-scroll::-webkit-scrollbar{width:6px}
.table-scroll::-webkit-scrollbar-track{background:var(--card2)}
.table-scroll::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px}

.badge{display:inline-block;padding:3px 10px;border-radius:8px;font-size:10px;font-weight:700;letter-spacing:0.3px;text-transform:uppercase}
.badge.green{background:var(--green-bg);color:var(--green);border:1px solid rgba(26,138,74,0.2)}
.badge.red{background:var(--red-bg);color:var(--red);border:1px solid rgba(197,48,48,0.2)}
.badge.gold{background:var(--gold-bg);color:var(--gold);border:1px solid rgba(200,148,10,0.2)}
.badge.blue{background:var(--blue-bg);color:var(--blue);border:1px solid rgba(37,99,235,0.2)}
.badge.purple{background:rgba(124,58,237,0.08);color:var(--purple);border:1px solid rgba(124,58,237,0.2)}
.badge.cyan{background:rgba(8,145,178,0.08);color:var(--cyan);border:1px solid rgba(8,145,178,0.2)}
.badge.steel{background:var(--card2);color:var(--text2);border:1px solid var(--border)}

.ms-card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:20px;margin-bottom:14px;transition:all .25s;box-shadow:var(--shadow)}
.ms-card:hover{box-shadow:var(--shadow-lg)}
.ms-card .ms-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.ms-card .ms-header h4{font-size:16px;font-weight:800}
.ms-card .ms-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.ms-card .ms-stat{text-align:center;padding:12px 8px;background:var(--card2);border-radius:10px;border:1px solid var(--border)}
.ms-card .ms-stat .num{font-size:20px;font-weight:800}
.ms-card .ms-stat .lbl{font-size:10px;color:var(--text3);margin-top:2px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px}

.search-wrap{position:relative;margin-bottom:16px}
.search-box{width:100%;padding:14px 20px 14px 48px;background:var(--card);border:2px solid var(--border);border-radius:12px;color:var(--text);font-size:14px;outline:none;transition:all .25s;font-family:inherit}
.search-box:focus{border-color:var(--gold);box-shadow:0 0 0 4px rgba(200,148,10,0.1);background:var(--card)}
.search-box::placeholder{color:var(--text3)}
.search-icon{position:absolute;left:16px;top:50%;transform:translateY(-50%);color:var(--text3);font-size:18px;transition:color .25s}
.search-box:focus ~ .search-icon{color:var(--gold)}
.search-count{position:absolute;right:16px;top:50%;transform:translateY(-50%);font-size:11px;color:var(--text3);background:var(--card2);padding:4px 10px;border-radius:6px;font-weight:600;transition:all .25s}
.search-active .search-count{color:var(--gold);background:var(--gold-bg);border:1px solid rgba(200,148,10,0.25)}

.filter-row{display:flex;gap:6px;margin-bottom:16px;flex-wrap:wrap}
.filter-btn{padding:7px 14px;border-radius:8px;border:1px solid var(--border);background:var(--card);color:var(--text3);font-size:11px;font-weight:700;cursor:pointer;transition:all .2s;text-transform:uppercase;letter-spacing:0.5px}
.filter-btn:hover{background:var(--card2);color:var(--text2);border-color:var(--border2)}
.filter-btn.active{background:var(--gold);color:#fff;border-color:var(--gold);box-shadow:0 2px 8px rgba(200,148,10,0.3)}

.search-highlight{background:rgba(200,148,10,0.2);color:var(--gold);padding:1px 4px;border-radius:3px;font-weight:700}
.searching tr.search-match td{background:rgba(200,148,10,0.04);border-bottom-color:rgba(200,148,10,0.15)}
.searching tr.search-match:hover td{background:rgba(200,148,10,0.1)}
.searching tr.search-nomatch td{opacity:0.3}
.searching tr.search-nomatch:hover td{opacity:0.6}
</style>
</head>
<body>
<div class="header" id="mainHeader">
  <div class="header-top">
    <h1><span>KENT</span> PLC - Completion Progress Dashboard</h1>
    <div class="header-badge">
      <span class="tag">PS5 - Tanzania</span>
      <span class="live">LIVE</span>
    </div>
  </div>
  <div class="subtitle">Pre-Commissioning Progress Tracker | Pumping Station 5 | Cut-off: 31 July 2026</div>
  <div class="meta">
    <span>Company: KENT</span>
    <span>Tasks: __TOTAL_TASKS__</span>
    <span>Subsystems: __TOTAL_SUBSYS__</span>
    <span>Punch List: __TOTAL_PL__</span>
    <span>Completion: __COMP_PCT__%</span>
  </div>
</div>

<div class="container">
  <div class="tabs">
    <div class="tab active" onclick="showPanel('overview',this)">Overview</div>
    <div class="tab" onclick="showPanel('milestones',this)">Milestones</div>
    <div class="tab" onclick="showPanel('subsystems',this)">Subsystems</div>
    <div class="tab" onclick="showPanel('punchlist',this)">Punch List</div>
    <div class="tab" onclick="showPanel('charts',this)">Analytics</div>
    <div class="tab" onclick="showPanel('systemview',this)">System View</div>
  </div>

  <!-- OVERVIEW -->
  <div id="overview" class="panel active">
    <div class="grid g5" style="margin-bottom:20px">
      <div class="card stat-card gold"><h3>Total Tasks</h3><div class="value">__TOTAL_TASKS__</div><div class="label">Across 9 Milestones</div></div>
      <div class="card stat-card green"><h3>Closed Tasks</h3><div class="value">__CLOSED_TASKS__</div><div class="label">__COMP_PCT__% Completion</div><div class="progress-bar" style="margin-top:10px"><div class="fill green" style="width:__COMP_PCT_VIS__%"></div></div></div>
      <div class="card stat-card red"><h3>Open Tasks</h3><div class="value">__OPEN_TASKS__</div><div class="label">845 Pending + 3 Started</div></div>
      <div class="card stat-card cyan"><h3>Subsystems</h3><div class="value">__TOTAL_SUBSYS__</div><div class="label">0 Complete / 123 Active</div></div>
      <div class="card stat-card purple"><h3>Punch List</h3><div class="value">__TOTAL_PL__</div><div class="label">__CLOSED_PL__ Closed / __ORIG_PL__ Open</div></div>
    </div>
    <div class="grid g3" style="margin-bottom:20px">
      <div class="card" style="border-left:4px solid var(--blue)">
        <h3>E - Electrical</h3>
        <div style="text-align:center;padding:8px 0">
          <div style="font-size:42px;font-weight:900;color:var(--blue)">538</div>
          <div style="font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:1px;margin-top:2px">Tasks</div>
          <div style="display:flex;justify-content:center;gap:24px;margin-top:12px">
            <div><span style="font-size:20px;font-weight:800;color:var(--green)">3</span><div style="font-size:10px;color:var(--text3)">CLOSED</div></div>
            <div><span style="font-size:20px;font-weight:800;color:var(--red)">535</span><div style="font-size:10px;color:var(--text3)">OPEN</div></div>
          </div>
          <div class="progress-bar" style="margin-top:12px"><div class="fill blue" style="width:0.6%"></div></div>
        </div>
      </div>
      <div class="card" style="border-left:4px solid var(--purple)">
        <h3>I - Instrumentation</h3>
        <div style="text-align:center;padding:8px 0">
          <div style="font-size:42px;font-weight:900;color:var(--purple)">313</div>
          <div style="font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:1px;margin-top:2px">Tasks</div>
          <div style="display:flex;justify-content:center;gap:24px;margin-top:12px">
            <div><span style="font-size:20px;font-weight:800;color:var(--green)">0</span><div style="font-size:10px;color:var(--text3)">CLOSED</div></div>
            <div><span style="font-size:20px;font-weight:800;color:var(--red)">313</span><div style="font-size:10px;color:var(--text3)">OPEN</div></div>
          </div>
          <div class="progress-bar" style="margin-top:12px"><div class="fill purple" style="width:0%"></div></div>
        </div>
      </div>
      <div class="card" style="border-left:4px solid var(--gold)">
        <h3>Subsystem Punch Summary</h3>
        <div style="padding:4px 0">
          <div style="display:flex;justify-content:space-between;padding:10px 12px;border-bottom:1px solid var(--border)"><span style="font-size:12px;font-weight:600">Total Open Punch</span><span style="font-size:18px;font-weight:800;color:var(--gold)">6</span></div>
          <div style="display:flex;justify-content:space-between;padding:10px 12px;border-bottom:1px solid var(--border)"><span style="font-size:12px;color:var(--text2)">Category A - Critical</span><span class="badge red">0</span></div>
          <div style="display:flex;justify-content:space-between;padding:10px 12px;border-bottom:1px solid var(--border)"><span style="font-size:12px;color:var(--text2)">Category B - Major</span><span class="badge gold">3</span></div>
          <div style="display:flex;justify-content:space-between;padding:10px 12px"><span style="font-size:12px;color:var(--text2)">Category C - Minor</span><span class="badge blue">3</span></div>
        </div>
      </div>
    </div>
    <div class="grid g2">
      <div class="card"><h3>Task Status Distribution</h3><div class="chart-container"><canvas id="overviewPie"></canvas></div></div>
      <div class="card"><h3>Punch List Status</h3><div class="chart-container"><canvas id="plPie"></canvas></div></div>
    </div>
  </div>

  <!-- MILESTONES -->
  <div id="milestones" class="panel">
    <div class="card" style="margin-bottom:20px"><h3>Tasks by Milestone</h3><div class="chart-container tall"><canvas id="msBar"></canvas></div></div>
    <div id="milestoneCards"></div>
  </div>

  <!-- SUBSYSTEMS -->
  <div id="subsystems" class="panel">
    <div class="search-wrap" id="subsysSearchWrap">
      <input type="text" class="search-box" id="subsysSearch" placeholder="Search systems, subsystems, milestones..." oninput="filterSubsystems()" onfocus="onSearchFocus()" onblur="onSearchBlur()">
      <div class="search-icon">&#128269;</div>
      <div class="search-count" id="subsysCount">123 results</div>
    </div>
    <div class="filter-row">
      <div class="filter-btn active" onclick="filterMs(this,'all')">All (123)</div>
      <div class="filter-btn" onclick="filterMs(this,'PS5 - Milestone A')">A (2)</div>
      <div class="filter-btn" onclick="filterMs(this,'PS5 - Milestone B')">B (13)</div>
      <div class="filter-btn" onclick="filterMs(this,'PS5 - Milestone C')">C (8)</div>
      <div class="filter-btn" onclick="filterMs(this,'PS5 - Milestone D')">D (11)</div>
      <div class="filter-btn" onclick="filterMs(this,'PS5 - Milestone E')">E (17)</div>
      <div class="filter-btn" onclick="filterMs(this,'PS5 - Milestone F')">F (14)</div>
      <div class="filter-btn" onclick="filterMs(this,'PS5 - Milestone G')">G (15)</div>
      <div class="filter-btn" onclick="filterMs(this,'PS5 - Milestone H')">H (32)</div>
      <div class="filter-btn" onclick="filterMs(this,'PS5 - Milestone I')">I (11)</div>
    </div>
    <div class="table-scroll" id="subsysTableWrap">
      <table id="subsysTable">
        <thead><tr><th>#</th><th>System</th><th>Subsystem</th><th>MILESTONE</th><th style="text-align:right">Total</th><th style="text-align:right">Closed</th><th style="text-align:right">E-Open</th><th style="text-align:right">I-Open</th><th style="text-align:right">%</th><th style="text-align:center">A</th><th style="text-align:center">B</th><th style="text-align:center">C</th><th style="width:130px">Progress</th></tr></thead>
        <tbody id="subsysBody"></tbody>
      </table>
    </div>
  </div>

  <!-- PUNCH LIST -->
  <div id="punchlist" class="panel">
    <div class="grid g4" style="margin-bottom:20px">
      <div class="card stat-card purple"><h3>Total Punch Items</h3><div class="value">__TOTAL_PL__</div><div class="label">All Categories</div></div>
      <div class="card stat-card red"><h3>Originated (Open)</h3><div class="value">__ORIG_PL__</div><div class="label">__ORIG_PCT__% of Total</div></div>
      <div class="card stat-card green"><h3>Closed</h3><div class="value">__CLOSED_PL__</div><div class="label">__CLOSED_PL_PCT__% of Total</div></div>
      <div class="card stat-card blue"><h3>Completed</h3><div class="value">__COMPLETED_PL__</div><div class="label">Fully Resolved</div></div>
    </div>
    <div class="grid g2">
      <div class="card"><h3>Punch List by Category</h3><div class="chart-container"><canvas id="plCatChart"></canvas></div></div>
      <div class="card"><h3>Punch List by Milestone</h3><div class="chart-container"><canvas id="plMsChart"></canvas></div></div>
    </div>
  </div>

  <!-- ANALYTICS -->
  <div id="charts" class="panel">
    <div class="grid g2">
      <div class="card"><h3>Tasks by Milestone</h3><div class="chart-container tall"><canvas id="chartTasksMs"></canvas></div></div>
      <div class="card"><h3>Completion Radar</h3><div class="chart-container tall"><canvas id="chartCompMs"></canvas></div></div>
      <div class="card"><h3>Discipline Split</h3><div class="chart-container"><canvas id="chartDisc"></canvas></div></div>
      <div class="card"><h3>Punch by Category per Milestone</h3><div class="chart-container tall"><canvas id="chartPlCross"></canvas></div></div>
    </div>
  </div>

  <!-- SYSTEM VIEW -->
  <div id="systemview" class="panel">
    <div class="card" style="margin-bottom:20px"><h3>Progress by System Group</h3><div class="chart-container tall"><canvas id="chartSys"></canvas></div></div>
    <div class="table-scroll">
      <table><thead><tr><th>System</th><th style="text-align:right">Subsystems</th><th style="text-align:right">Total Tasks</th><th style="text-align:right">Closed</th><th style="text-align:right">Open</th><th style="text-align:right">%</th><th style="width:180px">Progress</th></tr></thead>
      <tbody id="sysBody"></tbody></table>
    </div>
  </div>
</div>

<script>
var DATA = __DATA_JSON__;
var searchActive = false;
Chart.defaults.color = '#6b5e4d';
Chart.defaults.borderColor = '#d9d0c1';
Chart.defaults.font.family = "'Inter',system-ui,sans-serif";

var msColors = ['#c8940a','#c53030','#1a8a4a','#2563eb','#7c3aed','#ec4899','#0891b2','#d97706','#6366f1'];
var msColorsAlpha = ['rgba(200,148,10,0.7)','rgba(197,48,48,0.7)','rgba(26,138,74,0.7)','rgba(37,99,235,0.7)','rgba(124,58,237,0.7)','rgba(236,72,153,0.7)','rgba(8,145,178,0.7)','rgba(217,119,6,0.7)','rgba(99,102,241,0.7)'];

function showPanel(id, el) {
  document.querySelectorAll('.panel').forEach(function(p){ p.classList.remove('active') });
  document.querySelectorAll('.tab').forEach(function(t){ t.classList.remove('active') });
  document.getElementById(id).classList.add('active');
  el.classList.add('active');
  if (id === 'charts') initCharts();
  if (id === 'punchlist') initPunchList();
  if (id === 'systemview') initSystemView();
}

function initOverview() {
  new Chart(document.getElementById('overviewPie'), {
    type: 'doughnut',
    data: { labels: ['Closed (3)', 'Started (3)', 'Pending (845)'], datasets: [{ data: [3, 3, 845], backgroundColor: ['#1a8a4a','#c8940a','#c53030'], borderWidth: 3, borderColor: '#fffcf7', hoverOffset: 10 }] },
    options: { responsive: true, maintainAspectRatio: false, cutout: '68%', plugins: { legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyle: 'circle', color: '#6b5e4d' } } } }
  });
  new Chart(document.getElementById('plPie'), {
    type: 'doughnut',
    data: { labels: ['Originated (1766)', 'Closed (437)', 'Completed (30)'], datasets: [{ data: [1766, 437, 30], backgroundColor: ['#c53030','#1a8a4a','#2563eb'], borderWidth: 3, borderColor: '#fffcf7', hoverOffset: 10 }] },
    options: { responsive: true, maintainAspectRatio: false, cutout: '68%', plugins: { legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyle: 'circle', color: '#6b5e4d' } } } }
  });
}

function initMilestones() {
  var sorted = DATA.milestones.slice().sort(function(a,b){ return a.name.localeCompare(b.name) });
  var labels = sorted.map(function(m){ return 'Milestone ' + m.letter });
  new Chart(document.getElementById('msBar'), {
    type: 'bar',
    data: { labels: labels, datasets: [
      { label: 'Closed', data: sorted.map(function(m){ return m.closedTasks }), backgroundColor: '#1a8a4a', borderRadius: 6, barPercentage: 0.65 },
      { label: 'Open', data: sorted.map(function(m){ return m.openTasks }), backgroundColor: '#c53030', borderRadius: 6, barPercentage: 0.65 }
    ]},
    options: { responsive: true, maintainAspectRatio: false,
      scales: { x: { stacked: true, grid: { display: false } }, y: { stacked: true, beginAtZero: true, grid: { color: '#ede7db' } } },
      plugins: { legend: { position: 'top', labels: { usePointStyle: true, pointStyle: 'circle', padding: 16, color: '#6b5e4d' } } }
    }
  });
  var container = document.getElementById('milestoneCards');
  container.innerHTML = '';
  sorted.forEach(function(m, i) {
    var discHtml = m.disciplines.map(function(d) {
      return '<div style="display:flex;justify-content:space-between;padding:8px 12px;border-bottom:1px solid var(--border);font-size:12px"><span style="font-weight:500">' + d.name + '</span><span><span style="color:#1a8a4a;font-weight:700">' + d.closedTasks + '</span> / ' + d.totalTasks + '</span></div>';
    }).join('');
    container.innerHTML += '<div class="ms-card" style="border-left:5px solid ' + msColors[i % msColors.length] + '">' +
      '<div class="ms-header"><h4 style="color:' + msColors[i % msColors.length] + '">Milestone ' + m.letter + '</h4><span class="badge ' + (m.completion > 0 ? 'green' : 'red') + '">' + m.completion + '% Complete</span></div>' +
      '<div class="ms-stats"><div class="ms-stat"><div class="num" style="color:#c8940a">' + m.subsystems + '</div><div class="lbl">Subsystems</div></div><div class="ms-stat"><div class="num" style="color:#0891b2">' + m.totalTasks + '</div><div class="lbl">Total Tasks</div></div><div class="ms-stat"><div class="num" style="color:#1a8a4a">' + m.closedTasks + '</div><div class="lbl">Closed</div></div><div class="ms-stat"><div class="num" style="color:#c53030">' + m.openTasks + '</div><div class="lbl">Open</div></div></div>' +
      '<div class="progress-bar" style="margin-top:14px;height:10px"><div class="fill green" style="width:' + Math.max(m.completion, 0.5) + '%"></div></div>' +
      '<div style="margin-top:12px;background:var(--card2);border-radius:10px;padding:6px 0;border:1px solid var(--border)">' + discHtml + '</div></div>';
  });
}

var currentMsFilter = 'all';
function initSubsystems() { renderSubsystems(); }
function filterMs(el, ms) { currentMsFilter = ms; document.querySelectorAll('.filter-btn').forEach(function(b){ b.classList.remove('active') }); el.classList.add('active'); renderSubsystems(); }
function onSearchFocus() { searchActive = true; document.getElementById('subsysSearchWrap').classList.add('search-active'); document.getElementById('mainHeader').classList.add('searching-mode'); }
function onSearchBlur() { if (!document.getElementById('subsysSearch').value) { searchActive = false; document.getElementById('subsysSearchWrap').classList.remove('search-active'); document.getElementById('mainHeader').classList.remove('searching-mode'); } }
function filterSubsystems() { renderSubsystems(); }
function highlightText(text, query) { if (!query) return text; var regex = new RegExp('(' + query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi'); return text.replace(regex, '<span class="search-highlight">$1</span>'); }
function renderSubsystems() {
  var query = document.getElementById('subsysSearch').value.toLowerCase();
  var filtered = DATA.subsystems.filter(function(s) {
    var matchSearch = !query || s.system.toLowerCase().indexOf(query) >= 0 || s.subsystem.toLowerCase().indexOf(query) >= 0 || s.milestone.toLowerCase().indexOf(query) >= 0;
    var matchMs = currentMsFilter === 'all' || s.milestone === currentMsFilter;
    return matchSearch && matchMs;
  });
  var isSearching = query.length > 0;
  var tableWrap = document.getElementById('subsysTableWrap');
  if (isSearching) tableWrap.classList.add('searching'); else tableWrap.classList.remove('searching');
  document.getElementById('subsysCount').textContent = filtered.length + ' results';
  document.getElementById('subsysBody').innerHTML = filtered.map(function(s, idx) {
    var pct = s.total > 0 ? (s.closed / s.total * 100).toFixed(1) : '0.0';
    var fillColor = pct >= 50 ? 'green' : pct > 0 ? 'gold' : 'red';
    var systemText = highlightText(s.system, document.getElementById('subsysSearch').value);
    var subsystemText = highlightText(s.subsystem, document.getElementById('subsysSearch').value);
    return '<tr class="' + (isSearching ? 'search-match' : '') + '">' +
      '<td style="color:var(--text3);font-size:10px">' + (idx + 1) + '</td>' +
      '<td style="font-size:11px;max-width:200px;word-break:break-all;color:var(--text2)">' + systemText + '</td>' +
      '<td style="font-size:11px;max-width:260px;word-break:break-all;font-weight:500">' + subsystemText + '</td>' +
      '<td><span class="badge steel">' + s.milestone.replace('PS5 - ','') + '</span></td>' +
      '<td style="text-align:right;font-weight:800">' + s.total + '</td>' +
      '<td style="text-align:right;color:#1a8a4a;font-weight:700">' + s.closed + '</td>' +
      '<td style="text-align:right;color:#2563eb">' + s.elecOpen + '</td>' +
      '<td style="text-align:right;color:#7c3aed">' + s.instrOpen + '</td>' +
      '<td style="text-align:right;font-weight:800">' + pct + '%</td>' +
      '<td style="text-align:center">' + (s.punchA > 0 ? '<span class="badge red">' + s.punchA + '</span>' : '<span style="color:var(--text3)">-</span>') + '</td>' +
      '<td style="text-align:center">' + (s.punchB > 0 ? '<span class="badge gold">' + s.punchB + '</span>' : '<span style="color:var(--text3)">-</span>') + '</td>' +
      '<td style="text-align:center">' + (s.punchC > 0 ? '<span class="badge blue">' + s.punchC + '</span>' : '<span style="color:var(--text3)">-</span>') + '</td>' +
      '<td><div class="progress-bar" style="height:6px"><div class="fill ' + fillColor + '" style="width:' + pct + '%"></div></div></td></tr>';
  }).join('');
}

var punchListInit = false;
function initPunchList() {
  if (punchListInit) return; punchListInit = true;
  new Chart(document.getElementById('plCatChart'), {
    type: 'doughnut',
    data: { labels: Object.keys(DATA.plByCategory), datasets: [{ data: Object.values(DATA.plByCategory), backgroundColor: ['#c53030','#c8940a','#0891b2'], borderWidth: 3, borderColor: '#fffcf7', hoverOffset: 10 }] },
    options: { responsive: true, maintainAspectRatio: false, cutout: '62%', plugins: { legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyle: 'circle', color: '#6b5e4d' } } } }
  });
  var plSorted = DATA.plByMilestone.slice().sort(function(a,b){ return (a.Priority||'').localeCompare(b.Priority||''); });
  new Chart(document.getElementById('plMsChart'), {
    type: 'bar',
    data: { labels: plSorted.map(function(p){ return (p.Priority||'').replace('PS5 - ','') }),
      datasets: [
        { label: 'Originated', data: plSorted.map(function(p){return p.originated}), backgroundColor: '#c53030', borderRadius: 4 },
        { label: 'Closed', data: plSorted.map(function(p){return p.closed}), backgroundColor: '#1a8a4a', borderRadius: 4 },
        { label: 'Completed', data: plSorted.map(function(p){return p.completed}), backgroundColor: '#2563eb', borderRadius: 4 }
      ]},
    options: { responsive: true, maintainAspectRatio: false, scales: { x: { stacked: true, grid: { display: false } }, y: { stacked: true, beginAtZero: true, grid: { color: '#ede7db' } } }, plugins: { legend: { position: 'top', labels: { usePointStyle: true, pointStyle: 'circle', padding: 16, color: '#6b5e4d' } } } }
  });
}

var chartsInitialized = false;
function initCharts() {
  if (chartsInitialized) return; chartsInitialized = true;
  var sorted = DATA.milestones.slice().sort(function(a,b){ return a.name.localeCompare(b.name) });
  var labels = sorted.map(function(m){ return 'Ms ' + m.letter });
  new Chart(document.getElementById('chartTasksMs'), {
    type: 'bar', data: { labels: labels, datasets: [
      { label: 'Total Tasks', data: sorted.map(function(m){ return m.totalTasks }), backgroundColor: msColorsAlpha, borderRadius: 6, barPercentage: 0.7 },
      { label: 'Closed', data: sorted.map(function(m){ return m.closedTasks }), backgroundColor: '#1a8a4a', borderRadius: 6, barPercentage: 0.7 }
    ]}, options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, grid: { color: '#ede7db' } }, x: { grid: { display: false } } }, plugins: { legend: { labels: { usePointStyle: true, pointStyle: 'circle', color: '#6b5e4d' } } } }
  });
  new Chart(document.getElementById('chartCompMs'), {
    type: 'radar', data: { labels: sorted.map(function(m){ return 'Ms ' + m.letter }), datasets: [{
      label: 'Completion %', data: sorted.map(function(m){ return m.completion }),
      backgroundColor: 'rgba(200,148,10,0.15)', borderColor: '#c8940a', pointBackgroundColor: '#c8940a', pointBorderColor: '#fffcf7', pointBorderWidth: 2, borderWidth: 2
    }]}, options: { responsive: true, maintainAspectRatio: false, scales: { r: { beginAtZero: true, max: 5, ticks: { stepSize: 1, backdropColor: 'transparent' }, grid: { color: '#ede7db' }, angleLines: { color: '#ede7db' }, pointLabels: { color: '#6b5e4d' } } }, plugins: { legend: { display: false } } }
  });
  new Chart(document.getElementById('chartDisc'), {
    type: 'doughnut', data: { labels: ['E - Electrical (538)', 'I - Instrumentation (313)'], datasets: [{ data: [538, 313], backgroundColor: ['#2563eb', '#7c3aed'], borderWidth: 3, borderColor: '#fffcf7', hoverOffset: 10 }] },
    options: { responsive: true, maintainAspectRatio: false, cutout: '62%', plugins: { legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyle: 'circle', color: '#6b5e4d' } } } }
  });
  var plLetters = Object.keys(DATA.plCross).sort();
  new Chart(document.getElementById('chartPlCross'), {
    type: 'bar', data: { labels: plLetters.map(function(l){ return 'Ms ' + l }),
      datasets: [
        { label: 'A - Critical', data: plLetters.map(function(l){ return DATA.plCross[l].A }), backgroundColor: '#c53030', borderRadius: 4 },
        { label: 'B - Major', data: plLetters.map(function(l){ return DATA.plCross[l].B }), backgroundColor: '#c8940a', borderRadius: 4 },
        { label: 'C - Minor', data: plLetters.map(function(l){ return DATA.plCross[l].C }), backgroundColor: '#0891b2', borderRadius: 4 }
      ]}, options: { responsive: true, maintainAspectRatio: false, scales: { x: { stacked: true, grid: { display: false } }, y: { stacked: true, beginAtZero: true, grid: { color: '#ede7db' } } }, plugins: { legend: { position: 'top', labels: { usePointStyle: true, pointStyle: 'circle', padding: 16, color: '#6b5e4d' } } } }
  });
}

var systemViewInit = false;
function initSystemView() {
  if (systemViewInit) return; systemViewInit = true;
  document.getElementById('sysBody').innerHTML = DATA.sysSummary.map(function(s) {
    var pctColor = s.pct >= 50 ? 'green' : s.pct > 0 ? 'gold' : 'red';
    var open = s.total - s.closed;
    return '<tr><td style="font-weight:600;font-size:12px">' + s.system + '</td><td style="text-align:right;color:var(--text2)">' + s.count + '</td><td style="text-align:right;font-weight:800">' + s.total + '</td><td style="text-align:right;color:#1a8a4a;font-weight:700">' + s.closed + '</td><td style="text-align:right;color:#c53030;font-weight:700">' + open + '</td><td style="text-align:right;font-weight:800">' + s.pct + '%</td><td><div class="progress-bar" style="height:8px"><div class="fill ' + pctColor + '" style="width:' + s.pct + '%"></div></div></td></tr>';
  }).join('');
  new Chart(document.getElementById('chartSys'), {
    type: 'bar', data: { labels: DATA.sysSummary.map(function(s){ return s.system.replace('PS5-','') }),
      datasets: [{ label: 'Total Tasks', data: DATA.sysSummary.map(function(s){ return s.total }), backgroundColor: DATA.sysSummary.map(function(s,i){ return msColors[i % msColors.length] + 'cc' }), borderRadius: 6 }]
    }, options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', scales: { x: { beginAtZero: true, grid: { color: '#ede7db' } }, y: { grid: { display: false }, ticks: { font: { size: 11 } } } }, plugins: { legend: { display: false } } }
  });
}

initOverview();
initMilestones();
initSubsystems();
</script>
</body>
</html>'''


def generate_html(data):
    data_json = json.dumps(data, default=str)
    comp_pct = round(data["closedTasks"] / data["totalTasks"] * 100, 2)
    html = HTML_TEMPLATE
    html = html.replace('__DATA_JSON__', data_json)
    html = html.replace('__TOTAL_TASKS__', str(data["totalTasks"]))
    html = html.replace('__CLOSED_TASKS__', str(data["closedTasks"]))
    html = html.replace('__OPEN_TASKS__', str(data["openTasks"]))
    html = html.replace('__TOTAL_SUBSYS__', str(data["totalSubsystems"]))
    html = html.replace('__COMP_PCT__', str(comp_pct))
    html = html.replace('__COMP_PCT_VIS__', str(max(comp_pct, 2)))
    html = html.replace('__TOTAL_PL__', str(data["totalPL"]))
    html = html.replace('__CLOSED_PL__', str(data["closedPL"]))
    html = html.replace('__ORIG_PL__', str(data["originatedPL"]))
    html = html.replace('__COMPLETED_PL__', str(data["completedPL"]))
    html = html.replace('__ORIG_PCT__', str(round(data["originatedPL"] / data["totalPL"] * 100, 1)))
    html = html.replace('__CLOSED_PL_PCT__', str(round(data["closedPL"] / data["totalPL"] * 100, 1)))
    return html


if __name__ == '__main__':
    print("Extracting data from Excel...")
    data = extract_data()
    print(f"Milestones: {len(data['milestones'])} | Subsystems: {len(data['subsystems'])}")
    print("Generating HTML...")
    html = generate_html(data)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Saved: {OUTPUT_PATH}")
