#!/usr/bin/env python3
import os
import requests
import xml.etree.ElementTree as ET
import json
from dotenv import load_dotenv

class Fetcher:
    def __init__(self):
        env_path = os.path.expanduser('~/LEDMatrix/.env')
        load_dotenv(dotenv_path=env_path)
        self.TIMETABLE_CLIENT_ID     = os.getenv('DB_CLIENT_ID')
        self.TIMETABLE_CLIENT_SECRET = os.getenv('DB_CLIENT_SECRET')

        if not self.TIMETABLE_CLIENT_ID or not self.TIMETABLE_CLIENT_SECRET:
            raise EnvironmentError("DB_CLIENT_ID and DB_CLIENT_SECRET environment variables must be set.")


    def fetch_station_data(self, station_info: str or int):
        """
        Fetches station data from the DB API using the provided station information.
        :param station_info: string containing station information (EVA number, name, or ID).
        :raises ValueError: if station_info is not provided.
        :raises requests.HTTPError: if the request to the DB API fails.
        :return: JSON response from the DB API.
        """

        assert type(station_info) in [str, int], "station_info must be a string or an integer."
        assert station_info, "Station information must be provided."

        url = f"https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1/station/{station_info}"
        headers = {
            'DB-Client-Id': self.TIMETABLE_CLIENT_ID,
            'DB-Api-Key': self.TIMETABLE_CLIENT_SECRET,
            #'accept': 'application/json'
            'accept': 'application/vnd.de.db.ris+json'
        }
        
        response = None
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an error for bad responses
        except requests.HTTPError as http_err:
            raise requests.HTTPError(f"HTTP error occurred: {http_err}")
        except Exception as err:
            raise Exception(f"An error occurred: {err}")

        return Fetcher.parse_station_data(response.text)

    
    def fetch_station_departures(self, request_data):
        """
        Fetches departures from bahnhof.de API using its EVA number.
        :param station_eva: EVA number of the station.
        :raises ValueError: if station_eva is not provided.
        :raises requests.HTTPError: if the request to the DB API fails.
        :return: JSON response from the DB API containing departure information.
        """
        
        if not request_data:
            raise ValueError("Request data must be provided.")

        data_raw_options = {
            "evaNumbers": [f"{request_data['eva']}", ],          # List of EVA numbers (station IDs)
            "filterTransports": request_data["transports"],      # List of transport types to filter
            "duration": request_data["lookahead"],               # Lookahead in minutes
            "stationCategory": request_data["station_category"], # category 1 for main stations, 2 for all other stations eg. wiki article
            "locale": "de",
            "type": request_data["type"],                        # 'departures' or 'arrivals'
            "sortBy": "TIME_SCHEDULE" 
        }

        # Construct the URL for the API request
        base_api_url = f"https://www.bahnhof.de/{request_data['name'].lower().replace(' ', '-')}"
        headers = {
            "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": f"https://www.bahnhof.de/{request_data['name'].lower().replace(' ', '-')}",
            "Next-Action": "1763f424e6ce09c2e07592add424e2c1908b9082",  # This is a static value, might change in the future, without it the request fails.
            "Content-Type": "text/plain;charset=UTF-8"
        }
        body = json.dumps([data_raw_options])
        
        try:
            response = requests.post(base_api_url, headers=headers, data=body)
            response.raise_for_status()  # Raise an error for bad responses
            
            # Extract the balanced JSON from the response text
            json_str = Fetcher.extract_balanced_json(source = response.text, start_key='{"globalMessages":[')
            return json.loads(json_str) if json_str else None
        except requests.HTTPError as http_err:
            raise requests.HTTPError(f"HTTP error occurred: {http_err}")
        except Exception as err:
            raise Exception(f"An error occurred: {err}")
        
        
    def extract_balanced_json(source: str, start_key: str) -> str:
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


    def parse_station_data(response_text: str):
        """
        Parses the station data XML from the response text.
        :param response_text: The raw response text from the DB API.
        :return: A dictionary containing the parsed station data.
        """

        print(response_text)  # Debugging line to see the raw response

        try:
            root = ET.fromstring(response_text)
            station_data = []
            for station in root.findall('station'):
                station_data.append({
                    'name': station.get('name'),
                    'eva': station.get('eva'),
                    'ds100': station.get('ds100'),
                    'creation_ts': station.get('creationts'),
                    'platforms': station.get('p').split('|') if station.get('p') else []
                })
            return station_data[0]
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse station data: {e}")