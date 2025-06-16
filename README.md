# DeliveryDrive

This repository contains multiple FastAPI services that communicate with each other via HTTP.

## Running the services

The easiest way to start all dependencies is via `docker-compose`:

```bash
docker-compose up
```

The `orm-service` communicates with the `osrm-service` using the URL specified by the `OSRM_SERVICE_URL` environment variable. When running via `docker-compose` this is set automatically. If you run the services separately, make sure `OSRM_SERVICE_URL` points to the reachable `osrm-service` instance (by default it is exposed on port `6060`).
