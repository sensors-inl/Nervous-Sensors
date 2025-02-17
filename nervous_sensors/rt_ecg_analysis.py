"""
    Real-Time ECG Signal Analysis and Processing.
    
    This program calculates the heart rate and/or respiratory rate in real-time from an ECG signal, based on the methodology developed by Pan and Tompkins. 
    
"""

import numpy as np
from scipy.signal import butter, filtfilt, find_peaks

# History variables to store the R-peak indices, R-peak heights, and historical ECG data
history_R_peak_idx = []
previous_history_R_peak_idx = []
history_R_peak_height = []
previous_history_R_peak_height = []
history_ecg = []
history_time = []

# Variables for the measurement window
ecg_window = []
time_window = []

# Index for the start of the calculation window
idx_window = 0

def init_window():
    """
    Initializes the ECG signal and time window for processing.
    
    This function sets up two global variables: `ecg_window` and `time_window`.
    It initializes the `ecg_window` as a list of zero values, with a size of 3 * 512, 
    and it also initializes the `time_window` with corresponding time values.
    
    Note:
        - `ecg_window` is initialized with zeros, representing an empty window for the ECG signal.
        - `time_window` is initialized with time values calculated based on the sample rate.
    """
    global ecg_window
    global time_window
    
    # Initialize the ECG window with 3 * 512 zeros (default values)
    ecg_window = [0] * (3 * 512)
    
    # Initialize the time window with time values from -(3*512-i)/512
    time_window = []
    for i in range(3 * 512):
        time_window.append(-(3 * 512 - i) / 512)
        
def init_history():
    """
    Initializes and resets the history data for ECG signal and R-peak information.
    
    This function resets all global variables that store historical data related 
    to the ECG signal and R-peak positions and heights. It also initializes the 
    `history_ecg` and `history_time` lists with appropriate default values for 
    future data storage.
    
    Note:
        - The function initializes `history_ecg` as a list with 7 * 512 zero values 
          to represent initial ECG data.
        - The `history_time` list is populated with time values based on the sample rate.
        - Clears both the current history and previous history of R-peak data.
    """
    global history_ecg
    global history_R_peak_height
    global history_R_peak_idx
    global history_time
    global previous_history_R_peak_height
    global previous_history_R_peak_idx
    
    # Clear all previous stored data
    history_ecg.clear()
    history_R_peak_height.clear()
    history_R_peak_idx.clear()
    previous_history_R_peak_height.clear()
    previous_history_R_peak_idx.clear()
    history_time.clear()
    
    # Reinitialize the history variables as empty lists or predefined values
    history_R_peak_idx = []
    previous_history_R_peak_idx = []
    history_R_peak_height = []
    previous_history_R_peak_height = []
    
    # Initialize ECG history with 7 * 512 zeros (default values)
    history_ecg = [0] * (7 * 512)
    
    # Initialize history_time with time values from -(7*512-i)/512
    history_time = []
    for i in range(7 * 512):
        history_time.append(-(7 * 512 - i) / 512)

def init():
    init_window()
    init_history()

def reset_history_data():
    """
    Resets the history data for ECG signal and R-peak information.
    
    This function clears and reinitializes several global variables that store 
    historical data related to the ECG signal and R-peak positions and heights. 
    It is useful for resetting the state of the data storage to start fresh.
    
    Note:
        - The global variables involved include history of the ECG signal, 
          R-peak heights, R-peak indices, and corresponding times.
        - Clears both the current history and previous history of R-peak data.
    """
    global history_ecg
    global history_R_peak_height
    global history_R_peak_idx
    global history_time
    global previous_history_R_peak_height
    global previous_history_R_peak_idx
    
    # Clear all previous stored data
    history_ecg.clear()
    history_R_peak_height.clear()
    history_R_peak_idx.clear()
    previous_history_R_peak_height.clear()
    previous_history_R_peak_idx.clear()
    history_time.clear()
    
    # Reinitialize the history variables as empty lists
    history_R_peak_idx = []
    previous_history_R_peak_idx = []
    history_R_peak_height = []
    previous_history_R_peak_height = []
    history_ecg = []
    history_time = []

