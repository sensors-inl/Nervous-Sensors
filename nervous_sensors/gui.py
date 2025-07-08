import asyncio
import logging
import os
import pathlib
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import PhotoImage, filedialog, messagebox, ttk
from typing import Optional

from .cli_listener import CLIListener

# Import your existing modules
from .connection_manager import ConnectionManager
from .utils import extract_sensors

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("nervous_gui")


class ModernStyle:
    """Modern dark theme color palette and styling"""

    # Color palette
    BG_PRIMARY = "#1a1a1a"  # Main background
    BG_SECONDARY = "#2d2d2d"  # Secondary background
    BG_TERTIARY = "#3d3d3d"  # Tertiary background
    BG_ACCENT = "#4a4a4a"  # Accent background

    TEXT_PRIMARY = "#ffffff"  # Primary text
    TEXT_SECONDARY = "#cccccc"  # Secondary text
    TEXT_MUTED = "#888888"  # Muted text

    ACCENT_BLUE = "#0078d4"  # Primary accent
    ACCENT_GREEN = "#00cc44"  # Success/connected
    ACCENT_RED = "#ff4444"  # Error/disconnected
    ACCENT_ORANGE = "#ff8800"  # Warning/inactive
    ACCENT_PURPLE = "#6fa8d3"  # Highlight

    BORDER = "#555555"  # Border color
    HOVER = "#404040"  # Hover state

    @classmethod
    def configure_styles(cls, style: ttk.Style):
        """Configure modern dark theme styles"""

        # Configure the theme
        style.theme_use("clam")

        # Main frame styles
        style.configure("Modern.TFrame", background=cls.BG_SECONDARY, borderwidth=0)

        style.configure(
            "Secondary.TFrame", background=cls.BG_SECONDARY, borderwidth=1, relief="solid", bordercolor=cls.BORDER
        )

        # Label styles
        style.configure(
            "Modern.TLabel",
            background=cls.BG_SECONDARY,
            disabledbackground=cls.BG_SECONDARY,
            foreground=cls.TEXT_PRIMARY,
            font=("Segoe UI", 10),
        )

        style.configure(
            "Title.TLabel",
            background=cls.BG_SECONDARY,
            foreground=cls.TEXT_PRIMARY,
            disabledbackground=cls.BG_SECONDARY,
            font=("Segoe UI", 18, "bold"),
        )

        style.configure(
            "Subtitle.TLabel",
            background=cls.BG_SECONDARY,
            foreground=cls.TEXT_SECONDARY,
            disabledbackground=cls.BG_SECONDARY,
            font=("Segoe UI", 12, "bold"),
        )

        style.configure(
            "Status.TLabel",
            background=cls.BG_SECONDARY,
            foreground=cls.TEXT_PRIMARY,
            font=("Segoe UI", 11, "bold"),
            padding=(10, 5),
        )

        # Button styles
        style.configure(
            "Modern.TButton",
            background=cls.ACCENT_BLUE,
            foreground=cls.TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
            padding=(15, 8),
            borderwidth=0,
            focuscolor="none",
        )

        style.map("Modern.TButton", background=[("active", cls.ACCENT_PURPLE), ("pressed", "#0056a3")])

        style.configure(
            "Success.TButton",
            background=cls.ACCENT_GREEN,
            foreground=cls.TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
            padding=(15, 8),
            borderwidth=0,
        )

        style.map("Success.TButton", background=[("active", "#00aa33"), ("pressed", "#008822")])

        style.configure(
            "Danger.TButton",
            background=cls.ACCENT_RED,
            foreground=cls.TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
            padding=(15, 8),
            borderwidth=0,
        )

        style.map("Danger.TButton", background=[("active", "#dd3333"), ("pressed", "#cc2222")])

        # Entry styles
        style.configure(
            "Modern.TEntry",
            fieldbackground=cls.BG_TERTIARY,
            foreground=cls.TEXT_PRIMARY,
            bordercolor=cls.BORDER,
            lightcolor=cls.ACCENT_BLUE,
            darkcolor=cls.ACCENT_BLUE,
            borderwidth=2,
            insertcolor=cls.TEXT_PRIMARY,
            font=("Segoe UI", 10),
        )

        style.map(
            "Modern.TEntry", fieldbackground=[("focus", cls.BG_ACCENT)], bordercolor=[("focus", cls.ACCENT_BLUE)]
        )

        # Checkbutton styles
        style.configure(
            "Modern.TCheckbutton",
            background=cls.BG_SECONDARY,
            foreground=cls.TEXT_PRIMARY,
            focuscolor="none",
            font=("Segoe UI", 10),
        )

        # Spinbox styles
        style.configure(
            "Modern.TSpinbox",
            fieldbackground=cls.BG_TERTIARY,
            foreground=cls.TEXT_PRIMARY,
            bordercolor=cls.BORDER,
            arrowcolor=cls.TEXT_PRIMARY,
            font=("Segoe UI", 10),
        )

        # Notebook styles
        style.configure("Modern.TNotebook", background=cls.BG_SECONDARY, borderwidth=0, tabmargins=[0, 5, 0, 0])

        style.configure(
            "Modern.TNotebook.Tab",
            background=cls.BG_SECONDARY,
            foreground=cls.TEXT_SECONDARY,
            padding=[20, 10],  # Keep consistent padding
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            width=20,
        )  # Add fixed width to prevent size changes

        style.map(
            "Modern.TNotebook.Tab",
            background=[("selected", cls.ACCENT_BLUE), ("active", cls.HOVER)],
            foreground=[("selected", cls.TEXT_PRIMARY), ("active", cls.TEXT_PRIMARY)],
            # Remove any padding changes on state change
            padding=[],
        )  # Empty list means no state-specific padding changes

        # LabelFrame styles
        style.configure(
            "Modern.TLabelframe", background=cls.BG_SECONDARY, bordercolor=cls.BORDER, borderwidth=2, relief="solid"
        )

        style.configure(
            "Modern.TLabelframe.Label",
            background=cls.BG_SECONDARY,
            foreground=cls.ACCENT_BLUE,
            font=("Segoe UI", 11, "bold"),
        )


