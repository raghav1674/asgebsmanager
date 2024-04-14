import requests
import time


# Function to retrieve IMDS token with retry
def get_imds_token():
    retries = 3
    delay = 2
    for attempt in range(retries):
        try:
            url = "http://169.254.169.254/latest/api/token"
            headers = {
                "X-aws-ec2-metadata-token-ttl-seconds": "21600"
            }
            response = requests.put(url, headers=headers)
            if response.status_code == 200:
                return response.text
            else:
                raise Exception("Failed to retrieve IMDS token")
        except Exception as e:
            print(f"Error: {e}. Retrying ({attempt + 1}/{retries}) in {delay} seconds...")
            time.sleep(delay)

    raise Exception("Max retries exceeded for retrieving IMDS token")

# Function to retrieve instance metadata with retry
def get_instance_metadata(token,metadata_key):
    retries = 3
    delay = 2
    for attempt in range(retries):
        try:
            url = f"http://169.254.169.254/latest/meta-data/{metadata_key}"
            headers = {
                "X-aws-ec2-metadata-token": token
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                metadata = response.text
                return metadata
            else:
                raise Exception("Failed to retrieve instance metadata")
        except Exception as e:
            print(f"Error: {e}. Retrying ({attempt + 1}/{retries}) in {delay} seconds...")
            time.sleep(delay)

    raise Exception("Max retries exceeded for retrieving instance metadata")

