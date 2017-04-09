import numpy as np
import pickle


def aggregate_data(data_files):
    unix_time = np.array([])
    gX = np.array([])
    gY = np.array([])
    gZ = np.array([])
    for file in data_files:
        file_data = pickle.load(open(file.processed_datafile.name.encode(), 'rb'))
        unix_time = np.append(unix_time, file_data['time'])
        gX = np.append(gX, file_data['gX'])
        gY = np.append(gY, file_data['gY'])
        gZ = np.append(gZ, file_data['gZ'])
        del file_data
    return {'time': unix_time, 'gX': gX, 'gY': gY, 'gZ': gZ}


def window_data(acc, start_time, finish_time, window_duration):
    window_times = np.arange(start_time, finish_time, window_duration)
    windowed_acc = []

    for i_window in range(len(window_times)-1):
        samples = (acc['time'] >= window_times[i_window]) & (acc['time'] < window_times[i_window + 1])
        time = acc['time'][samples]
        gX = acc['gX'][samples]
        gY = acc['gY'][samples]
        gZ = acc['gZ'][samples]
        windowed_acc.append({'time': time, 'gX': gX, 'gY': gY, 'gZ': gZ})
        del time, gX, gY, gZ

    return windowed_acc