def butter_lowpass(cutoff, fs, order=4):
    """
    Designs a Butterworth low-pass filter.
    
    Parameters:
        cutoff (float): Cutoff frequency of the low-pass filter in Hz.
        fs (float): Sampling frequency of the signal in Hz.
        order (int, optional): Order of the Butterworth filter. Defaults to 4.
    
    Returns:
        tuple: Filter coefficients (b, a) for the low-pass filter.
    
    Note:
        - The function computes the Butterworth filter's coefficients using the scipy butter function.
        - The filter's frequency response is designed to allow frequencies below the cutoff to pass and attenuate frequencies above the cutoff.
        - The filter is digital (not analog), and the Nyquist frequency is used to normalize the cutoff frequency.
    """
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def lowpass_filter(ecg, fs, cutoff=12.0):
    """
    Applies a low-pass filter to the input ECG signal to remove high-frequency noise.
    
    Parameters:
        ecg (array-like): Input ECG signal to be filtered.
        fs (float): Sampling frequency of the ECG signal in Hz.
        cutoff (float, optional): Cutoff frequency of the low-pass filter in Hz. Defaults to 12.0 Hz.
    
    Returns:
        numpy.ndarray: Filtered ECG signal with low-frequency components preserved.
    
    Note:
        - Uses a Butterworth low-pass filter implemented by the butter_lowpass function.
        - The filter removes frequencies above the specified cutoff to eliminate high-frequency noise.
        - The filtfilt function is used to apply the filter forward and backward, ensuring zero-phase distortion.
    """
    b, a = butter_lowpass(cutoff, fs)
    return filtfilt(b, a, ecg)

def butter_highpass(cutoff, fs, order=4):
    """
    Designs a Butterworth high-pass filter.
    
    Parameters:
        cutoff (float): Cutoff frequency of the high-pass filter in Hz.
        fs (float): Sampling frequency of the signal in Hz.
        order (int, optional): Order of the Butterworth filter. Defaults to 4.
    
    Returns:
        tuple: Filter coefficients (b, a) for the high-pass filter.
    
    Note:
        - The function computes the Butterworth filter's coefficients using the scipy butter function.
        - The filter's frequency response is designed to allow frequencies above the cutoff to pass and attenuate frequencies below the cutoff.
        - The filter is digital (not analog), and the Nyquist frequency is used to normalize the cutoff frequency.
    """
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return b, a

def highpass_filter(ecg, fs, cutoff=5.0):
    """
    Applies a high-pass filter to the input ECG signal to remove low-frequency noise.
    
    Parameters:
        ecg (array-like): Input ECG signal to be filtered.
        fs (float): Sampling frequency of the ECG signal in Hz.
        cutoff (float, optional): Cutoff frequency of the high-pass filter in Hz. Defaults to 5.0 Hz.
    
    Returns:
        numpy.ndarray: Filtered ECG signal with high-frequency components preserved.
    
    Note:
        - Uses a Butterworth high-pass filter implemented by the butter_highpass function.
        - The filter removes frequencies below the specified cutoff to eliminate low-frequency noise, such as baseline wander.
        - The filtfilt function is used to apply the filter forward and backward, ensuring zero-phase distortion.
    """
    b, a = butter_highpass(cutoff, fs)
    
    return filtfilt(b, a, ecg)

def derivative(ecg):
    """
    Computes the numerical derivative of the input ECG signal.
    
    Parameters:
        ecg (array-like): Input ECG signal to calculate the derivative.
    
    Returns:
        numpy.ndarray: Derivative of the ECG signal (rate of change).
    
    Note:
        - Uses numpy's diff function to calculate the difference between consecutive samples.
        - The output signal will have one fewer sample than the input signal.
        - The derivative highlights rapid changes in the ECG signal, useful for detecting peaks or rapid fluctuations.
    """
    return np.diff(ecg)

def square(ecg):
    """
    Applies a squaring operation to the input ECG signal.
    
    Parameters:
        ecg (array-like): Input ECG signal to be squared
    
    Returns:
        numpy.ndarray: Squared ECG signal
    
    Note:
        - The squaring operation amplifies higher values in the ECG signal.
    """
    return ecg ** 2

def moving_average_filter(signal, window_size=150):
    """
    Applies a moving average filter to smooth the input signal.
    
    Parameters:
        signal (array-like): Input signal to be smoothed
        window_size (int): Size of the moving average window in samples.
                          Defaults to 150 samples.
    
    Returns:
        numpy.ndarray: Smoothed signal after applying moving average filter
    
    Note:
        - Uses numpy's convolve function with 'same' mode to maintain signal length
        - Window weights are uniform (simple moving average)
        - Edge effects are present for first and last (window_size-1)/2 samples
    """
    # Create window of ones normalized by window size
    window = np.ones(window_size) / window_size
    
    # Apply convolution with 'same' mode to maintain signal length
    filtered_signal = np.convolve(signal, window, mode='same')
    
    return filtered_signal

