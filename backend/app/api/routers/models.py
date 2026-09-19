from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.core.database import get_db
from app.services.model_service import ModelService
from app.services.training_service import TrainingService, TrainingError
from app.schemas.models import ModelRunCreate, ModelRunResponse
from app.schemas.training import ModelTrainRequest, ModelTrainResponse, SUPPORTED_TASKS
from app.ml.model_trainer import SUPPORTED_CLASSIFICATION_MODELS, SUPPORTED_REGRESSION_MODELS

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
