import json, os
from twilio.jwt.client import ClientCapabilityToken

def lambda_handler(event, context):
    #genera token con libreria twilio
    capability = ClientCapabilityToken(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
    capability.allow_client_outgoing(os.environ['TWILIO_TWIML_APP_SID'])
    token = capability.to_jwt()
    response = {'body':token}
    print(">>> ",response)
    return response
    