# Resets database and creates superuser as well as seeds the database

rm -f backend/db.sqlite3
python backend/manage.py migrate

# Create superuser
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=1234
export DJANGO_SUPERUSER_EMAIL=admin@example.com
venv/bin/python backend/manage.py createsuperuser --no-input --displayName "admin" --githubUrl "https://github.com/uofa-cmput404" 

python backend/manage.py seed
