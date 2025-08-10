# E-Commerce Order Processing & Aggregation Pipeline

This project simulates a real-time e-commerce order pipeline.  
It ingests order events from an SQS queue (via Localstack), processes & validates them, aggregates statistics in Redis, and exposes REST APIs via FastAPI for quick retrieval of user and global order stats.

## 📌 Features
- **Order ingestion** from AWS SQS (simulated with Localstack)
- **Validation & transformation** of incoming orders:
  - Required fields (`order_id`, `user_id`, `order_value`)
  - Cross-check `order_value` with items' `(quantity × price_per_unit)`
- **Aggregation**:
  - Per-user stats (`order_count`, `total_spend`)
  - Global stats (`total_orders`, `total_revenue`)
- **Advanced Queries**:
  - Top N users by spend or order count
  - Date range stats
- **Logging**: Detailed logs stored in `./logs` with timestamps
- **Docker Compose**: One command starts all services
- **Sample data script**: `populate_sqs.py` sends bulk valid/invalid orders to SQS

---

## 🛠️ Tech Stack
- **Python 3.11**
- **FastAPI** — API layer
- **Redis** — In-memory data store
- **AWS SQS (Localstack)** — Message queue
- **Docker Compose** — Container orchestration
- **boto3** — AWS SDK for Python
- **redis-py** — Redis client
- **Logging** — Python built-in `logging` module

---

## 📂 Project Structure
```
ecommerce-order-pipeline/
│
├── docker-compose.yml
├── logs/                 # Mounted container logs
├── scripts/
│   └── populate_sqs.py   # Sends sample orders to SQS
├── web/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py           # FastAPI app
└── worker/
    ├── Dockerfile
    ├── requirements.txt
    └── worker.py         # SQS consumer & Redis updater
```

---

## 🚀 Getting Started

### 1️⃣ Clone the Repository
```bash
git clone git@github.com:<your-username>/ecommerce-order-pipeline.git
cd ecommerce-order-pipeline
```

### 2️⃣ Start Services

```bash
docker compose up --build
```

This starts:
- Localstack (SQS)
- Redis
- FastAPI app (`localhost:8000`)
- Worker (SQS → Redis)

### 3️⃣ Create SQS Queue (Optional)

The system will automatically create the queue if it doesn't exist, but you can create it manually:

```bash
docker exec -it localstack awslocal sqs create-queue --queue-name orders
```

### 4️⃣ Populate Queue with Sample Orders

```bash
pip install boto3
python scripts/populate_sqs.py
```

---

## 📡 API Endpoints

### **1. User Stats**
```
GET /users/{user_id}/stats
```

**Example:**
```bash
curl http://localhost:8000/users/U123/stats
```

**Response:**
```json
{
  "user_id": "U123",
  "order_count": 3,
  "total_spend": 299.99
}
```

---

### **2. Global Stats**
```
GET /stats/global
```

**Example:**
```bash
curl http://localhost:8000/stats/global
```

**Response:**
```json
{
  "total_orders": 12,
  "total_revenue": 1200.50
}
```

---

### **3. Top N Spenders**
```
GET /stats/top-spenders?limit=3
```

### **4. Top N Buyers**
```
GET /stats/top-buyers?limit=3
```

### **5. Date Range Stats**
```
GET /stats/by-date?start_date=2025-08-01&end_date=2025-08-09
```

---

### **6. Health Check**
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "redis": "connected",
  "redis_latency_ms": 1.23,
  "timestamp": 1673875200.0
}
```

### **7. Metrics**
```
GET /metrics
```

**Response:**
```json
{
  "total_orders": 150,
  "total_revenue": 15000.00,
  "unique_users": 45,
  "average_order_value": 100.00,
  "timestamp": 1673875200.0
}
```

---

## 📝 Logging & Monitoring

- **Worker logs**: Stored in `./logs/YYYY-MM-DD.log`
- **API request logs**: Real-time logging with response times
- **Health monitoring**: `/health` endpoint for service status
- **Performance metrics**: `/metrics` endpoint for system stats
- **Configurable log levels**: Set via `LOG_LEVEL` environment variable

---

## ⚙️ Configuration

The system supports environment-based configuration. Key variables:

```bash
# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Localstack Configuration  
LOCALSTACK_URL=http://localstack:4566
AWS_REGION=us-east-1

# SQS Configuration
QUEUE_NAME=orders

# Logging Configuration
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

---

## 🧪 Running Tests

We use `pytest` for unit and integration testing.

### Unit Tests
Run all fast tests that don’t require services:
```bash
pytest


---

## 📈 Scaling Considerations

- **Redis sharding** for very large datasets
- Use **Redis Streams** or **Kafka** for high-throughput ingestion
- Move historical aggregates to a **persistent DB** (e.g., PostgreSQL, BigQuery)
- Maintain **time-series keys** for efficient date-range queries

---

## 📊 Design Diagram

```mermaid
flowchart LR
    subgraph Producer
        P1[populate_sqs.py<br>(sample data)]
        P2[CLI via awslocal]
    end

    subgraph Localstack_SQS
        SQS[SQS Queue<br>(orders)]
    end

    subgraph Consumer
        W1[Python Worker<br>(consumer.py)]
        V1[Validation & Transformation]
        L1[Logging<br>/logs/*.log]
    end

    subgraph DataStore
        R1[(Redis)]
    end

    subgraph API
        A1[FastAPI App<br>(main.py)]
        Q1[Basic Stats<br>/stats/global]
        Q2[Advanced Queries<br>/stats/top-users]
    end

    P1 --> SQS
    P2 --> SQS
    SQS --> W1
    W1 --> V1
    V1 -->|Valid Orders| R1
    V1 -->|Invalid Orders| L1
    A1 --> R1
    A1 --> Q1
    A1 --> Q2
```

---

## 📬 Author

**Pankhuri Trikha**
Data Engineer | Python | Big Data | Cloud

---