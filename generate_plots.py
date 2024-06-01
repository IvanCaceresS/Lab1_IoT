# -*- coding: utf-8 -*-
import os
import json
import re
import matplotlib.pyplot as plt

results_dir = './results'
output_dir = './graficos'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

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

# Función para graficar los resultados
def plot_task_results(results, varying_param, y_param, ylabel, title, filename, by_param):
    plt.figure()
    unique_values = sorted(set(result[by_param] for result in results))
    
    for value in unique_values:
        filtered_results = sorted([result for result in results if result[by_param] == value], key=lambda x: x[varying_param])
        x = [result[varying_param] for result in filtered_results]
        y = [result[y_param] for result in filtered_results]
        plt.plot(x, y, marker='o', label='{} {}'.format(by_param.replace('_', ' ').title(), value))
    
    plt.xlabel(varying_param)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()

# Tarea 1: Influencia de los patrones de tráfico
pattern_pkPeriod = re.compile(r'exec_numMotes_(\d+)_pkPeriod_(\d+)_pkLength_(\d+).dat.kpi')
task1_results = get_results_by_param(results_dir, 'pkPeriod', pattern_pkPeriod)
plot_task_results(task1_results, 'pkPeriod', 'latency_avg_s', 'End-to-End Delay (s)', 'End-to-End Delay vs Packet Period', 'end_to_end_delay_vs_packet_period.png', 'pkLength')
plot_task_results(task1_results, 'pkPeriod', 'upstream_delivery', 'Packet Delivery Rate', 'Packet Delivery Rate vs Packet Period', 'packet_delivery_rate_vs_packet_period.png', 'pkLength')
plot_task_results(task1_results, 'pkPeriod', 'network_lifetime', 'Network Lifetime (years)', 'Network Lifetime vs Packet Period', 'network_lifetime_vs_packet_period.png', 'pkLength')

# Tarea 2: Influencia de la duración del slotframe
pattern_slotframe = re.compile(r'exec_numMotes_(\d+)_slotframeLength_(\d+)_pkLength_(\d+).dat.kpi')
task2_results = get_results_by_param(results_dir, 'slotframeLength', pattern_slotframe)
plot_task_results(task2_results, 'slotframeLength', 'latency_avg_s', 'End-to-End Delay (s)', 'End-to-End Delay vs Slotframe Length', 'end_to_end_delay_vs_slotframe_length.png', 'pkLength')
plot_task_results(task2_results, 'slotframeLength', 'upstream_delivery', 'Packet Delivery Rate', 'Packet Delivery Rate vs Slotframe Length', 'packet_delivery_rate_vs_slotframe_length.png', 'pkLength')
plot_task_results(task2_results, 'slotframeLength', 'network_lifetime', 'Network Lifetime (years)', 'Network Lifetime vs Slotframe Length', 'network_lifetime_vs_slotframe_length.png', 'pkLength')

# Tarea 3: Influencia del tamaño de la fila de espera y la cantidad de retransmisiones
pattern_queue_size = re.compile(r'exec_numMotes_(\d+)_queue_size_(\d+)_max_retries_(\d+).dat.kpi')
task3_results = get_results_by_param(results_dir, 'queue_size', pattern_queue_size)
plot_task_results(task3_results, 'queue_size', 'latency_avg_s', 'End-to-End Delay (s)', 'End-to-End Delay vs Queue Size', 'end_to_end_delay_vs_queue_size.png', 'max_retries')
plot_task_results(task3_results, 'queue_size', 'upstream_delivery', 'Packet Delivery Rate', 'Packet Delivery Rate vs Queue Size', 'packet_delivery_rate_vs_queue_size.png', 'max_retries')
plot_task_results(task3_results, 'queue_size', 'network_lifetime', 'Network Lifetime (years)', 'Network Lifetime vs Queue Size', 'network_lifetime_vs_queue_size.png', 'max_retries')
