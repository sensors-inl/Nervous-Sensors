import logging
import socket
import time
from threading import Event, Thread

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import requests
from dash import Input, Output, dcc, html
from flask import Flask, request
from plotly.subplots import make_subplots
from werkzeug.serving import make_server

server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)
window_sec_size = 20

message_children = [
    html.H3(
        "Sensors are connecting...",
        style={"display": "flex", "align-items": "center", "justify-content": "center", "height": "100vh"},
    )
]


class RenforceViewer:
    _instance = None

    @staticmethod
    def get_instance():
        return RenforceViewer._instance

    def __init__(self, sensors, port=None):
        self._sensors = sensors
        if port is None:
            self.port = self.find_free_port()
        else:
            self.port = port
        RenforceViewer._instance = self

        app.layout = html.Div(
            [
                html.Div(
                    id="graph-div",
                    children=message_children,
                ),
                dcc.Interval(id="interval", interval=500),
            ]
        )

        # To stop the server
        self.should_stop = Event()

        # Add shutdown endpoint
        @server.route("/shutdown", methods=["POST"])
        def shutdown():
            self.should_stop.set()
            shutdown_server()
            return "Server shutting down..."

    @staticmethod
    def find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    def stop_server(self):
        requests.post(f"http://localhost:{self.port}/shutdown")

    def run_server(self):
        # Create and start the Flask server in a separate thread
        self.server = make_server("localhost", self.port, server)
        self.server_thread = Thread(target=self.server.serve_forever)
        self.server_thread.start()

        # Start the Dash app in a separate thread
        self.dash_thread = Thread(
            target=app.run_server, kwargs={"debug": False, "use_reloader": False, "port": self.port}
        )
        self.dash_thread.start()

        # Monitor the stop event
        while not self.should_stop.is_set():
            time.sleep(1)

        # Shutdown the Flask server
        self.server.shutdown()
        self.server_thread.join()
        self.dash_thread.join()

    def get_sensors(self):
        return self._sensors


@app.callback(Output("graph-div", "children"), Input("interval", "n_intervals"))
def update_data(n):
    viewer = RenforceViewer.get_instance()
    sensors = viewer.get_sensors()
    fig = make_subplots(rows=len(sensors), cols=1, vertical_spacing=0.1)

    for i, sensor in enumerate(sensors):
        data = sensor.data_manager.get_latest_data(last_n=1)

        try:
            sample_rate = sensor.get_sampling_rate()
            n_points = window_sec_size * sample_rate
            data = sensor.data_manager.get_latest_data(last_n=n_points)
            time = data.iloc[:, 0].tolist()
            data_value = data.iloc[:, 1].tolist()
            data_size = len(data_value)

            if data_size < n_points:
                data_value = [None] + data_value
                time = [time[0] - (time[1] - time[0]) * (n_points - data_size)] + time

            name = sensor.get_name()
            name = f"{name[:3]} {name[3:]}"
            suffix = " (mV)" if sensor.get_type() == "ECG" else " (µS)"

            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=data_value,
                    mode="lines",
                    name=name + suffix,
                ),
                row=i + 1,
                col=1,
            )
        except IndexError:
            return message_children

    fig.update_layout(
        template="plotly_white",
        height=800,
        autosize=True,
        legend={
            "x": 1.02,
        },
    )

    return [dcc.Graph(figure=fig)]


def shutdown_server():
    func = request.environ.get("werkzeug.server.shutdown")
    if func:
        func()
