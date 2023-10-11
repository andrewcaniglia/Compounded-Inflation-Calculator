import csv
import json
import urllib.parse

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State, ALL
import pandas as pd
from plotly.graph_objs import Figure
import plotly.graph_objs as go

from app import app
from load_tables import data_sources
from utils import calculate_yoy, get_distinct_colors

#Updates storage container based on input values and reset button
@app.callback(
    Output('storage', 'data'),
    [Input('submit-button', 'n_clicks'),
    Input('reset-button', 'n_clicks')],
    [State('input-box', 'value'),
     State('storage', 'data')]
)
def update_storage(submit_n_clicks, reset_n_clicks, input_value, storage_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    data = storage_data.get('data', [])

    # Reset button causes only the 1 year inflation rate to be displayed
    if button_id == 'reset-button':
        return {'reset': True, 'data': [1]}  # Include a reset flag

    # If no value is input, do nothing
    if not input_value:
        raise dash.exceptions.PreventUpdate

    # Ensures input is always an integer
    input_value = int(input_value)

    # If the value is not already in the data, append it
    if input_value not in data:
        data.append(input_value)
    
    return {'reset': False, 'data': data}

@app.callback(
    Output('modified-start-year-store', 'data'),
    [Input('start-year-input', 'n_blur')],
    [State('modified-start-year-store', 'data')]
)
def track_start_year_modifications(n_blur, data):
    if n_blur ==True and n_blur > 0:
        data['modified'] = True
    return data

#Handles cases where the start year value should be changed automatically
@app.callback(
    Output('start-year-input', 'value'),
    [Input('data-source-dropdown', 'value')],
    [State('start-year-input', 'value'),
     State('modified-start-year-store', 'data')]
)
def adjust_start_year(data_source, current_start_year, modified_data):
    #determines data source
    df_selected = data_sources[data_source]
    earliest_year = df_selected.index.min().year

    #If the start year was never modified then the earliest year in a data source is populated as the start year when the data source has been switched
    if not modified_data['modified']:
        return earliest_year

    #If a year earlier than the earliest year in the current data source is populated when the data source is changed, then the start year autoamtically changes to the earliest year in the new data source.
    if current_start_year < earliest_year:
        return earliest_year

    return current_start_year

#Updates the plot and custom legend at the same time.
@app.callback(
    [Output('plot', 'figure'), Output('visibility-store', 'data')],
    [
     Input('start-year-input', 'value'),
     Input('end-year-input', 'value'),
     Input('data-source-dropdown', 'value'),
     Input('storage', 'data'),
     Input({'type': 'legend-button', 'index': ALL}, 'n_clicks')
    ],
    [State('visibility-store', 'data'),
     State('plot', 'figure')]
)
def combined_update(start_year, end_year, data_source, storage_data, legend_button_clicks, visibility_data, current_fig):

    # Extract the 'data' list from storage_data
    data = storage_data.get('data', [])

    # Based on the dropdown value, select the data source
    df = data_sources[data_source]

    # Ensure necessary columns exist in the new data source
    for years in data:
        if years != 1 and '{} Year'.format(years) not in df.columns:
            #Applies compounded interest function
            df[f'{years} Year'] = calculate_yoy(df, years)
    
    ctx = dash.callback_context

    # Initialize fig
    if current_fig is None or not isinstance(current_fig, Figure):
        current_fig = go.Figure(current_fig)

    # Check if the callback was triggered by a legend button
    if "legend-button" in ctx.triggered[0]['prop_id']:
        clicked_id = ctx.triggered[0]['prop_id'].split('.')[0]
        trace_name = json.loads(clicked_id)['index']
    
        # Toggle trace visibility
        for trace in current_fig['data']:
            if trace['name'] == trace_name:
                current_visibility = trace.visible or True  # Get the current visibility or default to True if not set
                trace['visible'] = 'legendonly' if current_visibility == True else True

                # Update the visibility data
                visibility_data[trace_name] = trace['visible']

        return [current_fig, visibility_data]  # Return the updated figure and updated visibility data

    #Create snapshot of currently selected data source
    df_filtered = df.copy()
    # Apply date filter
    df_filtered = df[(df.index.year >= start_year) & (df.index.year <= end_year)]

    # Generate colors
    colors = get_distinct_colors(len(data))

    # Update or add lines for each year in data
    for idx, year in enumerate(data):
        column_name = '{} Year'.format(year)
        y_values = df_filtered[column_name]

        color=colors[idx]

        existing_trace_index = next((i for i, trace in enumerate(current_fig['data']) if trace['name'] == column_name), None)

        if existing_trace_index is not None:
            current_fig['data'][existing_trace_index]['y'] = y_values
            current_fig['data'][existing_trace_index]['x'] = df_filtered.index
        else:
            # Add a new line if it doesn't already exist
            new_trace = go.Scatter(
                x=df_filtered.index,
                y=y_values,
                mode='lines',
                name=column_name,
                line=dict(color=color)
            )
            current_fig.add_trace(new_trace)

    # Apply stored visibility data
    if visibility_data:
        for trace in current_fig['data']:
            trace_name = '{} Year'.format(trace['name'])
            if trace_name in visibility_data:
                trace['visible'] = visibility_data[trace_name]

    #This code triggers when the 'reset' button is clicked
    if storage_data.get('reset', False):
        traces_to_keep= ['1 Year']
        current_fig['data'] = [trace for trace in current_fig['data'] if trace['name'] in traces_to_keep]
        # Set all to visible
        for trace in current_fig['data']:
            trace['visible'] = True
        visibility_data = {}  # Reset visibility_data

        # Reset the data to 1-year inflation rate only
        storage_data['data'] = [1]

    #Make the graph look nice
    current_fig.update_layout(
        title_text="compoundinflation.org",
        title_font=dict(
            family="Courier New, monospace",
            size=24,
            color="#635DFF"
        ),
        xaxis=dict(
            title_text="Year",
            title_font=dict(
                family="Arial, sans-serif",
                size=18,
                color="DarkSlateGray"
            ),
            showgrid=True,
            gridcolor='LightGray',
            gridwidth=0.5,
            zerolinecolor='LightGray',
            zerolinewidth=0.5
        ),
        yaxis=dict(
            title_text="Inflation Rate (%)",
            title_font=dict(
                family="Times New Roman, Times, serif",
                size=18,
                color="DarkSlateGray"
            ),
            showgrid=True,
            gridcolor='LightGray',
            gridwidth=0.5,
            zerolinecolor='LightGray',
            zerolinewidth=0.5
        ),
        plot_bgcolor='#FAFAFA',
        paper_bgcolor='#FAFAFA',
        showlegend=False
    )
    
    current_fig.update_yaxes(
        zerolinecolor='black'
        )
        
    return [current_fig, visibility_data]  # Return the new figure and the unchanged visibility data

#Handles the legend and its special functionality
@app.callback(
    Output('custom-legend', 'children'),
    [Input('visibility-store', 'data'),
     Input('plot', 'figure')]
)
def update_custom_legend(visibility_data, current_fig):
    # Check if visibility_data or current_fig['data'] is None
    if visibility_data is None or current_fig is None or not current_fig.get('data'):
        raise dash.exceptions.PreventUpdate

    # Sort the traces based on their names
    sorted_traces = sorted(current_fig['data'], key=lambda trace: int(trace['name'].split(' ')[0]))

    #Stores all legend items
    legend_children = []
    for trace in sorted_traces:
        trace_name = trace['name']

        # Retrieve the visibility from visibility_data (or default to True if not present)
        trace_visible = visibility_data.get(trace_name, True)

        # Greys out hidden legend items after they are clicked or makes them normal if they are clicked again
        legend_style = {'opacity': 0.5} if trace_visible == 'legendonly' else {}

        #Adds or modifies legend items
        legend_children.append(
            html.Div(
                [
                    html.Span(
                        style={
                            'display': 'inline-block',
                            'width': '12px',
                            'height': '12px',
                            'backgroundColor': trace['line']['color'],
                            **legend_style
                        }
                    ),
                    html.Button(
                        trace['name'],
                        id={'type': 'legend-button', 'index': trace['name']},
                        style=legend_style
                    )
                ]
            )
        )
    return legend_children

#Controls 'Download CSV' functionality
@app.callback(
    Output('download-link', 'href'),
    [Input('start-year-input', 'value'),
     Input('end-year-input', 'value'),
     Input('data-source-dropdown', 'value'),
     Input('plot', 'figure')],
     [State('visibility-store', 'data')]
)
def update_download_link(start_year, end_year, data_source, current_fig, visibility_data):
    # Filter the dataframe based on the year range and data source
    df_filtered = data_sources[data_source][(data_sources[data_source].index.year >= start_year) & (data_sources[data_source].index.year <= end_year)]

    # Start with all traces
    all_traces = {trace['name'] for trace in current_fig['data']}
    
    # If visibility_data exists, consider only the traces that are not 'legendonly'
    if visibility_data:
        hidden_traces = {key for key, value in visibility_data.items() if value == 'legendonly'}
    else:
        hidden_traces = set()
        
    # Calculate the set of visible traces
    visible_traces = all_traces - hidden_traces

    # Sort the visible traces by the numerical value of the year
    visible_traces = sorted(visible_traces, key=lambda x: int(x.split(' ')[0]))

    # Filter the dataframe to only include visible traces
    df_filtered = df_filtered[list(visible_traces)].dropna(how='all')

    # Convert the DataFrame to a CSV string
    csv_string = df_filtered.to_csv(index=True, encoding='utf-8')
    
    # Create a data URI
    csv_data_uri = f"data:text/csv;charset=utf-8,{urllib.parse.quote(csv_string)}"
    
    return csv_data_uri
