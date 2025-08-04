Original README.md's remain in their respective folders alongside a NOTES.md file compiled during each exercise.

## Initial Setup
```bash
git clone https://github.com/Thareus/digital_control_room/
```

## Setup for Django Exercise
```bash
cd digital_control_room/django/
python -m venv dcr-django-test-env
.dcr-django-test-env\Scripts\activate
pip install -r requirements.txt
cd dcr-django-test

python manage.py runserver
python manage.py update_country_listing
python manage.py test
```

## Setup for Javascript Exercise
```bash
cd digital_control_room/javascript/
python -m http.server
```

Open http://localhost:8000 in your browser.