def update_analysis_window(ecg_data, time_data, fs=512, window_duration=3):
    """
    Updates the sliding analysis window for ECG data and corresponding time values.
    
    Parameters:
        ecg_data (array-like): New ECG signal data to be incorporated
        time_data (array-like): Corresponding time values for the ECG data
        fs (int): Sampling frequency in Hz. Defaults to 512 Hz.
        window_duration (int): Duration of analysis window in seconds. Defaults to 3.
    
    Global Variables Modified:
        idx_window: Global index tracking the current window position
        ecg_window: Global buffer storing ECG data for the analysis window
        time_window: Global buffer storing time values for the analysis window
    
    Returns:
        tuple: A tuple containing:
            - updated_ecg (list): Updated ECG data window
            - updated_time (list): Updated time values window
            
    Note:
        - Detects measurement discontinuities by checking time gaps
        - Resets history and reinitializes windows if discontinuity detected
        - Maintains fixed-size windows for both ECG and time data
        - Windows are shifted and padded as needed for partial updates
    """  
    global idx_window
    global ecg_window
    global time_window
    
    # Convert inputs to lists
    ecg_data = list(ecg_data)
    time_data = list(time_data)
    
    # Update window index
    idx_window = int(time_data[0] * fs)
    
    # Check for measurement discontinuity
    TIME_GAP_THRESHOLD = 0.01  # seconds
    if abs(time_window[-1] - time_data[0]) > TIME_GAP_THRESHOLD:
        print("ERROR: Measurement discontinuity detected!")
        reset_history_data()
        
        # Initialize empty windows
        window_size = window_duration * fs
        ecg_window = [0] * window_size
        time_window = [
            -(window_size - i) / fs + time_data[0]
            for i in range(window_size)
        ]
    
    # Calculate window size in samples
    window_size = window_duration * fs
    
    # Handle ECG data update
    if len(ecg_data) >= window_size:
        updated_ecg = ecg_data[-window_size:]
    else:
        # Shift existing data and add new samples
        current_ecg = ecg_window.copy()
        shift = len(ecg_data)
        updated_ecg = current_ecg[shift:] + ecg_data
        
        # Pad if needed
        if len(updated_ecg) < window_size:
            padding_size = window_size - len(updated_ecg)
            updated_ecg.extend(ecg_window[:padding_size])
    
    # Handle time data update
    if len(time_data) >= window_size:
        updated_time = time_data[-window_size:]
    else:
        # Shift existing data and add new samples
        current_time = time_window.copy()
        shift = len(time_data)
        updated_time = current_time[shift:] + time_data
        
        # Pad if needed
        if len(updated_time) < window_size:
            padding_size = window_size - len(updated_time)
            updated_time.extend(time_data[:padding_size])
    
    # Update global windows
    ecg_window = updated_ecg.copy()
    time_window = updated_time.copy()
    
    return updated_ecg, updated_time

def apply_pan_tompkins_filter(ecg_signal, fs=512):
    """
    Implements the Pan-Tompkins algorithm for QRS detection in ECG signals.
    
    The algorithm consists of a series of filters to emphasize the QRS complex:
    1. Bandpass filtering (5-12 Hz) to remove noise and baseline wander
    2. Derivative filter to emphasize high-frequency components of the QRS complex
    3. Squaring operation to emphasize large differences in signal
    4. Moving average integration window to obtain waveform feature information
    
    Parameters:
        ecg_signal (array-like): Raw ECG signal to be processed
        fs (int): Sampling frequency of the ECG signal in Hz. Defaults to 512 Hz.
    
    Returns:
        numpy.ndarray: Processed signal after applying the Pan-Tompkins algorithm
    
    Note:
        - The function expects the following helper functions to be defined:
          * lowpass_filter(signal, fs, cutoff)
          * highpass_filter(signal, fs, cutoff)
          * derivative(signal)
          * square(signal)
          * moving_average_filter(signal)
        - The bandpass filter is implemented as cascaded high-pass and low-pass filters
        - Cutoff frequencies are set to 5 Hz (high-pass) and 12 Hz (low-pass)
    
    Reference:
        Pan, J., & Tompkins, W. J. (1985). A real-time QRS detection algorithm.
        IEEE Transactions on Biomedical Engineering, (3), 230-236.
    """
    # Convert input to numpy array for consistent processing
    ecg_signal = np.array(ecg_signal)
    
    # Step 1: Bandpass filtering (cascaded low-pass and high-pass)
    LOWPASS_CUTOFF = 12.0  # Hz
    HIGHPASS_CUTOFF = 5.0  # Hz
    
    # Apply low-pass then high-pass filter
    bandpass_filtered = highpass_filter(
        lowpass_filter(ecg_signal, fs, LOWPASS_CUTOFF),
        fs,
        HIGHPASS_CUTOFF
    )
    
    # Step 2: Derivative filter
    # Emphasizes the steep slopes characteristic of the QRS complex
    derivative_signal = derivative(bandpass_filtered)
    
    # Step 3: Squaring
    # Intensifies large differences and suppresses small differences
    squared_signal = square(derivative_signal)
    
    # Step 4: Moving average integration
    # Smooths the output and provides waveform feature information
    integrated_signal = moving_average_filter(squared_signal)
    
    return integrated_signal

