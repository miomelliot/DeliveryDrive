package main

import (
	"net/http"
)

type Response struct {
	Message string `json:"message"`
}

func main() {
	// Создаем новый роутер Gin
	router := gin.Default()

	// Определяем маршруты
	router.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, Response{
			Message: "Welcome to DeliveryDrive API",
		})
	})

	// Группа API маршрутов
	api := router.Group("/api")
	{
		api.GET("/health", func(c *gin.Context) {
			c.JSON(http.StatusOK, Response{
				Message: "Service is healthy",
			})
		})
	}

	// Запускаем сервер на порту 8080
	router.Run(":8080")
} 