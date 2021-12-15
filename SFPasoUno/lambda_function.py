import json, boto3, decimal, os
client = boto3.client("lambda")
ConversationService = os.environ['ConversationService']

def lambda_handler(event, context):
    payload = {
      "operation": "get",
      "payload": {
            "Item": {
               "sessionId": event["sessionID"]
            }
      }
    }
    response = client.invoke(
        FunctionName = ConversationService,
        InvocationType = 'RequestResponse',
        Payload = json.dumps(payload)
    )
    responseFromAPI = json.load(response['Payload'], parse_float=decimal.Decimal)
    itemSaved = responseFromAPI["message"]
    print(itemSaved)

    if len(itemSaved) > 0:
        retonar = {"mensaje":event["mensaje"], "estado":itemSaved[0]['lastState'],"n_pregunta":itemSaved[0]['lastQuestion'],"sessionID":event["sessionID"]}
    else:        
        payload = {
            "operation": "create",
            "payload": {
                "Item": {
                    "sessionId" : event["sessionID"],
                    "lastState": "cm"
                }
            }
        }
        response = client.invoke(
            FunctionName = ConversationService,
            InvocationType = 'RequestResponse',
            Payload = json.dumps(payload)
        )
        responseFromAPI = json.load(response['Payload'], parse_float=decimal.Decimal)
        itemSaved = responseFromAPI["message"]
        print(itemSaved)
        retonar = {"mensaje":event["mensaje"], "estado":"mensajex","n_pregunta":0,"sessionID":event["sessionID"]}
    print("resultado ",retonar)
    return retonar