def refine_r_peak_locations(ecg_signal, peak_indices, search_window=55):
    """
    Refines the location of detected R-peaks by finding local maxima in the raw ECG signal.
    
    Parameters:
        ecg_signal (array-like): Raw ECG signal data
        peak_indices (list): Initial R-peak indices to be refined
        search_window (int): Number of samples to search on each side of the initial peak.
                           Defaults to 55 samples.
    
    Returns:
        tuple: A tuple containing:
            - refined_peaks (list): List of corrected R-peak indices
            - peak_amplitudes (list): List of ECG signal amplitudes at refined peak locations
    
    Note:
        - For each initial peak, searches within ±search_window samples for the true local maximum
        - Handles edge cases (beginning and end of signal)
        - Returns empty lists if either input is empty
        - Peak amplitudes are returned as integers for consistency
    """
    refined_peaks = []
    
    # Handle empty input cases
    if not peak_indices or not ecg_signal:
        return [], []
    
    # Refine each peak location
    for initial_index in peak_indices:
        # Define search range with boundary protection
        window_start = max(0, initial_index - search_window)
        window_end = min(len(ecg_signal), initial_index + search_window + 1)
        
        # Extract signal window around initial peak
        signal_window = ecg_signal[int(window_start):int(window_end)]
        
        # Find local maximum
        local_max_offset = np.argmax(signal_window)
        refined_index = local_max_offset + window_start
        
        refined_peaks.append(refined_index)
    
    # Get signal amplitudes at refined peak locations
    peak_amplitudes = [
        int(ecg_signal[int(peak_index)])
        for peak_index in refined_peaks
    ]
    
    return refined_peaks, peak_amplitudes

def update_history_ecg(ecg_data, fs=512, window_duration=7):
    """
    Updates the ECG signal history within a fixed-duration sliding window.
    
    Parameters:
        ecg_data (array-like): New ECG signal data to be incorporated into history
        sampling_rate (int): Sampling frequency in Hz. Defaults to 512 Hz.
        window_duration (int): Duration of the analysis window in seconds. Defaults to 7.
    
    Global Variables Modified:
        history_ecg: Global list storing the ECG signal history
    
    Note:
        - Maintains a fixed-size window of ECG data (default 7 seconds)
        - Handles both complete and partial data updates
        - For partial updates, shifts existing data and adds new samples
        - Ensures consistent window size by padding if necessary
    """
    global history_ecg
    
    # Convert input to list if it isn't already
    ecg_data = list(ecg_data)
    
    # Calculate fixed window size in samples
    window_size_samples = fs * window_duration
    
    # Handle case where new data exceeds window size
    if len(ecg_data) >= window_size_samples:
        history_ecg = ecg_data[-window_size_samples:]
        return
    
    # Handle case where new data is smaller than window size
    current_ecg = history_ecg.copy()
    shift = len(ecg_data)
    
    # Shift existing values and add new ones
    result_ecg = current_ecg[shift:] + ecg_data
    
    # Fill remaining space if needed
    if len(result_ecg) < window_size_samples:
        padding_size = window_size_samples - len(result_ecg)
        result_ecg.extend(ecg_data[:padding_size])
    
    history_ecg = result_ecg.copy()


def update_history_time(ecg_data_size, fs=512, window_duration=7):
    """
    Updates the time history for ECG data analysis with a sliding window approach.
    
    Parameters:
        ecg_data_size (int): Size of the current ECG data window in samples
        fs (int): Sampling frequency in Hz. Defaults to 512 Hz.
        window_duration (int): Duration of the analysis window in seconds. Defaults to 7.
    
    Global Variables Modified:
        window_index: Global index tracking the current window position
        history_time: Global list storing time values for the analysis window
    
    Returns:
        None
        
    Note:
        - Generates time values based on the window position and sampling rate
        - Maintains a fixed-size window (default 7 seconds)
        - Handles both complete and partial windows
        - Time values are in seconds, calculated from sample indices
    """
    global idx_window
    global history_time
    
    # Generate new time values based on window position
    new_time_values = [
        (i + idx_window) / fs 
        for i in range(ecg_data_size * fs)
    ]
    
    # Calculate fixed window size in samples
    window_size_samples = window_duration * fs
    
    # Handle case where new data exceeds window size
    if len(new_time_values) >= window_size_samples:
        history_time = new_time_values[-window_size_samples:]
        return
    
    # Handle case where new data is smaller than window size
    current_time_values = history_time.copy()
    shift = len(new_time_values)
    
    # Shift existing values and add new ones
    result_time = current_time_values[shift:] + new_time_values
    
    # Fill remaining space if needed
    if len(result_time) < window_size_samples:
        padding_size = window_size_samples - len(result_time)
        result_time.extend(new_time_values[:padding_size])
    
    history_time = result_time.copy()
   
