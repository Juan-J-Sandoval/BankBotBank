import json, boto3, os
rds_data = boto3.client('rds-data')
cluster_arn = os.environ['cluster_arn_aurora']
secret_arn = os.environ['secret_arn_aurora']

def lambda_handler(event, context):
    print(json.dumps(event))
    # sql = """ 
    #         UPDATE Users SET sessionId = '', lastState = 'baja' WHERE sessionId = :sessionId
    #     """
    # sessionId = {'name': 'sessionId', 'value': {'stringValue': event['requestContext']['connectionId']}}
    # response = rds_data.execute_statement(
    #     includeResultMetadata = True,
    #     resourceArn = cluster_arn, 
    #     secretArn = secret_arn, 
    #     database = os.environ['name_db'], 
    #     sql = sql,
    #     parameters = [sessionId])
    # if response['ResponseMetadata']['HTTPStatusCode'] == 200:
    #     print('Proceso de desconexión correcto')
    return {}


