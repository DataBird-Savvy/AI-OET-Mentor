# Load model directly
from llama_cpp import Llama

llm = Llama.from_pretrained(
	repo_id="jiya2/model_ReadTestOETwith_final_3b_18_10",
	filename="unsloth.F16.gguf",
)

llm.create_chat_completion(
	messages = [
		{
			"role": "user",
			"content": "What is the capital of France?"
		}
	]
)