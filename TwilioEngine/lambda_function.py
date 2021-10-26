import json, boto3, re, os
from datetime import datetime, timezone
from twilio.twiml.voice_response import Gather, VoiceResponse, Start, Stream, Say
sf = boto3.client('stepfunctions')
client = boto3.client("lambda")
ConversationService = os.environ['ConversationService']

def lambda_handler(event, context):
    print(">>> ",json.dumps(event))
    response = VoiceResponse()
    texto = event['queryStringParameters']['SpeechResult']
    idTelefono = event['queryStringParameters']['CallSid']
    print("Transcripcion: ",texto)
    #cambia signo por espacios
    texto = texto.replace("[+]", " ")
    print("texto procesado",texto)
    #identifica secuencia de numero y los deja juntos sin espacios
    print("Result expr: ",re.match("^\d+", texto))
    if (re.match("^\d+", texto) != None):
        texto = texto.replace(" ", "")
        print("texto limpio ",texto)
    try:
    
        now = datetime.now()
        payload = {
            "operation": "create",
            "payload": {
                "Item": {
                    "sessionId" : event['queryStringParameters']['CallSid'],
                    "startDate": now.strftime("%m/%d/%Y, %H:%M:%S")
                }
            }
        }
        client.invoke(
            FunctionName = ConversationService,
            InvocationType = 'RequestResponse',
            Payload = json.dumps(payload)
        )
        #se genera variable con los datos para la StepFunction debe ser json en formato string
        sf_data = "{\"sessionID\":\""+idTelefono+"\",\"mensaje\":\""+texto+"\"}"
        sf_respuesta = sf.start_sync_execution( stateMachineArn=os.environ['MAQUINA_ESTADOS'], input=str(sf_data))
        print('sf_respuesta: ',sf_respuesta['output'])
        sf_data_output=json.loads(sf_respuesta['output'])
        print(sf_data_output)
        txt = sf_data_output['respuesta']
    except:
        txt = "Tengo problemas de comunicación, puedes volver a intentarlo por favor"""
    #se genera la respuesta con la libreria de twilio para retornar un formato correcto
    response.say(txt, voice='Polly.Miguel')
    url = "https://"+event['requestContext']['domainName']+"/"+os.environ['STAGE']+"/engine"
    response.gather(input="speech", language='es-MX', method='GET', action=url, speechTimeout='auto')
    response = str(response)
    response = response.encode(encoding='UTF-8',errors='strict')
    #los headers son indispensables
    response = {'statusCode': 200,'headers': {'Content-Type': 'text/xml'},'body': response}
    print(">>>", response)
    return response
