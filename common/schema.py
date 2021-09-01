from graphql_jwt.decorators import login_required


class AuthDjangoSerializerMutationMixin:
    @classmethod
    @login_required
    def create(cls, root, info, **kwargs):
        return super().create(root, info, **kwargs)

    @classmethod
    @login_required
    def update(cls, root, info, **kwargs):
        data = kwargs.get(cls._meta.input_field_name)

        # HACK: Flutter Artemis passes nulls for fields
        # that are supposed to not be changed.
        if data is not None:
            kwargs[cls._meta.input_field_name] = {
                k: v for k, v in data.items() if v is not None
            }

        return super().update(root, info, **kwargs)

    @classmethod
    @login_required
    def delete(cls, root, info, **kwargs):
        return super().delete(root, info, **kwargs)

    @classmethod
    def get_serializer_kwargs(cls, root, info, **kwargs):
        return {"context": {"request": info.context}}
