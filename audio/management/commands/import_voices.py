import pandas as pd
from django.core.management.base import BaseCommand

from audio.models import Play_ht_voices, LanguageMapping


class Command(BaseCommand):
    help = "Import language from a CSV file into the Play_ht_voices model"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="The path to the CSV file")

    def handle(self, *args, **options):
        df = pd.read_csv(options["csv_file"])
        for _, row in df.iterrows():
            language_mapping_instance = LanguageMapping.objects.filter(
                mapped_language=row["語種"]
            ).first()
            if not language_mapping_instance:
                self.stdout.write(
                    self.style.ERROR(
                        f"No LanguageMapping found for language: {row['語種']}"
                    )
                )
                continue

            Play_ht_voices.objects.create(
                language_mapping=language_mapping_instance,
                voice=row["playht聲音代碼"],
                voice_url=row["playht聲音試聽url"],
            )
        self.stdout.write(self.style.SUCCESS("Data imported successfully"))
