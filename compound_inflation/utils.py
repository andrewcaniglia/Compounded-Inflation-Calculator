from math import fmod

import numpy as np
import pandas as pd

#Calculates cumulative interest rates based on the input year
def calculate_yoy(df_ref, years):
    # Create an empty DataFrame to store the YoY calculations
    result = pd.DataFrame(index=df_ref.index, columns=[f'Compounded_YoY_{years}'])
    
    # Create a list to hold the values for each year
    cols_to_multiply = [df_ref['1 Year']]
    
    # Generate a date range for each year to look back, accounting for monthly data
    for i in range(1, years):
        shifted_col = df_ref['1 Year'].shift(i * 12)
        cols_to_multiply.append(shifted_col.rename(f'Offset_{i}_Year'))
    
    # Concatenate the columns into one DataFrame
    df_with_shifted = pd.concat(cols_to_multiply, axis=1)
    
    # Calculate the compounded YoY change
    df_with_shifted['Total'] = df_with_shifted.apply(
        lambda x: np.prod((x / 100) + 1) if all(~np.isnan(x)) else np.nan, axis=1
    )

    # Convert the total change to percentage and round off
    result[f'Compounded_YoY_{years}'] = ((df_with_shifted['Total'] - 1) * 100).round(1)
    
    # Convert the 'Compounded_YoY' column to float
    result[f'Compounded_YoY_{years}'] = result[f'Compounded_YoY_{years}'].astype(float)

    return result
    
#Generates distinct colors to assign to each new line added to the chart
def get_distinct_colors(n, start_hue=240):
    golden_angle = 137.5
    #Holds colors used
    colors = []
    for i in range(n):
        #Ensures the colors are very distinct in hue
        hue = fmod(i * golden_angle + start_hue, 360)
        colors.append(f'hsl({int(hue)}, 50%, 50%)')
    return colors
