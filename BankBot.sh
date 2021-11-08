#!/bin/bash
echo Valor de la variable de entorno
read env
echo Nombre de usuario administrador
read userName
echo Contraseña de usuario administrador
read userPwd
echo $env $userName $userPwd
echo CREACION DE CLUSTER
aws rds create-db-cluster \
--database-name BankBot$env \
--db-cluster-identifier BankBot$env \
--engine aurora-mysql \
--engine-version 5.7 \
--master-username $userName \
--master-user-password $userPwd \
--engine-mode serverless \
--scaling-configuration MinCapacity=1,MaxCapacity=1,AutoPause=true,SecondsUntilAutoPause=1000 \
--enable-http-endpoint \
--profile dev
echo Copia y pega lo que se te pide
echo DatabaseName
read BDName
echo Endpoint
read host
echo Port
read port
echo DbClusterResourceId
read clusterID
echo DBClusterArn
read arnCluster
echo CREACION DE SECRET MANAGER
aws secretsmanager create-secret \
--name "CredencialDBBankBot$env" \
--secret-string '{
    "dbInstanceIdentifier": "'$BDName'",
    "engine": "aurora-mysql",
    "host": "'$host'",
    "port": "'$port'",
    "resourceId": "'$clusterID'",
    "username": "'$userName'",
    "password": "'$userPwd'"
}' \
--profile dev
echo Copia y pega el ARN
read SecretsManager
echo CREACION DE REPOSITORIO
aws ecr create-repository \
--repository-name "snipstrainerBankBot$env" \
--image-tag-mutability IMMUTABLE \
--profile dev
echo Copia y pega el repositoryUri
read ecrLambda
echo $arnCluster $BDName $SecretsManager
echo UPDATE CLUSTER
aws rds modify-db-cluster \
--db-cluster-identifier $BDName \
--enable-http-endpoint \
--apply-immediately \
--profile dev
echo CREACION DE TABLAS EN CLUSTER
aws rds-data execute-statement \
--resource-arn $arnCluster \
--database $BDName \
--secret-arn $SecretsManager \
--sql "CREATE TABLE IF NOT EXISTS Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    lastName VARCHAR(255) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    password VARCHAR(255) NOT NULL,
    rol VARCHAR(10) NULL,
    lastState VARCHAR(255) NULL,
    position VARCHAR(255) NULL,
  	updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Dashboard boolean NULL,
    Chat boolean NULL,
    Reportes boolean NULL,
    Respuestas boolean NULL,
    MiCuenta boolean NULL,
    RecuperarPsswrd boolean NULL,
    Consultar boolean NULL,
    Nuevo boolean NULL,
    sessionId VARCHAR(255) NULL
);" \
--profile dev
aws rds-data execute-statement \
--resource-arn $arnCluster \
--database $BDName \
--secret-arn $SecretsManager \
--sql "CREATE TABLE IF NOT EXISTS Clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    lastName VARCHAR(255) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);" \
--profile dev
aws rds-data execute-statement \
--resource-arn $arnCluster \
--database $BDName \
--secret-arn $SecretsManager \
--sql "CREATE TABLE IF NOT EXISTS Conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sessionId VARCHAR(255) NULL,
    userMessage text NULL,
    lastState VARCHAR(255) NULL,
    intent VARCHAR(255) NULL,
    lastQuestion int(11) NULL,
    botMessage text NULL,
    startConversation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    endConversation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent VARCHAR(255) NULL
);" \
--profile dev
aws rds-data execute-statement \
--resource-arn $arnCluster \
--database $BDName \
--secret-arn $SecretsManager \
--sql "CREATE TABLE IF NOT EXISTS Reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reportId VARCHAR(255) NOT NULL,
    agent VARCHAR(255) NOT NULL,
    comment text NOT NULL,
    priorityAttention boolean NULL,
    processStatus VARCHAR(255) NOT NULL,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);" \
--profile dev
echo Variables que se deben pasar al buildspec.yml
echo SecretManager: $SecretsManager
echo ClusterArn: $arnCluster
echo DBTableName: $BDName
echo ecrLambda: $ecrLambda