from ..controller import Controller
import dataclasses
from typing import Any, NamedTuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
import time

from jupyter_dash import JupyterDash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.express as px
from dash.dependencies import Input, Output


@dataclasses.dataclass
class Monitor:
    controller: Controller
    timestamp: list = dataclasses.field(default_factory=list, init=False)
    output: list = dataclasses.field(default_factory=list, init=False)
    voltage: list = dataclasses.field(default_factory=list, init=False)

    app: Any = JupyterDash(external_stylesheets=[dbc.themes.SLATE])

    def __post_init__(self):
        self.app.layout = html.Div([
            html.H1("Magnet Monitor"),
            html.Hr(),
            dbc.Row([
                dbc.Col(daq.Indicator(
                    id='heater-indicator',
                    label="Heater",
                    color='#ffb6c1',
                ),),
                dbc.Col(daq.Indicator(
                    id='persistent-indicator',
                    label="Persistent",
                    color='#98fb98',
                ),),
            ],),
            html.Hr(),
            dcc.Graph(id="my_graph"),
            dcc.Interval(
                id='interval-component',
                interval=1 * 1000,  # in milliseconds
                n_intervals=0,
                max_intervals=-1,
            ),
        ])

        @self.app.callback(Output("my_graph", "figure"), Input("interval-component", "n_intervals"))
        def update_graph(selected_country):
            out = controller.output
            timestamp.append(datetime.datetime.now())
            output.append(out.output)
            voltage.append(out.voltage)

            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Scatter(x=timestamp, y=output, name="Output", mode='markers', marker_color="dodgerblue"),
                secondary_y=False,
            )

            fig.add_trace(
                go.Scatter(x=timestamp, y=voltage, name="Voltage", mode='markers', marker_color="coral"),
                secondary_y=True,
            )

            xaxis = dict(
                title="Time",
                ticks='outside',
                linewidth=1,
                linecolor='Black',
                mirror=True
            )
            yaxis_output = dict(
                title="Output (T)",
                ticks='outside',
                linewidth=1,
                linecolor='Black',
                mirror=True
            )
            yaxis_voltage = dict(
                title="Voltage (V)",
                ticks='outside',
                linewidth=1,
                linecolor='Black',
                mirror=True
            )
            layout = go.Layout(
                title="OUTPUT",
                showlegend=False,
                xaxis_showgrid=True,
                xaxis=xaxis,
                yaxis=yaxis_output,
                yaxis2=yaxis_voltage,
                yaxis_showgrid=True,
                template='plotly_dark',
            )
            fig.update_layout(layout)
            return fig

        @self.app.callback(
            Output('heater-indicator', 'value'),
            Input("interval-component", "n_intervals")
        )
        def update_heater(value):
            time.sleep(0.2)
            return True if controller.heater else False

        @self.app.callback(
            Output('persistent-indicator', 'value'),
            Input("interval-component", "n_intervals")
        )
        def update_persistent(value):
            time.sleep(0.2)
            return True if controller.persistent_status else False

    def start(self):
        self.app.run_server(mode="jupyterlab")
