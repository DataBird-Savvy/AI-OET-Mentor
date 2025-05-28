
import os
import json
import re
import sqlite3
from typing import List
import sys

import pandas as pd
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from langchain.vectorstores import Pinecone as P
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone
from groq import Groq
from openai import OpenAI

from logger import logging
from exception import OETException

load_dotenv()
class OETReadingTaskAssistant:
    def __init__(self):
        try:
            self.PINECONE_API = os.getenv("PINE_CONE_API")
            self.INDEX_NAME_A = os.getenv("INDEX_NAME_A")
            self.INDEX_NAME_C = "oet-partc-content"
            self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
            self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

            logging.info("Initializing Pinecone and vector stores...")
            pc = Pinecone(api_key=self.PINECONE_API)
            indexA = pc.Index(self.INDEX_NAME_A)
            indexC = pc.Index(self.INDEX_NAME_C)

            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.client = Groq(api_key=self.GROQ_API_KEY)
            self.openai_client=OpenAI()

            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            self.vector_storeA = P(index=indexA, embedding=embeddings,text_key="text")
            self.vector_storeC = P(index=indexC, embedding=embeddings,text_key="text")

            logging.info("OETReadingTaskAssistant initialized successfully.")

        except Exception as e:
            logging.error("Error during initialization of OETReadingTaskAssistant.", exc_info=True)
            raise OETException(e, sys)
            
    def retrieve_context(self, topic, vectorstore, k=5):
        try:
            logging.info(f"Retrieving context for topic: {topic}")
            matching_results = vectorstore.similarity_search(topic, k=k)
            return matching_results
        except Exception as e:
            logging.error("Error in retrieve_context.", exc_info=True)
            raise OETException(e, sys)
            
    def retrieve_taskA_prompt(self,topic):
        try:
            vectorstore = self.vector_storeA
            doc_search = self.retrieve_context(topic, vectorstore)
            documents_text = "\n".join([doc.page_content[:300] for doc in doc_search])  

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
            - Should be 250-300 words long.
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
            # logging.info("Prompt generated successfully.")
            return prompt
        except Exception as e:
            logging.error("Error in retrieve_taskA_prompt.", exc_info=True)
            raise OETException(e, sys)
            
    
    def retrieve_taskC_prompt(self, topic):
        try:
            logging.info("Retrieving context for Part C prompt generation...")
            vectorstore = self.vector_storeC
            doc_search = self.retrieve_context(topic, vectorstore)
            documents_text = "\n".join([doc.page_content for doc in doc_search])
            logging.info("Successfully created document context for Part C.")
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
        except Exception as e:
            raise OETException(e, sys)
            

    def rag_taskpart(self, input):
        try:
            logging.info("Generating response using LLM for passage generation...")
            chat_completion = self.client.chat.completions.create(
            messages=[{
                "role": "system",
                "content": f"{input}"
            }],
            model="llama-3.1-8b-instant",
            
            )
            response_task=chat_completion.choices[0].message.content
            logging.info("LLM response received successfully.")
            return response_task
        except Exception as e:
            raise OETException(e,sys)
            

    def rag_taskpartQA(self, input):
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{
                    "role": "system",
                    "content": (
                        "You are a helpful assistant. Respond only with a JSON object. "
                        "Wrap your response between <JSON> and </JSON> tags. "
                        "No extra text outside the tags."
                    )
                },
                    {
                    "role": "user",
                    "content": f"{input}"
                }],
                model="llama-3.1-8b-instant",
                
            )
            response_next_input = chat_completion.choices[0].message.content
            print("response_next_input",response_next_input)
            start_index = response_next_input.find('{')
            end_index = response_next_input.rfind('}') + 1
            json_text = response_next_input[start_index:end_index]
            json_text = json_text.strip()  
            json_text = json_text.replace("\n", "").replace("\t", "")  
            json_output = json.loads(json_text)
            return json_output
        except json.JSONDecodeError as e:
            print("Invalid JSON response:", response_next_input)
            print("Error:", e)
            json_output = None
            raise OETException(e,sys)
            
    def retrieve_qaA_prompt(self, taskA_context):
        try:
                
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
            ⚠️ **Validation Rule:**  
                Before outputting, re-check each question.  
                - If a question does not contain `_____` exactly once, or the blank is at the wrong position — fix it before responding.

            """
            return prompt_next
        except Exception as e:
            raise OETException(e,sys)
            
    def retrieve_qaC_prompt(self, taskC_context):
        try:
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
        except Exception as e:
            raise OETException(e,sys)
            
    def compare_answersB_to_dataframe(self, mcq_answers, correct_answers, total_marks):
        try:
            results = []
            marks_per_question = 1  
            for idx, mcq in enumerate(mcq_answers):
                
                selected_answer = mcq['answer'].split(')')[0]  
                answer_mapping = { '0': 'a', '1': 'b', '2': 'c'}
                selected_answer = answer_mapping.get(selected_answer, "Invalid answer") 
                is_correct = 'Correct' if selected_answer == correct_answers[idx] else 'Incorrect'
                if is_correct == 'Correct':
                    total_marks += marks_per_question
    
                results.append({
                    'Question ID': idx+1,
                    'Selected Answer': selected_answer,
                    'Correct Answer': correct_answers[idx],
                    'Result': is_correct
                })
            df = pd.DataFrame(results)
            return df, total_marks
        except Exception as e:
            raise OETException(e,sys)
            
    def convert_to_markdown(self,string_input):
        try:
            sections = string_input.strip().split('},\n    {')
            markdown_content = ""
            for section in sections:
    
                section = section.replace('"\n', '" ').replace('\n    ', ' ').strip("{}").strip()
                title_start = section.find('"title": "') + len('"title": "') 
                title_end = section.find('"', title_start)
                title = section[title_start:title_end]
                passage_start = section.find('"passage": "') + len('"passage": "') 
                passage_end = section.find('"', passage_start)
                passage = section[passage_start:passage_end]
                markdown_content += f"## {title}\n\n**Passage:**\n{passage}\n\n"
                tasks_start = section.find('"tasks": [') + len('"tasks": [')
                tasks_end = section.find(']', tasks_start) + 1
                tasks_section = section[tasks_start:tasks_end]
                tasks = tasks_section.strip('["{}"]').split('},\n        {')
                for task in tasks:
                    task = task.replace('"\n', '" ').strip("{}").strip()
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
                    markdown_content += f"### {task_question}\nOptions:\n"
                    for option in options:
                        markdown_content += f"- {option}\n"
                    markdown_content += f"**Correct Answer:** {correct_answer}\n\n"

            return markdown_content
        except Exception as e:
            raise OETException(e,sys)
            

    def retrive_B(self,prompt):
        try:
            response=self.openai_client.beta.chat.completions.parse(
            model="ft:gpt-3.5-turbo-0125:personal::AicLfVa6",
            messages = [
                {
                    "role": "system",
                    "content": """
                    You are an assistant for creating OET Reading Part B tests. Given a passage, return an array of exactly 3 JSON objects. Each object must have:
                    "title" (string), 
                    "passage" (string, 3–4 concise sentences), 
                    "tasks" (an array of one object with "task", "options" [3 items starting with a), b), c)], and "correct_answer").

                    ⚠️IMPORTANT:
                    - Return only raw valid JSON. No explanations, no markdown, no text outside the JSON.
                    - Do not include extra commas or closing parentheses.
                    - Structure must look like: 
                    [{"title": "...", "passage": "...", "tasks": [{"task": "...", "options": ["a)...", "b)...", "c)..."], "correct_answer": "a"}]}]
                    """
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
                )
            generated_json=response.choices[0].message.content
            return generated_json
        except Exception as e:
            raise OETException(e,sys)
            
    

    def feedbacksub(self, corectanswer, useranswer, total_marks):
        try:
            correct_answers_mapping = {
                str(i + 1): corectanswer[i]
                for i in range(len(corectanswer))
            }
            marks_per_question = 1  
            feedback_data = []
            for answer in useranswer:
                question_id = answer['questionId']
                user_answer = answer['answer']
                correct_answer = correct_answers_mapping.get(question_id, "No correct answer available")
                is_correct = user_answer == correct_answer
                feedback = "Correct" if is_correct else "Incorrect"
                if is_correct:
                    total_marks += marks_per_question
                feedback_data.append({
                    "Question ID": question_id,
                    "User Answer": user_answer,
                    "Correct Answer": correct_answer,
                    "Feedback": feedback
                })

            
            feedback_df = pd.DataFrame(feedback_data)
            return feedback_df, total_marks
        except Exception as e:
            raise OETException(e,sys)
            
    def feedback(self, usrtxt_ans, ans_1_24,allmcqCorrectAnswersB,mcqAnswersB,correctAnswers_taskCQA1,mcq_answers_cqa1,correctAnswers_taskCQA2,mcq_answers_cqa2):
        try:
            print(f"usrtxt_ans:{usrtxt_ans},answer:{ans_1_24}")
            user_txtanswer_embeddings = self.model.encode(usrtxt_ans)
            correct_answer_embeddings = self.model.encode(ans_1_24)
            
            total_marks = 0
            data = {
                "Question Number": [],
                "User Answer": [],
                "Correct Answer": [],
                "Similarity Score": [],
                "Marks": []
            }

            for i, answer in enumerate(usrtxt_ans):
                    
                similarity_score = cosine_similarity([user_txtanswer_embeddings[i]], [correct_answer_embeddings[i]])[0][0]
                marks = self.assign_marks(similarity_score)
                data["Question Number"].append(i + 1)
                data["User Answer"].append(answer)
                data["Correct Answer"].append(ans_1_24[i])
                data["Similarity Score"].append(similarity_score)
                data["Marks"].append(marks)
                total_marks += marks
            df = pd.DataFrame(data)
            incorrect_answers_df = df[df["Marks"] == 0]
            incorrect_answers_df = incorrect_answers_df.drop(columns=['Marks','Similarity Score'], errors='ignore')
        
            # # ------------------------------------ans25_42------------------
            feedbackB,total_marks=self.compare_answersB_to_dataframe(mcqAnswersB, allmcqCorrectAnswersB,total_marks)
            feedbackCAQ1,total_marks=self.feedbacksub(correctAnswers_taskCQA1,mcq_answers_cqa1,total_marks)
            feedbackCAQ2,total_marks=self.feedbacksub(correctAnswers_taskCQA2,mcq_answers_cqa2,total_marks)
            markdown_content = "###### Answer Evaluation\n\n"
            markdown_content += f"\n\n##### Total Marks: {total_marks}\n"
            markdown_content += "##### Part A\n\n"
            markdown_content += incorrect_answers_df.to_markdown(index=False, tablefmt="pipe")  
            markdown_content += "\n\n ##### Part B\n\n"
            markdown_content += feedbackB.to_markdown(index=False, tablefmt="pipe") 
            markdown_content += "\n\n ##### Part C\n\n"
            markdown_content += "##### Text A\n\n"
            markdown_content += feedbackCAQ1.to_markdown(index=False, tablefmt="pipe") 
            markdown_content += "\n\n ##### Text B\n\n"
            markdown_content += feedbackCAQ2.to_markdown(index=False, tablefmt="pipe")
            return markdown_content
        except Exception as e:
            raise OETException(e,sys)
            
    def get_cyclic_inputsC(self,DB_TASKC):
        conn = sqlite3.connect(DB_TASKC)
        cursor = conn.cursor()
        cursor.execute('SELECT title, prompt FROM prompts ORDER BY ROWID')
        rows = cursor.fetchall()
        inputs = [(row[0], row[1]) for row in rows]
        conn.close()
        return inputs
    
    def assign_marks(self,similarity_score):
        if similarity_score > 0.8:
            return 1  
        else:
            return 0 
    def get_cyclic_inputs(self,DB_TASKB):
        conn = sqlite3.connect(DB_TASKB)
        cursor = conn.cursor()
        cursor.execute('SELECT id, input_value FROM inputs ORDER BY id')
        rows = cursor.fetchall()
        inputs = [(row[0], row[1]) for row in rows]

        return inputs
    def cyclic_iterator(self,idx,inputs):
        while True:
            yield inputs[idx][1]
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
    print("taskCQA_prompt",taskCQA_prompt)
    taskCQA=reading_task.rag_taskpartQA(taskCQA_prompt)
    print("taskCQA",taskCQA_prompt)