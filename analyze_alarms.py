#!/usr/bin/env python3
"""
Analyze missile alarm data from the war starting 2026-02-28
Creates HTML visualization of hourly histogram for Tel Aviv alarms
"""

import csv
import json
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

# Get all unique cities
all_cities = sorted(set(a['cities'] for a in war_alarms))
print(f"Unique cities: {len(all_cities)}")

# Group by day
all_days = ['2026-02-28', '2026-03-01', '2026-03-02', '2026-03-03']
all_day_names = ['Saturday (Feb 28)', 'Sunday (Mar 1)', 'Monday (Mar 2)', 'Tuesday (Mar 3)']
all_day_names_he = ['שבת (28 בפברואר)', 'ראשון (1 במרץ)', 'שני (2 במרץ)', 'שלישי (3 במרץ)']

def get_barrage_key(dt):
    """Round to minute for barrage grouping"""
    return dt.strftime('%Y-%m-%d %H:%M')

def calculate_histograms(city_filter=None):
    """Calculate histograms for a specific city or all cities"""
    if city_filter:
        filtered_alarms = [a for a in war_alarms if city_filter in a['cities']]
    else:
        filtered_alarms = war_alarms

    # Deduplicate barrages
    barrages = {}
    for alarm in filtered_alarms:
        key = get_barrage_key(alarm['datetime'])
        if key not in barrages:
            barrages[key] = alarm['datetime']

    # Calculate BARRAGE histogram per day
    barrage_hist = {}
    for day in all_days:
        barrage_hist[day] = [0] * 24

    for barrage_time_str, barrage_dt in barrages.items():
        day_str = barrage_dt.strftime('%Y-%m-%d')
        hour = barrage_dt.hour
        if day_str in barrage_hist:
            barrage_hist[day_str][hour] += 1

    # Calculate ALARM histogram per day
    alarm_hist = {}
    for day in all_days:
        alarm_hist[day] = [0] * 24

    for alarm in filtered_alarms:
        day_str = alarm['datetime'].strftime('%Y-%m-%d')
        hour = alarm['datetime'].hour
        if day_str in alarm_hist:
            alarm_hist[day_str][hour] += 1

    return barrage_hist, alarm_hist

# Calculate histograms for all cities (for determining which days to show)
barrage_histograms_all, alarm_histograms_all = calculate_histograms()

# Remove trailing days with no data
days = all_days[:]
day_names = all_day_names[:]
day_names_he = all_day_names_he[:]
while days and sum(barrage_histograms_all[days[-1]]) == 0 and sum(alarm_histograms_all[days[-1]]) == 0:
    days.pop()
    day_names.pop()
    day_names_he.pop()

print(f"Days with data: {len(days)}")

# Pre-calculate histograms for all cities
city_data = {}
for city in all_cities:
    barrage_hist, alarm_hist = calculate_histograms(city)
    # Only include cities that have data in the active days
    has_data = any(sum(barrage_hist[d]) > 0 or sum(alarm_hist[d]) > 0 for d in days)
    if has_data:
        city_data[city] = {
            'barrage': {d: barrage_hist[d] for d in days},
            'alarm': {d: alarm_hist[d] for d in days}
        }

# Add total
city_data['__total__'] = {
    'barrage': {d: barrage_histograms_all[d] for d in days},
    'alarm': {d: alarm_histograms_all[d] for d in days}
}

print(f"Cities with data: {len(city_data) - 1}")

# Print Tel Aviv statistics
tel_aviv_barrage, tel_aviv_alarm = calculate_histograms('תל אביב')
print("\n=== Tel Aviv Barrage Histogram by Hour ===")
for i, day in enumerate(days):
    total = sum(tel_aviv_barrage[day])
    print(f"\n{day_names[i]}: {total} barrages")
    for hour in range(24):
        count = tel_aviv_barrage[day][hour]
        if count > 0:
            bar = '#' * count
            print(f"  {hour:02d}:00 - {count:2d} {bar}")

# More distinct color palette
colors = ['#e74c3c', '#3498db', '#f39c12', '#9b59b6']  # Red, Blue, Orange, Purple

