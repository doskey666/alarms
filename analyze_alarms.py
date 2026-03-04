#!/usr/bin/env python3
"""
Analyze missile alarm data from the war starting 2026-02-28
Creates HTML visualization of hourly histogram for Tel Aviv alarms
"""

import csv
import json
import urllib.request
import io
from collections import defaultdict
from datetime import datetime

# Download the CSV file from GitHub
CSV_URL = 'https://raw.githubusercontent.com/yuval-harpaz/alarms/refs/heads/master/data/alarms.csv'
print(f"Downloading alarms data from {CSV_URL}...")

with urllib.request.urlopen(CSV_URL) as response:
    csv_data = response.read().decode('utf-8')

print(f"Downloaded {len(csv_data)} bytes")

# Parse the CSV data
alarms = []
reader = csv.DictReader(io.StringIO(csv_data))
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

# Get all unique locations
all_locations = sorted(set(a['cities'] for a in war_alarms))
print(f"Unique locations: {len(all_locations)}")

import re

def extract_main_city(location):
    """Extract the main city name from a location string."""
    original = location

    # Remove quotes if present
    location = location.strip('"').strip()

    # Skip "אזור תעשייה" locations - extract city name if possible
    if location.startswith('אזור תעשייה'):
        # Try to find a known city in the rest of the string
        rest = location.replace('אזור תעשייה', '').strip()
        # Return the industrial zone as-is for now, or extract city
        return location  # Keep industrial zones separate

    # Handle dash-separated names (e.g., "תל אביב - מרכז העיר")
    if ' - ' in location:
        return location.split(' - ')[0].strip()
    if ' -' in location:
        return location.split(' -')[0].strip()
    if '- ' in location:
        return location.split('- ')[0].strip()

    # Handle direction/area suffixes (without dash)
    suffixes = [
        ' מזרח', ' מערב', ' צפון', ' דרום', ' מרכז',
        ' א', ' ב', ' ג', ' ד', ' ה', ' ו', ' ז', ' ח', ' ט', ' י', ' יא', ' יב',
        ' עילית', ' תחתית',
    ]
    for suffix in suffixes:
        if location.endswith(suffix):
            return location[:-len(suffix)].strip()

    return location

# Group locations by main city
city_to_locations = defaultdict(set)
for loc in all_locations:
    main_city = extract_main_city(loc)
    city_to_locations[main_city].add(loc)

# Get unique main cities
main_cities = sorted(city_to_locations.keys())
print(f"Unique main cities (grouped): {len(main_cities)}")

# Group by day - dynamically from alarm data
all_days = sorted(set(a['datetime'].strftime('%Y-%m-%d') for a in war_alarms))

# Generate day names dynamically
day_name_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_name_he = ['שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת', 'ראשון']
month_name_en = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
month_name_he = ['', 'בינואר', 'בפברואר', 'במרץ', 'באפריל', 'במאי', 'ביוני', 'ביולי', 'באוגוסט', 'בספטמבר', 'באוקטובר', 'בנובמבר', 'בדצמבר']

all_day_names = []
all_day_names_he = []
for day_str in all_days:
    dt = datetime.strptime(day_str, '%Y-%m-%d')
    weekday = dt.weekday()  # 0=Monday, 6=Sunday
    day_num = dt.day
    month_num = dt.month
    all_day_names.append(f"{day_name_en[weekday]} ({month_name_en[month_num]} {day_num})")
    all_day_names_he.append(f"{day_name_he[weekday]} ({day_num} {month_name_he[month_num]})")

def calculate_histograms(locations_filter=None):
    """Calculate histogram for specific locations or all locations"""
    if locations_filter:
        filtered_alarms = [a for a in war_alarms if a['cities'] in locations_filter]
    else:
        filtered_alarms = war_alarms

    # Deduplicate alarms by exact second
    unique_seconds = {}
    for alarm in filtered_alarms:
        key = alarm['datetime'].strftime('%Y-%m-%d %H:%M:%S')
        if key not in unique_seconds:
            unique_seconds[key] = alarm['datetime']

    # Calculate histogram per day
    alarm_hist = {}
    for day in all_days:
        alarm_hist[day] = [0] * 24

    for second_key, dt in unique_seconds.items():
        day_str = dt.strftime('%Y-%m-%d')
        hour = dt.hour
        if day_str in alarm_hist:
            alarm_hist[day_str][hour] += 1

    return alarm_hist

