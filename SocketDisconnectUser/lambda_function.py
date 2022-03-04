import json, boto3, os
rds_data = boto3.client('rds-data')
cluster_arn = os.environ['cluster_arn_aurora']
secret_arn = os.environ['secret_arn_aurora']

def lambda_handler(event, context):
    print(json.dumps(event))
    sql = """
        UPDATE Users SET sessionId = '', onHold=False WHERE sessionId = :sessionId
    """
    sessionId = {'name': 'sessionId', 'value': {'stringValue': event['requestContext']['connectionId']}}
    response = rds_data.execute_statement(
        includeResultMetadata = True,
        resourceArn = cluster_arn, 
        secretArn = secret_arn, 
        database = os.environ['name_db'], 
        sql = sql,
        parameters = [sessionId]
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        sql = """
            UPDATE Agents SET sessionUser = '' WHERE sessionUser = :sessionId
        """
        sessionId = {'name': 'sessionId', 'value': {'stringValue': event['requestContext']['connectionId']}}
        response = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [sessionId]
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            query=QueryAgent()
            print(query)
            if 'idSockets' in query and 'sessionUsers' in query:
                mensaje={'message': '', 'sessionUsers':query['sessionUsers']}
                api_gateway = boto3.client('apigatewaymanagementapi',endpoint_url = os.environ['socketAgente'])
                for item in query['idSockets']:
                    api_gateway.post_to_connection(
                        Data=json.dumps(mensaje, indent=2).encode('utf-8'),
                        ConnectionId=item
                    )
            print('Conversacion eliminada')
    return {}
    
def QueryAgent():
    sql = """ 
        SELECT * from Agents where sessionId != ''
    """
    response = rds_data.execute_statement(
        includeResultMetadata = True,
        resourceArn = cluster_arn, 
        secretArn = secret_arn, 
        database = os.environ['name_db'], 
        sql = sql
    )
    rows = []
    rows = responseQuery(response)
    if len(rows) != 0:
        sockets=[]
        for item in rows:
            if item['sessionId'] != '':
                sockets.append(item['sessionId'])
        if len(sockets) != 0:
            sql = """ 
                SELECT * from Users where onHold = True
            """
            response = rds_data.execute_statement(
                includeResultMetadata = True,
                resourceArn = cluster_arn, 
                secretArn = secret_arn, 
                database = os.environ['name_db'], 
                sql = sql
            )
            rows = []
            rows = responseQuery(response)
            sessionUsers=[]
            if len(rows)!= 0:
                for item in rows:
                    sessionUsers.append(item['sessionId'])
            return {'idSockets': sockets, 'sessionUsers':sessionUsers}
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
