#!/usr/bin/env python3
import time
import sys
import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime
from PIL import Image
from PIL import ImageDraw
from xml.etree import ElementTree
from PIL import Image, ImageDraw, ImageFont

# This is a dependency from the rpi-rgb-led-matrix library.
# You must have it installed for this script to work.
# Installation instructions: https://github.com/hzeller/rpi-rgb-led-matrix
try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

except ImportError:
    print("Error: The 'rgbmatrix' library is not installed.")
    print("Please follow the installation instructions at:")
    print("https://github.com/hzeller/rpi-rgb-led-matrix")
    sys.exit(1)

debug = False  # Set to True for debugging output

# Read the schema file as a string
with open('db_timetables_schema.json', 'r') as f:
  schema_str = f.read()

# --- CONFIGURATION ---

# 1. Deutsche Bahn API Credentials from .env file
load_dotenv()
DB_CLIENT_ID = os.getenv('DB_CLIENT_ID')
DB_CLIENT_SECRET = os.getenv('DB_CLIENT_SECRET')

# 2. Station Configuration
# HSTM is the short name (DS100), but the API works best with the EVA number.
STATION_DS100 = "HSTM"  # Short name for "Steinheim (Westf)"
STATION_EVA_ID = 8005708 # HSTM=8005708 AH=8002549  
STATION_DISPLAY_NAME = "Steinheim Westf"

if (not STATION_EVA_ID):
  if (STATION_DS100):
    STATION_EVA_ID = request_eva_id(STATION_DS100)
  else:
    print("Error: No EVA ID or DS100 station name provided.")
    sys.exit(1) 


# 3. LED Matrix Configuration
MATRIX_ROWS = 64
MATRIX_COLS = 64

options = RGBMatrixOptions()
options.rows = MATRIX_ROWS
options.cols = MATRIX_COLS
options.brightness = 90  # Brightness level (0-100)
options.chain_length = 1
options.pwm_bits = 3  # PWM bits for brightness control
options.parallel = 1
options.hardware_mapping = 'regular'  # Change if you have a different hardware mapping
options.gpio_slowdown = 2 # Uncomment if you have issues with flickering
options.show_refresh_rate = True  # Show the refresh rate on the matrix

# 4. Display & Data Configuration
FONT_PATH = '5x8.bdf' # Place this font file in the same directory
REFRESH_INTERVAL_SECONDS = 30
MAX_DEPARTURES_TO_SHOW = 5

# --- API HANDLING ---

