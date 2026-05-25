/**
 * Default job offers used as fallback when the backend has no jobs stored.
 * These are automatically seeded into the API on startup if the DB is empty.
 * They appear both on the Job Positions page and in the Candidate Ranking dropdown.
 */
export const DEFAULT_JOBS = [
    {
        id: 'default-1',
        title: 'Développeur Python',
        location: 'France',
        experience: '3+ ans',
        source: 'Offre interne',
        description: 'Développement et maintenance d\'applications Python. Intégration de microservices. Tests unitaires et CI/CD.',
        skills: ['Python', 'Django', 'FastAPI', 'PostgreSQL', 'Docker'],
        criteria: {
            must_have_skills: ['Python', 'Django', 'FastAPI', 'PostgreSQL', 'Docker'],
            min_years_experience: 3,
        },
    },
    {
        id: 'default-2',
        title: 'Ingénieur Logiciel Java',
        location: 'Maroc / Remote',
        experience: '2+ ans',
        source: 'Offre interne',
        description: 'Conception et développement d\'applications Java dans un environnement Agile/Scrum. Participation aux code reviews.',
        skills: ['Java', 'Spring Boot', 'Microservices', 'Kubernetes', 'REST API'],
        criteria: {
            must_have_skills: ['Java', 'Spring Boot', 'Microservices', 'Kubernetes'],
            min_years_experience: 2,
        },
    },
    {
        id: 'default-3',
        title: 'Ingénieur DevOps',
        location: 'Casablanca, Maroc',
        experience: '4+ ans',
        source: 'Offre interne',
        description: 'Automatisation des pipelines CI/CD. Gestion de l\'infrastructure cloud. Monitoring et alerting des systèmes.',
        skills: ['CI/CD', 'Jenkins', 'Ansible', 'Terraform', 'AWS', 'Docker'],
        criteria: {
            must_have_skills: ['CI/CD', 'Jenkins', 'Ansible', 'Terraform', 'AWS'],
            min_years_experience: 4,
        },
    },
    {
        id: 'default-4',
        title: 'Data Scientist',
        location: 'Paris, France',
        experience: '2+ ans',
        source: 'Offre interne',
        description: 'Analyse de données et développement de modèles de machine learning pour des cas d\'usage RH et métier.',
        skills: ['Python', 'Machine Learning', 'Pandas', 'Scikit-learn', 'SQL'],
        criteria: {
            must_have_skills: ['Python', 'Machine Learning', 'Pandas', 'SQL'],
            min_years_experience: 2,
        },
    },
    {
        id: 'default-5',
        title: 'Développeur React / Frontend',
        location: 'Tunis, Tunisie',
        experience: '2+ ans',
        source: 'Offre interne',
        description: 'Développement d\'interfaces utilisateur modernes et réactives avec React.',
        skills: ['React', 'JavaScript', 'TypeScript', 'CSS', 'REST API'],
        criteria: {
            must_have_skills: ['React', 'JavaScript', 'TypeScript'],
            min_years_experience: 2,
        },
    },
    {
        id: 'default-6',
        title: 'Ingénieur Cybersécurité',
        location: 'France / Remote',
        experience: '3+ ans',
        source: 'Offre interne',
        description: 'Analyse des vulnérabilités, tests de pénétration et mise en œuvre des politiques de sécurité.',
        skills: ['Cybersécurité', 'Pentest', 'Linux', 'Firewalls', 'SIEM'],
        criteria: {
            must_have_skills: ['Cybersécurité', 'Pentest', 'Linux'],
            min_years_experience: 3,
        },
    },
]
