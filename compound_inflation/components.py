from datetime import datetime

import dash
from dash import dcc
from dash import html
from dash import dash_table

from load_tables import data_sources

#Used to input desired cumulative interest rate
input_box = dcc.Input(id='input-box', type='number', placeholder='Input Time Frame', n_blur=0)

#Eliminates all added cumulative rates
reset_button = html.Button('Reset', id='reset-button')

#Creates a new line based on the input value
submit_button = html.Button('Add Line', id='submit-button')

#Stores lines displayed
storage = dcc.Store(id='storage', data={'reset': False, 'data': [1, 4]})

#Stores lines visible (not made hidden by clicking the legend item)
visibility_store = dcc.Store(id='visibility-store', data={})

#Tracks whether or not the start year in the year range was modified
modified_start_year_store = dcc.Store(id='modified-start-year-store', data={'modified': False})

#Downloads currently visible data
download_link = html.A(
    'Download CSV',
    id='download-link',
    download="data.csv",
    href="",
    target="_blank",
    style={
        'backgroundColor': 'White',
        'color': 'Grey',
        'padding': '6px 10px',
        'border': 'none',
        'borderRadius': '4px',
        'cursor': 'pointer',
    }
)

#Describes how to use the dashboard
about_section = html.Div(
    [
        html.H4("About This Chart"),
        
        #Main description
        html.P(
            "Every month, the U.S. Labor Department's Buraeu of Labor Statistics releases the current year over year and month over month inflation rate. "
            "However, these intervals do not convey how much prices have increased over time intervals that may be more relevant to the average consumer. "
            "Calculate inflation rates over longer time frames and visualize them on this interactive time-series chart. "
            "Hover over the graph lines to see precise values."
        ),
        
        #Describes data source dropdown
        html.Ul(
            [
                html.Li(
                    [
                        html.I(className="fas fa-database"),  # Icon
                        " Category: ",
                        html.Span("Select a category to view. "),
                        html.Small(
                            "Note: Data starts from different years for each category. "
                            "All data is sourced from the U.S. Labor Department’s Bureau of Labor Statistics as reported by "
                        ),
                        html.A(
                            'usinflationcalculator.com.', 
                            href='https://www.usinflationcalculator.com/inflation/consumer-price-index-and-annual-percent-changes-from-1913-to-2008/',
                            style={'font-size': 'smaller'}
                        )
                    ]
                ),
                    
                #Describes time period input
                html.Li(
                    [
                        html.I(className="fas fa-calendar-alt"),  # Icon
                        "Range: ",
                        html.Span("Set the time period you're interested in.")
                    ]
                ),
                
                #Describes input box
                html.Li(
                    [
                        html.I(className="fas fa-clock"),  # Icon
                        " Time Frame: ",
                        html.Span("Input the number of years with which to calculate compounded inflation. "
                        "For example, "
                        "input '5' to calculate the amount of inflation that took place over a 5 year time span."
                        )
                    ]
                ),
                
                #Describes Add Line button
                html.Li(
                    [
                        html.I(className="fas fa-plus-circle"),  # Icon
                        " Add Line: ",
                        html.Span(
                            "Integrate the compounded inflation rate into the graph. "
                            "This also adds an interactive legend item that hides the line when clicked."
                        )
                    ]
                ),
                
                #Describes reset function
                html.Li(
                    [
                        html.I(className="fas fa-undo"),  # Icon
                        " Reset: ",
                        html.Span("Clears all lines except for the 1 Year inflation rate.")
                    ]
                )
            ]
        )
    ]
)

#Contains the plot and legend
plot_legend= html.Div(
    [
        # The graph is nested in a loading animation section
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
        
        #Custom legend that allows line hiding functionality
        html.Div(
            id='custom-legend',
            style={
                'position': 'absolute',
                'right': '10px',
                'top': '50px',
                'zIndex': 1000
            }
        )
    ],
    style={
        'position': 'relative'
    }
)

#Links to source code
github_link = html.A(
    [
        "Source Code ",
        #Insert GitHub logo
        html.Img(
            src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
            style={
                'height': '20px',
                'padding-bottom': '5px'
            }
        )
    ],
    href="https://github.com/andrewcaniglia/Compounded-Inflation-Calculator",
    target="_blank"
)

# Input fields for start and end years
start_year_input = dcc.Input(
    id='start-year-input',
    type='number',
    placeholder='Start Year',
    value=1914,
    style={
        'width': '80px'
    }
)

