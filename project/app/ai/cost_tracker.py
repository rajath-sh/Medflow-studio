"""
HealthOps Studio — AI Cost Tracker

Calculates estimated costs for LLM requests based on token usage,
and records the usage into the ai_usage_logs database table.
"""

from sqlalchemy.orm import Session
from app.db_models import AiUsageLog
from app.logging_config import get_logger
import uuid

logger = get_logger("healthops.ai.cost")

# Approximate pricing per 1M tokens (USD)
PRICING = {
    "gemini-2.5-flash": {
        "input": 0.075,
        "output": 0.30
    },
    "gemini-2.5-pro": {
        "input": 3.50,
        "output": 10.50
    }
}

def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate the estimated cost of an LLM request in USD."""
    rates = PRICING.get(model_name)
    if not rates:
        # Default fallback if model unknown
        rates = PRICING["gemini-2.5-flash"]
        
    input_cost = (input_tokens / 1_000_000) * rates["input"]
    output_cost = (output_tokens / 1_000_000) * rates["output"]
    
    return input_cost + output_cost

def record_usage(
    db: Session,
    user_id: str,
    model_name: str,
    input_tokens: int,
    output_tokens: int,
    request_id: str = None
) -> float:
    """
    Calculate cost and record the usage log in the database.
    Returns the estimated cost.
    """
    try:
        cost = calculate_cost(model_name, input_tokens, output_tokens)
        
        safe_user_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        
        usage_log = AiUsageLog(
            user_id=safe_user_id,
            request_id=request_id,
            model=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=cost
        )
        
        db.add(usage_log)
        db.commit()
        
        logger.info(
            f"AI Request Logged: {input_tokens} in / {output_tokens} out (${cost:.6f})",
            extra={
                "model": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
                "user_id": str(user_id),
                "request_id": request_id
            }
        )
        return cost
        
    except Exception as e:
        logger.error(f"Failed to record AI usage: {str(e)}")
        # Don't fail the request if tracking fails
        return 0.0
