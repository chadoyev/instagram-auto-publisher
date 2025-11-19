# Instagram Auto Publisher - Makefile
# Удобные команды для разработки и развёртывания

.PHONY: help setup install run docker-build docker-up docker-down docker-restart docker-logs clean test

# Цвета для вывода
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Показать справку
	@echo "$(BLUE)Instagram Auto Publisher - Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

setup: ## Первоначальная настройка (создание .env и authorize.json)
	@echo "$(YELLOW)🔧 Настройка проекта...$(NC)"
	@if [ ! -f .env ]; then \
		cp env.example.txt .env; \
		echo "$(GREEN)✅ Создан файл .env - заполните его!$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ Файл .env уже существует$(NC)"; \
	fi
	@echo "$(BLUE)📱 Настройка Instagram сессии:$(NC)"
	@python setup_instagram.py

install: ## Установить зависимости
	@echo "$(YELLOW)📦 Установка зависимостей...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✅ Зависимости установлены$(NC)"

run: ## Запустить приложение локально
	@echo "$(YELLOW)🚀 Запуск приложения...$(NC)"
	python app.py

docker-build: ## Собрать Docker образ
	@echo "$(YELLOW)🐳 Сборка Docker образа...$(NC)"
	docker-compose build
	@echo "$(GREEN)✅ Образ собран$(NC)"

docker-up: ## Запустить в Docker (detached mode)
	@echo "$(YELLOW)🐳 Запуск контейнера...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ Контейнер запущен$(NC)"
	@echo "$(BLUE)📋 Просмотр логов: make docker-logs$(NC)"

docker-down: ## Остановить Docker контейнер
	@echo "$(YELLOW)🛑 Остановка контейнера...$(NC)"
	docker-compose down
	@echo "$(GREEN)✅ Контейнер остановлен$(NC)"

docker-restart: ## Перезапустить Docker контейнер
	@echo "$(YELLOW)🔄 Перезапуск контейнера...$(NC)"
	docker-compose restart
	@echo "$(GREEN)✅ Контейнер перезапущен$(NC)"

docker-logs: ## Показать логи Docker контейнера
	@echo "$(BLUE)📋 Логи контейнера (Ctrl+C для выхода):$(NC)"
	docker-compose logs -f

docker-rebuild: ## Пересобрать и перезапустить Docker
	@echo "$(YELLOW)🔄 Пересборка и перезапуск...$(NC)"
	docker-compose down
	docker-compose up -d --build
	@echo "$(GREEN)✅ Контейнер пересобран и запущен$(NC)"

clean: ## Очистить временные файлы и кэши
	@echo "$(YELLOW)🧹 Очистка...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Очистка завершена$(NC)"

backup: ## Создать бэкап базы данных и сессии
	@echo "$(YELLOW)💾 Создание бэкапа...$(NC)"
	@mkdir -p backups
	@if [ -f db.db ]; then \
		cp db.db backups/db_$$(date +%Y%m%d_%H%M%S).db; \
		echo "$(GREEN)✅ База данных сохранена$(NC)"; \
	fi
	@if [ -f authorize.json ]; then \
		cp authorize.json backups/authorize_$$(date +%Y%m%d_%H%M%S).json; \
		echo "$(GREEN)✅ Сессия Instagram сохранена$(NC)"; \
	fi
	@echo "$(BLUE)📁 Бэкапы в директории: ./backups/$(NC)"

test: ## Запустить тесты (если есть)
	@echo "$(YELLOW)🧪 Запуск тестов...$(NC)"
	@echo "$(RED)⚠️ Тесты пока не реализованы$(NC)"

status: ## Показать статус Docker контейнера
	@echo "$(BLUE)📊 Статус контейнера:$(NC)"
	@docker-compose ps

shell: ## Открыть shell в Docker контейнере
	@echo "$(BLUE)🐚 Открытие shell в контейнере...$(NC)"
	docker-compose exec instagram-bot /bin/bash

env-check: ## Проверить .env файл
	@echo "$(BLUE)🔍 Проверка .env файла:$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN)✅ Файл .env существует$(NC)"; \
		python -c "from src.config import Config; Config.validate(); print('$(GREEN)✅ Конфигурация валидна$(NC)')" 2>&1 || echo "$(RED)❌ Ошибка конфигурации$(NC)"; \
	else \
		echo "$(RED)❌ Файл .env не найден! Запустите: make setup$(NC)"; \
	fi

# Алиасы для удобства
start: docker-up
stop: docker-down
restart: docker-restart
logs: docker-logs
build: docker-build

