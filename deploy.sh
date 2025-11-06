#!/bin/bash

# Script de deployment para Digital Ocean Ubuntu
echo "🚀 Iniciando deployment en Digital Ocean..."

# Crear directorio para logs si no existe
mkdir -p logs

# Detener contenedores existentes
echo "⏹️  Deteniendo contenedores existentes..."
docker-compose down

# Construir y levantar contenedores
echo "🔨 Construyendo e iniciando contenedores..."
docker-compose up -d --build

# Mostrar estado de los contenedores
echo "📊 Estado de los contenedores:"
docker-compose ps

# Mostrar logs en tiempo real
echo "📝 Logs de la aplicación:"
docker-compose logs -f app