class ValidationError(Exception):
    pass


def _validate_type(value, expected):
    t = expected.get('type')
    if t == 'string':
        if not isinstance(value, str):
            raise ValidationError('Expected string')
        enum = expected.get('enum')
        if enum is not None and value not in enum:
            raise ValidationError('Value not in enum')
    elif t == 'number':
        if not isinstance(value, (int, float)):
            raise ValidationError('Expected number')
    elif t == 'boolean':
        if not isinstance(value, bool):
            raise ValidationError('Expected boolean')
    elif t == 'object':
        validate(value, expected)
    elif t == 'array':
        if not isinstance(value, list):
            raise ValidationError('Expected array')
        item_schema = expected.get('items')
        if item_schema is not None:
            for item in value:
                _validate_schema(item, item_schema)
    elif t == 'null':
        if value is not None:
            raise ValidationError('Expected null')
    elif t is None:
        pass
    else:
        raise ValidationError(f'Unsupported type: {t}')


def _validate_schema(value, schema):
    if 'anyOf' in schema:
        for sub in schema['anyOf']:
            try:
                _validate_schema(value, sub)
                break
            except ValidationError:
                continue
        else:
            raise ValidationError('anyOf conditions not met')
    else:
        _validate_type(value, schema)


def validate(instance, schema):
    if schema.get('type') == 'object':
        if not isinstance(instance, dict):
            raise ValidationError('Expected object')
        props = schema.get('properties', {})
        required = schema.get('required', [])
        for r in required:
            if r not in instance:
                raise ValidationError(f"Missing required property: {r}")
        additional = schema.get('additionalProperties', True)
        for key, val in instance.items():
            if key in props:
                _validate_schema(val, props[key])
            elif not additional:
                raise ValidationError(f'Additional property {key} not allowed')
    else:
        _validate_schema(instance, schema)
