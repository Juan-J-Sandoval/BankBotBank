import json, re, boto3

defaultEntityToggles = {"SYS.TIEMPO":"True","SYS.MONEDA":"True","SYS.CP":"True","SYS.TELEFONO":"True","SYS.FECHA":"True","SYS.PORCENTAJE":"True","SYS.CORREO":"True","SYS.URL":"True","SYS.NUMERO.VUELO":"True","SYS.DURACION":"True","SYS.NOMBRE":"True","SYS.ORGANIZACION":"True","SYS.LOCACION":"True"}
entityDataStatic = {'range': {'start': 0, 'end': 0},'rawValue': '','value': {'kind': 'System', 'value': ''},'entity': '', 'slotName': ''}

def lambda_handler(event, context):
    print(event)
    toggledEntities = untoggleEntitiesUnsent(event['toggledEntities'])
    message = event['message']
    if toggledEntities:
        #Verificamos los valores perdidos en el diccionario para cambiarlos a Falso
        toggledEntities = untoggleEntitiesUnsent(toggledEntities)
        #agregamos las entidades del sistema extraídas
        event["response"]["slots"].extend(systemEntities(message, toggledEntities))
    else:
        event["response"]["slots"].extend(systemEntities(message))

    if toggledEntities:
        #Verificamos los valores perdidos en el diccionario para cambiarlos a Falso
        toggledEntities = untoggleEntitiesUnsent(toggledEntities)
        #agregamos las entidades del sistema extraídas 
        event["response"]["slots"].extend(comprehendEntities(message, toggledEntities))
    else:
        event["response"]["slots"].extend(comprehendEntities(message))
    return event["response"]

def systemEntities(text, toggledEntities):
    systemEntitiesExtracted = []
    if toggledEntities["SYS.TIEMPO"] == "True":
        entity = tiempo(text)
        if entity != None:
            systemEntitiesExtracted.append(entity)
    if toggledEntities["SYS.MONEDA"] == "True":
        entity = moneda(text)
        if entity != None:
            systemEntitiesExtracted.append(entity)
    if toggledEntities["SYS.CP"] == "True":
        entity = codigoPostal(text)
        if entity != None:
            systemEntitiesExtracted.append(entity)
    if toggledEntities["SYS.TELEFONO"] == "True":
        entity = telefono(text)
        if entity != None:
            systemEntitiesExtracted.append(entity)
    # if toggledEntities["SYS.FECHA"] == "True":
    #     entity = fecha(text)
    #     if entity != None:
    #         systemEntitiesExtracted.append(fecha(text))
    if toggledEntities["SYS.PORCENTAJE"] == "True":
        entity = porcentaje(text)
        if entity != None:
            systemEntitiesExtracted.append(entity)
    if toggledEntities["SYS.CORREO"] == "True":
        entity = correo(text)
        if entity != None:
            systemEntitiesExtracted.append(entity)
    if toggledEntities["SYS.URL"] == "True":
        entity = url(text)
        if entity != None:
            systemEntitiesExtracted.append(entity)
    if toggledEntities["SYS.NUMERO.VUELO"] == "True":
        entity = numerovuelo(text)
        if entity != None:
            systemEntitiesExtracted.append(entity)
    if toggledEntities["SYS.DURACION"] == "True":
        entity = duracion(text)
        if entity != None:
            systemEntitiesExtracted.append(entity)

    print("SYSTEM ENTITIES EXTRACTED LIST: " + str(systemEntitiesExtracted))
    return systemEntitiesExtracted

