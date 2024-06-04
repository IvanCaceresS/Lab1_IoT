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
        e2e_upstream_latency_mean = data["0"]["global-stats"]["e2e-upstream-latency"][0]["mean"]
        e2e_upstream_delivery_ratio = data["0"]["global-stats"]["e2e-upstream-delivery"][0]["value"]
        network_lifetime_min = data["0"]["global-stats"]["network_lifetime"][0]["min"]
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
                "max_retries": int(match.group(3)) if 'max_retries' in pattern.pattern else None,
                "rep": int(match.group(4)) if 'rep' in pattern.pattern else None
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

# Función para calcular la media y la varianza de los resultados
def calculate_statistics(results, varying_param):
    grouped_results = {}
    for result in results:
        key = result[varying_param]
        if key not in grouped_results:
            grouped_results[key] = {
                'latency_avg_s': [],
                'upstream_delivery': [],
                'network_lifetime': []
            }
        grouped_results[key]['latency_avg_s'].append(result['latency_avg_s'])
        grouped_results[key]['upstream_delivery'].append(result['upstream_delivery'])
        grouped_results[key]['network_lifetime'].append(result['network_lifetime'])

    statistics = []
    for key, values in grouped_results.items():
        statistics.append({
            varying_param: key,
            'latency_avg_s_mean': np.mean(values['latency_avg_s']),
            'latency_avg_s_var': np.var(values['latency_avg_s']),
            'upstream_delivery_mean': np.mean(values['upstream_delivery']),
            'upstream_delivery_var': np.var(values['upstream_delivery']),
            'network_lifetime_mean': np.mean(values['network_lifetime']),
            'network_lifetime_var': np.var(values['network_lifetime'])
        })

    return statistics

# Función para graficar los resultados
def plot_task_results(statistics, varying_param, y_param, ylabel, title, filename, by_param):
    plt.figure()
    unique_values = sorted(set(stat[by_param] for stat in statistics))
    
    for value in unique_values:
        filtered_stats = sorted([stat for stat in statistics if stat[by_param] == value], key=lambda x: x[varying_param])
        x = [stat[varying_param] for stat in filtered_stats]
        y = [stat['{}_mean'.format(y_param)] for stat in filtered_stats]
        y_err = [stat['{}_var'.format(y_param)] for stat in filtered_stats]
        plt.errorbar(x, y, yerr=y_err, marker='o', label='{} {}'.format(by_param.replace('_', ' ').title(), value))
    
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
task1_stats = calculate_statistics(task1_results, 'pkPeriod')
plot_task_results(task1_stats, 'pkPeriod', 'latency_avg_s', 'End-to-End Delay (s)', 'End-to-End Delay vs Packet Period', 'end_to_end_delay_vs_packet_period.png', 'pkLength')
plot_task_results(task1_stats, 'pkPeriod', 'upstream_delivery', 'Packet Delivery Rate (%)', 'Packet Delivery Rate vs Packet Period', 'packet_delivery_rate_vs_packet_period.png', 'pkLength')
plot_task_results(task1_stats, 'pkPeriod', 'network_lifetime', 'Network Lifetime (years)', 'Network Lifetime vs Packet Period', 'network_lifetime_vs_packet_period.png', 'pkLength')

# Tarea 2: Influencia de la duración del slotframe
for slotframeLength in tsch_slotframeLengths:
    for pkLength in app_pkLengths:
        for repetition in range(num_repetitions):
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
task2_stats = calculate_statistics(task2_results, 'slotframeLength')
plot_task_results(task2_stats, 'slotframeLength', 'latency_avg_s', 'End-to-End Delay (s)', 'End-to-End Delay vs Slotframe Length', 'end_to_end_delay_vs_slotframe_length.png', 'pkLength')
plot_task_results(task2_stats, 'slotframeLength', 'upstream_delivery', 'Packet Delivery Rate (%)', 'Packet Delivery Rate vs Slotframe Length', 'packet_delivery_rate_vs_slotframe_length.png', 'pkLength')
plot_task_results(task2_stats, 'slotframeLength', 'network_lifetime', 'Network Lifetime (years)', 'Network Lifetime vs Slotframe Length', 'network_lifetime_vs_slotframe_length.png', 'pkLength')

# Tarea 3: Influencia del tamaño de la fila de espera y retransmisiones
for queue_size in tsch_tx_queue_sizes:
    for max_retries in tsch_max_tx_retries:
        for repetition in range(num_repetitions):
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
task3_stats = calculate_statistics(task3_results, 'queue_size')
plot_task_results(task3_stats, 'queue_size', 'latency_avg_s', 'End-to-End Delay (s)', 'End-to-End Delay vs Queue Size', 'end_to_end_delay_vs_queue_size.png', 'max_retries')
plot_task_results(task3_stats, 'queue_size', 'upstream_delivery', 'Packet Delivery Rate (%)', 'Packet Delivery Rate vs Queue Size', 'packet_delivery_rate_vs_queue_size.png', 'max_retries')
plot_task_results(task3_stats, 'queue_size', 'network_lifetime', 'Network Lifetime (years)', 'Network Lifetime vs Queue Size', 'network_lifetime_vs_queue_size.png', 'max_retries')

print("Simulaciones completadas. Los resultados se guardaron en el directorio {} y los gráficos se guardaron en el directorio {}".format(results_dir, output_dir))
