from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from myapp.models import Certificate, Project


class Command(BaseCommand):
    help = (
        "Upload existing local Project/Certificate media to the configured "
        "Django storage (Cloudinary in production) when the local file exists."
    )

    def _sync_instance(self, instance):
        field = instance.image

        if not field or not field.name:
            return False

        local_path = Path(settings.MEDIA_ROOT) / field.name

        if not local_path.is_file():
            self.stdout.write(
                self.style.WARNING(
                    f"SKIP: local file not found: {local_path}"
                )
            )
            return False

        # If the file is already on Cloudinary, saving it again is unnecessary.
        # For local FileSystemStorage this also safely leaves the existing file.
        storage = field.storage
        if storage.__class__.__module__.startswith("cloudinary_storage"):
            try:
                if storage.exists(field.name):
                    self.stdout.write(f"OK: {field.name}")
                    return False
            except Exception as exc:
                self.stdout.write(
                    self.style.WARNING(
                        f"Cloudinary existence check failed for {field.name}: {exc}"
                    )
                )

        old_name = field.name
        with local_path.open("rb") as file_obj:
            field.save(
                Path(old_name).name,
                File(file_obj),
                save=False,
            )

        instance.save(update_fields=["image"])

        self.stdout.write(
            self.style.SUCCESS(
                f"SYNCED: {old_name} -> {field.name}"
            )
        )
        return True

    def handle(self, *args, **options):
        if not settings.CLOUDINARY_CONFIGURED:
            self.stdout.write(
                self.style.WARNING(
                    "Cloudinary credentials are not configured. "
                    "Skipping media sync."
                )
            )
            return

        changed = 0

        for project in Project.objects.all():
            if self._sync_instance(project):
                changed += 1

        for certificate in Certificate.objects.all():
            if self._sync_instance(certificate):
                changed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Media sync complete. {changed} file(s) uploaded/updated."
            )
        )
