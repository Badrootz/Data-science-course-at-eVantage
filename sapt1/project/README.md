# Loan Risk Scoring API

A production-style FastAPI application designed to predict the risk score and category of loan applications based on historical data normalization ranges and weighted risk scoring rules.

---

## Project Goal
Expose a high-performance REST API with a `POST /predict` endpoint that evaluates loan applications and classifies them into low, medium, or high risk categories.

---

## Architecture & Structure
```text
project/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI entry point, endpoints, middleware, error handlers
│   ├── models.py          # Pydantic v2 input/output data validation models
│   ├── config.py          # Configuration loader using python-dotenv
│   ├── services/
│   │   └── scoring_service.py # Core business logic (RiskScoringService)
│   └── utils/
│       └── logger.py      # Console and rotating file logging setup
├── .env                   # Environment-specific configuration
├── Dockerfile             # Multi-stage-like secure slim container definition
├── requirements.txt       # Pinned library dependencies
└── README.md              # Documentation
```

---

## Technical Specifications & Scoring Logic

### Normalization Ranges
The model scales features to a `[0.0, 1.0]` range using the min and max limits from the historical dataset (`loan_prediction_dataset.csv`):
*   **Age**: Min = 18, Max = 69
*   **Income**: Min = 20,155, Max = 149,992
*   **Credit Score**: Min = 300, Max = 849
*   **Loan Amount**: Min = 1,060, Max = 49,994

### Risk Calculation Rules
1.  **Clamping**: Inputs falling outside these historical ranges are clamped to the boundaries instead of failing.
2.  **Protective Features**: 
    *   `credit_score` is protective. Higher scores indicate lower risk. Risk is calculated as: `1 - normalized_credit_score`.
    *   `income` is protective. Higher income indicates lower risk. Risk is calculated as: `1 - normalized_income`.
    *   `age` is protective. Older age is historically associated with higher approvals (lower risk). Risk is calculated as: `1 - normalized_age`.
3.  **Risk Ratio**:
    *   `loan_to_income_ratio` = `loan_amount / income`
    *   Higher ratio represents higher risk. 
    *   Normalized using historical ratio min (`0.007977`) and max (`2.292190`).
4.  **Weights**:
    *   Credit Score: **40%**
    *   Loan-to-Income Ratio: **30%**
    *   Income: **20%**
    *   Age: **10%**
5.  **Risk Categories**:
    *   `[0.0 - 0.3]` = **LOW**
    *   `(0.3 - 0.7]` = **MEDIUM**
    *   `(0.7 - 1.0]` = **HIGH**

---

## API Endpoints

### 1. Health Check
*   **Endpoint**: `GET /health`
*   **Response**: `{"status": "healthy"}`

### 2. Predict Risk
*   **Endpoint**: `POST /predict`
*   **Request Headers**: `Content-Type: application/json`
*   **Request JSON**:
```json
{
  "age": 35,
  "income": 50000,
  "loan_amount": 10000,
  "credit_score": 680
}
```
*   **Response JSON**:
```json
{
  "risk_score": 0.37,
  "risk_category": "MEDIUM"
}
```

---

## Getting Started

### Local Setup (Without Docker)

1.  **Create a Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Server**:
    ```bash
    uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
    ```

4.  **Access Documentation**:
    *   Interactive Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
    *   Alternative ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Running with Docker

1.  **Build the Docker Image**:
    ```bash
    docker build -t loan-risk-api .
    ```

2.  **Run the Docker Container**:
    ```bash
    docker run -p 8000:8000 --name loan-risk-service loan-risk-api
    ```

3.  **Verification**:
    Verify the endpoint using `curl`:
    ```bash
    curl -X POST http://127.0.0.1:8000/predict \
         -H "Content-Type: application/json" \
         -d '{"age": 35, "income": 50000, "loan_amount": 10000, "credit_score": 680}'
    ```
