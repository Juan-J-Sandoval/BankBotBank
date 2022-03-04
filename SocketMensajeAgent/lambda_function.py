import json, boto3, os
rds_data = boto3.client('rds-data')
cluster_arn = os.environ['cluster_arn_aurora']
secret_arn = os.environ['secret_arn_aurora']


def lambda_handler(event, context):
    print(json.dumps(event))
    if json.loads(event['body']).get('sessionUsers'):
        query=QueryAsignacion(json.loads(event['body']).get('sessionUsers'), event['requestContext']['connectionId'])
        if 'NombreAgent' in query:
            msgsHistoric=QueryHistoric(json.loads(event['body']).get('sessionUsers'))
            mensaje={'message': msgsHistoric}
            api_gateway = boto3.client('apigatewaymanagementapi',endpoint_url = "https://" + event["requestContext"]["domainName"] + "/" + event["requestContext"]["stage"])
            api_gateway.post_to_connection(
                Data=json.dumps(mensaje, indent=2).encode('utf-8'),
                ConnectionId=event['requestContext']['connectionId']
            )
            message='Tu Agente asignado es: '+query['NombreAgent']
            mensaje={'message':message}
            api_gateway = boto3.client('apigatewaymanagementapi',endpoint_url = os.environ['socketUsuario'])
            api_gateway.post_to_connection(
                Data=json.dumps(mensaje, indent=2).encode('utf-8'),
                ConnectionId=json.loads(event['body']).get('sessionUsers')
            )
    else:
        mensaje={'message':json.loads(event['body'])['message']}
        query=QueryAgents(event['requestContext']['connectionId'])
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

def QueryAgents(idSocket):
    sql = """ 
        SELECT * from Agents WHERE sessionId = :agent
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
    if len(rows) != 0 and rows[0]['sessionUser'] != '':
        print("dddd")
        return {'idSocket': rows[0]['sessionUser']}
    else:
        return {}

def QueryAsignacion(socketUser,socketAgent):
    sql = """ 
        SELECT * from Agents WHERE sessionId = :sessionId
    """
    sessionId = {'name': 'sessionId', 'value': {'stringValue': socketAgent}}
    response = rds_data.execute_statement(
        includeResultMetadata = True,
        resourceArn = cluster_arn, 
        secretArn = secret_arn, 
        database = os.environ['name_db'], 
        sql = sql,
        parameters = [sessionId])
    rows = []
    rows = responseQuery(response)
    print(rows)
    if len(rows) != 0:
        sql = """ 
            UPDATE Users SET onHold=:onHold WHERE sessionId = :sessionId
        """
        sessionId = {'name': 'sessionId', 'value': {'stringValue': socketUser}}
        onHold = {'name':'onHold', 'value':{'booleanValue': False}}
        responseU = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [sessionId,onHold]
        )
        sql = """ 
            UPDATE Agents SET sessionUser=:sessionUser WHERE sessionId = :sessionId
        """
        sessionId = {'name': 'sessionId', 'value': {'stringValue': socketAgent}}
        sessionUser = {'name':'sessionUser', 'value':{'stringValue': socketUser}}
        responseA = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [sessionId,sessionUser]
        )
        if responseU['ResponseMetadata']['HTTPStatusCode'] == 200 and responseA['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {'NombreAgent': rows[0]['name']}
    return {}

def QueryHistoric(idSocket):
    sql = """ 
        SELECT * from Historic WHERE sessionId = :sessionId
    """
    sessionId= {'name':'sessionId', 'value':{'stringValue':idSocket}}
    response = rds_data.execute_statement(
        includeResultMetadata = True,
        resourceArn = cluster_arn, 
        secretArn = secret_arn, 
        database = os.environ['name_db'], 
        sql = sql,
        parameters = [sessionId])
    rows = []
    rows = responseQuery(response)
    response=[]
    if len(rows)>0:
        for fila in rows:
            response.append({'message':fila['mensaje'], 'type':fila['tipo']})
    else:
        response='Sin historial de mensajes'
    return response

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
