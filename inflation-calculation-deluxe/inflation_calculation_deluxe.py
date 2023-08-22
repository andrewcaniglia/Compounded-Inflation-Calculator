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

#Transforms web tables into the proper format for the viz
def make_usable(df):
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
    df.rename(columns={'YoY': '1 Year'}, inplace=True)
    df.sort_values('Date', inplace=True, ignore_index=True)
    df.set_index('Date', inplace=True)
    return df

#Headline CPI (main inflation)
mi=pd.read_html('https://www.usinflationcalculator.com/inflation/historical-inflation-rates/')[0]
mi=make_usable(mi)

#Core inflation
ci=pd.read_html('https://www.usinflationcalculator.com/inflation/united-states-core-inflation-rates/')[0]
ci.columns=ci.iloc[len(ci)-1]
ci=ci[:-1]
ci=make_usable(ci)
    
#food inflation
fi=pd.read_html('https://www.usinflationcalculator.com/inflation/food-inflation-in-the-united-states/')[0]
fi=make_usable(fi)

#healthcare inflation
hi=pd.read_html('https://www.usinflationcalculator.com/inflation/health-care-inflation-in-the-united-states/')[0]
hi.columns=hi.iloc[0]
hi=hi[1:]
hi=make_usable(hi)

#airline inflation
ai=pd.read_html('https://www.usinflationcalculator.com/inflation/airfare-inflation/')[0]
ai.columns=ai.iloc[0]
ai=ai[1:]
ai=ai[ai['Year'].astype('int')>=1970]
ai=make_usable(ai)

#energy inflation (defined as "gasoline, electricity, fuel oil, and utility (piped) gas prices")
ei=pd.read_html('https://www.usinflationcalculator.com/inflation/energy-prices-gasoline-electricity-and-fuel-oil-2015-present/')[0]
ei.columns=ei.iloc[0]
ei=ei[1:]
ei=make_usable(ei)

#grocery inflation
gi=pd.read_html('https://www.usinflationcalculator.com/inflation/average-prices-for-selected-grocery-store-items-2015-present/')[0]
gi.columns=gi.iloc[0]
gi=gi[1:]
gi=make_usable(gi)

#College inflation (tricky sonofa)
co=pd.read_html('https://www.usinflationcalculator.com/inflation/college-tuition-inflation-in-the-united-states/')[0]
co.columns=co.iloc[0]
co=co[1:]
co=co.melt(id_vars='Year', var_name='Month', value_name='YoY')
#Clean
huh=co[(co['Month']=='Jan')&(co['Year']=='1978')]['YoY'].values[0]
co=co[co['YoY']!=huh]
co.dropna(inplace=True)
# # #That's not a month
co=co[co['Month']!='Ave']
# # #Make date usable
co['Date']=co['Year'].astype('str')+co['Month']
co['Date']=pd.to_datetime(co['Date'], format='%Y%b')
#Final fix
co=co[~co['YoY'].astype('str').str.contains('Avail.')][['Date', 'YoY']]
co['YoY']=[float(x) for x in co['YoY']]
co.sort_values('Date', inplace=True, ignore_index=True)
co.set_index('Date', inplace=True)

#gasoline inflation
ga=pd.read_html('https://www.usinflationcalculator.com/inflation/gasoline-inflation-in-the-united-states/')[0]
ga.columns=ga.iloc[0]
ga=ga[1:]
ga.columns=ga.columns.str.capitalize()
ga=make_usable(ga)

#Used to determine the compounded inflation rate for a specified time span.
def calculate_yoy(row, years, df_ref):
    
    # Extract the starting date from the row's index
    start_date = row.name

    # Fetch the YoY values for the specified number of years
    yoy_values = [df_ref.loc[start_date - pd.DateOffset(years=i), '1 Year']
                  for i in range(years) if start_date - pd.DateOffset(years=i) in df_ref.index]
    
    # If any year's data is missing, return None
    if len(yoy_values) != years:
        return None

    # Calculate the compounded YoY change
    total = np.prod([(yoy / 100 + 1) for yoy in yoy_values])

    # Convert the total change to percentage and round off
    return round((total - 1) * 100, 1)

#Dash app
app = dash.Dash(__name__)

#Used to input desired cumulative interest rate
input_box = dcc.Input(id='input-box', type='number', placeholder='Years of Inflation', n_blur=0)

#All dates and all years that can be displayed
unique_dates = sorted(mi.index.unique())
unique_years = sorted(set(date.year for date in unique_dates))


#Eliminates all added cumulative rates
reset_button = html.Button('Reset', id='reset-button')

#Creates a new line based on the input value
submit_button = html.Button('Add Line', id='submit-button')

# Input fields for start and end years
start_year_input = dcc.Input(id='start-year-input', type='number', placeholder='Start Year',
                             value=min(unique_years), style={'width': '80px'})
end_year_input = dcc.Input(id='end-year-input', type='number', placeholder='End Year',
                           value=max(unique_years), style={'width': '80px'})

#Dictionary of all possible data sources and id names
data_sources={'Headline CPI':mi,
             'Core CPI':ci,
             'Energy':ei,
             'Gas':ga,
             'Grocery':gi,
             'Food':fi,
             'Healthcare':hi,
             'College':co,
             'Airline':ai}

