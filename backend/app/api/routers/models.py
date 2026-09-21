
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.ml.model_trainer import (
    SUPPORTED_CLASSIFICATION_MODELS,
    SUPPORTED_REGRESSION_MODELS,
)
from app.schemas.evaluation import ClassificationEvaluationResponse, RegressionEvaluationResponse, EvaluationRequest
from app.schemas.explainability import ExplainabilityResponse
from app.schemas.models import ModelRunCreate, ModelRunResponse
from app.schemas.prediction import ClassificationPredictionResponse, PredictionRequest, RegressionPredictionResponse
from app.schemas.training import SUPPORTED_TASKS, ModelTrainRequest, ModelTrainResponse
from app.services.evaluation_service import EvaluationError, EvaluationService
from app.services.model_service import ModelService
from app.services.prediction_service import PredictionError, PredictionService
from app.services.training_service import TrainingError, TrainingService

router = APIRouter()


@router.get("/", response_model=list[ModelRunResponse])
async def list_models(symbol: str | None = None, db: AsyncSession = Depends(get_db)):
    service = ModelService(db)
    return await service.list_models(symbol=symbol)


@router.get("/{model_run_id}", response_model=ModelRunResponse)
async def get_model(model_run_id: int, db: AsyncSession = Depends(get_db)):
    service = ModelService(db)
    model = await service.get_model(model_run_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model run not found")
    return model


@router.post("/", response_model=ModelRunResponse, status_code=201)
async def create_model_run(model_data: ModelRunCreate, db: AsyncSession = Depends(get_db)):
    service = ModelService(db)
    return await service.create_model_run(model_data)


@router.post("/train", response_model=ModelTrainResponse)
async def train_model(request: ModelTrainRequest, db: AsyncSession = Depends(get_db)):
    task = request.task.lower()
    model_name = request.model_name.lower()

    if task not in SUPPORTED_TASKS:
        raise HTTPException(status_code=400, detail=f"Unsupported task type: {request.task}. Supported: {sorted(SUPPORTED_TASKS)}")

    valid_models = SUPPORTED_CLASSIFICATION_MODELS if task == "classification" else SUPPORTED_REGRESSION_MODELS
    if model_name not in valid_models:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model '{request.model_name}' for task '{request.task}'. Supported: {sorted(valid_models)}",
        )

    service = TrainingService(
        db=db,
        symbol=request.symbol,
        start_date=request.start_date,
        end_date=request.end_date,
        task_type=task,
        model_name=model_name,
    )
    try:
        result = await service.train()
    except TrainingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Model training failed: {exc}") from exc

    return ModelTrainResponse(**result)


@router.post("/evaluate")
async def evaluate_model(request: EvaluationRequest, db: AsyncSession = Depends(get_db)):
    service = EvaluationService(db, model_run_id=request.model_run_id, split=request.evaluation_split)
    try:
        result = await service.evaluate()
    except EvaluationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {exc}") from exc

    if result["task_type"] == "classification":
        return ClassificationEvaluationResponse(**result)
    return RegressionEvaluationResponse(**result)


@router.post("/predict", response_model=ClassificationPredictionResponse | RegressionPredictionResponse)
async def predict(request: PredictionRequest, db: AsyncSession = Depends(get_db)):
    service = PredictionService(db, model_run_id=request.model_run_id, symbol=request.symbol, prediction_date=request.prediction_date)
    try:
        result = await service.predict()
    except PredictionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

    if result["task_type"] == "classification":
        return ClassificationPredictionResponse(**result)
    return RegressionPredictionResponse(**result)


@router.get("/{model_run_id}/explain", response_model=ExplainabilityResponse)
async def explain_model(model_run_id: int, symbol: str, prediction_date: str, db: AsyncSession = Depends(get_db)):
    try:
        parsed_date = date.fromisoformat(prediction_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {exc}") from exc
    service = PredictionService(db, model_run_id=model_run_id, symbol=symbol, prediction_date=parsed_date)
    try:
        result = await service.predict()
    except PredictionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {exc}") from exc

    feature_importance: dict[str, float] = {}
    if result.get("shap_values") and result.get("feature_columns"):
        for feature, shap_value in zip(result["feature_columns"], result["shap_values"], strict=False):
            feature_importance[feature] = shap_value

    top_features = [
        {"feature": feature, "shap_value": value}
        for feature, value in sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)[:10]
    ]

    return ExplainabilityResponse(
        model_run_id=model_run_id,
        model_name=result["model_name"],
        task_type=result["task_type"],
        prediction_date=prediction_date,
        predicted_class=result.get("predicted_class"),
        predicted_return=result.get("predicted_return"),
        predicted_direction=result.get("predicted_direction"),
        top_features=top_features,
        feature_importance=feature_importance,
    )
