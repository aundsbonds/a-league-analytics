import dash
from dash import dcc, html, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import webbrowser
from threading import Timer

# Load the already processed data
df = pd.read_csv("a_league_processed/standard_stats_processed.csv")

# Create a dictionary of team colors (based on real A-League team colors)
team_colors = {
    'Adelaide': '#9b2633',  # dimmed red
    'Auckland FC': '#145a7d',  # muted teal blue
    'Brisbane': '#b76d10',  # muted orange
    'Central Coast': '#d0af4c',  # softened yellow
    'Macarthur FC': '#313131',  # dark gray/black
    'Melb City': '#6295c3',  # sky blue
    'Melb Victory': '#1a3a7c',  # deep navy blue
    'Newcastle': '#d1a03e',  # gold (using only the main color)
    'Perth Glory': '#4f2c7d',  # muted purple
    'Sydney FC': '#4b77b8',  # dimmed blue
    'W Sydney': '#bc3034',  # muted red
    'Wellington': '#c3a023',  # toned-down yellow
    'Western United': '#2d5234',  # dimmed green
    'Western Sydney Wanderers': '#bc3034'  # muted red
}

# Create the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Custom CSS to match your design
app.layout = html.Div([
    html.H1("A-League Mens - Under 23 Player Analysis",
            style={'textAlign': 'center', 'color': '#3182ce', 'marginBottom': '30px', 'fontSize': '28px', 'fontWeight': '700'}),
    
    # Tabs
    html.Div([
        html.Div("Overview", id="tab-overview", className="tab active", **{'data-tab': 'overview'}),
        html.Div("Player Market Value [wip]", id="tab-scorers", className="tab", **{'data-tab': 'scorers'}),
        html.Div("On-Ball Value (OBV) [wip]", id="tab-assisters", className="tab", **{'data-tab': 'assisters'}),
        html.Div("Passing Stats [wip]", id="tab-minutes", className="tab", **{'data-tab': 'minutes'}),
        html.Div("Shooting Stats [wip]", id="tab-teams", className="tab", **{'data-tab': 'teams'}),
    ], className="tabs"),
    
    # Overview Tab Content
    html.Div([
        # Summary Stats
        html.Div([
            html.Div([
                html.Div("Total Players", className="metric-title"),
                html.Div(id="total-players", className="metric-value"),
                html.Div("Total Players Under 23", className="metric-title", style={'fontSize': '0.8em', 'color': '#718096'}), # Added U23
                html.Div(id="total-players-u23", className="metric-value", style={'fontSize': '1.2em', 'color': '#3182ce'}), # Added U23
            ], className="metric-card"),

            html.Div([
                html.Div("Total Goals", className="metric-title"),
                html.Div(id="total-goals", className="metric-value"),
                html.Div("Total Goals Under 23", className="metric-title", style={'fontSize': '0.8em', 'color': '#718096'}), # Added U23
                html.Div(id="total-goals-u23", className="metric-value", style={'fontSize': '1.2em', 'color': '#3182ce'}), # Added U23
            ], className="metric-card"),

            html.Div([
                html.Div("Total Assists", className="metric-title"),
                html.Div(id="total-assists", className="metric-value"),
                html.Div("Total Assists Under 23", className="metric-title", style={'fontSize': '0.8em', 'color': '#718096'}), # Added U23
                html.Div(id="total-assists-u23", className="metric-value", style={'fontSize': '1.2em', 'color': '#3182ce'}), # Added U23
            ], className="metric-card"),

            html.Div([
                html.Div("Total Minutes", className="metric-title"),
                html.Div(id="total-minutes", className="metric-value"),
                html.Div("Total Minutes Under 23", className="metric-title", style={'fontSize': '0.8em', 'color': '#718096'}), # Added U23
                html.Div(id="total-minutes-u23", className="metric-value", style={'fontSize': '1.2em', 'color': '#3182ce'}), # Added U23
            ], className="metric-card"),
        ], className="metrics-row"),
        
        # Charts
        html.Div([
            html.Div([
                dcc.Graph(id="goals-chart")
            ], className="chart-container"),
            
            html.Div([
                dcc.Graph(id="assisters-chart")
            ], className="chart-container"),
            
            html.Div([
                dcc.Graph(id="minutes-chart")
            ], className="chart-container"),
            
            html.Div([
                dcc.Graph(id="teams-chart")
            ], className="chart-container"),
        ], className="dashboard-container"),
        
        # Filters
        html.Div([
            html.Div([
                html.Label("Position:", style={'marginRight': '10px'}),
                dcc.Dropdown(
                    id="position-filter",
                    options=[{"label": "All Positions", "value": "all"}] +
                            [{"label": pos, "value": pos} for pos in df["Pos"].unique() if pd.notna(pos)],
                    value="all",
                    style={'width': '200px'}
                ),
                
                html.Label("Min Minutes:", style={'marginLeft': '15px', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id="min-minutes-filter",
                    options=[
                        {"label": "All", "value": 0},
                        {"label": "90+", "value": 90},
                        {"label": "270+", "value": 270},
                        {"label": "450+", "value": 450},
                        {"label": "900+", "value": 900},
                    ],
                    value=0,
                    style={'width': '150px'}
                ),
                html.Label("Under 23 Only:", style={'marginLeft': '15px', 'marginRight': '10px'}), # Added U23 Filter
                dcc.Checklist(
                    id="u23-filter",
                    options=[
                        {"label": "Yes", "value": "yes"},
                    ],
                    value=[],
                    style={'width': '50px'}
                ),
            ], className="filter-group"),
            
            html.Div([
                dcc.Input(
                    id="player-search",
                    type="text",
                    placeholder="Search players...",
                    style={'padding': '8px 12px', 'width': '200px', 'borderRadius': '4px', 'border': '1px solid #e2e8f0'}
                ),
            ], className="filter-group"),
        ], className="filter-container"),
        
        # Players Table
        html.Div([
            html.H2("Player Statistics"),
            dash_table.DataTable(
                id="players-table",
                style_table={'overflowX': 'auto'},
                style_header={
                    'backgroundColor': 'rgb(240, 240, 240)',
                    'fontWeight': 'bold',
                    'border': '1px solid #e2e8f0'
                },
                style_cell={
                    'padding': '10px',
                    'border': '1px solid #e2e8f0',
                    'textAlign': 'left'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 250, 252)'
                    }
                ]
            )
        ], className="table-container"),
        
    ], id="content-overview", className="tab-content active"),
    
    # Tab content for other tabs would go here
    
], style={
    'fontFamily': 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
    'margin': '0',
    'padding': '20px',
    'backgroundColor': '#f7fafc',
    'color': '#2d3748',
})