def comprehendEntities(text, toggledEntities):
    comprehend = boto3.client('comprehend', region_name='us-west-2')
    entities = comprehend.detect_entities(Text=text, LanguageCode='es')
    entities = entities['Entities']

    #print("AWS COMPREHEND TOTAL ENTITIES EXTRACTED: " + str(entities))

    entityData = entityDataStatic.copy()
    systemEntitiesExtracted = []

    for entity in entities:
        if entity["Type"] == "PERSON":
            if toggledEntities["SYS.NOMBRE"] == "True":
                entityData["rawValue"] = entity["Text"]
                entityData["entity"] = "SYS.NOMBRE"
                entityData["slotName"] = "entidadNombre"
                systemEntitiesExtracted.append(entityData.copy())
        elif entity["Type"] == "DATE":
            if toggledEntities["SYS.FECHA"] == "True":
                entityData["rawValue"] = entity["Text"]
                entityData["entity"] = "SYS.FECHA"
                entityData["slotName"] = "entidadFecha"
                systemEntitiesExtracted.append(entityData.copy())
        elif entity["Type"] == "ORGANIZATION":
            if toggledEntities["SYS.ORGANIZACION"] == "True":
                entityData["rawValue"] = entity["Text"]
                entityData["entity"] = "SYS.ORGANIZACION"
                entityData["slotName"] = "entidadOrganizacion"
                systemEntitiesExtracted.append(entityData.copy())
        elif entity["Type"] == "LOCATION":
            if toggledEntities["SYS.LOCACION"] == "True":
                entityData["rawValue"] = entity["Text"]
                entityData["entity"] = "SYS.LOCACION"
                entityData["slotName"] = "entidadLocacion"
                systemEntitiesExtracted.append(entityData.copy())

    return systemEntitiesExtracted

def untoggleEntitiesUnsent(toggledEntities):
    togglesUnsent = defaultEntityToggles.copy()

    all(map(togglesUnsent.pop, toggledEntities))   # use all() so it works for Python 2 and 3.

    for entityToggle in togglesUnsent:
        toggledEntities[entityToggle] = "False"

    return toggledEntities

def tiempo(texto):
    #Static values of the entity
    entityData = entityDataStatic.copy()
    entityData["entity"] = "SYS.TIEMPO"
    entityData["slotName"] = "entidadTiempo"

    horas = "(((1[0-2]){1,}|(\d))(\:)([0-6]\d))"
    SH = "((pm|am)|(p\.m\.|a\.m\.)|(\sp\.m\.|\sa\.m\.)|(\spm|\sam))"
    HO = "((\s)((de la))(\s)(tarde|noche|mañana|madrugada))"
    rangohoras = "(((1\d)|(2[0-4])|\d)\:([0-6]\d))"
    abrhoras = "((\s|)((h|H)(r|R)|(S|s)|\.|)(horas))"

    RE = horas+SH
    horas12 = re.compile(RE)
    horas12 = horas12.search(texto)

    RE = "("+horas+HO+")"
    hrOrd = re.compile(RE)
    hrOrd = hrOrd.search(texto)

    RE = "("+rangohoras+abrhoras+")"
    horas24 = re.compile(RE)
    horas24 = horas24.search(texto)

    if horas12 != None:
        entityData["rawValue"] = horas12.group()
        return entityData.copy()
    elif hrOrd != None:
        entityData["rawValue"] = hrOrd.group()
        return entityData.copy()
    elif horas24 != None:
        entityData["rawValue"] = horas24.group()
        return entityData.copy()
    else:
        return None

def moneda(texto):
    #Static values of the entity
    entityData = entityDataStatic.copy()
    entityData["entity"] = "SYS.MONEDA"
    entityData["slotName"] = "entidadMoneda"

    mon = "((\s|\sde\s)(dolar|euro|peso|libra|yuan))"
    cant = "(\s(millon|millones|mil))"
    numero = "(\d+)"
    RE = "("+numero+cant+mon+")"
    mnd1 = re.compile(RE)
    mnd1 = mnd1.search(texto)
    RE = "("+numero+mon+")"
    mnd2 = re.compile(RE)
    mnd2 = mnd2.search(texto)
    RE = "("+numero+cant+"\s"+numero+cant+mon+")"
    mnd3 = re.compile(RE)
    mnd3 = mnd3.search(texto)
    RE = "\$"+numero
    mnd4 = re.compile(RE)
    mnd4 = mnd4.search(texto)

    if mnd1 != None:
        entityData["rawValue"] = mnd1.group()
        return entityData.copy()
    elif mnd2 != None:
        entityData["rawValue"] = mnd2.group()
        return entityData.copy()
    elif mnd3 != None:
        entityData["rawValue"] = mnd3.group()
        return entityData.copy()
    elif mnd4 != None:
        entityData["rawValue"] = mnd4.group()
        return entityData.copy()
    else:
        return None