def update_history(r_peak,peak_heights,ecg_signal, max_window_seconds=7):
    """
    Updates the global history of R-peaks and related data within a sliding time window.
    
    Parameters:
        r_peak (list): List of newly detected R-peak indices
        peak_heights (list): List of corresponding R-peak heights
        ecg_signal (list): Current ECG signal window
        max_window_seconds (int): Maximum duration of history window in seconds. Defaults to 7.
    
    Global Variables Modified:
        history_peak_indices: Global list of historical R-peak indices
        history_peak_heights: Global list of historical R-peak heights
        history_ecg: Global ECG signal history
        history_time: Global time values history
    
    Note:
        - Function maintains a sliding window of R-peak detections and related data
        - Prevents duplicate peaks by checking minimum distance between peaks (0.3s)
        - Ensures history window doesn't exceed specified duration (default 7s)
        - Updates all related historical data (ECG signal, time values, peak heights)
        - Uses sampling rate of 512 Hz for time calculations
    """
    global history_R_peak_idx
    global history_R_peak_height
    global history_ecg
    global history_time
    
    # Update ECG and time history
    update_history_ecg(ecg_signal)
    update_history_time(len(ecg_signal))
    
    
    # Update R_peak et R_peak_height history   
    # Create working copies of global peak data
    current_peak_indices = history_R_peak_idx.copy()
    current_peak_heights = history_R_peak_height.copy()
    
    # Process new peaks while avoiding duplicates
    MINIMUM_PEAK_DISTANCE = int(0.3 * 512)  # 0.3s at 512 Hz sampling rate
    
    for i, new_peak_idx in enumerate(r_peak):
        # Check if new peak is sufficiently distant from existing peaks
        is_unique_peak = True
        for existing_peak_idx in history_R_peak_idx:
            if abs(new_peak_idx - existing_peak_idx) < MINIMUM_PEAK_DISTANCE:
                is_unique_peak = False
                break
        
        # Add new peak if it's unique
        if is_unique_peak:
            current_peak_indices.append(new_peak_idx)
            current_peak_heights.append(peak_heights[i])    
    
    # Update history peak data
    history_R_peak_idx = current_peak_indices .copy()
    history_R_peak_height = current_peak_heights.copy()
    
    # Trim history to maintain maximum window duration
    MAX_WINDOW_SAMPLES = max_window_seconds * 512  # Convert seconds to samples
    history_idx_7_sec = history_R_peak_idx.copy()  # Pour ne pas modifier la liste originale
    
    # Remove oldest peaks until window duration is within limit
    while len(history_idx_7_sec) > 1:  
        window_duration = abs(history_idx_7_sec[-1] - history_idx_7_sec[0])  
        if window_duration <= MAX_WINDOW_SAMPLES:
            break  
        history_idx_7_sec = history_idx_7_sec[1:] 
    
    # Update global variables with trimmed data
    history_R_peak_idx = history_idx_7_sec
    history_R_peak_height = history_R_peak_height[-len(history_R_peak_idx):]
    
