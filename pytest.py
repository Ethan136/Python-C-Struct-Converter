class _Mark:
    def __getattr__(self, name):
        def decorator(*args, **kwargs):
            def wrapper(obj):
                return obj
            return wrapper
        return decorator


def skipif(condition, reason=None):
    def decorator(obj):
        return obj
    return decorator


# expose as pytest.mark
mark = _Mark()