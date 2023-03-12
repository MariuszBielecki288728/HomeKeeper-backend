# HomeKeeper-backend

![CI](https://github.com/MariuszBielecki288728/HomeKeeper-backend/workflows/CI/badge.svg?branch=main) [![codecov](https://codecov.io/gh/MariuszBielecki288728/HomeKeeper-backend/branch/main/graph/badge.svg?token=7yzvV8BGGr)](https://codecov.io/gh/MariuszBielecki288728/HomeKeeper-backend)

Django backend that exposes GraphQL API for [HomeKeeper](https://github.com/Zjonn/HomeKeeper)

## Local development

To run this app locally you can run following command:

```bash
docker-compose up
```

Open your browser and go to [GraphiQL](http://localhost:8000/graphql/) - an interactive playground for HomeKeeper-backend API. Check out the `Docs` section on the right side to see what mutations and queries are available.

You can also install the application locally and run tests:

```bash
python3.9 -m venv ./venv/
source ./venv/bin/activate
pip install poetry
poetry install
python3 manage.py test
```
