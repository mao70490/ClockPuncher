import asyncio
from logs.logger import setup_logger
from clock.scheduler import schedule_today_jobs

logger = setup_logger(__name__, "logs/puncher.log")

def schedule_job_wrapper(puncher, checker, scheduler, network):
    """
    APScheduler job 專用
    永遠不丟例外
    """
    try:
        asyncio.run(
            schedule_today_jobs(puncher, checker, scheduler, network)
        )
    except Exception:
        logger.exception("[SCHEDULE JOB FAILED]")