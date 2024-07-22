import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, dcc, html
from plotly.subplots import make_subplots
from renforce_data import ECGData, EDAData

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
window_sec_size = 20

message_children = [
    html.H3(
        "Sensors are connecting...",
        style={
            "display": "flex",
            "align-items": "center",
            "justify-content": "center",
            "height": "100vh",
        },
    )
]


class RenforceViewer:
    _instance = None

    @staticmethod
    def get_instance():
        return RenforceViewer._instance

    def __init__(self):
        self._sensors = []
        self._sensor_names = ["ECG (mV)", "EDA (uS)"]
        self._sampling_rates = [ECGData.sampling_rate, EDAData.sampling_rate]
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

        # Remove Dash logs
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

    def run_server(self):
        app.run_server(debug=False, port=8050)

    def add_sensor(self, sensor):
        self._sensors.append(sensor)

    def get_name(self, sensor):
        for name in self._sensor_names:
            if name.split(" ")[0] in sensor.name:
                return name
        raise ValueError("Unknown sensor")

    def get_sampling_rate(self, sensor):
        for name in self._sensor_names:
            if name.split(" ")[0] in sensor.name:
                return self._sampling_rates[self._sensor_names.index(name)]
        raise ValueError("Unknown sensor")

    def get_sensors(self):
        return self._sensors


@app.callback(Output("graph-div", "children"), Input("interval", "n_intervals"))
def update_data(n):
    viewer = RenforceViewer.get_instance()
    sensors = viewer.get_sensors()
    fig = make_subplots(rows=len(sensors), cols=1, vertical_spacing=0.1)

    for i, sensor in enumerate(sensors):
        try:
            sample_rate = viewer.get_sampling_rate(sensor)
            n_points = window_sec_size * sample_rate
            data = sensor.data.get_latest_data(last_n=n_points)
            time = data.iloc[:, 0].tolist()
            data_value = data.iloc[:, 1].tolist()
            data_size = len(data_value)

            if data_size < n_points:
                data_value = [data_value[0]] + data_value
                time = [time[0] - (time[1] - time[0]) * (n_points - data_size)] + time

            fig.add_trace(
                go.Scatter(
                    x=time,
                    y=data_value,
                    mode="lines",
                    name=viewer.get_name(sensor),
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
