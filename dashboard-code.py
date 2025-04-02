import dash
# Make sure to import Input, Output, State if you haven't
from dash import dcc, html, dash_table, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import webbrowser
from threading import Timer
import os

# --- Data Loading Function (assuming it's mostly correct, added Cmp, Tkl, Tkl% attempts) ---
def load_data():
    """Load and prepare the merged player data for the dashboard"""
    print("Attempting to load data...")
    try:
        merged_path = "a_league_data/merged_player_stats.csv"
        standard_path = "a_league_processed/standard_stats_processed.csv"

        if os.path.exists(merged_path):
            df = pd.read_csv(merged_path)
            print(f"Loaded merged data: {len(df)} players, {len(df.columns)} columns from {merged_path}")
        elif os.path.exists(standard_path):
            df = pd.read_csv(standard_path)
            print(f"Loaded standard data: {len(df)} players, {len(df.columns)} columns from {standard_path}")
        else:
            print(f"CRITICAL: No data files found at expected locations:")
            print(f" - Searched for: {os.path.abspath(merged_path)}")
            print(f" - Searched for: {os.path.abspath(standard_path)}")
            return pd.DataFrame(columns=['Player', 'Pos', 'Squad', 'Age', 'Min', 'Gls', 'Ast', 'MP', 'U23', 'Cmp', 'Tkl', 'Tkl%']) # Add expected cols

        print("First 10 columns found:", df.columns[:10].tolist())

        # --- Column Mapping & Cleaning ---
        column_mapping_attempts = {
            'Player': ['Player', 'Player Name'], 'Squad': ['Squad', 'Team'], 'Age': ['Age'],
            'Min': ['Min', 'Playing Time Min', 'Minutes Played'], 'Gls': ['Gls', 'Performance Gls', 'Goals'],
            'Ast': ['Ast', 'Performance Ast', 'Assists'], 'MP': ['MP', 'Playing Time MP', 'Matches Played'],
            'Sh': ['Sh', 'Standard Sh', 'Shots'], 'SoT': ['SoT', 'Standard SoT', 'Shots on Target'],
            'SoT%': ['SoT%', 'Standard SoT%', 'Shot Accuracy %'], 'G/Sh': ['G/Sh', 'Standard G/Sh', 'Goals per Shot'],
            'Pos': ['Pos', 'Position'], '90s': ['90s', 'Playing Time 90s'],
            'xG': ['xG', 'Expected Goals'], 'KP': ['KP', 'Key Passes'], 'xA': ['xA', 'Expected Assists'],
            # Add potential names for new stats
            'Cmp': ['Cmp', 'Passes Completed', 'Total Cmp'], # Passes Completed
            'Tkl': ['Tkl', 'Tackles', 'Tackles Tkl'], # Tackles Won
            'Tkl%': ['Tkl%', 'Tackles Won %', 'TklW%'] # Tackle Success Rate
        }
        actual_mapping = {}
        found_columns = []
        for target_col, potential_names in column_mapping_attempts.items():
            found = False
            for potential_name in potential_names:
                if potential_name in df.columns:
                    if potential_name != target_col:
                         actual_mapping[potential_name] = target_col
                    found_columns.append(target_col)
                    found = True
                    break
            if not found:
                 # Don't make missing optional columns like xG, KP, Cmp, Tkl fatal warnings
                 if target_col not in ['xG', 'KP', 'xA', 'Cmp', 'Tkl', 'Tkl%']:
                    print(f"Warning: Required column '{target_col}' not found using potential names: {potential_names}")
                 else:
                    print(f"Info: Optional column '{target_col}' not found.")

        if actual_mapping:
            print("Applying column mapping:", actual_mapping)
            df = df.rename(columns=actual_mapping)
        print("Columns after potential renaming:", df.columns.tolist())

        # --- Ensure Numeric Types ---
        numeric_targets = ['Age', 'Min', 'Gls', 'Ast', 'MP', 'Sh', 'SoT', 'SoT%', 'G/Sh', '90s', 'xG', 'KP', 'xA', 'Cmp', 'Tkl', 'Tkl%']
        for col in numeric_targets:
            if col in df.columns:
                try:
                    # Special handling for percentages which might have '%' sign
                    if '%' in col and df[col].dtype == 'object':
                        df[col] = df[col].str.replace('%', '', regex=False)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    print(f"Converted '{col}' to numeric.")
                except Exception as e:
                    print(f"Error converting '{col}' to numeric: {e}. Check data.")

        # --- Ensure U23 Flag ---
        if 'Age' in df.columns:
            if 'U23' not in df.columns:
                df['U23'] = df['Age'] < 23
                u23_count = df['U23'].sum()
                print(f"Added 'U23' flag based on 'Age'. Found {u23_count} players under 23.")
            else:
                 df['U23'] = df['U23'].astype(bool)
                 print("'U23' column already exists. Ensured boolean type.")
        elif 'U23' not in df.columns:
            print("Warning: 'Age' column not found. Cannot create 'U23' flag.")
            df['U23'] = False

        print(f"Data loading complete. Final DataFrame shape: {df.shape}")
        return df

    except FileNotFoundError as e:
         print(f"Error: Data file not found. {e}")
         return pd.DataFrame(columns=['Player', 'Pos', 'Squad', 'Age', 'Min', 'Gls', 'Ast', 'MP', 'U23', 'Cmp', 'Tkl', 'Tkl%'])
    except Exception as e:
        print(f"An unexpected error occurred during data loading: {e}")
        return pd.DataFrame(columns=['Player', 'Pos', 'Squad', 'Age', 'Min', 'Gls', 'Ast', 'MP', 'U23', 'Cmp', 'Tkl', 'Tkl%'])


