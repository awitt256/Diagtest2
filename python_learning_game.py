import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import random
import sys
import io
import re
import json
import os

class PythonLearningGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Learning Game - Hands-On Coding")
        self.root.geometry("1000x700")
        self.root.configure(bg="#1e1e1e")
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
        
        self.lesson_indices = [random.randint(0, 5) for _ in range(50)]
        self.score = 0
        self.current_chapter = 0
        self.current_lesson = 0
        self.chapters = self.load_chapters()
        self.streak = 0
        self.total_lessons = sum(len(chapter['lessons']) for chapter in self.chapters)
        
        self.setup_ui()
        self.show_welcome()
    
    def setup_ui(self):
        # Main frame
        self.main_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Title
        self.title_label = tk.Label(
            self.main_frame,
            text="🐍 Python Coding Challenge",
            font=("Consolas", 20, "bold"),
            fg="#4ec9b0",
            bg="#1e1e1e"
        )
        self.title_label.pack(pady=(0, 10))
        
        # Stats frame
        self.stats_frame = tk.Frame(self.main_frame, bg="#2d2d30")
        self.stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.score_label = tk.Label(
            self.stats_frame,
            text="⭐ Score: 0",
            font=("Consolas", 12),
            fg="#dcdcaa",
            bg="#2d2d30"
        )
        self.score_label.pack(side=tk.LEFT, padx=15, pady=8)
        
        self.chapter_label = tk.Label(
            self.stats_frame,
            text="📚 Chapter: 0/0",
            font=("Consolas", 12),
            fg="#569cd6",
            bg="#2d2d30"
        )
        self.chapter_label.pack(side=tk.LEFT, padx=15, pady=8)
        
        self.streak_label = tk.Label(
            self.stats_frame,
            text="🔥 Streak: 0",
            font=("Consolas", 12),
            fg="#ce9178",
            bg="#2d2d30"
        )
        self.streak_label.pack(side=tk.RIGHT, padx=15, pady=8)
        
        # Game content frame (this will be cleared and rebuilt)
        self.game_content = tk.Frame(self.main_frame, bg="#1e1e1e")
        self.game_content.pack(fill=tk.BOTH, expand=True)
        
        # Challenge frame
        self.challenge_frame = tk.Frame(self.game_content, bg="#252526")
        self.challenge_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Challenge description
        self.desc_label = tk.Label(
            self.challenge_frame,
            text="",
            font=("Consolas", 13),
            fg="#d4d4d4",
            bg="#252526",
            wraplength=950,
            justify=tk.LEFT
        )
        self.desc_label.pack(padx=15, pady=10, anchor=tk.W)
        
        # Example section
        self.example_label = tk.Label(
            self.challenge_frame,
            text="",
            font=("Consolas", 11),
            fg="#808080",
            bg="#252526",
            wraplength=950,
            justify=tk.LEFT
        )
        self.example_label.pack(padx=15, pady=5, anchor=tk.W)
        
        # Code editor frame
        self.editor_frame = tk.Frame(self.game_content, bg="#1e1e1e")
        self.editor_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            self.editor_frame,
            text="💻 Your Code:",
            font=("Consolas", 11, "bold"),
            fg="#4ec9b0",
            bg="#1e1e1e"
        ).pack(anchor=tk.W, pady=(5, 5))
        
        # Code input with line numbers feel
        self.code_input = scrolledtext.ScrolledText(
            self.editor_frame,
            height=12,
            font=("Consolas", 12),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#00ff00",
            selectbackground="#264f78",
            relief=tk.FLAT,
            highlightthickness=2,
            highlightbackground="#007acc"
        )
        self.code_input.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Button frame
        self.btn_frame = tk.Frame(self.game_content, bg="#1e1e1e")
        self.btn_frame.pack(fill=tk.X)
        
        self.run_btn = tk.Button(
            self.btn_frame,
            text="▶ Run Code",
            command=self.run_code,
            font=("Consolas", 12, "bold"),
            bg="#0e639c",
            fg="white",
            activebackground="#1177bb",
            cursor="hand2",
            padx=30,
            pady=8
        )
        self.run_btn.pack(side=tk.LEFT, padx=5)
        
        self.hint_btn = tk.Button(
            self.btn_frame,
            text="💡 Hint",
            command=self.show_hint,
            font=("Consolas", 12),
            bg="#6b3fa0",
            fg="white",
            activebackground="#7b4fb0",
            cursor="hand2",
            padx=20,
            pady=8
        )
        self.hint_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = tk.Button(
            self.btn_frame,
            text="🔄 Reset",
            command=self.reset_code,
            font=("Consolas", 12),
            bg="#555555",
            fg="white",
            activebackground="#666666",
            cursor="hand2",
            padx=20,
            pady=8
        )
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = tk.Button(
            self.btn_frame,
            text="Next Lesson →",
            command=self.next_lesson,
            font=("Consolas", 12, "bold"),
            bg="#28a745",
            fg="white",
            activebackground="#2eb855",
            cursor="hand2",
            padx=30,
            pady=8
        )
        self.next_btn.pack(side=tk.RIGHT, padx=5)
        self.next_btn.pack_forget()
        
        # Output frame
        tk.Label(
            self.game_content,
            text="📤 Output:",
            font=("Consolas", 11, "bold"),
            fg="#4ec9b0",
            bg="#1e1e1e"
        ).pack(anchor=tk.W, pady=(5, 3))
        
        self.output_text = scrolledtext.ScrolledText(
            self.game_content,
            height=5,
            font=("Consolas", 11),
            bg="#000000",
            fg="#00ff00",
            state=tk.DISABLED,
            relief=tk.FLAT
        )
        self.output_text.pack(fill=tk.X, pady=(0, 5))
    
    def load_chapters(self):
        # Define the 10 chapters, each containing 5 lessons, and each lesson containing 6 variations.
        
        ch1 = {
            "title": "Chapter 1: Python Basics",
            "lessons": [
                {
                    "title": "Lesson 1.1: Hello World",
                    "concept": "The print() function outputs text to the screen. Wrap the text in quotes inside the parentheses.",
                    "concept_example": "print(\"Hello!\")",
                    "variants": [
                        {"task": "Print 'Hello, World!' to the screen.", "expected": "Hello, World!", "validate": lambda self, c, o: 'hello, world!' in o.lower()},
                        {"task": "Print 'Hello, Universe!' to the screen.", "expected": "Hello, Universe!", "validate": lambda self, c, o: 'hello, universe!' in o.lower()},
                        {"task": "Print 'Hello, Python!' to the screen.", "expected": "Hello, Python!", "validate": lambda self, c, o: 'hello, python!' in o.lower()},
                        {"task": "Print 'Hello, Programmer!' to the screen.", "expected": "Hello, Programmer!", "validate": lambda self, c, o: 'hello, programmer!' in o.lower()},
                        {"task": "Print 'Hello, Coding!' to the screen.", "expected": "Hello, Coding!", "validate": lambda self, c, o: 'hello, coding!' in o.lower()},
                        {"task": "Print 'Hello, Friend!' to the screen.", "expected": "Hello, Friend!", "validate": lambda self, c, o: 'hello, friend!' in o.lower()}
                    ],
                    "hint": "Use the print() function with the message wrapped in quotes inside the parentheses.",
                    "starter_code": "# Write your first Python program\n"
                },
                {
                    "title": "Lesson 1.2: Print Your Name",
                    "concept": "You can print any name or text inside print(). Be sure to close your quotes.",
                    "concept_example": "print('Bob')",
                    "variants": [
                        {"task": "Print the name 'John'.", "expected": "John", "validate": lambda self, c, o: 'john' in o.lower()},
                        {"task": "Print the name 'Alice'.", "expected": "Alice", "validate": lambda self, c, o: 'alice' in o.lower()},
                        {"task": "Print the name 'Charlie'.", "expected": "Charlie", "validate": lambda self, c, o: 'charlie' in o.lower()},
                        {"task": "Print the name 'Diana'.", "expected": "Diana", "validate": lambda self, c, o: 'diana' in o.lower()},
                        {"task": "Print the name 'Ethan'.", "expected": "Ethan", "validate": lambda self, c, o: 'ethan' in o.lower()},
                        {"task": "Print the name 'Fiona'.", "expected": "Fiona", "validate": lambda self, c, o: 'fiona' in o.lower()}
                    ],
                    "hint": "Use the print() function and pass the name as a string parameter.",
                    "starter_code": "# Print the name\n"
                },
                {
                    "title": "Lesson 1.3: Multiple Prints",
                    "concept": "Calling print() multiple times will output each message on a new line.",
                    "concept_example": "print(\"Line 1\")\nprint(\"Line 2\")",
                    "variants": [
                        {"task": "Print 'Python' on the first line and 'is fun!' on the second.", "expected": "Python\nis fun!", "validate": lambda self, c, o: 'python' in o.lower() and 'is fun!' in o.lower()},
                        {"task": "Print 'Learning' on the first line and 'is cool!' on the second.", "expected": "Learning\nis cool!", "validate": lambda self, c, o: 'learning' in o.lower() and 'is cool!' in o.lower()},
                        {"task": "Print 'Coding' on the first line and 'is creative!' on the second.", "expected": "Coding\nis creative!", "validate": lambda self, c, o: 'coding' in o.lower() and 'is creative!' in o.lower()},
                        {"task": "Print 'Computers' on the first line and 'are smart!' on the second.", "expected": "Computers\nare smart!", "validate": lambda self, c, o: 'computers' in o.lower() and 'are smart!' in o.lower()},
                        {"task": "Print 'Software' on the first line and 'is powerful!' on the second.", "expected": "Software\nis powerful!", "validate": lambda self, c, o: 'software' in o.lower() and 'is powerful!' in o.lower()},
                        {"task": "Print 'Practice' on the first line and 'makes perfect!' on the second.", "expected": "Practice\nmakes perfect!", "validate": lambda self, c, o: 'practice' in o.lower() and 'makes perfect!' in o.lower()}
                    ],
                    "hint": "You can print multiple lines by using two separate print() function calls on different lines.",
                    "starter_code": "# Print two lines\n"
                },
                {
                    "title": "Lesson 1.4: Print Numbers",
                    "concept": "To print numbers, pass them directly without quotation marks.",
                    "concept_example": "print(123)",
                    "variants": [
                        {"task": "Print the number 42.", "expected": "42", "validate": lambda self, c, o: o.strip() == '42'},
                        {"task": "Print the number 100.", "expected": "100", "validate": lambda self, c, o: o.strip() == '100'},
                        {"task": "Print the number 7.", "expected": "7", "validate": lambda self, c, o: o.strip() == '7'},
                        {"task": "Print the number 999.", "expected": "999", "validate": lambda self, c, o: o.strip() == '999'},
                        {"task": "Print the number 2026.", "expected": "2026", "validate": lambda self, c, o: o.strip() == '2026'},
                        {"task": "Print the number 123.", "expected": "123", "validate": lambda self, c, o: o.strip() == '123'}
                    ],
                    "hint": "You can pass numbers directly into the print() function without wrapping them in quotation marks.",
                    "starter_code": "# Print the number\n"
                },
                {
                    "title": "Lesson 1.5: Print a Message",
                    "concept": "Print sentences containing punctuation. Ensure quotes are correctly closed.",
                    "concept_example": "print(\"Keep learning!\")",
                    "variants": [
                        {"task": "Print 'I am learning Python!'", "expected": "I am learning Python!", "validate": lambda self, c, o: 'i am learning python!' in o.lower()},
                        {"task": "Print 'Python is my favorite language!'", "expected": "Python is my favorite language!", "validate": lambda self, c, o: 'python is my favorite language!' in o.lower()},
                        {"task": "Print 'Coding is my superpower!'", "expected": "Coding is my superpower!", "validate": lambda self, c, o: 'coding is my superpower!' in o.lower()},
                        {"task": "Print 'Every day I write code!'", "expected": "Every day I write code!", "validate": lambda self, c, o: 'every day i write code!' in o.lower()},
                        {"task": "Print 'Let's build something awesome!'", "expected": "Let's build something awesome!", "validate": lambda self, c, o: "let's build something awesome!" in o.lower()},
                        {"task": "Print 'Keep calm and write Python!'", "expected": "Keep calm and write Python!", "validate": lambda self, c, o: 'keep calm and write python!' in o.lower()}
                    ],
                    "hint": "Use the print() function to display the exact string, paying attention to quotation marks.",
                    "starter_code": "# Print the message\n"
                }
            ]
        }

        ch2 = {
            "title": "Chapter 2: Variables & Data Types",
            "lessons": [
                {
                    "title": "Lesson 2.1: Create a Variable",
                    "concept": "Variables store values. Use the assignment operator '=' to assign a value.",
                    "concept_example": "name = \"Bob\"",
                    "variants": [
                        {"task": "Create variable 'name' with value 'Alice' and print it.", "expected": "Alice", "validate": lambda self, c, o: 'alice' in o.lower()},
                        {"task": "Create variable 'name' with value 'Bob' and print it.", "expected": "Bob", "validate": lambda self, c, o: 'bob' in o.lower()},
                        {"task": "Create variable 'user' with value 'Charlie' and print it.", "expected": "Charlie", "validate": lambda self, c, o: 'charlie' in o.lower()},
                        {"task": "Create variable 'user' with value 'Diana' and print it.", "expected": "Diana", "validate": lambda self, c, o: 'diana' in o.lower()},
                        {"task": "Create variable 'player' with value 'Ethan' and print it.", "expected": "Ethan", "validate": lambda self, c, o: 'ethan' in o.lower()},
                        {"task": "Create variable 'player' with value 'Fiona' and print it.", "expected": "Fiona", "validate": lambda self, c, o: 'fiona' in o.lower()}
                    ],
                    "hint": "Assign the string to the variable name using the = operator, then pass the variable to the print() function.",
                    "starter_code": "# Create variable and print it\n"
                },
                {
                    "title": "Lesson 2.2: Integer Variable",
                    "concept": "Whole numbers without decimals are integers. Assign them directly without quotes.",
                    "concept_example": "count = 10",
                    "variants": [
                        {"task": "Create variable 'age' with value 25 and print it.", "expected": "25", "validate": lambda self, c, o: o.strip() == '25'},
                        {"task": "Create variable 'age' with value 30 and print it.", "expected": "30", "validate": lambda self, c, o: o.strip() == '30'},
                        {"task": "Create variable 'year' with value 2026 and print it.", "expected": "2026", "validate": lambda self, c, o: o.strip() == '2026'},
                        {"task": "Create variable 'year' with value 1999 and print it.", "expected": "1999", "validate": lambda self, c, o: o.strip() == '1999'},
                        {"task": "Create variable 'limit' with value 100 and print it.", "expected": "100", "validate": lambda self, c, o: o.strip() == '100'},
                        {"task": "Create variable 'limit' with value 50 and print it.", "expected": "50", "validate": lambda self, c, o: o.strip() == '50'}
                    ],
                    "hint": "Assign the integer value directly to the variable, then print that variable.",
                    "starter_code": "# Create integer variable and print it\n"
                },
                {
                    "title": "Lesson 2.3: Float Variable",
                    "concept": "Float variables represent numbers with decimals. Unlike strings, they are written without quotes. Unlike integers, they must contain a decimal point.",
                    "concept_example": "rating = 4.8",
                    "variants": [
                        {"task": "Create variable 'price' with value 19.99 and print it.", "expected": "19.99", "validate": lambda self, c, o: '19.99' in o},
                        {"task": "Create variable 'price' with value 5.49 and print it.", "expected": "5.49", "validate": lambda self, c, o: '5.49' in o},
                        {"task": "Create variable 'temp' with value 98.6 and print it.", "expected": "98.6", "validate": lambda self, c, o: '98.6' in o},
                        {"task": "Create variable 'temp' with value 36.5 and print it.", "expected": "36.5", "validate": lambda self, c, o: '36.5' in o},
                        {"task": "Create variable 'gpa' with value 3.85 and print it.", "expected": "3.85", "validate": lambda self, c, o: '3.85' in o},
                        {"task": "Create variable 'gpa' with value 4.0 and print it.", "expected": "4.0", "validate": lambda self, c, o: '4.0' in o or '4' in o}
                    ],
                    "hint": "Assign the decimal value directly to the variable, then print that variable.",
                    "starter_code": "# Create float variable and print it\n"
                },
                {
                    "title": "Lesson 2.4: Multiple Variables",
                    "concept": "Define multiple variables on separate lines and print them sequentially.",
                    "concept_example": "a = 1\nb = 2\nprint(a)\nprint(b)",
                    "variants": [
                        {"task": "Create variables x = 10 and y = 5, then print both on separate lines.", "expected": "10\n5", "validate": lambda self, c, o: '10' in o and '5' in o},
                        {"task": "Create variables x = 20 and y = 8, then print both on separate lines.", "expected": "20\n8", "validate": lambda self, c, o: '20' in o and '8' in o},
                        {"task": "Create variables x = 7 and y = 14, then print both on separate lines.", "expected": "7\n14", "validate": lambda self, c, o: '7' in o and '14' in o},
                        {"task": "Create variables x = 100 and y = 200, then print both on separate lines.", "expected": "100\n200", "validate": lambda self, c, o: '100' in o and '200' in o},
                        {"task": "Create variables x = 1 and y = 9, then print both on separate lines.", "expected": "1\n9", "validate": lambda self, c, o: '1' in o and '9' in o},
                        {"task": "Create variables x = 50 and y = 25, then print both on separate lines.", "expected": "50\n25", "validate": lambda self, c, o: '50' in o and '25' in o}
                    ],
                    "hint": "Define each variable on its own line, then call print() twice to display each one.",
                    "starter_code": "# Create and print multiple variables\n"
                },
                {
                    "title": "Lesson 2.5: Type Check",
                    "concept": "The type() function checks the data type of a value or variable.",
                    "concept_example": "print(type(42)) # Output: <class 'int'>",
                    "variants": [
                        {"task": "Create variable message = 'Hello', then print its type.", "expected": "<class 'str'>", "validate": lambda self, c, o: 'str' in o},
                        {"task": "Create variable age = 25, then print its type.", "expected": "<class 'int'>", "validate": lambda self, c, o: 'int' in o},
                        {"task": "Create variable price = 19.99, then print its type.", "expected": "<class 'float'>", "validate": lambda self, c, o: 'float' in o},
                        {"task": "Create variable is_coding = True, then print its type.", "expected": "<class 'bool'>", "validate": lambda self, c, o: 'bool' in o},
                        {"task": "Create variable values = [1, 2], then print its type.", "expected": "<class 'list'>", "validate": lambda self, c, o: 'list' in o},
                        {"task": "Create variable data = {'id': 1}, then print its type.", "expected": "<class 'dict'>", "validate": lambda self, c, o: 'dict' in o}
                    ],
                    "hint": "Pass the variable into the type() function, and wrap that inside a print() function call.",
                    "starter_code": "message = 'Hello'\n# Print type here\n"
                }
            ]
        }

        ch3 = {
            "title": "Chapter 3: Basic Operations",
            "lessons": [
                {
                    "title": "Lesson 3.1: Addition",
                    "concept": "Use the '+' operator to add numbers together.",
                    "concept_example": "print(5 + 3)",
                    "variants": [
                        {"task": "Print the result of 15 + 27.", "expected": "42", "validate": lambda self, c, o: o.strip() == '42'},
                        {"task": "Print the result of 50 + 75.", "expected": "125", "validate": lambda self, c, o: o.strip() == '125'},
                        {"task": "Print the result of 8 + 14.", "expected": "22", "validate": lambda self, c, o: o.strip() == '22'},
                        {"task": "Print the result of 100 + 45.", "expected": "145", "validate": lambda self, c, o: o.strip() == '145'},
                        {"task": "Print the result of 33 + 67.", "expected": "100", "validate": lambda self, c, o: o.strip() == '100'},
                        {"task": "Print the result of 12 + 18.", "expected": "30", "validate": lambda self, c, o: o.strip() == '30'}
                    ],
                    "hint": "Use the addition operator + inside a print() statement to add the numbers.",
                    "starter_code": "# Print the sum\n"
                },
                {
                    "title": "Lesson 3.2: Subtraction",
                    "concept": "Use the '-' operator to subtract one number from another.",
                    "concept_example": "print(10 - 4)",
                    "variants": [
                        {"task": "Print the result of 100 - 37.", "expected": "63", "validate": lambda self, c, o: o.strip() == '63'},
                        {"task": "Print the result of 50 - 15.", "expected": "35", "validate": lambda self, c, o: o.strip() == '35'},
                        {"task": "Print the result of 85 - 20.", "expected": "65", "validate": lambda self, c, o: o.strip() == '65'},
                        {"task": "Print the result of 200 - 45.", "expected": "155", "validate": lambda self, c, o: o.strip() == '155'},
                        {"task": "Print the result of 12 - 7.", "expected": "5", "validate": lambda self, c, o: o.strip() == '5'},
                        {"task": "Print the result of 99 - 99.", "expected": "0", "validate": lambda self, c, o: o.strip() == '0'}
                    ],
                    "hint": "Use the subtraction operator - to subtract the numbers inside the print statement.",
                    "starter_code": "# Print the difference\n"
                },
                {
                    "title": "Lesson 3.3: Multiplication",
                    "concept": "Use the '*' operator to multiply numbers.",
                    "concept_example": "print(3 * 4)",
                    "variants": [
                        {"task": "Print the result of 8 * 7.", "expected": "56", "validate": lambda self, c, o: o.strip() == '56'},
                        {"task": "Print the result of 5 * 12.", "expected": "60", "validate": lambda self, c, o: o.strip() == '60'},
                        {"task": "Print the result of 9 * 9.", "expected": "81", "validate": lambda self, c, o: o.strip() == '81'},
                        {"task": "Print the result of 11 * 4.", "expected": "44", "validate": lambda self, c, o: o.strip() == '44'},
                        {"task": "Print the result of 6 * 7.", "expected": "42", "validate": lambda self, c, o: o.strip() == '42'},
                        {"task": "Print the result of 15 * 3.", "expected": "45", "validate": lambda self, c, o: o.strip() == '45'}
                    ],
                    "hint": "Use the multiplication operator * to multiply the numbers inside the print statement.",
                    "starter_code": "# Print the product\n"
                },
                {
                    "title": "Lesson 3.4: Division",
                    "concept": "Use the '/' operator to divide numbers. The result is always a float.",
                    "concept_example": "print(10 / 2) # Output: 5.0",
                    "variants": [
                        {"task": "Print the result of 100 / 4.", "expected": "25.0", "validate": lambda self, c, o: '25.0' in o or o.strip() == '25'},
                        {"task": "Print the result of 80 / 5.", "expected": "16.0", "validate": lambda self, c, o: '16.0' in o or o.strip() == '16'},
                        {"task": "Print the result of 9 / 2.", "expected": "4.5", "validate": lambda self, c, o: '4.5' in o},
                        {"task": "Print the result of 30 / 3.", "expected": "10.0", "validate": lambda self, c, o: '10.0' in o or o.strip() == '10'},
                        {"task": "Print the result of 50 / 2.", "expected": "25.0", "validate": lambda self, c, o: '25.0' in o or o.strip() == '25'},
                        {"task": "Print the result of 15 / 5.", "expected": "3.0", "validate": lambda self, c, o: '3.0' in o or o.strip() == '3'}
                    ],
                    "hint": "Use the division operator / to divide the numbers inside the print statement.",
                    "starter_code": "# Print the quotient\n"
                },
                {
                    "title": "Lesson 3.5: Complex Math",
                    "concept": "Operations inside parentheses () are evaluated first, following PEMDAS math rules.",
                    "concept_example": "print((2 + 3) * 4)",
                    "variants": [
                        {"task": "Calculate and print: (10 + 5) * 3 - 15", "expected": "30", "validate": lambda self, c, o: o.strip() == '30'},
                        {"task": "Calculate and print: (20 - 5) * 2 + 10", "expected": "40", "validate": lambda self, c, o: o.strip() == '40'},
                        {"task": "Calculate and print: (4 + 6) * 5 - 20", "expected": "30", "validate": lambda self, c, o: o.strip() == '30'},
                        {"task": "Calculate and print: (8 + 2) * (5 - 3)", "expected": "20", "validate": lambda self, c, o: o.strip() == '20'},
                        {"task": "Calculate and print: (15 - 5) / 2 + 5", "expected": "10.0", "validate": lambda self, c, o: '10.0' in o or o.strip() == '10'},
                        {"task": "Calculate and print: (100 / 10) * 3 - 5", "expected": "25.0", "validate": lambda self, c, o: '25.0' in o or o.strip() == '25'}
                    ],
                    "hint": "Perform the operations inside a print statement. Use parentheses to ensure proper evaluation order.",
                    "starter_code": "# Calculate complex expression\n"
                }
            ]
        }

        ch4 = {
            "title": "Chapter 4: String Operations",
            "lessons": [
                {
                    "title": "Lesson 4.1: String Concatenation",
                    "concept": "You can combine (concatenate) strings together using the '+' operator.",
                    "concept_example": "full = \"hello\" + \"world\"",
                    "variants": [
                        {"task": "Create variables first = 'Python' and last = 'Programming', print them concatenated.", "expected": "PythonProgramming", "validate": lambda self, c, o: 'pythonprogramming' in o.lower()},
                        {"task": "Create variables first = 'Web' and last = 'Dev', print them concatenated.", "expected": "WebDev", "validate": lambda self, c, o: 'webdev' in o.lower()},
                        {"task": "Create variables first = 'Soft' and last = 'Ware', print them concatenated.", "expected": "SoftWare", "validate": lambda self, c, o: 'software' in o.lower()},
                        {"task": "Create variables first = 'Super' and last = 'Hero', print them concatenated.", "expected": "SuperHero", "validate": lambda self, c, o: 'superhero' in o.lower()},
                        {"task": "Create variables first = 'Code' and last = 'Base', print them concatenated.", "expected": "CodeBase", "validate": lambda self, c, o: 'codebase' in o.lower()},
                        {"task": "Create variables first = 'Play' and last = 'List', print them concatenated.", "expected": "PlayList", "validate": lambda self, c, o: 'playlist' in o.lower()}
                    ],
                    "hint": "Combine the variables using the '+' string concatenation operator inside print().",
                    "starter_code": "first = 'Python'\nlast = 'Programming'\n# Concatenate and print here\n"
                },
                {
                    "title": "Lesson 4.2: String Length",
                    "concept": "The len() function returns the total number of characters in a string (including spaces).",
                    "concept_example": "size = len(\"hi\") # 2",
                    "variants": [
                        {"task": "Print the length of the string 'Hello World'.", "expected": "11", "validate": lambda self, c, o: o.strip() == '11'},
                        {"task": "Print the length of the string 'Python Coding'.", "expected": "13", "validate": lambda self, c, o: o.strip() == '13'},
                        {"task": "Print the length of the string 'Supercalifragilistic'.", "expected": "20", "validate": lambda self, c, o: o.strip() == '20'},
                        {"task": "Print the length of the string 'Tkinter GUI'.", "expected": "11", "validate": lambda self, c, o: o.strip() == '11'},
                        {"task": "Print the length of the string 'Functions'.", "expected": "9", "validate": lambda self, c, o: o.strip() == '9'},
                        {"task": "Print the length of the string 'Developer'.", "expected": "9", "validate": lambda self, c, o: o.strip() == '9'}
                    ],
                    "hint": "Use the len() function on the target string and print the result.",
                    "starter_code": "# Print string length\n"
                },
                {
                    "title": "Lesson 4.3: Uppercase",
                    "concept": "The .upper() method converts all characters in a string to uppercase.",
                    "concept_example": "print(\"hello\".upper()) # HELLO",
                    "variants": [
                        {"task": "Convert 'python' to uppercase and print it.", "expected": "PYTHON", "validate": lambda self, c, o: o.strip() == 'PYTHON'},
                        {"task": "Convert 'learning' to uppercase and print it.", "expected": "LEARNING", "validate": lambda self, c, o: o.strip() == 'LEARNING'},
                        {"task": "Convert 'coding' to uppercase and print it.", "expected": "CODING", "validate": lambda self, c, o: o.strip() == 'CODING'},
                        {"task": "Convert 'variables' to uppercase and print it.", "expected": "VARIABLES", "validate": lambda self, c, o: o.strip() == 'VARIABLES'},
                        {"task": "Convert 'strings' to uppercase and print it.", "expected": "STRINGS", "validate": lambda self, c, o: o.strip() == 'STRINGS'},
                        {"task": "Convert 'developer' to uppercase and print it.", "expected": "DEVELOPER", "validate": lambda self, c, o: o.strip() == 'DEVELOPER'}
                    ],
                    "hint": "Call the .upper() method on the string and print the result.",
                    "starter_code": "# Convert to uppercase\n"
                },
                {
                    "title": "Lesson 4.4: Lowercase",
                    "concept": "The .lower() method converts all characters in a string to lowercase.",
                    "concept_example": "print(\"HI\".lower()) # hi",
                    "variants": [
                        {"task": "Convert 'PYTHON' to lowercase and print it.", "expected": "python", "validate": lambda self, c, o: o.strip() == 'python'},
                        {"task": "Convert 'LEARNING' to lowercase and print it.", "expected": "learning", "validate": lambda self, c, o: o.strip() == 'learning'},
                        {"task": "Convert 'CODING' to lowercase and print it.", "expected": "coding", "validate": lambda self, c, o: o.strip() == 'coding'},
                        {"task": "Convert 'VARIABLES' to lowercase and print it.", "expected": "variables", "validate": lambda self, c, o: o.strip() == 'variables'},
                        {"task": "Convert 'STRINGS' to lowercase and print it.", "expected": "strings", "validate": lambda self, c, o: o.strip() == 'strings'},
                        {"task": "Convert 'DEVELOPER' to lowercase and print it.", "expected": "developer", "validate": lambda self, c, o: o.strip() == 'developer'}
                    ],
                    "hint": "Call the .lower() method on the string and print the result.",
                    "starter_code": "# Convert to lowercase\n"
                },
                {
                    "title": "Lesson 4.5: String Slicing",
                    "concept": "Slicing extracts a part of a string using indexes. The syntax [start:end] takes characters from start index up to (but not including) end index.",
                    "concept_example": "print(\"Python\"[1:4]) # yth",
                    "variants": [
                        {"task": "Print the first 3 characters of 'Python'.", "expected": "Pyt", "validate": lambda self, c, o: o.strip() == 'Pyt'},
                        {"task": "Print the first 4 characters of 'Programming'.", "expected": "Prog", "validate": lambda self, c, o: o.strip() == 'Prog'},
                        {"task": "Print the first 2 characters of 'Developer'.", "expected": "De", "validate": lambda self, c, o: o.strip() == 'De'},
                        {"task": "Print characters at indexes 2 to 5 of 'Database'.", "expected": "tab", "validate": lambda self, c, o: o.strip() == 'tab'},
                        {"task": "Print characters at indexes 1 to 4 of 'Variables'.", "expected": "ari", "validate": lambda self, c, o: o.strip() == 'ari'},
                        {"task": "Print the last 3 characters of 'Python'.", "expected": "hon", "validate": lambda self, c, o: o.strip() == 'hon'}
                    ],
                    "hint": "Use slicing syntax (e.g. text[:3] for first three or text[-3:] for last three) and print it.",
                    "starter_code": "# Print sliced string\n"
                }
            ]
        }

        ch5 = {
            "title": "Chapter 5: Lists",
            "lessons": [
                {
                    "title": "Lesson 5.1: Create a List",
                    "concept": "Lists store multiple items in a single variable. Items are separated by commas inside square brackets [].",
                    "concept_example": "colors = [\"red\", \"green\", \"blue\"]",
                    "variants": [
                        {"task": "Create list 'fruits' with 'apple', 'banana', 'cherry', then print it.", "expected": "['apple', 'banana', 'cherry']", "validate": lambda self, c, o: 'apple' in o and 'banana' in o and 'cherry' in o},
                        {"task": "Create list 'colors' with 'red', 'green', 'blue', then print it.", "expected": "['red', 'green', 'blue']", "validate": lambda self, c, o: 'red' in o and 'green' in o and 'blue' in o},
                        {"task": "Create list 'numbers' with 1, 2, 3, then print it.", "expected": "[1, 2, 3]", "validate": lambda self, c, o: '1' in o and '2' in o and '3' in o},
                        {"task": "Create list 'languages' with 'Python', 'Java', then print it.", "expected": "['Python', 'Java']", "validate": lambda self, c, o: 'python' in o.lower() and 'java' in o.lower()},
                        {"task": "Create list 'sizes' with 'S', 'M', 'L', then print it.", "expected": "['S', 'M', 'L']", "validate": lambda self, c, o: 'S' in o and 'M' in o and 'L' in o},
                        {"task": "Create list 'cities' with 'NYC', 'LA', then print it.", "expected": "['NYC', 'LA']", "validate": lambda self, c, o: 'NYC' in o and 'LA' in o}
                    ],
                    "hint": "Create the list using brackets and comma-separated string/numeric elements, then print it.",
                    "starter_code": "# Create list and print it\n"
                },
                {
                    "title": "Lesson 5.2: Access List Item",
                    "concept": "Access items by index inside square brackets [index]. Note that Python indices start at 0.",
                    "concept_example": "first = items[0]",
                    "variants": [
                        {"task": "Given numbers = [10, 20, 30, 40, 50], print the first item (index 0).", "expected": "10", "validate": lambda self, c, o: o.strip() == '10'},
                        {"task": "Given numbers = [10, 20, 30, 40, 50], print the third item (index 2).", "expected": "30", "validate": lambda self, c, o: o.strip() == '30'},
                        {"task": "Given numbers = [10, 20, 30, 40, 50], print the last item (index 4 or -1).", "expected": "50", "validate": lambda self, c, o: o.strip() == '50'},
                        {"task": "Given colors = ['red', 'green', 'blue'], print the second item (index 1).", "expected": "green", "validate": lambda self, c, o: o.strip() == 'green'},
                        {"task": "Given items = ['A', 'B', 'C', 'D'], print the first item (index 0).", "expected": "A", "validate": lambda self, c, o: o.strip() == 'A'},
                        {"task": "Given items = ['A', 'B', 'C', 'D'], print the fourth item (index 3).", "expected": "D", "validate": lambda self, c, o: o.strip() == 'D'}
                    ],
                    "hint": "Access the list item using list_name[index] inside your print statement.",
                    "starter_code": "numbers = [10, 20, 30, 40, 50]\n# Print the correct item here\n"
                },
                {
                    "title": "Lesson 5.3: List Length",
                    "concept": "The len() function returns the total number of items stored in a list.",
                    "concept_example": "print(len([1, 2, 3])) # Output: 3",
                    "variants": [
                        {"task": "Given colors = ['red', 'green', 'blue'], print its length.", "expected": "3", "validate": lambda self, c, o: o.strip() == '3'},
                        {"task": "Given fruits = ['apple', 'banana', 'cherry', 'date'], print its length.", "expected": "4", "validate": lambda self, c, o: o.strip() == '4'},
                        {"task": "Given numbers = [5, 10, 15, 20, 25, 30], print its length.", "expected": "6", "validate": lambda self, c, o: o.strip() == '6'},
                        {"task": "Given items = ['single'], print its length.", "expected": "1", "validate": lambda self, c, o: o.strip() == '1'},
                        {"task": "Given list_data = [True, False], print its length.", "expected": "2", "validate": lambda self, c, o: o.strip() == '2'},
                        {"task": "Given items = [1, 2, 3, 4, 5], print its length.", "expected": "5", "validate": lambda self, c, o: o.strip() == '5'}
                    ],
                    "hint": "Pass the list variable into the len() function and print the result.",
                    "starter_code": "colors = ['red', 'green', 'blue']\n# Print length here\n"
                },
                {
                    "title": "Lesson 5.4: Add to List",
                    "concept": "The .append() method adds a new item to the end of a list.",
                    "concept_example": "items.append(\"new\")",
                    "variants": [
                        {"task": "Given nums = [1, 2, 3], append 4 to it, then print the list.", "expected": "[1, 2, 3, 4]", "validate": lambda self, c, o: '1' in o and '2' in o and '3' in o and '4' in o},
                        {"task": "Given colors = ['red', 'green'], append 'blue' to it, then print the list.", "expected": "['red', 'green', 'blue']", "validate": lambda self, c, o: 'red' in o and 'green' in o and 'blue' in o},
                        {"task": "Given list_data = ['A'], append 'B' to it, then print the list.", "expected": "['A', 'B']", "validate": lambda self, c, o: 'A' in o and 'B' in o},
                        {"task": "Given nums = [10, 20], append 30 to it, then print the list.", "expected": "[10, 20, 30]", "validate": lambda self, c, o: '10' in o and '20' in o and '30' in o},
                        {"task": "Given items = ['X', 'Y', 'Z'], append 'W' to it, then print the list.", "expected": "['X', 'Y', 'Z', 'W']", "validate": lambda self, c, o: 'X' in o and 'Y' in o and 'Z' in o and 'W' in o},
                        {"task": "Given nums = [5, 6, 7, 8], append 9 to it, then print the list.", "expected": "[5, 6, 7, 8, 9]", "validate": lambda self, c, o: '5' in o and '9' in o}
                    ],
                    "hint": "Call the .append() method on the list with the value, then print the modified list.",
                    "starter_code": "nums = [1, 2, 3]\n# Append 4 and print nums here\n"
                },
                {
                    "title": "Lesson 5.5: List Slicing",
                    "concept": "Slicing lists works like string slicing. Using list[:n] returns a sublist of the first n items.",
                    "concept_example": "print([10, 20, 30][:2]) # [10, 20]",
                    "variants": [
                        {"task": "Given numbers = [0, 1, 2, 3, 4, 5], print the first 3 items.", "expected": "[0, 1, 2]", "validate": lambda self, c, o: o.strip() == '[0, 1, 2]'},
                        {"task": "Given numbers = [0, 1, 2, 3, 4, 5], print the first 4 items.", "expected": "[0, 1, 2, 3]", "validate": lambda self, c, o: o.strip() == '[0, 1, 2, 3]'},
                        {"task": "Given numbers = [0, 1, 2, 3, 4, 5], print the first 2 items.", "expected": "[0, 1]", "validate": lambda self, c, o: o.strip() == '[0, 1]'},
                        {"task": "Given numbers = [0, 1, 2, 3, 4, 5], print items from index 2 to 4.", "expected": "[2, 3]", "validate": lambda self, c, o: o.strip() == '[2, 3]'},
                        {"task": "Given numbers = [0, 1, 2, 3, 4, 5], print items from index 1 to 5.", "expected": "[1, 2, 3, 4]", "validate": lambda self, c, o: o.strip() == '[1, 2, 3, 4]'},
                        {"task": "Given numbers = [0, 1, 2, 3, 4, 5], print items from index 3 to the end.", "expected": "[3, 4, 5]", "validate": lambda self, c, o: o.strip() == '[3, 4, 5]'}
                    ],
                    "hint": "Use the slicing syntax [:3] or [2:4] on the list inside the print statement.",
                    "starter_code": "numbers = [0, 1, 2, 3, 4, 5]\n# Print sliced list here\n"
                }
            ]
        }

        ch6 = {
            "title": "Chapter 6: Conditional Statements",
            "lessons": [
                {
                    "title": "Lesson 6.1: Basic If",
                    "concept": "An 'if' statement evaluates a condition. If the condition is True, the indented block of code runs.",
                    "concept_example": "if x > 5:\n    print(\"Big\")",
                    "variants": [
                        {"task": "Given age = 20. If age >= 18, print 'Adult'.", "expected": "Adult", "validate": lambda self, c, o: o.strip() == 'Adult'},
                        {"task": "Given age = 15. If age < 18, print 'Minor'.", "expected": "Minor", "validate": lambda self, c, o: o.strip() == 'Minor'},
                        {"task": "Given score = 85. If score >= 80, print 'Good'.", "expected": "Good", "validate": lambda self, c, o: o.strip() == 'Good'},
                        {"task": "Given price = 150. If price > 100, print 'Expensive'.", "expected": "Expensive", "validate": lambda self, c, o: o.strip() == 'Expensive'},
                        {"task": "Given speed = 75. If speed > 60, print 'Fast'.", "expected": "Fast", "validate": lambda self, c, o: o.strip() == 'Fast'},
                        {"task": "Given temperature = 35. If temperature > 30, print 'Hot'.", "expected": "Hot", "validate": lambda self, c, o: o.strip() == 'Hot'}
                    ],
                    "hint": "Write an 'if' block checking the condition, and indent the print statement directly below it.",
                    "starter_code": "age = 20\n# Write if statement here\n"
                },
                {
                    "title": "Lesson 6.2: If-Else",
                    "concept": "The 'else' block runs if the 'if' condition evaluates to False.",
                    "concept_example": "if score >= 50:\n    print(\"Pass\")\nelse:\n    print(\"Fail\")",
                    "variants": [
                        {"task": "Given score = 75. If score >= 60 print 'Pass', else print 'Fail'.", "expected": "Pass", "validate": lambda self, c, o: o.strip() == 'Pass'},
                        {"task": "Given score = 45. If score >= 60 print 'Pass', else print 'Fail'.", "expected": "Fail", "validate": lambda self, c, o: o.strip() == 'Fail'},
                        {"task": "Given price = 30. If price < 50 print 'Cheap', else print 'Expensive'.", "expected": "Cheap", "validate": lambda self, c, o: o.strip() == 'Cheap'},
                        {"task": "Given speed = 50. If speed > 60 print 'Fast', else print 'Slow'.", "expected": "Slow", "validate": lambda self, c, o: o.strip() == 'Slow'},
                        {"task": "Given temperature = 15. If temperature > 20 print 'Warm', else print 'Cold'.", "expected": "Cold", "validate": lambda self, c, o: o.strip() == 'Cold'},
                        {"task": "Given age = 16. If age >= 18 print 'Voter', else print 'Non-voter'.", "expected": "Non-voter", "validate": lambda self, c, o: o.strip() == 'Non-voter'}
                    ],
                    "hint": "Write an if-else statement checking the condition, matching indentation for both blocks.",
                    "starter_code": "score = 75\n# Write if-else statement here\n"
                },
                {
                    "title": "Lesson 6.3: Elif",
                    "concept": "The 'elif' (else if) block lets you check multiple sequential conditions if the previous conditions were False.",
                    "concept_example": "if x > 10:\n    print(\"Big\")\nelif x > 5:\n    print(\"Medium\")\nelse:\n    print(\"Small\")",
                    "variants": [
                        {"task": "Given grade = 85. Print 'A' if >= 90, 'B' if >= 80, 'C' otherwise.", "expected": "B", "validate": lambda self, c, o: o.strip() == 'B'},
                        {"task": "Given grade = 95. Print 'A' if >= 90, 'B' if >= 80, 'C' otherwise.", "expected": "A", "validate": lambda self, c, o: o.strip() == 'A'},
                        {"task": "Given grade = 65. Print 'A' if >= 90, 'B' if >= 80, 'C' otherwise.", "expected": "C", "validate": lambda self, c, o: o.strip() == 'C'},
                        {"task": "Given score = 15. Print 'High' if >= 20, 'Medium' if >= 10, 'Low' otherwise.", "expected": "Medium", "validate": lambda self, c, o: o.strip() == 'Medium'},
                        {"task": "Given speed = 120. Print 'Fast' if >= 100, 'Alert' if >= 80, 'Safe' otherwise.", "expected": "Fast", "validate": lambda self, c, o: o.strip() == 'Fast'},
                        {"task": "Given price = 5. Print 'High' if >= 20, 'Mid' if >= 10, 'Free' otherwise.", "expected": "Free", "validate": lambda self, c, o: o.strip() == 'Free'}
                    ],
                    "hint": "Write an if-elif-else chain to handle all three criteria in order.",
                    "starter_code": "grade = 85\n# Write if-elif-else here\n"
                },
                {
                    "title": "Lesson 6.4: Multiple Conditions",
                    "concept": "Combine multiple conditions in one statement using logical operators. 'and' requires both to be True.",
                    "concept_example": "if a > 0 and a < 10:\n    print(\"In range\")",
                    "variants": [
                        {"task": "Given x = 10. Print 'Valid' if x > 5 and x < 15, else print 'Invalid'.", "expected": "Valid", "validate": lambda self, c, o: o.strip() == 'Valid'},
                        {"task": "Given x = 20. Print 'Valid' if x > 5 and x < 15, else print 'Invalid'.", "expected": "Invalid", "validate": lambda self, c, o: o.strip() == 'Invalid'},
                        {"task": "Given age = 25. Print 'Eligible' if age >= 18 and age <= 30, else print 'Ineligible'.", "expected": "Eligible", "validate": lambda self, c, o: o.strip() == 'Eligible'},
                        {"task": "Given score = 80. Print 'Honor' if score >= 70 and score <= 90, else print 'Normal'.", "expected": "Honor", "validate": lambda self, c, o: o.strip() == 'Honor'},
                        {"task": "Given temp = 10. Print 'Cozy' if temp >= 15 and temp <= 25, else print 'Extreme'.", "expected": "Extreme", "validate": lambda self, c, o: o.strip() == 'Extreme'},
                        {"task": "Given speed = 40. Print 'Highway' if speed >= 50 and speed <= 80, else print 'Local'.", "expected": "Local", "validate": lambda self, c, o: o.strip() == 'Local'}
                    ],
                    "hint": "Combine the two expressions using the 'and' operator in your if statement.",
                    "starter_code": "x = 10\n# Write statement here\n"
                },
                {
                    "title": "Lesson 6.5: Nested If",
                    "concept": "Nested conditionals are 'if' statements placed inside another 'if' statement's block.",
                    "concept_example": "if x > 10:\n    if y > 10:\n        print(\"Both big\")",
                    "variants": [
                        {"task": "Given num = 15. If num > 10, check if num < 20 and print 'Between 10 and 20'.", "expected": "Between 10 and 20", "validate": lambda self, c, o: 'between 10 and 20' in o.lower()},
                        {"task": "Given val = 30. If val > 20, check if val < 40 and print 'In zone'.", "expected": "In zone", "validate": lambda self, c, o: 'in zone' in o.lower()},
                        {"task": "Given temperature = 35. If temperature > 30, check if temperature < 40 and print 'Hot Day'.", "expected": "Hot Day", "validate": lambda self, c, o: 'hot day' in o.lower()},
                        {"task": "Given score = 95. If score > 90, check if score <= 100 and print 'A Plus'.", "expected": "A Plus", "validate": lambda self, c, o: 'a plus' in o.lower()},
                        {"task": "Given speed = 65. If speed > 60, check if speed < 80 and print 'Cruising'.", "expected": "Cruising", "validate": lambda self, c, o: 'cruising' in o.lower()},
                        {"task": "Given price = 8. If price > 5, check if price < 10 and print 'Budget'.", "expected": "Budget", "validate": lambda self, c, o: 'budget' in o.lower()}
                    ],
                    "hint": "Write an outer if block. Indented inside it, write another if statement check.",
                    "starter_code": "num = 15\n# Write nested if here\n"
                }
            ]
        }

        ch7 = {
            "title": "Chapter 7: Loops",
            "lessons": [
                {
                    "title": "Lesson 7.1: For Loop Range",
                    "concept": "A 'for' loop repeats code. range(start, stop) generates numbers starting at 'start' up to (but excluding) 'stop'.",
                    "concept_example": "for i in range(1, 4):\n    print(i) # Prints 1, 2, 3",
                    "variants": [
                        {"task": "Use a for loop to print numbers 1 to 5.", "expected": "1\n2\n3\n4\n5", "validate": lambda self, c, o: o.strip() == '1\n2\n3\n4\n5'},
                        {"task": "Use a for loop to print numbers 1 to 4.", "expected": "1\n2\n3\n4", "validate": lambda self, c, o: o.strip() == '1\n2\n3\n4'},
                        {"task": "Use a for loop to print numbers 2 to 5.", "expected": "2\n3\n4\n5", "validate": lambda self, c, o: o.strip() == '2\n3\n4\n5'},
                        {"task": "Use a for loop to print numbers 1 to 3.", "expected": "1\n2\n3", "validate": lambda self, c, o: o.strip() == '1\n2\n3'},
                        {"task": "Use a for loop to print numbers 0 to 4.", "expected": "0\n1\n2\n3\n4", "validate": lambda self, c, o: o.strip() == '0\n1\n2\n3\n4'},
                        {"task": "Use a for loop to print numbers 5 to 8.", "expected": "5\n6\n7\n8", "validate": lambda self, c, o: o.strip() == '5\n6\n7\n8'}
                    ],
                    "hint": "Use 'for i in range(start, stop + 1):' and call print(i) inside the loop.",
                    "starter_code": "# Write for loop here\n"
                },
                {
                    "title": "Lesson 7.2: For Loop List",
                    "concept": "Iterate directly over elements in a list using 'for item in list_name:'.",
                    "concept_example": "for name in names:\n    print(name)",
                    "variants": [
                        {"task": "Given fruits = ['apple', 'banana', 'cherry'], use a for loop to print each fruit.", "expected": "apple\nbanana\ncherry", "validate": lambda self, c, o: 'apple' in o and 'banana' in o and 'cherry' in o},
                        {"task": "Given colors = ['red', 'green', 'blue'], use a for loop to print each color.", "expected": "red\ngreen\nblue", "validate": lambda self, c, o: 'red' in o and 'green' in o and 'blue' in o},
                        {"task": "Given items = ['A', 'B', 'C'], use a for loop to print each item.", "expected": "A\nB\nC", "validate": lambda self, c, o: 'A' in o and 'B' in o and 'C' in o},
                        {"task": "Given names = ['Alice', 'Bob'], use a for loop to print each name.", "expected": "Alice\nBob", "validate": lambda self, c, o: 'Alice' in o and 'Bob' in o},
                        {"task": "Given items = ['10', '20'], use a for loop to print each item.", "expected": "10\n20", "validate": lambda self, c, o: '10' in o and '20' in o},
                        {"task": "Given brands = ['Nike', 'Puma'], use a for loop to print each brand.", "expected": "Nike\nPuma", "validate": lambda self, c, o: 'Nike' in o and 'Puma' in o}
                    ],
                    "hint": "Loop directly through the items using 'for item in list_name:' and print each item.",
                    "starter_code": "fruits = ['apple', 'banana', 'cherry']\n# Write loop here\n"
                },
                {
                    "title": "Lesson 7.3: While Loop",
                    "concept": "A 'while' loop repeats code as long as its condition remains True. Be sure to increment your counter inside the loop.",
                    "concept_example": "i = 0\nwhile i < 3:\n    print(i)\n    i += 1",
                    "variants": [
                        {"task": "Use a while loop to print numbers 0, 1, 2.", "expected": "0\n1\n2", "validate": lambda self, c, o: o.strip() == '0\n1\n2'},
                        {"task": "Use a while loop to print numbers 1, 2, 3.", "expected": "1\n2\n3", "validate": lambda self, c, o: o.strip() == '1\n2\n3'},
                        {"task": "Use a while loop to print numbers 0, 1, 2, 3.", "expected": "0\n1\n2\n3", "validate": lambda self, c, o: o.strip() == '0\n1\n2\n3'},
                        {"task": "Use a while loop to print numbers 5, 6, 7.", "expected": "5\n6\n7", "validate": lambda self, c, o: o.strip() == '5\n6\n7'},
                        {"task": "Use a while loop to print numbers 10, 11.", "expected": "10\n11", "validate": lambda self, c, o: o.strip() == '10\n11'},
                        {"task": "Use a while loop to print numbers 0, 1.", "expected": "0\n1", "validate": lambda self, c, o: o.strip() == '0\n1'}
                    ],
                    "hint": "Initialize a counter variable, check the condition in the loop header, print, and increment the counter in the block.",
                    "starter_code": "# Write while loop here\n"
                },
                {
                    "title": "Lesson 7.4: Break Statement",
                    "concept": "The 'break' statement terminates the current loop immediately.",
                    "concept_example": "for i in range(10):\n    if i == 3:\n        break\n    print(i)",
                    "variants": [
                        {"task": "Loop range(1, 10), print each number, but break when i equals 5.", "expected": "1\n2\n3\n4", "validate": lambda self, c, o: o.strip() == '1\n2\n3\n4'},
                        {"task": "Loop range(1, 10), print each number, but break when i equals 4.", "expected": "1\n2\n3", "validate": lambda self, c, o: o.strip() == '1\n2\n3'},
                        {"task": "Loop range(1, 10), print each number, but break when i equals 3.", "expected": "1\n2", "validate": lambda self, c, o: o.strip() == '1\n2'},
                        {"task": "Loop range(5, 15), print each number, but break when i equals 9.", "expected": "5\n6\n7\n8", "validate": lambda self, c, o: o.strip() == '5\n6\n7\n8'},
                        {"task": "Loop range(10, 20), print each number, but break when i equals 13.", "expected": "10\n11\n12", "validate": lambda self, c, o: o.strip() == '10\n11\n12'},
                        {"task": "Loop range(1, 10), print each number, but break when i equals 2.", "expected": "1", "validate": lambda self, c, o: o.strip() == '1'}
                    ],
                    "hint": "Inside the loop, write a conditional check 'if i == target:' and trigger the break statement.",
                    "starter_code": "# Write loop with break here\n"
                },
                {
                    "title": "Lesson 7.5: Sum with Loop",
                    "concept": "Accumulate a sum over loop iterations using a variable initialized outside the loop.",
                    "concept_example": "total = 0\nfor x in [1, 2]:\n    total += x\nprint(total)",
                    "variants": [
                        {"task": "Use a for loop to calculate and print the sum of numbers 1 to 10.", "expected": "55", "validate": lambda self, c, o: o.strip() == '55'},
                        {"task": "Use a for loop to calculate and print the sum of numbers 1 to 5.", "expected": "15", "validate": lambda self, c, o: o.strip() == '15'},
                        {"task": "Use a for loop to calculate and print the sum of numbers 1 to 4.", "expected": "10", "validate": lambda self, c, o: o.strip() == '10'},
                        {"task": "Use a for loop to calculate and print the sum of numbers 1 to 6.", "expected": "21", "validate": lambda self, c, o: o.strip() == '21'},
                        {"task": "Use a for loop to calculate and print the sum of numbers 1 to 20.", "expected": "210", "validate": lambda self, c, o: o.strip() == '210'},
                        {"task": "Use a for loop to calculate and print the sum of numbers 1 to 8.", "expected": "36", "validate": lambda self, c, o: o.strip() == '36'}
                    ],
                    "hint": "Initialize a sum variable to 0, loop through the range of numbers, add each to the sum, and print the sum outside the loop.",
                    "starter_code": "# Calculate sum using a loop and print it\n"
                }
            ]
        }

        ch8 = {
            "title": "Chapter 8: Dictionaries",
            "lessons": [
                {
                    "title": "Lesson 8.1: Create Dictionary",
                    "concept": "Dictionaries store key-value pairs inside curly braces {}. Keys and values are separated by colons.",
                    "concept_example": "user = {\"name\": \"Bob\", \"age\": 25}",
                    "variants": [
                        {"task": "Create dict person = {'name': 'John', 'age': 30}, then print it.", "expected": "{'name': 'John', 'age': 30}", "validate": lambda self, c, o: 'name' in o and 'John' in o and 'age' in o and '30' in o},
                        {"task": "Create dict person = {'name': 'Alice', 'age': 25}, then print it.", "expected": "{'name': 'Alice', 'age': 25}", "validate": lambda self, c, o: 'name' in o and 'Alice' in o and 'age' in o and '25' in o},
                        {"task": "Create dict car = {'brand': 'Ford', 'year': 1964}, then print it.", "expected": "{'brand': 'Ford', 'year': 1964}", "validate": lambda self, c, o: 'brand' in o and 'Ford' in o and 'year' in o and '1964' in o},
                        {"task": "Create dict item = {'name': 'Pen', 'price': 1.5}, then print it.", "expected": "{'name': 'Pen', 'price': 1.5}", "validate": lambda self, c, o: 'name' in o and 'Pen' in o and 'price' in o and '1.5' in o},
                        {"task": "Create dict data = {'id': 101, 'status': 'OK'}, then print it.", "expected": "{'id': 101, 'status': 'OK'}", "validate": lambda self, c, o: 'id' in o and '101' in o and 'status' in o and 'OK' in o},
                        {"task": "Create dict score = {'math': 90, 'art': 95}, then print it.", "expected": "{'math': 90, 'art': 95}", "validate": lambda self, c, o: 'math' in o and '90' in o and 'art' in o and '95' in o}
                    ],
                    "hint": "Define a dictionary using curly braces containing key-value pairs, then print it.",
                    "starter_code": "# Create dictionary and print it\n"
                },
                {
                    "title": "Lesson 8.2: Access Value",
                    "concept": "Access values in a dictionary by passing the key in square brackets [key].",
                    "concept_example": "val = user[\"name\"]",
                    "variants": [
                        {"task": "Given student = {'name': 'Alice', 'grade': 'A'}, print the value of key 'name'.", "expected": "Alice", "validate": lambda self, c, o: o.strip() == 'Alice'},
                        {"task": "Given student = {'name': 'Alice', 'grade': 'A'}, print the value of key 'grade'.", "expected": "A", "validate": lambda self, c, o: o.strip() == 'A'},
                        {"task": "Given car = {'brand': 'Toyota', 'year': 2020}, print the brand name.", "expected": "Toyota", "validate": lambda self, c, o: o.strip() == 'Toyota'},
                        {"task": "Given item = {'id': 'P100', 'cost': 12}, print the value of key 'id'.", "expected": "P100", "validate": lambda self, c, o: o.strip() == 'P100'},
                        {"task": "Given user = {'user': 'admin', 'role': 'root'}, print the value of key 'role'.", "expected": "root", "validate": lambda self, c, o: o.strip() == 'root'},
                        {"task": "Given book = {'title': 'Python', 'pages': 300}, print the page count.", "expected": "300", "validate": lambda self, c, o: o.strip() == '300'}
                    ],
                    "hint": "Pass the target key inside brackets on the dictionary variable name in your print statement.",
                    "starter_code": "student = {'name': 'Alice', 'grade': 'A'}\n# Access and print the key value here\n"
                },
                {
                    "title": "Lesson 8.3: Add Key-Value",
                    "concept": "Add or modify key-value pairs using dictionary[new_key] = value.",
                    "concept_example": "user[\"status\"] = \"active\"",
                    "variants": [
                        {"task": "Given car = {'brand': 'Toyota'}, add key 'year' with value 2023, and print the dict.", "expected": "{'brand': 'Toyota', 'year': 2023}", "validate": lambda self, c, o: 'brand' in o and 'Toyota' in o and 'year' in o and '2023' in o},
                        {"task": "Given user = {'name': 'Bob'}, add key 'role' with value 'admin', and print the dict.", "expected": "{'name': 'Bob', 'role': 'admin'}", "validate": lambda self, c, o: 'name' in o and 'Bob' in o and 'role' in o and 'admin' in o},
                        {"task": "Given student = {'name': 'Alice'}, add key 'grade' with value 'A', and print the dict.", "expected": "{'name': 'Alice', 'grade': 'A'}", "validate": lambda self, c, o: 'name' in o and 'Alice' in o and 'grade' in o and 'A' in o},
                        {"task": "Given items = {'pen': 1}, add key 'pencil' with value 2, and print the dict.", "expected": "{'pen': 1, 'pencil': 2}", "validate": lambda self, c, o: 'pen' in o and '1' in o and 'pencil' in o and '2' in o},
                        {"task": "Given state = {'running': True}, add key 'error' with value False, and print the dict.", "expected": "{'running': True, 'error': False}", "validate": lambda self, c, o: 'running' in o and 'True' in o and 'error' in o and 'False' in o},
                        {"task": "Given data = {'id': 1}, add key 'name' with value 'game', and print the dict.", "expected": "{'id': 1, 'name': 'game'}", "validate": lambda self, c, o: 'id' in o and '1' in o and 'name' in o and 'game' in o}
                    ],
                    "hint": "Assign the new value to the new key using dictionary bracket notation, then print the dictionary.",
                    "starter_code": "car = {'brand': 'Toyota'}\n# Add key-value and print car here\n"
                },
                {
                    "title": "Lesson 8.4: Dictionary Keys",
                    "concept": "The .keys() method returns a sequence of all the keys in a dictionary.",
                    "concept_example": "print(user.keys())",
                    "variants": [
                        {"task": "Given book = {'title': 'Python', 'pages': 300}, print all keys.", "expected": "dict_keys(['title', 'pages'])", "validate": lambda self, c, o: 'title' in o and 'pages' in o},
                        {"task": "Given user = {'name': 'Bob', 'age': 30}, print all keys.", "expected": "dict_keys(['name', 'age'])", "validate": lambda self, c, o: 'name' in o and 'age' in o},
                        {"task": "Given info = {'id': 101, 'city': 'NY'}, print all keys.", "expected": "dict_keys(['id', 'city'])", "validate": lambda self, c, o: 'id' in o and 'city' in o},
                        {"task": "Given car = {'make': 'Ford', 'model': 'Mustang'}, print all keys.", "expected": "dict_keys(['make', 'model'])", "validate": lambda self, c, o: 'make' in o and 'model' in o},
                        {"task": "Given fruit = {'type': 'apple', 'color': 'red'}, print all keys.", "expected": "dict_keys(['type', 'color'])", "validate": lambda self, c, o: 'type' in o and 'color' in o},
                        {"task": "Given state = {'ok': True, 'code': 200}, print all keys.", "expected": "dict_keys(['ok', 'code'])", "validate": lambda self, c, o: 'ok' in o and 'code' in o}
                    ],
                    "hint": "Call the .keys() method on the dictionary object inside the print statement.",
                    "starter_code": "book = {'title': 'Python', 'pages': 300}\n# Print keys here\n"
                },
                {
                    "title": "Lesson 8.5: Iterate Dictionary",
                    "concept": "Use .items() to iterate over key-value pairs in a dictionary inside a loop.",
                    "concept_example": "for k, v in user.items():\n    print(k, v)",
                    "variants": [
                        {"task": "Given scores = {'math': 90, 'english': 85}, print each key and value separated by space.", "expected": "math 90\nenglish 85", "validate": lambda self, c, o: 'math' in o and '90' in o and 'english' in o and '85' in o},
                        {"task": "Given prices = {'milk': 3, 'bread': 2}, print each key and value separated by space.", "expected": "milk 3\nbread 2", "validate": lambda self, c, o: 'milk' in o and '3' in o and 'bread' in o and '2' in o},
                        {"task": "Given ages = {'Bob': 20, 'Ann': 22}, print each key and value separated by space.", "expected": "Bob 20\nAnn 22", "validate": lambda self, c, o: 'Bob' in o and '20' in o and 'Ann' in o and '22' in o},
                        {"task": "Given stats = {'hp': 100, 'mp': 50}, print each key and value separated by space.", "expected": "hp 100\nmp 50", "validate": lambda self, c, o: 'hp' in o and '100' in o and 'mp' in o and '50' in o},
                        {"task": "Given inventory = {'gold': 10, 'wood': 5}, print each key and value separated by space.", "expected": "gold 10\nwood 5", "validate": lambda self, c, o: 'gold' in o and '10' in o and 'wood' in o and '5' in o},
                        {"task": "Given points = {'x': 1, 'y': 2}, print each key and value separated by space.", "expected": "x 1\ny 2", "validate": lambda self, c, o: 'x' in o and '1' in o and 'y' in o and '2' in o}
                    ],
                    "hint": "Use a for loop with key, value variables and the dictionary .items() method, and print the key and value inside the loop.",
                    "starter_code": "scores = {'math': 90, 'english': 85}\n# Iterate and print here\n"
                }
            ]
        }

        ch9 = {
            "title": "Chapter 9: Functions",
            "lessons": [
                {
                    "title": "Lesson 9.1: Simple Function",
                    "concept": "Define a function using the 'def' keyword. Call a function by its name with parentheses.",
                    "concept_example": "def greet():\n    print(\"Hi\")\n\ngreet()",
                    "variants": [
                        {"task": "Define function greet() that prints 'Hello!', then call it.", "expected": "Hello!", "validate": lambda self, c, o: 'hello!' in o.lower()},
                        {"task": "Define function show() that prints 'Python!', then call it.", "expected": "Python!", "validate": lambda self, c, o: 'python!' in o.lower()},
                        {"task": "Define function run() that prints 'Start!', then call it.", "expected": "Start!", "validate": lambda self, c, o: 'start!' in o.lower()},
                        {"task": "Define function finish() that prints 'Done!', then call it.", "expected": "Done!", "validate": lambda self, c, o: 'done!' in o.lower()},
                        {"task": "Define function alert() that prints 'Warning!', then call it.", "expected": "Warning!", "validate": lambda self, c, o: 'warning!' in o.lower()},
                        {"task": "Define function test() that prints 'OK!', then call it.", "expected": "OK!", "validate": lambda self, c, o: 'ok!' in o.lower()}
                    ],
                    "hint": "Use def to define the function, indent the print statement inside it, and invoke the function using () afterwards.",
                    "starter_code": "# Define and call function here\n"
                },
                {
                    "title": "Lesson 9.2: Function with Parameter",
                    "concept": "Parameters are variables defined in the function signature. Arguments are values passed when calling it.",
                    "concept_example": "def say(msg):\n    print(msg)\n\nsay(\"Hi\")",
                    "variants": [
                        {"task": "Define function say_hello(name) that prints 'Hello, [name]!', call it with 'Bob'.", "expected": "Hello, Bob!", "validate": lambda self, c, o: 'hello, bob!' in o.lower()},
                        {"task": "Define function say_hello(name) that prints 'Hello, [name]!', call it with 'Alice'.", "expected": "Hello, Alice!", "validate": lambda self, c, o: 'hello, alice!' in o.lower()},
                        {"task": "Define function greet_user(username) that prints 'Welcome, [username]!', call it with 'Admin'.", "expected": "Welcome, Admin!", "validate": lambda self, c, o: 'welcome, admin!' in o.lower()},
                        {"task": "Define function show_item(item) that prints 'Item: [item]', call it with 'Sword'.", "expected": "Item: Sword", "validate": lambda self, c, o: 'item: sword' in o.lower()},
                        {"task": "Define function display_speed(s) that prints 'Speed: [s] mph', call it with '60'.", "expected": "Speed: 60 mph", "validate": lambda self, c, o: 'speed: 60 mph' in o.lower()},
                        {"task": "Define function log_status(status) that prints 'Status: [status]', call it with 'Active'.", "expected": "Status: Active", "validate": lambda self, c, o: 'status: active' in o.lower()}
                    ],
                    "hint": "Define function with parameter name, use format string or concatenation to output, and call with argument.",
                    "starter_code": "# Define and call parameterized function here\n"
                },
                {
                    "title": "Lesson 9.3: Function with Return",
                    "concept": "The 'return' keyword sends a value back from the function, ending its execution.",
                    "concept_example": "def double(x):\n    return x * 2\n\nprint(double(5))",
                    "variants": [
                        {"task": "Define function add(a, b) that returns a + b, print add(5, 3).", "expected": "8", "validate": lambda self, c, o: o.strip() == '8'},
                        {"task": "Define function mul(a, b) that returns a * b, print mul(4, 5).", "expected": "20", "validate": lambda self, c, o: o.strip() == '20'},
                        {"task": "Define function square(x) that returns x**2, print square(6).", "expected": "36", "validate": lambda self, c, o: o.strip() == '36'},
                        {"task": "Define function sub(a, b) that returns a - b, print sub(10, 7).", "expected": "3", "validate": lambda self, c, o: o.strip() == '3'},
                        {"task": "Define function get_half(x) that returns x / 2, print get_half(10).", "expected": "5.0", "validate": lambda self, c, o: '5.0' in o or o.strip() == '5'},
                        {"task": "Define function get_next(x) that returns x + 1, print get_next(99).", "expected": "100", "validate": lambda self, c, o: o.strip() == '100'}
                    ],
                    "hint": "Use the return keyword in the function instead of printing directly, then wrap the function call in a print statement.",
                    "starter_code": "# Define function and print the return value here\n"
                },
                {
                    "title": "Lesson 9.4: Default Parameter",
                    "concept": "Default parameters take a fallback value if no argument is passed during the function call.",
                    "concept_example": "def greet(name=\"Guest\"):\n    print(\"Hello \" + name)",
                    "variants": [
                        {"task": "Define function power(base, exp=2) that returns base**exp. Print power(3) and power(3, 3) on separate lines.", "expected": "9\n27", "validate": lambda self, c, o: '9' in o and '27' in o},
                        {"task": "Define function power(base, exp=2) that returns base**exp. Print power(5) and power(2, 4) on separate lines.", "expected": "25\n16", "validate": lambda self, c, o: '25' in o and '16' in o},
                        {"task": "Define function greet(name, msg='Hello') that returns f'{msg}, {name}'. Print greet('Bob') and greet('Alice', 'Hi') on separate lines.", "expected": "Hello, Bob\nHi, Alice", "validate": lambda self, c, o: 'hello, bob' in o.lower() and 'hi, alice' in o.lower()},
                        {"task": "Define function mult(x, factor=10) that returns x * factor. Print mult(5) and mult(5, 3) on separate lines.", "expected": "50\n15", "validate": lambda self, c, o: '50' in o and '15' in o},
                        {"task": "Define function inc(x, step=1) that returns x + step. Print inc(10) and inc(10, 5) on separate lines.", "expected": "11\n15", "validate": lambda self, c, o: '11' in o and '15' in o},
                        {"task": "Define function greet(name='Guest') that returns f'Hi {name}'. Print greet() and greet('Bob') on separate lines.", "expected": "Hi Guest\nHi Bob", "validate": lambda self, c, o: 'hi guest' in o.lower() and 'hi bob' in o.lower()}
                    ],
                    "hint": "Assign the default value in parameter definition (e.g. param=value), perform calculations/returns, print both calls.",
                    "starter_code": "# Define function and print results here\n"
                },
                {
                    "title": "Lesson 9.5: Multiple Returns",
                    "concept": "Python functions can return multiple values separated by commas. They are returned as a tuple.",
                    "concept_example": "def get_data():\n    return \"Alice\", 25\n\nprint(get_data()) # Output: ('Alice', 25)",
                    "variants": [
                        {"task": "Define function calc(a, b) that returns both a+b and a-b. Print it with arguments 10 and 5.", "expected": "(15, 5)", "validate": lambda self, c, o: '15' in o and '5' in o},
                        {"task": "Define function get_bounds(x) that returns x-1 and x+1. Print it with argument 5.", "expected": "(4, 6)", "validate": lambda self, c, o: '4' in o and '6' in o},
                        {"task": "Define function stats(nums) that returns min(nums) and max(nums). Print stats([2, 8, 5]).", "expected": "(2, 8)", "validate": lambda self, c, o: '2' in o and '8' in o},
                        {"task": "Define function parse_name(full_name) that splits string and returns first, last name. Print parse_name('John Doe').", "expected": "('John', 'Doe')", "validate": lambda self, c, o: 'john' in o.lower() and 'doe' in o.lower()},
                        {"task": "Define function get_coords() that returns x=100 and y=200. Print get_coords().", "expected": "(100, 200)", "validate": lambda self, c, o: '100' in o and '200' in o},
                        {"task": "Define function divide(a, b) that returns quotient a//b and remainder a%b. Print divide(10, 3).", "expected": "(3, 1)", "validate": lambda self, c, o: '3' in o and '1' in o}
                    ],
                    "hint": "Return multiple items separated by comma, e.g. return x, y, then print function call.",
                    "starter_code": "# Define function and print call here\n"
                }
            ]
        }

        ch10 = {
            "title": "Chapter 10: Advanced Concepts",
            "lessons": [
                {
                    "title": "Lesson 10.1: List Comprehension",
                    "concept": "List comprehension offers a shorter syntax to create a new list from an existing sequence.",
                    "concept_example": "squares = [x**2 for x in range(3)]",
                    "variants": [
                        {"task": "Use list comprehension to create list of squares [1, 4, 9, 16, 25] for numbers 1-5 and print it.", "expected": "[1, 4, 9, 16, 25]", "validate": lambda self, c, o: o.strip() == '[1, 4, 9, 16, 25]'},
                        {"task": "Use list comprehension to double numbers in range(1, 6) returning [2, 4, 6, 8, 10] and print it.", "expected": "[2, 4, 6, 8, 10]", "validate": lambda self, c, o: o.strip() == '[2, 4, 6, 8, 10]'},
                        {"task": "Use list comprehension to add 10 to range(1, 4) returning [11, 12, 13] and print it.", "expected": "[11, 12, 13]", "validate": lambda self, c, o: o.strip() == '[11, 12, 13]'},
                        {"task": "Use list comprehension to get cubes [1, 8, 27] for numbers 1-3 and print it.", "expected": "[1, 8, 27]", "validate": lambda self, c, o: o.strip() == '[1, 8, 27]'},
                        {"task": "Use list comprehension to filter even numbers in range(1, 6) returning [2, 4] and print it.", "expected": "[2, 4]", "validate": lambda self, c, o: o.strip() == '[2, 4]'},
                        {"task": "Use list comprehension to convert ['a','b'] to uppercase returning ['A','B'] and print it.", "expected": "['A', 'B']", "validate": lambda self, c, o: 'A' in o and 'B' in o}
                    ],
                    "hint": "Write expression like [x**2 for x in range(1, 6)] inside print().",
                    "starter_code": "# Write list comprehension and print it\n"
                },
                {
                    "title": "Lesson 10.2: Try-Except",
                    "concept": "Handle errors using try-except blocks, preventing the program from crashing on runtime exceptions.",
                    "concept_example": "try:\n    # code that might crash\nexcept:\n    # fallback code",
                    "variants": [
                        {"task": "Use try-except to handle division by zero. Try to print 10/0, catch exception and print 'Error'.", "expected": "Error", "validate": lambda self, c, o: 'error' in o.lower() or 'exception' in o.lower()},
                        {"task": "Use try-except to handle index error. Try to print list [1,2][5], catch exception and print 'Error'.", "expected": "Error", "validate": lambda self, c, o: 'error' in o.lower() or 'exception' in o.lower()},
                        {"task": "Use try-except to handle value error. Try to execute int('abc'), catch exception and print 'Invalid'.", "expected": "Invalid", "validate": lambda self, c, o: 'invalid' in o.lower() or 'error' in o.lower()},
                        {"task": "Use try-except to handle name error. Try to print undefined variable 'non_existent', catch exception and print 'Missing'.", "expected": "Missing", "validate": lambda self, c, o: 'missing' in o.lower() or 'error' in o.lower()},
                        {"task": "Use try-except to handle key error. Try to print dict {}['key'], catch exception and print 'Key Error'.", "expected": "Key Error", "validate": lambda self, c, o: 'key' in o.lower() or 'error' in o.lower()},
                        {"task": "Use try-except to handle type error. Try to calculate 'a' + 1, catch exception and print 'Bad Type'.", "expected": "Bad Type", "validate": lambda self, c, o: 'bad type' in o.lower() or 'error' in o.lower()}
                    ],
                    "hint": "Wrap the crashing operation in a 'try' block, catch using 'except:', and print fallback message in the handler.",
                    "starter_code": "# Use try-except block here\n"
                },
                {
                    "title": "Lesson 10.3: Lambda Function",
                    "concept": "A lambda function is a small anonymous function defined using the 'lambda' keyword.",
                    "concept_example": "double = lambda x: x * 2\nprint(double(5)) # Output: 10",
                    "variants": [
                        {"task": "Create lambda function square = lambda x: x**2, print square(5).", "expected": "25", "validate": lambda self, c, o: o.strip() == '25'},
                        {"task": "Create lambda function double = lambda x: x*2, print double(10).", "expected": "20", "validate": lambda self, c, o: o.strip() == '20'},
                        {"task": "Create lambda function add_ten = lambda x: x+10, print add_ten(5).", "expected": "15", "validate": lambda self, c, o: o.strip() == '15'},
                        {"task": "Create lambda function is_even = lambda x: x%2==0, print is_even(4).", "expected": "True", "validate": lambda self, c, o: o.strip() == 'True'},
                        {"task": "Create lambda function concat = lambda a,b: a+b, print concat('hi','ya').", "expected": "hiya", "validate": lambda self, c, o: o.strip() == 'hiya'},
                        {"task": "Create lambda function get_length = lambda s: len(s), print get_length('lambda').", "expected": "6", "validate": lambda self, c, o: o.strip() == '6'}
                    ],
                    "hint": "Define the lambda using the syntax 'lambda parameter: expression' and call it passing the argument.",
                    "starter_code": "# Define lambda and print call here\n"
                },
                {
                    "title": "Lesson 10.4: Map Function",
                    "concept": "The map() function applies a function to all items in an input list. Wrap it in list() to view the results.",
                    "concept_example": "res = list(map(lambda x: x+1, [1, 2])) # [2, 3]",
                    "variants": [
                        {"task": "Use map() to double numbers in [1, 2, 3, 4], print result as list.", "expected": "[2, 4, 6, 8]", "validate": lambda self, c, o: o.strip() == '[2, 4, 6, 8]'},
                        {"task": "Use map() to add 5 to numbers in [10, 20, 30], print result as list.", "expected": "[15, 25, 35]", "validate": lambda self, c, o: o.strip() == '[15, 25, 35]'},
                        {"task": "Use map() to calculate lengths of ['hi', 'hello', 'hola'], print result as list.", "expected": "[2, 5, 4]", "validate": lambda self, c, o: o.strip() == '[2, 5, 4]'},
                        {"task": "Use map() to square numbers in [2, 3, 4], print result as list.", "expected": "[4, 9, 16]", "validate": lambda self, c, o: o.strip() == '[4, 9, 16]'},
                        {"task": "Use map() to convert list of ints [1, 2] to strings list, print result as list.", "expected": "['1', '2']", "validate": lambda self, c, o: "'1'" in o and "'2'" in o},
                        {"task": "Use map() to subtract 1 from numbers in [5, 10], print result as list.", "expected": "[4, 9]", "validate": lambda self, c, o: o.strip() == '[4, 9]'}
                    ],
                    "hint": "Pass a lambda and the list to map(), then wrap the map object in list() inside print().",
                    "starter_code": "# Use map and print result here\n"
                },
                {
                    "title": "Lesson 10.5: File Operations",
                    "concept": "Use open() to open a file with mode 'w' for writing. Write text using file.write() and call file.close() to finish. Or use the 'with' block.",
                    "concept_example": "with open(\"test.txt\", \"w\") as f:\n    f.write(\"content\")",
                    "variants": [
                        {"task": "Write code to open file 'test.txt' for writing, write 'Hello File', then close it. (Just write the code)", "expected": "", "validate": lambda self, c, o: 'open' in c and 'write' in c.lower()},
                        {"task": "Write code to open file 'data.txt' for writing, write 'Python Data', then close it. (Just write the code)", "expected": "", "validate": lambda self, c, o: 'open' in c and 'write' in c.lower()},
                        {"task": "Write code to open file 'notes.txt' for writing, write 'Notes', then close it. (Just write the code)", "expected": "", "validate": lambda self, c, o: 'open' in c and 'write' in c.lower()},
                        {"task": "Write code to open file 'log.txt' for writing, write 'LogEntry', then close it. (Just write the code)", "expected": "", "validate": lambda self, c, o: 'open' in c and 'write' in c.lower()},
                        {"task": "Write code to open file 'output.txt' for writing, write 'Output', then close it. (Just write the code)", "expected": "", "validate": lambda self, c, o: 'open' in c and 'write' in c.lower()},
                        {"task": "Write code to open file 'todo.txt' for writing, write 'Task1', then close it. (Just write the code)", "expected": "", "validate": lambda self, c, o: 'open' in c and 'write' in c.lower()}
                    ],
                    "hint": "Open with 'w' write mode, write to the file handler, and execute close() at the end to save.",
                    "starter_code": "# Write file operation code here\n"
                }
            ]
        }

        ch_list = [ch1, ch2, ch3, ch4, ch5, ch6, ch7, ch8, ch9, ch10]
        
        # Verify self.lesson_indices exists and is correct size, if not initialize it
        if not hasattr(self, 'lesson_indices') or len(self.lesson_indices) != 50:
            self.lesson_indices = [random.randint(0, 5) for _ in range(50)]
            
        chapters = []
        slot_idx = 0
        for ch in ch_list:
            chapter_lessons = []
            for lesson_data in ch['lessons']:
                var_idx = self.lesson_indices[slot_idx]
                # Fallback if index out of bounds
                if var_idx < 0 or var_idx >= len(lesson_data['variants']):
                    var_idx = 0
                variant = lesson_data['variants'][var_idx]
                
                # Combine Concept, Example and Task in Description
                desc = f"Concept:\n{lesson_data['concept']}\n\nExample:\n{lesson_data['concept_example']}\n\nChallenge:\n{variant['task']}"
                
                expected_str = ""
                if variant['expected']:
                    expected_str = f"Expected output:\n{variant['expected']}"
                
                lesson = {
                    "title": lesson_data['title'],
                    "description": desc,
                    "example": expected_str,
                    "hint": lesson_data['hint'],
                    "starter_code": lesson_data['starter_code'],
                    "validate": variant['validate']
                }
                chapter_lessons.append(lesson)
                slot_idx += 1
            
            chapters.append({
                "title": ch['title'],
                "lessons": chapter_lessons
            })
            
        return chapters
    
    def save_progress(self):
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_progress.json")
        try:
            data = {
                "score": self.score,
                "current_chapter": self.current_chapter,
                "current_lesson": self.current_lesson,
                "streak": self.streak,
                "lesson_indices": self.lesson_indices
            }
            with open(save_path, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving progress: {e}")

    def load_progress(self):
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_progress.json")
        if os.path.exists(save_path):
            try:
                with open(save_path, "r") as f:
                    data = json.load(f)
                self.score = data.get("score", 0)
                self.current_chapter = data.get("current_chapter", 0)
                self.current_lesson = data.get("current_lesson", 0)
                self.streak = data.get("streak", 0)
                self.lesson_indices = data.get("lesson_indices", [random.randint(0, 5) for _ in range(50)])
                self.chapters = self.load_chapters()
                self.total_lessons = sum(len(chapter['lessons']) for chapter in self.chapters)
                return True
            except Exception as e:
                print(f"Error loading progress: {e}")
        return False

    def continue_game(self):
        if self.load_progress():
            self.update_stats()
            self.show_lesson()
        else:
            self.start_game()

    def confirm_start_new(self):
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_progress.json")
        if os.path.exists(save_path):
            confirm = messagebox.askyesno(
                "Confirm Restart",
                "Starting a new game will overwrite your saved progress. Do you want to continue?",
                icon='warning'
            )
            if not confirm:
                return
            try:
                os.remove(save_path)
            except Exception:
                pass
        self.start_game()

    def on_exit(self):
        self.save_progress()
        self.root.destroy()
    
    def show_welcome(self):
        # Clear game content
        for widget in self.game_content.winfo_children():
            widget.destroy()
        
        welcome_text = """🎮 Welcome to Python Coding Challenge! 🐍

📚 Learn Python by WRITING actual code!

🎯 How it works:
   • Each level gives you a coding challenge
   • Write Python code in the editor
   • Click 'Run Code' to test your solution
   • Get instant feedback on your code
   • Earn points and build your streak!

💡 Features:
   • 10 progressive levels (easy to advanced)
   • Real Python code execution
   • Hints available if you get stuck
   • Track your score and streak
   • Learn by doing!

🚀 Ready to code? Let's start!
"""
        
        welcome_label = tk.Label(
            self.game_content,
            text=welcome_text,
            font=("Consolas", 12),
            fg="#d4d4d4",
            bg="#1e1e1e",
            justify=tk.LEFT
        )
        welcome_label.pack(pady=40, padx=20, anchor=tk.W)
        
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_progress.json")
        if os.path.exists(save_path):
            btn_frame = tk.Frame(self.game_content, bg="#1e1e1e")
            btn_frame.pack(pady=20)
            
            continue_btn = tk.Button(
                btn_frame,
                text="▶ Continue Game",
                command=self.continue_game,
                font=("Consolas", 14, "bold"),
                bg="#28a745",
                fg="white",
                activebackground="#2eb855",
                cursor="hand2",
                padx=30,
                pady=12
            )
            continue_btn.pack(side=tk.LEFT, padx=10)
            
            new_game_btn = tk.Button(
                btn_frame,
                text="➕ Start New Game",
                command=self.confirm_start_new,
                font=("Consolas", 14, "bold"),
                bg="#0e639c",
                fg="white",
                activebackground="#1177bb",
                cursor="hand2",
                padx=30,
                pady=12
            )
            new_game_btn.pack(side=tk.LEFT, padx=10)
        else:
            start_btn = tk.Button(
                self.game_content,
                text="▶ Start Coding!",
                command=self.start_game,
                font=("Consolas", 14, "bold"),
                bg="#0e639c",
                fg="white",
                activebackground="#1177bb",
                cursor="hand2",
                padx=40,
                pady=12
            )
            start_btn.pack(pady=20)
    
    def start_game(self):
        self.score = 0
        self.current_chapter = 0
        self.current_lesson = 0
        self.streak = 0
        self.lesson_indices = [random.randint(0, 5) for _ in range(50)]
        self.chapters = self.load_chapters()
        self.total_lessons = sum(len(chapter['lessons']) for chapter in self.chapters)
        self.update_stats()
        self.save_progress()
        self.show_lesson()
    
    def clear_editor(self):
        if hasattr(self, 'code_input'):
            self.code_input.delete(1.0, tk.END)
        if hasattr(self, 'output_text'):
            self.set_output("")
    
    def show_lesson(self):
        if self.current_chapter >= len(self.chapters):
            self.show_results()
            return
        
        chapter = self.chapters[self.current_chapter]
        if self.current_lesson >= len(chapter['lessons']):
            self.current_chapter += 1
            self.current_lesson = 0
            if self.current_chapter >= len(self.chapters):
                self.show_results()
                return
            chapter = self.chapters[self.current_chapter]
        
        lesson = chapter['lessons'][self.current_lesson]
        
        # Clear and rebuild game content
        for widget in self.game_content.winfo_children():
            widget.destroy()
        
        # Chapter title
        tk.Label(
            self.game_content,
            text=chapter['title'],
            font=("Consolas", 14, "bold"),
            fg="#dcdcaa",
            bg="#1e1e1e"
        ).pack(pady=(5, 3))
        
        # Challenge frame
        self.challenge_frame = tk.Frame(self.game_content, bg="#252526")
        self.challenge_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Lesson title and description
        self.desc_label = tk.Label(
            self.challenge_frame,
            text=f"{lesson['title']}\n\n{lesson['description']}",
            font=("Consolas", 13),
            fg="#d4d4d4",
            bg="#252526",
            wraplength=950,
            justify=tk.LEFT
        )
        self.desc_label.pack(padx=15, pady=10, anchor=tk.W)
        
        # Example section
        self.example_label = tk.Label(
            self.challenge_frame,
            text=lesson['example'],
            font=("Consolas", 11),
            fg="#808080",
            bg="#252526",
            wraplength=950,
            justify=tk.LEFT
        )
        self.example_label.pack(padx=15, pady=5, anchor=tk.W)
        
        # Code editor frame
        self.editor_frame = tk.Frame(self.game_content, bg="#1e1e1e")
        self.editor_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            self.editor_frame,
            text="💻 Your Code:",
            font=("Consolas", 11, "bold"),
            fg="#4ec9b0",
            bg="#1e1e1e"
        ).pack(anchor=tk.W, pady=(5, 5))
        
        # Code input
        self.code_input = scrolledtext.ScrolledText(
            self.editor_frame,
            height=12,
            font=("Consolas", 12),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#00ff00",
            selectbackground="#264f78",
            relief=tk.FLAT,
            highlightthickness=2,
            highlightbackground="#007acc"
        )
        self.code_input.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.code_input.insert(1.0, lesson['starter_code'])
        
        # Button frame
        self.btn_frame = tk.Frame(self.game_content, bg="#1e1e1e")
        self.btn_frame.pack(fill=tk.X)
        
        self.run_btn = tk.Button(
            self.btn_frame,
            text="▶ Run Code",
            command=self.run_code,
            font=("Consolas", 12, "bold"),
            bg="#0e639c",
            fg="white",
            activebackground="#1177bb",
            cursor="hand2",
            padx=30,
            pady=8
        )
        self.run_btn.pack(side=tk.LEFT, padx=5)
        
        self.hint_btn = tk.Button(
            self.btn_frame,
            text="💡 Hint",
            command=self.show_hint,
            font=("Consolas", 12),
            bg="#6b3fa0",
            fg="white",
            activebackground="#7b4fb0",
            cursor="hand2",
            padx=20,
            pady=8
        )
        self.hint_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = tk.Button(
            self.btn_frame,
            text="🔄 Reset",
            command=self.reset_code,
            font=("Consolas", 12),
            bg="#555555",
            fg="white",
            activebackground="#666666",
            cursor="hand2",
            padx=20,
            pady=8
        )
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = tk.Button(
            self.btn_frame,
            text="Next Lesson →",
            command=self.next_lesson,
            font=("Consolas", 12, "bold"),
            bg="#28a745",
            fg="white",
            activebackground="#2eb855",
            cursor="hand2",
            padx=30,
            pady=8
        )
        self.next_btn.pack(side=tk.RIGHT, padx=5)
        self.next_btn.pack_forget()
        
        # Output frame
        tk.Label(
            self.game_content,
            text="📤 Output:",
            font=("Consolas", 11, "bold"),
            fg="#4ec9b0",
            bg="#1e1e1e"
        ).pack(anchor=tk.W, pady=(5, 3))
        
        self.output_text = scrolledtext.ScrolledText(
            self.game_content,
            height=5,
            font=("Consolas", 11),
            bg="#000000",
            fg="#00ff00",
            state=tk.DISABLED,
            relief=tk.FLAT
        )
        self.output_text.pack(fill=tk.X, pady=(0, 5))
        
        self.update_stats()
    
    def set_output(self, text):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(1.0, text)
        self.output_text.config(state=tk.DISABLED)
    
    def run_code(self):
        user_code = self.code_input.get(1.0, tk.END).strip()
        
        if not user_code or user_code.startswith('#'):
            self.set_output("⚠️ Please write some code first!")
            return
        
        # Capture output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        
        try:
            # Execute user code
            exec(user_code, {'__builtins__': __builtins__})
            output = sys.stdout.getvalue()
            error = sys.stderr.getvalue()
            
            if error:
                self.set_output(f"❌ Error:\n{error}")
            else:
                self.set_output(f"✅ Output:\n{output}")
                # Validate the solution
                self.validate_solution(user_code, output)
        except Exception as e:
            self.set_output(f"❌ Error:\n{str(e)}")
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    def validate_solution(self, user_code, output):
        chapter = self.chapters[self.current_chapter]
        lesson = chapter['lessons'][self.current_lesson]
        is_correct = lesson['validate'](self, user_code, output)
        
        if is_correct:
            self.score += 100 + (self.streak * 10)
            self.streak += 1
            self.set_output(self.output_text.get(1.0, tk.END).strip() + 
                          f"\n\n🎉 CORRECT! +{100 + (self.streak - 1) * 10} points")
            self.run_btn.config(state=tk.DISABLED)
            self.hint_btn.config(state=tk.DISABLED)
            self.next_btn.pack(side=tk.RIGHT, padx=5)
            self.update_stats()
            self.save_progress()
        else:
            self.streak = 0
            self.set_output(self.output_text.get(1.0, tk.END).strip() + 
                          f"\n\n❌ Not quite right. Check the hint and try again!")
            self.update_stats()
            self.save_progress()
    
    def show_hint(self):
        chapter = self.chapters[self.current_chapter]
        lesson = chapter['lessons'][self.current_lesson]
        self.set_output(f"💡 Hint:\n{lesson['hint']}")
        self.score = max(0, self.score - 5)  # Small penalty for using hints
        self.update_stats()
    
    def reset_code(self):
        chapter = self.chapters[self.current_chapter]
        lesson = chapter['lessons'][self.current_lesson]
        self.code_input.delete(1.0, tk.END)
        self.code_input.insert(1.0, lesson['starter_code'])
        self.set_output("")
    
    def next_lesson(self):
        self.current_lesson += 1
        chapter = self.chapters[self.current_chapter]
        if self.current_lesson >= len(chapter['lessons']):
            self.current_chapter += 1
            self.current_lesson = 0
        self.show_lesson()
    
    def update_stats(self):
        completed_lessons = self.current_chapter * 5 + self.current_lesson
        self.score_label.config(text=f"⭐ Score: {self.score}")
        self.chapter_label.config(text=f"📚 Chapter: {self.current_chapter + 1}/{len(self.chapters)} | Lesson: {self.current_lesson + 1}/5")
        self.streak_label.config(text=f"🔥 Streak: {self.streak}")
    
    def show_results(self):
        self.clear_editor()
        
        max_score = self.total_lessons * 100
        percentage = (self.score / max_score * 100) if max_score > 0 else 0
        
        grade = ""
        if percentage >= 90:
            grade = "🌟 Python Master! Excellent!"
        elif percentage >= 70:
            grade = "👍 Great Job! Keep Coding!"
        elif percentage >= 50:
            grade = "💪 Good Progress! Practice More!"
        else:
            grade = "📚 Keep Learning! You're Getting Better!"
        
        results_text = f"""🎉 Congratulations! {grade}

📊 Final Score: {self.score} points
🎯 Lessons Completed: {self.total_lessons}/{self.total_lessons}
📚 Chapters Completed: {len(self.chapters)}/{len(self.chapters)}

✅ You've completed all coding challenges!
🔥 You wrote real Python code and learned by doing!

🚀 Keep practicing to become a Python expert!"""
        
        # Clear game content
        for widget in self.game_content.winfo_children():
            widget.destroy()
        
        results_label = tk.Label(
            self.game_content,
            text=results_text,
            font=("Consolas", 14, "bold"),
            fg="#4ec9b0",
            bg="#1e1e1e",
            justify=tk.LEFT
        )
        results_label.pack(pady=60, padx=20, anchor=tk.W)
        
        btn_frame = tk.Frame(self.game_content, bg="#1e1e1e")
        btn_frame.pack(pady=20)
        
        restart_btn = tk.Button(
            btn_frame,
            text="🔄 Play Again",
            command=self.start_game,
            font=("Consolas", 12, "bold"),
            bg="#0e639c",
            fg="white",
            activebackground="#1177bb",
            cursor="hand2",
            padx=30,
            pady=10
        )
        restart_btn.pack(side=tk.LEFT, padx=10)
        
        quit_btn = tk.Button(
            btn_frame,
            text="👋 Quit",
            command=self.on_exit,
            font=("Consolas", 12),
            bg="#555555",
            fg="white",
            activebackground="#666666",
            cursor="hand2",
            padx=30,
            pady=10
        )
        quit_btn.pack(side=tk.LEFT, padx=10)

if __name__ == "__main__":
    root = tk.Tk()
    game = PythonLearningGame(root)
    root.mainloop()
