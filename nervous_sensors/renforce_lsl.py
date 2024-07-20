from pylsl import StreamInfo, StreamOutlet, local_clock
from renforce_data import ECGData, EDAData

_start_time_lsl = local_clock()

type_ecg = 'ECG'
srate_ecg = ECGData.sampling_rate
n_ch_ecg = 1

type_eda = 'EDA'
srate_eda = EDAData.sampling_rate
n_ch_eda = 1

sensors_list = []

def init(sender):
    stream_sensor = {
        'name': sender.name,
        'info': None,
        'outlet': None,
        'last_timestamp': 0,
    }

    if sender.type == 'RENFORCE ECG':
        stream_sensor['info'] = StreamInfo(sender.name, type_ecg, n_ch_ecg, srate_ecg, 'float32', sender.name)
    else:
        stream_sensor['info'] = StreamInfo(sender.name, type_eda, n_ch_eda, srate_eda, 'float32', sender.name)

    stream_sensor['outlet'] = StreamOutlet(stream_sensor['info'])
    sensors_list.append(stream_sensor)

    print("LSL outlet for " + sender.name + " is opened")


def send(sender, data, timestamp):
    global index

    if sender.type ==  'RENFORCE ECG':
        # Offset to use timestamp of the first sample
        # https://github.com/labstreaminglayer/pylsl/blob/master/pylsl/pylsl.py#L463C2-L467C47
        timestamp_offset = (len(data) - 1) * 1 / srate_ecg
        sender.outlet.push_chunk(data, timestamp=timestamp + _start_time_lsl + timestamp_offset, pushthrough=True)

    elif sender.type ==  'RENFORCE EDA':
        sender.outlet.push_sample([data], timestamp=timestamp + _start_time_lsl, pushthrough=True)


def send_callback(sensor_data):
    sensor_df = None

    for dico in sensors_list:
        if dico['name'] == sensor_data.get_name():
            sensor_df = dico

    if isinstance(sensor_data, ECGData):
        # Offset to use timestamp of the first sample
        # https://github.com/labstreaminglayer/pylsl/blob/master/pylsl/pylsl.py#L463C2-L467C47
        data = sensor_data.get_latest_data(latest_data=sensor_df['last_timestamp'])

        timestamp = data.iloc[0, 0]
        data_value = data.iloc[:, 1].tolist()
        timestamp_offset = (len(data_value) - 1) * 1 / srate_ecg

        sensor_df['outlet'].push_chunk(data_value, timestamp=timestamp + _start_time_lsl + timestamp_offset,
                                        pushthrough=True)
        sensor_df['last_timestamp'] = data.iloc[-1, 0]


    elif isinstance(sensor_data, EDAData):
        data = sensor_data.get_latest_data(last_n=1)
        timestamp = data.iloc[0, 0]
        data_value = data.iloc[0, 1]

        sensor_df['outlet'].push_sample([data_value], timestamp=timestamp + _start_time_lsl, pushthrough=True)

