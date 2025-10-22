"""
TUS Engage Tool Pilot - Staff Dashboard
Medium-detail dashboard for staff and researchers

Displays moderated data views appropriate for staff-level access.
"""

import os
import logging
import base64
from datetime import datetime
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://tusadmin:changeme@database:5432/tus_engage_db')
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

server = Flask(__name__)
server.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
jwt = JWTManager(server)

app = dash.Dash(
    __name__,
    server=server,
    url_base_pathname='/dashboard/',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title='TUS-Engage Staff Dashboard'
)

@server.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'staff_dashboard'}), 200

def load_data():
    try:
        df = pd.read_sql("SELECT * FROM mv_staff_dashboard LIMIT 5000", engine)
        return df
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return pd.DataFrame()

app.layout = dbc.Container([
    # Custom CSS for TUS-Engage branding
    html.Link(
        rel='stylesheet',
        href='data:text/css;base64,' + base64.b64encode("""
        .navbar { background: linear-gradient(90deg, #000000, #a39461) !important; }
        .card-header { 
            background: linear-gradient(90deg, #000000, #a39461) !important; 
            color: white !important; 
        }
        .btn-primary { 
            background-color: #000000 !important; 
            border-color: #000000 !important; 
        }
        .btn-primary:hover { 
            background-color: #a39461 !important; 
            border-color: #a39461 !important; 
        }
        h1, h2, h3, h4, h5 { color: #000000 !important; }
        """.encode()).decode()
    ),
    
    # Navigation Bar
    dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("TUS-Engage Staff Dashboard", className="ms-2"),
        ]),
        color="dark",
        dark=True,
        className="mb-4",
        style={"background": "linear-gradient(90deg, #000000, #a39461)"}
    ),
    
    # Main Content
    dbc.Card([
        dbc.CardHeader(html.H4("Staff Analytics Dashboard", className="mb-0")),
        dbc.CardBody([
            html.P("Medium-detail analytics for staff and researchers", className="text-muted"),
            dcc.Graph(id='staff-chart'),
        ])
    ], className="shadow"),
    
    dcc.Interval(id='interval', interval=60000)
])

@app.callback(Output('staff-chart', 'figure'), Input('interval', 'n_intervals'))
def update_chart(n):
    df = load_data()
    if df.empty:
        return px.bar(title="No data available")
    fig = px.bar(df.groupby('department').size().reset_index(name='count'), 
                 x='department', y='count', title="Submissions by Department")
    return fig

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=os.getenv('DASH_ENV') == 'development')
