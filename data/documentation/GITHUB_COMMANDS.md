# Команды для выгрузки проекта на GitHub

## 1. Инициализация Git репозитория

```bash
cd sberbank-procurement-analysis
git init
```

## 2. Создание .gitignore (уже есть в проекте)

Файл `.gitignore` уже настроен для исключения:
- Данных (data/*)
- Виртуального окружения
- Секретов (.env)
- Логов
- Временных файлов

## 3. Первый коммит

```bash
# Добавить все файлы
git add .

# Создать первый коммит
git commit -m "Initial commit: Sberbank procurement analysis project

- Complete project structure
- Data collectors: EIS API, CBR API, Selenium scraper
- Data processors: cleaner, anonymizer
- Analyzers: statistical, correlation, anomaly detection, LLM
- PostgreSQL schema with indexes and views
- Docker configuration
- Comprehensive README with methodology
- Analytical SQL queries (15+)
- Configuration and utilities"
```

## 4. Создание репозитория на GitHub

Вариант 1 - через веб-интерфейс:
1. Перейти на https://github.com/new
2. Создать репозиторий `sberbank-procurement-analysis`
3. НЕ инициализировать с README, .gitignore или лицензией

Вариант 2 - через GitHub CLI:
```bash
gh repo create sberbank-procurement-analysis --public --source=. --remote=origin
```

## 5. Подключение удалённого репозитория

```bash
# Добавить remote
git remote add origin https://github.com/YOUR_USERNAME/sberbank-procurement-analysis.git

# Или через SSH
git remote add origin git@github.com:YOUR_USERNAME/sberbank-procurement-analysis.git
```

## 6. Отправка кода на GitHub

```bash
# Создать и переключиться на main ветку
git branch -M main

# Отправить код
git push -u origin main
```

## 7. Создание дополнительных веток (опционально)

```bash
# Ветка для разработки
git checkout -b development
git push -u origin development

# Ветка для документации
git checkout -b docs
git push -u origin docs
```

## 8. Создание релиза (после завершения проекта)

```bash
# Создать тег
git tag -a v1.0.0 -m "Release v1.0.0: Complete procurement analysis system"

# Отправить тег
git push origin v1.0.0
```

Или через GitHub CLI:
```bash
gh release create v1.0.0 --title "v1.0.0: Complete Analysis System" --notes "
## Features
- 25+ data sources integration
- Statistical and correlation analysis
- Anomaly detection (IQR, Isolation Forest)
- LLM-powered insights
- 20+ visualizations
- Comprehensive documentation

## Data Coverage
- Period: 2024-2025
- Organizations: 87 Sberbank group entities
- Procurements: 150,000+
"
```

## 9. Настройка GitHub Pages (для документации)

```bash
# Создать ветку gh-pages
git checkout --orphan gh-pages
git reset --hard
echo "<h1>Sberbank Procurement Analysis</h1>" > index.html
git add index.html
git commit -m "Initialize GitHub Pages"
git push origin gh-pages

# Вернуться на main
git checkout main
```

Затем в настройках репозитория: Settings → Pages → Source → gh-pages branch

## 10. Добавление соавторов

```bash
# В веб-интерфейсе GitHub:
# Settings → Manage access → Invite a collaborator
```

## 11. Создание Issues и Project Board

```bash
# Создать issue через CLI
gh issue create --title "Add more ETP sources" --body "Integrate 10 additional commercial platforms"

# Создать project
gh project create --title "Procurement Analysis Development" --body "Track development progress"
```

## 12. Настройка GitHub Actions (CI/CD)

Создать `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest tests/
```

## 13. Защита main ветки

В Settings → Branches → Branch protection rules:
-  Require pull request before merging
-  Require status checks to pass
-  Require branches to be up to date

## 14. Добавление badges в README

Добавить в начало README.md:

```markdown
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
```

## 15. Полезные команды для работы

```bash
# Проверить статус
git status

# Посмотреть историю
git log --oneline --graph

# Создать новую ветку
git checkout -b feature/new-feature

# Обновить локальную копию
git pull origin main

# Посмотреть изменения
git diff

# Отменить изменения в файле
git checkout -- filename

# Создать stash (сохранить незакоммиченные изменения)
git stash
git stash pop

# Посмотреть удалённые репозитории
git remote -v

# Клонировать репозиторий (для других пользователей)
git clone https://github.com/YOUR_USERNAME/sberbank-procurement-analysis.git
```

## 16. Рекомендуемая структура коммитов

```bash
# Feature
git commit -m "feat: add correlation analysis with USD rate"

# Fix
git commit -m "fix: correct IQR anomaly detection threshold"

# Documentation
git commit -m "docs: update README with installation instructions"

# Refactor
git commit -m "refactor: optimize SQL queries for performance"

# Test
git commit -m "test: add unit tests for anonymizer module"
```

## Проверка перед публикацией

- [ ] Удалены все секреты и API ключи
- [ ] .env файл в .gitignore
- [ ] Реальные данные не попали в репозиторий
- [ ] README актуален и полон
- [ ] Лицензия добавлена (MIT/Apache)
- [ ] requirements.txt содержит все зависимости
- [ ] Документация написана
- [ ] Код прокомментирован

## Готово!

Ваш проект теперь на GitHub и доступен для:
- Совместной работы
- Code review
- CI/CD
- Публикации результатов
