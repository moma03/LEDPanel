"""
this python script, can handle some input parameters to fetch bahn data 
parameters:
    -h, --help: show this help message and exit
    -stationEVA: the station EVA number to fetch data for
    -stationName: the name of the station to fetch data for
    -stationRL100: the station ID to fetch data for

these station data need to be cached in a file called 'stationData.json', as one need to fetch the information from db api
"""

from Fetcher import Fetcher, StationDataCacher
from argparse import ArgumentParser
debug = False

if __name__ == "__main__":
    debug = True
    parser = ArgumentParser(description="Fetch station data from the DB API.")
    parser.add_argument('-stationEVA', type=int, help='The station EVA number to fetch data for.')
    parser.add_argument('-stationName', type=str, help='The name of the station to fetch data for.')
    parser.add_argument('-stationRL100', type=str, help='The station RLI100/DE100 name to fetch data for.')

    args = parser.parse_args()

    fetcher = Fetcher()
    if not args.stationName and not args.stationRL100 and not args.stationEVA:
        raise ValueError("Either stationName or stationRL100 must be provided.")
    
    #Check if station data is cached
    stationData = StationDataCacher.lookup_station_in_cache(station_eva=args.stationEVA, station_name=args.stationName, station_rl100=args.stationRL100)
    if not stationData:
        stationData = fetcher.fetch_station_data(args.stationName or args.stationRL100 or args.stationEVA)
        StationDataCacher.cache_station_data(stationData)
    
    print(f"Fetched data for station {stationData.name} (EVA: {stationData.eva})")
    #board = fetcher.fetch_station_departures({
    #    'eva': stationData.eva,
    #    'name': stationData.name,
    #    'lookahead': stationData.lookahead,  # Lookahead in minutes
    #    'transports': ["HIGH_SPEED_TRAIN","INTERCITY_TRAIN","INTER_REGIONAL_TRAIN","REGIONAL_TRAIN","CITY_TRAIN"],
    #    'station_category': stationData.category,  # 1 for main stations, 2 for all other,
    #    'type': 'departures'  # or 'arrivals' depending on the type of data needed
    #})
    #print(f"Departures: {board}")
