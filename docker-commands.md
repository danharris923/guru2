# Docker Commands for SavingsGuru

## Quick Start
```bash
# Build and run with docker-compose (recommended)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

## Manual Docker Commands
```bash
# Build the Docker image
docker build -t savingsguru .

# Run the container
docker run -d -p 3000:80 --name savingsguru savingsguru

# Stop the container
docker stop savingsguru

# Remove the container
docker rm savingsguru

# View logs
docker logs savingsguru
```

## Production Deployment
```bash
# Build for production
docker-compose -f docker-compose.yml up -d

# Scale if needed
docker-compose up -d --scale savingsguru-web=3

# Update the app
docker-compose pull
docker-compose up -d --force-recreate
```

## Useful Commands
```bash
# Enter the container shell
docker exec -it savingsguru sh

# Check container health
docker inspect --format='{{.State.Health.Status}}' savingsguru

# View container stats
docker stats savingsguru

# Rebuild without cache
docker build --no-cache -t savingsguru .
```

## Environment Variables
```bash
# Run with custom port
docker run -d -p 8080:80 -e NODE_ENV=production savingsguru
```

## Access Points
- **App**: http://localhost:3000
- **Health Check**: http://localhost:3000/health