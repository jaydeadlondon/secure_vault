# 🔒 SecureVault: Encrypted Cloud Storage

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-S3-c72c48?logo=minio&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Security](https://img.shields.io/badge/AES--256-CTR-green)

**SecureVault** — это защищенное облачное хранилище файлов (аналог Dropbox/Google Drive) с архитектурой **Zero-Knowledge**.

Главная особенность: **Потоковое шифрование (Streaming Encryption)**. Файлы шифруются чанками в оперативной памяти перед отправкой в S3. Сервер никогда не сохраняет незашифрованные данные на диск и потребляет минимум RAM даже при загрузке файлов объемом 100ГБ.

---

## 🚀 Ключевые возможности

### 🔐 End-to-End Security
- **Upload Pipeline:** `Client Stream` → `AES-256-CTR Encryptor` → `S3 Multipart Upload`
- **Download Pipeline:** `S3 Stream` → `AES-256-CTR Decryptor` → `Client Stream`
- Уникальные ключи шифрования и nonce генерируются для каждого файла

### ⚡ High Performance (Async I/O)
- Использование **aioboto3** для полностью асинхронного взаимодействия с объектным хранилищем (MinIO)
- Отсутствие блокирующих операций ввода-вывода позволяет обрабатывать сотни одновременных загрузок

### 👤 Privacy
- Система аутентификации JWT
- Изоляция данных: пользователь имеет доступ только к своим файлам
- Полное удаление данных (из БД и из S3) по запросу владельца

---

## 🛠 Технологический стек

- **Backend:** Python 3.11, FastAPI
- **Database:** PostgreSQL 15, SQLAlchemy 2.0 (Async)
- **Object Storage:** MinIO (S3 Compatible)
- **Cryptography:** `cryptography`
- **Migrations:** Alembic
- **Containerization:** Docker & Docker Compose

---

## 📦 Установка и Запуск

### 1. Настройка окружения

Создайте файл `.env`:

```ini
PROJECT_NAME=SecureVault
POSTGRES_SERVER=db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=vault_db
POSTGRES_PORT=5432
SECRET_KEY=secret_key
ALGORITHM=HS256

# MinIO Config
S3_ENDPOINT_URL=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=secure-files
```

### 2. Запуск контейнеров

```bash
docker-compose up -d --build
```

### 3. Инициализация S3

1. Перейдите в консоль MinIO: [http://localhost:9001](http://localhost:9001)
2. Логин/Пароль: `minioadmin` / `minioadmin`
3. Создайте Bucket с именем `secure-files`

### 4. Миграции БД

```bash
docker-compose exec app alembic upgrade head
```

---

## 📖 API Документация

Swagger UI доступен по адресу: [http://localhost:8000/docs](http://localhost:8000/docs)

### Основные эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| `POST` | `/auth/register` | Регистрация пользователя |
| `POST` | `/auth/login` | Получение JWT токена |
| `POST` | `/files/upload` | Потоковая загрузка с шифрованием |
| `GET` | `/files/{id}/download` | Потоковое скачивание с дешифровкой |
| `GET` | `/files` | Список моих файлов |
| `DELETE` | `/files/{id}` | Удаление файла |

---

## 🕵️‍♂️ Тест безопасности (Proof of Concept)

Вы можете убедиться, что сервер не хранит оригинальные файлы:

1. Загрузите изображение через API (`/files/upload`)
2. Скачайте тот же файл напрямую через админку MinIO
3. Попробуйте открыть его — файл будет поврежден/нечитаем, так как это зашифрованный бинарный массив
4. Скачайте файл через API (`/files/{id}/download`) — он откроется корректно

---

## 📜 Лицензия

MIT License
