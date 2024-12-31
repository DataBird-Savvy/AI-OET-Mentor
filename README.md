# AI OET Mentor: Your Smart, Personalized OET Preparation Platform

The **AI OET Mentor Project** leverages cutting-edge AI technologies, including **Generative AI (GenAI)**, **fine-tuning**, and **Retrieval-Augmented Generation (RAG)**, to create an intelligent platform that helps healthcare professionals prepare for the Occupational English Test (OET). The platform offers **targeted practice**, **real-time feedback**, and **adaptive learning tools**, making OET preparation efficient and effective.

---

## Problem Statement

Many healthcare professionals face challenges in achieving the required proficiency in the OET, a standardized test assessing language skills in healthcare-specific contexts. Existing preparation methods—such as self-study or in-person classes—often fall short due to:

- Lack of **personalized feedback**  
- Limited **practical simulations**  
- Inability to **adapt to individual learning needs**

These limitations result in inefficient preparation and insufficient readiness, ultimately affecting candidates' chances of success.

---

## Proposed Solution

The **AI OET Mentor** addresses these challenges with an AI-driven platform tailored specifically to healthcare professionals. By adapting to users’ unique strengths and weaknesses, the tool provides:

- **Tailored OET practice**  
- **Real-time feedback**  
- **Simulated exam environments**

This personalized approach empowers candidates to improve their language skills efficiently, boosting their confidence and success rate on the OET while supporting their journey into the healthcare workforce.

---

## Key Features of the AI OET Mentor

### 1. Writing Component
- **Technology:** Prompt engineering with LangChain and Google GenAI  
- **Functionality:**  
  - Generates practice tasks aligned with OET standards  
  - Provides **real-time, AI-driven feedback**, including insights into strengths and focus areas  
  - Helps users refine language skills with **personalized suggestions**  

### 2. Listening Component
- **Technology:** Hugging Face model integration and MongoDB for document storage  
- **Functionality:**  
  - Enhances similarity search capabilities using sentence transformers  
  - Assesses listening comprehension and provides feedback with **contextually relevant examples**
    
### 3. Reading Component
- **Technology:** Fine-tuned OpenAI models for Part B (using Ollama fine-tuned with Unsloth; the base model is Llama 3.2), combined with RAG using Pinecone for Parts A and C  
- **Functionality:**  
  - Improves understanding of complex texts through **context-specific explanations**  
  - Offers **targeted practice** to optimize performance on each section  

---


## Future Enhancements

1. **OET-Specific Speaking Module:**  
   - Powered by Generative AI (GenAI)  
   - Offers **realistic role-play sessions** simulating professional healthcare-patient interactions  
   - Focuses on key interaction skills needed in real-world healthcare settings  

2. **FAQ Chatbot:**  
   - Integrate an **AI-driven FAQ Chatbot** to answer users' common questions about OET preparation, platform features, and usage guidance.  
   - Powered by **Generative AI** and **knowledge retrieval**, ensuring quick and accurate responses.  
   - Enhances user experience by providing **on-demand assistance** and reducing learning barriers.  

---

