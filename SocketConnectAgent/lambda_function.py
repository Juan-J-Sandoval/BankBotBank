import json, boto3, os
# rds_data = boto3.client('rds-data')
# cluster_arn = os.environ['cluster_arn_aurora']
# secret_arn = os.environ['secret_arn_aurora']

def lambda_handler(event, context):
    print(json.dumps(event))
    # sql = """ 
    #         SELECT * from Users WHERE sessionId = ''
    #         """
    # response = rds_data.execute_statement(
    #     includeResultMetadata = True,
    #     resourceArn = cluster_arn, 
    #     secretArn = secret_arn, 
    #     database = os.environ['name_db'], 
    #     sql = sql)
    # rows = []
    # rows = responseQuery(response)
    # if len(rows) != 0:
    #     sql = """ 
    #         UPDATE Users SET sessionId = :sessionId, lastState = 'baja' WHERE email = :email
    #     """
    #     sessionId = {'name': 'sessionId', 'value': {'stringValue': event['requestContext']['connectionId']}}
    #     email = {'name': 'email', 'value': {'stringValue': rows[0]['email']}}
    #     response = rds_data.execute_statement(
    #         includeResultMetadata = True,
    #         resourceArn = cluster_arn, 
    #         secretArn = secret_arn, 
    #         database = os.environ['name_db'], 
    #         sql = sql,
    #         parameters = [sessionId, email])
    #     if response['ResponseMetadata']['HTTPStatusCode'] == 200:
    #         print('Proceso de conexión correcto')
    return {}
            
    
def responseQuery(payload_item):
    print(json.dumps(payload_item))
    rows = []
    cols = []
    for column in payload_item['columnMetadata']:
        cols.append(column['name'])
    for record in payload_item['records'] :
        i = 0
        row = {}
        for item in record:
            if 'stringValue' in item  :
                row[cols[i]] = item['stringValue']
            elif 'blobValue' in item :
                row[cols[i]] = item['blobValue']
            elif 'doubleValue' in item :
                row[cols[i]] = item['doubleValue']
            elif 'longValue' in item :
                row[cols[i]] = item['longValue']
            elif 'booleanValue' in item:
                row[cols[i]] = item['booleanValue']
            else :
                row[cols[i]] = null
            i += 1
        rows.append(row)
    return rows