def detect_R_peak(filtered_ecg_window, raw_ecg_window, time_window, fs=512, min_peak_distance = 0.3,threshold_factor=1/2, history_size=3):
    """
    Detects the R-peaks in the ECG window and calculates the heart rate indicator.
    
    Parameters:
        filtered_ecg_window (list): List of filtered ECG data points within the current window.
        raw_ecg_window (list): List of raw ECG data points within the current window.
        time_window (list): List of time values corresponding to the ECG data within the current window.
        sampling_rate (int): Sampling frequency of the ECG signal in Hz. Defaults to 512 Hz.
        min_peak_distance (float): Minimum required distance between consecutive R-peaks in seconds. Defaults to 0.3s.
        threshold_factor (float): Factor to determine minimum peak height threshold (0-1). Defaults to 1/2.
        history_size (int): Size of the peak history to maintain in seconds. Defaults to 3.
    
    Returns:
        list: List of detected R-peak indices adjusted for the window position in the complete signal.
    
    Note:
        - The function works with both complete and partial windows (time_window[0] < 0 indicates partial window)
        - Peak detection uses a threshold-based approach on the filtered signal
        - Peak locations are refined using the raw ECG signal
        - The function maintains a 7-second history of detected peaks
        - Edge effects are handled by excluding 0.5s from both ends of the window
    """
    
    window_size  = 3*512
    
    # Determine window position offset
    # If time_window[0] < 0, window is not yet full, so offset is 0
    # If time_window[0] >= 0, window is full, use it as reference
    
    if time_window[0] <= 0 : 
        window_offset_index = 0
    else :
        window_offset_index = int(time_window[0]*fs)
    
    # Calculate minimum peak height threshold
    min_peak_height = np.max(filtered_ecg_window) * threshold_factor
    
    # Detect peaks excluding 0.5s from edges (256 points at 512 Hz)
    edge_margin = int(0.5 * fs) 
    peak_indices, _ = find_peaks(filtered_ecg_window[edge_margin:window_size - edge_margin], distance=int(min_peak_distance * fs), height=min_peak_height )
    
    # Adjust peak indices to account for edge margin
    peak_indices = [index + edge_margin for index in peak_indices]
    
    # Refine R-peak locations using raw ECG signal
    peak_indices, peak_heights = refine_r_peak_locations(raw_ecg_window,peak_indices)
        
    # Adjust peak indices for window position in complete signal
    if time_window[0] <= 0:
        peak_indices = [index - abs(time_window[0] * fs) for index in peak_indices]
    else:
        peak_indices = [index + window_offset_index for index in peak_indices]
    
    # Update 7-second peak history
    update_history(peak_indices,peak_heights,raw_ecg_window)
    
    return peak_indices

def trouver_valeurs_uniques(liste_un, liste_deux):
    """
    Compare deux listes et retourne les valeurs présentes dans liste_un 
    mais absentes de liste_deux.
    
    Args:
        liste_un (list): Première liste de nombres
        liste_deux (list): Deuxième liste de nombres
    
    Returns:
        list: Liste des valeurs uniques à liste_un
    """
    # Convertir les listes en ensembles pour une comparaison efficace
    set_un = set(liste_un)
    set_deux = set(liste_deux)
    
    # Trouver les valeurs présentes uniquement dans liste_un
    valeurs_uniques = list(set_un - set_deux)
    
    # Trier les valeurs pour les avoir dans l'ordre
    valeurs_uniques.sort()
    
    return valeurs_uniques

def calculate_heart_rate():
    """
    Calculates the heart rate for `history_peak_idx`, returning a heart rate value only if it did not exist before.

    Returns:
        heart_rate:                    List of heart rates for the new elements since the last time the function was called.
        heart_rate_timestamp:          List of heart rate timestamps for the new elements since the last time the function was called.
        None:                          If no changes were detected.
    """
    global previous_history_R_peak_idx
    global history_R_peak_idx
    
    #######################
    ###### HEART RATE #####
    #######################
    
    # If the current list is identical to the previous one
    if history_R_peak_idx == previous_history_R_peak_idx:
        return None, None
        
    # If it's the first call (previous list is empty) and history_R_peak_idx contains less than 1 R-peak
    if not previous_history_R_peak_idx and len(history_R_peak_idx)<=1:
        previous_history_R_peak_idx = history_R_peak_idx.copy()
        return None, None
    
        
    # Calculate the timestamps of the new Heart Rates (R-R, using the most recent R for timestamping).
    set_history_R_peak_idx = set(history_R_peak_idx)
    set_previous_history_R_peak_idx = set(previous_history_R_peak_idx)
    last_peak_found = list(set_history_R_peak_idx - set_previous_history_R_peak_idx)
    last_peak_found.sort()

    heart_rate_timestamp = []
    for i in range(len(last_peak_found)):
        heart_rate_timestamp.append(last_peak_found[i]/512)
    
    # If there are no new elements
    if not last_peak_found:
        previous_history_R_peak_idx = history_R_peak_idx.copy()
        return None, None
        
    # Calculate the intervals RR
    differences = []
    if not previous_history_R_peak_idx :
        last_previous = history_R_peak_idx[0]
    else :
        last_previous = previous_history_R_peak_idx[-1]
    
    for element in last_peak_found:
        diff = element - last_previous
        differences.append(diff)
        last_previous = element
    
    # Calculate the intervals in seconds
    differences_seconds = []
    for i in range(len(differences)):
        differences_seconds.append(differences[i]/512)
    
    # Turn into Heart Rate
    heart_rate = []
    for i in range(len(differences_seconds)):
        if differences_seconds[i] > 0.3 : # Never possible to have less than 0.3s in difference_seconds value, because it will be equivalent to heart rate = 200 bpm
            heart_rate.append(int(60/differences_seconds[i]))
    
    # Update previous_list
    previous_history_R_peak_idx = history_R_peak_idx.copy()
    
    return heart_rate, heart_rate_timestamp

