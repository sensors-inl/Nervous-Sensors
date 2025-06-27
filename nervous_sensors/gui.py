import asyncio
import logging
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
from typing import Optional, List, Dict

# Import your existing modules
from .connection_manager import ConnectionManager
from .utils import extract_sensors, print_bold, print_green, print_grey, print_red
from .cli_listener import CLIListener

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("nervous_gui")


class SensorStatusFrame(ttk.Frame):
    """Frame to display sensor status information"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.sensor_labels = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the sensor status UI"""
        title_label = ttk.Label(self, text="Sensor Status", font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Headers
        headers_frame = ttk.Frame(self)
        headers_frame.pack(fill='x', pady=(0, 5))
        
        # Configure column weights for consistent alignment
        headers_frame.columnconfigure(0, weight=0, minsize=150)
        headers_frame.columnconfigure(1, weight=0, minsize=120) 
        headers_frame.columnconfigure(2, weight=0, minsize=120)
        
        ttk.Label(headers_frame, text="Sensor", font=('Arial', 10, 'bold'), width=15).grid(row=0, column=0, sticky='w')
        ttk.Label(headers_frame, text="Connection", font=('Arial', 10, 'bold'), width=12).grid(row=0, column=1, sticky='w')
        ttk.Label(headers_frame, text="Notifications", font=('Arial', 10, 'bold'), width=12).grid(row=0, column=2, sticky='w')
    
        # Scrollable frame for sensors
        self.sensors_frame = ttk.Frame(self)
        self.sensors_frame.pack(fill='both', expand=True)
    
    def update_sensor_status(self, sensor_name: str, connected: bool, notifications: bool):
        """Update the status of a specific sensor"""
        if sensor_name not in self.sensor_labels:
            # Create new sensor row
            row = len(self.sensor_labels)
            frame = ttk.Frame(self.sensors_frame)
            frame.pack(fill='x', pady=2)
            
            # Configure same column layout as headers
            frame.columnconfigure(0, weight=0, minsize=150)
            frame.columnconfigure(1, weight=0, minsize=120)
            frame.columnconfigure(2, weight=0, minsize=120)
            
            name_label = ttk.Label(frame, text=sensor_name, width=15)
            name_label.grid(row=0, column=0, sticky='w')
            
            conn_label = ttk.Label(frame, width=12)
            conn_label.grid(row=0, column=1, sticky='w')
            
            notif_label = ttk.Label(frame, width=12)
            notif_label.grid(row=0, column=2, sticky='w')
            
            self.sensor_labels[sensor_name] = {
                'connection': conn_label,
                'notifications': notif_label
            }
        
        # Update status
        conn_text = "Connected" if connected else "Disconnected"
        conn_fg = "green" if connected else "red"
        self.sensor_labels[sensor_name]['connection'].config(text=conn_text, foreground=conn_fg)
        
        notif_text = "Active" if notifications else "Inactive"
        notif_fg = "green" if notifications else "orange"
        self.sensor_labels[sensor_name]['notifications'].config(text=notif_text, foreground=notif_fg)
    
    def clear_sensors(self):
        """Clear all sensor status displays"""
        for widget in self.sensors_frame.winfo_children():
            widget.destroy()
        self.sensor_labels.clear()


class NervousGUI:
    """Modern GUI for the Nervous framework"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.connection_manager: Optional[ConnectionManager] = None
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        self.event_loop_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        # GUI state variables
        self.sensors_var = tk.StringVar()
        self.gui_var = tk.BooleanVar()
        self.lsl_var = tk.BooleanVar()
        self.file_var = tk.BooleanVar()
        self.folder_var = tk.StringVar()
        self.parallel_var = tk.IntVar(value=1)
        self.dash_port = 6378  # Default Dash port
        
        self.sensor_list = []
        
        self.setup_ui()
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging redirection"""
        sys.stdout = CLIListener(sys.stdout)
        sys.stderr = CLIListener(sys.stderr)
    
    def setup_ui(self):
        """Setup the main user interface"""
        self.root.title("Nervous Framework - GUI Control Panel")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Nervous Framework Control Panel", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Create notebook for organized layout
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)
        
        # Configuration tab
        config_frame = ttk.Frame(notebook, padding="15")
        notebook.add(config_frame, text="Configuration")
        
        # Status tab
        status_frame = ttk.Frame(notebook, padding="15")
        notebook.add(status_frame, text="Status")
        
        self.setup_config_tab(config_frame)
        self.setup_status_tab(status_frame)
        
        # Control buttons at bottom
        self.setup_control_buttons(main_frame)
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_config_tab(self, parent):
        """Setup the configuration tab"""
        # Sensors section
        sensors_frame = ttk.LabelFrame(parent, text="Sensors Configuration", padding="10")
        sensors_frame.pack(fill='x', pady=(0, 15))
        
        # Sensor input
        sensor_input_frame = ttk.Frame(sensors_frame)
        sensor_input_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(sensor_input_frame, text="Add Sensor:").pack(side='left')
        self.sensor_entry = ttk.Entry(sensor_input_frame, width=20)
        self.sensor_entry.pack(side='left', padx=(10, 5))
        self.sensor_entry.bind('<Return>', lambda e: self.add_sensor())
        
        ttk.Button(sensor_input_frame, text="Add", command=self.add_sensor).pack(side='left', padx=(5, 0))
        
        # Sensor list
        list_frame = ttk.Frame(sensors_frame)
        list_frame.pack(fill='both', expand=True)
        
        ttk.Label(list_frame, text="Configured Sensors:").pack(anchor='w')
        
        # Listbox with scrollbar
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill='both', expand=True, pady=(5, 0))
        
        self.sensor_listbox = tk.Listbox(listbox_frame, height=4)
        scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical', command=self.sensor_listbox.yview)
        self.sensor_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.sensor_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Remove sensor button
        ttk.Button(list_frame, text="Remove Selected", command=self.remove_sensor).pack(pady=(5, 0))
        
        # Output options section
        output_frame = ttk.LabelFrame(parent, text="Output Options", padding="10")
        output_frame.pack(fill='x', pady=(0, 15))
        
        # GUI option
        gui_frame = ttk.Frame(output_frame)
        gui_frame.pack(fill='x', pady=2)
        ttk.Checkbutton(gui_frame, text="Enable GUI Dashboard", variable=self.gui_var).pack(side='left')
        self.dashboard_btn = ttk.Button(gui_frame, text="Open Dashboard", command=self.open_dashboard, 
                               state='disabled')
        self.dashboard_btn.pack(side='right')
        
        # LSL option
        ttk.Checkbutton(output_frame, text="Enable LSL Streaming", variable=self.lsl_var).pack(anchor='w', pady=2)
        
        # File recording option
        file_frame = ttk.Frame(output_frame)
        file_frame.pack(fill='x', pady=2)
        ttk.Checkbutton(file_frame, text="Enable File Recording", variable=self.file_var).pack(side='left')
        
        folder_frame = ttk.Frame(output_frame)
        folder_frame.pack(fill='x', pady=(5, 0))
        ttk.Label(folder_frame, text="Folder:").pack(side='left')
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, state='readonly', width=40)
        folder_entry.pack(side='left', padx=(10, 5), fill='x', expand=True)
        ttk.Button(folder_frame, text="Browse", command=self.browse_folder).pack(side='left')
        
        # Advanced options section
        advanced_frame = ttk.LabelFrame(parent, text="Advanced Options", padding="10")
        advanced_frame.pack(fill='x')
        
        parallel_frame = ttk.Frame(advanced_frame)
        parallel_frame.pack(fill='x')
        ttk.Label(parallel_frame, text="Parallel Connections:").pack(side='left')
        parallel_spin = ttk.Spinbox(parallel_frame, from_=1, to=10, textvariable=self.parallel_var, width=5)
        parallel_spin.pack(side='left', padx=(10, 0))
    
    def setup_status_tab(self, parent):
        """Setup the status monitoring tab"""
        # System status
        system_frame = ttk.LabelFrame(parent, text="System Status", padding="10")
        system_frame.pack(fill='x', pady=(0, 15))
        
        self.status_label = ttk.Label(system_frame, text="Status: Stopped", 
                                     font=('Arial', 11, 'bold'), foreground='red')
        self.status_label.pack()
        
        # Sensor status
        sensor_status_frame = ttk.LabelFrame(parent, text="Sensor Status", padding="10")
        sensor_status_frame.pack(fill='both', expand=True)
        
        self.sensor_status_frame = SensorStatusFrame(sensor_status_frame)
        self.sensor_status_frame.pack(fill='both', expand=True)
    
    def setup_control_buttons(self, parent):
        """Setup control buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=(20, 0))
        
        self.start_button = ttk.Button(button_frame, text="Start Framework", 
                                      command=self.start_framework, style='Success.TButton')
        self.start_button.pack(side='left', padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Stop Framework", 
                                     command=self.stop_framework, state='disabled', 
                                     style='Danger.TButton')
        self.stop_button.pack(side='left')
        
        # Configure button styles
        style = ttk.Style()
        style.configure('Success.TButton', foreground='white', background='green')
        style.configure('Danger.TButton', foreground='white', background='red')
    
    def add_sensor(self):
        """Add a sensor to the list"""
        sensor_name = self.sensor_entry.get().strip()
        if sensor_name and sensor_name not in self.sensor_list:
            self.sensor_list.append(sensor_name)
            self.sensor_listbox.insert(tk.END, sensor_name)
            self.sensor_entry.delete(0, tk.END)
        elif sensor_name in self.sensor_list:
            messagebox.showwarning("Duplicate Sensor", f"Sensor '{sensor_name}' is already in the list.")
    
    def remove_sensor(self):
        """Remove selected sensor from the list"""
        selection = self.sensor_listbox.curselection()
        if selection:
            index = selection[0]
            sensor_name = self.sensor_listbox.get(index)
            self.sensor_list.remove(sensor_name)
            self.sensor_listbox.delete(index)
    
    def browse_folder(self):
        """Browse for folder to save recordings"""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)
    
    def open_dashboard(self):
        """Open the dashboard in the default web browser"""
        if self.is_running and self.gui_var.get():
            url = f"http://localhost:{self.dash_port}"
            webbrowser.open(url)
        else:
            messagebox.showwarning("Dashboard Not Available", 
                                 "Dashboard is only available when the GUI is enabled and framework is running.")
    
    def start_framework(self):
        """Start the Nervous framework"""
        if not self.sensor_list:
            messagebox.showerror("No Sensors", "Please add at least one sensor before starting.")
            return
        
        if self.file_var.get() and not self.folder_var.get():
            messagebox.showerror("No Folder Selected", "Please select a folder for file recording.")
            return
        
        try:
            # Validate sensors
            true_sensors = extract_sensors(self.sensor_list)
            if not true_sensors:
                messagebox.showerror("Invalid Sensors", "No valid sensors found. Please check sensor names.")
                return
            
            # Disable configuration controls
            self.set_config_state('disabled')
            
            # Update UI state
            self.is_running = True
            self.status_label.config(text="Status: Starting...", foreground='orange')
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            
            # Enable dashboard button if GUI is selected
            if self.gui_var.get():
                self.dashboard_btn.config(state='normal')
            
            # Start event loop in separate thread
            self.start_event_loop(true_sensors)
            
            logger.info("Framework started successfully")
            self.status_label.config(text="Status: Running", foreground='green')
            
        except Exception as e:
            logger.error(f"Error starting framework: {e}")
            messagebox.showerror("Start Error", f"Failed to start framework: {str(e)}")
            self.reset_ui_state()
    
    def stop_framework(self):
        """Stop the Nervous framework"""
        if not self.is_running:
            return
        
        try:
            self.status_label.config(text="Status: Stopping...", foreground='orange')
            
            # Stop the connection manager
            if self.connection_manager and self.event_loop:
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        self.connection_manager.stop(), self.event_loop
                    )
                    future.result(timeout=10)  # Wait up to 10 seconds
                except Exception as e:
                    logger.warning(f"Error stopping connection manager: {e}")
            
            # Stop event loop
            if self.event_loop and not self.event_loop.is_closed():
                self.event_loop.call_soon_threadsafe(self.event_loop.stop)
            
            # Wait for thread to finish
            if self.event_loop_thread and self.event_loop_thread.is_alive():
                self.event_loop_thread.join(timeout=5)
            
            logger.info("Framework stopped successfully")
            
        except Exception as e:
            error_msg = str(e).strip()
            # Filter out normal server shutdown errors
            if error_msg and "werkzeug.server.shutdown" not in error_msg:
                logger.error(f"Error stopping framework: {e}")
                messagebox.showerror("Stop Error", f"Error stopping framework: {error_msg}")
            else:
                logger.info("Framework stopped successfully (ignoring server shutdown warnings)")
        finally:
            self.reset_ui_state()
    
    def start_event_loop(self, sensors):
        """Start the asyncio event loop in a separate thread"""
        def run_event_loop():
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            
            try:
                # Create connection manager
                folder = self.folder_var.get() if self.file_var.get() else False
                self.connection_manager = ConnectionManager(
                    sensor_names=sensors,
                    gui=self.gui_var.get(),
                    folder=folder,
                    lsl=self.lsl_var.get(),
                    parallel_connection_authorized=self.parallel_var.get()
                )
                
                # Start periodic status updates
                self.event_loop.create_task(self.update_sensor_status_periodically())
                
                # Run the connection manager
                self.event_loop.run_until_complete(self.connection_manager.start())
                
            except Exception as e:
                # Filter out normal shutdown errors
                error_msg = str(e)
                if "Event loop stopped before Future completed" not in error_msg and self.is_running:
                    logger.error(f"Error in event loop: {e}")
                    self.root.after(0, lambda: self.handle_event_loop_error(error_msg))
        
        self.event_loop_thread = threading.Thread(target=run_event_loop, daemon=True)
        self.event_loop_thread.start()
    
    async def update_sensor_status_periodically(self):
        """Periodically update sensor status in the GUI"""
        try:
            while self.is_running:
                if self.connection_manager:
                    for sensor in self.connection_manager._sensors:
                        # Schedule GUI update on main thread
                        self.root.after(0, lambda s=sensor: self.update_sensor_gui_status(s))
                await asyncio.sleep(1)  # Update every second
        except (asyncio.CancelledError, RuntimeError):
            # Normal shutdown, ignore these errors
            pass
        except Exception as e:
            if self.is_running:
                logger.error(f"Error updating sensor status: {e}")
    
    def update_sensor_gui_status(self, sensor):
        """Update sensor status in GUI (called from main thread)"""
        try:
            connected = sensor.is_connected()
            # Get actual notification status from connection manager
            notifications = (connected and 
                            self.connection_manager and 
                            self.connection_manager.are_notifications_active())
            
            self.sensor_status_frame.update_sensor_status(
                sensor.get_name(),
                connected,
                notifications
            )
        except Exception as e:
            logger.error(f"Error updating GUI status for sensor: {e}")
    
    def handle_event_loop_error(self, error_msg):
        """Handle errors from the event loop thread"""
        messagebox.showerror("Framework Error", f"Framework encountered an error: {error_msg}")
        self.reset_ui_state()
    
    def set_config_state(self, state):
        """Enable/disable configuration controls"""
        def set_state_recursive(widget, state):
            try:
                widget.configure(state=state)
            except tk.TclError:
                pass  # Some widgets don't support state
            
            for child in widget.winfo_children():
                set_state_recursive(child, state)
        
        # Find and disable configuration notebook tab
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Notebook):
                        config_frame = subchild.nametowidget(subchild.tabs()[0])
                        set_state_recursive(config_frame, state)
    
    def reset_ui_state(self):
        """Reset UI to initial state"""
        self.is_running = False
        self.connection_manager = None
        self.event_loop = None
        self.event_loop_thread = None
        
        # Reset UI elements
        self.status_label.config(text="Status: Stopped", foreground='red')
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.set_config_state('normal')
        
        # Disable dashboard button
        self.dashboard_btn.config(state='disabled')
        
        # Clear sensor status
        self.sensor_status_frame.clear_sensors()
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            result = messagebox.askyesno("Confirm Exit", 
                                       "Framework is still running. Stop it before closing?")
            if result:
                self.stop_framework()
            else:
                return
        
        self.root.destroy()
    
    def run(self):
        """Run the GUI application"""
        logger.info("Starting Nervous Framework GUI")
        self.root.mainloop()


def gui():
    """Main entry point for the GUI application"""
    try:
        app = NervousGUI()
        app.run()
    except Exception as e:
        logger.error(f"Failed to start GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    gui()
