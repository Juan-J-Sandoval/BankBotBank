import json, boto3, os
client = boto3.client("lambda")
def lambda_handler(event, context):
    #solo para verificar la conexion 
    print(json.dumps(event))
    return {}