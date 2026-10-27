import logging
from typing import Any, List
from langchain_core.tools import tool
from services.farm_service import FarmService

logger = logging.getLogger(__name__)

# We use a global service instance or initialize inside tools.
# Since FarmService is lightweight and handles its own DB session logic
# via SessionLocal, we can instantiate it here.
farm_service = FarmService()

@tool
def get_farm_profile() -> str:
    """
    Retrieves the global farm profile including location, soil type,
    main crops, and farm size. Use this to get general context about the farm.
    """
    try:
        profile = farm_service.get_full_profile()
        return str(profile)
    except Exception as e:
        logger.error(f"Error getting farm profile: {e}")
        return "Could not retrieve farm profile."

@tool
def list_farm_fields() -> str:
    """
    Lists all registered fields on the farm, including their names,
    current crops, and areas. Use this to identify field IDs for further queries.
    """
    try:
        fields = farm_service.manage_fields("list")
        if not fields:
            return "No fields found."

        field_list = []
        for f in fields:
            field_list.append(f"ID: {f.id}, Name: {f.name}, Crop: {f.crop}, Area: {f.area} acres")

        return "\n".join(field_list)
    except Exception as e:
        logger.error(f"Error listing farm fields: {e}")
        return "Could not retrieve fields."

@tool
def get_field_activity_logs(field_id: int) -> str:
    """
    Retrieves the complete activity history for a specific field.
    Use the field_id obtained from list_farm_fields.
    """
    try:
        logs = farm_service.get_field_logs(field_id)
        if not logs:
            return f"No activity logs found for field ID {field_id}."

        log_list = []
        for l in logs:
            log_list.append(f"Date: {l.date}, Type: {l.activity_type}, Desc: {l.description}, Amount: {l.amount}")

        return "\n".join(log_list)
    except Exception as e:
        logger.error(f"Error getting logs for field {field_id}: {e}")
        return f"Could not retrieve logs for field ID {field_id}."

@tool
def search_activity_logs(query: str) -> str:
    """
    Searches through all activity logs across all fields for a specific keyword.
    Useful for finding when a specific action (e.g., 'fertilization') happened globally.
    """
    try:
        all_fields = farm_service.manage_fields("list")
        results = []

        for f in all_fields:
            logs = farm_service.get_field_logs(f.id)
            for l in logs:
                if query.lower() in l.description.lower() or query.lower() in l.activity_type.lower():
                    results.append(f"Field: {f.name}, Date: {l.date}, Type: {l.activity_type}, Desc: {l.description}")

        if not results:
            return f"No logs found matching query: {query}"

        return "\n".join(results)
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        return "Could not search activity logs."

@tool
def get_field_trend_analysis(field_id: int, activity_type: str) -> str:
    """
    Analyzes trends for a specific activity (e.g., 'irrigation', 'yield', 'fertilization')
    over the last 5 entries. Detects if values are increasing, decreasing, or stable.
    Use this to identify 'quiet' signals of crop stress or improvement.
    """
    try:
        logs = farm_service.get_field_logs(field_id)
        if not logs:
            return f"No logs found for field ID {field_id}."

        # Filter for the specific activity and take the last 5
        relevant_logs = [l for l in logs if l.activity_type.lower() == activity_type.lower()]
        if not relevant_logs:
            return f"No logs of type '{activity_type}' found for field ID {field_id}."

        recent_logs = relevant_logs[-5:]

        # Extract amounts for trend calculation
        amounts = []
        for l in recent_logs:
            try:
                # Attempt to convert amount to float
                val = float(str(l.amount).replace(',', '')) if l.amount else 0.0
                amounts.append(val)
            except (ValueError, TypeError):
                amounts.append(0.0)

        if len(amounts) < 2:
            return f"Insufficient data points ({len(amounts)}) to determine a trend for {activity_type}."

        # Calculate simple slope (last vs first)
        delta = amounts[-1] - amounts[0]
        percent_change = (delta / amounts[0] * 100) if amounts[0] != 0 else 0

        trend = "Stable"
        if percent_change > 5: trend = "Increasing"
        elif percent_change < -5: trend = "Decreasing"

        return (
            f"Trend Analysis for {activity_type} (Field ID {field_id}):\n"
            f"- Window: Last {len(amounts)} entries\n"
            f"- Start Value: {amounts[0]}, End Value: {amounts[-1]}\n"
            f"- Absolute Change: {delta:.2f}\n"
            f"- Percentage Change: {percent_change:.2f}%\n"
            f"- Overall Trend: {trend}"
        )
    except Exception as e:
        logger.error(f"Error analyzing trend for field {field_id}: {e}")
        return f"Could not analyze trend for field ID {field_id}."
