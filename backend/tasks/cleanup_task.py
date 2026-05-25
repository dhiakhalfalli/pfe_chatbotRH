"""
Cleanup Task: Suppression automatique des données personnelles sensibles
72 heures après le traitement IA. Conformité RGPD - Article 5(1)(e).
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

RETENTION_HOURS = 72  # Durée de conservation après traitement


async def cleanup_expired_candidate_data(dry_run: bool = False) -> dict:
    """
    Anonymise/supprime les données PII des candidats dont le traitement
    est terminé depuis plus de RETENTION_HOURS heures.

    Args:
        dry_run: Si True, simule sans modifier la base de données.

    Returns:
        Rapport de nettoyage avec le nombre de candidats traités.
    """
    from backend.database.mongo import MongoDB
    from backend.agents.privacy_agent import privacy_agent

    cutoff = datetime.now(timezone.utc) - timedelta(hours=RETENTION_HOURS)
    candidates = await MongoDB.list_candidates(limit=1000)

    processed = 0
    skipped = 0
    errors = 0
    deleted_ids = []

    for c in candidates:
        # Ignorer les candidats déjà nettoyés
        if c.get("data_deleted", False):
            skipped += 1
            continue

        # Ignorer les candidats sans date de traitement
        processed_at_str = c.get("processed_at") or c.get("created_at")
        if not processed_at_str:
            skipped += 1
            continue

        try:
            # Normaliser la date
            processed_at = datetime.fromisoformat(
                processed_at_str.replace("Z", "+00:00")
            )
            if processed_at.tzinfo is None:
                processed_at = processed_at.replace(tzinfo=timezone.utc)

            # Vérifier si la période de rétention est dépassée
            if processed_at < cutoff:
                if dry_run:
                    logger.info(f"[DRY RUN] Would delete PII for candidate {c['id']}")
                    processed += 1
                    deleted_ids.append(c["id"])
                else:
                    result = await privacy_agent.delete_sensitive_data(c["id"])
                    if result.get("status") == "deleted":
                        processed += 1
                        deleted_ids.append(c["id"])
                        logger.info(f"✅ PII deleted for candidate {c['id']}")
                    else:
                        errors += 1
            else:
                skipped += 1
        except Exception as e:
            logger.error(f"Error processing candidate {c.get('id')}: {e}")
            errors += 1

    report = {
        "status": "completed",
        "dry_run": dry_run,
        "retention_hours": RETENTION_HOURS,
        "cutoff_date": cutoff.isoformat(),
        "processed": processed,
        "skipped": skipped,
        "errors": errors,
        "deleted_candidate_ids": deleted_ids,
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        f"Cleanup task completed: {processed} deleted, "
        f"{skipped} skipped, {errors} errors"
    )
    return report


async def cleanup_orphan_cv_files() -> dict:
    """
    Supprime les fichiers CV physiques dont les données ont déjà été
    anonymisées dans MongoDB. Libère l'espace disque.
    """
    import os
    from pathlib import Path
    from backend.database.mongo import MongoDB
    from backend.config.settings import settings

    upload_dir = Path(settings.CV_UPLOAD_DIR)
    if not upload_dir.exists():
        return {"status": "skipped", "reason": "Upload directory does not exist"}

    candidates = await MongoDB.list_candidates(limit=1000)
    deleted_candidate_ids = {
        c["id"] for c in candidates if c.get("data_deleted", False)
    }

    deleted_files = []
    errors = []

    for cv_file in upload_dir.iterdir():
        if not cv_file.is_file():
            continue
        # Le nom de fichier contient l'ID candidat (format: {uuid}_{filename})
        for cid in deleted_candidate_ids:
            if cid[:8] in cv_file.name:
                try:
                    os.remove(cv_file)
                    deleted_files.append(cv_file.name)
                    logger.info(f"🗑️  Deleted orphan CV file: {cv_file.name}")
                except Exception as e:
                    errors.append(str(e))
                break

    return {
        "status": "completed",
        "deleted_files": deleted_files,
        "deleted_count": len(deleted_files),
        "errors": errors,
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }
