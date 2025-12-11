import socket
import json
import FreeSimpleGUI as sg
import time
import math # Not strictly needed, but useful for complex rounding

## --- Network Configuration ---
HOST = '127.0.0.1' # localhost for testing
# HOST = 'PI IP' # Use a real IP for remote access
PORT = 5000
FETCH_INTERVAL = 2 # Seconds between fetch attempts

#Color Constants for the GUI buttons, picked to match the GUI theme(taken from lab code)

COLOR_IDLE = '#404040'   # Dark Gray
COLOR_SUCCESS = '#008000' # Green
COLOR_ERROR = '#8B0000'  # Dark Red (Maroon)
COLOR_LOOP = '#FFD700'   # Gold/Yellow for Automatic Mode

#LED unicode characters (replaced use of two separate characters with just one character, changing colour instead)
LED_OFF_CHAR = '⚫' # Black Circle
LED_ON_CHAR = '🟢'  # Green Circle

#Data Processing Function 
def process_and_round_data(pi_data):
    """Parses numerical data from the dictionary, rounds it, and returns a string."""
    rounded_data = {}
    output_text = "--- Raspberry Pi Data Received ---\n"
    
    for key, value in pi_data.items():
        if key in ["Temperature_C", "Core_Voltage_V", "ARM_Frequency_MHz"]:
            try:
                # Attempt to convert to float
                float_value = float(value)
                
                # Round to one decimal place
                rounded_value = round(float_value, 1)
                
                rounded_data[key] = rounded_value
                output_text += f"{key}:   {rounded_value}\n"
            except ValueError:
                # If conversion fails, keep the original string value
                rounded_data[key] = value
                output_text += f"{key}:   {value} (Error/Raw)\n"
        else:
            # Keep non-numerical data (like Firmware Version, PMIC_EXT5V_Voltage) as is
            rounded_data[key] = value
            output_text += f"{key}:   {value}\n"
            
    return output_text, rounded_data

#GUI Layout Block
sg.theme('DarkAmber')

layout = [
    [
        sg.Text('Connection Status: ', size=(16, 1)),
        # Connectivity Indicator
        sg.Text(' Idle ', size=(8, 1), background_color=COLOR_IDLE,
                text_color='white', justification='center', key='-STATUS_LIGHT-'),
        sg.Text(f' | Server: {HOST}:{PORT}', key='-STATUS_TEXT-'),
        sg.Text(' | Data Received: '),
        # Unicode LED
        sg.Text(LED_OFF_CHAR, size=(2, 1), key='-UNICODE_LED-', text_color='gray')
    ],
    [
        # Button is now a toggle for the automated loop
        sg.Button('Start Auto Fetch', key='-FETCH_BUTTON-', button_color=('white', COLOR_SUCCESS)),
        sg.Button('Stop Auto Fetch', key='-STOP_BUTTON-', button_color=('white', COLOR_ERROR), disabled=True),
        sg.Button('Exit', key='-EXIT_BUTTON-', button_color=('white', COLOR_ERROR))
    ],
    [sg.HorizontalSeparator()],
    [sg.Text('vcgencmd Output (Rounded to 1 decimal place):', size=(40, 1))],
    [sg.Multiline(default_text='Press "Start Auto Fetch" to begin timed data collection...',
                  size=(60, 12), key='-OUTPUT-', autoscroll=True, disabled=True)]
]

window = sg.Window('TPRG Project 2: Client Side     Sebastian Azevedo', layout)

# State Variables
auto_fetch_running = False
led_state = False
fetch_count = 0 # Track fetches

