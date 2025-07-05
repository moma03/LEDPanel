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
STATION_EVA_ID = "8005708"  # EVA Number for "Steinheim (Westf)"
STATION_DISPLAY_NAME = "Steinheim"

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
REFRESH_INTERVAL_SECONDS = 20 # Refresh data every 60 seconds
MAX_DEPARTURES_TO_SHOW = 5 # How many departures to show on the 64x64 screen

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
    date = '250703'
    time_now = '08'
    #TODO get date and time in the correct format
    # date format: YYMMDD (e.g., 250703 for 03.07.2025)
    # time format: HH (e.g., 08 for 08:00)

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

        # Parse the XML response
        api_data = schema.to_dict(response.content)
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
    graphics.DrawText(offscreen_canvas, font, 1, 7, white, f"{STATION_DISPLAY_NAME} Abf.")
    
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

        # Line Number (e.g., S5)
        len = graphics.DrawText(offscreen_canvas, font, 1, y_pos, yellow, f"{line:<4}")
        
        # Destination (truncated to fit)
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


# --- MAIN EXECUTION ---

def main():
    """
    Main loop to fetch data and update the display.
    """
    print("Starting Deutsche Bahn Matrix Display...")
    print("Press CTRL-C to stop.")

    # Initialize the matrix
    matrix = RGBMatrix(options=options)
    
    try:
        while True:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching new departure data...")
            departures = get_db_departures(STATION_EVA_ID, DB_CLIENT_ID, DB_CLIENT_SECRET)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Drawing to matrix...")
            draw_to_matrix(matrix, departures)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for {REFRESH_INTERVAL_SECONDS} seconds...")
            time.sleep(REFRESH_INTERVAL_SECONDS)

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