def codigoPostal(texto):
    #Static values of the entity
    entityData = entityDataStatic.copy()
    entityData["entity"] = "SYS.CP"
    entityData["slotName"] = "entidadCp"

    nombre = "(((C|c)(ó|o)digo\s(P|p)ostal)|(c\.p\.|cp|C\.P\.))"
    numero = "((\s|:)(\d{5}))"
    RE = "("+nombre+numero+")"
    cp = re.compile(RE)
    cp = cp.search(texto)
    if cp != None:
        entityData["rawValue"] = cp.group()
        return entityData.copy()
    else:
        return None

def telefono(texto):
    #Static values of the entity
    entityData = entityDataStatic.copy()
    entityData["entity"] = "SYS.TELEFONO"
    entityData["slotName"] = "entidadTelefono"

    ladaI = "(\+\d\d)"
    ladaL = "(\d\d\d)"
    opc1 = "(\d\d\d-\d\d-\d\d)"
    opc2 ="(\d\d\d\d\d\d\d)"
    opc3 = "(\d\d\d\s\d\d\s\d\d)"

    RE = "("+ladaI+"(\s)"+ladaL+"(\s)"+opc1+")"
    form = re.compile(RE)
    form = form.search(texto)

    RE = "("+ladaI+"(\s)"+ladaL+"(\s)"+opc2+")"
    form1 = re.compile(RE)
    form1 = form1.search(texto)

    RE = "("+ladaI+"(\s)"+ladaL+"(\s)"+opc3+")"
    form2 = re.compile(RE)
    form2 = form2.search(texto)

    RE = "("+ladaI+"-\("+ladaL+"\)-"+opc1+")"
    form3 = re.compile(RE)
    form3 = form3.search(texto)

    RE = "("+ladaI+"\("+ladaL+"\)"+opc2+")"
    form4 = re.compile(RE)
    form4 = form4.search(texto)

    RE = "("+ladaI+"\s\("+ladaL+"\)\s"+opc3+")"
    form5 = re.compile(RE)
    form5 = form5.search(texto)

    RE = "("+ladaL+"-"+opc1+")"
    form6 = re.compile(RE)
    form6 = form6.search(texto)

    RE = "("+ladaL+"\s"+opc2+")"
    form7 = re.compile(RE)
    form7 = form7.search(texto)

    RE = "("+ladaL+"\s"+opc3+")"
    form8 = re.compile(RE)
    form8 = form8.search(texto)

    RE = "(\("+ladaL+"\)\s"+opc3+")"
    form9 = re.compile(RE)
    form9 = form9.search(texto)

    RE = "("+ladaL+opc2+")"
    form10 = re.compile(RE)
    form10 = form10.search(texto)

    if form != None:
        entityData["rawValue"] = form.group()
        return entityData.copy()
    elif form1 != None:
        entityData["rawValue"] = form1.group()
        return entityData.copy()
    elif form2 != None:
        entityData["rawValue"] = form2.group()
        return entityData.copy()
    elif form3 != None:
        entityData["rawValue"] = form3.group()
        return entityData.copy()
    elif form4 != None:
        entityData["rawValue"] = form4.group()
        return entityData.copy()
    elif form5 != None:
        entityData["rawValue"] = form5.group()
        return entityData.copy()
    elif form6 != None:
        entityData["rawValue"] = form6.group()
        return entityData.copy()
    elif form7 != None:
        entityData["rawValue"] = form7.group()
        return entityData.copy()
    elif form8 != None:
        entityData["rawValue"] = form8.group()
        return entityData.copy()
    elif form9 != None:
        entityData["rawValue"] = form9.group()
        return entityData.copy()
    elif form10 != None:
        entityData["rawValue"] = form10.group()
        return entityData.copy()
    else:
        return None

