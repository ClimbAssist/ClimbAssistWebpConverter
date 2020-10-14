import json
import os
import shutil
from unittest.mock import mock_open, Mock, patch

from botocore.exceptions import ClientError

from webp_converter import webp_converter

INPUT_IMAGE_PATH = "/tmp/input.jpg"
OUTPUT_IMAGE_PATH = "/tmp/output.webp"
EVENT = {
    "sourceLocation": {
        "bucket": "source-bucket",
        "key": "source-key"
    },
    "destinationLocation": {
        "bucket": "destination-bucket",
        "key": "destination-key"
    }
}


def assert_not_called_with(self, *args, **kwargs):
    try:
        self.assert_called_with(*args, **kwargs)
    except AssertionError:
        return
    raise AssertionError("Expected %s to not have been called." % self._format_mock_call_signature(args, kwargs))


Mock.assert_not_called_with = assert_not_called_with


@patch("webp_converter.webp_converter.boto3.client")
@patch("webp_converter.webp_converter.open", new_callable=mock_open)
def test_lambda_handler_success(mock_open_, mock_s3):
    shutil.copyfile("tests/fixtures/image.jpg", INPUT_IMAGE_PATH)

    result = webp_converter.convert_to_webp(EVENT)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["message"] == "Successfully converted file."

    mock_open_.assert_any_call(INPUT_IMAGE_PATH, "wb")
    mock_s3.return_value.download_fileobj.assert_called_with(EVENT["sourceLocation"]["bucket"],
                                                             EVENT["sourceLocation"]["key"], mock_open_.return_value)
    mock_open_.assert_any_call(OUTPUT_IMAGE_PATH, "rb")
    mock_s3.return_value.upload_fileobj.assert_called_with(mock_open_.return_value,
                                                           EVENT["destinationLocation"]["bucket"],
                                                           EVENT["destinationLocation"]["key"])

    assert not os.path.exists(INPUT_IMAGE_PATH)
    assert not os.path.exists(OUTPUT_IMAGE_PATH)


@patch("webp_converter.webp_converter.boto3.client")
@patch("webp_converter.webp_converter.open", new_callable=mock_open)
def test_lambda_handler_not_jpg(mock_open_, mock_s3):
    shutil.copyfile("tests/fixtures/not-an-image.txt", INPUT_IMAGE_PATH)

    result = webp_converter.convert_to_webp(EVENT)

    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert body["message"] == "Error! Could not process file /tmp/input.jpg\nError! Cannot read input picture file " \
                              "'/tmp/input.jpg'\n"

    mock_open_.assert_any_call(INPUT_IMAGE_PATH, "wb")
    mock_s3.return_value.download_fileobj.assert_called_with(EVENT["sourceLocation"]["bucket"],
                                                             EVENT["sourceLocation"]["key"], mock_open_.return_value)

    mock_open_.assert_not_called_with(OUTPUT_IMAGE_PATH, "rb")
    mock_s3.return_value.upload_fileobj.assert_not_called()

    assert not os.path.exists(INPUT_IMAGE_PATH)
    assert not os.path.exists(OUTPUT_IMAGE_PATH)


@patch("webp_converter.webp_converter.boto3.client")
@patch("webp_converter.webp_converter.open", new_callable=mock_open)
def test_lambda_handler_source_download_client_error(mock_open_, mock_s3):
    s3_client_error = ClientError({
        "Error": {
            "Code": 400,
            "Message": "S3 woes"
        }
    }, "GetObject")
    mock_s3.return_value.download_fileobj.side_effect = s3_client_error

    result = webp_converter.convert_to_webp(EVENT)

    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert body["message"] == f"Unable to download source file: {s3_client_error}"

    mock_open_.assert_any_call(INPUT_IMAGE_PATH, "wb")
    mock_s3.return_value.download_fileobj.assert_called_with(EVENT["sourceLocation"]["bucket"],
                                                             EVENT["sourceLocation"]["key"], mock_open_.return_value)

    mock_open_.assert_not_called_with(OUTPUT_IMAGE_PATH, "rb")
    mock_s3.return_value.upload_fileobj.assert_not_called()

    assert not os.path.exists(INPUT_IMAGE_PATH)
    assert not os.path.exists(OUTPUT_IMAGE_PATH)


@patch("webp_converter.webp_converter.boto3.client")
@patch("webp_converter.webp_converter.open", new_callable=mock_open)
def test_lambda_handler_source_upload_client_error(mock_open_, mock_s3):
    shutil.copyfile("tests/fixtures/image.jpg", INPUT_IMAGE_PATH)

    s3_client_error = ClientError({
        "Error": {
            "Code": 400,
            "Message": "S3 woes"
        }
    }, "PutObject")
    mock_s3.return_value.upload_fileobj.side_effect = s3_client_error

    result = webp_converter.convert_to_webp(EVENT)

    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert body["message"] == f"Unable to upload file to destination: {s3_client_error}"

    mock_open_.assert_any_call(INPUT_IMAGE_PATH, "wb")
    mock_s3.return_value.download_fileobj.assert_called_with(EVENT["sourceLocation"]["bucket"],
                                                             EVENT["sourceLocation"]["key"], mock_open_.return_value)

    mock_open_.assert_any_call(OUTPUT_IMAGE_PATH, "rb")
    mock_s3.return_value.upload_fileobj.assert_called_with(mock_open_.return_value,
                                                           EVENT["destinationLocation"]["bucket"],
                                                           EVENT["destinationLocation"]["key"])

    assert not os.path.exists(INPUT_IMAGE_PATH)
    assert not os.path.exists(OUTPUT_IMAGE_PATH)
