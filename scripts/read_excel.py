import pandas as pd

path =  "canada_fsa_climate_footprint.csv"

def clean_data(path):
    '''
    Reads in a file and cleans it 
    '''
    df = read.csv(path, header=3, thousands=",")


clean_data(path)

