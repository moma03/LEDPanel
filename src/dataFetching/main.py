"""
this python script, can handle some input parameters to fetch bahn data 
parameters:
    -h, --help: show this help message and exit
    -stationEVA: the station EVA number to fetch data for
    -stationName: the name of the station to fetch data for
    -stationRLI100: the station ID to fetch data for

these station data need to be cached in a file called 'stationData.json', as one need to fetch the information from db api
"""

from Fetcher import Fetcher
from argparse import ArgumentParser

if __name__ == "__main__":
    parser = ArgumentParser(description="Fetch station data from the DB API.")
    parser.add_argument('-stationEVA', type=int, help='The station EVA number to fetch data for.')
    parser.add_argument('-stationName', type=str, help='The name of the station to fetch data for.')
    parser.add_argument('-stationRLI100', type=str, help='The station RLI100/DE100 name to fetch data for.')

    args = parser.parse_args()

    fetcher = Fetcher()
    if args.stationEVA is None:
        if not args.stationName and not args.stationRLI100:
            raise ValueError("Either stationName or stationRLI100 must be provided.")
        s = fetcher.fetch_station_data(args.stationName or args.stationRLI100)
        print(s)
        print(f"Fetched data for station {s['name']} (EVA: {s['eva']})")
        board = fetcher.fetch_station_departures({
            'eva': s['eva'],
            'name': s['name'],
            'lookahead': 20,  # Lookahead in minutes
            'transports': ["HIGH_SPEED_TRAIN","INTERCITY_TRAIN","INTER_REGIONAL_TRAIN","REGIONAL_TRAIN","CITY_TRAIN"],
            'station_category': 1,  # 1 for main stations, 2 for all other,
            'type': 'departures'  # or 'arrivals' depending on the type of data needed
        })
        print(f"Fetched data for station {s['name']} (EVA: {s['eva']})")
        print(f"Departures: {board}")
    else:
        # TODO Check if provided EVA number is valid, by lookup in cached data
        board = fetcher.fetch_station_departures(args.stationEVA)
        print(f"Fetched departures for station with EVA {args.stationEVA}")