def get_db_departures(station_id, client_id, client_secret):
    """
    Fetches departure data from the Deutsche Bahn Timetables API.
    """
    if client_id == "YOUR_CLIENT_ID" or client_secret == "YOUR_CLIENT_SECRET" or True:
        # Return mock data if API keys are not set, so the display part can be tested.
        print("Warning: DB API credentials are not set. Using mock data.")
        return [
            {'line': 'S5', 'direction': 'Paderborn Hbf', 'departure_time': '18:05', 'delay_minutes': 0},
            {'line': 'S5', 'direction': 'Hannover Flug', 'departure_time': '18:25', 'delay_minutes': 5},
            {'line': 'S5', 'direction': 'Altenbeken', 'departure_time': '18:40', 'delay_minutes': 0},
            {'line': 'S5', 'direction': 'Paderborn Hbf', 'departure_time': '19:05', 'delay_minutes': 0},
        ]

    # Construct the API URL
    date = datetime.now().strftime('%y%m%d')      # Get today's date in YYMMDD format
    time_now = format_time(datetime.now().strftime('%H:%M'))  # Get current time in HH format

    api_url = f"https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/plan/{station_id}/{date}/{time_now}"
    print(f"Fetching data from: {api_url}")
    headers = {
        "DB-Client-Id": client_id,
        "DB-Api-Key": client_secret,
        "accept": "application/json"
    }

    try:
        response = requests.get(url=api_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        print(f"API response status: {response.status_code}")
        print(response.text)  # Print the raw response for debugging

        # Parse the XML response
        api_data = None
        departures = []

        for item in api_data.get('timetable', {}).get('departures', []):
            dp = item.get('departure', {})
            
            # Extract train line identifier
            line = item.get('train', {}).get('line', item.get('train', {}).get('category', ''))

            # Extract destination
            direction = item.get('station', {}).get('title', 'N/A')

            # Extract and format time
            scheduled_time_str = dp.get('scheduledTime')
            actual_time_str = dp.get('time', scheduled_time_str)

            if not scheduled_time_str:
                continue

            scheduled_dt = datetime.fromisoformat(scheduled_time_str)
            actual_dt = datetime.fromisoformat(actual_time_str)
            
            departure_time_formatted = actual_dt.strftime('%H:%M')
            
            # Calculate delay
            delay_seconds = (actual_dt - scheduled_dt).total_seconds()
            delay_minutes = int(delay_seconds / 60)

            departures.append({
                'line': line,
                'direction': direction,
                'departure_time': departure_time_formatted,
                'delay_minutes': delay_minutes
            })
        
        return departures

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from DB API: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def get_db_departures_iris(station_id):
    options = {
        "datum": "2025-07-05",
        "zeit": "14:42:00",
        "ortExtId": station_id,
        "ortId": station_id,
        "mitVias": "true",
        "maxVias": 8,
        "verkehrsmittel": ["ICE", "EC_IC", "IR", "REGIONAL", "SBAHN"] 
        # ["ICE", "EC_IC", "IR", "REGIONAL", "SBAHN", "BUS", "SCHIFF", "UBAHN", "TRAM", "ANRUFPFLICHTIG"]
    }

    options["datum"] = datetime.now().strftime('%Y-%m-%d')
    options["zeit"] = datetime.now().strftime('%H:%M:%S')


    base_api_url = "https://www.bahn.de/web/api/reiseloesung/abfahrten"
    params = "&".join([f"{key}={value}" for key, value in options.items()])
    api_url = f"{base_api_url}?{params}"
    api_url = f"https://www.bahn.de/web/api/reiseloesung/abfahrten?datum=2025-07-05&zeit=14:42:00&ortExtId=8005708&ortId=8005708&mitVias=true&maxVias=8&verkehrsmittel[]=ICE&verkehrsmittel[]=EC_IC&verkehrsmittel[]=IR&verkehrsmittel[]=REGIONAL&verkehrsmittel[]=SBAHN&verkehrsmittel[]=BUS&verkehrsmittel[]=SCHIFF&verkehrsmittel[]=UBAHN&verkehrsmittel[]=TRAM&verkehrsmittel[]=ANRUFPFLICHTIG"


def get_db_departures_bahnhofde(station_id, station_name, station_category=1, lookahead_minutes=60, transport_types=["HIGH_SPEED_TRAIN", "INTERCITY_TRAIN", "INTER_REGIONAL_TRAIN", "REGIONAL_TRAIN", "CITY_TRAIN"]):
    """
    Fetches departure data from the Deutsche Bahn Bahnhof.de.
    Now it uses a workaround as the official API is not available anymore.
    
    The fetching is based on this curl command:
    curl 'https://www.bahnhof.de/steinheim-westf/abfahrt' \                                                                               
        --compressed \
        -X POST \                                                                                              
        -H 'Accept-Language: de,en-US;q=0.7,en;q=0.3' \                                                                                   
        -H 'Accept-Encoding: gzip, deflate, br, zstd' \                       
        -H 'Referer: https://www.bahnhof.de/steinheim-westf/abfahrt' \                                                                    
        -H 'Next-Action: 1763f424e6ce09c2e07592add424e2c1908b9082' \                                                                                                                                       
        -H 'Content-Type: text/plain;charset=UTF-8' \                           
        --data-raw '[{"duration":60,"type":"departures","locale":"de","evaNumbers":["8005708"],"stationCategory":6,"filterTransports":["HIGH_SPEED_TRAIN","INTERCITY_TRAIN","INTER_REGIONAL_TRAIN","REGIONAL_TRAIN","CITY_TRAIN"],"sortBy":"TIME_SCHEDULE"}]'
    
    As one can see the -- data-raw part is a JSON object that contains the parameters for the request.
    """

    assert type(station_id) == int, "station_id must be an integer."
    assert type(station_name) == str, "station_name must be a string."

    data_raw_options = {
        "evaNumbers": [f"{station_id}", ],    # List of EVA numbers (station IDs)
        "filterTransports": transport_types,  # List of transport types to filter
        "duration": lookahead_minutes,        # Lookahead in minutes
        "stationCategory": station_category,  # category 1 for main stations, 2 for all other stations eg. wiki article
        "locale": "de",
        "sortBy": "TIME_SCHEDULE" 
    }

    # Construct the request URL
    base_api_url = f"https://www.bahnhof.de/{station_name.lower().replace(' ', '-')}/abfahrt"
    headers = {
        "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": f"https://www.bahnhof.de/{station_name.lower().replace(' ', '-')}/abfahrt",
        "Next-Action": "1763f424e6ce09c2e07592add424e2c1908b9082",  # This is a static value, might change in the future, without it the request fails.
        "Content-Type": "text/plain;charset=UTF-8"
    }
    data_raw = json.dumps([data_raw_options])  # Convert the options to a JSON string
    print(f"Fetching data ...")
    print(f"Request URL: {base_api_url}")
    print(f"Request Headers: {headers}")
    print(f"Request Data: {data_raw}")

    try:
        response = requests.post(url=base_api_url, headers=headers, data=data_raw)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        print(f"API response status: {response.status_code}")

        def extract_balanced_json(source: str, start_key: str = '{"globalMessages":[') -> str:
            start_idx = source.find(start_key)
            if start_idx == -1:
                return None  # or raise an exception

            brace_count = 0
            in_string = False
            escape = False

            for i in range(start_idx, len(source)):
                char = source[i]

                if char == '"' and not escape:
                    in_string = not in_string
                elif char == '\\' and not escape:
                    escape = True
                    continue
                elif not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            return source[start_idx:i+1]

                escape = False  # reset escape flag unless it was just set

            return None  # If no matching brace was found
    

        json_str = extract_balanced_json(response.text)

        if debug:
            print(response.text)  # Print the raw response for debugging
            print("----------")
            print(json_str)  # Print the extracted JSON string for debugging
        
        # Parse the JSON response
        api_data = json.loads(json_str) if json_str else {}
        departures = []

        for item in api_data.get('entries', []):
            for train in item:
                # Extract train line identifier
                line = train.get('lineName', '')

                # Extract destination
                direction = train.get('destination', {}).get('name', '')

                # Extract and format time
                scheduled_time_str = train.get('timeSchedule', '')
                actual_time_str = train.get('timeDelayed', '')

                if not scheduled_time_str:
                    continue

                scheduled_dt = datetime.fromisoformat(scheduled_time_str)
                actual_dt = datetime.fromisoformat(actual_time_str)
                
                departure_time_formatted = actual_dt.strftime('%H:%M')
                
                # Calculate delay
                delay_seconds = (actual_dt - scheduled_dt).total_seconds()
                delay_minutes = int(delay_seconds / 60)

                departures.append({
                    'line': str(line).strip().replace('â\x80¯', ''),
                    'direction': direction,
                    'departure_time': departure_time_formatted,
                    'delay_minutes': delay_minutes,
                    'is_cancelled': train.get('canceled', False) or train.get('stopPlace', {}).get('canceled', False)
                })
        print(f"Fetched {len(departures)} departures.")
        print(departures)  # Debugging output
        return departures

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from DB API: {e}")
        return None



def get_db_departures_bahnhof_de_old(station_id):
    options = {
        "evaNumbers": station_id,
        "filterTransports": ["HIGH_SPEED_TRAIN", "INTERCITY_TRAIN", "INTER_REGIONAL_TRAIN", "REGIONAL_TRAIN", "CITY_TRAIN"],
        "duration": 100,       # Lookahead in minutes
        "stationCategory": 1,  # catergory 1 for main stations, 2 for all other stations eg. wiki article
        "locale": "de",
        "sortBy": "TIME_SCHEDULE" 
    }

    # Construct the API URL
    base_api_url = "https://www.bahnhof.de/api/boards/departures"
    params = ""
    for key, value in options.items():
        if isinstance(value, list):
            for item in value:
                params += f"&{key}={item}"
        else:
            params += f"&{key}={value}"
    api_url = f"{base_api_url}?{params}"
    headers = {"accept": "application/json"}
    
    print(f"Fetching data from: {api_url}")
    

    try:
        response = requests.get(url=api_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        print(f"API response status: {response.status_code}")
        # Parse the JSON response
        api_data = response.json()
        departures = []

        for item in api_data.get('entries', []):
            for train in item:
                # Extract train line identifier
                line = train.get('lineName', '')

                # Extract destination
                direction = train.get('destination', {}).get('name', '')

                # Extract and format time
                scheduled_time_str = train.get('timeSchedule', '')
                actual_time_str = train.get('timeDelayed', '')

                if not scheduled_time_str:
                    continue

                scheduled_dt = datetime.fromisoformat(scheduled_time_str)
                actual_dt = datetime.fromisoformat(actual_time_str)
                
                departure_time_formatted = actual_dt.strftime('%H:%M')
                
                # Calculate delay
                delay_seconds = (actual_dt - scheduled_dt).total_seconds()
                delay_minutes = int(delay_seconds / 60)

                departures.append({
                    'line': str(line).strip().replace('\u202f', ''),
                    'direction': direction,
                    'departure_time': departure_time_formatted,
                    'delay_minutes': delay_minutes,
                    'is_cancelled': train.get('canceled', False) or train.get('stopPlace', {}).get('canceled', False)
                })
        print(f"Fetched {len(departures)} departures.")
        print(departures)  # Debugging output
        return departures
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from DB API: {e}")
        return None


# --- DISPLAY LOGIC ---

def draw_to_matrix(matrix, departures_data):
    """
    Draws the departure information onto the LED matrix.
    """
    offscreen_canvas = matrix.CreateFrameCanvas()

    try:
        font = graphics.Font()
        font.LoadFont(FONT_PATH)
    except IOError as e:
        print(e)
        print(f"Error: Could not load font file '{FONT_PATH}'.")
        print("Please ensure the font file is in the same directory as the script.")
        # Draw error message on the matrix itself
        draw.text((2, 2), "FONT", fill="red")
        draw.text((2, 12), "ERR", fill="red")
        matrix.SetImage(image)
        return

    # Blue DB like background
    offscreen_canvas.Fill(0, 0, 140)

    # --- Colors ---
    white  = graphics.Color(255, 255, 255)
    gray   = graphics.Color(128, 128, 128)
    green  = graphics.Color(0,   255, 0)
    red    = graphics.Color(255,   0, 0)
    yellow = graphics.Color(255, 255, 0)

    # --- Draw Header ---
    graphics.DrawLine(offscreen_canvas, 0, 8, MATRIX_COLS, 8, gray)
    graphics.DrawText(offscreen_canvas, font, 1, 7, white, f"{STATION_DISPLAY_NAME}")
    
    # --- Handle No Data ---
    if departures_data is None:
        graphics.DrawText(offscreen_canvas, font, 2, 20, red, "API Error")
        graphics.DrawText(offscreen_canvas, font, 2, 30, red, "Check Conn.")
        matrix.SwapOnVSync(offscreen_canvas)
        return

    if not departures_data:
        graphics.DrawText(offscreen_canvas, font, 2, 20, yellow, "Keine Abf.")
        matrix.SwapOnVSync(offscreen_canvas)
        return

    # --- Draw Departures ---
    y_pos = 16
    for i, dep in enumerate(departures_data[:MAX_DEPARTURES_TO_SHOW]):
        line = dep['line']
        direction = dep['direction']
        dep_time = dep['departure_time']
        delay = dep['delay_minutes']
        is_cancelled = dep['is_cancelled']

        # Line Number (e.g., S5)
        len = graphics.DrawText(offscreen_canvas, font, 1, y_pos, yellow, f"{line:<4}")
        
        # Destination (truncated to fit)
        if (is_cancelled):
            graphics.DrawText(offscreen_canvas, font, 15, y_pos, red, f"x {direction[:10]:<10}")

            # Draw cancellation notice
            graphics.DrawText(offscreen_canvas, font, 1, y_pos + 8, red, "Zug entfällt")

        else:
            graphics.DrawText(offscreen_canvas, font, 15, y_pos, white, f"{direction[:10]:<10}")
        
            # Departure Time
            time_color = green if delay <= 0 else red
            graphics.DrawText(offscreen_canvas, font, 1, y_pos + 8, time_color, dep_time)
        
            # Delay
            if delay > 0:
                graphics.DrawText(offscreen_canvas, font, 30, y_pos + 8, red, f"+{delay} min")

        y_pos += 18 # Move to the next line
        if y_pos > MATRIX_ROWS - 10:
            break

    # Send the finished image to the matrix
    matrix.SwapOnVSync(offscreen_canvas)

class TextBox:
    '''
    A simple text box, that starts scrolling if the text is too long.
    '''

    def __init__(self, matrix, text, font, x=0, y=0, width=None, height=None):
        self.matrix = matrix
        self.text = text
        self.font = font
        self.x = x
        self.y = y
        self.width = width if width else matrix.width
        self.height = height if height else matrix.height
        self.scroll_pos = 0

    def draw(self):
        """
        Draws the text box on the matrix, scrolling if necessary.
        """
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        offscreen_canvas.Clear()

        # Draw the text
        text_width, text_height = graphics.DrawText(offscreen_canvas, self.font, self.x - self.scroll_pos, self.y, graphics.Color(255, 255, 255), self.text)

        # If the text is wider than the box, start scrolling
        if text_width > self.width:
            self.scroll_pos += 1
            if self.scroll_pos > text_width:
                self.scroll_pos = 0

        # Swap the canvas to display it
        self.matrix.SwapOnVSync(offscreen_canvas)



def format_time(time):
    """
    Formats a time string from 'HH:MM' or 'HH:MM:SS' to 'HH'.
    """
    if len(time) < 5:
        raise ValueError("Time must be in 'HH:MM' or 'HH:MM:SS' format.")
    return time[:2]  # Return only the hour part


# --- MAIN EXECUTION ---

def main():
    """
    Main loop to fetch data and update the display.
    """
    print("Starting Deutsche Bahn Matrix Display...")
    print("Press CTRL-C to stop.")

    # Initialize the matrix
    matrix = RGBMatrix(options=options)
    
    i = 0
    try:
        while i < 150:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching new departure data...")
            departures = get_db_departures_bahnhofde(STATION_EVA_ID, STATION_DISPLAY_NAME, station_category=6, lookahead_minutes=100)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Drawing to matrix...")
            draw_to_matrix(matrix, departures)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for {REFRESH_INTERVAL_SECONDS} seconds...")
            time.sleep(REFRESH_INTERVAL_SECONDS)
            i += 1

    except KeyboardInterrupt:
        print("\nExiting. Clearing matrix...")
        matrix.Clear()
        sys.exit(0)
    except Exception as e:
        print(f"An unhandled error occurred in main loop: {e}")
        matrix.Clear()
        sys.exit(1)

if __name__ == "__main__":
    main()
