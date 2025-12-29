"""
Persona Compatibility Helper
Provides backward compatibility between Legacy (P001-P007) and Kadence (K001-K008) persona formats.

Key differences:
- Legacy: age_group, gender, skin_type are top-level keys
- Kadence: these are nested under 'demographics' dict
- Kadence has additional: segment_id, segment_size, preferred_products, sample_message
"""
from typing import Dict, Any, Optional


def get_persona_field(persona: Dict[str, Any], field: str, default: Any = None) -> Any:
    """
    Get a field from persona with automatic format detection.
    Handles both Legacy (P-series) and Kadence (K-series) formats.

    Args:
        persona: Persona dictionary
        field: Field name to retrieve
        default: Default value if field not found

    Returns:
        Field value or default
    """
    # Direct access first
    if field in persona:
        return persona[field]

    # Check demographics for Kadence format
    demographics = persona.get('demographics', {})
    if field in demographics:
        return demographics[field]

    # Field mappings for edge cases
    field_mappings = {
        'age': 'age_group',
        'skin': 'skin_type',
    }

    mapped_field = field_mappings.get(field, field)
    if mapped_field in persona:
        return persona[mapped_field]
    if mapped_field in demographics:
        return demographics[mapped_field]

    return default


def normalize_persona(persona: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize persona to have consistent top-level access for common fields.
    Returns a new dict with both original and flattened demographics.

    Args:
        persona: Original persona dictionary

    Returns:
        Normalized persona with age_group, gender, skin_type at top level
    """
    result = dict(persona)  # Copy original

    # If Kadence format, flatten demographics to top level
    demographics = persona.get('demographics', {})
    if demographics:
        # Add demographics fields to top level if not already present
        for key in ['age_group', 'gender', 'skin_type', 'income_level']:
            if key not in result and key in demographics:
                result[key] = demographics[key]

    return result


def get_age_group(persona: Dict[str, Any]) -> str:
    """Get age group from persona (works with both formats)"""
    return get_persona_field(persona, 'age_group', 'N/A')


def get_gender(persona: Dict[str, Any]) -> str:
    """Get gender from persona (works with both formats)"""
    return get_persona_field(persona, 'gender', 'N/A')


def get_skin_type(persona: Dict[str, Any]) -> str:
    """Get skin type from persona (works with both formats)"""
    return get_persona_field(persona, 'skin_type', 'N/A')


def get_income_level(persona: Dict[str, Any]) -> str:
    """Get income level from persona (Kadence only, defaults for Legacy)"""
    return get_persona_field(persona, 'income_level', '중')


def is_kadence_persona(persona: Dict[str, Any]) -> bool:
    """Check if persona is Kadence format (K-series)"""
    persona_id = persona.get('id', '')
    return persona_id.startswith('K') or 'segment_id' in persona


def get_segment_id(persona: Dict[str, Any]) -> Optional[str]:
    """Get segment ID for Kadence personas"""
    return persona.get('segment_id')


def get_preferred_products(persona: Dict[str, Any]) -> list:
    """Get preferred products (Kadence only)"""
    return persona.get('preferred_products', [])


def get_sample_message(persona: Dict[str, Any]) -> str:
    """Get sample message (Kadence only)"""
    return persona.get('sample_message', '')


def build_persona_summary(persona: Dict[str, Any]) -> str:
    """
    Build a summary string for persona (works with both formats).

    Returns:
        Multi-line string with persona details
    """
    lines = []

    # Basic info
    lines.append(f"이름: {persona.get('name', 'N/A')}")
    lines.append(f"연령대: {get_age_group(persona)}")
    lines.append(f"성별: {get_gender(persona)}")
    lines.append(f"피부타입: {get_skin_type(persona)}")

    # Kadence-specific
    if is_kadence_persona(persona):
        segment_id = get_segment_id(persona)
        if segment_id:
            lines.append(f"세그먼트: {segment_id}")

        segment_size = persona.get('segment_size', {})
        if segment_size:
            pct = segment_size.get('percentage', 0)
            lines.append(f"세그먼트 비율: {pct}%")

    # Common fields
    if persona.get('skin_concerns'):
        lines.append(f"피부고민: {', '.join(persona['skin_concerns'])}")

    if persona.get('lifestyle'):
        lines.append(f"라이프스타일: {persona['lifestyle'][:100]}...")

    if persona.get('preferred_brands'):
        lines.append(f"선호브랜드: {', '.join(persona['preferred_brands'][:5])}")

    if persona.get('price_sensitivity'):
        lines.append(f"가격민감도: {persona['price_sensitivity']}")

    if persona.get('purchase_triggers'):
        lines.append(f"구매트리거: {', '.join(persona['purchase_triggers'][:5])}")

    if persona.get('values'):
        lines.append(f"가치관: {', '.join(persona['values'])}")

    # Communication style
    comm_style = persona.get('communication_style', {})
    if isinstance(comm_style, dict):
        if comm_style.get('tone'):
            lines.append(f"커뮤니케이션 톤: {comm_style['tone']}")
    elif isinstance(comm_style, str):
        lines.append(f"커뮤니케이션 스타일: {comm_style}")

    return '\n'.join(lines)


# For testing
if __name__ == "__main__":
    import json
    from pathlib import Path

    # Test with both persona files
    base_path = Path(__file__).parent.parent / "data" / "personas"

    # Legacy
    with open(base_path / "personas.json", 'r') as f:
        legacy = json.load(f)

    # Kadence
    with open(base_path / "personas_kadence_enriched.json", 'r') as f:
        kadence = json.load(f)

    print("=" * 60)
    print("Testing Legacy Persona (P001)")
    print("=" * 60)
    p = legacy['personas'][0]
    print(f"ID: {p['id']}")
    print(f"is_kadence: {is_kadence_persona(p)}")
    print(f"age_group: {get_age_group(p)}")
    print(f"skin_type: {get_skin_type(p)}")
    print(f"gender: {get_gender(p)}")
    print()

    print("=" * 60)
    print("Testing Kadence Persona (K001)")
    print("=" * 60)
    k = kadence['personas'][0]
    print(f"ID: {k['id']}")
    print(f"is_kadence: {is_kadence_persona(k)}")
    print(f"age_group: {get_age_group(k)}")
    print(f"skin_type: {get_skin_type(k)}")
    print(f"gender: {get_gender(k)}")
    print(f"segment_id: {get_segment_id(k)}")
    print()

    print("=" * 60)
    print("Normalized Kadence Persona")
    print("=" * 60)
    normalized = normalize_persona(k)
    print(f"Top-level age_group: {normalized.get('age_group')}")
    print(f"Top-level skin_type: {normalized.get('skin_type')}")
    print(f"Top-level gender: {normalized.get('gender')}")
