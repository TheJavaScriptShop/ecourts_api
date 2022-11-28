from sys import exc_info
import time
import os
import traceback

from azure.storage.blob import BlobServiceClient
from sentry_sdk import capture_exception, capture_message
from dotenv import load_dotenv


if os.environ.get("APP_ENV") == "local":
    load_dotenv()


def wait_for_download_and_rename(blob_path, __location__, file_name, case_no):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(
            os.environ.get('BLOB_STORAGE_CONTAINER'))
        blob_client = blob_service_client.get_blob_client(
            container="ecourtsapiservicebucketdev", blob=blob_path)
        file_exists = True
        trial = 1
        while file_exists:
            time.sleep(int(os.environ.get('MIN_WAIT_TIME')))
            if os.path.isfile(f"{__location__}/{file_name}"):
                with open(os.path.join(__location__, file_name), "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)
                os.remove(f"{__location__}/{file_name}")
                file_exists = False
                return {"upload": True}
            if trial >= 10:
                return {"upload": False}
            trial = trial + 1

    except Exception as e_exc:
        tb = traceback.TracebackException.from_exception(e_exc)
        capture_message("Message: Failed upload file to blob storage" + "\n" + "traceback: " + ''.join(
            tb.format()) + "\n" + "case_no: " + case_no)
        return {'upload': False}
