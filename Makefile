# Makefile для проекта QGIS Move point to next rectangle

# Переменные
PYTHON := python3
SRC_DIR := src
POETRY := poetry

# Цвета для вывода
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help format lint check test clean install run

# Помощь по командам
help:
	@echo "$(GREEN)Доступные команды:$(NC)"
	@echo "  $(YELLOW)make format$(NC)     - Форматирование кода с помощью ruff"
	@echo "  $(YELLOW)make lint$(NC)       - Проверка кода на ошибки с помощью ruff"
	@echo "  $(YELLOW)make check$(NC)      - Полная проверка (lint + format check)"
	@echo "  $(YELLOW)make fix$(NC)        - Автоматическое исправление проблем"
	@echo "  $(YELLOW)make install$(NC)    - Установка зависимостей через Poetry"
	@echo "  $(YELLOW)make run$(NC)        - Запуск скрипта с примером данных"
	@echo "  $(YELLOW)make run-help$(NC)   - Показать справку по скрипту"
	@echo "  $(YELLOW)make clean$(NC)      - Очистка временных файлов"
	@echo "  $(YELLOW)make help$(NC)       - Показать эту справку"

# Форматирование кода
format:
	@echo "$(GREEN)Форматирование кода с помощью ruff...$(NC)"
	ruff format $(SRC_DIR)/
	@echo "$(GREEN)Форматирование завершено!$(NC)"

# Проверка кода на ошибки
lint:
	@echo "$(GREEN)Проверка кода на ошибки...$(NC)"
	ruff check $(SRC_DIR)/
	@echo "$(GREEN)Проверка завершена!$(NC)"

# Полная проверка
check: lint
	@echo "$(GREEN)Проверка форматирования...$(NC)"
	ruff format --check $(SRC_DIR)/
	@echo "$(GREEN)Все проверки пройдены!$(NC)"

# Автоматическое исправление проблем
fix:
	@echo "$(GREEN)Автоматическое исправление проблем...$(NC)"
	ruff check --fix $(SRC_DIR)/
	ruff format $(SRC_DIR)/
	@echo "$(GREEN)Исправления применены!$(NC)"

# Установка зависимостей
install:
	@echo "$(GREEN)Установка зависимостей через Poetry...$(NC)"
	$(POETRY) install
	@echo "$(GREEN)Зависимости установлены!$(NC)"

# Запуск скрипта с примером данных
run:
	@if [ "$(filter --help,$(MAKECMDGOALS))" ]; then \
		echo "$(GREEN)Справка по использованию скрипта:$(NC)"; \
		/Applications/QGIS-LTR.app/Contents/MacOS/bin/python3 $(SRC_DIR)/move_point.py --help; \
	else \
		echo "$(GREEN)Запуск скрипта с данными city.gpkg...$(NC)"; \
		/Applications/QGIS-LTR.app/Contents/MacOS/bin/python3 $(SRC_DIR)/move_point.py --points data/points.gpkg --rects data/rectangles.gpkg; \
	fi

# Показать справку по скрипту
run-help:
	@echo "$(GREEN)Справка по использованию скрипта:$(NC)"
	/Applications/QGIS-LTR.app/Contents/MacOS/bin/python3 $(SRC_DIR)/move_point.py --help

# Очистка временных файлов
clean:
	@echo "$(GREEN)Очистка временных файлов...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	@echo "$(GREEN)Очистка завершена!$(NC)"
