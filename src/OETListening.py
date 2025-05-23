import os
import sqlite3
import sys

from pymongo import MongoClient
from gridfs import GridFS
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

from logger import logging
from exception import OETException


load_dotenv()


class OETListeningTaskAssistant:
    def __init__(self):
        logging.info("Initializing OETListeningTaskAssistant...")
        
        try:
            self.mongo_db_uri = os.getenv("MONGO_DB_URI")
            self.database_name = os.getenv("DATA_BASE")
            self.collection_name = os.getenv("COLLECTION_NAME")
            self.artifact_path = "static/artifacts"
            logging.info(f"self.mongo_db_uri: {self.mongo_db_uri}")
            logging.info(f"self.database_name: {self.database_name}")
            logging.info(f"self.collection_name: {self.collection_name}")

            self.client = MongoClient(self.mongo_db_uri)
            self.db = self.client[self.database_name]
            self.scenario_collection = self.db[self.collection_name]
            self.fs = GridFS(self.db)

            self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            logging.info("Initialization completed successfully.")
        except Exception as e:
            raise OETException(e, sys)

    def generate_embedding(self, input_text):
        logging.debug(f"Generating embedding for input text: {input_text}")
        return self.model.encode(str(input_text)).tolist()

    def query_scenarios(self, user_query, num_candidates=2, limit=1):
        logging.info(f"Querying scenarios for user input: {user_query}")
        try:
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

            results = list(self.scenario_collection.aggregate(pipeline))
            logging.info(f"Query returned {len(results)} result(s).")
            return results[0] if results else None
        except Exception as e:
            raise OETException(e, sys)

    def retrieve_audio_files(self, shared_id):
        logging.info(f"Retrieving audio file for shared_id: {shared_id}")
        try:
            audio_file = self.fs.find_one({"metadata.shared_id": shared_id})

            if audio_file:
                local_file_path = os.path.join(self.artifact_path, audio_file.filename)

                if not os.path.exists(local_file_path):
                    with open(local_file_path, "wb") as f:
                        chunk_size = 4 * 1024 * 1024
                        while True:
                            chunk = audio_file.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                    logging.info(f"Audio file saved locally to: {local_file_path}")
                else:
                    logging.info(f"Audio file already exists locally at: {local_file_path}")

                return audio_file.filename

            logging.warning("No audio file found with the specified shared_id.")
            return None
        except Exception as e:
            raise OETException(e, sys)

    def listeningXto_markdown(self, data):
        md_text = ""
        for part, details in data.items():
            md_text += f"### {part}\n"
            if isinstance(details, dict):
                for sub_part, sub_details in details.items():
                    if sub_part in ["Extract 1: Questions 1-12", "Extract 2: Questions 13-24"]:
                        sub_part = f"**{sub_part}**"
                    if isinstance(sub_details, str):
                        sub_details = f"**{sub_details}**"
                    if isinstance(sub_details, list):
                        md_text += f"#### {sub_part}\n"
                        for item in sub_details:
                            for question, options in item.items():
                                md_text += f"- **{question}**\n"
                                if isinstance(options, list):
                                    for option in options:
                                        md_text += f"  - ⚪ {option}\n"
                                else:
                                    md_text += f"{options}\n"
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
                        md_text += f"- {sub_part}: {sub_details}\n"
            md_text += "\n"
        return md_text

    def retrieve_answerpart(self, user_query):
        logging.info("Retrieving answer parts...")
        try:
            result = self.query_scenarios(user_query)
            ans1_24 = result['scenario']["Listening_Sub-Test_Answer_Key"]['Part_A']['Questions_1-24']
            ans25_30 = result['scenario']["Listening_Sub-Test_Answer_Key"]['Part_B']['Questions_25-30']
            ans31_42 = result['scenario']["Listening_Sub-Test_Answer_Key"]['Part_C']['Questions_31-42']
            ans25_42 = ans25_30 + ans31_42
            ans1_24_list = [list(item.values())[0] for item in ans1_24]
            
            logging.info("Answer parts successfully retrieved.")
            return ans1_24_list, ans25_42
        except Exception as e:
            raise OETException(e, sys)

    def assign_marks(self, similarity_score):
        return 1 if similarity_score > 0.8 else 0

    def feedback(self, usrtxt_ans, ans_1_24, usrmcq_ans, ans25_42):
        logging.info("Evaluating user answers and generating feedback...")
        try:
            user_embeddings = self.model.encode(usrtxt_ans)
            correct_embeddings = self.model.encode(ans_1_24)
            total_marks = 0

            data = {
                "Question Number": [],
                "User Answer": [],
                "Correct Answer": [],
                "Similarity Score": [],
                "Marks": []
            }

            for i, answer in enumerate(usrtxt_ans):
                score = cosine_similarity([user_embeddings[i]], [correct_embeddings[i]])[0][0]
                marks = self.assign_marks(score)
                total_marks += marks

                data["Question Number"].append(i + 1)
                data["User Answer"].append(answer)
                data["Correct Answer"].append(ans_1_24[i])
                data["Similarity Score"].append(score)
                data["Marks"].append(marks)

            df_text = pd.DataFrame(data)
            incorrect_df = df_text[df_text["Marks"] == 0].drop(columns='Marks', errors='ignore')

            comparison_results = []
            for item in usrmcq_ans:
                q_num = item['question'].split('.')[0]
                usr_ans = item['answer']
                match = next((a for a in ans25_42 if q_num in a), None)
                if match:
                    correct = match[q_num]
                    if usr_ans == "No answer selected":
                        status = "No answer provided"
                    elif correct.startswith(usr_ans.split(')')[0]):
                        status = "Correct"
                        total_marks += 1
                    else:
                        status = "Incorrect"
                    comparison_results.append({
                        'Question': q_num,
                        'Your Answer': usr_ans,
                        'Correct Answer': correct,
                        'Status': status
                    })
                else:
                    comparison_results.append({
                        'Question': q_num,
                        'Your Answer': usr_ans,
                        'Correct Answer': "Not found",
                        'Status': "Question not found"
                    })

            df_mcq = pd.DataFrame(comparison_results)

            markdown = "##### Answer Evaluation\n\n"
            markdown += f"##### Total Marks: {total_marks}\n\n"
            markdown += incorrect_df.to_markdown(index=False, tablefmt="pipe")
            markdown += "\n\n"
            markdown += df_mcq.to_markdown(index=False, tablefmt="pipe")
            
            logging.info(f"Feedback generation complete. Total marks: {total_marks}")
            return markdown
        except Exception as e:
            raise OETException(e, sys)

    def search_and_retrieve(self, user_query):
        logging.info(f"Searching and retrieving data for: {user_query}")
        try:
            result = self.query_scenarios(user_query)
            audio_file = None

            if result:
                shared_id = result["shared_id"]
                audio_file = self.retrieve_audio_files(shared_id)
            else:
                print("No matching scenario found.")
                return None

            scenario = result['scenario']
            part_a = {k: v for k, v in scenario.items() if k == "Part A"}
            part_b = {k: v for k, v in scenario.items() if k == "Part B"}
            part_c = {k: v for k, v in scenario.items() if k == "Part C"}

            markdown_part_a = self.listeningXto_markdown(part_a)
            
            logging.info("Scenario and audio retrieval successful.")
            return markdown_part_a, part_b, part_c, audio_file
        except Exception as e:
            raise OETException(e, sys)

    def get_cyclic_inputs(self):
        logging.info("Fetching cyclic inputs from SQLite database...")
        try:
            conn = sqlite3.connect('db/listeninginput_query.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, input_value FROM inputs ORDER BY id')
            results = [(row[0], row[1]) for row in cursor.fetchall()]
            
            logging.info(f"Retrieved {len(results)} cyclic inputs.")
            return results
        except Exception as e:
            raise OETException(e, sys)

    def cyclic_iterator(self, idx):
        logging.info(f"Starting cyclic iterator from index: {idx}")
        inputs = self.get_cyclic_inputs()

        while True:
            yield inputs[idx][1]




    
 