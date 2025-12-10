#!/bin/bash
#
# A simple script to back up the SQLite database.
#

# --- Configuration ---
DATABASE_PATH="management_server/db/app.db"
BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
BACKUP_FILENAME="backup-${TIMESTAMP}.sql"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"

# --- Main Logic ---

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

echo "Starting database backup..."

# Check if the database file exists
if [ ! -f "${DATABASE_PATH}" ]; then
  echo "Error: Database file not found at ${DATABASE_PATH}"
  exit 1
fi

# Perform the backup using sqlite3 dump
sqlite3 "${DATABASE_PATH}" ".dump" > "${BACKUP_PATH}"

# Check if the backup was successful
if [ $? -eq 0 ]; then
  echo "✅ Backup successful!"
  echo "File created at: ${BACKUP_PATH}"
else
  echo "❌ Backup failed."
  # Clean up failed backup file
  rm -f "${BACKUP_PATH}"
  exit 1
fi

echo "Backup process finished."
