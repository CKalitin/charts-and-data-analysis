import os
import requests
import urllib.parse
import time
from pathlib import Path

# https://nsrdb.nlr.gov/data-viewer

env_path = Path(__file__).with_name(".env")
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

API_KEY = os.getenv("NLR_API_KEY")
EMAIL = "christopher.kalitin@gmail.com"
# Synchronous CSV endpoint: returns the data directly in the response body
# (only supported for single-point requests) instead of emailing a download link.
BASE_URL = "https://developer.nlr.gov/api/nsrdb/v2/solar/nsrdb-GOES-full-disc-v4-0-0-download.csv?"
POINTS = [
'836224'
]
OUTPUT_DIR = Path(__file__).with_name("nsrdb_data")

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    for name in ['2024','2023','2022','2020','2021']:
        print(f"Processing name: {name}")
        for id, location_ids in enumerate(POINTS):
            input_data = {
                'attributes': 'clearsky_dhi,clearsky_dni,clearsky_ghi,cloud_fill_flag,dhi,dni,ghi,relative_humidity,surface_albedo,solar_zenith_angle,fill_flag,air_temperature',
                'interval': '10',
                'api_key': API_KEY,
                'email': EMAIL,
                'names': [name],
                'location_ids': location_ids,
            }
            print(f'Making request for point group {id + 1} of {len(POINTS)}...')

            url = BASE_URL + urllib.parse.urlencode(input_data, True)
            response = requests.get(url)
            if response.status_code != 200:
                print(f"An error has occurred ({response.status_code} {response.reason}): {response.text}")
                exit(1)

            out_path = OUTPUT_DIR / f"nsrdb_{location_ids}_{name}.csv"
            out_path.write_bytes(response.content)
            print(f"Saved {out_path} ({len(response.content)} bytes)")

            # Delay to prevent rate limiting
            time.sleep(1)
            print(f'Processed')


def get_response_json_and_handle_errors(response: requests.Response) -> dict:
    """Takes the given response and handles any errors, along with providing
    the resulting json

    Parameters
    ----------
    response : requests.Response
        The response object

    Returns
    -------
    dict
        The resulting json
    """
    if response.status_code != 200:
        print(f"An error has occurred with the server or the request. The request response code/status: {response.status_code} {response.reason}")
        print(f"The response body: {response.text}")
        exit(1)

    try:
        response_json = response.json()
    except:
        print(f"The response couldn't be parsed as JSON, likely an issue with the server, here is the text: {response.text}")
        exit(1)

    if len(response_json['errors']) > 0:
        errors = '\n'.join(response_json['errors'])
        print(f"The request errored out, here are the errors: {errors}")
        exit(1)
    return response_json

if __name__ == "__main__":
    main()