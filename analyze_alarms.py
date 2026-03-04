#!/usr/bin/env python3
"""
Analyze missile alarm data from the war starting 2026-02-28
Creates HTML visualization of hourly histogram for alarms with filters
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
            alarm['origin'] = alarm.get('origin', '') or ''
            war_alarms.append(alarm)
    except:
        continue

print(f"Total alarms during war period: {len(war_alarms)}")

# Get all unique locations
all_locations = sorted(set(a['cities'] for a in war_alarms))
print(f"Unique locations: {len(all_locations)}")

# Get all unique origins
all_origins = sorted(set(a['origin'] for a in war_alarms if a['origin']))
print(f"Unique origins: {all_origins}")

import re

def extract_main_city(location):
    """Extract the main city name from a location string."""
    original = location

    # Remove quotes if present
    location = location.strip('"').strip()

    # Skip "אזור תעשייה" locations - extract city name if possible
    if location.startswith('אזור תעשייה'):
        rest = location.replace('אזור תעשייה', '').strip()
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

# Define area mappings - cities that belong to each area
# A city can belong to multiple areas (overlapping)
area_definitions = {
    'מישור החוף': [
        'תל אביב', 'חולון', 'בת ים', 'ראשון לציון', 'חיפה', 'הרצליה', 'רעננה', 'כפר סבא',
        'נתניה', 'חדרה', 'פתח תקווה', 'רמת גן', 'גבעתיים', 'בני ברק', 'רמת השרון',
        'הוד השרון', 'כפר יונה', 'אור יהודה', 'יהוד', 'אזור', 'קריית אונו', 'גבעת שמואל',
        'נס ציונה', 'רחובות', 'יבנה', 'אשדוד', 'אשקלון', 'עכו', 'נהריה', 'קריית ים',
        'קריית מוצקין', 'קריית ביאליק', 'קריית אתא', 'טירת כרמל', 'עתלית', 'זכרון יעקב',
        'בנימינה', 'פרדס חנה', 'אור עקיבא', 'קיסריה', 'גן יבנה', 'קריית מלאכי',
    ],
    'גוש דן': [
        'תל אביב', 'חולון', 'בת ים', 'ראשון לציון', 'הרצליה', 'רעננה', 'פתח תקווה',
        'רמת גן', 'גבעתיים', 'בני ברק', 'רמת השרון', 'אור יהודה', 'יהוד', 'אזור',
        'קריית אונו', 'גבעת שמואל', 'כפר סבא', 'הוד השרון', 'לוד', 'רמלה',
    ],
    'השפלה': [
        'רחובות', 'נס ציונה', 'גדרה', 'יבנה', 'אשדוד', 'אשקלון', 'קריית גת', 'קריית מלאכי',
        'בית שמש', 'גן יבנה', 'באר טוביה', 'שדרות', 'נתיבות', 'אופקים',
    ],
    'הרי יהודה': [
        'ירושלים', 'בית שמש', 'מעלה אדומים', 'גוש עציון', 'אפרת', 'ביתר עילית',
        'מבשרת ציון', 'מודיעין', 'מודיעין עילית',
    ],
    'אזור ירושלים': [
        'ירושלים', 'בית שמש', 'מעלה אדומים', 'מבשרת ציון', 'מודיעין', 'מודיעין עילית',
        'גוש עציון', 'אפרת', 'ביתר עילית', 'מעלה אפרים', 'אבו גוש',
    ],
    'הרי שומרון': [
        'אריאל', 'קדומים', 'ברקן', 'קרני שומרון', 'אלקנה', 'עמנואל',
    ],
    'הגליל': [
        'צפת', 'כרמיאל', 'נהריה', 'עכו', 'מעלות', 'שלומי', 'ראש פינה', 'חצור הגלילית',
        'קריית שמונה', 'מטולה', 'יסוד המעלה', 'עמיעד', 'ראש הנקרה', 'נהריה',
        'מגדל העמק', 'יוקנעם', 'נצרת', 'נצרת עילית', 'נוף הגליל', 'טבריה',
    ],
    'עמק החולה': [
        'קריית שמונה', 'מטולה', 'יסוד המעלה', 'ראש פינה', 'חצור הגלילית',
        'כפר גלעדי', 'דן', 'שניר', 'מנרה',
    ],
    'רמת הגולן': [
        'קצרין', 'רמת מגשימים', 'אל רום', 'נווה אטי"ב', 'מג\'דל שמס', 'מסעדה', 'בוקעאתא',
        'עין זיוון', 'אניעם', 'מרום גולן', 'אורטל', 'נמרוד', 'בניאס',
    ],
    'עמק יזרעאל': [
        'עפולה', 'מגדל העמק', 'יוקנעם', 'נצרת', 'נצרת עילית', 'נוף הגליל',
        'בית שאן', 'בית שערים', 'נהלל', 'כפר תבור',
    ],
    'עמק בית שאן': [
        'בית שאן', 'מעוז חיים', 'נווה אור', 'רשפים', 'שדה נחום', 'טירת צבי',
    ],
    'בקעת הירדן': [
        'בית שאן', 'מחולה', 'חמדת', 'מכורה', 'משואה', 'פצאל', 'ארגמן', 'יפית',
        'נערן', 'גלגל', 'יריחו',
    ],
    'הנגב': [
        'באר שבע', 'דימונה', 'ערד', 'ירוחם', 'מצפה רמון', 'שדה בוקר',
        'אופקים', 'נתיבות', 'שדרות', 'קריית גת', 'רהט', 'תל שבע', 'לקיה', 'כסייפה',
    ],
    'עוטף עזה': [
        'שדרות', 'נתיבות', 'אופקים', 'אשקלון', 'קריית גת', 'קריית מלאכי',
        'ניר עם', 'כיסופים', 'נחל עוז', 'כפר עזה', 'בארי', 'רעים', 'עין השלושה',
        'ניר עוז', 'מגן', 'ארז', 'יבול', 'נירים', 'עין הבשור', 'תקומה',
    ],
    'הערבה': [
        'אילת', 'יטבתה', 'באר אורה', 'גרופית', 'פארן', 'נאות סמדר', 'קטורה',
        'לוטן', 'עידן', 'ספיר', 'עין חצבה', 'עין יהב', 'צופר',
    ],
    'חיפה והקריות': [
        'חיפה', 'קריית ים', 'קריית מוצקין', 'קריית ביאליק', 'קריית אתא',
        'טירת כרמל', 'נשר', 'קריית חיים', 'קריית שמואל',
    ],
}

# Create reverse mapping: city -> list of areas
city_to_areas = defaultdict(list)
for area, cities in area_definitions.items():
    for city in cities:
        city_to_areas[city].append(area)

# Also map by pattern matching for cities not explicitly listed
def get_city_areas(city_name):
    """Get areas for a city, including pattern matching."""
    areas = city_to_areas.get(city_name, [])

    # Pattern matching for common prefixes
    if not areas:
        # Check if it starts with a known area indicator
        if any(x in city_name for x in ['קיבוץ', 'מושב', 'ישוב']):
            # Try to infer from nearby cities or leave unmapped
            pass

    return areas if areas else ['אחר']  # 'Other' for unmapped cities

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

# Build compact alarm data for frontend
# Format: {timestamp_second: {cities: [city_indices], origin: origin_index}}
city_list = sorted(main_cities)
city_to_idx = {c: i for i, c in enumerate(city_list)}
origin_list = [''] + sorted(all_origins)  # Empty string first for "unknown"
origin_to_idx = {o: i for i, o in enumerate(origin_list)}

# Group alarms by exact second
alarms_by_second = defaultdict(lambda: {'cities': set(), 'origin': ''})
for alarm in war_alarms:
    second_key = alarm['datetime'].strftime('%Y-%m-%d %H:%M:%S')
    main_city = extract_main_city(alarm['cities'])
    if main_city in city_to_idx:
        alarms_by_second[second_key]['cities'].add(city_to_idx[main_city])
    # Keep first non-empty origin for this second
    if not alarms_by_second[second_key]['origin'] and alarm['origin']:
        alarms_by_second[second_key]['origin'] = alarm['origin']

# Convert to list format for JSON
compact_alarms = []
for second_key, data in sorted(alarms_by_second.items()):
    compact_alarms.append({
        't': second_key,
        'c': sorted(data['cities']),
        'o': origin_to_idx.get(data['origin'], 0)
    })

print(f"Unique alarm seconds: {len(compact_alarms)}")

# Build area data for frontend
area_list = sorted(area_definitions.keys())
area_to_cities_idx = {}
for area in area_list:
    city_indices = []
    for city in area_definitions[area]:
        if city in city_to_idx:
            city_indices.append(city_to_idx[city])
    area_to_cities_idx[area] = sorted(set(city_indices))

# Remove trailing days with no data
days = all_days[:]
day_names = all_day_names[:]
day_names_he = all_day_names_he[:]

print(f"Days with data: {len(days)}")

# Print Tel Aviv statistics for verification
tel_aviv_idx = city_to_idx.get('תל אביב', -1)
tel_aviv_count = sum(1 for a in compact_alarms if tel_aviv_idx in a['c'])
print(f"\nTel Aviv alarm count: {tel_aviv_count}")

# More distinct color palette (extended for more days)
colors = ['#e74c3c', '#3498db', '#f39c12', '#9b59b6', '#2ecc71', '#1abc9c', '#e67e22', '#34495e']

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
        .filter-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .filter-group label {
            font-size: 1em;
            white-space: nowrap;
        }
        .select2-container {
            min-width: 200px;
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
        footer a {
            color: #3498db;
        }
        .section-title {
            text-align: center;
            font-size: 1.5em;
            margin: 30px 0 15px 0;
            color: #f39c12;
        }
        .current-filter {
            text-align: center;
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #3498db;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>התרעות טילים</h1>
        <div class="title-en">Missile Alarms Analysis</div>
        <p class="subtitle">מלחמה 2026 | War 2026</p>

        <div class="controls">
            <div class="filter-group">
                <label>מקור / Origin:</label>
                <select id="originSelect">
                    <option value="__all__">הכל / All</option>
'''

# Add origin options
for origin in all_origins:
    html_content += f'                    <option value="{origin}">{origin}</option>\n'

html_content += '''                </select>
            </div>
            <div class="filter-group">
                <label>אזור / Area:</label>
                <select id="areaSelect">
                    <option value="__all__">הכל / All</option>
'''

# Add area options
for area in area_list:
    html_content += f'                    <option value="{area}">{area}</option>\n'

html_content += '''                </select>
            </div>
            <div class="filter-group">
                <label>עיר / City:</label>
                <select id="citySelect">
                    <option value="__all__">הכל / All</option>
'''

# Add city options sorted alphabetically
for city in city_list:
    html_content += f'                    <option value="{city}">{city}</option>\n'

html_content += '''                </select>
            </div>
        </div>

        <div class="current-filter" id="currentFilterDisplay">הכל / All</div>

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

        const colors = ''' + json.dumps(colors) + ''';
        const days = ''' + json.dumps(days) + ''';
        const dayNames = ''' + json.dumps(day_names) + ''';
        const dayNamesHe = ''' + json.dumps(day_names_he) + ''';

        // City and origin mappings
        const cityList = ''' + json.dumps(city_list, ensure_ascii=False) + ''';
        const originList = ''' + json.dumps(origin_list, ensure_ascii=False) + ''';

        // Area to city indices mapping
        const areaToCities = ''' + json.dumps(area_to_cities_idx, ensure_ascii=False) + ''';

        // Compact alarm data: [{t: timestamp, c: [city_indices], o: origin_index}]
        const alarmData = ''' + json.dumps(compact_alarms, ensure_ascii=False) + ''';

        let alarmCombinedChart = null;
        let alarmDayCharts = [];

        // Compute histogram based on current filters
        function computeHistogram(originFilter, areaFilter, cityFilter) {
            // Determine which city indices to include
            let allowedCities = null;  // null means all

            if (cityFilter !== '__all__') {
                // Specific city selected
                const cityIdx = cityList.indexOf(cityFilter);
                if (cityIdx >= 0) {
                    allowedCities = new Set([cityIdx]);
                }
            } else if (areaFilter !== '__all__') {
                // Area selected, get all cities in that area
                const areaCities = areaToCities[areaFilter];
                if (areaCities) {
                    allowedCities = new Set(areaCities);
                }
            }

            // Determine origin filter
            let allowedOrigin = null;  // null means all
            if (originFilter !== '__all__') {
                allowedOrigin = originList.indexOf(originFilter);
            }

            // Initialize histogram
            const histogram = {};
            days.forEach(day => {
                histogram[day] = new Array(24).fill(0);
            });

            // Process alarms
            alarmData.forEach(alarm => {
                // Check origin filter
                if (allowedOrigin !== null && alarm.o !== allowedOrigin) {
                    return;
                }

                // Check city filter
                if (allowedCities !== null) {
                    const hasMatchingCity = alarm.c.some(c => allowedCities.has(c));
                    if (!hasMatchingCity) {
                        return;
                    }
                }

                // Extract day and hour from timestamp
                const dayStr = alarm.t.substring(0, 10);
                const hour = parseInt(alarm.t.substring(11, 13), 10);

                if (histogram[dayStr]) {
                    histogram[dayStr][hour]++;
                }
            });

            return histogram;
        }

        // URL parameter handling
        function getUrlParam(param) {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(param);
        }

        function setUrlParams(params) {
            const url = new URL(window.location);
            Object.entries(params).forEach(([key, value]) => {
                if (value && value !== '__all__') {
                    url.searchParams.set(key, value);
                } else {
                    url.searchParams.delete(key);
                }
            });
            window.history.replaceState({}, '', url);
        }

        // Initialize Select2
        $(document).ready(function() {
            $('#originSelect, #areaSelect, #citySelect').select2({
                allowClear: false,
                width: '200px'
            });

            // When area changes, update city dropdown
            $('#areaSelect').on('change', function() {
                const area = this.value;
                updateCityOptions(area);
                updateFromFilters();
            });

            $('#originSelect, #citySelect').on('change', function() {
                updateFromFilters();
            });

            // Initial render
            initCharts();

            // Check URL for parameters
            const urlOrigin = getUrlParam('origin') || '__all__';
            const urlArea = getUrlParam('area') || '__all__';
            const urlCity = getUrlParam('city') || '__all__';

            $('#originSelect').val(urlOrigin).trigger('change.select2');
            $('#areaSelect').val(urlArea).trigger('change.select2');
            updateCityOptions(urlArea);
            $('#citySelect').val(urlCity).trigger('change.select2');

            updateFromFilters();
        });

        function updateCityOptions(area) {
            const citySelect = $('#citySelect');
            const currentCity = citySelect.val();

            // Clear and rebuild options
            citySelect.empty();
            citySelect.append('<option value="__all__">הכל / All</option>');

            if (area === '__all__') {
                // Show all cities
                cityList.forEach(city => {
                    citySelect.append(`<option value="${city}">${city}</option>`);
                });
            } else {
                // Show only cities in selected area
                const areaCityIndices = areaToCities[area] || [];
                areaCityIndices.forEach(idx => {
                    const city = cityList[idx];
                    citySelect.append(`<option value="${city}">${city}</option>`);
                });
            }

            // Try to keep current selection if still valid
            if (citySelect.find(`option[value="${currentCity}"]`).length > 0) {
                citySelect.val(currentCity);
            } else {
                citySelect.val('__all__');
            }
            citySelect.trigger('change.select2');
        }

        function updateFromFilters() {
            const origin = $('#originSelect').val();
            const area = $('#areaSelect').val();
            const city = $('#citySelect').val();

            setUrlParams({origin, area, city});

            const histogram = computeHistogram(origin, area, city);
            updateCharts(histogram, origin, area, city);
        }

        function initCharts() {
            // Create legend
            const legendHtml = days.map((day, i) =>
                `<div class="legend-item"><div class="legend-color" style="background:${colors[i % colors.length]}"></div>${dayNamesHe[i]} | ${dayNames[i]}</div>`
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
                        backgroundColor: colors[i % colors.length],
                        borderColor: colors[i % colors.length],
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
                        backgroundColor: colors[colorIndex % colors.length],
                        borderColor: colors[colorIndex % colors.length],
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

        function updateCharts(histogram, origin, area, city) {
            // Build display name
            let displayParts = [];
            if (origin !== '__all__') displayParts.push(origin);
            if (area !== '__all__') displayParts.push(area);
            if (city !== '__all__') displayParts.push(city);
            const displayName = displayParts.length > 0 ? displayParts.join(' | ') : 'הכל / All';
            document.getElementById('currentFilterDisplay').textContent = displayName;

            // Update combined chart
            days.forEach((day, i) => {
                alarmCombinedChart.data.datasets[i].data = histogram[day];
            });
            alarmCombinedChart.update();

            // Update day charts
            days.forEach((day, i) => {
                alarmDayCharts[i].data.datasets[0].data = histogram[day];
                alarmDayCharts[i].update();
            });

            // Update stats
            updateStats(histogram);

            // Update change indicators
            updateChangeIndicators(histogram);
        }

        function updateStats(histogram) {
            let total = 0;
            let rows = '';
            days.forEach((day, i) => {
                const sum = histogram[day].reduce((a, b) => a + b, 0);
                total += sum;
                rows += `
                    <tr>
                        <td><span class="color-indicator" style="background: ${colors[i % colors.length]}"></span> ${dayNamesHe[i]}</td>
                        <td class="day-label">${dayNames[i]}</td>
                        <td style="color: ${colors[i % colors.length]}">${sum}</td>
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
                            <th>התרעות / Alarms</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>`;
            document.getElementById('alarmStats').innerHTML = html;
        }

        function updateChangeIndicators(histogram) {
            days.forEach((day, i) => {
                const elem = document.getElementById('alarmChange' + i);
                if (i === 0) {
                    elem.style.display = 'none';
                    return;
                }
                const prev = histogram[days[i-1]].reduce((a, b) => a + b, 0);
                const curr = histogram[day].reduce((a, b) => a + b, 0);
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
                elem.innerHTML = `${arrow} ${Math.abs(change)} התרעות (${pct > 0 ? '+' : ''}${pct}%) מהיום הקודם | ${arrow} ${Math.abs(change)} alarms from previous day`;
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
