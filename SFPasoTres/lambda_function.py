import json, boto3, decimal, os
from datetime import datetime
client = boto3.client("lambda")
ConversationService = os.environ['ConversationService']

def lambda_handler(event, context):
   payload = {
      "operation": "update",
      "payload": {
            "Item": {
               "sessionId": event["sessionID"],
               "userMessage": event["mensaje"],
               "lastState": event["estado"],
               "intent": event["intent"],
               "lastQuestion": event["n_pregunta"],
               "botMessage": event["respuesta"]
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
   return retornar
   
def handle_decimal_type(obj):
  if isinstance(obj, Decimal):
      if float(obj).is_integer():
         return int(obj)
      else:
         return float(obj)
  raise TypeError