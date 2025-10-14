from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from .score_processor import process_pending_submissions

def start():
    scheduler = BackgroundScheduler()
    
    # Process submissions every 30 seconds
    scheduler.add_job(
        process_pending_submissions,
        'interval',
        seconds=30,
        kwargs={'batch_size': 50}
    )
    
    # Start the scheduler
    scheduler.start()