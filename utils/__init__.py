"""
Utils module for CRM Message Generation System
Contains persona compatibility helpers and custom persona builder
"""

from .persona_compat import (
    get_persona_field,
    normalize_persona,
    get_age_group,
    get_gender,
    get_skin_type,
    get_income_level,
    is_kadence_persona,
    build_persona_summary
)

from .custom_persona_builder import (
    AGE_GROUPS,
    GENDERS,
    SKIN_TYPES,
    SKIN_CONCERNS,
    PRICE_SENSITIVITIES,
    load_persona_profiles,
    get_segment_options,
    get_segment_insights,
    build_custom_persona,
    get_persona_preview
)

__all__ = [
    # persona_compat
    'get_persona_field',
    'normalize_persona',
    'get_age_group',
    'get_gender',
    'get_skin_type',
    'get_income_level',
    'is_kadence_persona',
    'build_persona_summary',
    # custom_persona_builder
    'AGE_GROUPS',
    'GENDERS',
    'SKIN_TYPES',
    'SKIN_CONCERNS',
    'PRICE_SENSITIVITIES',
    'load_persona_profiles',
    'get_segment_options',
    'get_segment_insights',
    'build_custom_persona',
    'get_persona_preview',
]