# --- Team Color Function (keep as is) ---
def get_team_color(team):
    team_map = {
        'Adelaide United': 'Adelaide', 'Adelaide': 'Adelaide', 'Brisbane Roar': 'Brisbane', 'Brisbane': 'Brisbane',
        'Central Coast Mariners': 'Central Coast', 'Central Coast': 'Central Coast', 'Macarthur FC': 'Macarthur FC',
        'Melbourne City': 'Melb City', 'Melb City': 'Melb City', 'Melbourne Victory': 'Melb Victory', 'Melb Victory': 'Melb Victory',
        'Newcastle Jets': 'Newcastle', 'Newcastle': 'Newcastle', 'Perth Glory': 'Perth Glory', 'Perth': 'Perth Glory',
        'Sydney FC': 'Sydney FC', 'Sydney': 'Sydney FC', 'Wellington Phoenix': 'Wellington', 'Wellington': 'Wellington',
        'Western Sydney Wanderers': 'W Sydney', 'WS Wanderers': 'W Sydney', 'W Sydney': 'W Sydney',
        'Western United': 'Western United', 'Auckland FC': 'Auckland FC',
    }
    normalized_team = team_map.get(team, team)
    team_colors = {
        'Adelaide': '#9b2633', 'Auckland FC': '#145a7d', 'Brisbane': '#b76d10', 'Central Coast': '#d0af4c',
        'Macarthur FC': '#313131', 'Melb City': '#6295c3', 'Melb Victory': '#1a3a7c', 'Newcastle': '#d1a03e',
        'Perth Glory': '#4f2c7d', 'Sydney FC': '#4b77b8', 'W Sydney': '#bc3034', 'Wellington': '#c3a023',
        'Western United': '#2d5234',
    }
    default_color = '#808080'
    return team_colors.get(normalized_team, default_color)

# --- Load Data ---
df = load_data()
if df.empty:
    print("WARNING: Data loading failed. Dashboard will show 'No Data'.")
    # Ensure fallback df has columns for the new cards too
    df = pd.DataFrame(columns=['Player', 'Pos', 'Squad', 'Age', 'Min', 'Gls', 'Ast', 'MP', 'U23', 'Sh', 'SoT', 'SoT%', 'G/Sh', 'KP', 'xA', 'xG', 'Cmp', 'Tkl', 'Tkl%'])

