# -*- coding: utf-8 -*-
import os
import subprocess
import shutil
import json
import re
import numpy as np
import matplotlib.pyplot as plt

# Parámetros a variar
app_pkPeriods = [1, 5, 10, 15, 20, 25, 30]
app_pkLengths = [100, 300, 500]
tsch_slotframeLengths = [10, 30, 50, 70, 100]
tsch_tx_queue_sizes = [1, 5, 10, 15, 20, 25, 30]
tsch_max_tx_retries = [0, 1, 2, 3]

# Número de repeticiones para cada configuración
num_repetitions = 30

# Directorios
results_dir = "./results"
output_dir = './graficos'
if not os.path.exists(results_dir):
    os.makedirs(results_dir)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Función para ejecutar el simulador
def run_sim():
    subprocess.call(["python", "runSim.py"])

# Función para mover los archivos generados a la carpeta de resultados
def move_results(destination_base, repetition):
    sim_data_dir = "./simData"
    latest_dir = max([os.path.join(sim_data_dir, d) for d in os.listdir(sim_data_dir) if os.path.isdir(os.path.join(sim_data_dir, d))], key=os.path.getmtime)
    print("Último directorio generado: {}".format(latest_dir))
    
    src_kpi = os.path.join(latest_dir, "exec_numMotes_4.dat.kpi")
    dest_kpi = "{}_rep_{}.dat.kpi".format(destination_base, repetition)
    
    shutil.move(src_kpi, dest_kpi)
    
    print("Archivo movido a {}".format(dest_kpi))

