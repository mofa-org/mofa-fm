import os
import django
import sys

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.podcasts.models import Category

def seed():
    if not Category.objects.filter(slug="tech").exists():
        Category.objects.create(name="Tech", slug="tech")
        print("Created category: Tech")
    else:
        print("Category 'Tech' already exists")

if __name__ == "__main__":
    seed()
