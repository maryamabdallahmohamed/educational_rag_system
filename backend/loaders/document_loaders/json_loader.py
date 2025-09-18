import json
import re


class JSONPreprocessor:
    def load_and_preprocess_data(self, file_path):
        with open(file_path, 'r') as f:
            raw_data = json.load(f)

        texts = []
        for entry in raw_data:
            if isinstance(entry, str):
                texts.append(entry)
            elif isinstance(entry, dict) and "text" in entry:
                texts.append(entry["text"])

        clean_texts = [self.clean_text(t) for t in texts]
        return "\n".join(clean_texts)
    
    def clean_text(self, text):
        """Clean text by normalizing whitespace and line breaks."""
        try:
            cleaned = re.sub(r'\s+', ' ', re.sub(r'\n{3,}', '\n\n', str(text))).strip()
            return cleaned
        except Exception as e:
            print(f"❌ Error cleaning text: {str(e)}")
            raise
    


    def load_and_preprocess_data(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)  # parse JSON
            except json.JSONDecodeError:
                # If it's not valid JSON, fallback to raw text
                return f.read()

        # If it's a dict
        if isinstance(data, dict):
            # Join all string values in the dict
            return "\n".join(str(v) for v in data.values() if isinstance(v, str))

        # If it's a list of dicts
        if isinstance(data, list):
            texts = []
            for item in data:
                if isinstance(item, dict):
                    # take any fields that are text
                    texts.extend(str(v) for v in item.values() if isinstance(v, str))
                else:
                    texts.append(str(item))
            return "\n".join(texts)

        # Fallback
        return str(data)


