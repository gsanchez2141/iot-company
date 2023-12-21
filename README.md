

# Architecture Diagram

![IOT Architecture Pipeline.png](..%2F..%2F..%2F..%2FDownloads%2FIOT%20Architecture%20Pipeline.png)

# Current Implementation 
- Python script that generates IoT Mock Data according to CSV Sample - On bin/sqs_generator
- Python Lambda - On app/src
- Python API - on api/src 
- [sqls_with_explanations.sql](sqls_with_explanations.sql)
  - Different SQLs with their corresponding questions 
- Docker-script.sh that preps the environment with
  - Docker compose 
    - Enabling 
    - Postgres container with postgis
      - init.sql contains table schema creation and indexes 
    - Localstack
      - Deploying
        - SQS Queue
        - Python Lambda Function
        - SQS Trigger/Event source mapping
    - Python API with fast api that reads from Postgres
    - Runs python script that mocks IoT data sending it to SQS

# High level End to End current Implementation explanation
  - Docker-script.sh || Start preps the environment and deploys resources on Local Stack 
  - Docker-script.sh also executes Python script that mocks IoT data sends it to SQS
  - SQS Triggers Lambda function 
  - Lambda Function writes messages into Postgres concurrently according to batch size and batch window
  - Python API enabled via Docker-script.sh has
    - 3 different endpoints according to what was understood on the requirements
    - Each of them perform sql queries to postgres and provides the proper response according to the request
  - Docker-script.sh || Stop destroys and brings down the environments and resources

## Debt
  - Many best practices
  - Some hard coding
  - Environment variables
  - Better Error Handling
  - Code rearrangement and readability 
  - Testing 
    - Unit 
    - Integration
  - Reading sample CSV and persisting it on a different table with the purpose of answering the last SQL question 


## Requirements:
- Docker - [How to install?](https://docs.docker.com/engine/install/)
- Docker Compose - [How to install?](https://docs.docker.com/compose/install/)
- awslocal - [How to install?](https://github.com/localstack/awscli-local)
- Python - [How to install?](https://www.python.org/downloads/)


# Step by Step 
- Double check that you have all the requirements
- Download the repo https://github.com/gsanchez2141/iot-company
- Git clone into a new folder
- Deploy stack, resources and run mock data generator
  - Once on the root of your iot-company repo
    - cd bin
    - ./docker-script.sh start
    - RUN Sample Curls provided below which I believe fulfills all the [questions](sqls_with_explanations.sql) 
    - Check the localstack logs with the sample provided below
    - Log in with your favorite IDE to the postgres db to run and check and validate the SQL [queries](sqls_with_explanations.sql) 
    - Once you're done 
    - ./docker-script.sh stop will destroy and tear down all the stack and resources


## Sample to check LocalStack logs 
- awslocal logs describe-log-groups

## Sample API Curls 
Once the .sh scripts finishes deploying the following curls can be run
- curl -X 'GET'   'http://localhost:8000/similar_trips'   -H 'accept: application/json'
- curl -X 'GET' 'http://localhost:8000/weekly_average_trips?min_lon=-120&min_lat=-30&max_lon=50&max_lat=70' -H 'accept: application/json'
- curl -X 'GET' 'http://localhost:8000/weekly_average_trips_by_regions?regions=Davidport&regions=New%20Brandonmouth&regions=Taylorstad' -H 'accept: application/json'

## Logging into the db to run the queries if you like
Before destroying and bringing down the deployment you can access the postgres db and run the queries on [sqls_with_explanations.sql](sqls_with_explanations.sql) 
Credentials required by your IDE
- db_host = 'localhost' 
- db_port = 5432
- db_name = 'mydatabase'
- db_user = 'myuser'
- db_password = 'mypassword'

