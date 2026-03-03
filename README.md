# Missile Alarms Dashboard

A real-time dashboard visualizing missile alarm data from the Israeli Home Front Command during the 2026 war period.

## Live Dashboard

The dashboard is hosted via GitHub Pages and updates automatically every 30 minutes.

## Data Source

Alarm data is sourced from [yuval-harpaz/alarms](https://github.com/yuval-harpaz/alarms), which collects and maintains historical alarm records from the Israeli Home Front Command (Pikud HaOref).

The CSV file contains:
- Timestamp of each alarm
- Location/city name

## How It Works

### Analysis Script (`analyze_alarms.py`)

The Python script:
1. Downloads the latest alarm CSV from the source repository
2. Filters alarms from the war period (February 28, 2026 onwards)
3. Groups locations by main city (merging neighborhoods like "Tel Aviv - Center" into "Tel Aviv")
4. Deduplicates alarms by exact second for merged cities
5. Generates hourly histograms per day
6. Outputs an interactive HTML dashboard

### Dashboard Features

- City selector with search (Select2)
- Daily alarm counts table
- Stacked bar chart showing hourly distribution across all days
- Individual day charts with day-over-day change indicators
- Bilingual interface (Hebrew/English)
- URL parameter support for direct city links (e.g., `?city=תל אביב`)

## Automatic Updates

A GitHub Actions workflow (`.github/workflows/update.yml`) runs every 30 minutes to:
1. Fetch the latest alarm data
2. Regenerate the HTML dashboard
3. Commit and push changes if the data has updated

The workflow can also be triggered manually via the GitHub Actions UI.

## Local Development

```bash
# Generate the dashboard
python3 analyze_alarms.py

# Open the generated file
open index.html
```

## Project Structure

```
.
├── .github/workflows/update.yml  # Automated update workflow
├── analyze_alarms.py             # Main analysis script
├── index.html                    # Generated dashboard (auto-updated)
└── README.md
```

## License

Data provided by [yuval-harpaz/alarms](https://github.com/yuval-harpaz/alarms).
