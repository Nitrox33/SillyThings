from typing import Optional, Literal, Union
import pathlib
try:
    from colorama import Fore, Style # pip install colorama
    colorama_available = True
except ImportError:
    print("colorama not found, please install it with 'pip install colorama'")
    print("Continuing without color support.")
    colorama_available = False
    
import re
from threading import Thread

NUMBER_OF_THREADS = 8 # Adjust based on your machine's core count and performance considerations    

class Row:
    # Example word: "crane"
    # if a letter is correctly placed, we put it in uppercase
    # if a letter is present but misplaced, we put a ? after it in lowercase
    # if a letter is absent, we put it in lowercase
    # Example: "cRAn?e" means R and A are correctly placed, N is present but misplaced, C and E are absent
    def __init__(self, word: str):
        if not re.match(r"^[a-z?A-Z]{5,10}$", word):
            raise ValueError("Word must be 5 to 10 letters long, only letters and ? are allowed.")
        self.word = word
        separated_word = []
        last_was_misplaced = False
        for i, letter in enumerate(word):
            if last_was_misplaced:
                last_was_misplaced = False
                continue
            if i + 1 < len(word) and word[i + 1] == "?":
                separated_word.append((letter.lower(), "misplaced"))
                last_was_misplaced = True
            elif letter.isupper():
                separated_word.append((letter.lower(), "correct"))
            else:
                separated_word.append((letter.lower(), "absent"))

        self.separated_word: list[tuple[str, Literal["correct", "misplaced", "absent"]]] = separated_word

    def __repr__(self):
        colored_word = ""
        for letter, status in self.separated_word:
            if status == "correct":
                if colorama_available:
                    colored_word += Fore.GREEN + letter.upper() + Style.RESET_ALL
                else:
                    colored_word += letter.upper()
            elif status == "misplaced":
                if colorama_available:
                    colored_word += Fore.YELLOW + letter.lower() + Style.RESET_ALL
                else:
                    colored_word += letter.lower() + "?"
            else:
                if colorama_available:
                    colored_word += Fore.RED + letter.lower() + Style.RESET_ALL
                else:
                    colored_word += letter.lower()
        return colored_word

class WordleSolver:
    def __init__(self):
        self.rows: list[Row] = []
        
    def add_row(self, row: str):
        self.rows.append(Row(row))

    def calculate_possible_letters(self):
        possible_letters = [set("abcdefghijklmnopqrstuvwxyz") for _ in range(5)]
        letters_in_word = set()
        for status in ["absent", "misplaced", "correct"]:
            for row in self.rows:
                for i, (letter, letter_status) in enumerate(row.separated_word):
                    if letter_status == status:
                        if status == "absent":
                            # if letter is absent, remove it from all positions
                            for j in range(5):
                                possible_letters[j].discard(letter)
                        elif status == "misplaced":
                            possible_letters[i].discard(letter) # only work if letter is not duplicated in the word!
                            letters_in_word.add(letter)
                        elif status == "correct":
                            possible_letters[i] = {letter}
                            letters_in_word.add(letter)
        
        if len(letters_in_word) > 5:
            raise ValueError("Too many letters in word, please check your rows.")
        elif len(letters_in_word) == 5:
            for i in range(5):
                possible_letters[i] = possible_letters[i].intersection(letters_in_word)
        
        return possible_letters, letters_in_word
    
    def calculate_all_possibilities(self, possible_letters):
        words = []
        for letter1 in possible_letters[0]:
            for letter2 in possible_letters[1]:
                for letter3 in possible_letters[2]:
                    for letter4 in possible_letters[3]:
                        for letter5 in possible_letters[4]:
                            word = letter1 + letter2 + letter3 + letter4 + letter5
                            words.append(word)
        return words
    
    def find_closest_words(self):
        possible_letters, letters_in_word = self.calculate_possible_letters()
        possible_words = self.calculate_all_possibilities(possible_letters)
        path = pathlib.Path(__file__).parent / "output_words.txt"
        with open(path, "r") as f:
            word_list = [line.strip() for line in f.readlines()]
    
        
        def worker(word_chunk):
            local_results = []
            for word in word_chunk:
                if word in word_list and set(word).issuperset(letters_in_word):
                    local_results.append(word)
            return local_results
        
        chunks = [possible_words[i::NUMBER_OF_THREADS] for i in range(NUMBER_OF_THREADS)]
        
        threads = []
        results = []
        for chunk in chunks:
            thread = Thread(target=lambda q, arg1: q.append(worker(arg1)), args=(results, chunk))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        results = [word for sublist in results for word in sublist]
        return results

    
if __name__ == "__main__":
    solver = WordleSolver()
    title = r"""
       ___       __         _      __            ____      ____     __            
      / _ |__ __/ /____    | | /| / /__  _______/ / /__   / __/__  / /  _____ ____
     / __ / // / __/ _ \   | |/ |/ / _ \/ __/ _  / / -_) _\ \/ _ \/ / |/ / -_) __/
    /_/ |_\_,_/\__/\___/   |__/|__/\___/_/  \_,_/_/\__/ /___/\___/_/|___/\__/_/   
                                                                                """
                                                    
    print(title)
    print("RULES:")
    print("1. Use uppercase for correct letters.")
    print("2. Use lowercase for absent letters.")
    print("3. Use '?' after a letter for misplaced letters.")
    print("4. Enter '-' to remove the last row.")
    print("5. Enter 'q' to quit.")
    print("6. Press Enter on an empty line to get possible words.")
    print("7. Put '&' and press Enter to get possible combinations")

    while True:
        row = input(">: ")  
        if row == "-":
            print("Current rows:")
            for r in solver.rows:
                print(r)
            solver.rows.pop() if solver.rows else None
        elif row == "q":
            break
        elif row == "":
            if len(solver.rows) == 0:
                print("No rows entered yet. Please enter at least one row.")
                continue
            possible_words = solver.find_closest_words()
            print("Possible words: ({} found)".format(len(possible_words)))
            for w in possible_words:
                print(w)
        elif row == "&":
            possible_letters, letters_in_word = solver.calculate_possible_letters()
            possible_words = solver.calculate_all_possibilities(possible_letters)
            print("Possible combinations: ({} found)".format(len(possible_words)))
            A = input("Do you want to see all combinations? (y/n): ")
            if A.lower() == 'y':
                for w in possible_words:
                    print(w)
        else:
            if not re.match(r"^[a-z?A-Z]{5,10}$", row):
                print("Invalid row format. Please try again.")
                continue
            solver.add_row(row)
            print("Current rows:")
            for r in solver.rows:
                print(r)