#!/bin/bash
# Скрипт для просмотра логов

echo "📋 Логи Instagram Auto Publisher:"
echo "=================================="
docker-compose logs -f --tail=100

