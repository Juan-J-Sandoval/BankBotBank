import os
import json
import boto3
from datetime import datetime,date

rds_data = boto3.client('rds-data')

# configuracion de auroraserveless
cluster_arn = os.environ['cluster_arn_aurora']
secret_arn = os.environ['secret_arn_aurora']

def lambda_handler(event, context):
    
    print("Received event: " + json.dumps(event, indent=2))
    print("evento" + event['operation'])
    
    payload_dictionary = json.loads(json.dumps(event['payload']['Item']))    
    operation = event['operation']
    
    if operation == 'RedesSociales':
        result = getRedesSociales()
        
    if operation == 'getCounterQuestionsByConversationAndDates':
        result = getCounterQuestionsByConversationAndDates(event['payload']['Item'], payload_dictionary)

    if operation == 'getUsersToday':
         result = getUsersToday(event['payload']['Item'], payload_dictionary)
    
    if operation == 'getAllUsersToday':
         result = getAllUsersToday(event['payload']['Item'], payload_dictionary)
    
    if operation == 'getUserWeekly':
         result = getUserWeekly(event['payload']['Item'], payload_dictionary)
         
    if operation == 'getUserMonthly':
         result = getUserMonthly(event['payload']['Item'], payload_dictionary)
         
    if operation == 'getUserYearly':
         result = getUserYearly(event['payload']['Item'], payload_dictionary)
    
    return result
    
def getRedesSociales():
    rs= ['TG', 'FB', 'LP']
    resulRS=[]
    for item in rs:
        sql = "select count(*) from Users where canal='"+item+"';"
        print(sql)
        response = rds_data.execute_statement(
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql)
        resulRS.append({item: response['records'][0][0]['longValue']})
    response={ 'code': 200, 'message': resulRS }
    return response

#definicion de conteo de preguntas por conversacion y rango de fechas
#formato de fechas %Y-%m-%d %H:%M:%S
def getCounterQuestionsByConversationAndDates(item, diccionary):

    if 'dateStart' not in diccionary or 'dateEnd' not in diccionary:
        result = {
            'code': 400,
            'messageError': "No puede crear el cliente, faltan datos requeridos"
        }
    else :
        sql = """ 
            SELECT count(1) from Users WHERE startConversation >= :dateStart AND endConversation <= :dateEnd
            """
        dateStart = {'name':'dateStart', 'value':{'stringValue': datetime.strptime(item['dateStart'], "%Y-%m-%d %H:%M:%S")}}
        dateEnd = {'name':'dateEnd', 'value':{'stringValue': datetime.strptime(item['dateEnd'], "%Y-%m-%d %H:%M:%S")}}
        response = rds_data.execute_statement(
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            database = os.environ['name_db'], 
            sql = sql,
            parameters = [dateStart, dateEnd])
        rows = []
        rows = responseQuery(response)
        if len(response['records']) > 0:
            result = {
                'code': 400,
                'message': "Sin resultados"
            }
        else :
            result = {
                'code': 200,
                'message': rows
            }
    
    return result

#obtener el numero de usuarios conectados hoy por hora
def getUsersToday(item, diccionary):
    today =date.today()
    sql = """ 
        select HOUR(startConversation) as Hora, count(1) as interacciones from Users WHERE startConversation >= :dateStart AND startConversation <= :dateEnd GROUP BY HOUR(startConversation)
        """
    dateStart = {'name':'dateStart', 'value':{'stringValue': today.strftime("%Y-%m-%d")+" 00:00:00"}}
    dateEnd = {'name':'dateEnd', 'value':{'stringValue': today.strftime("%Y-%m-%d")+" 23:59:59"}}
        #select count(1) from Users WHERE startConversation >= Date_format(now(),'%Y-%m-%d 00:00:00') AND startConversation <=Date_format(now(),'%Y-%m-%d 23:59:59')
        #select count(1) as interacciones from Users WHERE startConversation >= Date_format(now(),'%Y-%m-%d 00:00:00') AND startConversation <=Date_format(now(),'%Y-%m-%d 23:59:59') GROUP BY HOUR(startConversation)
    response = rds_data.execute_statement(
        resourceArn = cluster_arn,
        includeResultMetadata = True,   
        secretArn = secret_arn, 
        database = os.environ['name_db'], 
        sql = sql,
        parameters = [dateStart, dateEnd]
        )
    rows=responseQuery(response)
    print(json.dumps(rows))
        #result=print(json.dumps(response['records'][0][0]['longValue']))
    result={
        "code":200,
        "message": rows
    }
    return result

