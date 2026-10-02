import boto3
import json

S3API = boto3.client("s3", region_name="us-east-1") 
bucket_name = "c220889a5570646l16933639t1w232137066767-s3bucket-hau9a1rr1vgc"

policy_file = open("/home/ec2-user/environment/resources/public_policy.json", "r")


S3API.put_bucket_policy(
    Bucket = bucket_name,
    Policy = policy_file.read()
)
print ("Setting Permissions - DONE")