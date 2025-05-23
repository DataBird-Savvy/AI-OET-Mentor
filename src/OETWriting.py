import random
import re

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from logger import logging
from exception import OETException
import sys



load_dotenv()


class OETWritingTaskAssistant:
    def __init__(self):
        """Initialize the OET Writing Task Assistant with Google GenAI client."""
        logging.info("Initializing OET Writing Task Assistant...")
        try:
            
            self.client = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash")
            self.task_question = self.generate_task_question()
            logging.info("Initial task question generated successfully.")
        except Exception as e:
            raise OETException(e, sys)
            

    def extract_time(self, task):
        """Extract the time allowed from a writing task using regex."""
        logging.info("Extracting time allowed from the task...")
        try:
            time_pattern = r"\*\*Time allowed:\*\*\s*(\d+)\s*minutes"
            match = re.search(time_pattern, task)
            if match:
                return int(match.group(1))
            logging.warning("No time pattern matched in the task.")
            return None
        except Exception as e:
            raise OETException(e, sys)

    def generate_score(self, task_text):
        """Generate a score for the writing task."""
        logging.info("Generating score for the writing task...")
        try:
            response = self.client.invoke(
                f"Evaluate the quality of the following OET writing task and provide a score from 1 to 10:\n{task_text}"
            )
            response_md = response.content.strip('```json\n').strip('```').strip()
            logging.info("Score generation successful.")
            return response_md
        except Exception as e:
            raise OETException(e, sys)

    def generate_task_question(self):
        """Generate a complete OET writing task prompt with case notes and a task."""
        logging.info("Generating new OET writing task question...")
        try:
            prompt = """Create detailed patient case notes and a corresponding writing task for the OET Nursing Writing Test. Follow the structured format for the case notes and ensure the writing task aligns with OET standards.

    # Steps

    1. **Create Detailed Patient Case Notes**:
    - Use the following structured format with sections and subsections:
    - **Patient Name**
    - Patient Details
    - **Social Background**
    - **Medical Background**
    - **Medications**
    - **Nursing Management and Progress**
    - **Discharge Plan**
    - Case notes should be concise and in point form under each section and subsection.
    - donot provide any examples or format

    2. **Develop a Writing Task**:
    - Provide clear instructions for candidates to draft a formal letter using the case notes.
    - Choose a recipient category from the following:
    1. **Referring Healthcare Professional**: e.g., write to Dr. Emily Carter regarding patient follow-up care.
    2. **Patient or Family Member**: explain post-operative care instructions.
    3. **Senior Nurse (Nursing Home)**: discuss ongoing post-operative care needs.
    4. **Hospital Discharge Planner or Social Worker**: organize home care post-surgery.
    5. **Health Insurance Company**: justify a treatment or medication claim.
    6. **School or Employer**: explain medical leave requirements and return dates.

    3. **Align Content with OET Standards**:
    - Ensure content complexity and detail match OET standards.
    - Instruct candidates to expand notes into full sentences and follow a formal letter format.

    # Output Format
    - Begin with detailed case notes, fully structured into sections.
    - Follow with a concise writing task description in 1–2 sentences.
    
    # Notes
    - Maintain **h4** and **bold** style consistency for headings 'Notes' and 'Writing task' in dark grey box with white letter.
    - Ensure tone and style match OET standards.
    - Address specific recipient requirements with bold letter and line by line.

    """
            task_question = self.client.invoke(prompt)
            response_md = task_question.content.strip('```json\n').strip('```').strip()
            logging.info("Task question generated successfully.")
            return response_md
        except Exception as e:
            raise OETException(e, sys)

    def get_feedback_and_score(self, task_text):
        """Get both feedback and score for a given OET writing task."""
        logging.info("Getting feedback and score for submitted task...")
        try:
            if not task_text:
                return "Please provide a valid writing task.", None

            feedback = self.generate_score(task_text)
            return feedback
        except Exception as e:
            raise OETException(e, sys)

    def get_next_question(self):
        """Fetch a new writing task question."""
        logging.info("Fetching next writing task question...")
        try:
            self.task_question = self.generate_task_question()
            return self.task_question
        except Exception as e:
            raise OETException(e, sys)
