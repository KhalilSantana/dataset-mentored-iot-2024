import pandas as pd
import argparse
import matplotlib.pyplot as plt
from tqdm.auto import tqdm



def read_data(file_path):
    data = pd.read_csv(file_path)
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], format='%H:%M:%S.%f')
    return data



def compute_metrics(data, freq='S'):
    data.set_index('Timestamp', inplace=True)

    # Start counting the timestamp from 0
    data.index = data.index - data.index[0]
    throughput = data['Packet Size'].resample(freq).sum()  # Sum of packet sizes
    packet_counts = data['Packet Size'].resample(freq).count()  # Count of packets
    return throughput, packet_counts



def plot_metrics(throughput, packet_counts, freq, fontsize, expected_time):
    fig, ax1 = plt.subplots(figsize=(12, 6))
    # convert expected_time to Timedelta
    expected_time = pd.Timedelta(seconds=expected_time)
    color = 'tab:red'
    ax1.set_xlabel('Tempo (segundos)', fontsize=fontsize, fontweight='bold')
    ax1.set_ylabel('Vazão (MB)', color=color, fontsize=fontsize, fontweight='bold')

    # Plot x axis as time
    # "Recover" the initial part not captured in the pcap file
    # data_x = throughput.index/1000000000
    data_x = throughput.index
    print(max(throughput.index))
    print(expected_time)
    if max(data_x) < expected_time:
        data_x = data_x + (expected_time - max(data_x))
   
    ax1.plot(data_x/1000000000, throughput.values/(2**20), color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()

    color = 'tab:blue'
    ax2.set_ylabel('Número de Pacotes', color=color, fontsize=fontsize, fontweight='bold')

    data_x = packet_counts.index
    if max(data_x) < expected_time:
        data_x = data_x + (expected_time - max(data_x))

    ax2.plot(data_x/1000000000, packet_counts.values, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    # Avoid using scientific notation
    ax1.get_xaxis().get_major_formatter().set_scientific(False)
    ax1.get_yaxis().get_major_formatter().set_scientific(False)
    ax2.get_yaxis().get_major_formatter().set_scientific(False)

    # Set font size
    ax1.tick_params(axis='both', which='major', labelsize=fontsize)
    ax2.tick_params(axis='both', which='major', labelsize=fontsize)

    plt.savefig(f'../output_{freq}.png', dpi=300)


def filter_to_experiment_duration(data, unix_timestamp, duration):
    #  For a DF with:
    # Timestamp,Packet Size
    # 19:33:32.399970,60
    # Filter the data such that only the data between unix_timestamp and unix_timestamp + duration is kept
    # The Timestamp column is in the format %H:%M:%S.%f
    # The unix_timestamp is in seconds since the unix epoch
    # The duration is in seconds

    start_time = pd.Timestamp(unix_timestamp, unit='s')
    # get hours only from start time
    # Consider that the data PD timestamps don't have a date, only the time
    start_time = start_time.replace(year=1900, day=1, month=1)
    end_time = start_time + pd.Timedelta(seconds=duration)
    data_start = data['Timestamp'].iloc[0]
    data_start = pd.Timestamp(data_start, unit='s')

    print(f"Start capture data: {data_start}")
    filtered_data = data[(data['Timestamp'] >= start_time) & (data['Timestamp'] <= end_time)]
    print(f"Start time: {start_time}")
    print(filtered_data)
    return filtered_data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--input_file', dest='input_file', required=True)
    parser.add_argument('-s', '--fontsize', dest='fontsize', type=int, default=12, help='Font size for the plot')
    parser.add_argument('-t', '--expected_time', dest='time', type=int, default=60, help='Experiment expected time in seconds')
    parser.add_argument('-u', '--unix_timestamp', dest='unix_timestamp', type=int, help='Unix timestamp of experiment start')

    args = parser.parse_args()
    file_path = args.input_file
    expected_time = args.time
    # freq_options = {'S': 'Second', 'T': 'Minute', 'H': 'Hour', 'D': 'Day', 'M': 'Month', 'Y': 'Year'}

    freq_options = {'S': 'Second'}

    data = read_data(file_path)
    data = filter_to_experiment_duration(data, args.unix_timestamp, args.time)

    for freq, label in tqdm(freq_options.items(), desc="Computing and plotting metrics"):
        throughput, packet_counts = compute_metrics(data, freq=freq)
        plot_metrics(throughput, packet_counts, label, args.fontsize, expected_time)


if __name__ == '__main__':
    main()