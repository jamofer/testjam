from pydantic import BaseModel, ConfigDict


class NotificationPreferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_type: str
    in_app: bool
    email: bool


class NotificationPreferenceUpdate(BaseModel):
    in_app: bool
    email: bool
