import logging
import socket
import time
from threading import Event, Thread

import dash
import dash_bootstrap_components as dbc
import numpy as np
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
        self.dash_thread = Thread(target=app.run, kwargs={"debug": False, "use_reloader": False, "port": self.port})
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
        try:
            name = sensor.get_name()
            sensor_name = f"{name}"
            plot_type = sensor.get_plot_type()
            # Get signal names
            header = sensor._data_manager.get_header()
            header = header[1:]

            time = []
            data_value = np.empty((2, len(header)))
            data = sensor.data_manager.get_latest_data(last_n=1)
            if len(data) > 0:
                last_timestamp = data.iloc[-1, 0]
                data = sensor.data_manager.get_latest_data(latest_data=max(0, last_timestamp - window_sec_size))
                time = data.iloc[:, 0].tolist()
                data_value = data.iloc[:, 1:].to_numpy()

            for j, signal in enumerate(header):
                signal_name = f" {signal}"
                if plot_type == "bar":
                    fig.add_trace(
                        go.Bar(
                            x=time,
                            y=data_value[:, j],
                            name=sensor_name + signal_name,
                        ),
                        row=i + 1,
                        col=1,
                    )
                else:
                    fig.add_trace(
                        go.Scatter(
                            x=time,
                            y=data_value[:, j],
                            mode="lines",
                            name=sensor_name + signal_name,
                        ),
                        row=i + 1,
                        col=1,
                    )
        except Exception as e:
            print("Viewer error:", str(e))
            return

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
