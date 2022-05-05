import json, boto3, os
sf = boto3.client('stepfunctions')

rds_data = boto3.client('rds-data')
cluster_arn = os.environ['cluster_arn_aurora']
secret_arn = os.environ['secret_arn_aurora']

def lambda_handler(event, context):
    print(json.dumps(event))
    mensaje={'message':''}
    query=QueryAgentsInUsers(event['requestContext']['connectionId'])
    print(query)
    if 'idSocket' in query:
        mensaje.update({'message':json.loads(event['body'])['message']})
        api_gateway = boto3.client('apigatewaymanagementapi',endpoint_url = os.environ['socketAgente'])
        api_gateway.post_to_connection(
            Data=json.dumps(mensaje, indent=2).encode('utf-8'),
            ConnectionId=query['idSocket']
        )
    else:
        sf_data = "{\"sessionID\":\""+event['requestContext']['connectionId']+"\",\"mensaje\":\""+json.loads(event['body'])['message']+"\"}"
        sf_respuesta = sf.start_sync_execution(stateMachineArn=os.environ['STATE_MACHINE'], input=str(sf_data))
        mensajeBot=json.loads(sf_respuesta['output'])
        updateCanal(id=event['requestContext']['connectionId'])
        if json.loads(sf_respuesta['output'])['intent'] == 'agentehabla':
            # Se le notifica al agente que tiene un usuario en espera
            if User(event['requestContext']['connectionId']):
                query=QueryAgent()
                print(query)
            if 'idSockets' in query:
                mensaje.update({'message': 'Hay un nuevo usuario en espera', 'sessionUsers':query['sessionUsers']})
                api_gateway = boto3.client('apigatewaymanagementapi',endpoint_url = os.environ['socketAgente'])
                for item in query['idSockets']:
                    api_gateway.post_to_connection(
                        Data=json.dumps(mensaje, indent=2).encode('utf-8'),
                        ConnectionId=item
                    )
                mensaje.update({'message':json.loads(sf_respuesta['output'])['message']})
                api_gateway = boto3.client('apigatewaymanagementapi',endpoint_url = "https://" + event["requestContext"]["domainName"] + "/" + event["requestContext"]["stage"])
                api_gateway.post_to_connection(
                    Data=json.dumps(mensajeBot, indent=2).encode('utf-8'),
                    ConnectionId=event['requestContext']['connectionId']
                )
            else:
                mensaje.update({'message':'No contamos con agentes disponibles, intenta mas tarde'})
                api_gateway = boto3.client('apigatewaymanagementapi',endpoint_url = "https://" + event["requestContext"]["domainName"] + "/" + event["requestContext"]["stage"])
                api_gateway.post_to_connection(
                    Data=json.dumps(mensaje, indent=2).encode('utf-8'),
                    ConnectionId=event['requestContext']['connectionId']
                )
        else:
            mensaje.update({'message':json.loads(sf_respuesta['output'])['message']})
            api_gateway = boto3.client('apigatewaymanagementapi',endpoint_url = "https://" + event["requestContext"]["domainName"] + "/" + event["requestContext"]["stage"])
            api_gateway.post_to_connection(
                Data=json.dumps(mensajeBot, indent=2).encode('utf-8'),
                ConnectionId=event['requestContext']['connectionId']
            )
    return {}

def QueryAgentsInUsers(idSocket):
    sql = """ 
        SELECT * from Agents WHERE sessionUser = :sessionUser
    """
    sessionUser = {'name': 'sessionUser', 'value': {'stringValue': idSocket}}
    response = rds_data.execute_statement(
        includeResultMetadata = True,
        resourceArn = cluster_arn, 
        secretArn = secret_arn, 
        database = os.environ['name_db'], 
        sql = sql,
        parameters = [sessionUser]
    )
    rows = []
    rows = responseQuery(response)
    print(rows)
    if len(rows) != 0:
        return {'idSocket': rows[0]['sessionId']}
    return {}

def User(sessionId):
    sql = """
        UPDATE Users SET onHold = True WHERE sessionId = :sessionId
    """
    sessionId = {'name': 'sessionId', 'value': {'stringValue': sessionId}}
    response = rds_data.execute_statement(
        includeResultMetadata = True,
        resourceArn = cluster_arn, 
        secretArn = secret_arn, 
        database = os.environ['name_db'], 
        sql = sql,
        parameters = [sessionId]
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return True

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
    print(rows)
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
            print(rows)
            if len(rows)!= 0:
                sessionUsers=[]
                for item in rows:
                    sessionUsers.append(item['sessionId'])
                return {'idSockets': sockets, 'sessionUsers':sessionUsers}
    return {}

def updateCanal(id, rs='LP'):
    sql = """ 
        SELECT * from Users where sessionId = :sessionId
    """
    sessionId = {'name': 'sessionId', 'value': {'stringValue': id}}
    response = rds_data.execute_statement(
        includeResultMetadata = True,
        resourceArn = cluster_arn, 
        secretArn = secret_arn, 
        database = os.environ['name_db'], 
        sql = sql,
        parameters = [sessionId]
    )
    rows = []
    rows = responseQuery(response)
    if len(rows) != 0:
        if rows[0]['canal'] != '':
            sql = """
                UPDATE Users SET canal = :canal WHERE sessionId = :sessionId
            """
            sessionId = {'name': 'sessionId', 'value': {'stringValue': id}}
            canal = {'name': 'canal', 'value': {'stringValue': rs}}
            response = rds_data.execute_statement(
                includeResultMetadata = True,
                resourceArn = cluster_arn, 
                secretArn = secret_arn, 
                database = os.environ['name_db'], 
                sql = sql,
                parameters = [sessionId,canal]
            )
            print(response['ResponseMetadata']['HTTPStatusCode']) 

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