# Calculate histograms for all cities (for determining which days to show)
alarm_histograms_all = calculate_histograms()

# Remove trailing days with no data
days = all_days[:]
day_names = all_day_names[:]
day_names_he = all_day_names_he[:]
while days and sum(alarm_histograms_all[days[-1]]) == 0:
    days.pop()
    day_names.pop()
    day_names_he.pop()

print(f"Days with data: {len(days)}")

# Pre-calculate histograms for all grouped cities
city_data = {}
for main_city in main_cities:
    locations = city_to_locations[main_city]
    alarm_hist = calculate_histograms(locations)
    # Only include cities that have data in the active days
    has_data = any(sum(alarm_hist[d]) > 0 for d in days)
    if has_data:
        city_data[main_city] = {
            'alarm': {d: alarm_hist[d] for d in days}
        }

# Add total
city_data['__total__'] = {
    'alarm': {d: alarm_histograms_all[d] for d in days}
}

print(f"Grouped cities with data: {len(city_data) - 1}")

# Print Tel Aviv statistics
tel_aviv_locations = city_to_locations.get('תל אביב', set())
tel_aviv_alarm = calculate_histograms(tel_aviv_locations)
print("\n=== Tel Aviv Alarm Histogram by Hour ===")
for i, day in enumerate(days):
    total = sum(tel_aviv_alarm[day])
    print(f"\n{day_names[i]}: {total} alarms")
    for hour in range(24):
        count = tel_aviv_alarm[day][hour]
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
        </div>

        <div class="current-city" id="currentCityDisplay">הכל / Total</div>

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

    <footer>
        <p>מקור: פיקוד העורף | Data source: Israeli Home Front Command</p>
        <p>Data provided by <a href="https://github.com/yuval-harpaz/alarms" target="_blank">yuval-harpaz/alarms</a></p>
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

        let alarmCombinedChart = null;
        let alarmDayCharts = [];

        // URL parameter handling
        function getUrlParam(param) {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(param);
        }

        function setUrlParam(param, value) {
            const url = new URL(window.location);
            if (value && value !== '__total__') {
                url.searchParams.set(param, value);
            } else {
                url.searchParams.delete(param);
            }
            window.history.replaceState({}, '', url);
        }

        // Initialize Select2
        $(document).ready(function() {
            $('#citySelect').select2({
                placeholder: 'בחר עיר / Select city',
                allowClear: false,
                width: '300px'
            });

            $('#citySelect').on('change', function() {
                const city = this.value;
                setUrlParam('city', city);
                updateCharts(city);
            });

            // Initial render
            initCharts();

            // Check URL for city parameter
            const urlCity = getUrlParam('city');
            if (urlCity && cityData[urlCity]) {
                $('#citySelect').val(urlCity).trigger('change.select2');
                updateCharts(urlCity);
            } else {
                updateCharts('__total__');
            }
        });

        function initCharts() {
            // Create legend
            const legendHtml = days.map((day, i) =>
                `<div class="legend-item"><div class="legend-color" style="background:${colors[i]}"></div>${dayNamesHe[i]} | ${dayNames[i]}</div>`
            ).join('');
            document.getElementById('alarmLegend').innerHTML = legendHtml;

            // Create day chart containers
            let alarmDayHtml = '';
            days.forEach((day, i) => {
                alarmDayHtml += `
                    <div class="day-chart">
                        <h3>${dayNamesHe[i]} | ${dayNames[i]}</h3>
                        <div class="day-chart-wrapper">
                            <canvas id="alarmChart${i}"></canvas>
                        </div>
                        <div class="change-indicator" id="alarmChange${i}"></div>
                    </div>`;
            });
            document.getElementById('alarmDayCharts').innerHTML = alarmDayHtml;

            // Initialize combined chart
            alarmCombinedChart = createCombinedChart('alarmCombinedChart');

            // Initialize day charts
            days.forEach((day, i) => {
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

            // Update alarm charts
            updateChartData(alarmCombinedChart, data.alarm);
            days.forEach((day, i) => {
                alarmDayCharts[i].data.datasets[0].data = data.alarm[day];
                alarmDayCharts[i].update();
            });

            // Update stats
            updateStats('alarm', data.alarm, 'התרעות', 'Alarms');

            // Update change indicators
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
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("\n✓ HTML file generated: index.html")
