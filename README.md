ClimbAssistWebpConverter
============

Welcome to ClimbAssistWebpConverter!

See it live at [climbassist.com](https://climbassist.com)!

This repository contains the code for a stand-alone AWS Lambda function which converts JPG images to WEBP images. The
Lambda function and related resources are provisioned using CloudFormation. This function accepts a source and
destination S3 location, retrieves the image from the source location, converts it to WEBP, and uploads it to the
destination.

In production, this function is triggered by ClimbAssistService to convert JPG images (uploaded by users) to WEBP and
store both images in S3 to be retrieved as needed by the ClimbAssistUI. The two formats are required because WEBP images
are smaller (and thus cheaper) than JPG, but WEBP is not supported on Apple products so we use the JPG images as a
fallback. However, there is no Climb-Assist-specific logic in this package.

If you have any questions or concerns, reach out to the development team at 
[dev@climbassist.com](mailto:dev@climbassist.com).

To clone this repository, run the following command:

    $ git clone https://github.com/ClimbAssist/ClimbAssistWebpConverter.git

Documentation
-------------

The Lambda function accepts the following input:
```json
{
    "sourceLocation": {
        "bucket": string,
        "key": string
    },
    "destinationLocation": {
        "bucket": string,
        "key": string
    }
}
```
It produces the following output:
```json
{
    "statusCode": int,
    "body": {
        "message": string
    }
}
```

If `statusCode` is 200, then the file was successfully converted and uploaded to the destination. If not, then there
will be a reason given in `body`.

Deploying a Development Stack
-----------------------------

In order to run the service, you will need access to the Climb Assist AWS account. Most likely, you will have to reach
out to the development team and have them run your changes and confirm that they work.

However, if you do have access to the AWS account and you would like to try to create a development stack, the
instructions are as follows:

1. Install the SAM CLI following [these
instructions](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html).
Note: You don't need to install Docker, even though it says you do.
   
1. Create a development stack.

        $ ./dev-stack --name <name>
         
    `<name>` is whatever you want used to name the stack, deployment S3 bucket, and resources. If I pass in "dustin", 
    the stack will be named "dustin-dev" and named resources will have "-dustin" added to the ends of their names to
    avoid naming conflicts.

Integration Tests
-------------------------

The integration tests in the package are located under `tests/integration`.

1. Create a development stack. See above.

1. Install Python 3.7+ following the instructions [here](https://wiki.python.org/moin/BeginnersGuide/Download).

1. Install `virtualenv`.

        $ python3 -m pip install --user virtualenv

1. Create a virtual environment (this only needs to be done once).

        $ python3 -m venv venv

1. Activate the virtual environment.

        $ source env/bin/activate
        
1. Install the test dependencies (this only needs to be done once).

        $ pip install -r tests/requirements.txt

1. Run the integration tests.

        $ python -m pytest -s tests/integration/* --bucket <S3 bucket> --function_name <AWS Lambda function name>
        
    `<S3 bucket>` is an S3 bucket to which you have read and write access. The tests will use this bucket to store input
    and output artifacts and will clean them up when finished. If you've created a development stack in
    ClimbAssistService, it is convenient to use the photos S3 bucket created for you, named like
    `photos-172776452117-us-west-2-<name>`.  `<AWS Lambda function name>` is the name of the WEBP converter Lambda
    function created in the development stack, `ClimbAssistWebpConverter-<name>` (although technically it can be run
    against any Lambda function, including Beta or Prod).
