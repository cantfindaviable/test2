# Сервис для генерации изображений на основе брендбука
Краткая структура проекта

```
.
├── app/ - Основное FastAPI приложение (API, веб-интерфейс, аутентификация)
│ ├── auth/ - Модуль аутентификации и авторизации
│ ├── database/ - Работа с базой данных
│ ├── models/ - Модели данных
│ ├── routes/ - API endpoints
│ ├── services/ - Бизнес-логика и сервисы
│ ├── tests/ - Тесты
│ └── webui/ - Веб-интерфейс на Streamlit
│
├── ml_worker/ - Сервис машинного обучения
│ ├── brandbook/ - Обработка PDF брендбуков
│ ├── llm.py - Работа с языковыми моделями
│ ├── rmq/ - Интеграция с RabbitMQ
│ └── services/ml/ - ML сервисы
│
├── nginx/ - Конфигурация веб-сервера
├── generated_images/ - Сгенерированные изображения
└── docker-compose.yaml - Конфигурация Docker
```

## Для запуска сервиса используйте docker-compose:

1. Отредактируйте файл .env в соответствии с вашими настройками
2. Запустите сервис с помощью Docker Compose:
   `docker compose up -d`

Доступы:
- API: http://localhost:8000
- Frontend: http://localhost:8501
- RabbitMQ Management: http://localhost:15672
