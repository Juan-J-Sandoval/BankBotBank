import json
from nltk.stem.snowball import SpanishStemmer
import io
import sys
from unidecode import unidecode

stopwords = "la de él ésta éstas éste estos última últimas último últimos a añadió aún actualmente adelante además afirmó agregó ahí ahora al algún algo alguna algunas alguno algunos alrededor ambos ante anterior antes apenas aproximadamente aquí así aseguró aunque bajo cada casi cerca cierto cinco comentó con conocer consideró considera contra eres tamte cosas creo cual cuales cualquier cuatro cuenta da dado dan dar debe deben debido decir dejó del demás dentro desde después dice dicen dicho dieron diferente diferentes dijeron dijo dio dos durante e ejemplo el ella ellas ello ellos embargo en entonces entre era eran es esa esas ese eso esos está están estaba estaban estamos estar estará estas este esto estos estoy estuvo ex existe existen explicó expresó fin fue fuera fueron gran grandes ha había habían haber habrá hace hacen hacer hacerlo hacia haciendo han hasta hay haya he hecho hemos hicieron hizo hoy hubo igual incluso indicó informó junto lado las le les llegó lleva llevar lo los luego lugar más manifestó mayor mediante mejor mencionó menos mientras misma mismas mismo mismos momento mucha muchas mucho muchos muy nada nadie ni ningún ninguna ningunas ninguno ningunos nos nosotras nosotros nuestra nuestras nuestro nuestros nueva nuevas nuevo nuevos nunca o ocho otra otras otro otros para parece parte partir pasada pasado pero pesar poca pocas poco pocos podemos podrá podrán podría podrían poner por porque posible próximo próximos primer primera primero primeros principalmente propia propias propio propios pudo pueda puede pueden pues qué que quedó queremos quién quien quienes quiere realizó realizado realizar respecto sí sólo se señaló sea sean según segunda segundo seis ser será serán sería si sido siempre siendo siete sigue siguiente sino sobre sola solamente solas solo solos son su sus tal también tampoco tan tanto tenía tendrá tendrán tenemos tener tenga tengo tenido tercera tiene tienen toda todas todavía todo todos total tras trata través tres tuvo un una unas uno unos usted va vamos van varias varios veces ver vez y ya q w e r t y u i o p a s d f g h j k l z x c v b n m"
whitelist = set('abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
pesosYMedidas = ["kg", "metr", "alto", "larg", "ancho", "m3", "m2", "volum", "dimension", "maxim", "pes", "kilogr", "centimetr", "cubic","cuadr","limit","pulg","gram","mililitr","litr","kil","ml"]


def lambda_handler(event, context):
    payload_dictionary = json.loads(json.dumps(event['payload']))
    operation = event['operation']

    if operation == 'lexemas':
        result = vectorizeText(payload_dictionary)
    else:
        result={ "statusCode": 400, "body":"Falta datos" }

    return result

def removeStopwords(text):
    text = text.lower()
    text = unidecode(text)

    stopwordsUnidecode = unidecode(stopwords)

    sw = stopwordsUnidecode.split(" ")

    for character in text:
        if character not in whitelist:
            text = text.replace(character, " ")

    text = ''.join(filter(whitelist.__contains__,text))
    textlist = text.split(" ")

    for stopword in sw:
        index = 0
        for word in textlist:
            if word == stopword or word == "":
                textlist.remove(word)
            for termino in pesosYMedidas:
                if termino in word:
                    textlist[index] = termino
            index = index + 1
    return textlist

def stemIt(text):
    stemmer = SpanishStemmer()
    stemmedlist = []
    for word in text:
        stemmedlist.append(stemmer.stem(word))
    return stemmedlist

def vectorizeText(text):
    text = removeStopwords(text)
    text = stemIt(text)

    words = []
    vector = []

    text
    for word in text:
        if word not in words:
            n = text.count(word)
            words.append(word)

            vector.append([word, n])
        else:
            continue
    return {
        "statusCode": 200,
        "body":vector
    }
