from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NotificationResponse(BaseModel):
    id: int
    titleAr: str
    messageAr: str
    notificationType: str
    relatedApplicationId: Optional[int] = None
    relatedStage: Optional[str] = None
    isRead: bool = False
    readAt: Optional[datetime] = None
    createdAt: datetime


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    unreadCount: int
    total: int


class MarkReadRequest(BaseModel):
    notificationIds: list[int] = Field(..., min_length=1)


class ApplicantStatusResponse(BaseModel):
    id: int
    applicationId: int
    currentStage: str
    overallStatus: str
    statusNotes: Optional[str] = None
    lastUpdatedAt: datetime
    createdAt: datetime


class StatusHistoryItem(BaseModel):
    stageName: str
    stageStatus: str
    reviewDate: Optional[datetime] = None
    reviewerNotes: Optional[str] = None


class ApplicationStatusDetailResponse(BaseModel):
    applicationId: int
    courseName: str
    currentStage: str
    overallStatus: str
    statusNotes: Optional[str] = None
    stages: list[StatusHistoryItem]
    lastUpdatedAt: datetime