# --- Create Dash App ---
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# --- App Layout ---
app.layout = html.Div([
    # -- Page Title --
    html.H1(
        "A-League Advanced Analytics Dashboard (U23 Players)",
        style={
            'textAlign': 'center',
            'color': '#4285F4',
            'marginBottom': '30px',
            'fontSize': '32px',
            'fontWeight': '600',
            # Font family will be inherited from body
        }
    ),

    # -- Tabs --
    html.Div([
        html.Div("Overview", id="tab-overview", className="tab active", **{'data-tab': 'overview'}),
    ], className="tabs", style={'borderBottom': '2px solid #e0e0e0', 'marginBottom': '30px'}),

    # -- Overview Tab Content --
    html.Div([
        # -- Summary Stats Row --
        html.Div([
             # Card 1: Total U23 Players
            html.Div([
                html.Div("Total Young Players", className="metric-title"),
                html.Div(id="total-players-u23", className="metric-value", children="--"),
                html.Div(id="total-players-pct", className="metric-subtitle", children="--% of -- players"),
            ], className="metric-card"),
            # Card 2: Average Age U23
            html.Div([
                html.Div("Average Age - U23", className="metric-title"),
                html.Div(id="avg-age-u23", className="metric-value", children="--"),
                html.Div(id="avg-age-all", className="metric-subtitle", children="vs. -- overall"),
            ], className="metric-card"),
            # Card 3: Goals by U23
            html.Div([
                html.Div("Goals by U23 Players", className="metric-title"),
                html.Div(id="total-goals-u23", className="metric-value", children="--"),
                html.Div(id="total-goals-pct", className="metric-subtitle", children="--% of -- goals"),
            ], className="metric-card"),
            # Card 4: Assists by U23
            html.Div([
                html.Div("Assists by U23 Players", className="metric-title"),
                html.Div(id="total-assists-u23", className="metric-value", children="--"),
                html.Div(id="total-assists-pct", className="metric-subtitle", children="--% of -- assists"),
            ], className="metric-card"),
        ], className="metrics-row"), # This class defines the 4-column grid

        # -- Top Young Performers Section Title --
        # Wrap title in a Div for alignment control
        html.Div([
            html.H2("Top Young Performers By Category",
               style={'fontSize': '24px', 'fontWeight': '600', 'color': '#333',
                      'marginTop': '40px', 'marginBottom': '25px',
                      'paddingLeft': '2px', # Small left padding
                      'textAlign': 'left' # Ensure text aligns left within container
                      })
        ], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '0 15px'}), # Container matching card row below


        # -- Performer Cards (Single Row of 4) --
        # Reuse 'metrics-row' class for the 4-column layout
        html.Div([
            # Card 1: Top Goal Scorer (Updated Style)
            html.Div([
                html.Div(html.H3("Top Goal Scorer", style={'fontSize': '16px', 'fontWeight': '600', 'color': '#4285F4', 'marginBottom': '10px', 'textAlign': 'center'}),
                         style={'borderBottom': '1px solid var(--border)', 'paddingBottom': '8px', 'marginBottom': '15px'}),
                html.Div(id="top-scorer-name", children="--",
                         style={'fontSize': '18px', 'fontWeight': 'bold', 'textAlign': 'center', 'marginBottom': '15px', 'color': 'var(--text)'}),
                html.Div([
                    html.Div([ html.Div("Goals", className="perf-label"), html.Div(id="top-scorer-goals", children="--", className="perf-value") ]),
                    html.Div([ html.Div("xG", className="perf-label"), html.Div(id="top-scorer-xg", children="--", className="perf-value") ]),
                    html.Div([ html.Div("Age", className="perf-label"), html.Div(id="top-scorer-age", children="--", className="perf-value") ]),
                ], className="perf-stats-row"), # Use new class for flex layout
            ], className="performer-card"), # Standard card class

            # Card 2: Best Playmaker (Updated Style)
            html.Div([
                html.Div(html.H3("Best Playmaker", style={'fontSize': '16px', 'fontWeight': '600', 'color': '#4285F4', 'marginBottom': '10px', 'textAlign': 'center'}),
                         style={'borderBottom': '1px solid var(--border)', 'paddingBottom': '8px', 'marginBottom': '15px'}),
                html.Div(id="best-playmaker-name", children="--",
                         style={'fontSize': '18px', 'fontWeight': 'bold', 'textAlign': 'center', 'marginBottom': '15px', 'color': 'var(--text)'}),
                html.Div([
                    html.Div([ html.Div("Assists", className="perf-label"), html.Div(id="best-playmaker-assists", children="--", className="perf-value") ]),
                    html.Div([ html.Div("Key Passes", className="perf-label"), html.Div(id="best-playmaker-key-passes", children="--", className="perf-value") ]),
                    html.Div([ html.Div("xA", className="perf-label"), html.Div(id="best-playmaker-xa", children="--", className="perf-value") ]),
                ], className="perf-stats-row"),
            ], className="performer-card"),

            # Card 3: Most Passes (New)
            html.Div([
                html.Div(html.H3("Most Passes", style={'fontSize': '16px', 'fontWeight': '600', 'color': '#4285F4', 'marginBottom': '10px', 'textAlign': 'center'}),
                         style={'borderBottom': '1px solid var(--border)', 'paddingBottom': '8px', 'marginBottom': '15px'}),
                html.Div(id="most-passes-name", children="--",
                         style={'fontSize': '18px', 'fontWeight': 'bold', 'textAlign': 'center', 'marginBottom': '15px', 'color': 'var(--text)'}),
                html.Div([
                    html.Div([ html.Div("Passes", className="perf-label"), html.Div(id="most-passes-total", children="--", className="perf-value") ]),
                    html.Div([ html.Div("Position", className="perf-label"), html.Div(id="most-passes-position", children="--", className="perf-value") ]),
                    html.Div([ html.Div("Age", className="perf-label"), html.Div(id="most-passes-age", children="--", className="perf-value") ]),
                ], className="perf-stats-row"),
            ], className="performer-card"),

            # Card 4: Most Tackles (New)
            html.Div([
                html.Div(html.H3("Most Tackles", style={'fontSize': '16px', 'fontWeight': '600', 'color': '#4285F4', 'marginBottom': '10px', 'textAlign': 'center'}),
                         style={'borderBottom': '1px solid var(--border)', 'paddingBottom': '8px', 'marginBottom': '15px'}),
                html.Div(id="most-tackles-name", children="--",
                         style={'fontSize': '18px', 'fontWeight': 'bold', 'textAlign': 'center', 'marginBottom': '15px', 'color': 'var(--text)'}),
                html.Div([
                    html.Div([ html.Div("Tackles", className="perf-label"), html.Div(id="most-tackles-total", children="--", className="perf-value") ]),
                    html.Div([ html.Div("Success %", className="perf-label"), html.Div(id="most-tackles-success", children="--", className="perf-value") ]),
                    html.Div([ html.Div("Position", className="perf-label"), html.Div(id="most-tackles-position", children="--", className="perf-value") ]),
                ], className="perf-stats-row"),
            ], className="performer-card"),

        ], className="metrics-row", style={'marginBottom': '30px'}), # Use metrics-row for 4 columns


        # -- Filters --
        html.Div([
            # Left group
            html.Div([
                html.Label("Position:", style={'marginRight': '5px', 'fontWeight': '500'}),
                dcc.Dropdown(
                    id="position-filter",
                    options=[{"label": "All Positions", "value": "all"}] +
                            ([{"label": pos, "value": pos} for pos in sorted(df["Pos"].astype(str).unique()) if pd.notna(pos) and pos != 'nan'] if "Pos" in df.columns else []),
                    value="all", clearable=False, style={'width': '180px', 'marginRight': '15px'}
                ),
                html.Label("Min Minutes:", style={'marginRight': '5px', 'fontWeight': '500'}),
                dcc.Dropdown(
                    id="min-minutes-filter",
                    options=[{"label": "Any", "value": 0},{"label": "90+", "value": 90},{"label": "270+", "value": 270},{"label": "450+", "value": 450},{"label": "900+", "value": 900}],
                    value=0, clearable=False, style={'width': '120px', 'marginRight': '15px'}
                ),
                 html.Label("Scope:", style={'marginRight': '5px', 'fontWeight': '500'}),
                 dcc.RadioItems( # Using RadioItems for better U23 toggle
                     id='u23-filter-toggle', # Changed ID slightly
                     options=[{'label': 'All Players', 'value': 'all'}, {'label': 'U23 Only', 'value': 'u23'}],
                     value='all', labelStyle={'display': 'inline-block', 'marginRight': '10px'}, inputStyle={'marginRight': '3px'}
                ),
            ], className="filter-group-left"),
            # Right group
            html.Div([
                dcc.Input(
                    id="player-search", type="text", placeholder="Search player name...", debounce=True,
                    style={'padding': '8px 12px', 'width': '220px', 'borderRadius': '4px', 'border': '1px solid var(--border)'}
                ),
            ], className="filter-group-right"),
        ], className="filter-container"),


        # -- Charts Section (2x2 Grid) --
        html.Div([
            html.Div([dcc.Graph(id="goals-chart", config={'displayModeBar': False})], className="chart-container"),
            html.Div([dcc.Graph(id="assisters-chart", config={'displayModeBar': False})], className="chart-container"),
            html.Div([dcc.Graph(id="minutes-chart", config={'displayModeBar': False})], className="chart-container"),
            html.Div([dcc.Graph(id="teams-chart", config={'displayModeBar': False})], className="chart-container"),
        ], className="charts-grid"),

        # -- Player Statistics Table --
        html.Div([
            html.H2("Player Statistics", style={'fontSize': '20px', 'fontWeight': '600', 'color': '#333', 'marginBottom': '15px', 'borderBottom': '1px solid #eee', 'paddingBottom': '10px'}),
            dash_table.DataTable(
                id="players-table", columns=[], data=[],
                style_table={'overflowX': 'auto', 'minWidth': '100%'},
                style_header={
                    'backgroundColor': 'var(--background)', 'fontWeight': 'bold', 'border': '1px solid var(--border)',
                    'padding': '10px', 'textAlign': 'left'
                },
                style_cell={
                    'padding': '10px', 'border': '1px solid var(--border)', 'textAlign': 'left',
                    'fontSize': '14px', 'minWidth': '80px', 'width': '120px', 'maxWidth': '180px',
                    'whiteSpace': 'normal', 'height': 'auto',
                },
                 style_cell_conditional=[
                    {'if': {'column_id': c}, 'textAlign': 'right'} for c in ['Age', 'MP', 'Min', 'Gls', 'Ast', 'Sh', 'SoT', 'SoT%', 'G/Sh', '90s', 'xG', 'KP', 'xA', 'Cmp', 'Tkl', 'Tkl%'] # Added new numeric cols
                 ],
                style_data={'border': '1px solid var(--border)'},
                style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 250)'}],
                page_size=15, sort_action='native', filter_action='native',
            )
        ], className="table-container"),

    ], id="content-overview", className="tab-content active"),
], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '20px'})


