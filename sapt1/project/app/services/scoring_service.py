import csv
from pathlib import Path
from typing import Dict, Any
from app import config
from app.utils.logger import get_logger

logger = get_logger(__name__)

class RiskScoringService:
    """
    Service class responsible for calculating loan application risk scores.
    Dynamically loads normalization bounds from the local CSV dataset.
    """
    WEIGHT_CREDIT = 0.40
    WEIGHT_RATIO = 0.30
    WEIGHT_INCOME = 0.20
    WEIGHT_AGE = 0.10

    def __init__(self):
        self.age_min = None
        self.age_max = None
        self.income_min = None
        self.income_max = None
        self.credit_min = None
        self.credit_max = None
        self.loan_min = None
        self.loan_max = None
        self.ratio_min = None
        self.ratio_max = None

        self._load_bounds_from_dataset()

    def _load_bounds_from_dataset(self):
        """
        Locates the local loan_prediction_dataset.csv file and computes feature ranges.
        Raises FileNotFoundError if the dataset is missing.
        """
        csv_path = (config.BASE_DIR / "loan_prediction_dataset.csv").resolve()

        if not csv_path.exists():
            error_msg = f"Critical Error: Historical dataset CSV not found at '{csv_path}'."
            logger.critical(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            logger.info(f"Loading dataset bounds dynamically from '{csv_path}'...")
            ages = []
            incomes = []
            credit_scores = []
            loan_amounts = []
            ratios = []

            with open(csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                if reader.fieldnames:
                    reader.fieldnames = [name.strip() for name in reader.fieldnames]

                for row in reader:
                    age_val = float(row["Age"])
                    income_val = float(row["Income"])
                    credit_val = float(row["Credit_Score"])
                    loan_val = float(row["Loan_Amount"])

                    ages.append(age_val)
                    incomes.append(income_val)
                    credit_scores.append(credit_val)
                    loan_amounts.append(loan_val)
                    ratios.append(loan_val / income_val)

            self.age_min = min(ages)
            self.age_max = max(ages)
            self.income_min = min(incomes)
            self.income_max = max(incomes)
            self.credit_min = min(credit_scores)
            self.credit_max = max(credit_scores)
            self.loan_min = min(loan_amounts)
            self.loan_max = max(loan_amounts)
            self.ratio_min = min(ratios)
            self.ratio_max = max(ratios)

            logger.info(
                "Dataset bounds loaded successfully. Ranges: "
                f"Age: [{self.age_min}-{self.age_max}], "
                f"Income: [{self.income_min}-{self.income_max}], "
                f"Credit Score: [{self.credit_min}-{self.credit_max}], "
                f"Loan Amount: [{self.loan_min}-{self.loan_max}], "
                f"LTI Ratio: [{self.ratio_min:.6f}-{self.ratio_max:.6f}]"
            )

        except Exception as exc:
            logger.critical(f"Failed to read bounds from dataset CSV: {str(exc)}")
            raise exc

    @staticmethod
    def _clamp(value: float, min_val: float, max_val: float) -> float:
        """Clamps the value within the [min_val, max_val] range."""
        return max(min_val, min(max_val, value))

    @staticmethod
    def _normalize(value: float, min_val: float, max_val: float) -> float:
        """Performs min-max normalization, yielding a value in [0.0, 1.0]."""
        if max_val == min_val:
            return 0.0
        return (value - min_val) / (max_val - min_val)

    def calculate_risk(self, age: int, income: float, loan_amount: float, credit_score: int) -> Dict[str, Any]:
        """
        Calculates the risk score and risk category for a loan application.
        """
        logger.info(
            f"Starting risk calculation: age={age}, income={income}, "
            f"loan_amount={loan_amount}, credit_score={credit_score}"
        )

        age_clamped = self._clamp(float(age), self.age_min, self.age_max)
        income_clamped = self._clamp(income, self.income_min, self.income_max)
        credit_clamped = self._clamp(float(credit_score), self.credit_min, self.credit_max)
        loan_clamped = self._clamp(loan_amount, self.loan_min, self.loan_max)

        raw_ratio = loan_clamped / income_clamped
        ratio_clamped = self._clamp(raw_ratio, self.ratio_min, self.ratio_max)
        ratio_risk = self._normalize(ratio_clamped, self.ratio_min, self.ratio_max)

        age_norm = self._normalize(age_clamped, self.age_min, self.age_max)
        income_norm = self._normalize(income_clamped, self.income_min, self.income_max)
        credit_norm = self._normalize(credit_clamped, self.credit_min, self.credit_max)

        credit_risk = 1.0 - credit_norm
        income_risk = 1.0 - income_norm
        age_risk = 1.0 - age_norm

        weighted_score = (
            self.WEIGHT_CREDIT * credit_risk +
            self.WEIGHT_RATIO * ratio_risk +
            self.WEIGHT_INCOME * income_risk +
            self.WEIGHT_AGE * age_risk
        )

        risk_score = self._clamp(round(weighted_score, 2), 0.0, 1.0)

        if risk_score <= 0.30:
            risk_category = "LOW"
        elif risk_score <= 0.70:
            risk_category = "MEDIUM"
        else:
            risk_category = "HIGH"

        logger.info(
            f"Risk calculation complete. Raw Score: {weighted_score:.4f}, "
            f"Rounded Score: {risk_score}, Category: {risk_category}"
        )

        return {
            "risk_score": risk_score,
            "risk_category": risk_category
        }
