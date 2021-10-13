import numpy as np
import matplotlib.pyplot as plt

import sys
import os

def get_g_from_flow_and_setpoint(time_array, flow_array, sp):
	mass_mg = np.zeros_like(time_array)
	
	for i in range(1, time_array.size):
		mass_mg[i] = sp*flow_array[i]*(time_array[i] - time_array[i-1])/3600. + mass_mg[i-1]
	
	return mass_mg/1000.

def get_g_from_bilancia(bilancia_array):
	return (bilancia_array - bilancia_array[0])

def get_g_corrected_from_flow_and_setpoint(time_array, flow_array, sp, act, dyn):
	mass_g = get_g_from_flow_and_setpoint(time_array, flow_array, sp)
	
	unique_dyn = list()
	
	
	for d in dyn:
		if d not in unique_dyn:
			unique_dyn.append(d)
	
	unique_dyn = np.asarray(unique_dyn)
	
	for i in range(1, unique_dyn.size):
		
		d_mask = dyn == unique_dyn[i-1]
		
		mass_g[d_mask] = mass_g[d_mask]*unique_dyn[i]/act[d_mask]

	return mass_g

def get_error(bilancia_array, flow_array): 
	return (bilancia_array - flow_array)*100./bilancia_array

if __name__ == '__main__':
    folder_path = str(sys.argv[1])
    time_array = np.loadtxt(os.path.join(folder_path, "time.txt"))
    bilancia_array = np.loadtxt(os.path.join(folder_path, "bilancia.txt"))
    flow_array = np.loadtxt(os.path.join(folder_path, "portata.txt"))
    r_act_array = np.loadtxt(os.path.join(folder_path, "r_act.txt"))
    r_dyn_array = np.loadtxt(os.path.join(folder_path, "r_dyn.txt"))
    
    
    g_bilancia = get_g_from_bilancia(bilancia_array)
    g_from_flow = get_g_from_flow_and_setpoint(time_array, flow_array, 22.)
    
    fig = plt.figure(1)
    DPI = fig.get_dpi()
    fig.set_size_inches(float(800) / float(DPI), float(600) / float(DPI))
    plt.plot(time_array - time_array[0], g_bilancia, '-o')
    plt.plot(time_array - time_array[0], g_from_flow)
    plt.plot(time_array - time_array[0], get_g_corrected_from_flow_and_setpoint(time_array, flow_array, 22., r_act_array, r_dyn_array))
    plt.xlabel("Time [s]")
    plt.ylabel("Mass [g]")
    plt.title(folder_path.split("/")[1])
    plt.legend(["Bilancia", "From flow", "From level"])
    plt.savefig("img/mass_" + folder_path.split("/")[1] + ".svg", dpi=DPI)
    
    
    fig = plt.figure(2)
    DPI = fig.get_dpi()
    fig.set_size_inches(float(800) / float(DPI), float(600) / float(DPI))
    plt.plot(time_array - time_array[0], get_error(g_bilancia, g_from_flow))
    plt.xlabel("Time [s]")
    plt.ylabel("Error [%]")
    plt.title(folder_path.split("/")[1])
    plt.ylim([0,35])
    plt.savefig("img/error_" + folder_path.split("/")[1] + ".svg", dpi=DPI)
    plt.show()
    
