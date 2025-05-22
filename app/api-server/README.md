# DeliveryDrive API Server

Простой микросервис на Go с использованием Gin framework.

## Требования

- Go 1.21 или выше
- Git

## Установка и запуск

1. Перейдите в директорию сервиса:
```bash
cd app/api-server
```

2. Установите зависимости:
```bash
go mod download
```

3. Запустите сервис:
```bash
go run main.go
```

Сервис будет доступен по адресу `http://localhost:8080`

## API Endpoints

- `GET /` - Приветственное сообщение
- `GET /api/health` - Проверка состояния сервиса

## Структура проекта

```
app/api-server/
├── main.go        # Основной файл приложения
├── go.mod         # Файл зависимостей
└── README.md      # Документация
``` 