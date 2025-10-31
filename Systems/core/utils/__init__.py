"""
Utility modules for SwiftDevBot.

Provides:
- validators: Validation functions
- formatters: Formatting functions
- helpers: General-purpose helpers
"""

from Systems.core.utils.validators import (
    validate_telegram_id,
    validate_username,
    validate_role,
    validate_module_name,
    validate_version,
    validate_setting_value,
)

from Systems.core.utils.formatters import (
    format_datetime,
    format_date,
    format_time,
    format_timedelta,
    format_number,
    format_bytes,
    format_percentage,
    format_relative_time,
    format_username,
    format_role,
)

from Systems.core.utils.helpers import (
    generate_random_string,
    hash_string,
    safe_int,
    safe_float,
    safe_str,
    chunk_list,
    retry_async,
    retry_sync,
    truncate_string,
    sanitize_filename,
    merge_dicts,
    get_nested_value,
    set_nested_value,
)

__all__ = [
    # Validators
    "validate_telegram_id",
    "validate_username",
    "validate_role",
    "validate_module_name",
    "validate_version",
    "validate_setting_value",
    # Formatters
    "format_datetime",
    "format_date",
    "format_time",
    "format_timedelta",
    "format_number",
    "format_bytes",
    "format_percentage",
    "format_relative_time",
    "format_username",
    "format_role",
    # Helpers
    "generate_random_string",
    "hash_string",
    "safe_int",
    "safe_float",
    "safe_str",
    "chunk_list",
    "retry_async",
    "retry_sync",
    "truncate_string",
    "sanitize_filename",
    "merge_dicts",
    "get_nested_value",
    "set_nested_value",
]
