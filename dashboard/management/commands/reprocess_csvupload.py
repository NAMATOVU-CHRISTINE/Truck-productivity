from django.core.management.base import BaseCommand, CommandError
from dashboard.models import CSVUpload
from dashboard.views import process_csv_file

class Command(BaseCommand):
    help = 'Reprocess a CSVUpload by its ID (re-runs the processing logic on the uploaded file)'

    def add_arguments(self, parser):
        parser.add_argument('upload_id', type=int, help='ID of the CSVUpload to reprocess')

    def handle(self, *args, **options):
        upload_id = options['upload_id']
        try:
            csv_upload = CSVUpload.objects.get(id=upload_id)
        except CSVUpload.DoesNotExist:
            raise CommandError(f'CSVUpload with id {upload_id} does not exist.')

        self.stdout.write(self.style.NOTICE(f'Reprocessing CSVUpload: {csv_upload}'))
        success = process_csv_file(csv_upload)
        if success:
            self.stdout.write(self.style.SUCCESS('Successfully reprocessed.'))
        else:
            self.stdout.write(self.style.ERROR('Error during reprocessing. Check logs for details.'))
