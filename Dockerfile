# syntax=docker/dockerfile:1

FROM python:3.9-slim as python-base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"


FROM python-base as builder-base
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    build-essential

ENV POETRY_VERSION=1.4.0
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR $PYSETUP_PATH
COPY . .

RUN poetry install --no-dev
RUN poetry build


FROM python-base as development

COPY --from=builder-base $POETRY_HOME $POETRY_HOME
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

COPY ./docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

WORKDIR $PYSETUP_PATH
RUN poetry install

WORKDIR /app
COPY . .

CMD ["/docker-entrypoint.sh"]


FROM python-base as production

COPY --from=builder-base $VENV_PATH $VENV_PATH
COPY --from=builder-base $PYSETUP_PATH/dist .
RUN pip install *.whl

COPY ./docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

WORKDIR /app
COPY ./manage.py ./



CMD ["/docker-entrypoint.sh"]


# FROM python:3.9 as base

# ENV PYTHONFAULTHANDLER=1 \
#     PYTHONHASHSEED=random \
#     PYTHONUNBUFFERED=1

# # RUN apt-get update && apt-get install -y gcc libffi-dev g++
# WORKDIR /app


# FROM base as builder

# ENV PIP_DEFAULT_TIMEOUT=100 \
#     PIP_DISABLE_PIP_VERSION_CHECK=1 \
#     PIP_NO_CACHE_DIR=1 \
#     POETRY_VERSION=1.4.0

# RUN pip install "poetry==${POETRY_VERSION}"
# RUN python -m venv /venv

# COPY pyproject.toml poetry.lock ./
# RUN . /venv/bin/activate && poetry install --no-dev --no-root

# COPY . .
# RUN . /venv/bin/activate && poetry build

# FROM base as final

# COPY --from=builder /venv /venv
# COPY --from=builder /app/dist .
# COPY docker-entrypoint.sh manage.py ./

# RUN . /venv/bin/activate && pip install *.whl
# CMD ["./docker-entrypoint.sh"]