#Main Loop
while True:
    # Read the window with a timeout to allow the automated process to run
    event, values = window.read(timeout=100) # Timeout of 100ms

    if event == sg.WIN_CLOSED or event == '-EXIT_BUTTON-' or event == 'Cancel':
        break
    
    # 1. Start Auto Fetch Button Handler
    if event == '-FETCH_BUTTON-' and not auto_fetch_running:
        auto_fetch_running = True
        fetch_count = 0 # Reset counter
        window['-FETCH_BUTTON-'].update('Running...', disabled=True, button_color=('white', COLOR_LOOP))
        window['-STOP_BUTTON-'].update(disabled=False)
        window['-STATUS_LIGHT-'].update('Running', background_color=COLOR_LOOP, text_color='black')
        window['-OUTPUT-'].update(f'Starting automated fetch every {FETCH_INTERVAL} seconds...')

    # 2. Stop Auto Fetch Button Handler
    if event == '-STOP_BUTTON-':
        auto_fetch_running = False
        window['-FETCH_BUTTON-'].update('Start Auto Fetch', disabled=False, button_color=('white', COLOR_SUCCESS))
        window['-STOP_BUTTON-'].update(disabled=True)
        window['-STATUS_LIGHT-'].update(' Idle ', background_color=COLOR_IDLE, text_color='white')
        window['-STATUS_TEXT-'].update(f' | Server: {HOST}:{PORT} | Status: Stopped')
        window['-OUTPUT-'].print(f'\n--- Auto Fetch Stopped Manually at {fetch_count} attempts. ---')

    # 3. Timed Auto Fetch Logic
    if auto_fetch_running and (event == sg.TIMEOUT_KEY or event == '-FETCH_BUTTON-'):
        
        # Check if the required time has passed since the last fetch
        current_time = time.time()
        if 'last_fetch_time' not in locals():
            last_fetch_time = current_time - FETCH_INTERVAL # Ensure first run executes immediately
            
        if current_time - last_fetch_time >= FETCH_INTERVAL:
            last_fetch_time = current_time # Update timer for next cycle
            
            fetch_count += 1
            window['-STATUS_TEXT-'].update(f' | Server: {HOST}:{PORT} | Status: Fetching #{fetch_count}...')
            window.refresh() # Force update status immediately

            try:
                # 3a. Establish connection
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(1) # Short timeout is better for a loop
                client_socket.connect((HOST, PORT))

                # 3b. Receive data
                data_bytes = client_socket.recv(4096)
                client_socket.close()

                # 3c. Process data
                json_string = data_bytes.decode('utf-8')
                pi_data = json.loads(json_string)

                # 3d. Format, Round, and Display
                output_text, _ = process_and_round_data(pi_data)
                window['-OUTPUT-'].update(output_text)
                
                # 3e. Set Status to Success (Green) and Toggle Unicode LED
                window['-STATUS_TEXT-'].update(f' | Server: {HOST}:{PORT} | Status: SUCCESS (#{fetch_count})')
                window['-STATUS_LIGHT-'].update(' Online ', background_color=COLOR_SUCCESS, text_color='white')
                
                # Toggle LED state colour change only to remove bizarre visual artifact  
                led_state = not led_state
                if led_state:
                    window['-UNICODE_LED-'].update(LED_ON_CHAR, text_color='green')
                else:
                    window['-UNICODE_LED-'].update(LED_ON_CHAR, text_color='#404040') 


            except ConnectionRefusedError:
                error_msg = f"ERROR: Connection Refused. Server is likely shut down after 50 attempts."
                window['-OUTPUT-'].print(f'\n{error_msg}')
                
                # Stop the loop and set error status
                window['-STATUS_TEXT-'].update(f' | Server: {HOST}:{PORT} | Status: SERVER EXIT')
                window['-STATUS_LIGHT-'].update(' STOPPED ', background_color=COLOR_ERROR, text_color='white')
                window['-UNICODE_LED-'].update(LED_OFF_CHAR, text_color='gray')
                window['-OUTPUT-'].print('--- Auto Fetch Terminated by Server Exit ---')
                
                # Automatically stop the loop
                auto_fetch_running = False
                window['-FETCH_BUTTON-'].update('Start Auto Fetch', disabled=False, button_color=('white', COLOR_SUCCESS))
                window['-STOP_BUTTON-'].update(disabled=True)
                
            except Exception as e:
                error_msg = f"An error occurred on fetch #{fetch_count}: {e}"
                window['-OUTPUT-'].print(f'\n{error_msg}')
                
                window['-STATUS_TEXT-'].update(f' | Server: {HOST}:{PORT} | Status: ERROR')
                window['-STATUS_LIGHT-'].update(' ERROR ', background_color=COLOR_ERROR, text_color='white')
                window['-UNICODE_LED-'].update(LED_OFF_CHAR, text_color='gray')

# Close the window gracefully
window.close()