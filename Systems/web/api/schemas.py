"""
Pydantic schemas for API responses.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

from Systems.core.database.models.user import UserRole


class UserResponse(BaseModel):
    """User response schema."""
    
    telegram_id: int = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="Is user active")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Update timestamp")
    
    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """User creation schema."""
    
    telegram_id: int = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, description="Username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    full_name: Optional[str] = Field(
        None, description="Full name (will be split into first/last name if provided)"
    )
    role: UserRole = Field(default=UserRole.USER, description="User role")

    @model_validator(mode="after")
    def ensure_name_present(self) -> "UserCreate":
        """Ensure at least first name or full name is provided."""

        if not (self.first_name and self.first_name.strip()) and not (
            self.full_name and self.full_name.strip()
        ):
            raise ValueError("first_name or full_name must be provided")

        return self


class UserUpdate(BaseModel):
    """User update schema."""
    
    username: Optional[str] = Field(None, description="Username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    full_name: Optional[str] = Field(None, description="Full name")
    is_active: Optional[bool] = Field(None, description="Is user active")


class RoleChange(BaseModel):
    """Role change schema."""
    
    role: UserRole = Field(..., description="New role")


class ModuleResponse(BaseModel):
    """Module response schema."""
    
    name: str = Field(..., description="Module name")
    display_name: str = Field(..., description="Display name")
    version: str = Field(..., description="Module version")
    description: str = Field(default="", description="Module description")
    author: str = Field(default="", description="Module author")
    enabled: bool = Field(..., description="Is module enabled")
    enabled_by_default: bool = Field(..., description="Enabled by default")
    dependencies: list[str] = Field(default_factory=list, description="Dependencies")
    commands: list[dict[str, Any]] = Field(
        default_factory=list, description="Commands"
    )
    settings: dict[str, Any] = Field(default_factory=dict, description="Settings schema")
    languages: list[str] = Field(default_factory=list, description="Languages")
    background_tasks: list[str] = Field(
        default_factory=list, description="Background tasks"
    )


class SettingResponse(BaseModel):
    """Setting response schema."""
    
    module_name: str = Field(..., description="Module name")
    key: str = Field(..., description="Setting key")
    value: Any = Field(..., description="Setting value")
    level: str = Field(..., description="Setting level (user/admin)")
    user_id: Optional[int] = Field(None, description="User ID (for user settings)")


class SettingUpdate(BaseModel):
    """Setting update schema."""
    
    value: Any = Field(..., description="Setting value")


class SettingSchema(BaseModel):
    """Setting schema from manifest."""
    
    type: str = Field(..., description="Setting type")
    default: Optional[Any] = Field(None, description="Default value")
    min: Optional[float] = Field(None, description="Minimum value")
    max: Optional[float] = Field(None, description="Maximum value")
    description: Optional[str] = Field(None, description="Setting description")


class StatsResponse(BaseModel):
    """Stats response schema."""
    
    total_users: int = Field(..., description="Total users")
    active_users: int = Field(..., description="Active users")
    total_modules: int = Field(..., description="Total modules")
    enabled_modules: int = Field(..., description="Enabled modules")
    total_commands: int = Field(..., description="Total commands")
    total_settings: int = Field(..., description="Total settings")


class AuditLogResponse(BaseModel):
    """Audit log response schema."""
    
    id: int = Field(..., description="Log ID")
    user_id: int = Field(..., description="User ID")
    action: str = Field(..., description="Action")
    resource: str = Field(..., description="Resource")
    old_value: Optional[str] = Field(None, description="Old value")
    new_value: Optional[str] = Field(None, description="New value")
    ip_address: Optional[str] = Field(None, description="IP address")
    success: bool = Field(..., description="Success status")
    timestamp: str = Field(..., description="Timestamp")
    
    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    detail: str = Field(..., description="Error message")