# --- Custom CSS ---
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>A-League U23 Analytics</title>
        <!-- Add Google Font Link -->
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600;1,700&display=swap" rel="stylesheet">
        {%favicon%}
        {%css%}
        <style>
            /* --- Global Styles & Variables --- */
            :root {
                --primary: #3182ce; --secondary: #e53e3e; --accent: #38a169;
                --background: #f7fafc; --card-bg: #ffffff; --text: #2d3748;
                --text-light: #718096; --border: #e2e8f0;
                --shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                --shadow-md: 0 6px 10px rgba(0, 0, 0, 0.07);
            }

            body {
                /* Set IBM Plex Sans as the default font */
                font-family: "IBM Plex Sans", sans-serif;
                background-color: var(--background);
                color: var(--text);
                margin: 0;
                padding: 0;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }

            /* Apply font to Plotly charts */
            .js-plotly-plot .plotly, .js-plotly-plot .plotly svg {
                font-family: "IBM Plex Sans", sans-serif !important;
            }

            /* --- Layout Classes --- */
            .tabs { display: flex; border-bottom: 1px solid var(--border); margin-bottom: 25px; }
            .tab { padding: 12px 20px; cursor: pointer; border-bottom: 3px solid transparent; font-weight: 500; color: var(--text-light); transition: all 0.2s ease-in-out; }
            .tab:hover { color: var(--text); }
            .tab.active { border-bottom-color: var(--primary); color: var(--primary); font-weight: 600; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }

            /* Metrics & Performer Row (4 columns) */
            .metrics-row {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); /* Responsive 4 columns */
                gap: 20px;
                margin-bottom: 30px;
                max-width: 1200px; /* Limit width */
                margin-left: auto;
                margin-right: auto;
            }

            .metric-card, .performer-card { /* Shared styles */
                background-color: var(--card-bg);
                border-radius: 8px;
                padding: 20px;
                box-shadow: var(--shadow);
                border: 1px solid var(--border);
                display: flex; /* Use flex for vertical alignment within card */
                flex-direction: column; /* Stack items vertically */
            }

            .metric-card { /* Specific metric card style */
                 text-align: center;
            }

            .metric-title { font-size: 14px; font-weight: 500; color: var(--text-light); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
            .metric-value { font-size: 28px; font-weight: 600; color: var(--primary); margin: 5px 0 8px 0; }
            .metric-subtitle { font-size: 13px; color: var(--text-light); }

            /* Performer Card specific styles */
            .performer-card {
                 padding: 15px; /* Slightly less padding than metrics */
            }

            /* New class for the row of stats inside performer cards */
            .perf-stats-row {
                 display: flex;
                 justify-content: space-around; /* Spread stats horizontally */
                 align-items: flex-start; /* Align tops */
                 margin-top: auto; /* Push stats to bottom if card height varies */
                 padding-top: 15px; /* Space above stats */
                 width: 100%; /* Take full width */
             }

             /* Individual stat block inside the row */
            .perf-stats-row > div {
                 text-align: center;
                 flex: 1; /* Allow equal sharing of space */
            }

             .perf-label { font-size: 13px; color: var(--text-light); margin-bottom: 4px; }
             .perf-value { font-size: 16px; font-weight: 600; color: var(--text); }

            /* Filter Container */
            .filter-container { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; margin-bottom: 25px; padding: 15px; background-color: var(--card-bg); border-radius: 6px; box-shadow: var(--shadow); border: 1px solid var(--border); max-width: 1200px; margin-left: auto; margin-right: auto;}
            .filter-group-left, .filter-group-right { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; }

            /* Charts Grid */
            .charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 30px; max-width: 1200px; margin-left: auto; margin-right: auto;}
            .chart-container { background-color: var(--card-bg); border-radius: 8px; padding: 15px; box-shadow: var(--shadow); border: 1px solid var(--border); }

            /* Table Container */
            .table-container { background-color: var(--card-bg); border-radius: 8px; padding: 20px; box-shadow: var(--shadow-md); border: 1px solid var(--border); margin-bottom: 30px; overflow-x: auto; max-width: 1200px; margin-left: auto; margin-right: auto;}

        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# --- Callbacks ---
