import time
import traceback
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.models import LoanApplication, RiskPrediction
from app.services.scoring_service import RiskScoringService
from app.utils.logger import get_logger

logger = get_logger("app.main")

app = FastAPI(
    title="Loan Risk Scoring API",
    description=(
        "Production-style API for calculating loan application risk scores. "
        "Normalizes applicant details based on historical metrics and produces "
        "a weighted risk category classification."
    ),
    version="1.0.0"
)

scoring_service = RiskScoringService()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    method = request.method
    path = request.url.path
    logger.info(f"Incoming request: {method} {path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"Completed request: {method} {path} | "
            f"Status: {response.status_code} | Duration: {process_time:.4f}s"
        )
        return response
    except Exception as exc:
        process_time = time.time() - start_time
        logger.error(
            f"Failed request: {method} {path} | "
            f"Duration: {process_time:.4f}s | Error: {str(exc)}"
        )
        raise exc

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.critical(
        f"Unhandled application exception on {request.method} {request.url.path}: {str(exc)}\n"
        f"{traceback.format_exc()}"
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred. Please check application logs."}
    )

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify service status.
    """
    logger.debug("Health check endpoint hit.")
    return {"status": "healthy"}

@app.post("/predict", response_model=RiskPrediction, status_code=status.HTTP_200_OK)
async def predict_risk(application: LoanApplication):
    """
    Evaluates loan applicant criteria and predicts risk score and category.
    """
    logger.info(f"Received prediction request for age={application.age}, credit_score={application.credit_score}")
    try:
        result = scoring_service.calculate_risk(
            age=application.age,
            income=application.income,
            loan_amount=application.loan_amount,
            credit_score=application.credit_score
        )
        return RiskPrediction(**result)
    except Exception as exc:
        logger.error(f"Internal calculation failure: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing the risk score."
        )
