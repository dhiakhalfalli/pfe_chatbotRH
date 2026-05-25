import asyncio
import sys
import os

# Ensure backend can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.mongo import MongoDB

async def seed():
    await MongoDB.connect()
    
    jobs = [
        {
            'title': 'Développeur Python', 
            'location': 'France', 
            'description': 'Développement et maintenance d\'applications Python.', 
            'criteria': {
                'must_have_skills': ['Python', 'Django', 'FastAPI', 'PostgreSQL', 'Docker'], 
                'min_years_experience': 3
            }
        }, 
        {
            'title': 'Ingénieur Logiciel – Offre 1', 
            'location': 'Maroc / Remote', 
            'description': 'Conception et développement d\'applications Java dans un environnement Agile.', 
            'criteria': {
                'must_have_skills': ['Java', 'Spring Boot', 'Microservices', 'Kubernetes'], 
                'min_years_experience': 2
            }
        }, 
        {
            'title': 'Ingénieur DevOps – Offre 2', 
            'location': 'Casablanca, Maroc', 
            'description': 'Automatisation des pipelines CI/CD.', 
            'criteria': {
                'must_have_skills': ['CI/CD', 'Jenkins', 'Ansible', 'Terraform', 'AWS'], 
                'min_years_experience': 4
            }
        }
    ]
    
    for j in jobs:
        await MongoDB.insert_job_offer(j)
        
    print("Done seeding")

if __name__ == "__main__":
    asyncio.run(seed())
