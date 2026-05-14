from datetime import date as _Date
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VitalsCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "pseudo_id": "user_12345",
                "pseudo_id2": "device_fitbit_67890",
                # Core Activity
                "steps": 8542,
                "calories_kcal": 2150.5,
                "distance_meters": 5200.0,
                "total_active_minutes": 45,
                # Exercise
                "activity_name": "WALKING",
                "exercise_duration_minutes": 45.5,
                "active_zone_minutes": 45,
                "fatburn_active_zone_minutes": 22,
                "cardio_active_zone_minutes": 13,
                "peak_active_zone_minutes": 9,
                # Vitals
                "resting_heart_rate": 72,
                "heart_rate": 72,
                "heart_rate_variability": 45.5,
                "stress_management_score": None,
                "blood_pressure_systolic": None,
                "blood_pressure_diastolic": None,
                # Sleep
                "sleep_minutes": 480,
                "rem_sleep_minutes": 90,
                "deep_sleep_minutes": 60,
                "light_sleep_minutes": 250,
                "awake_minutes": 20,
                "bed_time": "22:00",
                "wake_up_time": "06:00",
                "deep_sleep_percent": 14.2,
                "rem_sleep_percent": 21.4,
                "light_sleep_percent": 59.5,
                "awake_percent": 4.7,
                # Biometrics
                "weight_kg": 70.0,
                "height_cm": 175.0,
                "age": None,
                "gender": None,
                # Metadata
                "recorded_at": "2026-05-02T18:03:00",
                "date": "2026-05-02",
            }
        },
    )

    # Identity
    pseudo_id: Optional[str] = None
    pseudo_id2: Optional[str] = None
    patient_id: Optional[int] = Field(None, description="Public patient_id.")

    # Core Activity
    steps: Optional[int] = None
    calories_kcal: Optional[float] = None
    distance_meters: Optional[float] = None
    total_active_minutes: Optional[int] = None

    # Exercise
    activity_name: Optional[str] = None
    exercise_duration_minutes: Optional[float] = None
    active_zone_minutes: Optional[int] = None
    fatburn_active_zone_minutes: Optional[int] = None
    cardio_active_zone_minutes: Optional[int] = None
    peak_active_zone_minutes: Optional[int] = None

    # Vitals
    resting_heart_rate: Optional[int] = None
    heart_rate: Optional[int] = None
    heart_rate_variability: Optional[float] = None
    stress_management_score: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None

    # Sleep
    sleep_minutes: Optional[int] = None
    rem_sleep_minutes: Optional[int] = None
    deep_sleep_minutes: Optional[int] = None
    light_sleep_minutes: Optional[int] = None
    awake_minutes: Optional[int] = None
    bed_time: Optional[str] = None
    wake_up_time: Optional[str] = None
    deep_sleep_percent: Optional[float] = None
    rem_sleep_percent: Optional[float] = None
    light_sleep_percent: Optional[float] = None
    awake_percent: Optional[float] = None

    # Biometrics
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None

    # Metadata
    recorded_at: Optional[datetime] = None
    date: Optional[_Date] = None


class VitalsPatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Identity
    pseudo_id: Optional[str] = None
    pseudo_id2: Optional[str] = None
    patient_id: Optional[int] = None

    # Core Activity
    steps: Optional[int] = None
    calories_kcal: Optional[float] = None
    distance_meters: Optional[float] = None
    total_active_minutes: Optional[int] = None

    # Exercise
    activity_name: Optional[str] = None
    exercise_duration_minutes: Optional[float] = None
    active_zone_minutes: Optional[int] = None
    fatburn_active_zone_minutes: Optional[int] = None
    cardio_active_zone_minutes: Optional[int] = None
    peak_active_zone_minutes: Optional[int] = None

    # Vitals
    resting_heart_rate: Optional[int] = None
    heart_rate: Optional[int] = None
    heart_rate_variability: Optional[float] = None
    stress_management_score: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None

    # Sleep
    sleep_minutes: Optional[int] = None
    rem_sleep_minutes: Optional[int] = None
    deep_sleep_minutes: Optional[int] = None
    light_sleep_minutes: Optional[int] = None
    awake_minutes: Optional[int] = None
    bed_time: Optional[str] = None
    wake_up_time: Optional[str] = None
    deep_sleep_percent: Optional[float] = None
    rem_sleep_percent: Optional[float] = None
    light_sleep_percent: Optional[float] = None
    awake_percent: Optional[float] = None

    # Biometrics
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None

    # Metadata
    recorded_at: Optional[datetime] = None
    date: Optional[_Date] = None


class VitalsResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(..., description="Public vitals identifier.")

    # Identity
    pseudo_id: Optional[str] = None
    pseudo_id2: Optional[str] = None
    user_id: Optional[str] = None
    patient_id: Optional[int] = None
    org_id: Optional[str] = None

    # Core Activity
    steps: Optional[int] = None
    calories_kcal: Optional[float] = None
    distance_meters: Optional[float] = None
    total_active_minutes: Optional[int] = None

    # Exercise
    activity_name: Optional[str] = None
    exercise_duration_minutes: Optional[float] = None
    active_zone_minutes: Optional[int] = None
    fatburn_active_zone_minutes: Optional[int] = None
    cardio_active_zone_minutes: Optional[int] = None
    peak_active_zone_minutes: Optional[int] = None

    # Vitals
    resting_heart_rate: Optional[int] = None
    heart_rate: Optional[int] = None
    heart_rate_variability: Optional[float] = None
    stress_management_score: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None

    # Sleep
    sleep_minutes: Optional[int] = None
    rem_sleep_minutes: Optional[int] = None
    deep_sleep_minutes: Optional[int] = None
    light_sleep_minutes: Optional[int] = None
    awake_minutes: Optional[int] = None
    bed_time: Optional[str] = None
    wake_up_time: Optional[str] = None
    deep_sleep_percent: Optional[float] = None
    rem_sleep_percent: Optional[float] = None
    light_sleep_percent: Optional[float] = None
    awake_percent: Optional[float] = None

    # Biometrics
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None

    # Metadata
    recorded_at: Optional[datetime] = None
    date: Optional[_Date] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
