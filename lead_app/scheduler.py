"""
PythonAnywhere Always-On Task entry point.
Configure as an Always-On Task pointing to: python /path/to/lead_app/scheduler.py
"""
import sys
import os
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger('scheduler')

project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

import schedule
from app import create_app

app = create_app('production')


def run_gmail_poll():
    with app.app_context():
        try:
            from services.gmail_service import poll_gmail
            poll_gmail()
        except Exception as e:
            logger.error(f'Gmail poll error: {e}', exc_info=True)


def run_truncation_check():
    with app.app_context():
        try:
            from services.truncation_service import check_and_run
            check_and_run()
        except Exception as e:
            logger.error(f'Truncation check error: {e}', exc_info=True)


schedule.every(60).seconds.do(run_gmail_poll)
schedule.every(1).minutes.do(run_truncation_check)

if __name__ == '__main__':
    logger.info('Scheduler starting — running initial Gmail poll...')
    run_gmail_poll()
    logger.info('Entering schedule loop (Gmail every 60s, truncation check every 1m)')
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error(f'Unexpected scheduler error: {e}', exc_info=True)
        time.sleep(1)
