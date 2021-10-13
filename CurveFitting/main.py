import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pylab
import itertools
import datetime
from datetime import datetime
from logger import logging
import math
import os.path
import os
from pathlib import Path
import shutil
from scipy.signal import butter, lfilter, freqz, lfilter_zi, filtfilt


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5, zi_val=0):
    b, a = butter_lowpass(cutoff, fs, order=order)
    zi=lfilter_zi(b,a)*zi_val
    z, _    = lfilter(b, a, data, zi=zi)
    z2,_    = lfilter(b, a, z, zi=zi*z[0])
    y       = filtfilt(b, a, data)
    return y, z, z2

def hand_made_lowpass_2(x, cutoff, fs, order, zi_val=0):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y=x.copy()
    for j in range(len(x)):
        i=order
        y[j]=0
        while(j>=i and i>0):
            y[j]=y[j] + b[i]*x[j-i] - a[i]*y[j-i]   
            i-=1           
        y[j]=y[j]+b[0]*x[j]
        y[j]=(1/a[0])*y[j]
    return y

def hand_made_lowpass(x, cutoff, fs, order, zi_val=0):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y=x.copy()
    d=np.full((order+1,1), 0)
    for j in range(len(x)):
        i=order-1
        while (i):
            if (j >= i):
                d[i - 1,0] = b[i] * x[j - i] - a[i] * y[j - i] + d[i,0]
            i-=1
        y[i] = b[0] * x[i] + d[0,0]
        y[i] = y[i]/a[0]
    return y

if __name__=='__main__':
    print("::STARTING::")   

    # Filter requirements.
    order = 2
    fs = 1      # sample rate, Hz
    cutoff = 1/100  # desired cutoff frequency of the filter, Hz


    # Get the filter coefficients so we can check its frequency response.
    b, a = butter_lowpass(cutoff, fs, order)

    # colonne
    meas = ['RAW_1', 'RAW_2']
    filtered = ['FILTERED']

    # dati random
    data = {}
    T = 1000
    x = np.arange(0,T)
    max_val = 1
    min_val = 0

    sin_wave = 4*np.sin(4*np.pi*x/T)
    noise = np.random.uniform(min_val, max_val, size=T)
    noisy_sin_wave = sin_wave + noise

    data[meas[0]] = pd.DataFrame(noisy_sin_wave, columns = ['value'])



    # Plot the frequency response.
    w, h = freqz(b, a, worN=8000)
    plt.subplot(2, 1, 1)
    plt.plot(0.5*fs*w/np.pi, np.abs(h), 'b')
    plt.plot(cutoff, 0.5*np.sqrt(2), 'ko')
    plt.axvline(cutoff, color='k')
    plt.xlim(0, 0.5*fs)
    plt.title("Lowpass Filter Frequency Response")
    plt.xlabel('Frequency [Hz]')
    plt.grid()


    # Filter the data, and plot both the original and filtered signals.
    data[filtered[0]] = data[meas[0]].copy()
    zi_val=data[meas[0]]['value'][0]
    y, z, z2 = butter_lowpass_filter(data[meas[0]]['value'], cutoff, fs, order, zi_val)
    data[filtered[0]]['value_y'] = y
    data[filtered[0]]['value_z'] = z
    data[filtered[0]]['value_z2'] = z2
    data[filtered[0]]['value_hm'] = hand_made_lowpass_2(data[meas[0]]['value'], cutoff, fs, order, zi_val)


    plt.subplot(2, 1, 2)
    #plt.plot(data[meas[0]], 'b-', label='RAW')
    plt.plot(data[filtered[0]].index, data[filtered[0]]['value_y'], 'g.', linewidth=1, label='RAW_FILTERED_y')
    plt.plot(data[filtered[0]].index, data[filtered[0]]['value_z'], 'y.', linewidth=1, label='RAW_FILTERED_z')
    plt.plot(data[filtered[0]].index, data[filtered[0]]['value_z2'], 'pink', linewidth=1, label='RAW_FILTERED_z2')
    plt.plot(data[filtered[0]].index, data[filtered[0]]['value_hm'], 'r.', linewidth=1, label='RAW_FILTERED_hm')
    plt.plot(data[meas[0]], 'black', linewidth=1, label='RAW')
    plt.xlabel('Time [sec]')
    plt.grid()
    plt.legend()

    plt.subplots_adjust(hspace=0.35)
    plt.show()
    print('::END::')