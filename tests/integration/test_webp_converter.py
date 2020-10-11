import json
import random
import string

import boto3
import pytest
# TODO PERMISSIONS!!!!!!!
from botocore.exceptions import ClientError

s3 = boto3.client("s3")
aws_lambda = boto3.client("lambda")


@pytest.fixture(autouse=True)
def fixture(bucket, function_name):
    pytest.test_id = generate_test_id()
    pytest.function_name = function_name
    pytest.source_bucket = bucket
    pytest.source_key = f"{pytest.test_id}/{pytest.test_id}.jpg"
    pytest.destination_bucket = bucket
    pytest.destination_key = f"{pytest.test_id}/{pytest.test_id}.webp"

    yield

    delete_object_silently(pytest.source_bucket, pytest.source_key)
    delete_object_silently(pytest.destination_bucket, pytest.destination_key)


def test_webp_converter_success():
    s3.upload_file("tests/fixtures/image.jpg", pytest.source_bucket, pytest.source_key)

    result = invoke_function(build_event())

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["message"] == "Successfully converted file."
    assert_file_equals_s3_object("tests/fixtures/image.webp", pytest.destination_bucket, pytest.destination_key)
    # making sure the original file wasn't modified
    assert_file_equals_s3_object("tests/fixtures/image.jpg", pytest.source_bucket, pytest.source_key)


def test_webp_converter_source_file_does_not_exist():
    pytest.source_key = "does-not-exist.jpg"
    result = invoke_function(build_event())

    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert body["message"] == \
           "Unable to download source file: An error occurred (404) when calling the HeadObject operation: Not Found"

    assert_s3_object_does_not_exist(pytest.destination_bucket, pytest.destination_key)


def test_webp_converter_source_file_is_not_jpg():
    s3.upload_file("tests/fixtures/not-an-image.txt", pytest.source_bucket, pytest.source_key)
    result = invoke_function(build_event())

    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert body["message"] == \
           "Error! Could not process file /tmp/input.jpg\nError! Cannot read input picture file '/tmp/input.jpg'\n"

    assert_s3_object_does_not_exist(pytest.source_bucket, pytest.destination_key)
    # making sure the original file wasn't modified
    assert_file_equals_s3_object("tests/fixtures/not-an-image.txt", pytest.source_bucket, pytest.source_key)


def test_webp_converter_destination_bucket_does_not_exist():
    s3.upload_file("tests/fixtures/image.jpg", pytest.source_bucket, pytest.source_key)
    pytest.destination_bucket = "definitely-does-not-exist"
    result = invoke_function(build_event())

    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert body["message"] == ("Unable to upload file to destination: An error occurred (NoSuchBucket) when calling "
                               "the PutObject operation: The specified bucket does not exist")

    assert_s3_object_does_not_exist(pytest.source_bucket, pytest.destination_key)
    # making sure the original file wasn't modified
    assert_file_equals_s3_object("tests/fixtures/image.jpg", pytest.source_bucket, pytest.source_key)


def generate_test_id():
    return f"integ-{''.join((random.choice(string.ascii_lowercase + string.digits) for i in range(10)))}"


def assert_file_equals_s3_object(file_path, bucket, key):
    expected_jpg_image = open(file_path, "rb").read()
    actual_jpg_image = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    assert expected_jpg_image == actual_jpg_image


def build_event():
    return {
        "sourceLocation": {
            "bucket": pytest.source_bucket,
            "key": pytest.source_key
        },
        "destinationLocation": {
            "bucket": pytest.destination_bucket,
            "key": pytest.destination_key
        }
    }


def invoke_function(event):
    return json.loads(
        aws_lambda.invoke(FunctionName=pytest.function_name, Payload=json.dumps(event))["Payload"].read().decode(
            "utf-8"))


def assert_s3_object_does_not_exist(bucket, key):
    assertion_error = AssertionError(
        f"S3 object with bucket {bucket} and key {key} should not exist.")
    try:
        s3.get_object(Bucket=bucket, Key=key)
        raise assertion_error
    except ClientError as client_error:
        if client_error.response["Error"]["Code"] != "NoSuchKey":
            raise assertion_error


def delete_object_silently(bucket, key):
    try:
        s3.delete_object(Bucket=bucket, Key=key)
    except ClientError:
        pass
