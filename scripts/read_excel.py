import pandas as pd
import numpy as np
import os


path =  "canada_fsa_climate_footprint.csv"

def replace_empty(file):
    df = pd.read_csv(file)
    total_missing = df.isna().sum().sum()
    missing_columns = df.isna().sum()
    if total_
    print(total_missing)
    print(missing_columns)
replace_empty(path)

