"""
TUS Engage Tool Pilot - Public Dashboard
High-level dashboard for students, stakeholders, and public access

Displays aggregated, anonymized data for public viewing.
"""

import os
import logging
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
    title='TUS Public Dashboard'
)

@server.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'public_dashboard'}), 200

def load_data():
    try:
        df = pd.read_sql("SELECT * FROM mv_public_dashboard", engine)
        return df
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return pd.DataFrame()

app.layout = dbc.Container([
    html.H1("TUS Public Dashboard", className="my-4"),
    html.P("High-level engagement statistics"),
    dcc.Graph(id='public-chart'),
    dcc.Interval(id='interval', interval=60000)
])

@app.callback(Output('public-chart', 'figure'), Input('interval', 'n_intervals'))
def update_chart(n):
    df = load_data()
    if df.empty:
        return px.bar(title="No data available")
    fig = px.bar(df, x='month', y='total_submissions', title="Monthly Submission Trends")
    return fig

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=os.getenv('DASH_ENV') == 'development')