def calculate_breathing_rate():
    """
    Calculates the breathing rate for `history_R_peak_height`, returning a breathing rate value only if it did not exist before.

    Returns:
        breathing_rates:               List of breathing rates for the new elements since the last time the function was called.
        breathing_rates_timestamp:     List of breathing rates timestamps for the new elements since the last time the function was called.
        None:                          If no changes were detected.
    """
    global previous_history_R_peak_height
    global history_R_peak_height
    global history_R_peak_idx
    
    ########################
    #### BREATHING RATE ####
    ########################
    
    # If the current list is identical to the previous one
    if history_R_peak_height == previous_history_R_peak_height:
        return None, None
        
    # If it's the first call (previous list is empty)
    if not previous_history_R_peak_height and len(history_R_peak_height) <= 0:
        previous_history_R_peak_height = history_R_peak_height.copy()
        return None, None
        
    # Get new Breathing Rate
    set_history_R_peak_height = set(history_R_peak_height)
    set_previous_history_R_peak_height = set(previous_history_R_peak_height)
    breathing_rates = list(set_history_R_peak_height - set_previous_history_R_peak_height)
    breathing_rates.sort()
    
    #breathing_rates = history_R_peak_height[len(previous_history_R_peak_height):]
    
    # If there are no new elements
    if not breathing_rates:
        previous_history_R_peak_height = history_R_peak_height.copy()
        return None, None
    
    # Calculate the timestamps of the new Breathing Rates (using R for timestamping)
    breathing_rates_timestamp = []
    for height in breathing_rates:
        if height in history_R_peak_height:
            idx = history_R_peak_height.index(height)
            breathing_rates_timestamp.append(history_R_peak_idx[idx]/512)
    
    # Update the previous list
    previous_history_R_peak_height = history_R_peak_height.copy()
    
    
    return breathing_rates,breathing_rates_timestamp

def measure_hr(ecg_window,time_window):
    """
    Detects the R-peaks in the ECG window and calculates the heart rate indicator.
    
    Parameters:
        ecg_window (list): List of ECG data points within the current window.
        time_window (list): List of time values corresponding to the ECG data within the current window.

    Returns:
        tuple: A tuple containing:
            - r_peak (list): List of detected R-peaks in the ECG window.
            - heart_rate (float): Instantaneous heart rate (beats per minute).
            - timestamp_heart_rate (float): Timestamp of the instantaneous heart rate measurement.

    Note:
        - The function first filters the ECG window using the Pan-Tompkins algorithm for QRS detection.
        - The R-peaks are then detected using a threshold-based method with configurable parameters.
        - The heart rate (BPM) are calculated using predefined indicators.
    """
    # Apply Pan-Tompkins filtering to the ECG window
    ecg_window_filtered = apply_pan_tompkins_filter(ecg_window)
    # Detect R-peaks using the filtered ECG window
    r_peak = detect_R_peak(ecg_window_filtered,ecg_window,time_window, fs=512, threshold_factor=1/2, history_size=3)
    
    # Calculate instantaneous heart rate (BPM)
    heart_rate, timestamp_heart_rate = calculate_heart_rate()
    
    
    # Return HR
    return r_peak, heart_rate, timestamp_heart_rate

def measure_br(ecg_window,time_window):
    """
    Detects the R-peaks in the ECG window and calculates the heart rate indicator.
    
    Parameters:
        ecg_window (list): List of ECG data points within the current window.
        time_window (list): List of time values corresponding to the ECG data within the current window.

    Returns:
        tuple: A tuple containing:
            - r_peak (list): List of detected R-peaks in the ECG window.
            - breathing_rate (float): Instantaneous breathing rate (beats per minute).
            - timestamp_breathing_rate (float): Timestamp of the instantaneous breathing rate measurement.

    Note:
        - The function first filters the ECG window using the Pan-Tompkins algorithm for QRS detection.
        - The R-peaks are then detected using a threshold-based method with configurable parameters.
        - The breathing rate are calculated using predefined indicators.
    """
    # Apply Pan-Tompkins filtering to the ECG window
    ecg_window_filtered = apply_pan_tompkins_filter(ecg_window)
    # Detect R-peaks using the filtered ECG window
    r_peak = detect_R_peak(ecg_window_filtered,ecg_window,time_window, fs=512, threshold_factor=1/2, history_size=3)
    
    # Calculate instantaneous breathing rate 
    breathing_rate, timestamp_breathing_rate = calculate_breathing_rate()
    
    # Return BR
    return r_peak, breathing_rate, timestamp_breathing_rate