# Generate HTML
html_content = '''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Missile Alarms Analysis - War 2026 | ניתוח התרעות טילים - מלחמה 2026</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/jquery@3.6.0/dist/jquery.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
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
            margin-bottom: 5px;
            font-size: 2.2em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        .title-en {
            text-align: center;
            font-size: 1.4em;
            color: #aaa;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            margin-bottom: 20px;
            color: #888;
            font-size: 1em;
        }
        .controls {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 20px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .city-selector {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .city-selector label {
            font-size: 1.1em;
        }
        .select2-container {
            min-width: 300px;
        }
        .select2-container--default .select2-selection--single {
            background-color: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 8px;
            height: 42px;
            padding: 6px;
        }
        .select2-container--default .select2-selection--single .select2-selection__rendered {
            color: #fff;
            line-height: 28px;
        }
        .select2-container--default .select2-selection--single .select2-selection__arrow {
            height: 40px;
        }
        .select2-dropdown {
            background-color: #1a1a2e;
            border: 1px solid rgba(255,255,255,0.3);
        }
        .select2-search--dropdown .select2-search__field {
            background-color: rgba(255,255,255,0.1);
            color: #fff;
            border: 1px solid rgba(255,255,255,0.3);
        }
        .select2-results__option {
            color: #fff;
        }
        .select2-container--default .select2-results__option--highlighted[aria-selected] {
            background-color: #e74c3c;
        }
        .view-toggle {
            display: flex;
            justify-content: center;
            gap: 10px;
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
            background: #e74c3c;
            border-color: #e74c3c;
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
        .stats-table-container {
            margin-bottom: 25px;
            overflow-x: auto;
        }
        .stats-table {
            width: 100%;
            border-collapse: collapse;
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            overflow: hidden;
        }
        .stats-table th,
        .stats-table td {
            padding: 12px 20px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .stats-table th {
            background: rgba(255,255,255,0.1);
            font-weight: bold;
            color: #fff;
        }
        .stats-table td {
            font-size: 1.4em;
            font-weight: bold;
        }
        .stats-table tr:last-child td {
            border-bottom: none;
            background: rgba(255,255,255,0.05);
        }
        .stats-table .day-label {
            font-weight: normal;
            font-size: 0.9em;
            color: #aaa;
        }
        .stats-table .color-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 3px;
            margin-left: 8px;
            vertical-align: middle;
        }
        .chart-container {
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .chart-title {
            text-align: center;
            margin-bottom: 15px;
            font-size: 1.3em;
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
            color: #f39c12;
        }
        .change-indicator {
            text-align: center;
            padding: 10px;
            margin-top: 10px;
            border-radius: 8px;
            font-size: 0.9em;
        }
        .change-up {
            background: rgba(231, 76, 60, 0.2);
            color: #e74c3c;
        }
        .change-down {
            background: rgba(46, 213, 115, 0.2);
            color: #2ed573;
        }
        .legend {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
        }
        .legend-color {
            width: 18px;
            height: 18px;
            border-radius: 4px;
        }
        footer {
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 0.85em;
        }
        .section-title {
            text-align: center;
            font-size: 1.5em;
            margin: 30px 0 15px 0;
            color: #f39c12;
        }
        .current-city {
            text-align: center;
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #3498db;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>התרעות טילים</h1>
        <div class="title-en">Missile Alarms Analysis</div>
        <p class="subtitle">מלחמה 2026 | War Period: February 28 - March 2, 2026</p>

        <div class="controls">
            <div class="city-selector">
                <label>עיר / City:</label>
                <select id="citySelect">
                    <option value="__total__">הכל / Total</option>
'''

# Add city options sorted alphabetically
for city in sorted(city_data.keys()):
    if city != '__total__':
        html_content += f'                    <option value="{city}">{city}</option>\n'

