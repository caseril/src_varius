import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pylab
import itertools
import datetime
from datetime import datetime
import math
import os, os.path
from pathlib import Path
import shutil
from scipy.signal import butter, lfilter, freqz, lfilter_zi, filtfilt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from aenum import Enum, auto
import json


def resample_all_tests(tsts, time_colum:str, ts:str, label:str='right', closed:str = 'right', origin:str='epoch'):
    if origin == 'epoch':
        for tst in tsts:
            for d in tst['DATA']:
                    d['DATA'].index = pd.to_datetime(d['DATA'][time_column], unit='s')
                    df = d['DATA']
                    d['DATA'] = df.resample(ts, label=closed, closed=closed).pad()
    return tsts


def get_all_tests(dir: str):
    '''
    Acquisizione di tutti i dati in formato df
    '''
    tests = []
    for root, dirs, files in os.walk(data_dir, topdown=False):
        tests.append({
            'NAME': os.path.basename(root), 
            'DATA':[{'NAME': root + '/' + f, 'DATA': pd.read_csv(root + '/' + f)} for f in files]
            })
    return tests

def add_sqrt_column(df:pd.DataFrame, column_name: str):
    df[column_name+' sqrt']=np.sqrt(df[column_name])


def add_sqrt_column_to_all_tests(tests, column_name: str)-> str:
    for t in tests:
        for d in t['DATA']:
            add_sqrt_column(d['DATA'], column_name)
    return like_in_list(tests[0]['DATA'][0]['DATA'].columns, [column_name, 'sqrt'])[0]


def like_in_list(ref:list, checks:list):
    return [r for r in ref if all(c.lower() in r.lower() for c in checks)]


def add_col_variation_by_col_ref(df: pd.DataFrame, col_variation: str, col_ref: str = 'time', delta = -1):
    return df[col_variation].diff()

def filter_by_std(df: pd.DataFrame, column:str, coeff=1)-> pd.DataFrame:
    descr = df[column].describe()
    return df.loc[
        (df[column] >= (descr['mean'] - descr['std']*coeff)) & 
        (df[column] <= (descr['mean'] + descr['std']*coeff)) 
        ]



if __name__ == "__main__":

    data_dir='data/input/'
    sampling_time = '2000ms'

    # Acquisizione di tutti i dati
    tsts = get_all_tests(data_dir)

    # Lettura dei nomi delle colonne
    col_names =tsts[0]['DATA'][0]['DATA'].columns
    press_column = like_in_list(col_names, ['press'])[0]
    mass_column = like_in_list(col_names, ['mass'])[0]
    n_inj_column = like_in_list(col_names, ['inject'])[0]
    time_column = like_in_list(col_names, ['time'])[0]

    # Resampling
    tsts = resample_all_tests(tsts, time_column, sampling_time)

    # Introduzione del quadrato della pressione e acquisizione del nome della colonna
    sqrt_press_column = add_sqrt_column_to_all_tests(tsts, press_column)

    # DataFrame di riferimento
    d_test:pd.DataFrame = tsts[0]['DATA'][0]['DATA']

    # mass ratio
    d_test[mass_column + ' fst_der'] = d_test[mass_column] / (d_test[n_inj_column] +1 - d_test[n_inj_column].min())
    d_test[mass_column + ' diff'] = add_col_variation_by_col_ref(d_test, mass_column)

    # riacquisizione nome
    mass_fst_der_column = like_in_list(d_test.columns, ['mass', 'fst_der'])[0]

    # test ratio filtered
    d_test_filtered = filter_by_std(d_test, mass_fst_der_column, 3)

    # Regressione lineare
    length = len(d_test_filtered[sqrt_press_column].values)
    x = d_test_filtered[sqrt_press_column].values.reshape(length, 1)
    y = d_test_filtered[mass_fst_der_column].values.reshape(length, 1)
    reg = LinearRegression().fit(x, y)


    # PLOT DATA
    plt.subplot(2,1,1)
    plt.title("DELTA_MASS / time")
    plt.plot(d_test.index, d_test[mass_fst_der_column ])
    plt.grid()
    
    plt.subplot(2,1,2)
    plt.title("DELTA MASS / SQRT(PRESSURE)")
    plt.plot(d_test_filtered[sqrt_press_column], d_test_filtered[mass_fst_der_column])
    plt.plot(x, reg.predict(x))
    plt.grid()

    plt.show()

    print('FINE')

    
    #plt.plot(df_data)
    #plt.show()