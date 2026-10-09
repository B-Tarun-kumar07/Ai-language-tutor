# 🌸 AI Language Tutor — Japanese Learning Assistant

An AI-powered Japanese learning application designed to make learning Japanese easier through grammar explanations, vocabulary analysis, quizzes, and interactive study tools.

## ✨ Features

- **Japanese Sentence Analysis** — Analyze Japanese sentences and understand their structure.
- **Grammar Explanations** — Learn how Japanese grammar works with clear explanations.
- **Vocabulary Learning** — Explore vocabulary and understand words in context.
- **Interactive Quizzes** — Test your understanding and reinforce what you've learned.
- **Flashcards** — Review vocabulary and strengthen your memory.
- **Learning Progress** — Support a more structured and consistent learning experience.

## 🛠️ Tech Stack

**Frontend**
- React
- Vite
- JavaScript
- CSS

**Backend**
- Python
- FastAPI
- SQLite

**AI / Language Processing**
- Ollama (local LLM support)
- Japanese language analysis

## 📁 Project Structure

```text
ai-language-tutor/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── japanese_analyzer.py
│   ├── vocabulary.py
│   ├── vocabulary_db.py
│   └── test_japanese.py
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

## 🚀 Getting Started

### Prerequisites

Install the following before running the application:

- Python 3.12
- Node.js and npm
- Ollama, if using the local AI features

### 1. Clone the repository

```bash
git clone https://github.com/B-Tarun-kumar07/Ai-language-tutor.git
cd Ai-language-tutor
```

### 2. Set up the backend

Create and activate a Python virtual environment.

**Windows PowerShell:**

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the backend dependencies listed in your project's requirements file, then start the FastAPI server:

```powershell
uvicorn main:app --reload
```

The API documentation is typically available at:

http://127.0.0.1:8000/docs

### 3. Set up the frontend

Open a second terminal from the project root:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL displayed by Vite in your terminal.

### 4. Configure local AI (if required)

If your application uses Ollama, install Ollama and download the model configured in your backend. Ensure the model name and connection settings match your application configuration.

## 🎯 Project Goal

The goal of this project is to build an interactive Japanese learning assistant that helps learners understand sentences, build vocabulary, practice grammar, and study more effectively.

## 🔮 Future Improvements

- Voice-based pronunciation and speaking practice
- More interactive conversation exercises
- JLPT-level-based learning
- Improved learning analytics and progress tracking
- Additional study and revision tools

## 👨‍💻 Author

**B. Tarun Kumar**

Developed as a personal project combining language learning, AI, and web development.

---

⭐ If you find this project interesting, consider giving the repository a star!