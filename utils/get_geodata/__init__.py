"""Utility to get geodata from the Chilean Ministry of Environment API, using the requests library.
"""
import requests
from json import loads, dumps
from pathlib import Path
from time import sleep

PATH_TO_SAVE_DATA = path = (Path(__file__).parent.parent/"data").joinpath("geodata.json")
PAGINATION_LIMIT = 100
BASE_URL = "https://arcgis.mma.gob.cl/server/rest/services/IDE/Cartografia_Base/FeatureServer/1/query"
URL = BASE_URL + "?where=1%3D1&outFields=*&f=json&resultOffset={start_from}&resultRecordCount={page_limit}"

data = []

def _get_geodata(url: str = URL, start_from: int = 0, page_limit: int = PAGINATION_LIMIT) -> dict:
    """Get geodata from the Chilean Ministry of Environment API.

    Args:
        url (str): The URL to the API endpoint.

        start_from (int): The starting index for the data.

        page_limit (int): The number of records to retrieve per request.

    Returns:
        dict: The geodata from the API
    """
    response = requests.get(url.format(start_from=start_from, page_limit=page_limit))
    data = response.content.decode("utf-8")
    return loads(data)

def django_serializer(data: dict, model: str, pk: str) -> dict:
    """Convert the data to a list of dictionaries that can be used with Django's serializers.
    
    Args:
        data (dict): The data to convert.
        
    Returns:
        list: The data as a list of dictionaries.
    """
    return {"pk": data.get(pk), "model": model, "fields": data}

def get_all_geodata(url: str = URL, start_from: int = 0, page_limit: int = PAGINATION_LIMIT) -> list:
    """Get all geodata from the Chilean Ministry of Environment API.
    
    Args:
        url (str): The URL to the API endpoint.

        start_from (int): The starting index for the data.

        page_limit (int): The number of records to retrieve per request.
        
    Returns:
        dict: The geodata from the API
    """
    data = []
    while True:
        print(f"Getting geodata from {start_from} to {start_from + page_limit}")
        response = _get_geodata(url, start_from, page_limit)
        # Save the features from the response to the data list
        features = response.get("features", [])
        attributes = [feature.get("attributes") for feature in features]
        # Filter out the None values
        attributes = [attr for attr in attributes if attr]
        # Lower key names
        attributes = [{k.lower(): v for k, v in attr.items()} for attr in attributes]
        data.extend(attributes)
        start_from += page_limit
        # Throttle the requests to avoid exceeding API limits
        sleep(1)
        # Until the response has the exceededTransferLimit key set to False, the loop will continue
        if not response.get("exceededTransferLimit"):
            break
    data = [django_serializer(d, "consultorio.consultorio", "objectid") for d in data]
    return data

data = get_all_geodata()
# Save the data to a JSON file (note that the encoding is set to utf-8 and ensure_ascii is set to False in order to have accented characters... thanks Chilean Spanish!)
PATH_TO_SAVE_DATA.write_text(
    dumps(
        data, 
        indent=4, 
        ensure_ascii=False
    ),
    encoding="utf-8"
)