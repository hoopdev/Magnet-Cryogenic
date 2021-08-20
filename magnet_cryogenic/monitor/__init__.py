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
                ), width=2),
                dbc.Col(daq.LEDDisplay(
                    label="Output (T)",
                    id='output-display',
                    color="#ff7f50",
                    backgroundColor="#708090",
                    value=""
                ), width={"size": 3, "offset": 1},),
                dbc.Col(daq.LEDDisplay(
                    label="MID (T)",
                    id='mid-display',
                    color="#00bfff",
                    backgroundColor="#708090",
                    value=""
                ), width={"size": 3, "offset": 0},),
                dbc.Col(daq.LEDDisplay(
                    label="MAX (T)",
                    id='max-display',
                    color="#00bfff",
                    backgroundColor="#708090",
                    value=""
                ), width={"size": 3, "offset": 0},),
                # dbc.Col(daq.LEDDisplay(
                #     label="Voltage (V)",
                #     id='voltage-display',
                #     color="#ff7f50",
                #     backgroundColor="#708090",
                #     value=""
                # ), width={"size": 3, "offset": 0},),
            ], align="center",),
            html.Hr(),
            dbc.Row([
                dbc.Col(daq.Indicator(
                    id='persistent-indicator',
                    label="Persistent",
                    color='#98fb98',
                ), width=2),
                dbc.Col(daq.LEDDisplay(
                    label="Persistent (T)",
                    id='persistent-display',
                    color='#98fb98',
                    backgroundColor="#708090",
                    value=""
                ), width={"size": 3, "offset": 1},),
                # dbc.Col(daq.LEDDisplay(
                #     label="Polarity",
                #     id='polarity-display',
                #     color='#98fb98',
                #     backgroundColor="#708090",
                #     value="+"
                # ), width={"size": 3, "offset": 1},),
                dbc.Col(html.H3(id='polarity-display')),
            ], align="center",),
            html.Hr(),
            dcc.Graph(id="my_graph"),

            dcc.Textarea(id='log-output', style={'width': '90%', 'height': 300},),
            dcc.Interval(
                id='interval-component',
                interval=1 * 1000,  # in milliseconds
                n_intervals=0,
                max_intervals=-1,
            ),
        ])

        @self.app.callback(Output("my_graph", "figure"), Input("interval-component", "n_intervals"))
        def update_graph(n_intervals):
            record = self.controller._record
            self.timestamp = []
            self.output = []
            self.voltage = []
            for item in record:
                self.timestamp.append(item.timestamp)
                self.output.append(item.output)
                self.voltage.append(item.voltage)

            fig = make_subplots(specs=[[{"secondary_y": True}]])

            fig.add_trace(
                go.Scatter(x=self.timestamp, y=self.voltage, name="Voltage", mode='markers', marker_color="silver"),
                secondary_y=True,
            )
            fig.add_trace(
                go.Scatter(x=self.timestamp, y=self.output, name="Output", mode='markers', marker_color="coral"),
                secondary_y=False,
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
        def update_heater_indicator(value):
            return self.controller._heater.switch

        @self.app.callback(
            Output('persistent-indicator', 'value'),
            Input("interval-component", "n_intervals")
        )
        def update_persistent_indicator(value):
            return self.controller._heater.persistent

        @self.app.callback(
            Output('mid-display', 'value'),
            Input("interval-component", "n_intervals")
        )
        def update_mid(value):
            return "{:.3f}".format(self.controller._mid.value)

        @self.app.callback(
            Output('max-display', 'value'),
            Input("interval-component", "n_intervals")
        )
        def update_max(value):
            return "{:.3f}".format(self.controller._max.value)

        @self.app.callback(
            Output('output-display', 'value'),
            Input("interval-component", "n_intervals")
        )
        def update_output(value):
            return "{:.3f}".format(self.controller._output.output)

        # @self.app.callback(
        #     Output('voltage-display', 'value'),
        #     Input("interval-component", "n_intervals")
        # )
        # def update_voltage(value):
        #     return "{:.3f}".format(self.controller._output.voltage)

        @self.app.callback(
            Output('persistent-display', 'value'),
            Input("interval-component", "n_intervals")
        )
        def update_persistent(value):
            return "{:.3f}".format(self.controller._heater.field) if self.controller._heater.persistent else "{:.3f}".format(0)

        @self.app.callback(
            Output('polarity-display', 'children'),
            Input("interval-component", "n_intervals")
        )
        def update_polarity(value):
            return f"Polarity:\n{self.controller._polarity.value}"

        @self.app.callback(
            Output('log-output', 'value'),
            Input("interval-component", "n_intervals")
        )
        def update_log(value):
            return self.controller._log

    def start(self):
        self.app.run_server(mode="jupyterlab")
