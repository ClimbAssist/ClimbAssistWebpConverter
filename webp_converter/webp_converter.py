import json
import logging
import os
import subprocess

import boto3
from botocore.exceptions import ClientError

INPUT_FILE_PATH = "/tmp/input.jpg"
OUTPUT_FILE_PATH = "/tmp/output.webp"


def convert_to_webp(event, context):  # TODO do we need context at all?
    logging.info(f"Received event: {event}")
    source_location = event["sourceLocation"]
    destination_location = event["destinationLocation"]

    s3 = boto3.client("s3")
    with open(INPUT_FILE_PATH, "wb") as file:
        try:
            s3.download_fileobj(source_location["bucket"], source_location["key"], file)
        except ClientError as e:
            error_message = f"Unable to download source file: {e}"
            logging.error(error_message)
            return build_return_object(400, error_message)

    process = subprocess.Popen(
        ["./lib/libwebp-1.1.0-linux-x86-64/bin/cwebp", "/tmp/input.jpg", "-o", "/tmp/output.webp"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.path.dirname(os.path.realpath(__file__)))
    process.wait()
    stdout = process.communicate()[1].decode()  # [1] gets stdout
    return_code = process.returncode

    logging.info(f"Return code: %s")
    logging.info(stdout)

    os.remove(INPUT_FILE_PATH)

    if return_code == 0:
        with (open(OUTPUT_FILE_PATH, "rb")) as file:
            try:
                s3.upload_fileobj(file, destination_location["bucket"], destination_location["key"])
            except ClientError as e:
                error_message = f"Unable to upload file to destination: {e}"
                logging.error(error_message)
                os.remove(OUTPUT_FILE_PATH)
                return build_return_object(400, error_message)
        os.remove(OUTPUT_FILE_PATH)
        message = "Successfully converted file."
        logging.info(message)
        return build_return_object(200, message)
    else:
        logging.warning("Failure converting file.")
        message = stdout
        return build_return_object(400, message)


def build_return_object(status_code, message):
    return {
        "statusCode": status_code,
        "body": json.dumps({
            "message": message,
        }),
    }