# Dropdown for data source selection
data_source_dropdown = dcc.Dropdown(
    id='data-source-dropdown',
    options=[{'label': source, 'value': source} for source in data_sources.keys()],
    value='Headline CPI' ,# default value
    style={'width': '200px',
          'fontFamily': 'Arial, sans-serif',
                'borderRadius': '5px'},
                clearable=False
)

#Divs for data source dropdown, input box, submit button, reset button, and year range.
control_center = html.Div([
    # Data Source Section
    html.Div([
        html.Label('Data Source', style={'fontWeight': 'bold', 'fontSize': '18px'}),
        data_source_dropdown
    ], style={
        'border': '1px solid #ccc',
        'padding': '5px',
        'borderRadius': '5px',
        'backgroundColor': '#f8f8f8',
        'boxShadow': '3px 3px 5px #aaa',
        'width': '220px',
        'marginRight': '15px'
    }),

    # Controls Section
    html.Div([
        html.Div([  # This Div holds the year inputs
            html.Div([
                html.Label('Range  ', style={'fontWeight': 'bold'}),
                start_year_input, html.Label('  -  ', style={'fontWeight': 'bold'}),
                end_year_input
            ], style={'marginRight': '1px'}),
        ], style={'display': 'flex', 'gap': '0px', 'marginBottom': '10px'}),

        html.Div([  # This Div holds the YoY label and input
            input_box,
            submit_button,
            reset_button
        ])
    ], style={
        'border': '1px solid #ccc',
        'padding': '5px',
        'borderRadius': '5px',
        'backgroundColor': '#f8f8f8',
        'boxShadow': '3px 3px 5px #aaa',
        'width': 'auto'
    })

], style={'display': 'flex', 'gap': '10px', 'flexDirection': 'row', 'marginBottom': '10px'})

# Container for plot
plot = dcc.Graph(id='plot')

#Stores lines displayed
storage = dcc.Store(id='storage', data=[1])

#Stores lines visible (not made hidden by clicking the legend item
visibility_store = dcc.Store(id='visibility-store', data={})

#Tracks whether or not the start year in the year range was modified
modified_start_year_store = dcc.Store(id='modified-start-year-store', data={'modified': False})

# Arranges the components of the app
app.layout = html.Div([control_center, html.Div([
        # The graph nested in a loading animation section
        dcc.Loading(
            id="loading-plot",
            type="circle",
        children=[
        dcc.Graph(
            id='plot',
            #Makes it look cool
            style={
                'boxShadow': '3px 3px 5px #aaa'
            }
        )
    ]
        ),
        
        # The custom legend
        html.Div(id='custom-legend', style={
            'position': 'absolute',
            'right': '10px',
            'top': '50px',  # adjust as needed
            'zIndex': 1000
        })
    ],
    style={'position': 'relative'}),
    #Storage items aren't displayed explicitly
    modified_start_year_store,
    visibility_store, storage]
    , style={'backgroundColor': 'white'})

#Updates storage container based on input values and reset button
@app.callback(
    Output('storage', 'data'),
    [Input('submit-button', 'n_clicks'),
    Input('reset-button', 'n_clicks')],
    [State('input-box', 'value'),
     State('storage', 'data')]
)
def update_storage(submit_n_clicks, reset_n_clicks, input_value, data):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Reset button causes only the 1 year inflation rate to be displayed
    if button_id == 'reset-button':
        return [1]

    # If no value is input, do nothing
    if not input_value:
        raise dash.exceptions.PreventUpdate

    # Ensures input is always an integer
    input_value = int(input_value)

    # If the value is not already in the data, append it
    if input_value not in data:
        data.append(input_value)
    
    return data

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

    #If a year earlier than the earliest year in the current data source is populated when the data source is changed, then the start year autoamtically changes to the earliest year in the new data source. This does not change what is displayed if an earlier year is written than appears in the dataset after the data source has been changed. In that case, the too-early year is displayed but it does not change how the plot looks.
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
def combined_update(start_year, end_year, data_source, data, legend_button_clicks, visibility_data, current_fig):

    # Based on the dropdown value, select the data source
    df = data_sources[data_source]

    # Ensure necessary columns exist in the new data source
    for years in data:
        if years != 1 and '{} Year'.format(years) not in df.columns:
            #Applies compounded interest function
            df['{} Year'.format(years)] = df.apply(lambda row: calculate_yoy(row, years, df), axis=1)
    
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

    df_filtered = df.copy()
    # Apply date filter
    df_filtered = df[(df.index.year >= start_year) & (df
                                                      .index.year <= end_year)]

    # Filter the dataframe to include only the relevant 'Inflation Change' columns
    columns_to_include = ['{} Year'.format(year) for year in data]
    df_plot = df_filtered[columns_to_include]
    
    # Create the line chart
    fig = px.line(df_plot, title='Multi-Year Inflation Rate', labels={'value': 'Inflation Rate', 'index': 'Date', 'variable': 'Years'}
                 )

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
    xaxis=dict(title_text="Year", title_font=dict(family="Arial, sans-serif", size=18, color="Grey")),
    yaxis=dict(title_text="Inflation Rate", title_font=dict(family="Times New Roman, Times, serif", size=18, color="Grey")),
        xaxis_showgrid=True,
        yaxis_showgrid=True,
        xaxis_gridcolor='gray',
        yaxis_gridcolor='gray',
        plot_bgcolor='#f8f8f8',
        paper_bgcolor='#f8f8f8'
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
    
