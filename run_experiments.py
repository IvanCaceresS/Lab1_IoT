# -*- coding: utf-8 -*-
import os
import subprocess
import shutil
import json

# Parámetros a variar
app_pkPeriods = [1, 5, 10, 15, 20, 25, 30]
app_pkLengths = [100, 300, 500]
tsch_slotframeLengths = [10, 30, 50, 70, 100]
tsch_tx_queue_sizes = [1, 5, 10, 15, 20, 25, 30]
tsch_max_tx_retries = [0, 1, 2, 3]

# Directorio para los resultados
results_dir = "./results"
if not os.path.exists(results_dir):
    os.makedirs(results_dir)

# Función para ejecutar el simulador
def run_sim():
    subprocess.call(["python", "runSim.py"])

# Función para mover los archivos generados a la carpeta de resultados
def move_results(destination_base):
    sim_data_dir = "./simData"
    latest_dir = max([os.path.join(sim_data_dir, d) for d in os.listdir(sim_data_dir) if os.path.isdir(os.path.join(sim_data_dir, d))], key=os.path.getmtime)
    print("Último directorio generado: {}".format(latest_dir))
    
    src_dat = os.path.join(latest_dir, "exec_numMotes_4.dat")
    src_kpi = os.path.join(latest_dir, "exec_numMotes_4.dat.kpi")
    
    dest_dat = "{}.dat".format(destination_base)
    dest_kpi = "{}.dat.kpi".format(destination_base)
    
    shutil.move(src_dat, dest_dat)
    shutil.move(src_kpi, dest_kpi)
    
    print("Archivos movidos a {} y {}".format(dest_dat, dest_kpi))

# Función para recolectar resultados de archivos .kpi
def collect_results(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

# Función para analizar y recolectar datos de los resultados
def analyze_results(results_dir):
    collected_data = {}
    for root, dirs, files in os.walk(results_dir):
        for file in files:
            if file.endswith(".dat.kpi"):
                file_path = os.path.join(root, file)
                data = collect_results(file_path)
                # Extraer la configuración y métricas
                config_key = file.split('.')[0]
                collected_data[config_key] = data
    return collected_data

# Tarea 1: Influencia de los patrones de tráfico
for pkPeriod in app_pkPeriods:
    for pkLength in app_pkLengths:
        print("Ejecutando simulación para pkPeriod={}s, pkLength={} bytes".format(pkPeriod, pkLength))
        with open('config.json', 'r+') as config_file:
            config = json.load(config_file)
            config['settings']['regular']['app_pkPeriod'] = pkPeriod
            config['settings']['regular']['app_pkLength'] = pkLength
            config_file.seek(0)
            json.dump(config, config_file, indent=4)
            config_file.truncate()
        run_sim()
        move_results(os.path.join(results_dir, "exec_numMotes_4_pkPeriod_{}_pkLength_{}".format(pkPeriod, pkLength)))

# Tarea 2: Influencia de la duración del slotframe
for slotframeLength in tsch_slotframeLengths:
    for pkLength in app_pkLengths:
        print("Ejecutando simulación para slotframeLength={}, pkLength={} bytes".format(slotframeLength, pkLength))
        with open('config.json', 'r+') as config_file:
            config = json.load(config_file)
            config['settings']['regular']['tsch_slotframeLength'] = slotframeLength
            config['settings']['regular']['app_pkLength'] = pkLength
            config_file.seek(0)
            json.dump(config, config_file, indent=4)
            config_file.truncate()
        run_sim()
        move_results(os.path.join(results_dir, "exec_numMotes_4_slotframeLength_{}_pkLength_{}".format(slotframeLength, pkLength)))

# Tarea 3: Influencia del tamaño de la fila de espera y retransmisiones
for queue_size in tsch_tx_queue_sizes:
    for max_retries in tsch_max_tx_retries:
        print("Ejecutando simulación para queue_size={}, max_retries={}".format(queue_size, max_retries))
        with open('config.json', 'r+') as config_file:
            config = json.load(config_file)
            config['settings']['regular']['tsch_tx_queue_size'] = queue_size
            config['settings']['regular']['tsch_max_tx_retries'] = max_retries
            config_file.seek(0)
            json.dump(config, config_file, indent=4)
            config_file.truncate()
        run_sim()
        move_results(os.path.join(results_dir, "exec_numMotes_4_queue_size_{}_max_retries_{}".format(queue_size, max_retries)))

# Analizar y recolectar todos los resultados
collected_data = analyze_results(results_dir)

# Guardar los datos recolectados en un archivo JSON
with open('collected_results.json', 'w') as f:
    json.dump(collected_data, f, indent=4)

print("Simulaciones completadas. Los resultados se guardaron en el directorio {} y los datos recolectados se guardaron en 'collected_results.json'".format(results_dir))