def fecha(texto):
    #Static values of the entity
    entityData = entityDataStatic.copy()
    entityData["entity"] = "SYS.FECHA"
    entityData["slotName"] = "entidadFecha"

    meses =  "(0[1-9]|1[0-2])"
    dias = "([0-2]\d|3[0-1])"
    anios = "([1-2]\d\d\d)"
    aniosDD = "(\d\d)"

    RE = "("+dias+"/"+meses+"/"+anios+")"
    form = re.compile(RE)
    form = form.search(texto)

    RE = "("+dias+"-"+meses+"-"+anios+")"
    form1 = re.compile(RE)
    form1 = form1.search(texto)

    RE = "("+meses+"-"+dias+"-"+anios+")"
    form2 = re.compile(RE)
    form2 = form2.search(texto)

    RE = "("+meses+"/"+dias+"/"+anios+")"
    form3 = re.compile(RE)
    form3 = form3.search(texto)

    RE = "("+dias+"/"+meses+"/"+aniosDD+"\s)"
    form4 = re.compile(RE)
    form4 = form4.search(texto)

    if form != None:
        entityData["rawValue"] = form.group()
        return entityData.copy()
    elif form1 != None:
        entityData["rawValue"] = form1.group()
        return entityData.copy()
    elif form2 != None:
        entityData["rawValue"] = form2.group()
        return entityData.copy()
    elif form3 != None:
        entityData["rawValue"] = form3.group()
        return entityData.copy()
    elif form4 != None:
        entityData["rawValue"] = form4.group()
        return entityData.copy()
    else:
        return None

def porcentaje(texto):
    #Static values of the entity
    entityData = entityDataStatic.copy()
    entityData["entity"] = "SYS.PORCENTAJE"
    entityData["slotName"] = "entidadPorcentaje"

    porcentaje = re.compile(r"((\d+\%)|((\d+\s)(por ciento|porcentual)))")
    porcentaje = porcentaje.search(texto)

    if porcentaje != None:
        entityData["rawValue"] = porcentaje.group()
        return entityData.copy()
    else:
        return None

def correo(texto):
    #Static values of the entity
    entityData = entityDataStatic.copy()
    entityData["entity"] = "SYS.CORREO"
    entityData["slotName"] = "entidadCorreo"

    correo = re.compile(r"(([\S+][._a-z0-9-]+)*(@| arroba )([a-z0-9-]+)((\.| punto )([a-z]{2,3}))+)")
    correo = correo.search(texto)

    if correo != None:
        entityData["rawValue"] = correo.group()
        return entityData.copy()
    else:
        return None

def url(texto):
    #Static values of the entity
    entityData = entityDataStatic.copy()
    entityData["entity"] = "SYS.URL"
    entityData["slotName"] = "entidadUrl"

    url = re.compile(r"(https?:\/\/)?(www\.)[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)")
    url = url.search(texto)

    if url != None:
        entityData["rawValue"] = url.group()
        return entityData.copy()
    else:
        return None

def numerovuelo(texto):
    #Static values of the entity
    entityData = entityDataStatic.copy()
    entityData["entity"] = "SYS.NUMERO.VUELO"
    entityData["slotName"] = "entidadNumeroVuelo"

    numerovuelo = re.compile(r"[A-Z]{2}[0-9]{4}")
    numerovuelo = numerovuelo.search(texto)

    if numerovuelo != None:
        entityData["rawValue"] = numerovuelo.group()
        return entityData.copy()
    else:
        return None

def duracion(texto):
    #Static values of the entity
    entityData = entityDataStatic.copy()
    entityData["entity"] = "SYS.DURACION"
    entityData["slotName"] = "entidadDuracion"

    duracion = re.compile(r"(\s\d+)((\shoras\s)|(\sminutos\s)|(\ssegundos\s)|(\sdías\s)|(\smeses\s)|(\saños\s))")
    duracion = duracion.search(texto)

    if duracion != None:
        entityData["rawValue"] = duracion.group()
        return entityData.copy()
    else:
        return None
