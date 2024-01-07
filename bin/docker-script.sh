#!/bin/bash

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if a valid argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 [start|stop]"
    exit 1
fi

# Change to the script's directory
cd "$SCRIPT_DIR" || exit

# Get the current directory
CURRENT_DIR="$(pwd)"

# Check the provided argument and execute the corresponding Docker Compose command
case "$1" in
    "start")


        # Install and Activate virtual environment
        python3 -m venv venv
        echo "$CURRENT_DIR/venv/bin/activate"
        source "$CURRENT_DIR/venv/bin/activate"
        if [ -n "$VIRTUAL_ENV" ]; then
          echo "Virtual environment is active."
        else
          echo "Virtual environment is not active."
        fi

        # Copy the lambda python code for its localstack deployment
        cp -r "$CURRENT_DIR/../app/src/" "$CURRENT_DIR/src"

        # Install dependencies for the lambda python code for its localstack deployment
        pip install -r "$CURRENT_DIR/../app/src/requirements.txt" -t  "$CURRENT_DIR/src/"
        echo "$CURRENT_DIR/../app/src/requirements.txt"

        #zip lambda
        cd "$CURRENT_DIR/src"
        zip -r "$CURRENT_DIR/lambda_function.zip" *
        cd ..

        # Introduce a 10-second delay
        sleep 10


        # Removal of lambda's src
        rm -rf "$CURRENT_DIR/src"
        # Copy the api python for its docker deployment
        cp -r "$CURRENT_DIR/../api/src/" "$CURRENT_DIR/src"
        # Docker build
        docker build -t iot_company_api .


        docker-compose -f "$CURRENT_DIR/docker-compose.yml" up -d

        # Removal of APIs src
        rm -rf "$CURRENT_DIR/src"


        # Create SQS queue
        awslocal sqs create-queue --queue-name my-queue

        # Create Lambda Function
        awslocal lambda create-function \
            --function-name my-lambda \
            --runtime python3.11 \
            --zip-file fileb://lambda_function.zip \
            --handler app.lambda_handler \
            --role arn:aws:iam::000000000000:role/lambda-role

        # Create SQS Lambda Trigger
        awslocal lambda create-event-source-mapping \
             --function-name my-lambda \
             --event-source-arn arn:aws:sqs:us-west-2:000000000000:my-queue \
             --batch-size 500 \
             --maximum-batching-window-in-seconds 1

        rm "$CURRENT_DIR/lambda_function.zip"
        rm -rf "$CURRENT_DIR/src"



        # RUN SQS messages generator
        cd "$CURRENT_DIR/sqs_generator"
        pip install -r requirements.txt
        python generator.py

        # Deactivate virtual environment
        deactivate
        rm -rf venv

        echo "Stack running and sqs sample messages generated"

        ;;

    "stop")
        # Delete the SQS queue
        awslocal sqs delete-queue --queue-url http://sqs.us-west-2.localhost.localstack.cloud:4566/000000000000/my-queue

        # Delete the Lambda function
        awslocal lambda delete-function --function-name my-lambda

        docker-compose -f "$CURRENT_DIR/docker-compose.yml" down
        ;;

    *)
        echo "Invalid argument. Usage: $0 [start|stop]"
        exit 1
        ;;
esac

exit 0
