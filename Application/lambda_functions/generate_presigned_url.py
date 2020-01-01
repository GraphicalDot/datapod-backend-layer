


import boto3
import uuid
from datetime import datetime
import json
from boto3.dynamodb.conditions import Key, Attr
from urllib.parse import unquote_plus
from botocore.client import Config

import decimal
DYNAMODB_URL = "http://dynamodb.ap-south-1.amazonaws.com"
DYNAMODB_REGION = "ap-south-1"
TABLE_NAME = "shared"
dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION, endpoint_url=DYNAMODB_URL)
table = dynamodb.Table(TABLE_NAME)

s3 = boto3.client('s3', config=Config(signature_version='s3v4'))

def lambda_handler(event, context):
    """
    Args 
        username: 
        filename:
        nonce:
        signednonce:
        noncehash:


    """

    for value in ["username", "filename", "nonce", "signed_nonce", "nonce_hash"]:
        if not event.get():
            return {"error": True, "sucess": False, "message": f"{value} is required", "data": None}

    user = table.get_item(
        Key={
            'username': event["username"],
        }
    )
    if not user.get("Item"):
        return {"error": True, "sucess": False, "message": "User doesnt exists", "data": None}

    public_key = user.get("public_key")


    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        print(json.dumps(event))
        print("Bucket : " + bucket)
        print("Key : " + key)
        
        response = s3.head_object(Bucket=bucket, Key=key)
    


        print("iv : " + response['Metadata']['x-amz-iv'])
        print("Public key : " + response['Metadata']['x-amz-shared-with'])
        print("Aes key : " + response['Metadata']['x-amz-aes_key'])
        print("Usenrame : " + response['Metadata']['x-amz-username'])
        
        session = boto3.session.Session(region_name='ap-south-1')
        s3Client = session.client('s3')
        url = s3Client.generate_presigned_url('get_object', Params = {'Bucket': bucket, 'Key': key}, ExpiresIn=3600)
        print("Presigned URL : " + url)
        item = {
                  'username': response['Metadata']['x-amz-username'],
                  'public_key':  response['Metadata']['x-amz-shared-with'],
                  'key': response['Metadata']['x-amz-aes_key'],
                  "created_at": int(datetime.now().timestamp()),
                  "iv": response['Metadata']['x-amz-iv'],
                  "source_username": response['Metadata']["x-amz-source-username"]
                }
        print (item)
        response = table.put_item(
              Item=item
            )
    return 