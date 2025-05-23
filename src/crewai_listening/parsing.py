import json
class JSONExtractor:
    def __init__(self, filename):
        self.filename = filename
        self.data = self._read_file()

    def _read_file(self):
        with open(self.filename, 'r') as file:
            return file.read()

    def _extract_value(self, key):
        start_index = self.data.find(f'"{key}":') + len(f'"{key}":')
        start_index = self.data.find('"', start_index)
        end_index = self.data.find('"', start_index + 1)
        return self.data[start_index + 1:end_index]

    def _extract_list(self, key):
        start_key_index = self.data.find(f'"{key}":')
        if start_key_index == -1:
            return []

        start_list_index = self.data.find('[', start_key_index) + 1
        end_list_index = self.data.find(']', start_list_index)
        list_str = self.data[start_list_index:end_list_index].strip()
        
        try:
            return json.loads(f"[{list_str}]")
        except json.JSONDecodeError as e:
            print(f"Failed to parse {key} JSON. Error:", e)
            return []

    def extract_values(self):
        return {
            'Scenario': self._extract_value('Scenario'),
            'Passage_type': self._extract_value('Passage_type'),
            'Listening_Passage': self._extract_value('Listening_Passage')
        }

    def extract_additional_data(self):
        result = {}

        # Extract "Questions"
        start_index = self.data.find('"Questions":') + len('"Questions":')
        if start_index != -1:
            start_index = self.data.find('[', start_index)
            if start_index != -1:
                open_brackets = 1
                end_index = start_index
                while open_brackets > 0 and end_index < len(self.data):
                    end_index += 1
                    if self.data[end_index] == '[':
                        open_brackets += 1
                    elif self.data[end_index] == ']':
                        open_brackets -= 1
                questions_str = self.data[start_index:end_index + 1]
                try:
                    questions = json.loads(questions_str)
                    result["Questions"] = [
                        {
                            "Type": question.get('Type', 'N/A'),
                            "Question": question.get('Question', 'N/A'),
                            "Options": question.get('Options', [])
                        }
                        for question in questions
                    ]
                except json.JSONDecodeError as e:
                    print("Failed to parse Questions JSON. Error:", e)
                    result["Questions"] = []
            else:
                result["Questions"] = []
        else:
            result["Questions"] = []

        # Extract "Correct_answers"
        start_key_index = self.data.find('"Correct_answers":')
        if start_key_index != -1:
            start_list_index = self.data.find('[', start_key_index) + 1
            end_list_index = self.data.find(']', start_list_index)
            correct_answers_str = self.data[start_list_index:end_list_index].strip()
            try:
                correct_answers = json.loads(f"[{correct_answers_str}]")
                result["Correct_answers"] = correct_answers
            except json.JSONDecodeError as e:
                print("Failed to parse Correct_answers JSON. Error:", e)
                result["Correct_answers"] = []
        else:
            result["Correct_answers"] = []

        return result

    def extract_list(self, key):
        return self._extract_list(key)

    def extract_all_data(self):
        return {
            **self.extract_values(),
            **self.extract_additional_data(),
            'Explanation': self.extract_list('Explanation'),
            'Suggestions': self.extract_list('Suggestions')
        }


