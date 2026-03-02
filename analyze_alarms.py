#!/usr/bin/env python3
"""
Analyze missile alarm data from the war starting 2026-02-28
Creates HTML visualization of hourly histogram for Tel Aviv alarms
"""

import csv
from collections import defaultdict
from datetime import datetime

# Read the CSV file
alarms = []
with open('alarms.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        alarms.append(row)

# Filter for war period (2026-02-28 onwards)
war_start = datetime(2026, 2, 28)
war_alarms = []
for alarm in alarms:
    try:
        alarm_time = datetime.strptime(alarm['time'], '%Y-%m-%d %H:%M:%S')
        if alarm_time >= war_start:
            alarm['datetime'] = alarm_time
            war_alarms.append(alarm)
    except:
        continue

print(f"Total alarms during war period: {len(war_alarms)}")

# Filter for Tel Aviv alarms only
tel_aviv_alarms = [a for a in war_alarms if 'תל אביב' in a['cities']]
print(f"Tel Aviv alarms during war period: {len(tel_aviv_alarms)}")

# Deduplicate barrages - a barrage is a unique timestamp (to the minute)
def get_barrage_key(dt):
    """Round to minute for barrage grouping"""
    return dt.strftime('%Y-%m-%d %H:%M')

# Get unique barrages for Tel Aviv (deduplicate by minute)
tel_aviv_barrages = {}
for alarm in tel_aviv_alarms:
    key = get_barrage_key(alarm['datetime'])
    if key not in tel_aviv_barrages:
        tel_aviv_barrages[key] = alarm['datetime']

print(f"Unique Tel Aviv barrages: {len(tel_aviv_barrages)}")

# Group by day
all_days = ['2026-02-28', '2026-03-01', '2026-03-02', '2026-03-03']
all_day_names = ['Saturday (Feb 28)', 'Sunday (Mar 1)', 'Monday (Mar 2)', 'Tuesday (Mar 3)']

# Calculate BARRAGE histogram per day (hour 0-23) - deduplicated
barrage_histograms = {}
for day in all_days:
    barrage_histograms[day] = [0] * 24

for barrage_time_str, barrage_dt in tel_aviv_barrages.items():
    day_str = barrage_dt.strftime('%Y-%m-%d')
    hour = barrage_dt.hour
    if day_str in barrage_histograms:
        barrage_histograms[day_str][hour] += 1

# Calculate ALARM histogram per day (hour 0-23) - individual alarms (not deduplicated)
alarm_histograms = {}
for day in all_days:
    alarm_histograms[day] = [0] * 24

for alarm in tel_aviv_alarms:
    day_str = alarm['datetime'].strftime('%Y-%m-%d')
    hour = alarm['datetime'].hour
    if day_str in alarm_histograms:
        alarm_histograms[day_str][hour] += 1

# Remove trailing days with no data (but keep intermediate zero days)
days = all_days[:]
day_names = all_day_names[:]
while days and sum(barrage_histograms[days[-1]]) == 0 and sum(alarm_histograms[days[-1]]) == 0:
    days.pop()
    day_names.pop()

# Print statistics
print("\n=== Tel Aviv Barrage Histogram by Hour ===")
for i, day in enumerate(days):
    total = sum(barrage_histograms[day])
    print(f"\n{day_names[i]}: {total} barrages")
    for hour in range(24):
        count = barrage_histograms[day][hour]
        if count > 0:
            bar = '#' * count
            print(f"  {hour:02d}:00 - {count:2d} {bar}")

print("\n=== Tel Aviv Alarm (Individual) Histogram by Hour ===")
for i, day in enumerate(days):
    total = sum(alarm_histograms[day])
    print(f"\n{day_names[i]}: {total} alarms")
    for hour in range(24):
        count = alarm_histograms[day][hour]
        if count > 0:
            bar = '#' * min(count, 50)
            print(f"  {hour:02d}:00 - {count:2d} {bar}")

# Calculate changes between days
print("\n=== Changes Between Days (Barrages) ===")
for i in range(1, len(days)):
    prev_day = days[i-1]
    curr_day = days[i]
    prev_total = sum(barrage_histograms[prev_day])
    curr_total = sum(barrage_histograms[curr_day])
    change = curr_total - prev_total
    pct = (change / prev_total * 100) if prev_total > 0 else 0
    print(f"{day_names[i-1]} -> {day_names[i]}: {prev_total} -> {curr_total} ({change:+d}, {pct:+.1f}%)")

# Generate HTML
colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96c93d']

html_content = '''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tel Aviv Missile Alarms Analysis - War 2026</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
            color: #fff;
        }
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        .subtitle {
            text-align: center;
            margin-bottom: 30px;
            color: #aaa;
            font-size: 1.1em;
        }
        .view-toggle {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 30px;
        }
        .view-btn {
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: all 0.3s ease;
            background: rgba(255,255,255,0.1);
            color: #fff;
            border: 2px solid transparent;
        }
        .view-btn.active {
            background: #ff6b6b;
            border-color: #ff6b6b;
        }
        .view-btn:hover:not(.active) {
            background: rgba(255,255,255,0.2);
        }
        .view-section {
            display: none;
        }
        .view-section.active {
            display: block;
        }
        .stats-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #ff6b6b;
        }
        .stat-label {
            color: #aaa;
            margin-top: 5px;
        }
        .chart-container {
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .chart-title {
            text-align: center;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        .chart-wrapper {
            height: 250px;
        }
        .day-chart-wrapper {
            height: 180px;
        }
        .day-chart {
            background: rgba(255,255,255,0.03);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .day-chart h3 {
            text-align: center;
            margin-bottom: 15px;
            color: #ff9f43;
        }
        .change-indicator {
            text-align: center;
            padding: 10px;
            margin-top: 10px;
            border-radius: 8px;
            font-size: 0.9em;
        }
        .change-up {
            background: rgba(255, 71, 87, 0.2);
            color: #ff4757;
        }
        .change-down {
            background: rgba(46, 213, 115, 0.2);
            color: #2ed573;
        }
        .legend {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }
        footer {
            text-align: center;
            margin-top: 40px;
            color: #666;
            font-size: 0.9em;
        }
        .section-title {
            text-align: center;
            font-size: 1.8em;
            margin: 40px 0 20px 0;
            color: #ff9f43;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Tel Aviv Missile Alarms</h1>
        <p class="subtitle">War Period: February 28 - March 3, 2026 | Hourly Analysis</p>

        <div class="view-toggle">
            <button class="view-btn active" onclick="showView('barrages')">Barrages (Deduplicated)</button>
            <button class="view-btn" onclick="showView('alarms')">Individual Alarms</button>
        </div>

        <!-- BARRAGES VIEW -->
        <div id="barrages-view" class="view-section active">
            <div class="stats-row">
'''

# Add barrage stat cards
total_barrages = sum(sum(barrage_histograms[d]) for d in days)
for i, day in enumerate(days):
    total = sum(barrage_histograms[day])
    html_content += f'''
                <div class="stat-card">
                    <div class="stat-value">{total}</div>
                    <div class="stat-label">{day_names[i]}</div>
                </div>
'''

html_content += f'''
                <div class="stat-card">
                    <div class="stat-value" style="color: #ffa502;">{total_barrages}</div>
                    <div class="stat-label">Total Barrages</div>
                </div>
            </div>

            <div class="chart-container">
                <h2 class="chart-title">All Days Combined - Hourly Distribution (Stacked)</h2>
                <div class="chart-wrapper">
                    <canvas id="barrageCombinedChart"></canvas>
                </div>
                <div class="legend">
'''

for i, day_name in enumerate(day_names):
    html_content += f'                    <div class="legend-item"><div class="legend-color" style="background:{colors[i]}"></div>{day_name}</div>\n'

html_content += '''                </div>
            </div>

            <h2 class="section-title">Daily Breakdown</h2>
'''

# Add individual barrage day charts
for i, day in enumerate(days):
    change_html = ''
    if i > 0:
        prev_total = sum(barrage_histograms[days[i-1]])
        curr_total = sum(barrage_histograms[day])
        if prev_total > 0:
            change = curr_total - prev_total
            pct = change / prev_total * 100
            change_class = 'change-up' if change > 0 else 'change-down'
            arrow = '↑' if change > 0 else '↓'
            change_html = f'<div class="change-indicator {change_class}">{arrow} {abs(change)} barrages ({pct:+.1f}%) from previous day</div>'

    html_content += f'''
            <div class="day-chart">
                <h3>{day_names[i]}</h3>
                <div class="day-chart-wrapper">
                    <canvas id="barrageChart{i}"></canvas>
                </div>
                {change_html}
            </div>
'''

html_content += '''
        </div>

        <!-- ALARMS VIEW -->
        <div id="alarms-view" class="view-section">
            <div class="stats-row">
'''

# Add alarm stat cards
total_alarms = sum(sum(alarm_histograms[d]) for d in days)
for i, day in enumerate(days):
    total = sum(alarm_histograms[day])
    html_content += f'''
                <div class="stat-card">
                    <div class="stat-value">{total}</div>
                    <div class="stat-label">{day_names[i]}</div>
                </div>
'''

html_content += f'''
                <div class="stat-card">
                    <div class="stat-value" style="color: #ffa502;">{total_alarms}</div>
                    <div class="stat-label">Total Alarms</div>
                </div>
            </div>

            <div class="chart-container">
                <h2 class="chart-title">All Days Combined - Hourly Distribution (Stacked)</h2>
                <div class="chart-wrapper">
                    <canvas id="alarmCombinedChart"></canvas>
                </div>
                <div class="legend">
'''

for i, day_name in enumerate(day_names):
    html_content += f'                    <div class="legend-item"><div class="legend-color" style="background:{colors[i]}"></div>{day_name}</div>\n'

html_content += '''                </div>
            </div>

            <h2 class="section-title">Daily Breakdown</h2>
'''

# Add individual alarm day charts
for i, day in enumerate(days):
    change_html = ''
    if i > 0:
        prev_total = sum(alarm_histograms[days[i-1]])
        curr_total = sum(alarm_histograms[day])
        if prev_total > 0:
            change = curr_total - prev_total
            pct = change / prev_total * 100
            change_class = 'change-up' if change > 0 else 'change-down'
            arrow = '↑' if change > 0 else '↓'
            change_html = f'<div class="change-indicator {change_class}">{arrow} {abs(change)} alarms ({pct:+.1f}%) from previous day</div>'

    html_content += f'''
            <div class="day-chart">
                <h3>{day_names[i]}</h3>
                <div class="day-chart-wrapper">
                    <canvas id="alarmChart{i}"></canvas>
                </div>
                {change_html}
            </div>
'''

html_content += '''
        </div>
    </div>

    <footer>
        <p>Data source: Israeli Home Front Command alerts | Analysis generated on March 3, 2026</p>
    </footer>

    <script>
        const hours = ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00',
                       '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00',
                       '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'];

        const colors = ''' + str(colors) + ''';
        const dayNames = ''' + str(day_names) + ''';

        const barrageData = {
'''

for i, day in enumerate(days):
    html_content += f"            '{day}': {barrage_histograms[day]},\n"

html_content += '''        };

        const alarmData = {
'''

for i, day in enumerate(days):
    html_content += f"            '{day}': {alarm_histograms[day]},\n"

html_content += '''        };

        const days = ''' + str(days) + ''';

        // View toggle
        function showView(view) {
            document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(view + '-view').classList.add('active');
            event.target.classList.add('active');
        }

        // Create stacked combined chart
        function createCombinedChart(canvasId, data) {
            const ctx = document.getElementById(canvasId).getContext('2d');
            return new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: hours,
                    datasets: days.map((day, i) => ({
                        label: dayNames[i],
                        data: data[day],
                        backgroundColor: colors[i],
                        borderColor: colors[i],
                        borderWidth: 1
                    }))
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            stacked: true,
                            ticks: { color: '#aaa' },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        },
                        y: {
                            stacked: true,
                            beginAtZero: true,
                            ticks: { color: '#aaa' },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        }
                    }
                }
            });
        }

        // Create individual day chart
        function createDayChart(canvasId, data, colorIndex) {
            const ctx = document.getElementById(canvasId).getContext('2d');
            return new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: hours,
                    datasets: [{
                        label: 'Count',
                        data: data,
                        backgroundColor: colors[colorIndex],
                        borderColor: colors[colorIndex],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#aaa', maxRotation: 45, minRotation: 45 },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: { color: '#aaa' },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        }
                    }
                }
            });
        }

        // Initialize all charts
        createCombinedChart('barrageCombinedChart', barrageData);
        createCombinedChart('alarmCombinedChart', alarmData);

        days.forEach((day, i) => {
            createDayChart('barrageChart' + i, barrageData[day], i);
            createDayChart('alarmChart' + i, alarmData[day], i);
        });
    </script>
</body>
</html>
'''

# Write HTML file
with open('tel_aviv_alarms.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("\n✓ HTML file generated: tel_aviv_alarms.html")
