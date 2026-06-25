# Deployment & Setup Guide

##  Развертывание проекта

### Системные требования

- **OS**: Linux/macOS/Windows with WSL2
- **Python**: 3.11 или выше
- **PostgreSQL**: 15 или выше
- **RAM**: минимум 8GB (рекомендуется 16GB)
- **Disk**: минимум 10GB свободного места
- **Docker**: 20.10+ (опционально)

### Вариант 1: Локальная установка

#### Шаг 1: Клонирование репозитория
```bash
git clone https://github.com/YOUR_USERNAME/sberbank-procurement-analysis.git
cd sberbank-procurement-analysis
```

#### Шаг 2: Настройка Python окружения
```bash
# Создать виртуальное окружение
python3.11 -m venv venv

# Активировать
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

#### Шаг 3: Установка зависимостей
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Шаг 4: Настройка переменных окружения
```bash
cp .env.example .env
nano .env  # или любой другой редактор
```

Обязательно укажите:
- `DATABASE_URL` - строка подключения к PostgreSQL
- `EIS_API_KEY` - ключ для ЕИС API (если требуется)
- `OPENAI_API_KEY` - ключ OpenAI для LLM анализа

#### Шаг 5: Запуск PostgreSQL

**Вариант A: Через Docker**
```bash
docker-compose up -d postgres
```

**Вариант B: Локальная установка**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-15

# macOS
brew install postgresql@15

# Создать базу данных
createdb procurement
```

#### Шаг 6: Инициализация схемы БД
```bash
python scripts/00_init_db.py
```

### Вариант 2: Docker (рекомендуется для production)

```bash
# Собрать образ
docker-compose build

# Запустить все сервисы
docker-compose up -d

# Инициализировать БД
docker-compose exec jupyter python scripts/00_init_db.py
```

##  Сбор данных

### Полный pipeline

```bash
# 1. Сбор из ЕИС (основной источник)
python scripts/01_collect_eis.py --start-date 2024-01-01 --end-date 2025-12-31

# 2. Сбор из коммерческих ЭТП
python scripts/02_collect_commercial.py

# 3. Сбор внешних данных (курсы, ставки)
python scripts/03_collect_external.py

# 4. Обработка и обезличивание
python scripts/04_process_and_anonymize.py

# 5. Загрузка в БД
python scripts/05_load_to_db.py

# 6. Аналитические расчеты
python scripts/06_analysis.py

# 7. Генерация визуализаций
python scripts/07_visualize.py
```

### Частичный запуск

Для тестирования или работы с подмножеством данных:

```bash
# Только один месяц
python scripts/01_collect_eis.py --start-date 2024-01-01 --end-date 2024-01-31

# Пропустить коммерческие ЭТП
# Закомментировать вызов в основном pipeline

# Использовать существующие данные
python scripts/05_load_to_db.py --skip-collection
```

## 📓 Jupyter Notebook

### Локальный запуск

```bash
jupyter notebook notebooks/analysis.ipynb
```

### Через Docker

```bash
docker-compose up jupyter
# Открыть http://localhost:8888
# Token будет в логах: docker-compose logs jupyter
```

### Структура notebook

1. **Setup & Data Loading** - загрузка данных из БД
2. **Exploratory Analysis** - первичный анализ
3. **Statistical Tests** - проверка гипотез
4. **Correlation Analysis** - корреляции с внешними факторами
5. **Anomaly Detection** - выявление аномалий
6. **Visualizations** - все 25+ графиков
7. **LLM Insights** - анализ через GPT-4
8. **Conclusions** - итоговые выводы

## 🧪 Тестирование

```bash
# Запустить все тесты
pytest tests/

# С покрытием
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Конкретный модуль
pytest tests/test_collectors.py -v

# С логами
pytest tests/ -s --log-cli-level=INFO
```

##  Проверка работоспособности

### Health Check

