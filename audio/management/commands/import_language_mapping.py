import pandas as pd
from django.core.management.base import BaseCommand

from audio.models import LanguageMapping


class Command(BaseCommand):
    help = "Import language from a CSV file into the LanguageMapping model"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="The path to the CSV file")

    def handle(self, *args, **options):
        df = pd.read_csv(options["csv_file"])
        for _, row in df.iterrows():
            if not LanguageMapping.objects.filter(
                original_language=row["deepl語種"]
            ).exists():
                LanguageMapping.objects.create(
                    original_language=row["deepl語種"],
                    mapped_language=row["play.ht語種"],
                )
        self.stdout.write(self.style.SUCCESS("Data imported successfully"))
