# Данные об авторе

**Фамилия Имя Отчество:** Дубенец Даниил Иванович 
**Логин:** dubenec_di_23  
**Курс / семестр:** 3 курс / 6 семестр  
**Специальность:** Кибербезопасность  
**Вид проекта:** курсовая работа  

---

# Название проекта

Демонстрационный стенд: деанонимизация через clickjacking и browser fingerprinting

Программа реализует учебный стенд для исследования техник деанонимизации пользователей в браузере. Включает два сайта-ловушки (классический clickjacking и drag-and-drop jacking), сервер сбора отпечатков браузера и алгоритм стыковки профилей по fingerprint-данным.

---

# Требования

- Python 3.9+
- pip

---

## Как запустить

### 1. Клонируйте репозиторий

```bash
git https://github.com/Piwmaster228/clickjack.git
cd clickjack
```

### 2. Создайте и активируйте виртуальное окружение

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

### 4. Запустите серверы (три отдельных терминала)

**Терминал 1 — сервер трекинга**
```bash
cd stand/server
python app.py
```

**Терминал 2 — Сайт А**
```bash
cd stand/site_a
python server.py
```

**Терминал 3 — Сайт Б**
```bash
cd stand/site_b
python server.py
```

### 5. Откройте в браузере

| Адрес | Что открывается |
|-------|----------------|
| `http://localhost:5000` | Сайт А — новостной блог |
| `http://localhost:5001` | Сайт Б — викторина |
| `http://localhost:5002/admin` | Панель администратора |

---

## Структура файлов

```
stand/
├── site_a/
│   ├── index.html      — новостной блог с ловушкой
│   ├── target.html     — цель iframe (классический clickjacking)
│   └── server.py       — HTTP-сервер (порт 5000)
├── site_b/
│   ├── index.html      — викторина с drag-and-drop ловушкой
│   ├── target.html     — цель iframe (drop jacking)
│   └── server.py       — HTTP-сервер (порт 5001)
├── server/
│   ├── app.py          — Flask-сервер трекинга
│   ├── tracking.db     — SQLite БД (создаётся автоматически)
│   └── templates/
│       └── admin.html  — панель администратора
└── README.md
```

