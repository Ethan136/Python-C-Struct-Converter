import jsonschema

# V2P Presenter context JSON Schema
PRESENTER_CONTEXT_SCHEMA = {
    "type": "object",
    "properties": {
        "display_mode": {"type": "string"},
        "gui_version": {"type": "string", "enum": ["legacy", "modern"]},
        "expanded_nodes": {"type": "array", "items": {"type": "string"}},
        "selected_node": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "error": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "filter": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "search": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "version": {"type": "string"},
        "extra": {"type": "object"},
        "loading": {"type": "boolean"},
        "history": {"type": "array"},
        "user_settings": {"type": "object"},
        "last_update_time": {"type": "number"},
        "readonly": {"type": "boolean"},
        "pending_action": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "debug_info": {"type": "object"}
    },
    "required": ["display_mode", "gui_version", "expanded_nodes", "selected_node", "error", "version", "extra", "loading", "history", "user_settings", "last_update_time", "readonly", "debug_info"],
    "additionalProperties": True
}

def validate_presenter_context(context: dict):
    """驗證 Presenter context 是否符合 schema，若不符會拋出 jsonschema.ValidationError"""
    jsonschema.validate(instance=context, schema=PRESENTER_CONTEXT_SCHEMA) 