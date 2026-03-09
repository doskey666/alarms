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
day_name_en = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
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
    <title id="pageTitle">ניתוח התרעות טילים - מבצע שאגת האריה</title>
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
        .header {
            position: relative;
            margin-bottom: 20px;
        }
        h1 {
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.2em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        .subtitle {
            text-align: center;
            margin-bottom: 20px;
            color: #888;
            font-size: 1em;
        }
        .lang-toggle {
            position: absolute;
            top: 0;
            right: 0;
        }
        .lang-btn {
            padding: 8px 16px;
            border: 1px solid rgba(255,255,255,0.3);
            background: rgba(255,255,255,0.1);
            color: #fff;
            cursor: pointer;
            border-radius: 5px;
            font-size: 0.9em;
            transition: all 0.3s ease;
            min-width: 80px;
        }
        .lang-btn:hover {
            background: rgba(255,255,255,0.2);
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
            width: 200px !important;
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
        .stats-table .color-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 3px;
            margin-left: 8px;
            vertical-align: middle;
        }
        [dir="ltr"] .stats-table .color-indicator {
            margin-left: 0;
            margin-right: 8px;
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
        /* Desktop: table and graphs at 80% width */
        @media (min-width: 768px) {
            .stats-table-container, .chart-container, .day-chart {
                width: 80%;
                margin-left: auto;
                margin-right: auto;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="lang-toggle">
                <button class="lang-btn" id="langToggleBtn">English</button>
            </div>
            <h1 id="mainTitle">התרעות טילים</h1>
            <p class="subtitle" id="subtitleText">מבצע שאגת האריה</p>
        </div>

        <div class="controls">
            <div class="filter-group">
                <label id="labelOrigin">מקור:</label>
                <select id="originSelect">
                    <option value="__all__" data-he="הכל" data-en="All">הכל</option>
'''

# Add origin options
for origin in all_origins:
    html_content += f'                    <option value="{origin}">{origin}</option>\n'

html_content += '''                </select>
            </div>
            <div class="filter-group">
                <label id="labelArea">אזור:</label>
                <select id="areaSelect">
                    <option value="__all__" data-he="הכל" data-en="All">הכל</option>
'''

# Add area options
for area in area_list:
    html_content += f'                    <option value="{area}">{area}</option>\n'

html_content += '''                </select>
            </div>
            <div class="filter-group">
                <label id="labelCity">עיר:</label>
                <select id="citySelect">
                    <option value="__all__" data-he="הכל" data-en="All">הכל</option>
'''

# Add city options sorted alphabetically
for city in city_list:
    html_content += f'                    <option value="{city}">{city}</option>\n'

html_content += '''                </select>
            </div>
        </div>

        <div class="current-filter" id="currentFilterDisplay">הכל</div>

        <div class="stats-table-container" id="alarmStats"></div>

        <div class="chart-container">
            <h2 class="chart-title" id="chartTitle">התפלגות שעתית - כל הימים</h2>
            <div class="chart-wrapper">
                <canvas id="alarmCombinedChart"></canvas>
            </div>
            <div class="legend" id="alarmLegend"></div>
        </div>

        <div class="chart-container">
            <h2 class="chart-title" id="chartTitleLast3">התפלגות שעתית - 3 ימים אחרונים</h2>
            <div class="chart-wrapper">
                <canvas id="alarmLast3Chart"></canvas>
            </div>
        </div>

        <h2 class="section-title" id="dailyBreakdownTitle">פירוט יומי</h2>
        <div id="alarmDayCharts"></div>
    </div>

    <footer>
        <p id="footerSource">מקור: פיקוד העורף</p>
        <p id="footerData">מידע מסופק על ידי <a href="https://github.com/yuval-harpaz/alarms" target="_blank">yuval-harpaz/alarms</a></p>
    </footer>

    <script>
        const hours = ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00',
                       '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00',
                       '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'];

        const colors = ''' + json.dumps(colors) + ''';
        const days = ''' + json.dumps(days) + ''';
        const dayNames = ''' + json.dumps(day_names) + ''';
        const dayNamesHe = ''' + json.dumps(day_names_he) + ''';

        // Translations
        const translations = {
            he: {
                pageTitle: 'ניתוח התרעות טילים - מבצע שאגת האריה',
                mainTitle: 'התרעות טילים',
                subtitle: 'מבצע שאגת האריה',
                labelOrigin: 'מקור:',
                labelArea: 'אזור:',
                labelCity: 'עיר:',
                all: 'הכל',
                chartTitle: 'התפלגות שעתית - כל הימים',
                chartTitleLast3: 'התפלגות שעתית - 3 ימים אחרונים',
                dailyBreakdown: 'פירוט יומי',
                day: 'יום',
                alarms: 'התרעות',
                total: 'סה"כ',
                change: 'שינוי',
                footerSource: 'מקור: פיקוד העורף',
                footerData: 'מידע מסופק על ידי',
                fromPrevDay: 'מהיום הקודם',
                origins: {
                    '': 'לא ידוע',
                    'Iran': 'איראן',
                    'Lebanon': 'לבנון',
                    'FA': 'התרעת שווא'
                },
                areas: {
                    'מישור החוף': 'מישור החוף',
                    'גוש דן': 'גוש דן',
                    'השפלה': 'השפלה',
                    'הרי יהודה': 'הרי יהודה',
                    'אזור ירושלים': 'אזור ירושלים',
                    'הרי שומרון': 'הרי שומרון',
                    'הגליל': 'הגליל',
                    'עמק החולה': 'עמק החולה',
                    'רמת הגולן': 'רמת הגולן',
                    'עמק יזרעאל': 'עמק יזרעאל',
                    'עמק בית שאן': 'עמק בית שאן',
                    'בקעת הירדן': 'בקעת הירדן',
                    'הנגב': 'הנגב',
                    'עוטף עזה': 'עוטף עזה',
                    'הערבה': 'הערבה',
                    'חיפה והקריות': 'חיפה והקריות'
                }
            },
            en: {
                pageTitle: "Missile Alarms Analysis - Operation Lion's Roar",
                mainTitle: 'Missile Alarms',
                subtitle: "Operation Lion's Roar",
                labelOrigin: 'Origin:',
                labelArea: 'Area:',
                labelCity: 'City:',
                all: 'All',
                chartTitle: 'Hourly Distribution - All Days',
                chartTitleLast3: 'Hourly Distribution - Last 3 Days',
                dailyBreakdown: 'Daily Breakdown',
                day: 'Day',
                alarms: 'Alarms',
                total: 'Total',
                change: 'Change',
                footerSource: 'Source: Israeli Home Front Command',
                footerData: 'Data provided by',
                fromPrevDay: 'from previous day',
                origins: {
                    '': 'Unknown',
                    'Iran': 'Iran',
                    'Lebanon': 'Lebanon',
                    'FA': 'False Alarm'
                },
                areas: {
                    'מישור החוף': 'Coastal Plain',
                    'גוש דן': 'Gush Dan',
                    'השפלה': 'Shfela',
                    'הרי יהודה': 'Judean Mountains',
                    'אזור ירושלים': 'Jerusalem Area',
                    'הרי שומרון': 'Samarian Mountains',
                    'הגליל': 'Galilee',
                    'עמק החולה': 'Hula Valley',
                    'רמת הגולן': 'Golan Heights',
                    'עמק יזרעאל': 'Jezreel Valley',
                    'עמק בית שאן': 'Beit Shean Valley',
                    'בקעת הירדן': 'Jordan Valley',
                    'הנגב': 'Negev',
                    'עוטף עזה': 'Gaza Envelope',
                    'הערבה': 'Arava',
                    'חיפה והקריות': 'Haifa & Krayot'
                },
                cities: {
                    'תל אביב': 'Tel Aviv', 'חולון': 'Holon', 'בת ים': 'Bat Yam', 'ראשון לציון': 'Rishon LeZion',
                    'חיפה': 'Haifa', 'הרצליה': 'Herzliya', 'רעננה': 'Raanana', 'כפר סבא': 'Kfar Saba',
                    'נתניה': 'Netanya', 'חדרה': 'Hadera', 'פתח תקווה': 'Petah Tikva', 'רמת גן': 'Ramat Gan',
                    'גבעתיים': 'Givatayim', 'בני ברק': 'Bnei Brak', 'רמת השרון': 'Ramat HaSharon',
                    'הוד השרון': 'Hod HaSharon', 'כפר יונה': 'Kfar Yona', 'אור יהודה': 'Or Yehuda',
                    'יהוד': 'Yehud', 'אזור': 'Azor', 'קריית אונו': 'Kiryat Ono', 'גבעת שמואל': 'Givat Shmuel',
                    'נס ציונה': 'Nes Ziona', 'רחובות': 'Rehovot', 'יבנה': 'Yavne', 'אשדוד': 'Ashdod',
                    'אשקלון': 'Ashkelon', 'עכו': 'Acre', 'נהריה': 'Nahariya', 'קריית ים': 'Kiryat Yam',
                    'קריית מוצקין': 'Kiryat Motzkin', 'קריית ביאליק': 'Kiryat Bialik', 'קריית אתא': 'Kiryat Ata',
                    'טירת כרמל': 'Tirat Carmel', 'עתלית': 'Atlit', 'זכרון יעקב': 'Zichron Yaakov',
                    'בנימינה': 'Binyamina', 'פרדס חנה': 'Pardes Hanna', 'אור עקיבא': 'Or Akiva',
                    'קיסריה': 'Caesarea', 'גן יבנה': 'Gan Yavne', 'קריית מלאכי': 'Kiryat Malakhi',
                    'לוד': 'Lod', 'רמלה': 'Ramla', 'גדרה': 'Gedera', 'קריית גת': 'Kiryat Gat',
                    'בית שמש': 'Beit Shemesh', 'באר טוביה': 'Beer Tuvia', 'שדרות': 'Sderot',
                    'נתיבות': 'Netivot', 'אופקים': 'Ofakim', 'ירושלים': 'Jerusalem',
                    'מעלה אדומים': 'Maale Adumim', 'גוש עציון': 'Gush Etzion', 'אפרת': 'Efrat',
                    'ביתר עילית': 'Beitar Illit', 'מבשרת ציון': 'Mevaseret Zion', 'מודיעין': 'Modiin',
                    'מודיעין עילית': 'Modiin Illit', 'מעלה אפרים': 'Maale Efraim', 'אבו גוש': 'Abu Ghosh',
                    'אריאל': 'Ariel', 'קדומים': 'Kedumim', 'ברקן': 'Barkan', 'קרני שומרון': 'Karnei Shomron',
                    'אלקנה': 'Elkana', 'עמנואל': 'Emanuel', 'צפת': 'Safed', 'כרמיאל': 'Karmiel',
                    'מעלות': 'Maalot', 'שלומי': 'Shlomi', 'ראש פינה': 'Rosh Pina', 'חצור הגלילית': 'Hazor HaGlilit',
                    'קריית שמונה': 'Kiryat Shmona', 'מטולה': 'Metula', 'יסוד המעלה': 'Yesod HaMaala',
                    'עמיעד': 'Amiad', 'ראש הנקרה': 'Rosh HaNikra', 'מגדל העמק': 'Migdal HaEmek',
                    'יוקנעם': 'Yokneam', 'נצרת': 'Nazareth', 'נצרת עילית': 'Nazareth Illit',
                    'נוף הגליל': 'Nof HaGalil', 'טבריה': 'Tiberias', 'כפר גלעדי': 'Kfar Giladi',
                    'דן': 'Dan', 'שניר': 'Snir', 'מנרה': 'Manara', 'קצרין': 'Katzrin',
                    'רמת מגשימים': 'Ramat Magshimim', 'אל רום': 'El Rom', 'עין זיוון': 'Ein Zivan',
                    'אניעם': 'Aniam', 'מרום גולן': 'Merom Golan', 'אורטל': 'Ortal', 'נמרוד': 'Nimrod',
                    'בניאס': 'Banias', 'עפולה': 'Afula', 'בית שאן': 'Beit Shean', 'בית שערים': 'Beit Shearim',
                    'נהלל': 'Nahalal', 'כפר תבור': 'Kfar Tavor', 'מעוז חיים': 'Maoz Haim',
                    'נווה אור': 'Neve Ur', 'רשפים': 'Reshafim', 'שדה נחום': 'Sde Nahum', 'טירת צבי': 'Tirat Zvi',
                    'מחולה': 'Mehola', 'חמדת': 'Hamdat', 'מכורה': 'Mekhora', 'משואה': 'Masua',
                    'פצאל': 'Petzael', 'ארגמן': 'Argaman', 'יפית': 'Yafit', 'נערן': 'Naaran',
                    'גלגל': 'Gilgal', 'יריחו': 'Jericho', 'באר שבע': 'Beersheba', 'דימונה': 'Dimona',
                    'ערד': 'Arad', 'ירוחם': 'Yeruham', 'מצפה רמון': 'Mitzpe Ramon', 'שדה בוקר': 'Sde Boker',
                    'רהט': 'Rahat', 'תל שבע': 'Tel Sheva', 'לקיה': 'Lakiya', 'כסייפה': 'Kuseife',
                    'ניר עם': 'Nir Am', 'כיסופים': 'Kissufim', 'נחל עוז': 'Nahal Oz', 'כפר עזה': 'Kfar Aza',
                    'בארי': 'Beeri', 'רעים': 'Reim', 'עין השלושה': 'Ein HaShlosha', 'ניר עוז': 'Nir Oz',
                    'מגן': 'Magen', 'ארז': 'Erez', 'יבול': 'Yevul', 'נירים': 'Nirim',
                    'עין הבשור': 'Ein HaBesor', 'תקומה': 'Tkuma', 'אילת': 'Eilat', 'יטבתה': 'Yotvata',
                    'באר אורה': 'Beer Ora', 'גרופית': 'Grofit', 'פארן': 'Paran', 'נאות סמדר': 'Neot Smadar',
                    'קטורה': 'Ketura', 'לוטן': 'Lotan', 'עידן': 'Idan', 'ספיר': 'Sapir',
                    'עין חצבה': 'Ein Hatzeva', 'עין יהב': 'Ein Yahav', 'צופר': 'Tzofar',
                    'נשר': 'Nesher', 'קריית חיים': 'Kiryat Haim', 'קריית שמואל': 'Kiryat Shmuel'
                }
            }
        };

        let currentLang = localStorage.getItem('lang') || 'he';

        // City and origin mappings
        const cityList = ''' + json.dumps(city_list, ensure_ascii=False) + ''';
        const originList = ''' + json.dumps(origin_list, ensure_ascii=False) + ''';

        // Origin colors
        const originColors = {'': '#95a5a6', 'Iran': '#e74c3c', 'Lebanon': '#27ae60', 'FA': '#3498db'};

        function getOriginName(origin) {
            return translations[currentLang].origins[origin] || origin;
        }

        function getAreaName(area) {
            return translations[currentLang].areas[area] || area;
        }

        function getCityName(city) {
            return (translations[currentLang].cities && translations[currentLang].cities[city]) || city;
        }

        function t(key) {
            return translations[currentLang][key] || key;
        }

        function getDayName(index) {
            return currentLang === 'he' ? dayNamesHe[index] : dayNames[index];
        }

        function setLanguage(lang) {
            currentLang = lang;
            localStorage.setItem('lang', lang);

            // Update document direction
            document.documentElement.lang = lang;
            document.documentElement.dir = lang === 'he' ? 'rtl' : 'ltr';

            // Update language toggle button to show opposite language
            const langBtn = document.getElementById('langToggleBtn');
            langBtn.textContent = lang === 'he' ? 'English' : 'עברית';

            // Update static text
            document.getElementById('pageTitle').textContent = t('pageTitle');
            document.getElementById('mainTitle').textContent = t('mainTitle');
            document.getElementById('subtitleText').textContent = t('subtitle');
            document.getElementById('labelOrigin').textContent = t('labelOrigin');
            document.getElementById('labelArea').textContent = t('labelArea');
            document.getElementById('labelCity').textContent = t('labelCity');
            document.getElementById('chartTitle').textContent = t('chartTitle');
            document.getElementById('chartTitleLast3').textContent = t('chartTitleLast3');
            document.getElementById('dailyBreakdownTitle').textContent = t('dailyBreakdown');
            document.getElementById('footerSource').textContent = t('footerSource');
            document.getElementById('footerData').innerHTML = t('footerData') + ' <a href="https://github.com/yuval-harpaz/alarms" target="_blank">yuval-harpaz/alarms</a>';

            // Update "All" option text in selects
            document.querySelectorAll('option[value="__all__"]').forEach(opt => {
                opt.textContent = t('all');
            });

            // Update origin dropdown options
            $('#originSelect option').each(function() {
                const val = $(this).val();
                if (val !== '__all__') {
                    $(this).text(getOriginName(val));
                }
            });

            // Update area dropdown options
            $('#areaSelect option').each(function() {
                const val = $(this).val();
                if (val !== '__all__') {
                    $(this).text(getAreaName(val));
                }
            });

            // Update city dropdown options
            $('#citySelect option').each(function() {
                const val = $(this).val();
                if (val !== '__all__') {
                    $(this).text(getCityName(val));
                }
            });

            // Destroy and reinitialize Select2 to pick up new option texts
            $('#originSelect, #areaSelect, #citySelect').select2('destroy').select2({
                allowClear: false,
                width: '200px'
            });

            // Refresh charts and legends
            updateFromFilters();
            updateLegends();
        }

        function updateLegends() {
            // Update combined chart legend (by day groups)
            const legendHtml = dayGroups.map((group, g) =>
                `<div class="legend-item"><div class="legend-color" style="background:${groupColors[g % groupColors.length]}"></div>${getDayGroupLabel(group)}</div>`
            ).join('');
            document.getElementById('alarmLegend').innerHTML = legendHtml;

            // Update day titles
            days.forEach((day, i) => {
                const titleEl = document.getElementById('dayTitle' + i);
                if (titleEl) titleEl.textContent = getDayName(i);
            });

            // Update origin legend
            updateOriginLegend();
        }

        function updateOriginLegend() {
            const knownOrigins = originList.filter(o => o !== '');
            const originLegendHtml = [...knownOrigins, ''].map(origin =>
                `<div class="legend-item"><div class="legend-color" style="background:${originColors[origin]}"></div>${getOriginName(origin)}</div>`
            ).join('');
            const legendEl = document.getElementById('originLegend');
            if (legendEl) legendEl.innerHTML = originLegendHtml;
        }

        // Area to city indices mapping
        const areaToCities = ''' + json.dumps(area_to_cities_idx, ensure_ascii=False) + ''';

        // Compact alarm data: [{t: timestamp, c: [city_indices], o: origin_index}]
        const alarmData = ''' + json.dumps(compact_alarms, ensure_ascii=False) + ''';

        let alarmCombinedChart = null;
        let alarmLast3Chart = null;
        let alarmDayCharts = [];
        const last3Days = days.slice(-3);
        const last3DayIndices = days.map((d, i) => i).slice(-3);

        // Build day groups (chunks of 3) for the all-days combined chart
        const dayGroups = [];
        for (let i = 0; i < days.length; i += 3) {
            dayGroups.push(days.slice(i, Math.min(i + 3, days.length)));
        }
        const groupColors = ['#e74c3c', '#3498db', '#f39c12', '#9b59b6', '#2ecc71'];

        function getDayGroupLabel(group) {
            if (group.length === 1) {
                const idx = days.indexOf(group[0]);
                return getDayName(idx);
            }
            const firstIdx = days.indexOf(group[0]);
            const lastIdx = days.indexOf(group[group.length - 1]);
            return getDayName(firstIdx) + ' — ' + getDayName(lastIdx);
        }

        // Compute histogram based on current filters
        // Returns: { combined: {day: [24 hourly counts]}, byOrigin: {day: {originIdx: [24 hourly counts]}} }
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

            // Initialize histograms
            const combined = {};
            const byOrigin = {};
            days.forEach(day => {
                combined[day] = new Array(24).fill(0);
                byOrigin[day] = {};
                originList.forEach((_, idx) => {
                    byOrigin[day][idx] = new Array(24).fill(0);
                });
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

                if (combined[dayStr]) {
                    combined[dayStr][hour]++;
                    byOrigin[dayStr][alarm.o][hour]++;
                }
            });

            return { combined, byOrigin };
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

            // Language toggle - single button that toggles between languages
            document.getElementById('langToggleBtn').addEventListener('click', () => {
                setLanguage(currentLang === 'he' ? 'en' : 'he');
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
            const urlLang = getUrlParam('lang');

            $('#originSelect').val(urlOrigin).trigger('change.select2');
            $('#areaSelect').val(urlArea).trigger('change.select2');
            updateCityOptions(urlArea);
            $('#citySelect').val(urlCity).trigger('change.select2');

            // Set initial language
            setLanguage(urlLang || currentLang);
        });

        function updateCityOptions(area) {
            const citySelect = $('#citySelect');
            const currentCity = citySelect.val();

            // Clear and rebuild options
            citySelect.empty();
            citySelect.append(`<option value="__all__">${t('all')}</option>`);

            if (area === '__all__') {
                // Show all cities
                cityList.forEach(city => {
                    citySelect.append(`<option value="${city}">${getCityName(city)}</option>`);
                });
            } else {
                // Show only cities in selected area
                const areaCityIndices = areaToCities[area] || [];
                areaCityIndices.forEach(idx => {
                    const city = cityList[idx];
                    citySelect.append(`<option value="${city}">${getCityName(city)}</option>`);
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

            const histogramData = computeHistogram(origin, area, city);
            updateCharts(histogramData, origin, area, city);
        }

        function initCharts() {
            // Create legend for combined chart (by day)
            updateLegends();

            // Create day chart containers (legend will be added dynamically)
            let alarmDayHtml = `<div id="originLegend" class="origin-legend" style="display:flex;justify-content:center;gap:20px;margin-bottom:20px;flex-wrap:wrap;"></div>`;
            days.forEach((day, i) => {
                alarmDayHtml += `
                    <div class="day-chart">
                        <h3 id="dayTitle${i}">${getDayName(i)}</h3>
                        <div class="day-chart-wrapper">
                            <canvas id="alarmChart${i}"></canvas>
                        </div>
                        <div class="change-indicator" id="alarmChange${i}"></div>
                    </div>`;
            });
            document.getElementById('alarmDayCharts').innerHTML = alarmDayHtml;

            // Update origin legend
            updateOriginLegend();

            // Initialize combined chart (all days, grouped by 3)
            alarmCombinedChart = createGroupedChart('alarmCombinedChart');

            // Initialize last 3 days chart (single color, not stacked)
            alarmLast3Chart = createLast3Chart('alarmLast3Chart');

            // Initialize day charts (stacked by origin)
            days.forEach((day, i) => {
                alarmDayCharts.push(createDayChart('alarmChart' + i));
            });
        }

        function createGroupedChart(canvasId) {
            const ctx = document.getElementById(canvasId).getContext('2d');
            return new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: hours,
                    datasets: dayGroups.map((group, g) => ({
                        label: getDayGroupLabel(group),
                        data: new Array(24).fill(0),
                        backgroundColor: groupColors[g % groupColors.length],
                        borderColor: groupColors[g % groupColors.length],
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

        function createLast3Chart(canvasId) {
            const ctx = document.getElementById(canvasId).getContext('2d');
            return new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: hours,
                    datasets: [{
                        label: t('alarms'),
                        data: new Array(24).fill(0),
                        backgroundColor: '#e67e22',
                        borderColor: '#d35400',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: {
                            ticks: { color: '#aaa' },
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

        function createDayChart(canvasId) {
            const ctx = document.getElementById(canvasId).getContext('2d');
            // Create datasets for each origin (excluding empty/unknown for cleaner display)
            const datasets = originList.filter(o => o !== '').map((origin, i) => ({
                label: getOriginName(origin),
                data: new Array(24).fill(0),
                backgroundColor: originColors[origin],
                borderColor: originColors[origin],
                borderWidth: 1
            }));
            // Add unknown origin dataset at the end
            datasets.push({
                label: getOriginName(''),
                data: new Array(24).fill(0),
                backgroundColor: originColors[''],
                borderColor: originColors[''],
                borderWidth: 1
            });

            return new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: hours,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: {
                            stacked: true,
                            ticks: { color: '#aaa', maxRotation: 45, minRotation: 45 },
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

        function updateCharts(histogramData, origin, area, city) {
            const { combined, byOrigin } = histogramData;

            // Build display name with translations
            let displayParts = [];
            if (origin !== '__all__') displayParts.push(getOriginName(origin));
            if (area !== '__all__') displayParts.push(getAreaName(area));
            if (city !== '__all__') displayParts.push(getCityName(city));
            const displayName = displayParts.length > 0 ? displayParts.join(' | ') : t('all');
            document.getElementById('currentFilterDisplay').textContent = displayName;

            // Update combined chart (stacked by day groups)
            dayGroups.forEach((group, g) => {
                const merged = new Array(24).fill(0);
                group.forEach(day => {
                    combined[day].forEach((v, h) => merged[h] += v);
                });
                alarmCombinedChart.data.datasets[g].label = getDayGroupLabel(group);
                alarmCombinedChart.data.datasets[g].data = merged;
            });
            alarmCombinedChart.update();

            // Update last 3 days chart (single merged series)
            const last3Merged = new Array(24).fill(0);
            last3Days.forEach(day => {
                combined[day].forEach((v, h) => last3Merged[h] += v);
            });
            alarmLast3Chart.data.datasets[0].label = t('alarms');
            alarmLast3Chart.data.datasets[0].data = last3Merged;
            alarmLast3Chart.update();

            // Update day charts (stacked by origin) - update labels and data
            const knownOrigins = originList.filter(o => o !== '');
            days.forEach((day, i) => {
                knownOrigins.forEach((origin, j) => {
                    const originIdx = originList.indexOf(origin);
                    alarmDayCharts[i].data.datasets[j].label = getOriginName(origin);
                    alarmDayCharts[i].data.datasets[j].data = byOrigin[day][originIdx];
                });
                // Unknown origin is last dataset
                const unknownIdx = originList.indexOf('');
                alarmDayCharts[i].data.datasets[knownOrigins.length].label = getOriginName('');
                alarmDayCharts[i].data.datasets[knownOrigins.length].data = byOrigin[day][unknownIdx];
                alarmDayCharts[i].update();
            });

            // Update stats
            updateStats(combined);

            // Update change indicators
            updateChangeIndicators(combined);
        }

        function updateStats(histogram) {
            let total = 0;
            let rows = '';
            let prevSum = null;
            days.forEach((day, i) => {
                const sum = histogram[day].reduce((a, b) => a + b, 0);
                total += sum;

                // Calculate change from previous day
                let changeHtml = '-';
                if (prevSum !== null && prevSum > 0) {
                    const pct = ((sum - prevSum) / prevSum * 100).toFixed(0);
                    const arrow = sum > prevSum ? '↑' : (sum < prevSum ? '↓' : '');
                    const color = sum > prevSum ? '#e74c3c' : (sum < prevSum ? '#2ed573' : '#aaa');
                    changeHtml = `<span style="color: ${color}">${arrow} ${pct > 0 ? '+' : ''}${pct}%</span>`;
                }
                prevSum = sum;

                rows += `
                    <tr>
                        <td><span class="color-indicator" style="background: ${colors[i % colors.length]}"></span> ${getDayName(i)}</td>
                        <td style="color: ${colors[i % colors.length]}">${sum}</td>
                        <td>${changeHtml}</td>
                    </tr>`;
            });
            rows += `
                <tr>
                    <td><strong>${t('total')}</strong></td>
                    <td style="color: #ffa502"><strong>${total}</strong></td>
                    <td></td>
                </tr>`;

            const html = `
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>${t('day')}</th>
                            <th>${t('alarms')}</th>
                            <th>${t('change')}</th>
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
                elem.innerHTML = `${arrow} ${Math.abs(change)} ${t('alarms')} (${pct > 0 ? '+' : ''}${pct}%) ${t('fromPrevDay')}`;
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
