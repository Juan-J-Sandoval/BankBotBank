import json, boto3, os
rds_data = boto3.client('rds-data')
cluster_arn = os.environ['cluster_arn_aurora']
secret_arn = os.environ['secret_arn_aurora']


def lambda_handler(event, context):
    print(json.dumps(event))
    mensaje={'message':json.loads(event['body'])['message']}
    query=QueryConversation(event['requestContext']['connectionId'])
    if 'idSocket' in query:
        api_gateway = boto3.client('apigatewaymanagementapi',endpoint_url = os.environ['socketUsuario'])
        print(mensaje,' ',type(mensaje))
        api_gateway.post_to_connection(
            Data=json.dumps(mensaje, indent=2).encode('utf-8'),
            ConnectionId=query['idSocket']
        )
    else:
        api_gateway = boto3.client('apigatewaymanagementapi',endpoint_url = "https://" + event["requestContext"]["domainName"] + "/" + event["requestContext"]["stage"])
        mensaje.update({'message': 'Sin usuario asignado'})
        print(mensaje,' ',type(mensaje))
        api_gateway.post_to_connection(
            Data=json.dumps(mensaje, indent=2).encode('utf-8'),
            ConnectionId=event['requestContext']['connectionId']
        )
    return {}

def QueryConversation(idSocket):
    sql = """ 
        SELECT * from Conversations WHERE agent = :agent
    """
    agent = {'name': 'agent', 'value': {'stringValue': idSocket}}
    response = rds_data.execute_statement(
        includeResultMetadata = True,
        resourceArn = cluster_arn, 
        secretArn = secret_arn, 
        database = os.environ['name_db'], 
        sql = sql,
        parameters = [agent]
    )
    rows = []
    rows = responseQuery(response)
    print(rows)
    if len(rows) != 0:
        return {'idSocket': rows[0]['sessionId']}
    else:
        return {}


def responseQuery(payload_item):
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
                row[cols[i]] = None
            i += 1
        rows.append(row)
    return rows
