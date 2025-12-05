"""
Service for resolving dynamic field values
"""
from datetime import datetime, date
from typing import Dict, Any, Optional


class DynamicValueResolver:
    """Resolve dynamic field values based on configuration"""

    # Available dynamic value types
    DYNAMIC_TYPES = {
        "current_date": "Data atual (YYYY-MM-DD)",
        "current_date_br": "Data atual (DD/MM/YYYY)",
        "current_datetime": "Data e hora atual",
        "current_time": "Hora atual",
        "current_year": "Ano atual",
        "user_name": "Nome do usuário",
        "user_email": "Email do usuário",
        "user_username": "Username do usuário",
        "serial_number": "Número de série sequencial (gerado na submissão)",
    }

    @staticmethod
    def get_available_types() -> Dict[str, str]:
        """
        Get list of available dynamic value types

        Returns:
            Dictionary mapping type keys to their descriptions
        """
        return DynamicValueResolver.DYNAMIC_TYPES.copy()

    @staticmethod
    def resolve_value(
        dynamic_type: str,
        user: Optional[Any] = None,
        template: Optional[Any] = None,
        db_session: Optional[Any] = None
    ) -> str:
        """
        Resolve a dynamic value based on its type

        Args:
            dynamic_type: Type of dynamic value to resolve
            user: User object for user-related values
            template: Template object for serial_number type
            db_session: Database session for serial_number atomicity

        Returns:
            Resolved value as string

        Raises:
            ValueError: If dynamic_type is unknown or requirements not met
        """
        if dynamic_type == "current_date":
            return date.today().isoformat()

        elif dynamic_type == "current_date_br":
            return date.today().strftime("%d/%m/%Y")

        elif dynamic_type == "current_datetime":
            return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        elif dynamic_type == "current_time":
            return datetime.now().strftime("%H:%M:%S")

        elif dynamic_type == "current_year":
            return str(date.today().year)

        elif dynamic_type == "user_name":
            if user:
                return user.name or user.username
            return ""

        elif dynamic_type == "user_email":
            if user:
                return user.email
            return ""

        elif dynamic_type == "user_username":
            if user:
                return user.username
            return ""

        elif dynamic_type == "serial_number":
            if not template or not db_session:
                raise ValueError("serial_number requires template and db_session")
            # Increment and return the sequence number atomically
            template.sequence_number += 1
            db_session.flush()  # Ensure it's persisted immediately
            return str(template.sequence_number)

        else:
            raise ValueError(f"Unknown dynamic type: {dynamic_type}")

    @staticmethod
    def resolve_template_values(
        template: Any,
        user: Optional[Any] = None,
        db_session: Optional[Any] = None
    ) -> Dict[str, str]:
        """
        Resolve all dynamic values for a template

        Args:
            template: Template object with field_config
            user: User object for user-related values
            db_session: Database session for serial_number atomicity

        Returns:
            Dictionary mapping field names to resolved values
        """
        resolved = {}

        if not template.field_config:
            return resolved

        # Resolve dynamic values
        for field_name, config in template.field_config.items():
            if config.get("dynamic_type"):
                try:
                    resolved[field_name] = DynamicValueResolver.resolve_value(
                        config["dynamic_type"],
                        user,
                        template,
                        db_session
                    )
                except ValueError:
                    # If dynamic type is invalid, skip it
                    pass

        return resolved

    @staticmethod
    def merge_values(
        default_values: Optional[Dict[str, str]],
        dynamic_values: Dict[str, str],
        user_values: Optional[Dict[str, str]] = None,
        field_config: Optional[Dict[str, Dict]] = None
    ) -> Dict[str, str]:
        """
        Merge default values, dynamic values, and user-provided values

        Priority:
        1. Dynamic values (always applied)
        2. User values (if field is not locked)
        3. Default values

        Args:
            default_values: Static default values
            dynamic_values: Resolved dynamic values
            user_values: User-provided values (from form submission)
            field_config: Field configuration (for locked status)

        Returns:
            Merged values dictionary
        """
        merged = {}

        # Start with default values
        if default_values:
            merged.update(default_values)

        # Apply user values (if not locked)
        if user_values:
            for field_name, value in user_values.items():
                # Check if field is locked
                is_locked = False
                if field_config and field_name in field_config:
                    is_locked = field_config[field_name].get("locked", False)

                # Only apply user value if field is not locked
                if not is_locked:
                    merged[field_name] = value

        # Apply dynamic values (always override)
        merged.update(dynamic_values)

        return merged