html_content += '''                </select>
            </div>
            <div class="view-toggle">
                <button class="view-btn active" onclick="showView('barrages')">מטחים / Barrages</button>
                <button class="view-btn" onclick="showView('alarms')">התרעות / Alarms</button>
            </div>
        </div>

        <div class="current-city" id="currentCityDisplay">הכל / Total</div>

        <!-- BARRAGES VIEW -->
        <div id="barrages-view" class="view-section active">
            <div class="stats-table-container" id="barrageStats"></div>

            <div class="chart-container">
                <h2 class="chart-title">התפלגות שעתית - כל הימים (מוערם) | Hourly Distribution - All Days (Stacked)</h2>
                <div class="chart-wrapper">
                    <canvas id="barrageCombinedChart"></canvas>
                </div>
                <div class="legend" id="barrageLegend"></div>
            </div>

            <h2 class="section-title">פירוט יומי | Daily Breakdown</h2>
            <div id="barrageDayCharts"></div>
        </div>

        <!-- ALARMS VIEW -->
        <div id="alarms-view" class="view-section">
            <div class="stats-table-container" id="alarmStats"></div>

            <div class="chart-container">
                <h2 class="chart-title">התפלגות שעתית - כל הימים (מוערם) | Hourly Distribution - All Days (Stacked)</h2>
                <div class="chart-wrapper">
                    <canvas id="alarmCombinedChart"></canvas>
                </div>
                <div class="legend" id="alarmLegend"></div>
            </div>

            <h2 class="section-title">פירוט יומי | Daily Breakdown</h2>
            <div id="alarmDayCharts"></div>
        </div>
    </div>

    <footer>
        <p>מקור: פיקוד העורף | Data source: Israeli Home Front Command | נוצר ב-3 במרץ 2026</p>
    </footer>

    <script>
        const hours = ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00',
                       '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00',
                       '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'];

        const colors = ''' + str(colors) + ''';
        const days = ''' + str(days) + ''';
        const dayNames = ''' + str(day_names) + ''';
        const dayNamesHe = ''' + str(day_names_he) + ''';

        const cityData = ''' + json.dumps(city_data, ensure_ascii=False) + ''';

        let barrageCombinedChart = null;
        let alarmCombinedChart = null;
        let barrageDayCharts = [];
        let alarmDayCharts = [];

        // Initialize Select2
        $(document).ready(function() {
            $('#citySelect').select2({
                placeholder: 'בחר עיר / Select city',
                allowClear: false,
                width: '300px'
            });

            $('#citySelect').on('change', function() {
                updateCharts(this.value);
            });

            // Initial render
            initCharts();
            updateCharts('__total__');
        });

        function showView(view) {
            document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(view + '-view').classList.add('active');
            event.target.classList.add('active');
        }

        function initCharts() {
            // Create legend
            const legendHtml = days.map((day, i) =>
                `<div class="legend-item"><div class="legend-color" style="background:${colors[i]}"></div>${dayNamesHe[i]} | ${dayNames[i]}</div>`
            ).join('');
            document.getElementById('barrageLegend').innerHTML = legendHtml;
            document.getElementById('alarmLegend').innerHTML = legendHtml;

            // Create day chart containers
            let barrageDayHtml = '';
            let alarmDayHtml = '';
            days.forEach((day, i) => {
                barrageDayHtml += `
                    <div class="day-chart">
                        <h3>${dayNamesHe[i]} | ${dayNames[i]}</h3>
                        <div class="day-chart-wrapper">
                            <canvas id="barrageChart${i}"></canvas>
                        </div>
                        <div class="change-indicator" id="barrageChange${i}"></div>
                    </div>`;
                alarmDayHtml += `
                    <div class="day-chart">
                        <h3>${dayNamesHe[i]} | ${dayNames[i]}</h3>
                        <div class="day-chart-wrapper">
                            <canvas id="alarmChart${i}"></canvas>
                        </div>
                        <div class="change-indicator" id="alarmChange${i}"></div>
                    </div>`;
            });
            document.getElementById('barrageDayCharts').innerHTML = barrageDayHtml;
            document.getElementById('alarmDayCharts').innerHTML = alarmDayHtml;

            // Initialize combined charts
            barrageCombinedChart = createCombinedChart('barrageCombinedChart');
            alarmCombinedChart = createCombinedChart('alarmCombinedChart');

            // Initialize day charts
            days.forEach((day, i) => {
                barrageDayCharts.push(createDayChart('barrageChart' + i, i));
                alarmDayCharts.push(createDayChart('alarmChart' + i, i));
            });
        }

        function createCombinedChart(canvasId) {
            const ctx = document.getElementById(canvasId).getContext('2d');
            return new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: hours,
                    datasets: days.map((day, i) => ({
                        label: dayNames[i],
                        data: new Array(24).fill(0),
                        backgroundColor: colors[i],
                        borderColor: colors[i],
                        borderWidth: 1
                    }))
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
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

        function createDayChart(canvasId, colorIndex) {
            const ctx = document.getElementById(canvasId).getContext('2d');
            return new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: hours,
                    datasets: [{
                        label: 'Count',
                        data: new Array(24).fill(0),
                        backgroundColor: colors[colorIndex],
                        borderColor: colors[colorIndex],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
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

        function updateCharts(city) {
            const data = cityData[city] || cityData['__total__'];
            const displayName = city === '__total__' ? 'הכל / Total' : city;
            document.getElementById('currentCityDisplay').textContent = displayName;

            // Update barrage charts
            updateChartData(barrageCombinedChart, data.barrage);
            days.forEach((day, i) => {
                barrageDayCharts[i].data.datasets[0].data = data.barrage[day];
                barrageDayCharts[i].update();
            });

            // Update alarm charts
            updateChartData(alarmCombinedChart, data.alarm);
            days.forEach((day, i) => {
                alarmDayCharts[i].data.datasets[0].data = data.alarm[day];
                alarmDayCharts[i].update();
            });

            // Update stats
            updateStats('barrage', data.barrage, 'מטחים', 'Barrages');
            updateStats('alarm', data.alarm, 'התרעות', 'Alarms');

            // Update change indicators
            updateChangeIndicators('barrage', data.barrage, 'מטחים', 'barrages');
            updateChangeIndicators('alarm', data.alarm, 'התרעות', 'alarms');
        }

        function updateChartData(chart, data) {
            days.forEach((day, i) => {
                chart.data.datasets[i].data = data[day];
            });
            chart.update();
        }

        function updateStats(type, data, labelHe, labelEn) {
            let total = 0;
            let rows = '';
            days.forEach((day, i) => {
                const sum = data[day].reduce((a, b) => a + b, 0);
                total += sum;
                rows += `
                    <tr>
                        <td><span class="color-indicator" style="background: ${colors[i]}"></span> ${dayNamesHe[i]}</td>
                        <td class="day-label">${dayNames[i]}</td>
                        <td style="color: ${colors[i]}">${sum}</td>
                    </tr>`;
            });
            rows += `
                <tr>
                    <td><strong>סה"כ</strong></td>
                    <td class="day-label"><strong>Total</strong></td>
                    <td style="color: #ffa502"><strong>${total}</strong></td>
                </tr>`;

            const html = `
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>יום</th>
                            <th>Day</th>
                            <th>${labelHe} / ${labelEn}</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>`;
            document.getElementById(type + 'Stats').innerHTML = html;
        }

        function updateChangeIndicators(type, data, labelHe, labelEn) {
            days.forEach((day, i) => {
                const elem = document.getElementById(type + 'Change' + i);
                if (i === 0) {
                    elem.style.display = 'none';
                    return;
                }
                const prev = data[days[i-1]].reduce((a, b) => a + b, 0);
                const curr = data[day].reduce((a, b) => a + b, 0);
                if (prev === 0) {
                    elem.style.display = 'none';
                    return;
                }
                const change = curr - prev;
                const pct = (change / prev * 100).toFixed(1);
                const arrow = change > 0 ? '↑' : '↓';
                const cls = change > 0 ? 'change-up' : 'change-down';
                elem.className = 'change-indicator ' + cls;
                elem.style.display = 'block';
                elem.innerHTML = `${arrow} ${Math.abs(change)} ${labelHe} (${pct > 0 ? '+' : ''}${pct}%) מהיום הקודם | ${arrow} ${Math.abs(change)} ${labelEn} from previous day`;
            });
        }
    </script>
</body>
</html>
'''

# Write HTML file
with open('tel_aviv_alarms.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("\n✓ HTML file generated: tel_aviv_alarms.html")
