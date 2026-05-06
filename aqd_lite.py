import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ── Page configuration ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Loftgæðamælingar",
    page_icon="🌍",
    layout="wide"
)

st.markdown("""
<style>
    svg {
        width: 100% !important;
        height: auto !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Auto-refresh every 60 minutes (3 600 000 ms) ───────────────────────────────
# st_autorefresh returns an incrementing integer; we use it to detect when the
# component has fired so we know to re-fetch data.
_refresh_count = st_autorefresh(interval=60 * 60 * 1000, key="autorefresh")

# ── Station data — hardcoded from stationlist.xlsx ─────────────────────────────
# Columns: id, name, and one boolean per pollutant indicating whether that
# station is expected to report that measurement.
STATION_DATA = [
    {'id': 'STA-IS0037A', 'name': 'Dalsmári',             'PM10': True,  'PM2.5': True,  'PM1': True,  'NO2': True,  'H2S': True,  'SO2': True},
    {'id': 'STA-IS0046A', 'name': 'Norðurhella',           'PM10': True,  'PM2.5': True,  'PM1': False, 'NO2': True,  'H2S': True,  'SO2': True},
    {'id': 'STA-IS0064A', 'name': 'Garðaholt',             'PM10': True,  'PM2.5': True,  'PM1': True,  'NO2': False, 'H2S': True,  'SO2': True},
    {'id': 'STA-IS0063A', 'name': 'Hörðuvallaskóli',       'PM10': True,  'PM2.5': True,  'PM1': True,  'NO2': True,  'H2S': True,  'SO2': True},
    {'id': 'STA-IS0044A', 'name': 'Grindavík',             'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': False},
    {'id': 'STA-IS0033A', 'name': 'Reykjahlíð',            'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': False},
    {'id': 'STA-IS0034A', 'name': 'Vogar, Mývatn',         'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': False},
    {'id': 'STA-IS0035A', 'name': 'Kelduhverfi',           'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': False},
    {'id': 'STA-IS0062A', 'name': 'Reykjaheiði',           'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': False},
    {'id': 'STA-IS0025A', 'name': 'Kríuvarða',             'PM10': False, 'PM2.5': False, 'PM1': True,  'NO2': True,  'H2S': True,  'SO2': True},
    {'id': 'STA-IS0041A', 'name': 'Gröf',                  'PM10': True,  'PM2.5': True,  'PM1': False, 'NO2': True,  'H2S': True,  'SO2': True},
    {'id': 'STA-IS0048A', 'name': 'Melahverfi',            'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': True},
    {'id': 'STA-IS0022A', 'name': 'Norðlingaholt',         'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': False},
    {'id': 'STA-IS0024A', 'name': 'Hveragerði',            'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': False},
    {'id': 'STA-IS0036A', 'name': 'Waldorfskólinn',        'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': False},
    {'id': 'STA-IS0054A', 'name': 'Lambhagi',              'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': False},
    {'id': 'STA-IS0002A', 'name': 'Hvaleyrarholt',         'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': False, 'SO2': True},
    {'id': 'STA-IS0065A', 'name': 'Lónakot',               'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': False, 'SO2': True},
    {'id': 'STA-IS0052A', 'name': 'Akureyri',              'PM10': True,  'PM2.5': False, 'PM1': False, 'NO2': True,  'H2S': False, 'SO2': True},
    {'id': 'STA-IS0005A', 'name': 'Grensásvegur',          'PM10': True,  'PM2.5': True,  'PM1': False, 'NO2': True,  'H2S': True,  'SO2': True},
    {'id': 'STA-IS0006A', 'name': 'Húsdýragarðurinn',      'PM10': True,  'PM2.5': True,  'PM1': True,  'NO2': True,  'H2S': False, 'SO2': False},
    {'id': 'STA-IS0061A', 'name': 'Laugarnes',             'PM10': True,  'PM2.5': True,  'PM1': True,  'NO2': True,  'H2S': True,  'SO2': True},
    {'id': 'STA-IS0066A', 'name': 'Garður',                'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': True},
    {'id': 'STA-IS0067A', 'name': 'Ásbrú',                 'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': True},
    {'id': 'STA-IS0068A', 'name': 'Sandgerði',             'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': True},
    {'id': 'STA-IS0069A', 'name': 'Hafnir',                'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': True},
    {'id': 'STA-IS0070A', 'name': 'Keflavík Vatnaveröld',  'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': True},
    {'id': 'STA-IS0071A', 'name': 'Stapaskóli',            'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': True},
    {'id': 'STA-IS0072A', 'name': 'Vogar',                 'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': True},
    {'id': 'STA-IS0073A', 'name': 'Selfoss',               'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': True},
    {'id': 'STA-IS0074A', 'name': 'Kirkjubæjarklaustur',   'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': True,  'SO2': True},
    {'id': 'STA-IS0027A', 'name': 'Hjallaleyra',           'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': False, 'SO2': True},
    {'id': 'STA-IS0028A', 'name': 'Ljósá',                 'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': False, 'SO2': True},
    {'id': 'STA-IS0029A', 'name': 'Hólmar',                'PM10': False, 'PM2.5': False, 'PM1': False, 'NO2': False, 'H2S': False, 'SO2': True},
]

STATIONS = [s['id'] for s in STATION_DATA]
STATION_NAMES = {s['id']: s['name'] for s in STATION_DATA}
EXPECTED_MEASUREMENTS = {
    s['id']: {p: s[p] for p in ['PM10', 'PM2.5', 'PM1', 'NO2', 'H2S', 'SO2']}
    for s in STATION_DATA
}

# ── Pollutants ─────────────────────────────────────────────────────────────────
POLLUTANTS = ["PM10", "PM2.5", "PM1", "NO2", "SO2", "H2S"]

# ── Colors and markers — one per station, consistent across charts ──────────────
cmap  = plt.colormaps['tab20']
cmap2 = plt.colormaps['tab20b']

all_colors = []
for i in range(20):
    all_colors.append(cmap(i / 20))
for i in range(20):
    all_colors.append(cmap2(i / 20))

MARKER_STYLES = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h', 'H', '+', 'x', 'd', '|', '_']

STATION_COLORS  = {}
STATION_MARKERS = {}
for idx, station_id in enumerate(STATIONS):
    rgba = all_colors[idx]
    STATION_COLORS[station_id]  = '#{:02x}{:02x}{:02x}'.format(
        int(rgba[0] * 255), int(rgba[1] * 255), int(rgba[2] * 255)
    )
    STATION_MARKERS[station_id] = MARKER_STYLES[idx % len(MARKER_STYLES)]

# ── Pollutant thresholds (from loftgaedi.is) ───────────────────────────────────
# Format: (min_value, max_value, color, category_name)
POLLUTANT_THRESHOLDS = {
    'PM10':  [(0,   25,         '#3ab734', 'Mjög góð'),
              (25,  50,         '#B5CF87', 'Góð'),
              (50,  75,         '#efef33', 'Sæmileg'),
              (75,  100,        '#e2791b', 'Óholl fyrir viðkvæma'),
              (100, float('inf'), '#f73138', 'Óholl')],
    'PM2.5': [(0,   10,         '#3ab734', 'Mjög góð'),
              (10,  15,         '#B5CF87', 'Góð'),
              (15,  25,         '#efef33', 'Sæmileg'),
              (25,  50,         '#e2791b', 'Óholl fyrir viðkvæma'),
              (50,  float('inf'), '#f73138', 'Óholl')],
    'PM1':   [(0,   6,          '#3ab734', 'Mjög góð'),
              (6,   13,         '#B5CF87', 'Góð'),
              (13,  19,         '#efef33', 'Sæmileg'),
              (19,  25,         '#e2791b', 'Óholl fyrir viðkvæma'),
              (25,  float('inf'), '#f73138', 'Óholl')],
    'NO2':   [(0,   50,         '#3ab734', 'Mjög góð'),
              (50,  75,         '#B5CF87', 'Góð'),
              (75,  150,        '#efef33', 'Sæmileg'),
              (150, 200,        '#e2791b', 'Óholl fyrir viðkvæma'),
              (200, float('inf'), '#f73138', 'Óholl')],
    'SO2':   [(0,   20,         '#3ab734', 'Mjög góð'),
              (20,  350,        '#B5CF87', 'Góð'),
              (350, 600,        '#efef33', 'Sæmileg'),
              (600, 2600,       '#e2791b', 'Óholl fyrir viðkvæma'),
              (2600, float('inf'), '#f73138', 'Óholl')],
    'H2S':   [(0,   25,         '#3ab734', 'Mjög góð'),
              (25,  50,         '#B5CF87', 'Góð'),
              (50,  75,         '#efef33', 'Sæmileg'),
              (75,  100,        '#e2791b', 'Óholl fyrir viðkvæma'),
              (100, float('inf'), '#f73138', 'Óholl')],
}

# ── Helper functions ───────────────────────────────────────────────────────────

def get_air_quality_color(pollutant, value):
    """Return (hex_color, category_name) for a given pollutant and concentration."""
    if pollutant not in POLLUTANT_THRESHOLDS:
        return '#cccccc', 'Óþekkt'
    for min_val, max_val, color, category in POLLUTANT_THRESHOLDS[pollutant]:
        if min_val <= value < max_val:
            return color, category
    return '#cccccc', 'Óþekkt'


def add_threshold_lines(ax, pollutant, max_data_value):
    """Draw dashed horizontal lines for all threshold boundaries on the given axis."""
    if pollutant not in POLLUTANT_THRESHOLDS:
        return
    for min_val, max_val, color, category in POLLUTANT_THRESHOLDS[pollutant]:
        if min_val == 0:
            continue
        ax.axhline(y=min_val, color=color, linestyle='--', linewidth=1.0,
                   alpha=0.85, dashes=(10, 10), zorder=1)


def set_minimum_y_scale(ax, pollutant, max_data_value, min_data_value):
    """
    Set y-axis limits so that all threshold lines are visible and negative
    sensor readings are not clipped.
    """
    min_y_maximums = {
        'PM10':  105,
        'PM2.5': 52,
        'PM1':   26,
        'NO2':   210,
        'SO2':   100,
        'H2S':   40,
    }
    min_y_max = min_y_maximums.get(pollutant, 100)
    y_max = max(max_data_value * 1.1, min_y_max)
    y_min = min(min_data_value * 1.1 if min_data_value < 0 else 0, 0)
    ax.set_ylim(bottom=y_min, top=y_max)


def format_pollutant_name(pollutant):
    """Return a pollutant name with proper LaTeX subscript formatting for matplotlib."""
    formatting = {
        'PM10':  r'PM$_{\mathbf{10}}$',
        'PM2.5': r'PM$_{\mathbf{2.5}}$',
        'PM1':   r'PM$_{\mathbf{1}}$',
        'NO2':   r'NO$_\mathbf{2}$',
        'SO2':   r'SO$_\mathbf{2}$',
        'H2S':   r'H$_\mathbf{2}$S',
    }
    return formatting.get(pollutant, pollutant)


def format_unit(unit):
    """Return a unit string with proper LaTeX superscript for m³."""
    if 'µg/m3' in unit or 'μg/m3' in unit or 'ug/m3' in unit:
        return 'µg/m$^3$'
    elif 'mg/m3' in unit:
        return 'mg/m$^3$'
    return unit


def fetch_station_data(station_id):
    """
    Fetch the last 24 hours of data for a single station from api.ust.is.
    Returns (DataFrame, station_name) on success, or (None, None) on failure.
    """
    url = f"https://api.ust.is/aq/a/getCurrent/id/{station_id}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None, None

        data = response.json()
        if station_id not in data:
            return None, None

        station_data = data[station_id]
        station_name = station_data['name']
        parameters   = station_data['parameters']

        measurements = []
        for pollutant in POLLUTANTS:
            if pollutant in parameters:
                pollutant_readings = parameters[pollutant]
                unit = pollutant_readings.get('unit', 'µg/m³')
                for key, reading in pollutant_readings.items():
                    if key.isdigit():
                        measurements.append({
                            'station_id':   station_id,
                            'station_name': station_name,
                            'parameter':    pollutant,
                            'datetime':     reading['endtime'],
                            'value':        float(reading['value']),
                            'unit':         unit,
                        })

        if measurements:
            df = pd.DataFrame(measurements)
            df['datetime'] = pd.to_datetime(df['datetime'])
            mapped_name = STATION_NAMES.get(station_id, station_name)
            df['station_name'] = mapped_name
            return df, mapped_name
        else:
            mapped_name = STATION_NAMES.get(station_id, station_name)
            return pd.DataFrame(), mapped_name

    except Exception:
        return None, None


def load_all_data():
    """Fetch data for every station and return (all_data dict, station_names dict)."""
    all_data      = {}
    station_names = {}
    for station_id in STATIONS:
        df, name = fetch_station_data(station_id)
        all_data[station_id]      = df
        station_names[station_id] = STATION_NAMES.get(station_id, name if name else "Unknown")
    return all_data, station_names


def create_compact_dashboard(all_data):
    """Create a 3×2 grid of pollutant charts and return the matplotlib Figure."""
    fig, axes = plt.subplots(3, 2, figsize=(18, 16), dpi=150)
    axes = axes.flatten()

    for idx, pollutant in enumerate(POLLUTANTS):
        ax = axes[idx]

        # Collect data for stations expected to report this pollutant
        pollutant_data = []
        for station_id, df in all_data.items():
            if df is not None:
                is_expected = EXPECTED_MEASUREMENTS.get(station_id, {}).get(pollutant, False)
                if is_expected:
                    station_pollutant = df[df['parameter'] == pollutant]
                    if not station_pollutant.empty:
                        pollutant_data.append((station_id, station_pollutant))

        if not pollutant_data:
            ax.text(0.5, 0.5, f'Engin {format_pollutant_name(pollutant)} gögn',
                    ha='center', va='center', fontsize=14)
            ax.set_title(format_pollutant_name(pollutant), fontsize=16, fontweight='bold')
            ax.axis('off')
            continue

        station_plot_data = []
        max_value = 0
        min_value = 0

        for station_id, df in pollutant_data:
            station_name = df['station_name'].iloc[0]
            df_sorted = df.sort_values('datetime')

            if not df_sorted['value'].empty:
                max_value      = max(max_value, df_sorted['value'].max())
                min_value      = min(min_value, df_sorted['value'].min())
                latest_value   = df_sorted['value'].iloc[-1]
                latest_ts      = df_sorted['datetime'].iloc[-1]
            else:
                latest_value = -float('inf')
                latest_ts    = None

            station_plot_data.append({
                'station_id':   station_id,
                'station_name': station_name,
                'df_sorted':    df_sorted,
                'latest_value': latest_value,
                'latest_ts':    latest_ts,
            })

        station_plot_data.sort(key=lambda x: x['latest_value'], reverse=True)

        current_time  = datetime.now()
        stale_stations = {}
        for plot_data in station_plot_data:
            sid = plot_data['station_id']
            lts = plot_data['latest_ts']
            if lts is not None:
                hours_since = (current_time - lts).total_seconds() / 3600
                stale_stations[sid] = hours_since > 3
            else:
                stale_stations[sid] = False

        handles = []
        labels  = []
        for plot_data in station_plot_data:
            station_id   = plot_data['station_id']
            station_name = plot_data['station_name']
            df_sorted    = plot_data['df_sorted']
            latest_value = plot_data['latest_value']

            legend_label = (
                f"{station_name} - {int(round(latest_value))}"
                if latest_value != -float('inf') else station_name
            )

            color  = STATION_COLORS[station_id]
            marker = STATION_MARKERS[station_id]
            line,  = ax.plot(df_sorted['datetime'], df_sorted['value'],
                             marker=marker, label=legend_label,
                             linewidth=1.5, markersize=4, color=color, alpha=0.7)
            handles.append(line)
            labels.append(legend_label)

        add_threshold_lines(ax, pollutant, max_value)
        set_minimum_y_scale(ax, pollutant, max_value, min_value)

        # Add dummy legend entries for expected-but-missing stations
        for station_id in STATIONS:
            is_expected = EXPECTED_MEASUREMENTS.get(station_id, {}).get(pollutant, True)
            has_data = (
                all_data.get(station_id) is not None
                and not all_data[station_id][all_data[station_id]['parameter'] == pollutant].empty
            )
            if is_expected and not has_data:
                station_name = STATION_NAMES.get(station_id, station_id)
                color  = STATION_COLORS[station_id]
                marker = STATION_MARKERS[station_id]
                line,  = ax.plot([], [], marker=marker, linewidth=1.5, markersize=4,
                                 color=color, alpha=0.7, label=station_name)
                handles.append(line)
                labels.append(station_name)

        unit           = pollutant_data[0][1]['unit'].iloc[0]
        formatted_unit = format_unit(unit)
        ax.set_xlabel('', fontsize=9)
        ax.set_ylabel(formatted_unit, fontsize=9)
        ax.set_title(format_pollutant_name(pollutant), fontsize=16, fontweight='bold', pad=10)
        ax.axhline(y=0, color='black', linewidth=1.5, alpha=0.6, zorder=1)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d. %H:%M'))

        legend = ax.legend(handles, labels, fontsize=6, loc='best', ncol=2)
        for text, legend_label in zip(legend.get_texts(), labels):
            for sid in STATIONS:
                sname = STATION_NAMES.get(sid, sid)
                if legend_label.startswith(sname):
                    is_expected = EXPECTED_MEASUREMENTS.get(sid, {}).get(pollutant, True)
                    has_data = (
                        all_data.get(sid) is not None
                        and not all_data[sid][all_data[sid]['parameter'] == pollutant].empty
                    )
                    is_stale = stale_stations.get(sid, False)
                    if (is_expected and not has_data) or is_stale:
                        text.set_color('red')
                    break

        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45, labelsize=7)
        ax.tick_params(axis='y', labelsize=8)

    plt.tight_layout()
    return fig


def create_status_table(all_data, station_names):
    """Return a DataFrame showing which pollutants each station is currently reporting."""
    status_data = []
    for station_id in STATIONS:
        df           = all_data.get(station_id)
        station_name = STATION_NAMES.get(station_id, station_names.get(station_id, "Unknown"))
        display_name = f"{station_name} ({station_id})"
        row = {'Stöð': display_name}
        for pollutant in POLLUTANTS:
            is_expected = EXPECTED_MEASUREMENTS.get(station_id, {}).get(pollutant, True)
            has_data    = df is not None and not df[df['parameter'] == pollutant].empty
            if not is_expected:
                row[pollutant] = '—'
            elif has_data:
                row[pollutant] = '✓'
            else:
                row[pollutant] = '✗'
        status_data.append(row)
    return pd.DataFrame(status_data)


# ── Session state and data loading ────────────────────────────────────────────
# Load data on first visit, and whenever the auto-refresh component fires.
_needs_load = (
    'all_data' not in st.session_state
    or _refresh_count > st.session_state.get('last_refresh_count', -1)
)

if _needs_load:
    with st.spinner("Sæki gögn..."):
        try:
            all_data, station_names               = load_all_data()
            st.session_state.all_data             = all_data
            st.session_state.station_names        = station_names
            st.session_state.last_refresh         = datetime.now()
            st.session_state.last_refresh_count   = _refresh_count
        except Exception as e:
            st.error(f"Gat ekki sótt gögn: {str(e)}")
            st.stop()

# ── Compact overview dashboard ─────────────────────────────────────────────────
fig = create_compact_dashboard(st.session_state.all_data)

svg_buffer = io.BytesIO()
fig.savefig(svg_buffer, format='svg', bbox_inches='tight')
svg_buffer.seek(0)
svg_string = svg_buffer.getvalue().decode('utf-8')

st.markdown(svg_string, unsafe_allow_html=True)
plt.close(fig)

# ── Station summary with colour indicators ─────────────────────────────────────
st.markdown("---")
st.markdown("### Yfirlit stöðva")

color_priority = {'#f73138': 4, '#e2791b': 3, '#efef33': 2, '#B5CF87': 1, '#3ab734': 0, '#cccccc': -1}
station_summary = []
for station_id in STATIONS:
    df           = st.session_state.all_data.get(station_id)
    station_name = STATION_NAMES.get(station_id, "Unknown")

    if df is not None and not df.empty:
        colors = []
        for pollutant in POLLUTANTS:
            pollutant_data = df[df['parameter'] == pollutant]
            if not pollutant_data.empty:
                current_value = pollutant_data['value'].iloc[0]
                color, _      = get_air_quality_color(pollutant, current_value)
                colors.append(color)
        if colors:
            worst_color = max(colors, key=lambda c: color_priority.get(c, -1))
            station_summary.append((station_name, worst_color, station_id))
        else:
            station_summary.append((station_name, '#cccccc', station_id))
    else:
        station_summary.append((station_name, '#cccccc', station_id))

cols_per_row = 6
for i in range(0, len(station_summary), cols_per_row):
    cols = st.columns(cols_per_row)
    for j, col in enumerate(cols):
        if i + j < len(station_summary):
            name, color, station_id = station_summary[i + j]
            with col:
                st.markdown(
                    f'<div style="display: flex; align-items: center; gap: 5px; padding: 3px 0;">'
                    f'<div style="width: 15px; height: 15px; border-radius: 50%; '
                    f'background-color: {color}; border: 1px solid #333; flex-shrink: 0;"></div>'
                    f'<span style="font-size: 16px;" title="{station_id}">{name}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

st.markdown("---")

# ── Status table and manual refresh ───────────────────────────────────────────
status_df = create_status_table(st.session_state.all_data, st.session_state.station_names)

def color_status(val):
    if val == '✓':
        return 'color: green; font-weight: bold'
    elif val == '✗':
        return 'color: red; font-weight: bold'
    elif val == '—':
        return 'color: gray; font-weight: normal'
    return ''

styled_df = status_df.style.map(color_status, subset=POLLUTANTS)
st.dataframe(styled_df, width='stretch', height=600)

last_refresh_str = st.session_state.last_refresh.strftime('Uppfært: %d.%m.%y - %H:%M')
st.markdown(f"*{last_refresh_str}*")

col1, col2 = st.columns([5, 1])
with col2:
    if st.button("Uppfæra", use_container_width=True):
        with st.spinner("Uppfæri..."):
            try:
                all_data, station_names             = load_all_data()
                st.session_state.all_data           = all_data
                st.session_state.station_names      = station_names
                st.session_state.last_refresh       = datetime.now()
                # Keep last_refresh_count unchanged so the auto-refresh
                # cycle is not accidentally reset.
            except Exception as e:
                st.error(f"Uppfærsla mistókst: {str(e)}")
        st.rerun()

# ── Hourly values (expandable tables, one per pollutant) ───────────────────────
st.markdown("---")
st.markdown("## Tímagildi (24 tíma gögn)")

for pollutant in POLLUTANTS:
    hourly_data = {}
    expected_stations = [
        (sid, STATION_NAMES.get(sid, sid))
        for sid in STATIONS
        if EXPECTED_MEASUREMENTS.get(sid, {}).get(pollutant, False)
    ]

    for station_id, station_name in expected_stations:
        df = st.session_state.all_data.get(station_id)
        if df is not None:
            station_pollutant = df[df['parameter'] == pollutant]
            if not station_pollutant.empty:
                for _, row in station_pollutant.sort_values('datetime').iterrows():
                    timestamp = row['datetime'].strftime('%Y-%m-%d %H:%M')
                    if timestamp not in hourly_data:
                        hourly_data[timestamp] = {}
                    hourly_data[timestamp][station_name] = f"{row['value']:.2f}"

    if expected_stations:
        with st.expander(f"{pollutant} - Tímagildi"):
            if hourly_data:
                hourly_df = pd.DataFrame(hourly_data).T
                hourly_df.index.name = 'Tími'
                hourly_df = hourly_df.sort_index(ascending=False)

                all_station_names = [name for _, name in expected_stations]
                for sname in all_station_names:
                    if sname not in hourly_df.columns:
                        hourly_df[sname] = None
                hourly_df = hourly_df[all_station_names]

                st.dataframe(hourly_df, width='stretch', height=400)
            else:
                st.warning(f"Engin gögn tiltæk fyrir {pollutant}")