#obtener el numero total de usuarios del dia de hoy
def getAllUsersToday(item, diccionary):
    today =date.today()
    sql = """ 
        select count(1) from Users WHERE startConversation >= :dateStart AND startConversation <= :dateEnd 
        """
    dateStart = {'name':'dateStart', 'value':{'stringValue': today.strftime("%Y-%m-%d")+" 00:00:00"}}
    dateEnd = {'name':'dateEnd', 'value':{'stringValue': today.strftime("%Y-%m-%d")+" 23:59:59"}}
    response = rds_data.execute_statement(
        resourceArn = cluster_arn,
        includeResultMetadata = True,   
        secretArn = secret_arn, 
        database = os.environ['name_db'], 
        sql = sql,
        parameters = [dateStart, dateEnd]
        )
    rows=responseQuery(response)
    print(json.dumps(rows))
        #result=print(json.dumps(response['records'][0][0]['longValue']))
    result={
        "code":200,
        "message": rows
    }
    return result
 
#obtener el total de usuarios por numero de semana#
#el lunes es el dia 0, martes 1, miercoles 2 y asi susesivamente hasta el domingo= 6
def getUserWeekly(item, diccionary):
    sql = """ 
    select WEEKDAY(startConversation) as dia, count(1) as interacciones from Users WHERE WEEK(startConversation) = WEEK(Date_format(now(),'%Y-%m-%d 23:59:59')- INTERVAL 0 WEEK)GROUP BY DAY(startConversation) 
    """
    response = rds_data.execute_statement(
        resourceArn = cluster_arn,
        includeResultMetadata = True,   
        secretArn = secret_arn, 
        database = os.environ['name_db'], 
        sql = sql
        )
    rows=responseQuery(response)
    print(json.dumps(rows))
        #result=print(json.dumps(response['records'][0][0]['longValue']))
    result={
        "code":200,
        "message": rows
    }
    return result

#funcion para obtener el total de usuarios por mes.#
def getUserMonthly(item, diccionary):
    sql = """ 
            select MONTH(startConversation) as MES, count(1) as interacciones from Users GROUP BY MONTH(startConversation)
        """
    response = rds_data.execute_statement(
        resourceArn = cluster_arn,
        includeResultMetadata = True,   
        secretArn = secret_arn, 
        database = os.environ['name_db'], 
        sql = sql
        )
    rows=responseQuery(response)
    print(json.dumps(rows))
        #result=print(json.dumps(response['records'][0][0]['longValue']))
    result={
        "code":200,
        "message": rows
    }
    return result

#obtener el total de usuarios anualmente
def getUserYearly(item, diccionary):
    sql = """ 
        select YEAR(startConversation) as year, count(1) as interacciones from Users GROUP BY YEAR(startConversation)
    """
    response = rds_data.execute_statement(
        resourceArn = cluster_arn,
        includeResultMetadata = True,   
        secretArn = secret_arn, 
        database = os.environ['name_db'], 
        sql = sql
        )
    rows=responseQuery(response)
    print(json.dumps(rows))
        #result=print(json.dumps(response['records'][0][0]['longValue']))
    result={
        "code":200,
        "message": rows
    }
    return result

def responseQuery(payload_item):
    rows = []
    cols = []
    for column in payload_item['columnMetadata']:
        cols.append(column['name'])
    for record in payload_item['records'] :
        i = 0
        row = {}
        for item in record:
            print (item, i)
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