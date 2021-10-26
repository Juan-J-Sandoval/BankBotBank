# try:
#     import unzip_requirements
# except ImportError:
#     pass

import json
import requests
from bs4 import BeautifulSoup

MOBILE_USER_AGENT = "Mozilla/5.0 (Linux; U; Android 2.3.6; en-us; Nexus S Build/GRK39F) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1"

##
# Adquiere la página con la búsqueda solicitada, y la zona especificada de la cual adquirir el texto.
# @param event {dict} {"queryStringParameters":{"text":"texto a buscar"}} una estructura conteniendo el texto con el cual se hará una busqueda de google
# @param context {dict} especificaciones para la función lambda
# @return {string} texto extraído como respuesta
##
def lambda_handler  (event, context):
    #text = event['text']

    try:
        print("EVENT: " + str(event))
    except Exception as e:
        print("Event Exception: " + str(e))

    try:
        print("EVENT MESSAGE: " + str(event['text']))
        text = event['text']
    except Exception as e:
        print("Event Exception: " + str(e))

    """try:
        body = json.loads(event.get('body', '{}'))
    except Exception as e:
        print("Exception: " + str(e))
    try:
        print("REQUEST BODY: " + str(body))
    except Exception as e:
        print("Exception printing 1: " + str(e))
    try:
        print("MESSAGE: " + body.get('text', ''))
        text = body.get('text', '')
    except Exception as e:
        print("Exception printing 2: " + str(e))"""

    # los elementos de la pagina de los cuales buscar
    headers = {"user-agent": MOBILE_USER_AGENT}
    URL = f"https://google.com/search?hl=es&q={text}"
    resp = requests.get(URL, headers=headers)
    resultado = "Por el momento no cuento con esa información"
    
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.content, "html.parser")
        resultado = ""
        for g in soup.find_all('div', class_='uUPGi')[1]:
            resultado += ' ' + g.get_text(' ')
        print(resultado)

    response = {"answer": resultado}

    print("THE ANSWER TO BE SENT IS: " + str(response))

    return {
        "statusCode": 200,
        "body": response
    }
