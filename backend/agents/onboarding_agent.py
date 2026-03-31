"""
Onboarding Agent: Generates onboarding checklists, welcome messages,
and initial employee profile setup.
"""
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import date, timedelta

logger = logging.getLogger(__name__)


ONBOARDING_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "it_setup": [
        {"title": "Issue laptop and equipment", "assigned_to": "IT", "due_days": 0},
        {"title": "Create company email account", "assigned_to": "IT", "due_days": 0},
        {"title": "Grant access to required systems", "assigned_to": "IT", "due_days": 1},
        {"title": "Setup VPN and security tools", "assigned_to": "IT", "due_days": 1},
        {"title": "Install required software", "assigned_to": "IT", "due_days": 2},
    ],
    "hr_admin": [
        {"title": "Complete employment contract signing", "assigned_to": "HR", "due_days": 0},
        {"title": "Setup payroll and banking details", "assigned_to": "HR", "due_days": 1},
        {"title": "Enroll in health insurance and benefits", "assigned_to": "HR", "due_days": 3},
        {"title": "Complete compliance training (GDPR, security)", "assigned_to": "HR", "due_days": 5},
        {"title": "ID badge and access card issuance", "assigned_to": "HR", "due_days": 0},
    ],
    "manager_tasks": [
        {"title": "Schedule 1:1 introduction meeting", "assigned_to": "Manager", "due_days": 0},
        {"title": "Introduce to team members", "assigned_to": "Manager", "due_days": 0},
        {"title": "Set 30/60/90 day goals", "assigned_to": "Manager", "due_days": 3},
        {"title": "Assign buddy/mentor", "assigned_to": "Manager", "due_days": 1},
        {"title": "Review team workflows and processes", "assigned_to": "Manager", "due_days": 5},
    ],
    "employee_tasks": [
        {"title": "Read employee handbook", "assigned_to": "Employee", "due_days": 2},
        {"title": "Complete company culture orientation", "assigned_to": "Employee", "due_days": 3},
        {"title": "Set up profile in HR system", "assigned_to": "Employee", "due_days": 1},
        {"title": "Attend department introduction sessions", "assigned_to": "Employee", "due_days": 5},
        {"title": "Shadow team members for role understanding", "assigned_to": "Employee", "due_days": 7},
    ],
    "engineering": [
        {"title": "Join engineering Slack channels", "assigned_to": "IT", "due_days": 0},
        {"title": "Clone and setup development repositories", "assigned_to": "Employee", "due_days": 2},
        {"title": "Review architecture documentation", "assigned_to": "Employee", "due_days": 5},
        {"title": "Complete first task/ticket", "assigned_to": "Employee", "due_days": 14},
        {"title": "Participate in code review process", "assigned_to": "Employee", "due_days": 7},
    ],
}


class OnboardingAgent:
    """
    Generates comprehensive onboarding plans for new employees.
    """

    def create_onboarding_plan(
        self,
        employee_id: str,
        employee_name: str,
        department: str,
        job_title: str,
        start_date: date,
        manager_name: Optional[str] = None,
        buddy_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a complete onboarding plan for a new hire."""
        logger.info(f"Creating onboarding plan for {employee_name} in {department}")

        tasks = []

        # Always include core tasks
        for category in ["it_setup", "hr_admin", "manager_tasks", "employee_tasks"]:
            for task_template in ONBOARDING_TEMPLATES[category]:
                task = {
                    "task_id": str(uuid.uuid4()),
                    "title": task_template["title"],
                    "description": f"Required onboarding step for {employee_name}",
                    "assigned_to": task_template["assigned_to"],
                    "due_days": task_template["due_days"],
                    "due_date": (start_date + timedelta(days=task_template["due_days"])).isoformat(),
                    "is_completed": False,
                    "completed_at": None,
                }
                tasks.append(task)

        # Department-specific tasks
        dept_lower = department.lower()
        if any(d in dept_lower for d in ["engineer", "tech", "dev", "software", "it"]):
            for task_template in ONBOARDING_TEMPLATES["engineering"]:
                tasks.append({
                    "task_id": str(uuid.uuid4()),
                    "title": task_template["title"],
                    "description": f"Engineering-specific onboarding for {employee_name}",
                    "assigned_to": task_template["assigned_to"],
                    "due_days": task_template["due_days"],
                    "due_date": (start_date + timedelta(days=task_template["due_days"])).isoformat(),
                    "is_completed": False,
                    "completed_at": None,
                })

        # Sort by due date
        tasks.sort(key=lambda x: x["due_days"])

        welcome_message = self._generate_welcome_message(
            employee_name, department, job_title, start_date, manager_name
        )

        plan = {
            "id": str(uuid.uuid4()),
            "employee_id": employee_id,
            "employee_name": employee_name,
            "department": department,
            "job_title": job_title,
            "start_date": start_date.isoformat(),
            "tasks": tasks,
            "total_tasks": len(tasks),
            "welcome_message": welcome_message,
            "buddy_assigned": buddy_name,
            "manager": manager_name,
            "timeline": "30-day onboarding program",
            "milestones": self._get_milestones(start_date),
        }

        logger.info(f"Onboarding plan created with {len(tasks)} tasks")
        return plan

    def _generate_welcome_message(
        self,
        name: str,
        department: str,
        job_title: str,
        start_date: date,
        manager: Optional[str] = None,
    ) -> str:
        return f"""
🎉 **Welcome to the Team, {name}!**

We are thrilled to have you join us as **{job_title}** in the **{department}** department.

Your first day is **{start_date.strftime('%A, %B %d, %Y')}**.
{f"You will be reporting to **{manager}**." if manager else ""}

**What to expect on Day 1:**
• Orientation session with HR
• Meet your team and manager
• Equipment setup with IT
• Office tour and introductions

**Resources you'll need:**
• Employee Handbook
• IT Setup Guide
• Company Benefits Portal
• HR Self-Service Portal

We believe you'll make an incredible contribution to our team. Don't hesitate to ask questions – that's what we're here for!

Warm regards,
**The HR Team** 🌟
        """.strip()

    @staticmethod
    def _get_milestones(start_date: date) -> List[Dict[str, str]]:
        return [
            {
                "milestone": "Day 1 – First Day Complete",
                "date": start_date.isoformat(),
                "description": "Administrative setup, introductions, system access",
            },
            {
                "milestone": "Week 1 – Foundation",
                "date": (start_date + timedelta(days=7)).isoformat(),
                "description": "Tools set up, team met, initial training completed",
            },
            {
                "milestone": "Month 1 – Integration",
                "date": (start_date + timedelta(days=30)).isoformat(),
                "description": "Contributing to projects, workflows understood",
            },
            {
                "milestone": "Month 3 – Independence",
                "date": (start_date + timedelta(days=90)).isoformat(),
                "description": "Fully productive, goals set and progressing",
            },
        ]


onboarding_agent = OnboardingAgent()
