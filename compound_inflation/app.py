import dash
import dash_bootstrap_components as dbc
from dash import html

from components import (about_section, control_center, desc_table,
download_link, github_link, modified_start_year_store, plot_legend, storage,
visibility_store)

app = dash.Dash(__name__)
server=app.server
app.config.suppress_callback_exceptions = True
#Controls what ends up in the tab bar
app.title = "Compound Inflation"

app.layout = dbc.Container(
    [
        html.Div(
            [
                control_center,
                plot_legend,
                download_link,
                about_section,
                desc_table,
                github_link,
                # Storage items aren't displayed explicitly
                modified_start_year_store,
                visibility_store,
                storage
            ],
            style={'backgroundColor': 'white'}
        )
    ],
    fluid=True
)
