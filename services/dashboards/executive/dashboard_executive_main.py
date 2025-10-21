"""
TUS Engage Tool Pilot - Executive Dashboard
High-detail dashboard for executive users (Presidents, VPs, Deans, HODs)

This dashboard provides comprehensive analytics and detailed data views
for executive-level decision making.

Author: TUS Development Team
Date: October 2025
License: See LICENSE file
"""

import os
import logging
from datetime import datetime, timedelta
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from flask import Flask, request, jsonify, redirect
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://tusadmin:changeme@database:5432/tus_engage_db')
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)

# Initialize Flask server
server = Flask(__name__)
server.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
server.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
server.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
server.config['JWT_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
server.config['JWT_COOKIE_CSRF_PROTECT'] = False

# Initialize JWT
jwt = JWTManager(server)

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    server=server,
    url_base_pathname='/dashboard/',
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    title='TUS Executive Dashboard'
)


# ============================================
# AUTHENTICATION ROUTES
# ============================================

@server.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'executive_dashboard', 'version': '1.0.0'}), 200


@server.route('/api/auth/validate', methods=['POST'])
@jwt_required()
def validate_token():
    """Validate JWT token and check role"""
    try:
        claims = get_jwt()
        user_role = claims.get('role', 'public')
        
        # Executive dashboard requires executive or admin role
        if user_role not in ['executive', 'admin']:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        return jsonify({
            'valid': True,
            'user_id': get_jwt_identity(),
            'role': user_role
        }), 200
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return jsonify({'error': 'Invalid token'}), 401


# ============================================
# DATA LOADING FUNCTIONS
# ============================================

def load_dashboard_data():
    """
    Load data from materialized view for executive dashboard
    
    Returns:
        pd.DataFrame: Dashboard data
    """
    try:
        query = """
        SELECT 
            data_id,
            submission_date,
            department,
            category,
            data_fields,
            original_filename,
            uploaded_at,
            uploaded_by_name,
            uploader_role
        FROM mv_executive_dashboard
        ORDER BY submission_date DESC
        LIMIT 10000
        """
        
        df = pd.read_sql(query, engine)
        logger.info(f"Loaded {len(df)} records for executive dashboard")
        return df
    
    except Exception as e:
        logger.error(f"Error loading dashboard data: {str(e)}")
        return pd.DataFrame()


def get_summary_stats():
    """
    Get summary statistics for dashboard
    
    Returns:
        dict: Summary statistics
    """
    try:
        query = """
        SELECT 
            COUNT(DISTINCT data_id) as total_records,
            COUNT(DISTINCT department) as total_departments,
            COUNT(DISTINCT category) as total_categories,
            COUNT(DISTINCT DATE_TRUNC('month', submission_date)) as months_covered
        FROM mv_executive_dashboard
        """
        
        result = pd.read_sql(query, engine)
        return result.iloc[0].to_dict() if not result.empty else {}
    
    except Exception as e:
        logger.error(f"Error loading summary stats: {str(e)}")
        return {}


# ============================================
# DASHBOARD LAYOUT
# ============================================

def create_navbar():
    """Create navigation bar"""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col(html.Img(src="/assets/logo.png", height="40px") if os.path.exists("assets/logo.png") else None),
                dbc.Col(dbc.NavbarBrand("TUS Executive Dashboard", className="ms-2")),
            ], align="center", className="g-0"),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("Overview", href="#overview")),
                    dbc.NavItem(dbc.NavLink("Analytics", href="#analytics")),
                    dbc.NavItem(dbc.NavLink("Data Table", href="#data")),
                ], className="ms-auto", navbar=True),
                id="navbar-collapse",
                navbar=True,
            ),
        ], fluid=True),
        color="primary",
        dark=True,
        className="mb-4"
    )


