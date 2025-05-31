# Chinook Database Quick Start Guide

## Prerequisites
- Docker Desktop installed and running

## Steps to View Data

1. Start PostgreSQL container:
```bash
docker compose up -d postgres2
```

2. Import the database (if not already done):
```bash
docker cp db-netflix/Chinook_PostgreSql.sql aaltoai-hackathon-postgres2-1:/tmp/
docker exec -it aaltoai-hackathon-postgres2-1 psql -U postgres -d netflixdb -f /tmp/Chinook_PostgreSql.sql
```

3. View available tables:
```bash
docker exec -it aaltoai-hackathon-postgres2-1 psql -U postgres -d chinook -c "\dt"
```

## Example Queries

1. View all artists:
```bash
docker exec -it aaltoai-hackathon-postgres2-1 psql -U postgres -d chinook -c "SELECT * FROM artist;"
```

2. View all albums:
```bash
docker exec -it aaltoai-hackathon-postgres2-1 psql -U postgres -d chinook -c "SELECT * FROM album;"
```

3. View tracks with their artists and albums:
```bash
docker exec -it aaltoai-hackathon-postgres2-1 psql -U postgres -d chinook -c "SELECT t.name as track_name, a.title as album_title, ar.name as artist_name FROM track t JOIN album a ON t.album_id = a.album_id JOIN artist ar ON a.artist_id = ar.artist_id LIMIT 5;"
```

## Database Connection Details
- Host: localhost
- Port: 5432
- Database: chinook
- Username: postgres
- Password: postgres 