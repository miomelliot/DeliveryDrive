# DeliveryDrive

This repository contains multiple FastAPI services that communicate with each other via HTTP.

## Running the services

The easiest way to start all dependencies is via `docker-compose`:

```bash
docker-compose up
```

The `orm-service` communicates with the `osrm-service` using the URL specified by the `OSRM_SERVICE_URL` environment variable. When running via `docker-compose` this is set automatically. If you run the services separately, make sure `OSRM_SERVICE_URL` points to the reachable `osrm-service` instance (by default it is exposed on port `6060`).

## Кэширование матрицы OSRM

`osrm-service` сохраняет рассчитанные расстояния между всеми адресами партии в Neo4j.
При первом обращении формируется полный запрос к `/table` OSRM с параметрами
`sources=all&destinations=all&annotations=distance`. Если адресов больше ста,
запрос разбивается на части и итоговая матрица собирается из частичных ответов.
Результат кэшируется как ориентированный граф `(:Address)-[:DISTANCE]->(:Address)`;
всего создаётся `N × (N-1)` рёбер. Повторные вызовы используют уже сохранённые
значения.