def create_summary_cards(stats):
    """Create summary statistics cards"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4([html.I(className="fas fa-database me-2"), "Total Records"]),
                    html.H2(f"{stats.get('total_records', 0):,}", className="text-primary")
                ])
            ], className="shadow-sm")
        ], width=12, md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4([html.I(className="fas fa-building me-2"), "Departments"]),
                    html.H2(f"{stats.get('total_departments', 0)}", className="text-success")
                ])
            ], className="shadow-sm")
        ], width=12, md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4([html.I(className="fas fa-tags me-2"), "Categories"]),
                    html.H2(f"{stats.get('total_categories', 0)}", className="text-info")
                ])
            ], className="shadow-sm")
        ], width=12, md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4([html.I(className="fas fa-calendar me-2"), "Months"]),
                    html.H2(f"{stats.get('months_covered', 0)}", className="text-warning")
                ])
            ], className="shadow-sm")
        ], width=12, md=3),
    ], className="mb-4")


app.layout = dbc.Container([
    # Store for data
    dcc.Store(id='dashboard-data-store'),
    dcc.Interval(id='interval-component', interval=60*1000, n_intervals=0),  # Update every minute
    
    # Navigation
    create_navbar(),
    
    # Summary Cards
    html.Div(id='summary-cards'),
    
    # Filters Section
    dbc.Card([
        dbc.CardHeader(html.H5("Filters")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Department"),
                    dcc.Dropdown(id='department-filter', multi=True, placeholder="All Departments")
                ], width=12, md=4),
                
                dbc.Col([
                    html.Label("Category"),
                    dcc.Dropdown(id='category-filter', multi=True, placeholder="All Categories")
                ], width=12, md=4),
                
                dbc.Col([
                    html.Label("Date Range"),
                    dcc.DatePickerRange(
                        id='date-range-filter',
                        start_date_placeholder_text="Start Date",
                        end_date_placeholder_text="End Date"
                    )
                ], width=12, md=4),
            ])
        ])
    ], className="mb-4 shadow-sm"),
    
    # Charts Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Submissions by Department")),
                dbc.CardBody([dcc.Graph(id='department-chart')])
            ], className="shadow-sm")
        ], width=12, md=6, className="mb-4"),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Submissions Over Time")),
                dbc.CardBody([dcc.Graph(id='timeline-chart')])
            ], className="shadow-sm")
        ], width=12, md=6, className="mb-4"),
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Category Distribution")),
                dbc.CardBody([dcc.Graph(id='category-chart')])
            ], className="shadow-sm")
        ], width=12, className="mb-4"),
    ]),
    
    # Data Table Section
    dbc.Card([
        dbc.CardHeader(html.H5("Detailed Data")),
        dbc.CardBody([
            html.Div(id='data-table')
        ])
    ], className="shadow-sm mb-4"),
    
    # Footer
    html.Footer([
        html.Hr(),
        html.P("© 2025 TUS Engage Tool - Executive Dashboard", className="text-center text-muted")
    ])
], fluid=True)


# ============================================
# CALLBACKS
# ============================================

@app.callback(
    [Output('dashboard-data-store', 'data'),
     Output('summary-cards', 'children'),
     Output('department-filter', 'options'),
     Output('category-filter', 'options')],
    [Input('interval-component', 'n_intervals')]
)
def load_data(n):
    """Load and cache dashboard data"""
    df = load_dashboard_data()
    stats = get_summary_stats()
    
    # Create filter options
    dept_options = [{'label': d, 'value': d} for d in sorted(df['department'].dropna().unique())] if not df.empty else []
    cat_options = [{'label': c, 'value': c} for c in sorted(df['category'].dropna().unique())] if not df.empty else []
    
    return df.to_dict('records'), create_summary_cards(stats), dept_options, cat_options


@app.callback(
    [Output('department-chart', 'figure'),
     Output('timeline-chart', 'figure'),
     Output('category-chart', 'figure'),
     Output('data-table', 'children')],
    [Input('dashboard-data-store', 'data'),
     Input('department-filter', 'value'),
     Input('category-filter', 'value'),
     Input('date-range-filter', 'start_date'),
     Input('date-range-filter', 'end_date')]
)
def update_charts(data, selected_depts, selected_cats, start_date, end_date):
    """Update all charts based on filters"""
    if not data:
        empty_fig = go.Figure()
        empty_fig.update_layout(title="No data available")
        return empty_fig, empty_fig, empty_fig, html.P("No data available")
    
    df = pd.DataFrame(data)
    
    # Apply filters
    if selected_depts:
        df = df[df['department'].isin(selected_depts)]
    if selected_cats:
        df = df[df['category'].isin(selected_cats)]
    if start_date:
        df = df[pd.to_datetime(df['submission_date']) >= start_date]
    if end_date:
        df = df[pd.to_datetime(df['submission_date']) <= end_date]
    
    # Department chart
    dept_counts = df['department'].value_counts().reset_index()
    dept_counts.columns = ['department', 'count']
    dept_fig = px.bar(dept_counts, x='department', y='count', title="Submissions by Department")
    
    # Timeline chart
    df['submission_date'] = pd.to_datetime(df['submission_date'])
    timeline_data = df.groupby(df['submission_date'].dt.to_period('M')).size().reset_index()
    timeline_data.columns = ['month', 'count']
    timeline_data['month'] = timeline_data['month'].astype(str)
    timeline_fig = px.line(timeline_data, x='month', y='count', title="Submissions Over Time", markers=True)
    
    # Category chart
    cat_counts = df['category'].value_counts().reset_index()
    cat_counts.columns = ['category', 'count']
    cat_fig = px.pie(cat_counts, values='count', names='category', title="Category Distribution")
    
    # Data table
    table_df = df[['submission_date', 'department', 'category', 'uploaded_by_name']].head(100)
    table = dbc.Table.from_dataframe(table_df, striped=True, bordered=True, hover=True, responsive=True)
    
    return dept_fig, timeline_fig, cat_fig, table


# ============================================
# RUN APPLICATION
# ============================================

if __name__ == '__main__':
    host = os.getenv('DASH_HOST', '0.0.0.0')
    port = int(os.getenv('DASH_PORT', 8050))
    debug = os.getenv('DASH_ENV', 'production') == 'development'
    
    logger.info(f"Starting Executive Dashboard on {host}:{port}")
    app.run_server(host=host, port=port, debug=debug)
