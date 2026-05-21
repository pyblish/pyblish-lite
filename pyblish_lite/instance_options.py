"""Query selectable options for Artist page instance fields."""


def query_instance_field_options():
    # TODO: Replace with pipeline
    return {
        "asset_type": ["ve", "char", "prop", "env"],
        "entity_name": ["main", "secondary"],
        "asset_name": ["Halftrack", "Tank", "Vehicle"],
        "entity_variant": ["main", "variant_a", "variant_b"],
    }
