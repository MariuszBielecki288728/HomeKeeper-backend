from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Save a graphene schema into a schema.graphql file"

    def handle(self, *args, **options):
        call_command(
            "graphql_schema",
            "--schema",
            "homekeeper.schema.schema",
            "--out",
            "schema.graphql",
        )
