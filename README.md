
if you have a mac 
Environment
- check that docker desktop is running
- go to the bin folder and execute
  - ./docker-script.sh start
    - to start the docker files
  - ./docker-script.sh stop
    - to stop the docker files


python3 -m venv venv
source venv/bin/activate





API
- aws --endpoint-url=http://localhost:4566 logs describe-log-groups 
- curl -X 'GET'   'http://localhost:8000/similar_trips'   -H 'accept: application/json'
- curl -X 'GET' 'http://localhost:8000/weekly_average_trips?min_lon=-120&min_lat=-30&max_lon=50&max_lat=70' -H 'accept: application/json'
- curl -X 'GET' 'http://localhost:8000/weekly_average_trips_by_regions?regions=Davidport&regions=New%20Brandonmouth&regions=Taylorstad' -H 'accept: application/json'