class SensorStatusFrame(ttk.Frame):
    """Frame to display sensor status information with modern styling"""

    def __init__(self, parent):
        super().__init__(parent, style="Modern.TFrame")
        self.sensor_labels = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup the sensor status UI with modern styling"""
        # Title with accent
        title_frame = ttk.Frame(self, style="Modern.TFrame")
        title_frame.pack(fill="x", pady=(0, 15))

        title_label = ttk.Label(title_frame, text="🔌 Sensor Status", style="Subtitle.TLabel")
        title_label.pack(side="left")

        # Status indicator
        self.status_indicator = ttk.Label(
            title_frame,
            text="●",
            foreground=ModernStyle.ACCENT_RED,
            background=ModernStyle.BG_SECONDARY,
            font=("Segoe UI", 16),
        )
        self.status_indicator.pack(side="right")

        # Headers with modern styling
        headers_frame = ttk.Frame(self, style="Secondary.TFrame")
        headers_frame.pack(fill="x", pady=(0, 10))
        headers_frame.configure(padding=10)

        headers_frame.columnconfigure(0, weight=1)
        headers_frame.columnconfigure(1, weight=1)
        headers_frame.columnconfigure(2, weight=1)

        ttk.Label(
            headers_frame,
            text="SENSOR",
            font=("Segoe UI", 9, "bold"),
            foreground=ModernStyle.TEXT_MUTED,
            background=ModernStyle.BG_SECONDARY,
        ).grid(row=0, column=0, sticky="w", padx=10)

        ttk.Label(
            headers_frame,
            text="CONNECTION",
            font=("Segoe UI", 9, "bold"),
            foreground=ModernStyle.TEXT_MUTED,
            background=ModernStyle.BG_SECONDARY,
        ).grid(row=0, column=1, sticky="w", padx=10)

        ttk.Label(
            headers_frame,
            text="STATUS",
            font=("Segoe UI", 9, "bold"),
            foreground=ModernStyle.TEXT_MUTED,
            background=ModernStyle.BG_SECONDARY,
        ).grid(row=0, column=2, sticky="w", padx=10)

        # Scrollable frame for sensors
        self.sensors_frame = ttk.Frame(self, style="Modern.TFrame")
        self.sensors_frame.pack(fill="both", expand=True)

    def update_sensor_status(self, sensor_name: str, connected: bool, notifications: bool):
        """Update the status of a specific sensor with modern styling"""
        if sensor_name not in self.sensor_labels:
            # Create new sensor row with modern styling
            row_frame = ttk.Frame(self.sensors_frame, style="Secondary.TFrame")
            row_frame.pack(fill="x", pady=2)
            row_frame.configure(padding=10)

            row_frame.columnconfigure(0, weight=1)
            row_frame.columnconfigure(1, weight=1)
            row_frame.columnconfigure(2, weight=1)

            # Sensor name with icon
            name_label = ttk.Label(
                row_frame,
                text=f"📡 {sensor_name}",
                font=("Segoe UI", 10, "bold"),
                foreground=ModernStyle.TEXT_PRIMARY,
                background=ModernStyle.BG_SECONDARY,
            )
            name_label.grid(row=0, column=0, sticky="w", padx=10)

            # Connection status
            conn_frame = ttk.Frame(row_frame, style="Modern.TFrame")
            conn_frame.grid(row=0, column=1, sticky="w", padx=10)
            conn_frame.configure(style="Secondary.TFrame")

            conn_indicator = ttk.Label(
                conn_frame, text="●", font=("Segoe UI", 12), background=ModernStyle.BG_SECONDARY
            )
            conn_indicator.pack(side="left", padx=(0, 5))

            conn_label = ttk.Label(conn_frame, font=("Segoe UI", 10), background=ModernStyle.BG_SECONDARY)
            conn_label.pack(side="left")

            # Notification status
            notif_frame = ttk.Frame(row_frame, style="Modern.TFrame")
            notif_frame.grid(row=0, column=2, sticky="w", padx=10)
            notif_frame.configure(style="Secondary.TFrame")

            notif_indicator = ttk.Label(
                notif_frame, text="●", font=("Segoe UI", 12), background=ModernStyle.BG_SECONDARY
            )
            notif_indicator.pack(side="left", padx=(0, 5))

            notif_label = ttk.Label(notif_frame, font=("Segoe UI", 10), background=ModernStyle.BG_SECONDARY)
            notif_label.pack(side="left")

            self.sensor_labels[sensor_name] = {
                "connection_indicator": conn_indicator,
                "connection_label": conn_label,
                "notification_indicator": notif_indicator,
                "notification_label": notif_label,
            }

        # Update connection status
        if connected:
            self.sensor_labels[sensor_name]["connection_indicator"].config(foreground=ModernStyle.ACCENT_GREEN)
            self.sensor_labels[sensor_name]["connection_label"].config(
                text="Connected", foreground=ModernStyle.ACCENT_GREEN
            )
        else:
            self.sensor_labels[sensor_name]["connection_indicator"].config(foreground=ModernStyle.ACCENT_RED)
            self.sensor_labels[sensor_name]["connection_label"].config(
                text="Disconnected", foreground=ModernStyle.ACCENT_RED
            )

        # Update notification status
        if notifications:
            self.sensor_labels[sensor_name]["notification_indicator"].config(foreground=ModernStyle.ACCENT_GREEN)
            self.sensor_labels[sensor_name]["notification_label"].config(
                text="Active", foreground=ModernStyle.ACCENT_GREEN
            )
        else:
            self.sensor_labels[sensor_name]["notification_indicator"].config(foreground=ModernStyle.ACCENT_ORANGE)
            self.sensor_labels[sensor_name]["notification_label"].config(
                text="Inactive", foreground=ModernStyle.ACCENT_ORANGE
            )

        # Update main status indicator
        any_connected = any(connected for connected in [connected])  # This would be expanded for multiple sensors
        self.status_indicator.config(foreground=ModernStyle.ACCENT_GREEN if any_connected else ModernStyle.ACCENT_RED)

    def clear_sensors(self):
        """Clear all sensor status displays"""
        for widget in self.sensors_frame.winfo_children():
            widget.destroy()
        self.sensor_labels.clear()
        self.status_indicator.config(foreground=ModernStyle.ACCENT_RED)


class NervousGUI:
    """Modern GUI for the Nervous framework with dark theme"""

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
        """Setup the modern user interface"""
        self.root.title("Nervous Control Panel")
        self.root.geometry("900x900")
        img_file_name = "icon.png"
        current_dir = pathlib.Path(__file__).parent.resolve()  # current directory
        img_path = os.path.join(current_dir, img_file_name)  # join with your image's file name
        icon = PhotoImage(file=img_path)
        self.root.iconphoto(True, icon)
        self.root.resizable(True, True)
        self.root.configure(bg=ModernStyle.BG_SECONDARY)

        # Configure modern style
        style = ttk.Style()
        ModernStyle.configure_styles(style)

        # Main container
        main_frame = ttk.Frame(self.root, style="Modern.TFrame", padding=25)
        main_frame.pack(fill="both", expand=True)

        # Header section
        header_frame = ttk.Frame(main_frame, style="Modern.TFrame")
        header_frame.pack(fill="x", pady=(0, 30))

        # Title with modern styling
        title_label = ttk.Label(header_frame, text="Nervous Control Panel", style="Title.TLabel")
        title_label.pack(side="left")

        # Create modern notebook
        self.notebook = ttk.Notebook(main_frame, style="Modern.TNotebook")
        self.notebook.pack(fill="both", expand=True, pady=(0, 20))

        # Configuration tab
        config_frame = ttk.Frame(self.notebook, style="Modern.TFrame", padding=20)
        self.notebook.add(config_frame, text="⚙️ Configuration")

        # Status tab
        status_frame = ttk.Frame(self.notebook, style="Modern.TFrame", padding=20)
        self.notebook.add(status_frame, text="📊 Status")

        self.setup_config_tab(config_frame)
        self.setup_status_tab(status_frame)

        # Modern control buttons
        self.setup_control_buttons(main_frame)

        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_config_tab(self, parent):
        """Setup the configuration tab with modern styling"""
        # Sensors section
        sensors_frame = ttk.LabelFrame(parent, text="🔧 Sensors Configuration", style="Modern.TLabelframe", padding=15)
        sensors_frame.pack(fill="x", pady=(0, 20))

        # Sensor input with modern styling
        input_label = ttk.Label(
            sensors_frame, text="Add New Sensor", style="Modern.TLabel", font=("Segoe UI", 11, "bold")
        )
        input_label.pack(anchor="w", pady=(0, 10))

        sensor_input_frame = ttk.Frame(sensors_frame, style="Modern.TFrame")
        sensor_input_frame.pack(fill="x", pady=(0, 15))

        self.sensor_entry = ttk.Entry(sensor_input_frame, style="Modern.TEntry", font=("Segoe UI", 11), width=25)
        self.sensor_entry.pack(side="left", ipady=4, padx=(0, 10))
        self.sensor_entry.bind("<Return>", lambda e: self.add_sensor())

        add_btn = ttk.Button(sensor_input_frame, text="➕ Add", style="Modern.TButton", command=self.add_sensor)
        add_btn.pack(side="left")

        # Sensor list with modern styling
        list_label = ttk.Label(
            sensors_frame, text="Configured Sensors", style="Modern.TLabel", font=("Segoe UI", 11, "bold")
        )
        list_label.pack(anchor="w", pady=(0, 10))

        # Custom listbox styling
        listbox_frame = ttk.Frame(sensors_frame, style="Secondary.TFrame")
        listbox_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.sensor_listbox = tk.Listbox(
            listbox_frame,
            height=4,
            bg=ModernStyle.BG_TERTIARY,
            fg=ModernStyle.TEXT_PRIMARY,
            selectbackground=ModernStyle.ACCENT_BLUE,
            selectforeground=ModernStyle.TEXT_PRIMARY,
            font=("Segoe UI", 10),
            borderwidth=0,
            highlightthickness=0,
        )

        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.sensor_listbox.yview)
        self.sensor_listbox.configure(yscrollcommand=scrollbar.set)

        self.sensor_listbox.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

        # Remove button
        ttk.Button(sensors_frame, text="🗑️ Remove Selected", style="Danger.TButton", command=self.remove_sensor).pack(
            pady=(0, 0)
        )

        # Output options section
        output_frame = ttk.LabelFrame(parent, text="📤 Output Options", style="Modern.TLabelframe", padding=15)
        output_frame.pack(fill="x", pady=(0, 20))

        # GUI option with dashboard button
        gui_container = ttk.Frame(output_frame, style="Modern.TFrame")
        gui_container.pack(fill="x", pady=5)

        ttk.Checkbutton(
            gui_container, text=" Enable GUI Dashboard", variable=self.gui_var, style="Modern.TCheckbutton"
        ).pack(side="left")

        self.dashboard_btn = ttk.Button(
            gui_container,
            text="🚀 Open Dashboard",
            style="Modern.TButton",
            command=self.open_dashboard,
            state="disabled",
        )
        self.dashboard_btn.pack(side="right")

        # Other options
        ttk.Checkbutton(
            output_frame, text=" Enable LSL Streaming", variable=self.lsl_var, style="Modern.TCheckbutton"
        ).pack(anchor="w", pady=5)

        ttk.Checkbutton(
            output_frame, text=" Enable File Recording", variable=self.file_var, style="Modern.TCheckbutton"
        ).pack(anchor="w", pady=5)

        # Folder selection
        folder_frame = ttk.Frame(output_frame, style="Modern.TFrame")
        folder_frame.pack(fill="x", pady=(10, 0))

        ttk.Label(folder_frame, text="📁 Output Folder:", style="Modern.TLabel").pack(side="left")

        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, style="Modern.TEntry", state="readonly")
        folder_entry.pack(side="left", ipady=6, padx=(10, 5), fill="x", expand=True)

        ttk.Button(folder_frame, text="Browse", style="Modern.TButton", command=self.browse_folder).pack(side="left")

        # Advanced options
        advanced_frame = ttk.LabelFrame(parent, text="⚡ Advanced Options", style="Modern.TLabelframe", padding=15)
        advanced_frame.pack(fill="x")

        parallel_frame = ttk.Frame(advanced_frame, style="Modern.TFrame")
        parallel_frame.pack(fill="x")

        ttk.Label(parallel_frame, text="🔗 Parallel Connections:", style="Modern.TLabel").pack(side="left")

        ttk.Spinbox(
            parallel_frame, from_=1, to=10, textvariable=self.parallel_var, style="Modern.TSpinbox", width=8
        ).pack(side="left", padx=(10, 0))

    def setup_status_tab(self, parent):
        """Setup the status monitoring tab with modern styling"""
        # System status
        system_frame = ttk.LabelFrame(parent, text="⚙️ System Status", style="Modern.TLabelframe", padding=15)
        system_frame.pack(fill="x", pady=(0, 20))

        status_container = ttk.Frame(system_frame, style="Secondary.TFrame")
        status_container.pack(fill="x")
        status_container.configure(padding=15)

        self.status_label = ttk.Label(
            status_container,
            text="● System Stopped",
            font=("Segoe UI", 14, "bold"),
            foreground=ModernStyle.ACCENT_RED,
            background=ModernStyle.BG_SECONDARY,
        )
        self.status_label.pack()

        # Sensor status with modern frame
        sensor_status_frame = ttk.LabelFrame(
            parent, text="📡 Sensor Monitoring", style="Modern.TLabelframe", padding=15
        )
        sensor_status_frame.pack(fill="both", expand=True)

        self.sensor_status_frame = SensorStatusFrame(sensor_status_frame)
        self.sensor_status_frame.pack(fill="both", expand=True)

    def setup_control_buttons(self, parent):
        """Setup modern control buttons"""
        button_frame = ttk.Frame(parent, style="Modern.TFrame")
        button_frame.pack(fill="x", pady=(0, 0))

        # Create a centered button container
        button_container = ttk.Frame(button_frame, style="Modern.TFrame")
        button_container.pack(expand=True)

        self.start_button = ttk.Button(
            button_container, text="🚀 Start Framework", command=self.start_framework, style="Success.TButton"
        )
        self.start_button.pack(side="left", padx=(0, 15))

        self.stop_button = ttk.Button(
            button_container,
            text="⏹️ Stop Framework",
            command=self.stop_framework,
            state="disabled",
            style="Danger.TButton",
        )
        self.stop_button.pack(side="left")

    def add_sensor(self):
        """Add a sensor to the list"""
        sensor_name = self.sensor_entry.get().strip()
        if sensor_name and sensor_name not in self.sensor_list:
            self.sensor_list.append(sensor_name)
            self.sensor_listbox.insert(tk.END, f"📡 {sensor_name}")
            self.sensor_entry.delete(0, tk.END)
        elif sensor_name in self.sensor_list:
            messagebox.showwarning(
                "Duplicate Sensor", f"Sensor '{sensor_name}' is already in the list.", parent=self.root
            )

    def remove_sensor(self):
        """Remove selected sensor from the list"""
        selection = self.sensor_listbox.curselection()
        if selection:
            index = selection[0]
            sensor_text = self.sensor_listbox.get(index)
            sensor_name = sensor_text.replace("📡 ", "")
            self.sensor_list.remove(sensor_name)
            self.sensor_listbox.delete(index)

    def browse_folder(self):
        """Browse for folder to save recordings"""
        folder = filedialog.askdirectory(parent=self.root)
        if folder:
            self.folder_var.set(folder)

    def open_dashboard(self):
        """Open the dashboard in the default web browser"""
        if self.is_running and self.gui_var.get():
            url = f"http://localhost:{self.dash_port}"
            webbrowser.open(url)
        else:
            messagebox.showwarning(
                "Dashboard Not Available",
                "Dashboard is only available when the GUI is enabled and framework is running.",
                parent=self.root,
            )

    def start_framework(self):
        """Start the Nervous framework"""
        if not self.sensor_list:
            messagebox.showerror("No Sensors", "Please add at least one sensor before starting.", parent=self.root)
            return

        if self.file_var.get() and not self.folder_var.get():
            messagebox.showerror("No Folder Selected", "Please select a folder for file recording.", parent=self.root)
            return

        try:
            # Validate sensors
            true_sensors = extract_sensors(self.sensor_list)
            if not true_sensors:
                messagebox.showerror(
                    "Invalid Sensors", "No valid sensors found. Please check sensor names.", parent=self.root
                )
                return

            # Disable configuration controls
            self.set_config_state("disabled")

            # Update UI state
            self.is_running = True
            self.status_label.config(text="● System Starting...", foreground=ModernStyle.ACCENT_ORANGE)
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")

            # Enable dashboard button if GUI is selected
            if self.gui_var.get():
                self.dashboard_btn.config(state="normal")

            # Start event loop in separate thread
            self.start_event_loop(true_sensors)

            logger.info("Framework started successfully")
            self.status_label.config(text="● System Running", foreground=ModernStyle.ACCENT_GREEN)

        except Exception as e:
            logger.error(f"Error starting framework: {e}")
            messagebox.showerror("Start Error", f"Failed to start framework: {str(e)}", parent=self.root)
            self.reset_ui_state()

    def stop_framework(self):
        """Stop the Nervous framework"""
        if not self.is_running:
            return

        try:
            self.status_label.config(text="● System Stopping...", foreground=ModernStyle.ACCENT_ORANGE)

            # Stop the connection manager
            if self.connection_manager and self.event_loop:
                try:
                    future = asyncio.run_coroutine_threadsafe(self.connection_manager.stop(), self.event_loop)
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
                messagebox.showerror("Stop Error", f"Error stopping framework: {error_msg}", parent=self.root)
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
                    parallel_connection_authorized=self.parallel_var.get(),
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
            notifications = (
                connected and self.connection_manager and self.connection_manager.are_notifications_active()
            )

            self.sensor_status_frame.update_sensor_status(sensor.get_name(), connected, notifications)
        except Exception as e:
            logger.error(f"Error updating GUI status for sensor: {e}")

    def handle_event_loop_error(self, error_msg):
        """Handle errors from the event loop thread"""
        messagebox.showerror("Framework Error", f"Framework encountered an error: {error_msg}", parent=self.root)
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
        self.status_label.config(text="● System Stopped", foreground=ModernStyle.ACCENT_RED)
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.set_config_state("normal")

        # Disable dashboard button
        self.dashboard_btn.config(state="disabled")

        # Clear sensor status
        self.sensor_status_frame.clear_sensors()

    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            result = messagebox.askyesno(
                "Confirm Exit", "Framework is still running. Stop it before closing?", parent=self.root
            )
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
