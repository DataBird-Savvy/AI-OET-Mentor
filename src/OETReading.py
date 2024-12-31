import os
import json
from pinecone import Pinecone
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

import re
import sqlite3
from flask import  send_file, jsonify
import pandas as pd

from langchain_pinecone import PineconeVectorStore
from pydantic import BaseModel
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from groq import Groq
from typing import List
from openai import OpenAI
load_dotenv()

from openai import OpenAI


class Task(BaseModel):
    task: str
    options: List[str]
    correct_answer: str


class Passage(BaseModel):
    title: str
    passage: str
    tasks: List[Task]


class ResponseData(BaseModel):
    passages: List[Passage]    

class OETReadingTaskAssistant:
    def __init__(self):
        self.PINECONE_API = os.getenv("PINE_CONE_API")
        self.INDEX_NAME_A = os.getenv("INDEX_NAME_A")
        self.INDEX_NAME_C = os.getenv("INDEX_NAME_C")
        self.artifact_path = "static/artifacts"
        self.GROQ_API_KEY=os.getenv("GROQ_API_KEY")
        self.openai_client=OpenAI()
        self.ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY")
        pc = Pinecone(api_key=self.PINECONE_API )
        indexA = pc.Index(self.INDEX_NAME_A)
        indexC = pc.Index(self.INDEX_NAME_C)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.client = Groq(api_key=self.GROQ_API_KEY)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self.vector_storeA = PineconeVectorStore(index=indexA, embedding=embeddings)
        self.vector_storeC = PineconeVectorStore(index=indexC, embedding=embeddings)
        self.client_openai=OpenAI()
        
        
    def retrieve_context(self,topic,vectorstore,k=8):
        matching_results=vectorstore.similarity_search(topic,k=k)
        return matching_results
    
    
    
    def retrieve_taskA_prompt(self,topic):
        vectorstore=self.vector_storeA
        # Retrieve documents based on the query
        doc_search = self.retrieve_context(topic,vectorstore)
    
        # Concatenating page content of documents
        documents_text = "\n".join([doc.page_content for doc in doc_search])  
        
        # Prompt for generating OET Part A reading task in markdown format with complex numerical data
        prompt = f"""
        Generate a passage for the Occupational English Test (OET) Part A reading section based on the topic '{topic}' as a mock test. 
        The passage should be divided into four distinct sections (Text A, Text B, Text C, and Text D), each covering a different aspect or sub-topic related to the overall theme.

        Each section (Text A, Text B, Text C, and Text D) should be structured as a coherent passage of text, and only one of these sections should include a table with relevant data or information in **Markdown** format. 
        The table should present complex medical data, such as patient statistics, clinical trial results, or comparisons of treatment options. 
        It must include numerical data with appropriate units of measurement, and the columns and rows should be clearly labeled.

        The content should be derived from the following documents and reflect their key points:

        {documents_text}

        The passage should:
        - Start with a main heading.
        - Begin immediately with the content, without any introductory phrases like "Here is a passage for..." or "This is based on...".
        - Avoid any concluding phrases, such as "I hope this helps..." or "Good luck...".
        - Be structured strictly into four separate texts (Text A, Text B, Text C, and Text D), each covering different aspects of a specific medical topic.
        - Use advanced medical terminology, advanced English, and clinical concepts.
        - should have 250-300 words long.
        - Not include any questions.
        - Maintain a professional and clinical tone, appropriate for healthcare professionals.
        - Include detailed and accurate references to medical practices, symptoms, treatments, or case studies.
        - Ensure the table is well-organized with clear labels and appropriate units of measurement.
        - Avoid including any summaries, figures, conclusions, meta-instructional sentences, or notes.
        - Exclude any opening, closing, or descriptive statements such as "Here is a passage for..." or "Please note that...".
        - Include exactly one table.

        **Example of table structure in Markdown:**

        | Treatment | Group A (n=200) | Group B (n=200) | p-value  |
        |-----------|-----------------|-----------------|----------|
        | Drug A    | 85% (170)       | 75% (150)       | 0.03     |
        | Drug B    | 78% (156)       | 72% (144)       | 0.05     |
        | Placebo   | 55% (110)       | 52% (104)       | 0.2      |

        In this example, the table compares the efficacy of two drugs in clinical trials, with numerical results and statistical significance.
        """

        return prompt
    
    def retrieve_taskC_prompt(self, topic):
        vectorstore = self.vector_storeC
        # Retrieve documents based on the query
        doc_search = self.retrieve_context(topic, vectorstore)

        # Concatenating page content of documents
        documents_text = "\n".join([doc.page_content for doc in doc_search])

        # Prompt for generating OET Part C reading task in markdown format with a professional tone
        prompt = f"""
        Generate a detailed and professional reading passage for the Occupational English Test (OET) Part C reading section based on the topic '{topic}' as a mock test, adhering strictly to OET standards.

        The content should be derived from the following documents and reflect their key points:

        {documents_text}

        The passage should:
        - Begin with a main heading that is relevant to the topic.
        - Present the information in paragraph form without any subheadings.
        - Use advanced medical terminology and complex English language, suitable for healthcare professionals.
        - Be at least 500 words in length and maintain a clinical and professional tone throughout.
        - Avoid introductory or concluding remarks such as "Here is a passage for..." or "I hope this helps...".
        - Include challenging and contextually rich content with a focus on critical thinking.
        - Maintain accuracy and relevance, using key insights from the provided documents.
        """

        return prompt

    def rag_taskpart(self, input):
        chat_completion = self.client.chat.completions.create(
        messages=[{
            "role": "system",
            "content": f"{input}"
        }],
        
        
        model="llama-3.1-8b-instant",
        # model="llama3-8b-8192",
        
        # model="llama-3.2-3b-preview",
        # max_tokens=200 
    )
        response_task=chat_completion.choices[0].message.content
        
        return response_task
    
    
    
    def rag_taskpartQA(self, input):
        # Send the request to the AI model
        chat_completion = self.client.chat.completions.create(
            messages=[{
                "role": "system",
                "content": (
                    "You are a helpful assistant. Please provide the output strictly in JSON format. "
                    "Do not include any extra text or explanations. Ensure the JSON is valid and well-structured. "
                    f"{input}"
                )
            }],
            model="llama-3.1-8b-instant",
        )

        response_next_input = chat_completion.choices[0].message.content

        # Extract JSON portion
        start_index = response_next_input.find('{')
        end_index = response_next_input.rfind('}') + 1

        try:
            # Extract the JSON content
            json_text = response_next_input[start_index:end_index]
            
            # Clean up potential issues
            json_text = json_text.strip()  # Remove extra whitespace
            json_text = json_text.replace("\n", "").replace("\t", "")  # Remove control characters
            
            # Parse JSON
            json_output = json.loads(json_text)

            # Pretty print for debugging (optional)
            print(json.dumps(json_output, indent=4))

        except json.JSONDecodeError as e:
            print("Invalid JSON response:", response_next_input)
            print("Error:", e)
            json_output = None  # Return None or handle the fallback case

        return json_output
        
        # def rag_taskpartAQA(self, input):
        #     # print(input)
        #     response_next_input = self.genai_client.invoke(input)

        #     print("task_question:",response_next_input)
        #     response_next_input=response_next_input.content.strip('```json\n').strip('```').strip()
            
        #     print("json_text",response_next_input)
        #     json_output = json.loads(response_next_input)
            
        #     return json_output
        
    
    
    def retrieve_qaA_prompt(self, taskA_context):
               # Format the prompt string dynamically using f-string, ensuring correct escaping
        prompt_next = f"""
            You are tasked with generating questions for an OET Reading Test Part A. Based on the provided context below, generate **exactly 20 fill-in-the-blank questions** that strictly adhere to the OET Reading Test Part A format and guidelines.

            ### Context:
            {taskA_context}

            ### Guidelines:

            1. **Divide the questions into three sets** with specific instructions:
                - **Set 1: Questions 1-7**:
                    - Instruction: "For each question, 1-7, decide which text (A, B, C, or D) the information comes from. Write the letter A, B, C, or D in the space provided. You may use any letter more than once."
                    - Questions must require the user to identify *which text contains the specific information being asked about*. The blank (_____) must always appear at the end of the question.
                    - Questions must start with "Which Text" or "From which text".
                    
                - **Set 2: Questions 8-14**:
                    - Instruction: "Answer each of the questions, 8-14, with a word or short phrase from one of the texts. Each answer may include words, numbers, or both. Do not write full sentences."
                    - Questions should require concise answers, based on specific information from the context. The blank (_____) must always be placed at the end of the question.
                    
                - **Set 3: Questions 15-20**:
                    - Instruction: "Complete each of the sentences, 15-20, with a word or short phrase from one of the texts. Each answer may include words, numbers, or both."
                    - Questions must involve sentence completion, with the blank (_____) placed at the end or in the middle of the sentence for clarity.

            2. **Question Requirements**:
                - Each blank **must be exactly 5 underscores (_____)** without spaces around it.
                - Each question **must contain only one blank**.
                - **Blanks must not appear at the beginning of any question.**
                - Ensure all questions are clear, concise, and contextually accurate, strictly based on the provided context.

            3. **Output Format**:
                - Provide the questions and their answers in **JSON format, adhering to the following structure**:

            ```json
            {{
                "instruction1": "For each question, 1-7, decide which text (A, B, C, or D) the information comes from. Write the letter A, B, C, or D in the space provided. You may use any letter more than once.",
                "set1": [
                    {{"1": "Which text discusses the issue of data on limb salvage? _____", "correct_answer": "A"}},
                    {{"2": "Which text provides information about the eligibility criteria for clinical trials? _____", "correct_answer": "C"}}
                ],
                "instruction2": "Answer each of the questions, 8-14, with a word or short phrase from one of the texts. Each answer may include words, numbers, or both. Do not write full sentences.",
                "set2": [
                    {{"8": "What is the duration of the treatment? _____", "correct_answer": "6 months"}},
                    {{"9": "What is the recommended daily dosage? _____", "correct_answer": "10 mg"}}
                ],
                "instruction3": "Complete each of the sentences, 15-20, with a word or short phrase from one of the texts. Each answer may include words, numbers, or both.",
                "set3": [
                    {{"15": "The procedure should be completed within _____ weeks.", "correct_answer": "4 weeks"}},
                    {{"16": "Patients are advised to avoid strenuous activity for at least _____ post-surgery.", "correct_answer": "2 weeks"}}
                ]
            }}


            ```
            - **Ensure proper JSON formatting with no trailing commas or syntax errors**.

        4. **Key Instructions**:
            - **Do not include explanations, notes, or additional content outside the JSON output.**
            - Ensure all questions are formatted correctly and comply with the structure and style of the OET Reading Test Part A.

        """

        return prompt_next

    
    def retrieve_qaC_prompt(self, taskC_context):
        prompt_next = f"""
            Generate **one task** with 6 multiple-choice questions (MCQs) for an OET Reading Test Part C.

            Each question must:
            - Have a clear question and four options (one correct answer, three distractors).
            - Include options formatted as a JSON array with prefixes ("a)", "b)", etc.).
            - Specify the correct answer as the **exact text of the correct option**.
            - Every opening quotation mark has a corresponding closing quotation mark.
            - Every opening bracket has a corresponding closing bracket.

            ### Context:
            {taskC_context}

            ### Output Format:
            ```json
            {{
                "task": {{
                    "questions": [
                        {{
                            "question": "First question based on the passage.",
                            "options": ["a) Option A", "b) Option B", "c) Option C", "d) Option D"],
                            "correct_answer": "b) Option B"
                        }},
                        {{
                            "question": "Second question based on the passage.",
                            "options": ["a) Option A", "b) Option B", "c) Option C", "d) Option D"],
                            "correct_answer": "c) Option C"
                        }},
                        ...# 4 more
                    ]
                }}
            }}
            ```"""

        return prompt_next
    def compare_answersB_to_dataframe(self, mcq_answers, correct_answers, total_marks):
        results = []
        marks_per_question = 1  # Set the mark per correct answer (adjust as needed)
        
        # Loop through each answer and check if it matches the correct answer
        for idx, mcq in enumerate(mcq_answers):
            
            selected_answer = mcq['answer'].split(')')[0]  # Get the letter before ')'
            print("selected_answer",selected_answer)
            answer_mapping = { '0': 'a', '1': 'b', '2': 'c'}
            selected_answer = answer_mapping.get(selected_answer, "Invalid answer") 
            print("selected_answer",selected_answer)
            print("correct_answers[idx] ",correct_answers[idx] )
            # Compare with the correct answer
            is_correct = 'Correct' if selected_answer == correct_answers[idx] else 'Incorrect'
            
            # If the answer is correct, add marks
            if is_correct == 'Correct':
                total_marks += marks_per_question
            
            # Append the result to the list
            results.append({
                'Question ID': idx+1,
                'Selected Answer': selected_answer,
                'Correct Answer': correct_answers[idx],
                'Result': is_correct
            })
    
        # Create a DataFrame from the results list
        df = pd.DataFrame(results)
        
        # Return the DataFrame along with the total marks
        return df, total_marks
    def convert_to_markdown(self,string_input):
        # Split the input string into relevant parts manually
        sections = string_input.strip().split('},\n    {')

        # Initialize an empty string for the final markdown content
        markdown_content = ""

        # Iterate over each section (each one represents an item in the array)
        for section in sections:
            # Clean up the section and split based on the content
            section = section.replace('"\n', '" ').replace('\n    ', ' ').strip("{}").strip()
            
            # Extract title and passage by splitting the content
            title_start = section.find('"title": "') + len('"title": "') 
            title_end = section.find('"', title_start)
            title = section[title_start:title_end]

            passage_start = section.find('"passage": "') + len('"passage": "') 
            passage_end = section.find('"', passage_start)
            passage = section[passage_start:passage_end]
            
            # Add the title and passage to markdown content
            markdown_content += f"## {title}\n\n**Passage:**\n{passage}\n\n"

            # Extract task information
            tasks_start = section.find('"tasks": [') + len('"tasks": [')
            tasks_end = section.find(']', tasks_start) + 1
            tasks_section = section[tasks_start:tasks_end]
            
            # Clean up and split tasks
            tasks = tasks_section.strip('["{}"]').split('},\n        {')
            for task in tasks:
                task = task.replace('"\n', '" ').strip("{}").strip()
                
                # Extract the task question, options, and the correct answer
                task_start = task.find('"task": "') + len('"task": "') 
                task_end = task.find('"', task_start)
                task_question = task[task_start:task_end]

                options_start = task.find('"options": [') + len('"options": [')
                options_end = task.find(']', options_start) + 1
                options_section = task[options_start:options_end]
                options = options_section.strip('[]').split('", "')

                correct_answer_start = task.find('"correct_answer": "') + len('"correct_answer": "') 
                correct_answer_end = task.find('"', correct_answer_start)
                correct_answer = task[correct_answer_start:correct_answer_end]

                # Add task details to markdown content
                markdown_content += f"### {task_question}\nOptions:\n"
                for option in options:
                    markdown_content += f"- {option}\n"
                markdown_content += f"**Correct Answer:** {correct_answer}\n\n"

        return markdown_content




    def retrive_B(self,prompt):
        response=self.openai_client.beta.chat.completions.parse(
        model="ft:gpt-3.5-turbo-0125:personal::AicLfVa6",# better model
       messages = [
            {
                "role": "system",
                "content": """
                Given an OET reading PartB test, provide the following fields in a JSON dict for each passage: 
                "title", "passage", "tasks" (with an array of tasks containing: "task", "options", and "correct_answer"). 
                Each passage should be followed by a task with options and the correct answer. 
                Ensure that each passage and task set is clearly structured in valid JSON format with unique keys for each title.
                Ensure the passage is only 3-4 sentences, avoiding verbosity.
                Ensure only one task for each passage with exactly 3 options.
                Ensure the output is a valid JSON object for each passage with the following format:
                [{"title":"<passage_title>","passage":"<passage_text>","tasks":[{"task":"<task_1>","options":["a) <opt1>","b) <opt2>","c) <opt3>"],"correct_answer":"<correct_option>"}]}]
                """
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
            )
            
        
        generated_json=response.choices[0].message.content
        print("generated_json",generated_json)
        print('type of generated_json',type(generated_json))
        # markdown_response=self.convert_to_markdown(generated_json)
        return generated_json

    def feedbacksub(self, corectanswer, useranswer, total_marks):
        # Create a mapping of question IDs to correct answers
        correct_answers_mapping = {
            str(i + 1): corectanswer[i]
            for i in range(len(corectanswer))
        }

        # Set marks per question (adjust as needed)
        marks_per_question = 1  # Marks for each correct answer
        
        # Prepare data for the DataFrame
        feedback_data = []
        for answer in useranswer:
            question_id = answer['questionId']
            user_answer = answer['answer']
            correct_answer = correct_answers_mapping.get(question_id, "No correct answer available")
            
            # Determine if the answer is correct and create feedback
            is_correct = user_answer == correct_answer
            feedback = "Correct" if is_correct else "Incorrect"
            
            # Add marks if the answer is correct
            if is_correct:
                total_marks += marks_per_question

            # Append data to the list
            feedback_data.append({
                "Question ID": question_id,
                "User Answer": user_answer,
                "Correct Answer": correct_answer,
                "Feedback": feedback
            })

        # Convert feedback data into a DataFrame
        feedback_df = pd.DataFrame(feedback_data)
        
        # Return the feedback DataFrame along with the updated total marks
        return feedback_df, total_marks
 
    def feedback(self, usrtxt_ans, ans_1_24,allmcqCorrectAnswersB,mcqAnswersB,correctAnswers_taskCQA1,mcq_answers_cqa1,correctAnswers_taskCQA2,mcq_answers_cqa2):
        
        print(f"usrtxt_ans:{usrtxt_ans},answer:{ans_1_24}")
        # print(f"usrmcq_ans:{usrmcq_ans},answer:{ans25_42}")
        # Generate embeddings
        user_txtanswer_embeddings = self.model.encode(usrtxt_ans)
        correct_answer_embeddings = self.model.encode(ans_1_24)
        
        total_marks = 0

        # Create a DataFrame to hold question details
        data = {
            "Question Number": [],
            "User Answer": [],
            "Correct Answer": [],
            "Similarity Score": [],
            "Marks": []
        }

        for i, answer in enumerate(usrtxt_ans):
            
            # Calculate similarity score
            similarity_score = cosine_similarity([user_txtanswer_embeddings[i]], [correct_answer_embeddings[i]])[0][0]
            
            # Assign marks based on similarity score
            marks = self.assign_marks(similarity_score)
            
            
            # Append details to the DataFrame
            data["Question Number"].append(i + 1)
            data["User Answer"].append(answer)
            data["Correct Answer"].append(ans_1_24[i])
            data["Similarity Score"].append(similarity_score)
            data["Marks"].append(marks)

            # Update total marks
            total_marks += marks

        # Convert data into a DataFrame
        df = pd.DataFrame(data)

        # Filter rows with 0 marks for markdown content
        incorrect_answers_df = df[df["Marks"] == 0]
        incorrect_answers_df = incorrect_answers_df.drop(columns=['Marks','Similarity Score'], errors='ignore')
        
        
        
        # # ------------------------------------ans25_42------------------
        feedbackB,total_marks=self.compare_answersB_to_dataframe(mcqAnswersB, allmcqCorrectAnswersB,total_marks)
        feedbackCAQ1,total_marks=self.feedbacksub(correctAnswers_taskCQA1,mcq_answers_cqa1,total_marks)
        feedbackCAQ2,total_marks=self.feedbacksub(correctAnswers_taskCQA2,mcq_answers_cqa2,total_marks)
            
        
        
        
        print("total_marks",total_marks)

        # Generate markdown content
        markdown_content = "##### Answer Evaluation\n\n"
        
        markdown_content += f"\n\n##### Total Marks: {total_marks}\n"
        markdown_content += "### Part A\n\n"
        markdown_content += incorrect_answers_df.to_markdown(index=False, tablefmt="pipe")  # Markdown table format
        markdown_content += "\n\n ### Part B\n\n"
        markdown_content += feedbackB.to_markdown(index=False, tablefmt="pipe") 
        markdown_content += "\n\n ### Part C\n\n"
        markdown_content += "##### Text A\n\n"
        markdown_content += feedbackCAQ1.to_markdown(index=False, tablefmt="pipe") 
        markdown_content += "\n\n ##### Text B\n\n"
        markdown_content += feedbackCAQ2.to_markdown(index=False, tablefmt="pipe")
        print("markdown_content",markdown_content)
        
        

        return markdown_content
   
   
    
                    
        
        
  
       
    def get_cyclic_inputsC(self,DB_TASKC):
        # Connect to SQLite database
        conn = sqlite3.connect(DB_TASKC)
        cursor = conn.cursor()

        # Fetch all input data from the table
        cursor.execute('SELECT title, prompt FROM prompts ORDER BY ROWID')
        rows = cursor.fetchall()

        # Store results in a list of tuples (title, prompt)
        inputs = [(row[0], row[1]) for row in rows]

        conn.close()
        return inputs
    
    def assign_marks(self,similarity_score):
        if similarity_score > 0.8:
            return 1  
        else:
            return 0 
    
    def retrieve_answerpart(self, user_query):
        pass
        
        


    def cleanup_B(self,task_list):
        
        try:
            # Replace single quotes with double quotes
            fixed_data = task_list.replace("'", '"')
            
            # Remove extraneous brackets at the beginning and end if needed
            task_list = task_list.strip("[]")
            print("task_listforjson",task_list)
            
            # Parse the fixed string into a JSON object
            parsed_data = json.loads(task_list)
            
            return parsed_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON: {e}")
        
    def parse_taskC(self,input_string):
        # Parse the input string (assuming it is a valid JSON-like dictionary string)
        parsed_data = {}
        
        # Convert the input string to a dictionary (if it's in string format)
        if isinstance(input_string, str):
            input_string = json.loads(input_string)

        # Extract task details
        try:
            questions = input_string.get('task', {}).get('questions', [])
            
            parsed_data['questions'] = []
            
            for q in questions:
                question_data = {}
                
                question_data['question'] = q.get('question', None)
                question_data['options'] = q.get('options', [])
                question_data['correct_answer'] = q.get('correct_answer', None)
                
                parsed_data['questions'].append(question_data)
        except Exception as e:
            print(f"Error parsing the task: {e}")
            parsed_data['questions'] = []

        return parsed_data

    def parse_stringA(self, input_string):
        parsed_data = {}

        def safe_extract(key, input_string):
            """Helper function to extract a field from the string safely"""
            try:
                return input_string.split(f'"{key}": "')[1].split('",')[0]
            except (IndexError, ValueError):
                return None

        # Extracting instruction1, instruction2, and instruction3
        parsed_data["instruction1"] = safe_extract("instruction1", input_string)
        parsed_data["instruction2"] = safe_extract("instruction2", input_string)
        parsed_data["instruction3"] = safe_extract("instruction3", input_string)

        def parse_set(set_key):
            """Helper function to parse sets like set1, set2, set3"""
            set_start = input_string.find(f'"{set_key}": [') + len(f'"{set_key}": [')
            set_end = input_string.find('],', set_start)
            if set_start == -1 or set_end == -1:  # Return empty list if not found
                return []

            set_data = input_string[set_start:set_end].strip()
            set_list = []
            for entry in set_data.split('},'):
                entry = entry.strip().strip("{").strip("}")
                if entry:
                    key_value_pairs = entry.split('",')
                    if len(key_value_pairs) > 1:
                        question = key_value_pairs[0].split(":")[1].strip().strip('"')
                        correct_answer = key_value_pairs[1].split(":")[1].strip().strip('"')
                        set_list.append({question: correct_answer})
            return set_list

        # Parsing set1, set2, set3
        parsed_data["set1"] = parse_set("set1")
        parsed_data["set2"] = parse_set("set2")
        parsed_data["set3"] = parse_set("set3")

        # Convert the parsed data to a JSON string
        return json.dumps(parsed_data, indent=4)

    def parse_nested_string(self, raw_string):
        def clean_string(raw_string):
            # Replace single quotes with double quotes, but avoid altering apostrophes in words
            cleaned = re.sub(r"(?<!\w)'(?!\w)", '"', raw_string)
            
            # Normalize spaces and remove unwanted whitespace
            cleaned = re.sub(r'\s+', ' ', cleaned)
            
            # Add missing commas between JSON fields
            cleaned = re.sub(r'"}\s*{', '"}, {', cleaned)
            cleaned = re.sub(r'"\s*([a-zA-Z_]+)\s*":', r'", "\1":', cleaned)
            
            # Remove stray trailing commas before closing brackets or braces
            cleaned = re.sub(r',\s*]', ']', cleaned)
            cleaned = re.sub(r',\s*}', '}', cleaned)
            
            return cleaned

        def parse_cleaned_string(cleaned_string):
            try:
                # Parse manually using regular expressions
                parsed_data = []
                entries = re.findall(r'{.*?}', cleaned_string)  # Find individual JSON-like objects
                for entry in entries:
                    obj = {}
                    # Extract key-value pairs
                    key_value_pairs = re.findall(r'"(.*?)"\s*:\s*(.*?)(?=, "|}$)', entry)
                    for key, value in key_value_pairs:
                        # Handle nested lists and dictionaries
                        if value.startswith("[") and value.endswith("]"):
                            # Remove surrounding brackets and split into list
                            items = re.findall(r'"(.*?)"', value)
                            obj[key] = items
                        elif value.startswith('"') and value.endswith('"'):
                            obj[key] = value.strip('"')  # Remove quotes from strings
                        else:
                            obj[key] = value  # Treat as a raw value (numbers, etc.)
                    parsed_data.append(obj)
                return parsed_data
            except Exception as e:
                print(f"Error while parsing: {e}")
                return None

        # Clean and parse the raw string
        cleaned_string = clean_string(raw_string)
        parsed_data = parse_cleaned_string(cleaned_string)
        return parsed_data
                     
            
    
    
            
    def get_cyclic_inputs(self,DB_TASKB):
        # Connect to SQLite database
        conn = sqlite3.connect(DB_TASKB)
        cursor = conn.cursor()

        # Fetch all input data from the table
        cursor.execute('SELECT id, input_value FROM inputs ORDER BY id')
        rows = cursor.fetchall()

        # Store results in a list of tuples (id, input_value)
        inputs = [(row[0], row[1]) for row in rows]

        return inputs
    
    
    def cyclic_iterator(self,idx,inputs):
        # print("inputs",inputs)
        
        
        while True:
            
            yield inputs[idx][1]

            inputs.append(inputs.pop(idx))
            idx = (idx + 1) % len(inputs)
            
    def cyclic_iteratorC(self,idx,inputs):
        
        
        
        while True:
            
            yield inputs[idx]

            inputs.append(inputs.pop(idx))
            idx = (idx + 1) % len(inputs)


if __name__ == "__main__":
    reading_task = OETReadingTaskAssistant()
    DB_TASKC = "db/readingpartC_topicsforRAG.db"
    inputsC = reading_task.get_cyclic_inputs(DB_TASKC)
    cyclic_gen = reading_task.cyclic_iterator(idx=0,inputs=inputsC)
    topic = next(cyclic_gen)
    taskC_prompt = reading_task.retrieve_taskC_prompt(topic)
    taskC=reading_task.rag_taskpart(taskC_prompt)
    taskCQA_prompt=reading_task.retrieve_qaC_prompt(taskC)
    print("taskCQA",taskCQA_prompt)
    taskCQA=reading_task.rag_taskpartQA(taskCQA_prompt)
    

    