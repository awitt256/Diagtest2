import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import random
import sys
import io
import re

class PythonLearningGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Learning Game - Hands-On Coding")
        self.root.geometry("1000x700")
        self.root.configure(bg="#1e1e1e")
        
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
        return [
            {
                "title": "Chapter 1: Python Basics",
                "lessons": [
                    {
                        "title": "Lesson 1.1: Hello World",
                        "description": "Write your first Python program that prints 'Hello, World!' to the screen.",
                        "example": "Expected output:\nHello, World!",
                        "hint": "Use the print() function: print('text')",
                        "starter_code": "# Write your first Python program\n",
                        "validate": lambda self, code, output: 'hello, world!' in output.lower()
                    },
                    {
                        "title": "Lesson 1.2: Print Your Name",
                        "description": "Print your name (replace 'Your Name' with your actual name).",
                        "example": "Example output:\nJohn",
                        "hint": "print('Your Name')",
                        "starter_code": "# Print your name\n",
                        "validate": lambda self, code, output: len(output.strip()) > 0
                    },
                    {
                        "title": "Lesson 1.3: Multiple Prints",
                        "description": "Print two lines: first line 'Python' and second line 'is fun!'",
                        "example": "Expected output:\nPython\nis fun!",
                        "hint": "Use two print() statements",
                        "starter_code": "# Print two lines\n",
                        "validate": lambda self, code, output: 'python' in output.lower() and 'is fun!' in output.lower()
                    },
                    {
                        "title": "Lesson 1.4: Print Numbers",
                        "description": "Print the number 42.",
                        "example": "Expected output:\n42",
                        "hint": "You can print numbers without quotes: print(42)",
                        "starter_code": "# Print the number 42\n",
                        "validate": lambda self, code, output: output.strip() == '42'
                    },
                    {
                        "title": "Lesson 1.5: Print a Message",
                        "description": "Print 'I am learning Python!' to the screen.",
                        "example": "Expected output:\nI am learning Python!",
                        "hint": "print('I am learning Python!')",
                        "starter_code": "# Print the message\n",
                        "validate": lambda self, code, output: 'i am learning python!' in output.lower()
                    }
                ]
            },
            {
                "title": "Chapter 2: Variables & Data Types",
                "lessons": [
                    {
                        "title": "Lesson 2.1: Create a Variable",
                        "description": "Create a variable called 'name' and assign it the value 'Alice', then print it.",
                        "example": "Expected output:\nAlice",
                        "hint": "name = 'Alice' then print(name)",
                        "starter_code": "# Create variable and print it\n",
                        "validate": lambda self, code, output: 'alice' in output.lower()
                    },
                    {
                        "title": "Lesson 2.2: Integer Variable",
                        "description": "Create a variable 'age' with value 25, then print it.",
                        "example": "Expected output:\n25",
                        "hint": "age = 25, then print(age)",
                        "starter_code": "# Create integer variable\n",
                        "validate": lambda self, code, output: output.strip() == '25'
                    },
                    {
                        "title": "Lesson 2.3: Float Variable",
                        "description": "Create a variable 'price' with value 19.99 and print it.",
                        "example": "Expected output:\n19.99",
                        "hint": "price = 19.99, then print(price)",
                        "starter_code": "# Create float variable\n",
                        "validate": lambda self, code, output: '19.99' in output
                    },
                    {
                        "title": "Lesson 2.4: Multiple Variables",
                        "description": "Create variables x = 10 and y = 5, then print both on separate lines.",
                        "example": "Expected output:\n10\n5",
                        "hint": "x = 10, y = 5, print(x), print(y)",
                        "starter_code": "# Create and print multiple variables\n",
                        "validate": lambda self, code, output: '10' in output and '5' in output
                    },
                    {
                        "title": "Lesson 2.5: Type Check",
                        "description": "Create variable message = 'Hello', then print its type using type(message).",
                        "example": "Expected output:\n<class 'str'>",
                        "hint": "Use type() function: print(type(message))",
                        "starter_code": "message = 'Hello'\n# Print the type\n",
                        "validate": lambda self, code, output: 'str' in output
                    }
                ]
            },
            {
                "title": "Chapter 3: Basic Operations",
                "lessons": [
                    {
                        "title": "Lesson 3.1: Addition",
                        "description": "Print the result of 15 + 27.",
                        "example": "Expected output:\n42",
                        "hint": "print(15 + 27)",
                        "starter_code": "# Print the sum\n",
                        "validate": lambda self, code, output: output.strip() == '42'
                    },
                    {
                        "title": "Lesson 3.2: Subtraction",
                        "description": "Print the result of 100 - 37.",
                        "example": "Expected output:\n63",
                        "hint": "print(100 - 37)",
                        "starter_code": "# Print the difference\n",
                        "validate": lambda self, code, output: output.strip() == '63'
                    },
                    {
                        "title": "Lesson 3.3: Multiplication",
                        "description": "Print the result of 8 * 7.",
                        "example": "Expected output:\n56",
                        "hint": "print(8 * 7)",
                        "starter_code": "# Print the product\n",
                        "validate": lambda self, code, output: output.strip() == '56'
                    },
                    {
                        "title": "Lesson 3.4: Division",
                        "description": "Print the result of 100 / 4.",
                        "example": "Expected output:\n25.0",
                        "hint": "print(100 / 4)",
                        "starter_code": "# Print the quotient\n",
                        "validate": lambda self, code, output: '25.0' in output or output.strip() == '25'
                    },
                    {
                        "title": "Lesson 3.5: Complex Math",
                        "description": "Calculate and print: (10 + 5) * 3 - 15",
                        "example": "Expected output:\n30",
                        "hint": "print((10 + 5) * 3 - 15)",
                        "starter_code": "# Calculate complex expression\n",
                        "validate": lambda self, code, output: output.strip() == '30'
                    }
                ]
            },
            {
                "title": "Chapter 4: String Operations",
                "lessons": [
                    {
                        "title": "Lesson 4.1: String Concatenation",
                        "description": "Create variables first = 'Python' and last = 'Programming', then print them concatenated.",
                        "example": "Expected output:\nPythonProgramming",
                        "hint": "Use + operator: print(first + last)",
                        "starter_code": "first = 'Python'\nlast = 'Programming'\n# Print concatenation\n",
                        "validate": lambda self, code, output: 'pythonprogramming' in output.lower()
                    },
                    {
                        "title": "Lesson 4.2: String Length",
                        "description": "Print the length of the string 'Hello World' using len().",
                        "example": "Expected output:\n11",
                        "hint": "print(len('Hello World'))",
                        "starter_code": "# Print string length\n",
                        "validate": lambda self, code, output: output.strip() == '11'
                    },
                    {
                        "title": "Lesson 4.3: Uppercase",
                        "description": "Convert 'python' to uppercase and print it.",
                        "example": "Expected output:\nPYTHON",
                        "hint": "Use .upper() method: 'python'.upper()",
                        "starter_code": "# Convert to uppercase\n",
                        "validate": lambda self, code, output: output.strip() == 'PYTHON'
                    },
                    {
                        "title": "Lesson 4.4: Lowercase",
                        "description": "Convert 'PYTHON' to lowercase and print it.",
                        "example": "Expected output:\npython",
                        "hint": "Use .lower() method: 'PYTHON'.lower()",
                        "starter_code": "# Convert to lowercase\n",
                        "validate": lambda self, code, output: output.strip() == 'python'
                    },
                    {
                        "title": "Lesson 4.5: String Slicing",
                        "description": "Print the first 3 characters of 'Python'.",
                        "example": "Expected output:\nPyt",
                        "hint": "Use slicing: 'Python'[:3]",
                        "starter_code": "# Print first 3 characters\n",
                        "validate": lambda self, code, output: output.strip() == 'Pyt'
                    }
                ]
            },
            {
                "title": "Chapter 5: Lists",
                "lessons": [
                    {
                        "title": "Lesson 5.1: Create a List",
                        "description": "Create a list called 'fruits' with 'apple', 'banana', 'cherry', then print it.",
                        "example": "Expected output:\n['apple', 'banana', 'cherry']",
                        "hint": "fruits = ['apple', 'banana', 'cherry']",
                        "starter_code": "# Create the list\n# Print it\n",
                        "validate": lambda self, code, output: 'apple' in output and 'banana' in output and 'cherry' in output
                    },
                    {
                        "title": "Lesson 5.2: Access List Item",
                        "description": "Create list numbers = [10, 20, 30, 40, 50], then print the first item.",
                        "example": "Expected output:\n10",
                        "hint": "Access with index: print(numbers[0])",
                        "starter_code": "numbers = [10, 20, 30, 40, 50]\n# Print first item\n",
                        "validate": lambda self, code, output: output.strip() == '10'
                    },
                    {
                        "title": "Lesson 5.3: List Length",
                        "description": "Create list colors = ['red', 'green', 'blue'] and print its length.",
                        "example": "Expected output:\n3",
                        "hint": "Use len(): print(len(colors))",
                        "starter_code": "colors = ['red', 'green', 'blue']\n# Print length\n",
                        "validate": lambda self, code, output: output.strip() == '3'
                    },
                    {
                        "title": "Lesson 5.4: Add to List",
                        "description": "Create list nums = [1, 2, 3], append 4 to it, then print the list.",
                        "example": "Expected output:\n[1, 2, 3, 4]",
                        "hint": "Use .append(): nums.append(4)",
                        "starter_code": "nums = [1, 2, 3]\n# Add 4 to the list\n# Print the list\n",
                        "validate": lambda self, code, output: '1' in output and '2' in output and '3' in output and '4' in output
                    },
                    {
                        "title": "Lesson 5.5: List Slicing",
                        "description": "Create list numbers = [0, 1, 2, 3, 4, 5], print the first 3 items.",
                        "example": "Expected output:\n[0, 1, 2]",
                        "hint": "Use slicing: print(numbers[:3])",
                        "starter_code": "numbers = [0, 1, 2, 3, 4, 5]\n# Print first 3 items\n",
                        "validate": lambda self, code, output: output.strip() == '[0, 1, 2]'
                    }
                ]
            },
            {
                "title": "Chapter 6: Conditional Statements",
                "lessons": [
                    {
                        "title": "Lesson 6.1: Basic If",
                        "description": "Create variable age = 20. If age >= 18, print 'Adult'.",
                        "example": "Expected output:\nAdult",
                        "hint": "if age >= 18: print('Adult')",
                        "starter_code": "age = 20\n# Write if statement\n",
                        "validate": lambda self, code, output: output.strip() == 'Adult'
                    },
                    {
                        "title": "Lesson 6.2: If-Else",
                        "description": "Create variable score = 75. If score >= 60 print 'Pass', else print 'Fail'.",
                        "example": "Expected output:\nPass",
                        "hint": "Use if-else statement",
                        "starter_code": "score = 75\n# Write if-else\n",
                        "validate": lambda self, code, output: output.strip() == 'Pass'
                    },
                    {
                        "title": "Lesson 6.3: Elif",
                        "description": "Create variable grade = 85. Print 'A' if >= 90, 'B' if >= 80, 'C' otherwise.",
                        "example": "Expected output:\nB",
                        "hint": "Use if-elif-else chain",
                        "starter_code": "grade = 85\n# Write if-elif-else\n",
                        "validate": lambda self, code, output: output.strip() == 'B'
                    },
                    {
                        "title": "Lesson 6.4: Multiple Conditions",
                        "description": "Create x = 10. Print 'Valid' if x > 5 and x < 15, else print 'Invalid'.",
                        "example": "Expected output:\nValid",
                        "hint": "Use 'and' operator: if x > 5 and x < 15:",
                        "starter_code": "x = 10\n# Check multiple conditions\n",
                        "validate": lambda self, code, output: output.strip() == 'Valid'
                    },
                    {
                        "title": "Lesson 6.5: Nested If",
                        "description": "Create num = 15. If num > 10, check if num < 20 and print 'Between 10 and 20'.",
                        "example": "Expected output:\nBetween 10 and 20",
                        "hint": "Nest one if inside another",
                        "starter_code": "num = 15\n# Write nested if\n",
                        "validate": lambda self, code, output: 'between 10 and 20' in output.lower()
                    }
                ]
            },
            {
                "title": "Chapter 7: Loops",
                "lessons": [
                    {
                        "title": "Lesson 7.1: For Loop Range",
                        "description": "Use a for loop to print numbers 1 to 5.",
                        "example": "Expected output:\n1\n2\n3\n4\n5",
                        "hint": "for i in range(1, 6): print(i)",
                        "starter_code": "# Use for loop to print 1-5\n",
                        "validate": lambda self, code, output: output.strip() == '1\n2\n3\n4\n5'
                    },
                    {
                        "title": "Lesson 7.2: For Loop List",
                        "description": "Create list fruits = ['apple', 'banana', 'cherry'], use for loop to print each fruit.",
                        "example": "Expected output:\napple\nbanana\ncherry",
                        "hint": "for fruit in fruits: print(fruit)",
                        "starter_code": "fruits = ['apple', 'banana', 'cherry']\n# Use for loop\n",
                        "validate": lambda self, code, output: 'apple' in output and 'banana' in output and 'cherry' in output
                    },
                    {
                        "title": "Lesson 7.3: While Loop",
                        "description": "Use a while loop to print numbers 0, 1, 2.",
                        "example": "Expected output:\n0\n1\n2",
                        "hint": "i = 0, while i < 3: print(i), i += 1",
                        "starter_code": "# Use while loop\n",
                        "validate": lambda self, code, output: output.strip() == '0\n1\n2'
                    },
                    {
                        "title": "Lesson 7.4: Break Statement",
                        "description": "Use a for loop with range(1, 10), break when i equals 5. Print each number.",
                        "example": "Expected output:\n1\n2\n3\n4",
                        "hint": "Use 'if i == 5: break'",
                        "starter_code": "# Use for loop with break\n",
                        "validate": lambda self, code, output: output.strip() == '1\n2\n3\n4'
                    },
                    {
                        "title": "Lesson 7.5: Sum with Loop",
                        "description": "Use a for loop to calculate and print the sum of numbers 1 to 10.",
                        "example": "Expected output:\n55",
                        "hint": "total = 0, for i in range(1, 11): total += i, print(total)",
                        "starter_code": "# Calculate sum using loop\n",
                        "validate": lambda self, code, output: output.strip() == '55'
                    }
                ]
            },
            {
                "title": "Chapter 8: Dictionaries",
                "lessons": [
                    {
                        "title": "Lesson 8.1: Create Dictionary",
                        "description": "Create dict person = {'name': 'John', 'age': 30}, then print it.",
                        "example": "Expected output:\n{'name': 'John', 'age': 30}",
                        "hint": "person = {'name': 'John', 'age': 30}",
                        "starter_code": "# Create dictionary\n# Print it\n",
                        "validate": lambda self, code, output: 'name' in output and 'John' in output and 'age' in output and '30' in output
                    },
                    {
                        "title": "Lesson 8.2: Access Value",
                        "description": "Create dict student = {'name': 'Alice', 'grade': 'A'}, print the name.",
                        "example": "Expected output:\nAlice",
                        "hint": "Access with key: print(student['name'])",
                        "starter_code": "student = {'name': 'Alice', 'grade': 'A'}\n# Print the name\n",
                        "validate": lambda self, code, output: output.strip() == 'Alice'
                    },
                    {
                        "title": "Lesson 8.3: Add Key-Value",
                        "description": "Create dict car = {'brand': 'Toyota'}, add key 'year' with value 2023, print dict.",
                        "example": "Expected output:\n{'brand': 'Toyota', 'year': 2023}",
                        "hint": "car['year'] = 2023",
                        "starter_code": "car = {'brand': 'Toyota'}\n# Add year\n# Print dict\n",
                        "validate": lambda self, code, output: 'Toyota' in output and '2023' in output
                    },
                    {
                        "title": "Lesson 8.4: Dictionary Keys",
                        "description": "Create dict book = {'title': 'Python', 'pages': 300}, print all keys.",
                        "example": "Expected output:\ndict_keys(['title', 'pages'])",
                        "hint": "Use .keys() method: print(book.keys())",
                        "starter_code": "book = {'title': 'Python', 'pages': 300}\n# Print keys\n",
                        "validate": lambda self, code, output: 'title' in output and 'pages' in output
                    },
                    {
                        "title": "Lesson 8.5: Iterate Dictionary",
                        "description": "Create dict scores = {'math': 90, 'english': 85}, print each key and value.",
                        "example": "Example output:\nmath 90\nenglish 85",
                        "hint": "for key, value in scores.items(): print(key, value)",
                        "starter_code": "scores = {'math': 90, 'english': 85}\n# Iterate and print\n",
                        "validate": lambda self, code, output: 'math' in output and '90' in output and 'english' in output and '85' in output
                    }
                ]
            },
            {
                "title": "Chapter 9: Functions",
                "lessons": [
                    {
                        "title": "Lesson 9.1: Simple Function",
                        "description": "Define function greet() that prints 'Hello!', then call it.",
                        "example": "Expected output:\nHello!",
                        "hint": "def greet(): print('Hello!'), then greet()",
                        "starter_code": "# Define function\n\n# Call function\n",
                        "validate": lambda self, code, output: 'hello!' in output.lower()
                    },
                    {
                        "title": "Lesson 9.2: Function with Parameter",
                        "description": "Define function say_hello(name) that prints 'Hello, [name]!', call it with 'Bob'.",
                        "example": "Expected output:\nHello, Bob!",
                        "hint": "def say_hello(name): print(f'Hello, {name}!')",
                        "starter_code": "# Define function with parameter\n\n# Call function\n",
                        "validate": lambda self, code, output: 'hello, bob!' in output.lower()
                    },
                    {
                        "title": "Lesson 9.3: Function with Return",
                        "description": "Define function add(a, b) that returns a + b, print add(5, 3).",
                        "example": "Expected output:\n8",
                        "hint": "def add(a, b): return a + b",
                        "starter_code": "# Define function\n\n# Print result\n",
                        "validate": lambda self, code, output: output.strip() == '8'
                    },
                    {
                        "title": "Lesson 9.4: Default Parameter",
                        "description": "Define function power(base, exp=2) that returns base**exp. Print power(3) and power(3, 3).",
                        "example": "Expected output:\n9\n27",
                        "hint": "def power(base, exp=2): return base ** exp",
                        "starter_code": "# Define function with default\n\n# Print results\n",
                        "validate": lambda self, code, output: '9' in output and '27' in output
                    },
                    {
                        "title": "Lesson 9.5: Multiple Returns",
                        "description": "Define function calc(a, b) that returns both sum and difference. Print them.",
                        "example": "Example output:\n15 5 (for a=10, b=5)",
                        "hint": "return a + b, a - b",
                        "starter_code": "# Define function\n\n# Call and print\n",
                        "validate": lambda self, code, output: len(output.strip().split()) >= 2
                    }
                ]
            },
            {
                "title": "Chapter 10: Advanced Concepts",
                "lessons": [
                    {
                        "title": "Lesson 10.1: List Comprehension",
                        "description": "Use list comprehension to create list of squares [1, 4, 9, 16, 25] for numbers 1-5.",
                        "example": "Expected output:\n[1, 4, 9, 16, 25]",
                        "hint": "[x**2 for x in range(1, 6)]",
                        "starter_code": "# Use list comprehension\n# Print result\n",
                        "validate": lambda self, code, output: output.strip() == '[1, 4, 9, 16, 25]'
                    },
                    {
                        "title": "Lesson 10.2: Try-Except",
                        "description": "Use try-except to handle division by zero. Try to print 10/0, catch the error.",
                        "example": "Expected output:\nError occurred (or similar)",
                        "hint": "try: print(10/0) except: print('Error occurred')",
                        "starter_code": "# Use try-except\n",
                        "validate": lambda self, code, output: 'error' in output.lower() or 'exception' in output.lower()
                    },
                    {
                        "title": "Lesson 10.3: Lambda Function",
                        "description": "Create lambda function square = lambda x: x**2, print square(5).",
                        "example": "Expected output:\n25",
                        "hint": "square = lambda x: x**2",
                        "starter_code": "# Create lambda function\n# Print result\n",
                        "validate": lambda self, code, output: output.strip() == '25'
                    },
                    {
                        "title": "Lesson 10.4: Map Function",
                        "description": "Use map() to double each number in [1, 2, 3, 4]. Print the result as a list.",
                        "example": "Expected output:\n[2, 4, 6, 8]",
                        "hint": "list(map(lambda x: x*2, [1, 2, 3, 4]))",
                        "starter_code": "# Use map function\n# Print result\n",
                        "validate": lambda self, code, output: output.strip() == '[2, 4, 6, 8]'
                    },
                    {
                        "title": "Lesson 10.5: File Operations",
                        "description": "Write code to open a file 'test.txt' for writing, write 'Hello File', then close it. (Just write the code)",
                        "example": "No output expected, just write correct code",
                        "hint": "f = open('test.txt', 'w'), f.write('Hello File'), f.close()",
                        "starter_code": "# Write file operation code\n",
                        "validate": lambda self, code, output: 'open' in code and 'write' in code.lower()
                    }
                ]
            }
        ]
    
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
        self.update_stats()
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
        else:
            self.streak = 0
            self.set_output(self.output_text.get(1.0, tk.END).strip() + 
                          f"\n\n❌ Not quite right. Check the hint and try again!")
            self.update_stats()
    
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
            command=self.root.quit,
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