```bash
# 1. Проверить подключение к БД
python -c "from src.utils.db import test_connection; print('OK' if test_connection() else 'FAIL')"

# 2. Проверить конфигурацию
python -c "from src.utils.config import settings; print(settings.database_url)"

# 3. Проверить данные в БД
psql $DATABASE_URL -c "SELECT COUNT(*) FROM procurements;"
```

### Troubleshooting

**Проблема**: Database connection failed
```bash
# Решение:
# 1. Проверить, запущен ли PostgreSQL
docker-compose ps
# 2. Проверить DATABASE_URL в .env
# 3. Проверить файрвол
```

**Проблема**: API rate limit exceeded
```bash
# Решение:
# 1. Увеличить EIS_REQUESTS_PER_MINUTE в .env
# 2. Добавить задержки в коде
# 3. Использовать кеш
```

**Проблема**: Out of memory
```bash
# Решение:
# 1. Обрабатывать данные батчами
# 2. Использовать chunked reading pandas
# 3. Увеличить RAM или использовать swap
```

##  Мониторинг

### Логи

```bash
# Просмотр логов
tail -f logs/procurement.log

# Поиск ошибок
grep ERROR logs/procurement.log

# Статистика по уровням
grep -c INFO logs/procurement.log
grep -c ERROR logs/procurement.log
```

### Метрики

```bash
# Количество записей
psql $DATABASE_URL -c "
SELECT 
    source,
    COUNT(*) as count,
    AVG(data_quality_score) as avg_quality
FROM procurements
GROUP BY source;
"

# Статус сбора
psql $DATABASE_URL -c "
SELECT * FROM collection_log 
ORDER BY created_at DESC 
LIMIT 10;
"
```

##  Обновление данных

### Регулярные обновления

Добавить в crontab для ежедневного обновления:

```bash
# Открыть crontab
crontab -e

# Добавить задачу (каждый день в 2:00)
0 2 * * * cd /path/to/sberbank-procurement-analysis && ./scripts/daily_update.sh
```

### Incremental updates

```python
# В scripts/01_collect_eis.py
# Собирать только новые данные с последней даты

from datetime import datetime, timedelta

last_date = get_last_procurement_date()
start_date = last_date + timedelta(days=1)
end_date = datetime.now().date()
```

##  Безопасность

### Checklist перед production

- [ ] Все API ключи в .env, не в коде
- [ ] .env добавлен в .gitignore
- [ ] Реальные данные не в git
- [ ] PostgreSQL с паролем
- [ ] Firewall настроен
- [ ] SSL для БД соединения
- [ ] Обезличивание ПД работает
- [ ] Логи не содержат sensitive data
- [ ] Backup настроен

### Backup

```bash
# Backup БД
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Backup данных
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/

# Восстановление
psql $DATABASE_URL < backup_20250625.sql
```

##  Performance Tuning

### PostgreSQL оптимизация

```sql
-- Analyze таблицы для обновления статистики
ANALYZE procurements;

-- Rebuild индексов
REINDEX TABLE procurements;

-- Vacuum для очистки
VACUUM ANALYZE;
```

### Python оптимизация

```python
# Использовать chunked processing
for chunk in pd.read_csv('large_file.csv', chunksize=10000):
    process_chunk(chunk)

# Multiprocessing для CPU-bound задач
from multiprocessing import Pool
with Pool(4) as p:
    results = p.map(process_function, data_list)
```

##  Production checklist

- [ ] Все тесты проходят
- [ ] Логирование настроено
- [ ] Мониторинг работает
- [ ] Backup автоматизирован
- [ ] Документация обновлена
- [ ] Secrets в безопасности
- [ ] Performance протестирован
- [ ] Error handling robust
- [ ] Rollback plan готов
- [ ] Team обучена

---

**Note**: Для production использования рекомендуется дополнительно настроить:
- Reverse proxy (nginx)
- Process manager (supervisord/systemd)
- Log aggregation (ELK/Loki)
- Metrics (Prometheus/Grafana)
- Alerting (PagerDuty/Opsgenie)
