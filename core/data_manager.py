import os
from datetime import datetime

class DataManager:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def get_boards(self):
        boards = []
        if os.path.exists(self.data_dir):
            for f in os.listdir(self.data_dir):
                if f.endswith('.txt') and '_bg' not in f:
                    boards.append(f[:-4])
        if not boards:
            boards = ['Work']
        return boards

    def delete_board(self, board_name):
        filepath = os.path.join(self.data_dir, f"{board_name}.txt")
        if os.path.exists(filepath):
            os.remove(filepath)

    def save_background(self, board_name, bg_path):
        filepath = os.path.join(self.data_dir, f"{board_name}_bg.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(bg_path)

    def load_background(self, board_name):
        filepath = os.path.join(self.data_dir, f"{board_name}_bg.txt")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return None

    def load(self, board_name):
        filepath = os.path.join(self.data_dir, f"{board_name}.txt")
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"=== ДОСКА: {board_name} ===\n\n")
                f.write("--- New ---\n\n")
                f.write("--- In work ---\n\n")
                f.write("--- Block ---\n\n")
                f.write("--- Need recheck ---\n\n")
                f.write("--- Done ---\n")
        data = {}
        current_column = None

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("--- ") and line.endswith(" ---"):
                    current_column = line[4:-4].strip()
                    data[current_column] = []
                elif line.startswith("- ") and current_column is not None:
                    content = line[2:].strip()
                    color = "white"
                    date = datetime.now().strftime('%Y-%m-%d')

                    if content.startswith("[") and "]" in content:
                        color_end = content.index("]")
                        color = content[1:color_end]
                        content = content[color_end + 1:].strip()

                    if content.startswith("[") and "]" in content:
                        date_end = content.index("]")
                        date = content[1:date_end]
                        content = content[date_end + 1:].strip()

                    data[current_column].append({
                        "text": content,
                        "color": color,
                        "date": date
                    })
        return data

    def save(self, board_name, data):
        filepath = os.path.join(self.data_dir, f"{board_name}.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"=== ДОСКА: {board_name} ===\n\n")
            for column_title, cards in data.items():
                f.write(f"--- {column_title} ---\n")
                for card in cards:
                    f.write(f"- [{card['color']}] [{card['date']}] {card['text']}\n")
                f.write("\n")