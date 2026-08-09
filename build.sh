python manage.py migrate
python manage.py loaddata myapp_data.json
python manage.py create_admin
python manage.py collectstatic --noinput
python manage.py sync_cloudinary_media