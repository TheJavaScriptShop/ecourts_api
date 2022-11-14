from sys import exc_info
import time
import os
import traceback

from azure.storage.blob import BlobServiceClient
from sentry_sdk import capture_exception


def wait_for_download_and_rename(blob_path, __location__):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(
            os.environ.get('BLOB_STORAGE_CONTAINER'))
        blob_client = blob_service_client.get_blob_client(
            container="ecourtsapiservicebucketdev", blob=blob_path)
        file_exists = True
        trial = 1
        while file_exists:
            time.sleep(int(os.environ.get('MIN_WAIT_TIME')))
            if os.path.isfile(f"{__location__}/display_pdf.pdf"):
                with open(os.path.join(__location__, "display_pdf.pdf"), "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)
                os.remove(f"{__location__}/display_pdf.pdf")
                file_exists = False
                return {"upload": True}
            if trial >= 10:
                return {"upload": False}
            trial = trial + 1

    except Exception as e_exc:
        tb = traceback.TracebackException.from_exception(e_exc)
        capture_exception(e_exc)
        return {'status': False, 'error': str(e_exc), "traceback": ''.join(tb.format()), "debugMessage": "Failed to upload file to blob", "code": 4}