# Add CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>A-League Analytics Dashboard</title>
        {%favicon%}
        {%css%}
        <style>
            :root {
                --primary: #3182ce;
                --secondary: #e53e3e;
                --accent: #38a169;
                --background: #f7fafc;
                --card-bg: #ffffff;
                --text: #2d3748;
                --text-light: #718096;
                --border: #e2e8f0;
                --shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            }
            
            .tabs {
                display: flex;
                border-bottom: 1px solid var(--border);
                margin-bottom: 20px;
            }
            
            .tab {
                padding: 10px 20px;
                cursor: pointer;
                border-bottom: 2px solid transparent;
                font-weight: 500;
            }
            
            .tab.active {
                border-bottom: 2px solid var(--primary);
                color: var(--primary);
            }
            
            .tab-content {
                display: none;
            }
            
            .tab-content.active {
                display: block;
            }
            
            .metrics-row {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .metric-card {
                background-color: var(--card-bg);
                border-radius: 8px;
                padding: 15px;
                box-shadow: var(--shadow);
                text-align: center;
            }
            
            .metric-value {
                font-size: 24px;
                font-weight: 700;
                color: var(--primary);
                margin: 10px 0;
            }
            
            .metric-title {
                font-size: 14px;
                color: var(--text-light);
            }
            
            .dashboard-container {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .chart-container {
                background-color: var(--card-bg);
                border-radius: 8px;
                padding: 20px;
                box-shadow: var(--shadow);
            }
            
            .table-container {
                background-color: var(--card-bg);
                border-radius: 8px;
                padding: 20px;
                box-shadow: var(--shadow);
                overflow-x: auto;
            }
            
            .filter-container {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                flex-wrap: wrap;
                gap: 10px;
            }
            
            .filter-group {
                display: flex;
                align-items: center;
            }
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

# Function to get color for team
def get_team_color(team):
    # Default color if team not found
    default_color = '#808080'  # Gray
    return team_colors.get(team, default_color)

# Callback to update charts and tables when filters change
@app.callback(
    [
        # Summary metric outputs
        dash.dependencies.Output('total-players', 'children'),
        dash.dependencies.Output('total-goals', 'children'),
        dash.dependencies.Output('total-assists', 'children'),
        dash.dependencies.Output('total-minutes', 'children'),
        
        # Chart outputs
        dash.dependencies.Output('goals-chart', 'figure'),
        dash.dependencies.Output('assisters-chart', 'figure'),
        dash.dependencies.Output('minutes-chart', 'figure'),
        dash.dependencies.Output('teams-chart', 'figure'),
        
        # Table output
        dash.dependencies.Output('players-table', 'data'),
        dash.dependencies.Output('players-table', 'columns'),
    ],
    [
        dash.dependencies.Input('position-filter', 'value'),
        dash.dependencies.Input('min-minutes-filter', 'value'),
        dash.dependencies.Input('player-search', 'value'),
    ]
)
def update_dashboard(position, min_minutes, search_term):
    # Filter data based on inputs
    filtered_data = df.copy()
    
    # Position filter
    if position != "all" and position is not None:
        filtered_data = filtered_data[filtered_data["Pos"] == position]
    
    # Minutes filter
    if min_minutes > 0:
        filtered_data = filtered_data[filtered_data["Min"] >= min_minutes]


    
    # Search filter
    if search_term:
        filtered_data = filtered_data[filtered_data["Player"].str.contains(search_term, case=False)]
    
    # Calculate summary metrics
    total_players = len(filtered_data)
    total_goals = filtered_data["Gls"].sum()
    
    # Handle 'Ast' which might be in different columns
    assist_col = None
    for col in ['Ast', 'Ast.1']:
        if col in filtered_data.columns:
            assist_col = col
            break
            
    total_assists = filtered_data[assist_col].sum() if assist_col else 0
    total_minutes = filtered_data["Min"].sum()
    
    # Create a color mapping based on teams
    teams = filtered_data["Squad"].unique()
    color_discrete_map = {team: get_team_color(team) for team in teams}
    
    # Create charts
    # 1. Goals Chart
    top_scorers = filtered_data.nlargest(10, "Gls").sort_values("Gls")
    goals_fig = px.bar(
        top_scorers,
        x="Gls",
        y="Player",
        orientation="h",
        title="Top 10 Goal Scorers",
        color="Squad",
        color_discrete_map=color_discrete_map,
        labels={"Gls": "Goals", "Player": "Player"},
        height=400
    )
    goals_fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    
    # 2. Assists Chart
    if assist_col:
        top_assisters = filtered_data.nlargest(10, assist_col).sort_values(assist_col)
        assisters_fig = px.bar(
            top_assisters,
            x=assist_col,
            y="Player",
            orientation="h",
            title="Top 10 Assist Providers",
            color="Squad",
            color_discrete_map=color_discrete_map,
            labels={assist_col: "Assists", "Player": "Player"},
            height=400
        )
    else:
        # Fallback if no assist column
        assisters_fig = go.Figure()
        assisters_fig.update_layout(title="Assist data not available")
    
    assisters_fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    
    # 3. Minutes Chart
    top_minutes = filtered_data.nlargest(10, "Min").sort_values("Min")
    minutes_fig = px.bar(
        top_minutes,
        x="Min",
        y="Player",
        orientation="h",
        title="Top 10 Players by Minutes Played",
        color="Squad",
        color_discrete_map=color_discrete_map,
        labels={"Min": "Minutes Played", "Player": "Player"},
        height=400
    )
    minutes_fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    
    # 4. Team Goals Chart
    team_goals = filtered_data.groupby("Squad")["Gls"].sum().reset_index().sort_values("Gls")
    teams_fig = px.bar(
        team_goals,
        x="Gls",
        y="Squad",
        orientation="h",
        title="Teams by Total Goals",
        color="Squad",
        color_discrete_map=color_discrete_map,
        labels={"Gls": "Total Goals", "Squad": "Team"},
        height=400
    )
    teams_fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    
    # Prepare table data
    clean_df = filtered_data.copy()
    if 'Min' in clean_df.columns:
        clean_df['Min'] = pd.to_numeric(clean_df['Min'], errors='coerce')
        # Replace NaN with empty string for display
        clean_df['Min'] = clean_df['Min'].fillna('').astype(str)
        # Remove decimal part if it's just .0
        clean_df['Min'] = clean_df['Min'].apply(lambda x: x.replace('.0', '') if x.endswith('.0') else x)

    table_data = clean_df.sort_values("Gls", ascending=False).to_dict('records')
    
    # Define table columns
    table_columns = [
        {"name": "Player", "id": "Player"},
        {"name": "Pos", "id": "Pos"},
        {"name": "Squad", "id": "Squad"},
        {"name": "Age", "id": "Age"},
        {"name": "MP", "id": "MP"},
        {"name": "Min", "id": "Min"},
        {"name": "Goals", "id": "Gls"}
    ]
    
    # Add assists column if it exists
    if assist_col:
        table_columns.append({"name": "Ast", "id": assist_col})
    
    # Add 90s column if it exists
    if '90s' in filtered_data.columns:
        table_columns.append({"name": "90s", "id": "90s"})
    
    return total_players, total_goals, total_assists, f"{total_minutes:,}", goals_fig, assisters_fig, minutes_fig, teams_fig, table_data, table_columns

# Function to open the browser automatically
def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050/")

# Run this after the app
if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(debug=False)
