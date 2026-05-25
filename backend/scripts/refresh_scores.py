import asyncio
import logging
import sys
import os

# Add root directory to path for imports
sys.path.append(os.getcwd())

from backend.database.mongo import mongo
from backend.agents.cv_agent import cv_agent
from backend.services.embedding_service import embedding_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def refresh_all_scores():
    logger.info("🚀 Starting bulk score refresh with semantic matching...")
    
    # 1. Initialize MongoDB and Embedding Service
    await mongo.connect()
    
    # Wait for embedding service to be ready
    if not embedding_service.ready:
        logger.error("❌ Embedding service not ready. Cannot perform semantic matching.")
        return

    # 2. Fetch all candidates
    candidates = await mongo.list_candidates(limit=1000)
    logger.info(f"Found {len(candidates)} candidates to update.")
    
    updated_count = 0
    
    # 3. Process each candidate
    for candidate in candidates:
        try:
            cand_id = candidate.get("id")
            name = candidate.get("full_name", "Unknown")
            old_score = candidate.get("score", {}).get("total_score", 0)
            
            # Prepare 'parsed' data structure from candidate document
            parsed_data = {
                "skills": candidate.get("skills", []),
                "experience": candidate.get("experience", []),
                "years_experience": candidate.get("years_experience", 0),
                "education": candidate.get("education", []),
                "languages": candidate.get("languages", []),
                "summary": candidate.get("summary", ""),
            }
            
            github_data = candidate.get("github_profile")
            
            # NOTE: We don't have job context here, so we score against general breadth
            # unless we find a way to get required_skills for their applied position.
            # However, even general breadth now uses semantic logic for skill categorization.
            
            # Re-calculate score using the new logic
            new_score_data = cv_agent._score_candidate(
                parsed=parsed_data,
                github_data=github_data,
                required_skills=None, # Default to breadth if no specific job context
                score_weights=None    # Use default weights
            )
            
            new_score = new_score_data.get("total_score", 0)
            
            # 4. Update MongoDB
            await mongo.update_candidate(cand_id, {"score": new_score_data})
            
            logger.info(f"✅ Updated {name} ({cand_id}): {old_score} -> {new_score}")
            updated_count += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to update candidate {candidate.get('id')}: {e}")

    logger.info(f"✨ Finished! Updated {updated_count}/{len(candidates)} candidates.")
    await mongo.disconnect()

if __name__ == "__main__":
    asyncio.run(refresh_all_scores())
