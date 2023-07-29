#!/bin/bash
# basic reference for writing script for travis

# rm db.sqlite3
# python manage.py migrate

# FIXME: add sample data for deveopment
python manage.py import_language_mapping language/language.csv
python manage.py import_voices language/voices.csv
