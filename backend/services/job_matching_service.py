import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from backend.services.llm_service import generate_response
from backend.database.mongo import mongo
from backend.models.job_offer import JobOffer

logger = logging.getLogger(__name__)

class JobMatchingService:
    """Service to evaluate how well a candidate matches a specific Job Offer using LLM."""

    def __init__(self):
        self.system_prompt = """
You are an expert HR Recruitment Assistant. Your role is exclusively to evaluate a candidate's profile against a specific Job Offer and determine how well they match.
You will be provided with:
1. The Job Offer Details (Title, Description, and required criteria).
2. The Candidate's Profile (Skills, Experience, Education, and parsed CV text).

Your task is to analyze the candidate against the Job Offer and return a JSON object with the following fields:
{
  "score": <integer from 0 to 100 representing the match percentage>,
  "justification": "<string explaining why this score was given>",
  "met_criteria": ["<list of strings detailing which criteria the candidate successfully met>"],
  "missing_criteria": ["<list of strings detailing which criteria the candidate lacks>"]
}

Important Rules:
- Output ONLY valid JSON, with no markdown formatting like ```json or newlines around it, just the raw JSON structure that Python can json.loads().
- Be objective and strict. If a "must-have" skill is completely missing, the score should drop significantly.
- Consider synonymous technologies (e.g. if offer asks for VueJS and candidate has React, they might partially meet it but note it in justification).
"""

    async def evaluate_candidate_for_offer(self, candidate_id: str, offer_id: str) -> Optional[Dict[str, Any]]:
        """Evaluate a specific candidate against a specific job offer and return the evaluation."""
        logger.info(f"Evaluating candidate {candidate_id} for offer {offer_id}")
        
        candidate = await mongo.get_candidate(candidate_id)
        if not candidate:
            logger.error(f"Candidate {candidate_id} not found.")
            return None
            
        offer_data = await mongo.get_job_offer(offer_id)
        if not offer_data:
            logger.error(f"Job offer {offer_id} not found.")
            return None
            
        # Prepare Candidate Summary
        candidate_summary = {
            "name": candidate.get("full_name"),
            "skills": [s.get("name") if isinstance(s, dict) else s for s in candidate.get("skills", [])],
            "experience": candidate.get("experience"),
            "education": candidate.get("education"),
            "summary": candidate.get("summary")
        }
        
        # Prepare Offer Summary
        criteria = offer_data.get("criteria", {})
        offer_summary = {
            "title": offer_data.get("title"),
            "description": offer_data.get("description"),
            "must_have_skills": criteria.get("must_have_skills", []),
            "nice_to_have_skills": criteria.get("nice_to_have_skills", []),
            "min_years_experience": criteria.get("min_years_experience", 0)
        }
        
        user_prompt = f"JOB OFFER:\n{json.dumps(offer_summary, indent=2)}\n\nCANDIDATE PROFILE:\n{json.dumps(candidate_summary, indent=2)}"
        
        llm_response = generate_response(self.system_prompt, user_prompt)
        
        if not llm_response:
            logger.error("LLM failed to return a response for job matching")
            return None
            
        try:
            # Clean up potential markdown formatting if the LLM ignores instructions
            cleaned_response = llm_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
                
            evaluation = json.loads(cleaned_response.strip())
            
            # Save the evaluation to the candidate document
            eval_record = {
                "offer_id": offer_id,
                "offer_title": offer_data.get("title"),
                "score": evaluation.get("score"),
                "justification": evaluation.get("justification"),
                "met_criteria": evaluation.get("met_criteria", []),
                "missing_criteria": evaluation.get("missing_criteria", []),
                "evaluated_at": datetime.utcnow().isoformat() if 'datetime' in globals() else None
            }
            
            # Fetch existing or create new list
            offer_evaluations = candidate.get("offer_evaluations", [])
            # Replace if already evaluated for this offer, else append
            offer_evaluations = [ev for ev in offer_evaluations if ev.get("offer_id") != offer_id]
            offer_evaluations.append(eval_record)
            
            await mongo.update_candidate(candidate_id, {"offer_evaluations": offer_evaluations})
            return eval_record
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON output: {e}\nRaw output: {llm_response}")
            return None
        except Exception as e:
            logger.error(f"Error during job matching evaluation: {e}")
            return None

job_matching_service = JobMatchingService()