# NOTE: The debug callback is removed as it wasn't present in the user's original final code block
@app.callback(
    [
        # Summary stats Outputs (8)
        Output('total-players-u23', 'children'), Output('total-players-pct', 'children'),
        Output('avg-age-u23', 'children'), Output('avg-age-all', 'children'),
        Output('total-goals-u23', 'children'), Output('total-goals-pct', 'children'),
        Output('total-assists-u23', 'children'), Output('total-assists-pct', 'children'),
        # Top scorer Outputs (4)
        Output('top-scorer-name', 'children'), Output('top-scorer-goals', 'children'),
        Output('top-scorer-xg', 'children'), Output('top-scorer-age', 'children'),
        # Best playmaker Outputs (4)
        Output('best-playmaker-name', 'children'), Output('best-playmaker-assists', 'children'),
        Output('best-playmaker-key-passes', 'children'), Output('best-playmaker-xa', 'children'),
        # Most passes Outputs (4) - NEW
        Output('most-passes-name', 'children'), Output('most-passes-total', 'children'),
        Output('most-passes-position', 'children'), Output('most-passes-age', 'children'),
        # Most tackles Outputs (4) - NEW
        Output('most-tackles-name', 'children'), Output('most-tackles-total', 'children'),
        Output('most-tackles-success', 'children'), Output('most-tackles-position', 'children'),
        # Chart Outputs (4)
        Output('goals-chart', 'figure'), Output('assisters-chart', 'figure'),
        Output('minutes-chart', 'figure'), Output('teams-chart', 'figure'),
        # Table Outputs (2)
        Output('players-table', 'data'), Output('players-table', 'columns'),
    ],
    [
        # Use the RadioItems ID for U23 scope
        Input('position-filter', 'value'), Input('min-minutes-filter', 'value'),
        Input('player-search', 'value'), Input('u23-filter-toggle', 'value'),
    ]
)
def update_dashboard(position, min_minutes, search_term, u23_scope): # Changed last input name
    # --- Input Validation & Data Check ---
    if df is None or df.empty:
        print("Callback triggered but DataFrame is empty.")
        empty_fig = go.Figure(layout={'title': 'No Data Available'})
        empty_fig.update_layout(font_family='"IBM Plex Sans", sans-serif')
        empty_table_cols = [{"name": "Info", "id": "info"}]
        empty_table_data = [{"info": "No data loaded to display."}]
        # Ensure return tuple length matches number of outputs (8+4+4+4+4+4+2 = 30)
        return ['--'] * 24 + [empty_fig] * 4 + [empty_table_data, empty_table_cols]

    print(f"\n--- Callback Update ---")
    print(f"Filters: Position='{position}', Min Minutes={min_minutes}, Search='{search_term}', Scope='{u23_scope}'")
    filtered_df = df.copy()

    # --- Apply Filters ---
    # Position
    if position and position != "all" and "Pos" in filtered_df.columns:
        filtered_df['Pos'] = filtered_df['Pos'].astype(str)
        filtered_df = filtered_df[filtered_df["Pos"].str.contains(position, case=False, na=False)]
    # Minutes
    if min_minutes and min_minutes > 0 and "Min" in filtered_df.columns:
        filtered_df['Min'] = pd.to_numeric(filtered_df['Min'], errors='coerce')
        filtered_df = filtered_df[filtered_df["Min"] >= min_minutes]
    # Search
    if search_term and "Player" in filtered_df.columns:
        filtered_df['Player'] = filtered_df['Player'].astype(str)
        filtered_df = filtered_df[filtered_df["Player"].str.contains(search_term, case=False, na=False)]

    # --- Calculate U23 Subset & Overall Stats ---
    if filtered_df.empty:
        print("Filtered DataFrame is empty.")
        empty_fig = go.Figure(layout={'title': 'No Matching Data'})
        empty_fig.update_layout(font_family='"IBM Plex Sans", sans-serif')
        empty_table_cols = [{"name": "Info", "id": "info"}]
        empty_table_data = [{"info": f"No players match the selected filters."}]
        return ['--'] * 24 + [empty_fig] * 4 + [empty_table_data, empty_table_cols]

    u23_subset_df = pd.DataFrame()
    if 'U23' in filtered_df.columns:
        u23_subset_df = filtered_df[filtered_df["U23"] == True].copy()
    else:
        print("Warning: 'U23' column missing.")

    # Overall stats
    total_players_filtered = len(filtered_df)
    total_goals_filtered = pd.to_numeric(filtered_df.get('Gls'), errors='coerce').sum()
    total_assists_filtered = pd.to_numeric(filtered_df.get('Ast'), errors='coerce').sum()
    avg_age_filtered = pd.to_numeric(filtered_df.get('Age'), errors='coerce').mean()
    # U23 stats
    total_players_u23 = len(u23_subset_df)
    total_goals_u23 = pd.to_numeric(u23_subset_df.get('Gls'), errors='coerce').sum()
    total_assists_u23 = pd.to_numeric(u23_subset_df.get('Ast'), errors='coerce').sum()
    avg_age_u23 = pd.to_numeric(u23_subset_df.get('Age'), errors='coerce').mean() if not u23_subset_df.empty else 0

    # Format strings
    players_pct_str = f"{(total_players_u23 / total_players_filtered * 100):.1f}% of {total_players_filtered}" if total_players_filtered > 0 else "0% of 0"
    goals_pct_str = f"{(total_goals_u23 / total_goals_filtered * 100):.1f}% of {int(total_goals_filtered)}" if total_goals_filtered > 0 else "0% of 0"
    assists_pct_str = f"{(total_assists_u23 / total_assists_filtered * 100):.1f}% of {int(total_assists_filtered)}" if total_assists_filtered > 0 else "0% of 0"
    avg_age_u23_str = f"{avg_age_u23:.1f}" if pd.notna(avg_age_u23) and avg_age_u23 > 0 else "--"
    avg_age_all_str = f"vs. {avg_age_filtered:.1f} overall" if pd.notna(avg_age_filtered) and avg_age_filtered > 0 else "vs. --"

    # --- Top U23 Performers ---
    top_scorer = {"name": "--", "goals": "--", "xg": "--", "age": "--"}
    best_playmaker = {"name": "--", "assists": "--", "key_passes": "--", "xa": "--"}
    most_passes = {"name": "--", "total": "--", "position": "--", "age": "--"}
    most_tackles = {"name": "--", "total": "--", "success": "--", "position": "--"}

    if not u23_subset_df.empty:
        # Top Scorer
        if 'Gls' in u23_subset_df.columns and u23_subset_df['Gls'].notna().any():
            try:
                sort_cols = ['Gls'] + (['Min'] if 'Min' in u23_subset_df.columns else [])
                scorer_data = u23_subset_df.sort_values(by=sort_cols, ascending=[False]*len(sort_cols), na_position='last').iloc[0]
                top_scorer["name"] = scorer_data.get("Player", "--")
                top_scorer["goals"] = int(scorer_data.get("Gls", 0)) if pd.notna(scorer_data.get("Gls")) else 0
                top_scorer["xg"] = f"{scorer_data.get('xG', 0):.1f}" if pd.notna(scorer_data.get("xG")) else "--"
                top_scorer["age"] = int(scorer_data.get("Age", 0)) if pd.notna(scorer_data.get("Age")) else "--"
            except IndexError: print("IndexError finding top scorer.")
            except Exception as e: print(f"Error finding top scorer: {e}")

        # Best Playmaker
        if 'Ast' in u23_subset_df.columns and u23_subset_df['Ast'].notna().any():
            try:
                sort_cols = ['Ast'] + (['KP'] if 'KP' in u23_subset_df.columns else []) + (['Min'] if 'Min' in u23_subset_df.columns else [])
                playmaker_data = u23_subset_df.sort_values(by=sort_cols, ascending=[False]*len(sort_cols), na_position='last').iloc[0]
                best_playmaker["name"] = playmaker_data.get("Player", "--")
                best_playmaker["assists"] = int(playmaker_data.get("Ast", 0)) if pd.notna(playmaker_data.get("Ast")) else 0
                best_playmaker["key_passes"] = int(playmaker_data.get("KP", 0)) if pd.notna(playmaker_data.get("KP")) else "--"
                best_playmaker["xa"] = f"{playmaker_data.get('xA', 0):.1f}" if pd.notna(playmaker_data.get("xA")) else "--"
            except IndexError: print("IndexError finding best playmaker.")
            except Exception as e: print(f"Error finding best playmaker: {e}")

        # Most Passes (** ADJUST 'Cmp' IF YOUR COLUMN NAME IS DIFFERENT **)
        passes_col = 'Cmp' # <---- *** CHECK YOUR CSV FOR PASSES COLUMN NAME ***
        if passes_col in u23_subset_df.columns and u23_subset_df[passes_col].notna().any():
            try:
                sort_cols = [passes_col] + (['Min'] if 'Min' in u23_subset_df.columns else [])
                passer_data = u23_subset_df.sort_values(by=sort_cols, ascending=[False]*len(sort_cols), na_position='last').iloc[0]
                most_passes["name"] = passer_data.get("Player", "--")
                most_passes["total"] = int(passer_data.get(passes_col, 0)) if pd.notna(passer_data.get(passes_col)) else 0
                most_passes["position"] = passer_data.get("Pos", "--")
                most_passes["age"] = int(passer_data.get("Age", 0)) if pd.notna(passer_data.get("Age")) else "--"
            except IndexError: print(f"IndexError finding most passes ({passes_col}).")
            except Exception as e: print(f"Error finding most passes: {e}")
        else:
             print(f"Column '{passes_col}' not found or no data for Most Passes card.")

        # Most Tackles (** ADJUST 'Tkl' AND 'Tkl%' IF NEEDED **)
        tackles_col = 'Tkl'     # <---- *** CHECK YOUR CSV FOR TACKLES COLUMN NAME ***
        tackles_pct_col = 'Tkl%' # <---- *** CHECK YOUR CSV FOR TACKLE % COLUMN NAME ***
        if tackles_col in u23_subset_df.columns and u23_subset_df[tackles_col].notna().any():
             try:
                sort_cols = [tackles_col] + (['Min'] if 'Min' in u23_subset_df.columns else [])
                tackler_data = u23_subset_df.sort_values(by=sort_cols, ascending=[False]*len(sort_cols), na_position='last').iloc[0]
                most_tackles["name"] = tackler_data.get("Player", "--")
                most_tackles["total"] = int(tackler_data.get(tackles_col, 0)) if pd.notna(tackler_data.get(tackles_col)) else 0
                # Format percentage if available
                if tackles_pct_col in tackler_data and pd.notna(tackler_data.get(tackles_pct_col)):
                    most_tackles["success"] = f"{tackler_data.get(tackles_pct_col):.1f}%"
                else:
                    most_tackles["success"] = "--"
                most_tackles["position"] = tackler_data.get("Pos", "--")
             except IndexError: print(f"IndexError finding most tackles ({tackles_col}).")
             except Exception as e: print(f"Error finding most tackles: {e}")
        else:
             print(f"Column '{tackles_col}' not found or no data for Most Tackles card.")


    # --- Determine Data for Charts & Table ---
    if u23_scope == 'u23':
        viz_df = u23_subset_df
        chart_title_suffix = " (U23 Only)"
    else:
        viz_df = filtered_df
        chart_title_suffix = " (Filtered)"

    plotly_font = dict(family='"IBM Plex Sans", sans-serif')

    if viz_df.empty:
         print(f"Viz DataFrame ('{u23_scope}') empty.")
         empty_fig = go.Figure(layout={'title': f'No Data for Scope: {u23_scope}'})
         empty_fig.update_layout(font=plotly_font)
         empty_table_cols = [{"name": "Info", "id": "info"}]
         empty_table_data = [{"info": f"No players match filters in '{u23_scope}' scope."}]
         return (
             total_players_u23, players_pct_str, avg_age_u23_str, avg_age_all_str,
             int(total_goals_u23), goals_pct_str, int(total_assists_u23), assists_pct_str,
             top_scorer["name"], top_scorer["goals"], top_scorer["xg"], top_scorer["age"],
             best_playmaker["name"], best_playmaker["assists"], best_playmaker["key_passes"], best_playmaker["xa"],
             most_passes["name"], most_passes["total"], most_passes["position"], most_passes["age"], # Pass values
             most_tackles["name"], most_tackles["total"], most_tackles["success"], most_tackles["position"], # Tackle values
             empty_fig, empty_fig, empty_fig, empty_fig,
             empty_table_data, empty_table_cols
         )

    # --- Create Charts ---
    chart_height = 350
    chart_margin = dict(l=10, r=10, t=60, b=10)
    hover_template_player = '<b>%{y}</b><br>Squad: %{customdata[0]}<br>%{label}: %{x}<extra></extra>'
    unique_teams = viz_df["Squad"].unique() if "Squad" in viz_df.columns else []
    color_map = {team: get_team_color(team) for team in unique_teams}

    def create_empty_figure(title):
        fig = go.Figure()
        fig.add_annotation(text="No data for this chart", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14))
        fig.update_layout(title=title, height=chart_height, margin=chart_margin, font=plotly_font)
        return fig

    # Define assist column for charts
    assist_col_chart = 'Ast' if 'Ast' in viz_df.columns else None

    # 1. Goals Chart
    goals_fig = create_empty_figure(f'Top 10 Goal Scorers{chart_title_suffix}')
    if 'Gls' in viz_df.columns and viz_df['Gls'].notna().sum() > 0:
        goals_data = viz_df[['Player', 'Gls', 'Squad']].dropna(subset=['Gls']).nlargest(10, 'Gls').sort_values('Gls', ascending=True)
        if not goals_data.empty:
             goals_fig = px.bar(goals_data, x='Gls', y='Player', orientation='h', title=f'Top 10 Goal Scorers{chart_title_suffix}',
                                color='Squad', color_discrete_map=color_map, labels={'Gls': 'Goals', 'Player': ''}, height=chart_height, custom_data=['Squad'])
             goals_fig.update_traces(hovertemplate=hover_template_player.replace('%{label}', 'Goals'))
             goals_fig.update_layout(margin=chart_margin, yaxis={'categoryorder':'total ascending'}, font=plotly_font)

    # 2. Assists Chart
    assisters_fig = create_empty_figure(f'Top 10 Assist Providers{chart_title_suffix}')
    if assist_col_chart and viz_df[assist_col_chart].notna().sum() > 0:
        assists_data = viz_df[['Player', assist_col_chart, 'Squad']].dropna(subset=[assist_col_chart]).nlargest(10, assist_col_chart).sort_values(assist_col_chart, ascending=True)
        if not assists_data.empty:
            assisters_fig = px.bar(assists_data, x=assist_col_chart, y='Player', orientation='h', title=f'Top 10 Assist Providers{chart_title_suffix}',
                                   color='Squad', color_discrete_map=color_map, labels={assist_col_chart: 'Assists', 'Player': ''}, height=chart_height, custom_data=['Squad'])
            assisters_fig.update_traces(hovertemplate=hover_template_player.replace('%{label}', 'Assists'))
            assisters_fig.update_layout(margin=chart_margin, yaxis={'categoryorder':'total ascending'}, font=plotly_font)

    # 3. Minutes Chart
    minutes_fig = create_empty_figure(f'Top 10 Minutes Played{chart_title_suffix}')
    if 'Min' in viz_df.columns and viz_df['Min'].notna().sum() > 0:
        minutes_data = viz_df[['Player', 'Min', 'Squad']].dropna(subset=['Min']).nlargest(10, 'Min').sort_values('Min', ascending=True)
        if not minutes_data.empty:
            minutes_fig = px.bar(minutes_data, x='Min', y='Player', orientation='h', title=f'Top 10 Minutes Played{chart_title_suffix}',
                                 color='Squad', color_discrete_map=color_map, labels={'Min': 'Minutes', 'Player': ''}, height=chart_height, custom_data=['Squad'])
            minutes_fig.update_traces(hovertemplate=hover_template_player.replace('%{label}', 'Minutes'))
            minutes_fig.update_layout(margin=chart_margin, yaxis={'categoryorder':'total ascending'}, font=plotly_font)

    # 4. Team Goals Chart
    teams_fig = create_empty_figure(f'Total Goals by Team{chart_title_suffix}')
    if 'Gls' in viz_df.columns and 'Squad' in viz_df.columns and viz_df['Gls'].notna().sum() > 0:
        team_goals_data = viz_df.dropna(subset=['Squad', 'Gls']).groupby('Squad')['Gls'].sum().reset_index().sort_values('Gls', ascending=True)
        if not team_goals_data.empty:
             teams_fig = px.bar(team_goals_data, x='Gls', y='Squad', orientation='h', title=f'Total Goals by Team{chart_title_suffix}',
                           color='Squad', color_discrete_map=color_map, labels={'Gls': 'Total Goals', 'Squad': ''}, height=chart_height)
             teams_fig.update_traces(hovertemplate='<b>%{y}</b><br>Total Goals: %{x}<extra></extra>')
             teams_fig.update_layout(margin=chart_margin, yaxis={'categoryorder':'total ascending'}, font=plotly_font)

    # --- Prepare Table Data ---
    table_cols_ordered = ['Player', 'Pos', 'Squad', 'Age', 'MP', 'Min', 'Gls', 'Ast', 'Sh', 'SoT', 'SoT%', 'G/Sh', 'xG', 'KP', 'xA', '90s', 'Cmp', 'Tkl', 'Tkl%'] # Added new cols
    table_cols_display = [col for col in table_cols_ordered if col in viz_df.columns]
    table_data = []
    table_columns = [{"name": "Info", "id": "info"}]

    if table_cols_display:
        table_data_df = viz_df[table_cols_display].copy()
        # Formatting (keep as before, add new cols)
        for col in ['SoT%', 'G/Sh', 'xG', 'xA', '90s', 'Tkl%']: # Added Tkl%
             if col in table_data_df.columns:
                 # Ensure numeric before formatting
                 table_data_df[col] = pd.to_numeric(table_data_df[col], errors='coerce')
                 table_data_df[col] = table_data_df[col].map('{:.1f}'.format, na_action='ignore')
                 # Re-add % sign if needed
                 if col == 'Tkl%':
                      table_data_df[col] = table_data_df[col].astype(str) + '%'
        for col in ['Age', 'MP', 'Min', 'Gls', 'Ast', 'Sh', 'SoT', 'KP', 'Cmp', 'Tkl']: # Added Cmp, Tkl
             if col in table_data_df.columns:
                 table_data_df[col] = pd.to_numeric(table_data_df[col], errors='coerce').astype('Int64').map('{:.0f}'.format, na_action='ignore')

        # Sorting (keep default sort by Gls or fallback)
        sort_column = 'Gls' if 'Gls' in table_data_df.columns else ('Min' if 'Min' in table_data_df.columns else table_cols_display[0])
        sort_ascending = False
        sort_column_numeric = sort_column + '_sort'
        if sort_column in table_data_df.columns:
             # Sort using original numeric data before formatting
             table_data_df[sort_column_numeric] = pd.to_numeric(viz_df[sort_column], errors='coerce')
             table_data_sorted = table_data_df.sort_values(by=sort_column_numeric, ascending=sort_ascending, na_position='last').drop(columns=[sort_column_numeric])
        else:
             table_data_sorted = table_data_df

        table_data = table_data_sorted.to_dict('records')
        table_columns = [{"name": col, "id": col} for col in table_cols_display]
    else:
        table_data = [{"info": "No displayable columns found."}]


    print("Dashboard update complete.")

    # Return all values in the correct order matching the Outputs list
    return (
        # Summary Stats (8)
        f"{total_players_u23}", players_pct_str, avg_age_u23_str, avg_age_all_str,
        f"{int(total_goals_u23)}", goals_pct_str, f"{int(total_assists_u23)}", assists_pct_str,
        # Top scorer (4)
        top_scorer["name"], top_scorer["goals"], top_scorer["xg"], top_scorer["age"],
        # Best playmaker (4)
        best_playmaker["name"], best_playmaker["assists"], best_playmaker["key_passes"], best_playmaker["xa"],
        # Most passes (4)
        most_passes["name"], most_passes["total"], most_passes["position"], most_passes["age"],
        # Most tackles (4)
        most_tackles["name"], most_tackles["total"], most_tackles["success"], most_tackles["position"],
        # Charts (4)
        goals_fig, assisters_fig, minutes_fig, teams_fig,
        # Table (2)
        table_data, table_columns
    )

# --- Function to open browser (keep as is) ---
def open_browser(port=8051):
    try:
        webbrowser.open_new(f"http://127.0.0.1:{port}/")
    except Exception as e:
        print(f"Could not automatically open browser: {e}")

# --- Run the App (keep as is) ---
if __name__ == '__main__':
    port = 8051
    print(f"--- Starting A-League Dashboard ---")
    print(f"Attempting to launch on: http://127.0.0.1:{port}/")
    Timer(1.5, lambda: open_browser(port)).start()
    # Use debug=True for development to see errors in browser
    # Use debug=False for 'production' or sharing
    app.run(debug=True, port=port)
