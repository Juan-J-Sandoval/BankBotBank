import json, boto3, os
sf = boto3.client('stepfunctions')

rds_data = boto3.client('rds-data')
cluster_arn = os.environ['cluster_arn_aurora']
secret_arn = os.environ['secret_arn_aurora']

def lambda_handler(event, context):
    print(json.dumps(event))
    mensaje={'message':''}
    query=QueryConversation(event['requestContext']['connectionId'])
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
        sf_respuesta = sf.start_sync_execution(
            stateMachineArn=os.environ['STATE_MACHINE'],
            input=str(sf_data))
        mensajeBot=json.loads(sf_respuesta['output'])
        if json.loads(sf_respuesta['output'])['intent'] == 'agentehabla':
            query=QueryAsignacion(event['requestContext']['connectionId'])
            print('segundo query',query)
            if 'idSocket' in query:
                # Instancia QueryHistoric(idSocket) para extraer historico de conversación
                QueryHistoric(event['requestContext']['connectionId'])
                mensaje.update({'message': "tu usuario es: "+event['requestContext']['connectionId']})
                api_gateway = boto3.client('apigatewaymanagementapi',endpoint_url = os.environ['socketAgente'])
                api_gateway.post_to_connection(
                    Data=json.dumps(mensaje, indent=2).encode('utf-8'),
                    ConnectionId=query['idSocket']
                )
                mensaje.update({'message':json.loads(sf_respuesta['output'])['message']})
                api_gateway = boto3.client('apigatewaymanagementapi',endpoint_url = "https://" + event["requestContext"]["domainName"] + "/" + event["requestContext"]["stage"])
                api_gateway.post_to_connection(
                    Data=json.dumps(mensajeBot, indent=2).encode('utf-8'),
                    ConnectionId=event['requestContext']['connectionId']
                )
            else:
                mensaje.update({'message':'Por el momento no tenemos agentes disponibles'})
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

def QueryConversation(idSocket):
    sql = """ 
        SELECT * from Conversations WHERE sessionId = :sessionId
    """
    sessionId = {'name': 'sessionId', 'value': {'stringValue': idSocket}}
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
    print(rows)
    if len(rows) != 0:
        if rows[0]['agent'] != None:
            return {'idSocket': rows[0]['agent']}
    return {}

def QueryAsignacion(idSocket):
    sql = """ 
        SELECT * from Users WHERE sessionId != '' and lastState = 'baja'
    """
    response = rds_data.execute_statement(
        includeResultMetadata = True,
        resourceArn = cluster_arn, 
        secretArn = secret_arn, 
        database = os.environ['name_db'], 
        sql = sql)
    rows = []
    rows = responseQuery(response)
    print(rows)
    if len(rows) != 0:
        sql = """ 
            UPDATE Conversations SET agent = :agent WHERE sessionId = :sessionId
        """
        sessionId = {'name': 'sessionId', 'value': {'stringValue': idSocket}}
        agent = {'name': 'agent', 'value': {'stringValue': rows[0]['sessionId']}}
        responseC = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [sessionId,agent]
        )
        sql = """ 
            UPDATE Users SET lastState = 'alta' WHERE email = :email
        """
        email = {'name': 'email', 'value': {'stringValue': rows[0]['email']}}
        responseU = rds_data.execute_statement(
            includeResultMetadata = True,
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [email]
        )
        if responseC['ResponseMetadata']['HTTPStatusCode'] == 200 and responseU['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {'idSocket': rows[0]['sessionId']}
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
    print(rows)

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
