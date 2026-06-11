#!/usr/bin/env python3
"""
Daily Airtable sync + GitHub backup.
Run once per day at 6:05 PM WAT (after the last email trigger).
"""
import sys, os, logging
from datetime import datetime

sys.path.insert(0, "/home/user/workspace")
from local_db import init_db, backup_to_github, sync_to_airtable, get_stats, load_env

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)
load_env()


def main():
    # Only run around 6pm WAT (17:00 UTC) — allow 16:50-17:10 window
    current_hour = datetime.utcnow().hour
    if current_hour != 17:
        logger.info("Not sync time (expected 17:00 UTC). Current hour: " + str(current_hour) + ". Skipping.")
        return

    init_db()
    stats = get_stats()
    logger.info("DB stats: " + str(stats))

    # 1. Sync to Airtable
    logger.info("=== Airtable Sync ===")
    synced = sync_to_airtable()
    logger.info("Airtable sync: " + str(synced) + " records")

    # 2. Backup to GitHub
    logger.info("=== GitHub Backup ===")
    backup_ok = backup_to_github()
    logger.info("GitHub backup: " + ("OK" if backup_ok else "FAILED"))

    # Final stats
    final_stats = get_stats()
    logger.info("Final stats: " + str(final_stats))


if __name__ == "__main__":
    main()
