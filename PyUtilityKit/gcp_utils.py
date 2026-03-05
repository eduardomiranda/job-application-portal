import os
from google.cloud import storage
from google.oauth2 import service_account
from PIL import Image 
import json


def get_storage_client():
    """
    Instantiates and returns a Google Cloud Storage client.
    """
    os.environ['GOOGLE_APPLICATION_CREDENTIALS']= 'paineis-administrativos-14efee966792.json'

    return storage.Client()



def upload_file_to_gcp_bucket(service_account_json_string, bucket_name, local_file, bucket_file_name):
    """
    Uploads a file to a specified Google Cloud Storage bucket.
    
    :param bucket_name: Name of the GCP bucket
    :param local_file: Local file object to upload
    :param bucket_file_name: The name the file will have in the bucket
    """

    try:
        # storage_client = get_storage_client()

        service_account_info = json.loads(service_account_json_string)
        credentials = service_account.Credentials.from_service_account_info(service_account_info)
        storage_client = storage.Client(credentials=credentials)

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(bucket_file_name)
        blob.upload_from_file(local_file) # Use upload_from_file to handle the file-like object directly
        print(f"File {local_file} uploaded to {bucket_name}/{bucket_file_name}.")
    except Exception as ex:
        print(f"An error occurred: {ex}")



def remove_file_from_gcp_bucket(bucket_name, bucket_file_name):
    """
    Removes a specified file from a Google Cloud Storage bucket.

    :param bucket_name: Name of the GCP bucket
    :param bucket_file_name: The name of the file in the bucket to be removed
    """
    try:
        storage_client = get_storage_client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(bucket_file_name)
        blob.delete()
        print(f"File {bucket_file_name} removed from the bucket {bucket_name}.")
    except Exception as ex:
        print(f"An error occurred: {ex}")


# https://storage.cloud.google.com                    /reembolsos/ /LsulhWrvYJIDZXbVxbE999NYRvBLkAOW.jpg
# https://storage.googleapis.com/download/storage/v1/b/reembolsos/o/LsulhWrvYJIDZXbVxbE999NYRvBLkAOW.jpg?alt=media: automatiza@paineis-administrativos.iam.gserviceaccount.com does not have storage.objects.get access to the Google Cloud Storage object. Permission &#39;storage.objects.get&#39; denied on resource (or it may not exist).: ('Request failed with status code', 403, 'Expected one of', <HTTPStatus.OK: 200>, <HTTPStatus.PARTIAL_CONTENT: 206>)



def download_file_from_gcp_bucket(bucket_name, bucket_file_name, download_path):
    """Write and read a blob from GCS using file-like IO"""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The ID of your new GCS object
    # blob_name = "storage-object-name"

    try:
        storage_client = get_storage_client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(bucket_file_name)
        blob.download_to_filename(download_path)

    except Exception as ex:
        print(f"An error occurred: {ex}")



# Example usage
if __name__ == "__main__":


    bucket_name = 'reembolsos'
    bucket_file_name = 'LsulhWrvYJIDZXbVxbE999NYRvBLkAOW.jpg'
    download_path = 'LsulhWrvYJIDZXbVxbE999NYRvBLkAOW.jpg'
    download_file_from_gcp_bucket(bucket_name, bucket_file_name, download_path)

