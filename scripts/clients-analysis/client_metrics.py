import os
import sys
import numpy as np
import argparse
import logging
logger = logging.getLogger()
from tqdm import tqdm


def read_csv_files(directory):
    data = []

    # Walk through all subdirectories and files
    for root, _, files in os.walk(directory):
        csv_files = [file for file in files if file.endswith('.csv')]
        logger.debug(csv_files)
        for file in tqdm(csv_files, desc="Processing CSV files"):
            file_path = os.path.join(root, file)
            with open(file_path, 'r') as f:
                lines = f.readlines()[1:]  # Ignore the first line (headers)
                csv_data = np.genfromtxt(lines, delimiter=',', dtype=float)
                data.append(csv_data)
    return data

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read CSV files from a directory')
    parser.add_argument('directory', type=str, help='Directory containing CSV files')

    parser.add_argument('-a', '--attack', type=int, help='Attack time in seconds')
    parser.add_argument('-p', '--postattack', type=int, help='Post time in seconds')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s - %(message)s')
    if args.debug:
        logger.setLevel(logging.DEBUG)

    csv_data = read_csv_files(args.directory)

    # Separate the date of each csv in three groups. The first is the lines where the time (second column) if less than 60, thhe second group is between 60 and 180 and the third is above 180

    group1_list = []
    group2_list = []
    group3_list = []

    preattack = args.attack
    postattack = args.postattack
    group1_errors = 0
    group2_errors = 0
    group3_errors = 0
    for data in csv_data:
        if len(data) == 0:
            continue
                
        group1 = data[data[:, 0] < preattack]
        group2 = data[(data[:, 0] >= preattack) & (data[:, 0] < postattack)]
        group3 = data[data[:, 0] >= postattack]
        
        group1_list += list(group1[:, 1])        
        group2_list += list(group2[:, 1])
        group3_list += list(group3[:, 1])

        group1_errors += np.isnan(group1_list).sum()
        group2_errors += np.isnan(group2_list).sum()
        group3_errors += np.isnan(group3_list).sum()

        # Drop nan values
        group1_list = [x for x in group1_list if str(x) != 'nan']
        group2_list = [x for x in group2_list if str(x) != 'nan']
        group3_list = [x for x in group3_list if str(x) != 'nan']

    # Calculate the mean of each group
    group1_mean = np.mean(group1_list, axis=0)
    group2_mean = np.mean(group2_list, axis=0)
    group3_mean = np.mean(group3_list, axis=0)

    # get the number of NAN values in group2
    logger.info(f'Average time for client response (Before {preattack} seconds)    : {group1_mean:.3f} - {group1_errors} errors')
    logger.info(f'Average time for client response ({preattack} - {postattack} seconds)      : {group2_mean:.3f} - {group2_errors} errors')
    logger.info(f'Average time for client response (After {postattack} seconds)     : {group3_mean:.3f} - {group3_errors} errors')