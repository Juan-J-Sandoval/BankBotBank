import json
import os
from twilio.twiml.voice_response import Gather, VoiceResponse, Start, Stream, Say

def lambda_handler(event, context):
    print(">>> ",json.dumps(event))
    #se genera una respuesta con la libreria de twilio, esta lambda solo es para que en la llamada empiece hablando el bot
    response = VoiceResponse()
    response.say('Hola buen día, estas llamando a Grupo Vanguardia, en que puedo ayudarte?', voice='Polly.Miguel')
    url = "https://"+event['requestContext']['domainName']+"/"+os.environ['STAGE']+"/engine"
    response.gather(input='speech', language='es-MX', method='GET', action=url, speechTimeout='auto')
    response = str(response)
    response = response.encode(encoding='UTF-8',errors='strict')
    response = {
        "statusCode": 200,
        "headers": {
            'Content-Type': 'text/xml'
        },
        "body":response
    }
    print("<<< ", response)
    return response