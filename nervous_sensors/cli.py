import click

gui_help = "Show real-time data graph"
folder_help = "Save CSV data files in folder"
lsl_help = "Send sensor data on LSL outlets"
sensors_help = (
    "ECGxxx,EDAxxx... : Give the name of the sensors you want to use. "
    "Make sure to put 'ecg' or 'eda' in their name so the program will know "
    "which type of sensor you want to use (not case sensitive)."
)


@click.command()
@click.option("-g", "--gui", is_flag=True, help=gui_help)
@click.option("-f", "--folder", type=click.Path(), help=folder_help)
@click.option("-l", "--lsl", is_flag=True, help=lsl_help)
@click.option("-s", "--sensors", help=sensors_help)
def cli(gui, folder, lsl, sensors):
    if gui:
        click.echo("Showing real-time data graph")
    if folder:
        click.echo(f"Saving CSV data files in folder: {folder}")
    if lsl:
        click.echo("Sending sensor data on LSL outlets")
    if sensors:
        sensors = sensors.split(",")
        eda_sensors = [s for s in sensors if "eda" in s.lower()]
        ecg_sensors = [s for s in sensors if "ecg" in s.lower()]
        other_sensors = [s for s in sensors if s not in eda_sensors and s not in ecg_sensors]
        click.echo(f"Using EDA sensors: {eda_sensors}")
        click.echo(f"Using ECG sensors: {ecg_sensors}")
        click.echo(f"Other sensors: {other_sensors}")