# Función para recolectar resultados de archivos .kpi
def collect_results(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

# Función para extraer datos de un archivo .dat.kpi
def extract_data_from_file(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
        try:
            e2e_upstream_latency_mean = data["0"]["global-stats"]["e2e-upstream-latency"][0]["mean"]
        except KeyError:
            e2e_upstream_latency_mean = None
        try:
            e2e_upstream_delivery_ratio = data["0"]["global-stats"]["e2e-upstream-delivery"][0]["value"]
        except KeyError:
            e2e_upstream_delivery_ratio = None
        try:
            network_lifetime_min = data["0"]["global-stats"]["network_lifetime"][0]["min"]
        except KeyError:
            network_lifetime_min = None
        return e2e_upstream_latency_mean, e2e_upstream_delivery_ratio, network_lifetime_min

# Función para organizar los datos según parámetros específicos
def get_results_by_param(results_dir, varying_param, pattern, fixed_param=None, fixed_value=None):
    results = []
    for filename in os.listdir(results_dir):
        if filename.endswith('.dat.kpi'):
            match = pattern.match(filename)
            if not match:
                continue
            config = {
                "numMotes": match.group(1),
                varying_param: int(match.group(2)),
                "pkLength": int(match.group(3)) if 'pkLength' in pattern.pattern else None,
                "max_retries": int(match.group(3)) if 'max_retries' in pattern.pattern else None
            }

            if fixed_param and str(config[fixed_param]) != str(fixed_value):
                continue

            filepath = os.path.join(results_dir, filename)
            e2e_upstream_latency_mean, e2e_upstream_delivery_ratio, network_lifetime_min = extract_data_from_file(filepath)
            result = {
                varying_param: config[varying_param],
                "latency_avg_s": e2e_upstream_latency_mean,
                "upstream_delivery": e2e_upstream_delivery_ratio,
                "network_lifetime": network_lifetime_min
            }
            if 'pkLength' in pattern.pattern:
                result["pkLength"] = config["pkLength"]
            if 'max_retries' in pattern.pattern:
                result["max_retries"] = config["max_retries"]
            results.append(result)
    return results

# Función para calcular promedios y desviaciones estándar
def calculate_mean_std(results, varying_param, y_param, by_param):
    unique_values = sorted(set(result[by_param] for result in results if result[by_param] is not None))
    stats = {value: {} for value in unique_values}
    for value in unique_values:
        filtered_results = sorted([result for result in results if result[by_param] == value], key=lambda x: x[varying_param])
        for result in filtered_results:
            x_val = result[varying_param]
            y_val = result[y_param]
            if x_val not in stats[value]:
                stats[value][x_val] = []
            stats[value][x_val].append(y_val)
    
    mean_std_results = {value: {"x": [], "mean": [], "std": []} for value in unique_values}
    for value, data in stats.items():
        for x_val, y_vals in data.items():
            filtered_y_vals = [y for y in y_vals if isinstance(y, (int, float))]
            if not filtered_y_vals:
                continue
            mean_std_results[value]["x"].append(x_val)
            mean_std_results[value]["mean"].append(np.mean(filtered_y_vals))
            mean_std_results[value]["std"].append(np.std(filtered_y_vals))
    
    return mean_std_results

# Función para graficar los resultados con promedios y desviaciones estándar
def plot_task_results(results, varying_param, y_param, ylabel, title, filename, by_param):
    plt.figure()
    mean_std_results = calculate_mean_std(results, varying_param, y_param, by_param)
    
    for value, data in mean_std_results.items():
        x = data["x"]
        y_mean = data["mean"]
        y_std = data["std"]
        plt.errorbar(x, y_mean, yerr=y_std, marker='o', label='{} {}'.format(by_param.replace('_', ' ').title(), value))
    
    plt.xlabel(varying_param)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()

# Contador de ejecuciones
total_executions = len(app_pkPeriods) * len(app_pkLengths) * num_repetitions + len(tsch_slotframeLengths) * len(app_pkLengths) * num_repetitions + len(tsch_tx_queue_sizes) * len(tsch_max_tx_retries) * num_repetitions
current_execution = 1

# Tarea 1: Influencia de los patrones de tráfico
for pkPeriod in app_pkPeriods:
    for pkLength in app_pkLengths:
        for repetition in range(num_repetitions):
            dest_kpi = os.path.join(results_dir, "exec_numMotes_4_pkPeriod_{}_pkLength_{}_rep_{}.dat.kpi".format(pkPeriod, pkLength, repetition))
            if os.path.exists(dest_kpi):
                print("Ejecución {}/{} (omitida): pkPeriod={}s, pkLength={} bytes, repetición={}".format(current_execution, total_executions, pkPeriod, pkLength, repetition))
                current_execution += 1
                continue
            print("Ejecución {}/{}: pkPeriod={}s, pkLength={} bytes, repetición={}".format(current_execution, total_executions, pkPeriod, pkLength, repetition))
            with open('config.json', 'r+') as config_file:
                config = json.load(config_file)
                config['settings']['regular']['app_pkPeriod'] = pkPeriod
                config['settings']['regular']['app_pkLength'] = pkLength
                config_file.seek(0)
                json.dump(config, config_file, indent=4)
                config_file.truncate()
            run_sim()
            move_results(os.path.join(results_dir, "exec_numMotes_4_pkPeriod_{}_pkLength_{}".format(pkPeriod, pkLength)), repetition)
            current_execution += 1

pattern_pkPeriod = re.compile(r'exec_numMotes_(\d+)_pkPeriod_(\d+)_pkLength_(\d+)_rep_(\d+).dat.kpi')
task1_results = get_results_by_param(results_dir, 'pkPeriod', pattern_pkPeriod)
plot_task_results(task1_results, 'pkPeriod', 'latency_avg_s', 'End-to-End Delay (s)', 'End-to-End Delay vs Packet Period', 'end_to_end_delay_vs_packet_period.png', 'pkLength')
plot_task_results(task1_results, 'pkPeriod', 'upstream_delivery', 'Packet Delivery Rate (%)', 'Packet Delivery Rate vs Packet Period', 'packet_delivery_rate_vs_packet_period.png', 'pkLength')
plot_task_results(task1_results, 'pkPeriod', 'network_lifetime', 'Network Lifetime (years)', 'Network Lifetime vs Packet Period', 'network_lifetime_vs_packet_period.png', 'pkLength')

# Tarea 2: Influencia de la duración del slotframe
for slotframeLength in tsch_slotframeLengths:
    for pkLength in app_pkLengths:
        for repetition in range(num_repetitions):
            dest_kpi = os.path.join(results_dir, "exec_numMotes_4_slotframeLength_{}_pkLength_{}_rep_{}.dat.kpi".format(slotframeLength, pkLength, repetition))
            if os.path.exists(dest_kpi):
                print("Ejecución {}/{} (omitida): slotframeLength={}, pkLength={} bytes, repetición={}".format(current_execution, total_executions, slotframeLength, pkLength, repetition))
                current_execution += 1
                continue
            print("Ejecución {}/{}: slotframeLength={}, pkLength={} bytes, repetición={}".format(current_execution, total_executions, slotframeLength, pkLength, repetition))
            with open('config.json', 'r+') as config_file:
                config = json.load(config_file)
                config['settings']['regular']['tsch_slotframeLength'] = slotframeLength
                config['settings']['regular']['app_pkLength'] = pkLength
                config_file.seek(0)
                json.dump(config, config_file, indent=4)
                config_file.truncate()
            run_sim()
            move_results(os.path.join(results_dir, "exec_numMotes_4_slotframeLength_{}_pkLength_{}".format(slotframeLength, pkLength)), repetition)
            current_execution += 1

pattern_slotframe = re.compile(r'exec_numMotes_(\d+)_slotframeLength_(\d+)_pkLength_(\d+)_rep_(\d+).dat.kpi')
task2_results = get_results_by_param(results_dir, 'slotframeLength', pattern_slotframe)
plot_task_results(task2_results, 'slotframeLength', 'latency_avg_s', 'End-to-End Delay (s)', 'End-to-End Delay vs Slotframe Length', 'end_to_end_delay_vs_slotframe_length.png', 'pkLength')
plot_task_results(task2_results, 'slotframeLength', 'upstream_delivery', 'Packet Delivery Rate (%)', 'Packet Delivery Rate vs Slotframe Length', 'packet_delivery_rate_vs_slotframe_length.png', 'pkLength')
plot_task_results(task2_results, 'slotframeLength', 'network_lifetime', 'Network Lifetime (years)', 'Network Lifetime vs Slotframe Length', 'network_lifetime_vs_slotframe_length.png', 'pkLength')

# Tarea 3: Influencia del tamaño de la fila de espera y retransmisiones
for queue_size in tsch_tx_queue_sizes:
    for max_retries in tsch_max_tx_retries:
        for repetition in range(num_repetitions):
            dest_kpi = os.path.join(results_dir, "exec_numMotes_4_queue_size_{}_max_retries_{}_rep_{}.dat.kpi".format(queue_size, max_retries, repetition))
            if os.path.exists(dest_kpi):
                print("Ejecución {}/{} (omitida): queue_size={}, max_retries={}, repetición={}".format(current_execution, total_executions, queue_size, max_retries, repetition))
                current_execution += 1
                continue
            print("Ejecución {}/{}: queue_size={}, max_retries={}, repetición={}".format(current_execution, total_executions, queue_size, max_retries, repetition))
            with open('config.json', 'r+') as config_file:
                config = json.load(config_file)
                config['settings']['regular']['tsch_tx_queue_size'] = queue_size
                config['settings']['regular']['tsch_max_tx_retries'] = max_retries
                config_file.seek(0)
                json.dump(config, config_file, indent=4)
                config_file.truncate()
            run_sim()
            move_results(os.path.join(results_dir, "exec_numMotes_4_queue_size_{}_max_retries_{}".format(queue_size, max_retries)), repetition)
            current_execution += 1

pattern_queue_size = re.compile(r'exec_numMotes_(\d+)_queue_size_(\d+)_max_retries_(\d+)_rep_(\d+).dat.kpi')
task3_results = get_results_by_param(results_dir, 'queue_size', pattern_queue_size)
plot_task_results(task3_results, 'queue_size', 'latency_avg_s', 'End-to-End Delay (s)', 'End-to-End Delay vs Queue Size', 'end_to_end_delay_vs_queue_size.png', 'max_retries')
plot_task_results(task3_results, 'queue_size', 'upstream_delivery', 'Packet Delivery Rate (%)', 'Packet Delivery Rate vs Queue Size', 'packet_delivery_rate_vs_queue_size.png', 'max_retries')
plot_task_results(task3_results, 'queue_size', 'network_lifetime', 'Network Lifetime (years)', 'Network Lifetime vs Queue Size', 'network_lifetime_vs_queue_size.png', 'max_retries')

print("Simulaciones completadas. Los resultados se guardaron en el directorio {} y los gráficos se guardaron en el directorio {}".format(results_dir, output_dir))