def updateHR(data_ecg,data_time):
    """
    Processes the given ECG data and time to calculate the heart rate using a sliding window approach.
    If any data is lost during the window update, the function triggers the saving of the data.

    Parameters:
        data_ecg (list): List of ECG data points to be processed.
        data_time (list): List of corresponding time values for the ECG data.

    Returns:
    tuple: A tuple containing:
        - r_peak (list): List of detected R-peaks in the ECG window.
        - heart_rate (float): Instantaneous heart rate (beats per minute).
        - timestamp_heart_rate (float): Timestamp of the instantaneous heart rate measurement.

    Note:
        - The function calls `measure_hr()` to detect R-peaks and calculate heart rate and breathing rhythm indicators.
    """
    idx_positive_time_value = 0
    # Handle negative time values
    if data_time[0]<0:
        for i, number in enumerate(data_time):
            if number > 0:
                idx_positive_time_value = i
                break
        temp_ecg_data = data_ecg[idx_positive_time_value:]
        temp_time_data = data_time[idx_positive_time_value:]
    else : 
        temp_ecg_data = data_ecg.copy()
        temp_time_data = data_time.copy()
    
    # Update the ECG window and time window
    ecg_window,time_window = update_analysis_window(temp_ecg_data,temp_time_data)
        
    # Call measure_hr to calculate heart rate 
    return measure_hr(ecg_window,time_window) 

def updateBR(data_ecg,data_time):
    """
    Processes the given ECG data and time to calculate the breathing rate using a sliding window approach.
    If any data is lost during the window update, the function triggers the saving of the data.

    Parameters:
        data_ecg (list): List of ECG data points to be processed.
        data_time (list): List of corresponding time values for the ECG data.

    Returns:
        tuple: A tuple containing:
            - r_peak (list): List of detected R-peaks in the ECG window.
            - breathing_rate (int): Instantaneous breathing rhythm.
            - timestamp_breathing_rate (float): Timestamp of the instantaneous breathing rhythm measurement.

    Note:
        - The function calls `measure_br()` to detect R-peaks and calculate breathing rate.
    """
    idx_positive_time_value = 0
    # Handle negative time values
    if data_time[0]<0:
        for i, number in enumerate(data_time):
            if number > 0:
                idx_positive_time_value = i
                break
        temp_ecg_data = data_ecg[idx_positive_time_value:]
        temp_time_data = data_time[idx_positive_time_value:]
    else : 
        temp_ecg_data = data_ecg.copy()
        temp_time_data = data_time.copy()
    
    # Update the ECG window and time window
    ecg_window,time_window = update_analysis_window(temp_ecg_data,temp_time_data)
        
    # Call measure_br to calculate breathing rate 
    return measure_br(ecg_window,time_window) 

def updateHR_BR(data_ecg,data_time):
    """
    Processes the given ECG data and time to calculate the heart and breathing rate using a sliding window approach.
    If any data is lost during the window update, the function triggers the saving of the data.

    Parameters:
        data_ecg (list): List of ECG data points to be processed.
        data_time (list): List of corresponding time values for the ECG data.

    Returns:
        tuple: A tuple containing:
            - r_peak (list): List of detected R-peaks in the ECG window.
            - heart_rate (float): Instantaneous heart rate (beats per minute).
            - timestamp_heart_rate (float): Timestamp of the instantaneous heart rate measurement.
            - breathing_rate (int): Instantaneous breathing rhythm.
            - timestamp_breathing_rate (float): Timestamp of the instantaneous breathing rhythm measurement.

    Note:
        - The function calls `measure_hr()` and `measure_br()` to detect R-peaks and calculate heart rate and breathing rate indicators.
    """
    idx_positive_time_value = 0
    # Handle negative time values
    if data_time[0]<0:
        for i, number in enumerate(data_time):
            if number > 0:
                idx_positive_time_value = i
                break
        temp_ecg_data = data_ecg[idx_positive_time_value:]
        temp_time_data = data_time[idx_positive_time_value:]
    else : 
        temp_ecg_data = data_ecg.copy()
        temp_time_data = data_time.copy()
    
    # Update the ECG window and time window
    ecg_window,time_window = update_analysis_window(temp_ecg_data,temp_time_data)
    
    # Call measure_hr to calculate heart rate 
    r_peak, heart_rate, timestamp_heart_rate = measure_hr(ecg_window,time_window)
        
    # Call measure_br to calculate breathing rate 
    r_peak, breathing_rate, timestamp_breathing_rate = measure_br(ecg_window,time_window)
    
    return r_peak, heart_rate, timestamp_heart_rate, breathing_rate, timestamp_breathing_rate