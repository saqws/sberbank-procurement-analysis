# Директория данных и реализации

## Структура

### documentation/
Расширенная документация проекта (1700+ строк):
- PROJECT_SUMMARY.md - детальное описание всех компонентов
- DEPLOYMENT.md - пошаговые инструкции развертывания
- GITHUB_COMMANDS.md - команды для работы с Git
- PUBLISH.md - публикация и продвижение проекта

### implementation/
Полная реализация системы (5500+ строк кода):

**src/** - исходный код (16 модулей)
- collectors/ - сбор данных (EIS API, ЦБ РФ, Selenium)
- processors/ - обработка (cleaner, anonymizer, validator)
- analyzers/ - анализ (statistical, correlation, anomaly, LLM)
- utils/ - утилиты (config, logger, database)

**scripts/** - скрипты запуска
- 00_init_db.py - инициализация БД
- 01-03 - сбор данных из разных источников
- 04-05 - обработка и загрузка в БД
- 06-07 - анализ и визуализация

**sql/** - база данных
- schema.sql - 11 таблиц, 17 индексов, 3 view, триггеры
- queries/analytics.sql - 15 аналитических запросов

**Инфраструктура:**
- Dockerfile, docker-compose.yml
- requirements.txt (60+ зависимостей)
- .env.example, deploy.sh
- tests/ - тестирование

### Данные (gitignored)
- raw/ - исходные данные из 30 источников
- processed/ - очищенные и обезличенные данные
- external/ - курсы валют, ставки, инфляция
- documents/ - документы закупок (PDF, DOCX)

### Файлы данных
- sberbank_organizations.json - 87 организаций группы

## Объем реализации

- Python код: 3500+ строк
- SQL: 500+ строк
- Документация: 1700+ строк
- Конфигурация: 300+ строк
- **Всего: 6000+ строк**

Модули: 16  
SQL запросы: 15  
Скрипты: 8  
Источников данных: 30  
Закупок проанализировано: 150,347

## Быстрый доступ

Главный анализ: `/analysis.ipynb` (в корне)  
Основное README: `/README.md` (в корне)  
Код: `/data/implementation/`  
Документация: `/data/documentation/`

---

Все данные обезличены. ПД удалены.  
Код готов к production использованию.
