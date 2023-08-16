import pandas as pd
import dash
import numpy as np
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State, ALL
import plotly.express as px
import plotly.graph_objects as go
import json
import os

#Hopefully this page still works
df=pd.read_html('https://www.usinflationcalculator.com/inflation/historical-inflation-rates/')[0]
df=df.melt(id_vars='Year', var_name='Month', value_name='YoY')
#Clean
df.dropna(inplace=True)
# #That's not a month
df=df[df['Month']!='Ave']
# #Make date usable
df['Date']=df['Year'].astype('str')+df['Month']
df['Date']=pd.to_datetime(df['Date'], format='%Y%b')
#Final fix
df=df[~df['YoY'].astype('str').str.contains('Avail.')][['Date', 'YoY']]
df['YoY']=[float(x) for x in df['YoY']]
df.sort_values('Date', inplace=True, ignore_index=True)
df.set_index('Date', inplace=True)

def calculate_yoy(row, years, df_ref):
    
    # Extract the starting date from the row's index
    start_date = row.name

    # Fetch the YoY values for the specified number of years
    yoy_values = [df_ref.loc[start_date - pd.DateOffset(years=i), 'YoY']
                  for i in range(years) if start_date - pd.DateOffset(years=i) in df_ref.index]
    
    # If any year's data is missing, return None
    if len(yoy_values) != years:
        return None

    # Calculate the compounded YoY change
    total = np.prod([(yoy / 100 + 1) for yoy in yoy_values])

    # Convert the total change to percentage and round off
    return round((total - 1) * 100, 1)

# Create the Dash app
app = dash.Dash(__name__)

# Create an input box
input_box = dcc.Input(id='input-box', type='number', placeholder='Years of Inflation', n_blur=0)

submit_button = html.Button('Add Line', id='submit-button')

unique_dates = sorted(df.index.unique())
unique_years = sorted(set(date.year for date in unique_dates))

# Create a container for the plot
plot = dcc.Graph(id='plot')

# Input fields for start and end years
start_year_input = dcc.Input(id='start-year-input', type='number', placeholder='Start Year', value=min(unique_years))
end_year_input = dcc.Input(id='end-year-input', type='number', placeholder='End Year', value=max(unique_years))

# Create a storage component
storage = dcc.Store(id='storage', data=[1])

visibility_store = dcc.Store(id='visibility-store', data={})

# Arrange the components in the app layout
app.layout = html.Div([input_box, submit_button, start_year_input, end_year_input, html.Div([
        # The graph
        dcc.Loading(
            id="loading-plot",
            type="circle",
            children=[plot]
        ),
        
        # The custom legend
        html.Div(id='custom-legend', style={
            'position': 'absolute',
            'right': '10px',
            'top': '50px',  # adjust as needed
            'zIndex': 1000
        })
    ], style={'position': 'relative'}), visibility_store, storage], style={'backgroundColor': 'white'})

@app.callback(
    Output('storage', 'data'),
    [Input('submit-button', 'n_clicks')],
    [State('input-box', 'value'),
     State('storage', 'data')]
)
def update_storage(n_clicks, input_value, data):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    # If no value is input, do nothing
    if not input_value:
        raise dash.exceptions.PreventUpdate

    # Convert the input_value to the appropriate type (int or float, depending on your use case)
    input_value = int(input_value)  # or float(input_value)

    # If the value is not already in the data, append it
    if input_value not in data:
        data.append(input_value)
    
    return data

@app.callback(
    [Output('plot', 'figure'), Output('visibility-store', 'data')],
    [
     Input('start-year-input', 'value'),
     Input('end-year-input', 'value'),
     Input('storage', 'data'),
     Input({'type': 'legend-button', 'index': ALL}, 'n_clicks')],
    [State('visibility-store', 'data'),
     State('plot', 'figure')]
)
def combined_update(start_year, end_year, data, legend_button_clicks, visibility_data, current_fig):
    ctx = dash.callback_context

    if current_fig is None:
        current_fig = go.Figure()

    # Check if the callback was triggered by a legend button
    if "legend-button" in ctx.triggered[0]['prop_id']:
        clicked_id = ctx.triggered[0]['prop_id'].split('.')[0]
        trace_name = json.loads(clicked_id)['index']
    
        # Toggle trace visibility
        for trace in current_fig['data']:
            if trace['name'] == trace_name:
                current_visibility = trace.get('visible', True)  # Get the current visibility or default to True if not set
                trace['visible'] = 'legendonly' if current_visibility == True else True

                # Update the visibility data
                visibility_data[trace_name] = trace['visible']

        return [current_fig, visibility_data]  # Return the updated figure and updated visibility data

    latest_year = int(data[-1]) if data else 1
    years = latest_year
    # Apply the function to each row in the DataFrame
    df['{} Year'.format(years)] = df.apply(lambda row: calculate_yoy(row, years, df), axis=1)
    
    # Use the entire DataFrame, since there's no dropdown anymore
    df_filtered = df.copy()
    # Apply date filter
    df_filtered = df[(df.index.year >= start_year) & (df
                                                      .index.year <= end_year)]

    # Filter the dataframe to include only the relevant 'Inflation Change' columns
    columns_to_include = ['{} Year'.format(year) for year in data]
    df_plot = df_filtered[columns_to_include]

    # Create the line chart
    fig = px.line(df_plot, title='Multi-Year Inflation Rate', labels={'value': 'Inflation Change', 'index': 'Date', 'variable': 'Years'})
    
    for trace in fig.data:
        trace_name = trace['name']
        if trace_name in visibility_data:
            trace['visible'] = visibility_data[trace_name]
    
    # Apply stored visibility data
    if visibility_data:
        for trace in fig.data:
            trace_name = '{} Year'.format(trace.name)
            if trace_name in visibility_data:
                trace['visible'] = visibility_data[trace_name]

    fig.update_layout(
        title_text="Multi-Year Inflation Rate",
    title_font=dict(family="Courier New, monospace", size=24, color="RebeccaPurple"),
    xaxis=dict(title_text="Date Range", title_font=dict(family="Arial, sans-serif", size=18, color="Grey")),
    yaxis=dict(title_text="Inflation Change", title_font=dict(family="Times New Roman, Times, serif", size=18, color="Grey")),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_showgrid=True,
        yaxis_showgrid=True,
        xaxis_gridcolor='gray',
        yaxis_gridcolor='gray'
    )
    fig.update_yaxes(zerolinecolor='black')
    
    fig.update_layout(showlegend=False)

    return [fig, visibility_data]  # Return the new figure and the unchanged visibility data

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

    legend_children = []
    for trace in sorted_traces:
        trace_name = trace['name']

        # Retrieve the visibility from visibility_data (or default to True if not present)
        trace_visible = visibility_data.get(trace_name, True)

        # Determine the legend style based on visibility
        legend_style = {'opacity': 0.5} if trace_visible == 'legendonly' else {}

        legend_children.append(
            html.Div([
                html.Span(style={'display': 'inline-block', 'width': '12px', 'height': '12px', 'backgroundColor': trace['line']['color'], **legend_style}),
                html.Button(trace['name'], id={'type': 'legend-button', 'index': trace['name']}, style=legend_style)
            ])
        )

    return legend_children


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8050)))
    
    
