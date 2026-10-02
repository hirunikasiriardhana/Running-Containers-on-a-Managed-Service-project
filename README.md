# Running Containers on a Managed Service

Deployed a containerized Node.js coffee suppliers app using managed AWS services.

## Architecture
Café website (S3) -> API Gateway -> Elastic Beanstalk (Docker, image from ECR) -> Aurora Serverless v2 (MySQL)

## Steps
1. Created a second subnet in another AZ and fixed the route table (internet gateway)
2. Created an Aurora Serverless v2 cluster (MySQL compatible) with the RDS Data API enabled
3. Tested the container from the IDE against Aurora
4. Created the DB objects (user, database, table) using the RDS Query Editor
5. Loaded supplier data from the SQL dump using the mysql client
6. Deployed to Elastic Beanstalk using options.txt and Dockerrun.aws.json
7. Created an API Gateway /bean_products GET proxy to /beans.json and deployed it to the prod stage
