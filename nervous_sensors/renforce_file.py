import csv
import asyncio
import threading
import os


sensors_list = []
quit_event = asyncio.Event()

def start():
    threading.Thread(target=lambda: _run_file_loop()).start()
    print("File thread started")

def stop():
    quit_event._loop.call_soon_threadsafe(quit_event.set)

def add_sensor(sensor, folder_path):

    sensors_list.append(
        {
            'sensor': sensor,
            'time': 0,
        }
    )

    sensor.file_path = f'{folder_path}/{sensor.start_time_str}_{sensor.name}.csv'
    fieldnames = sensor.data.get_header()

    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)

    with open(sensor.file_path, 'w', newline='') as f_object:
        writer = csv.DictWriter(f_object, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()


def _run_file_loop():
    asyncio.run(_file_loop())
    print("File thread stopped")


async def _file_loop():
    quit_event.clear()
    while True:
        try: 
            await asyncio.wait_for(quit_event.wait(), timeout=5.0)
            for dico in sensors_list:
                _write_csv(dico)
            return
        except TimeoutError:
            for dico in sensors_list:
                _write_csv(dico)


def _write_csv(dico):
    sensor = dico['sensor']
    file_path = sensor.file_path

    with open(file_path, 'a', newline='') as f_object:
        writer_object = csv.writer(f_object, delimiter=';')
        new_data = sensor.data.get_latest_data(latest_data=dico['time'])
        rows = new_data.values.tolist()
        writer_object.writerows(rows)
        if not new_data.empty:
            dico['time'] = new_data.iloc[-1, 0]