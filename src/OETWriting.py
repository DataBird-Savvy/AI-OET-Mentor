from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from logger import logging
load_dotenv()
import re

class OETWritingTaskAssistant:
    def __init__(self):
        logging.info("Initializing the OET Writing Task Assistant with Google GenAI client")
        
        self.client = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
        self.task_question = self.generate_task_question()
        
    
    
    

    def generate_score(self, task_text):
        logging.info("Generating a score for the writing task.")
        
        response = self.client.invoke(
            f"Evaluate the quality of the following OET writing task and provide a score from 1 to 10:\n{task_text}"
        )
        response_md = response.content.strip('```json\n').strip('```').strip()
        return response_md

    def generate_task_question(self):
        
        prompt =""" Create detailed patient case notes and a corresponding writing task for the OET Nursing Writing Test. Follow the structured format for the case notes and ensure the writing task aligns with OET standards.

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
            - Follow with a concise writing task description in 1-2 sentences.

            # Examples
            - **Example Writing Task**:
            - Use the information in the case notes to draft a letter to Ms. Samantha Bruin, Senior Nurse at Greywalls Nursing Home, 27 Station Road, Greywalls, who will oversee Mr. Baker’s continued care at the Nursing Home.

            # Notes
            - Maintain **h4** and **bold** style consistency for headings 'Notes' and 'Writing task' in dark grey box with white letter.
            - Ensure tone and style match OET standards.
            - Address specific recipient requirements with bold letter and line by line.

            **In your answer:**
                - Expand the relevant notes into complete sentences
                - Do not use note form
                - Use letter format
            -The body of the letter should be approximately 180–200 words."""

        task_question = self.client.invoke(prompt)

        # print("task_question:",task_question)
        response_md = task_question.content.strip('```json\n').strip('```').strip()
        # print("task_md:",response_md)
        return response_md
    def get_feedback_and_score(self, task_text):
        logging.info("Getting both feedback and score for a given OET writing task")
        
        if not task_text:
            return "Please provide a valid writing task.", None
        feedback = None  
        feedback = self.generate_score(task_text)
        
        return feedback

   


   