end_year_input = dcc.Input(
    id='end-year-input',
    type='number',
    placeholder='End Year',
    value=datetime.now().year,
    style={
        'width': '80px'
    }
)

# Dropdown for data source selection
data_source_dropdown = dcc.Dropdown(
    id='data-source-dropdown',
    options=[{'label': source, 'value': source} for source in data_sources.keys()],
    value='Headline CPI' ,# default value
    style={
        'width': '200px',
        'fontFamily': 'Arial, sans-serif',
        'borderRadius': '5px'
    },
    #No need to delete data source
    clearable=False
)

#Divs for data source dropdown, input box, submit button, reset button, and year range.
control_center = html.Div(
    [
        # Data Source Section (Category)
        html.Div(
            [
                html.Label(
                    'Category',
                    style={
                        'fontWeight': 'bold',
                        'fontSize': '18px'
                    }
                ),
                data_source_dropdown
            ],
            style={
                'border': '1px solid #ccc',
                'padding': '5px',
                'borderRadius': '5px',
                'backgroundColor': '#f8f8f8',
                'boxShadow': '3px 3px 5px #aaa',
                'width': '220px',
                'marginRight': '15px'
            }
        ),

        # Controls Section
        html.Div(
            [
                html.Div(
                
                    [  # Holds the year inputs
                        html.Div(
                            [
                                html.Label(
                                    'Range  ',
                                    style={
                                        'fontWeight': 'bold'
                                    }
                                ),
                                start_year_input,
                                html.Label(
                                    '  -  ',
                                    style={
                                        'fontWeight': 'bold'
                                    }
                                ),
                                end_year_input
                            ],
                            style={
                                'marginRight': '1px'
                            }
                        ),
                    ],
                    style={
                        'display': 'flex',
                        'gap': '0px',
                        'marginBottom': '10px'
                    }
                ),

                # Holds the YoY label and input
                html.Div(
                    [
                        input_box,
                        submit_button,
                        reset_button
                    ]
                )
            ],
            style={
                'border': '1px solid #ccc',
                'padding': '5px',
                'borderRadius': '5px',
                'backgroundColor': '#f8f8f8',
                'boxShadow': '3px 3px 5px #aaa',
                'width': 'auto'
            }
        )
    ],
    style={
    'display': 'flex',
    'gap': '10px',
    'flexDirection': 'row',
    'marginBottom': '10px'
    }
)

#Descriptions of every category of inflation
descriptions = [
    {
        "Category": "Headline CPI",
        "Description": "Encompasses all goods and services in an economy."
    },
    {
        "Category": "Core CPI",
        "Description": "Excludes volatile items such as food and energy prices."
    },
    {
        "Category": "Food",
        "Description": "Measures the change in prices of food items, both at home and away from home."
    },
    {
        "Category": "Grocery",
        "Description": "Focuses on food items bought at grocery stores for consumption at home."
    },
    {
        "Category": "Energy",
        "Description": "Captures price changes in energy commodities, including gasoline, natural gas, and electricity."
    },
    {
        "Category": "Gasoline",
        "Description": "Looks solely at gasoline prices."
    },
    {
        "Category": "Airline",
        "Description": "Reflects changes in the prices of airline tickets."
    },
    {
        "Category": "College",
        "Description": "Focuses on the rising costs of higher education, including tuition, fees, and room and board."
    },
    {
        "Category": "Healthcare",
        "Description": "Captures price changes in healthcare services, including hospital services, doctors' visits, and prescription drugs."
    }
]

#Displays the descriptions in a table
desc_table = html.Div(
    [
        dash_table.DataTable(
            data=descriptions,
            columns=[
                #Creates "Types of Inflation" super header
                {"name": ["Types of Inflation", "Category"], "id": "Category"},
                {"name": ["Types of Inflation", "Description"], "id": "Description"}
            ],
            style_table={
                'height': 'auto',
                'overflowY': 'auto',
                'width': 'fit-content',
                'marginLeft': '0',
                'marginRight': 'auto'
            },
            style_cell={
                'padding': '10px',
                'textAlign': 'left',
                'border': '1px solid #d6d6d6',
                'width': 'auto',
                'whiteSpace': 'normal'
            },
            style_header={
                'fontWeight': 'bold',
                'backgroundColor': '#f2f2f2',
                'border': '1px solid #d6d6d6'
            },
            merge_duplicate_headers=True
        )
    ]
)
