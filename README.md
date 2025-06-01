# **KHWARIZMI**

## **Overview**
KHWARIZMI: From Thought to Vision. Our system transforms your natural language prompts into comprehensive reports with data visualizations, SQL queries, and textual explanations - turning your analytical thoughts into visual insights.

---

## **Demo Video**

[Click here to watch the demo on Google Drive](https://drive.google.com/file/d/115j5jt2Ap34fEnMDd9fmzRI5LlRPpda_/view?usp=drive_link)

---

## **Agents**
1. **Reformulate Intent Agent** - Refines user queries
2. **Intent to Query Agent** - Generates SQL from natural language
3. **Query to Plots Agent** - Creates visualizations from query results
4. **API to Report Agent** - Assembles the final HTML report

---

## **Tech Stack**
- FastAPI microservices
- PostgreSQL database
- Docker containers
- MinIO for chart storage
- LangChain and OpenAI

---

## **Project Architecture**
![project_architecture](docs/architecture-diagram-khwarizmi.png)

---

## **Setup**

### Prerequisites

- Docker and Docker Compose
- OpenAI API key
- Python 3.10+ (for local development)

### Environment

Create a `.env` file:
```
OPENAI_API_KEY=your_openai_api_key
POSTGRES_URI=postgresql://postgres:postgres@db:5432/northwind
MINIO_USRER=minioadmin
MINIO_PWD=minioadmin
MINIO_ENDPOINT=http://minio:9000
```

> **Note:** You should have the `psql` client installed beforehand.  
> - **macOS:** `brew install postgresql`  
> - **Linux (Debian/Ubuntu):** `sudo apt install postgresql-client`  
> - **Windows:** Download from the [official PostgreSQL site](https://www.postgresql.org/download/windows/) and choose the "psql" tool during installation.


### Running

With Docker:
```bash
docker-compose up --build
```
---

## Usage

Once the containers are up, open your browser and navigate to:

Website: http://localhost:3000
Hosted: http://34.55.56.171:3000

The frontend React app will be available there.

---

## **Example Queries**

- "Top 10 best-selling products by quantity sold"
- "Total sales by customer for top 10 customers"

---

## **Acknowledgments**

Built by Team KHWARIZMI during the Aalto AI Hackathon 2025. Special thanks to all team members and mentors for their contributions.
