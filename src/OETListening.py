import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from gridfs import GridFS
import sqlite3
import pandas as pd
from logger import logging

load_dotenv()

class OETListeningTaskAssistant:
    def __init__(self):
        logging.info("Initializing the OET Listening Task Assistant")
        logging.info("Loading environment variables")
        self.mongo_db_uri = os.getenv("MONGO_DB_URI")
        self.database_name = os.getenv("DATA_BASE")
        self.collection_name = os.getenv("COLLECTION_NAME")
        self.artifact_path = "static/artifacts"
        
        logging.info("Initializing MongoDB client and collections")
        self.client = MongoClient(self.mongo_db_uri)
        self.db = self.client[self.database_name]
        self.scenario_collection = self.db[self.collection_name]
        self.fs = GridFS(self.db)
        
        logging.info("Loading the SentenceTransformer model")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def generate_embedding(self, input_text):
        
        result=self.model.encode(str(input_text)).tolist()
        return result

    def query_scenarios(self, user_query, num_candidates=2, limit=1):
        query_embedding = self.generate_embedding(user_query)
        
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "queryVector": query_embedding,
                    "path": "embedding",
                    "numCandidates": num_candidates,
                    "limit": limit
                }
            },
            {
                "$project": {
                    "shared_id": 1,
                    "scenario": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        
        logging.info("Executing the SentenceTransformer model")
        results = list(self.scenario_collection.aggregate(pipeline))
        return results[0] if results else None

    def retrieve_audio_files(self, shared_id):
        audio_file = self.fs.find_one({"metadata.shared_id": shared_id})
    
        if audio_file:
            
            local_file_path = os.path.join(self.artifact_path, audio_file.filename)
            
            
            if not os.path.exists(local_file_path):
                with open(local_file_path, "wb") as f:
                    # Use download_to_stream to ensure proper handling of binary data
                    chunk_size = 4 * 1024 * 1024  # 4 MB
                    while True:
                        chunk = audio_file.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                    print(f"Audio file saved to: {local_file_path}")
        
            return audio_file.filename
        else:
            print("No audio file found with the specified shared_id.")
            return None
         
    
    def listeningXto_markdown(self, data):
        md_text = ""

        for part, details in data.items():
            md_text += f"### {part}\n"
            if isinstance(details, dict):
                for sub_part, sub_details in details.items():

                    if isinstance(sub_part, str) and (sub_part == "Extract 1: Questions 1-12" or sub_part == "Extract 2: Questions 13-24"):
                        sub_part = f"**{sub_part}**"  # Wrap sub_part in bold

                    if isinstance(sub_details, str):
                        sub_details = f"**{sub_details}**"  # Wrap sub_details in bold

                    if isinstance(sub_details, list):
                        md_text += f"#### {sub_part}\n"
                        for item in sub_details:
                            for question, options in item.items():
                                md_text += f"- **{question}**\n"
                                if isinstance(options, list):
                                    for option in options:
                                        md_text += f"  - ⚪ {option}\n"  # Add round box symbol for each option
                                else:
                                    md_text += f"{options}\n"  # In case there is a single option
                    elif isinstance(sub_details, dict):
                        md_text += f"#### {sub_part}\n"
                        for task, task_details in sub_details.items():
                            if isinstance(task_details, list):
                                md_text += f"- {task}:\n"
                                for item in task_details:
                                    md_text += f"  - {item}\n"
                            else:
                                md_text += f"- {task}: {task_details}\n"
                    else:
                        # Plain key-value pairs, make sub_details bold
                        md_text += f"- {sub_part}: {sub_details}\n"
            md_text += "\n"

        return md_text



    def retrieve_answerpart(self, user_query):
        logging.info(f"user_query: {user_query}")
        result = self.query_scenarios(user_query)
        # print("result",result)
    
        ans1_24_dic=result['scenario']["Listening_Sub-Test_Answer_Key"]['Part_A']['Questions_1-24']
        ans25_30_dic=result['scenario']["Listening_Sub-Test_Answer_Key"]['Part_B']['Questions_25-30']
        ans31_42_dic=result['scenario']["Listening_Sub-Test_Answer_Key"]['Part_C']['Questions_31-42']
        ans25_42_dic = ans25_30_dic + ans31_42_dic
        
        answers_partA_list = [list(item.values())[0] for item in ans1_24_dic]
        
        return answers_partA_list,ans25_42_dic
    
    def assign_marks(self,similarity_score):
        if similarity_score > 0.8:
            return 1  
        else:
            return 0 
        
    


    def feedback(self, usrtxt_ans, ans_1_24,usrmcq_ans,ans25_42):
        
        print(f"usrtxt_ans:{usrtxt_ans},answer:{ans_1_24}")
        print(f"usrmcq_ans:{usrmcq_ans},answer:{ans25_42}")
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
        incorrect_answers_df = incorrect_answers_df.drop(columns='Marks', errors='ignore')
        
        
        
        # ------------------------------------ans25_42------------------
        
        print("usrmcq_ans",usrmcq_ans)
        print("ans25_42",ans25_42)
        
        comparison_results = []

        logging.info("Comparing answers in list1 with corresponding answers in list2")
        for item1 in usrmcq_ans:
            question_num = item1['question'].split('.')[0]  # Extract the question number
            answer1 = item1['answer']

            match = next((item2 for item2 in ans25_42 if question_num in item2), None)
            if match:
                correct_answer = match[question_num]
                if answer1 == "No answer selected":
                    status = "No answer provided"
                elif correct_answer.startswith(answer1.split(')')[0]):  # Match the option letter
                    status = "Correct"
                    total_marks += 1  # Increment total marks for correct answer
                else:
                    status = "Incorrect"
                comparison_results.append({'Question': question_num, 'Your Answer': answer1, 'Correct Answer': correct_answer, 'Status': status})
            else:
                comparison_results.append({'Question': question_num, 'Your Answer': answer1, 'Correct Answer': "Not found", 'Status': "Question not in list2"})
        df_comparison = pd.DataFrame(comparison_results)
        print("total_marks",total_marks)

        logging.info("Generating markdown content")
        markdown_content = "##### Answer Evaluation\n\n"
        markdown_content += f"\n\n##### Total Marks: {total_marks}\n"
        markdown_content += incorrect_answers_df.to_markdown(index=False, tablefmt="pipe")  # Markdown table format
        markdown_content += df_comparison.to_markdown(index=False, tablefmt="pipe") 
   
        
        print(markdown_content)

        return markdown_content
        
                
            
                     
            
    
    def search_and_retrieve(self, user_query):
        result = self.query_scenarios(user_query)
        
        if result:
            shared_id = result["shared_id"]
            # print(f"Shared ID: {shared_id}, Scenario: {result['scenario']}")
            audio_file=self.retrieve_audio_files(shared_id)
        else:
            print("No matching scenario found.")
        scenario=result['scenario']
        filtered_A = {key: value for key, value in scenario.items() if key in ["Part A"]}
        filtered_B = {key: value for key, value in scenario.items() if key in ["Part B"]}
        filtered_C = {key: value for key, value in scenario.items() if key in ["Part C"]}
        # print("filtered_B",filtered_B)
        # print("filtered_scerio:",filtered_scenario)
        filtered_A=self.listeningXto_markdown(filtered_A)
        
        return filtered_A,filtered_B,filtered_C,audio_file
            
    def get_cyclic_inputs(self):
        logging.info("Connecting to SQLite database")
        conn = sqlite3.connect('db/listeninginput_query.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, input_value FROM inputs ORDER BY id')
        rows = cursor.fetchall()
        # Store results in a list of tuples (id, input_value)
        inputs = [(row[0], row[1]) for row in rows]

        return inputs
    
    
    def cyclic_iterator(self,idx):
        inputs = self.get_cyclic_inputs()
        while True:
            yield inputs[idx][1]
            inputs.append(inputs.pop(idx))
            idx = (idx + 1) % len(inputs)


if __name__ == "__main__":
    listening_task = OETListeningTaskAssistant()
    cyclic_gen = listening_task.cyclic_iterator(idx=0)
    user_query=next(cyclic_gen)
    print("userquery",user_query)


    parta,partb,partc,audio_file=listening_task.search_and_retrieve(user_query)
    # print("partc",partc)
    # print("partb",partb)
    ans_1_24,ans25_42=listening_task.retrieve_answerpart(user_query)
    correct_ans=['(heavy) suitcase', '(his) right leg', '(really) intense', 'turn over in bed', 'get comfortable', 'tingling', '(an) events organiser', 'compression packs', '(an) osteopath', 'ultrasound', 'acupuncture', '(the) combination of treatments', '(a) slipped disc', 'palm', 'itching', '(little) blisters', 'chaotic', 'chest', 'frequent', 'anything in (his) daily life', 'anything in (his) diet', '(malignant) melanoma', 'cold sores', '(an) anti(-)viral cream']
    mcq_ans= [{'question': '25', 'answer': 'No answer selected'}, {'question': '26', 'answer': 'No answer selected'}, {'question': '27', 'answer': 'No answer selected'}, {'question': '28', 'answer': 'No answer selected'}, {'question': '29', 'answer': 'No answer selected'}, {'question': '30', 'answer': 'No answer selected'}, {'question': '31', 'answer': 'No answer selected'}, {'question': '32', 'answer': 'No answer selected'}, {'question': '33', 'answer': 'No answer selected'}, {'question': '34', 'answer': 'No answer selected'}, {'question': '35', 'answer': 'No answer selected'}, {'question': '36', 'answer': 'No answer selected'}, {'question': '37','answer': 'No answer selected'}, {'question': '38', 'answer': 'No answer selected'}, {'question': '39', 'answer': 'No answer selected'}, {'question': '40', 'answer': 'No answer selected'}, {'question': '41', 'answer': 'No answer selected'}, {'question': '42', 'answer': 'No answer selected'}]
    feedback_content=listening_task.feedback(correct_ans,ans_1_24,mcq_ans,ans25_42)
    print("feedback",feedback_content)
    
 
