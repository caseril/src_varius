import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pylab
import itertools
import datetime
from datetime import datetime
import math
import os.path
import os
from pathlib import Path
import shutil
import random

def  resampleCsv(dataDir:str, ts:str = '50ms', 
timeColumn:str = 'Time',
    dateFormat:str ='%Y-%m-%d %H:%M:%S', mtd:str='linear', interpolation:str = 'mean', ignoreTime:bool=True) -> pd.DataFrame :

    if (dataDir == None): return None
    if not(os.path.isfile(dataDir)): return None
    
    #Import dati portata alle Remi
    timeValueData: pd.DataFrame = pd.read_csv(dataDir)
    timeValueData[timeColumn]=pd.to_datetime(timeValueData[timeColumn], format = dateFormat)

    if(interpolation == 'mean'): 
        timeValueData= timeValueData.resample(ts, on = timeColumn).mean()
    elif(interpolation == 'sum'): 
        timeValueData= timeValueData.resample(ts, on = timeColumn).sum()
    elif(interpolation == 'pad'):
        timeValueData= timeValueData.resample(ts, on = timeColumn).pad()
    else: return None

    timeValueData = timeValueData.interpolate(method = mtd)
    if (ignoreTime):
        return pd.DataFrame(data=timeValueData.values) 
    return timeValueData


def getAllCsv(dir:str=None):
    farr=[]
    # acquisizione della directory della cartella di lavoro
    if not(dir) :
        cwd = os.getcwd() #os.listdir('.')
    else:
        cwd = dir
    # acquisizione dell'elenco dei file csv presenti nella directory.
    files = [f for f in os.listdir('.') if (os.path.isfile(f))]
    for f in files:
        if(f.lower().endswith('.csv')):
            farr.append(f)
    return farr


def outReport(data, outputDir) -> None:
    if not len(data) > 0 : return
    result:pd.DataFrame = pd.concat(data, axis=1)
    result.to_csv(outputDir)

def moveDataCsv2History(farr, historyDir) -> None:
    Path(historyDir).mkdir(parents=True, exist_ok=True)
    for f in farr:
        shutil.move(f, historyDir+'/'+f)



if __name__ == "__main__":
    #dataColumn='MASSFLOW', mtd='linear', interpolation='mean')

    ylabel = 'Portata [sm^3/h]'
    title = 'Confronto dati Portata'
    ts = '900s'
    timeColumn = 'Time'
    valueColumn = 'MASSFLOW'
    dateFormat:str ='%Y-%m-%d %H:%M:%S'
    interp_method = 'linear'
    interpolation = 'mean'
    ignoreTime:bool = True

    colors = ["blue", "black", "red", "red"]
    linestyles = ['-','-.','--',':', ]

    now_str = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    outputDir:str = './Result/out'+now_str+'.csv'
    historyDir:str = './History/inputs'+title+'_'+now_str


    arrFiles=[]
    data=[]
    arrFiles = getAllCsv()
    arrFiles.sort()
    fig, ax = plt.subplots()
    for f in arrFiles:
        res = resampleCsv(f,ts, timeColumn, dateFormat, interp_method, interpolation, ignoreTime)
        data.append(res)
        ax.plot(res.values, color=random.choice(colors), linestyle=random.choice(linestyles), label = f)

    # Spostamento dei file nelle rispettive directory al termine delle operazioni.
    outReport(data, outputDir)
    moveDataCsv2History(arrFiles, historyDir)

    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.show()

    

    
