import json, boto3, decimal, os
from datetime import datetime
client = boto3.client("lambda")
ConversationService = os.environ['ConversationService']
# configuracion de auroraserveless
rds_data = boto3.client('rds-data')
cluster_arn = os.environ['cluster_arn_aurora']
secret_arn = os.environ['secret_arn_aurora']

def lambda_handler(event, context):
   payload = {
      "operation": "update",
      "payload": {
            "Item": {
               "sessionId": event["sessionID"],
               "lastState": event["estado"],
               "intent": event["intent"],
               "lastQuestion": event["n_pregunta"]
            }
      }
   }
   response = client.invoke(
      FunctionName = ConversationService,
      InvocationType = 'RequestResponse',
      Payload = json.dumps(payload)
   )
   responseFromAPI = json.load(response['Payload'], parse_float=decimal.Decimal)
   print(responseFromAPI)
   
   retornar = {"message":event["respuesta"],"sessionID":event["sessionID"],"intent":event["intent"]}
   print("retornar ",retornar)

   historic(event)

   return retornar

def historic(event):
   now = datetime.now()
   sql = """
   INSERT INTO Historic( sessionId, mensaje, tipo, registro)
   VALUES (:sessionId, :mensaje, :tipo, :registro)
   """
   sessionId = {'name': 'sessionId', 'value': {'stringValue': event["sessionID"]}}
   mensaje = {'name': 'mensaje', 'value': {'stringValue': event["mensaje"]}}
   tipo = {'name': 'tipo', 'value': {'stringValue': 'user'}}
   registro = {'name':'registro', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
   parameters = [sessionId, mensaje, tipo, registro]
   response = rds_data.execute_statement(
      resourceArn = cluster_arn, 
      secretArn = secret_arn, 
      database = os.environ['name_db'], 
      sql = sql,
      parameters = parameters)

   if response['ResponseMetadata']['HTTPStatusCode'] == 200:
      print("Registrado de mensaje user correcto")
   else:
      print("Registrado de mensaje user fallido")
   
   sql = """
   INSERT INTO Historic( sessionId, mensaje, tipo, registro)
   VALUES (:sessionId, :mensaje, :tipo, :registro)
   """
   sessionId = {'name': 'sessionId', 'value': {'stringValue': event["sessionID"]}}
   mensaje = {'name': 'mensaje', 'value': {'stringValue': event["respuesta"]}}
   tipo = {'name': 'tipo', 'value': {'stringValue': 'bot'}}
   registro = {'name':'registro', 'value':{'stringValue': now.strftime("%Y-%m-%d %H:%M:%S")}}
   parameters = [sessionId, mensaje, tipo, registro]
   response = rds_data.execute_statement(
      resourceArn = cluster_arn, 
      secretArn = secret_arn, 
      database = os.environ['name_db'], 
      sql = sql,
      parameters = parameters)

   if response['ResponseMetadata']['HTTPStatusCode'] == 200:
      print("Registrado de mensaje user correcto")
   else:
      print("Registrado de mensaje user fallido")