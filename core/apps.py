from django.apps import AppConfig
import os

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        # Only run on main process
        if os.environ.get('RUN_MAIN'):
            try:
                # Initialize cache after Django is fully loaded
                from core.cache_utils import cache_exam_questions
                cache_exam_questions()
                
                # Start the background scheduler
                from job_portal_exam.scheduler import start
                start()
            except Exception as e:
                print(f"Error during app initialization: {str(e)}")
                # Don't raise the exception, allow Django to continue starting

    