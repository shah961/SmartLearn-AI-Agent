from flask import Flask, request
from google import genai
import os
import markdown
import re

app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

client = genai.Client(api_key=API_KEY)

# Shared HTML Header to avoid repeating CSS styles
HTML_HEADER = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartLearn AI Agent</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --primary: #38bdf8;
            --primary-hover: #0ea5e9;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .container {
            width: 100%;
            max-width: 600px;
            margin-top: 40px;
            text-align: center;
        }

        h1 {
            color: var(--primary);
            font-size: 2.2rem;
            margin-bottom: 10px;
            font-weight: 800;
        }

        .subtitle {
            color: var(--text-muted);
            font-size: 1rem;
            margin-bottom: 30px;
        }

        /* Form & Input Styles */
        .search-box {
            background: var(--card-bg);
            padding: 25px;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border: 1px solid #334155;
        }

        input[type="text"] {
            width: 100%;
            padding: 14px 18px;
            border-radius: 10px;
            border: 2px solid #334155;
            background-color: #0f172a;
            color: white;
            font-size: 1rem;
            margin-bottom: 15px;
            outline: none;
            transition: border-color 0.2s;
        }
        select {
            width: 100%;
            padding: 14px 18px;
            border-radius: 10px;
            border: 2px solid #334155;
            background-color: #0f172a;
            color: white;
            font-size: 1rem;
            margin-bottom: 15px;
            outline: none;
        }

        select:focus {
            border-color: var(--primary);
        }
        input[type="text"]:focus {
            border-color: var(--primary);
        }

        button {
            width: 100%;
            padding: 14px;
            background-color: var(--primary);
            color: #0f172a;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: background-color 0.2s, transform 0.1s;
        }

        button:hover {
            background-color: var(--primary-hover);
        }

        button:active {
            transform: scale(0.98);
        }

        /* AI Content Formatting (Markdown Output) */
        .content-card {
            background: var(--card-bg);
            padding: 25px;
            border-radius: 16px;
            text-align: left;
            margin-top: 20px;
            border: 1px solid #334155;
            line-height: 1.7;
            word-wrap: break-word;
            overflow-wrap: break-word;
            overflow-x: auto;
        }

        .content-card h1, .content-card h2, .content-card h3 {
            color: var(--primary);
            margin-top: 20px;
            margin-bottom: 10px;
        }

        .content-card p {
            margin-bottom: 15px;
            color: #e2e8f0;
        }

        .content-card ul, .content-card ol {
            margin-left: 20px;
            margin-bottom: 15px;
            color: #e2e8f0;
        }

        .content-card li {
            margin-bottom: 8px;
        }

        /* Code block styling for mobile */
        .content-card pre {
            background: #0f172a;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            margin-bottom: 15px;
            border: 1px solid #334155;
        }

        .content-card code {
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9rem;
        }

        .back-link {
            display: inline-block;
            margin-top: 25px;
            color: var(--primary);
            text-decoration: none;
            font-weight: 500;
        }

        .back-link:hover {
            text-decoration: underline;
        }
        .pdf-btn{
            margin-bottom:15px;
        }

        @media print{
            .pdf-btn,
            .back-link{
                display:none;
            }
        }
        #loading{
            text-align:center;
            margin-top:15px;
            color:#38bdf8;
            font-weight:bold;
        }
        .content-card table{
            width:100%;
            border-collapse:collapse;
            margin:15px 0;
            display: block;
            overflow-x: auto;
        }

        .content-card th,
        .content-card td{
            border:1px solid #334155;
            padding:10px;
        }

        .content-card th{
            background:#0f172a;
        }
        #loading{
            margin-top:20px;
            text-align:center;
        }

        .loader{
            width:60px;
            height:60px;
            border:5px solid #334155;
            border-top:5px solid #38bdf8;
            border-radius:50%;
            margin:auto;
            animation:spin 1s linear infinite;
        }

        .loading-text{
            margin-top:15px;
            color:#38bdf8;
            font-weight:bold;
        }

        .loading-sub{
            margin-top:8px;
            color:#94a3b8;
            font-size:0.9rem;
        }

        @keyframes spin{
            from{
                transform:rotate(0deg);
            }
            to{
                transform:rotate(360deg);
            }
        }
        .flashcard {
            background: transparent;
            width: 100%;
            min-height: 250px;
            margin: 25px 0;
            perspective: 1000px;
            margin: 20px 0;
        }
.flashcard-inner {
    position: relative;
    width: 100%;
    min-height: 220px;
    transition: transform 0.7s;
    transform-style: preserve-3d;
    cursor: pointer;
}

.flashcard.flipped .flashcard-inner {
    transform: rotateY(180deg);
}

.flashcard-front,
.flashcard-back {
    position: absolute;
    inset: 0;
    border-radius: 16px;
    padding: 25px;
    backface-visibility: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
    text-align: center;
    font-size: 1rem;
    line-height: 1.6;
}

.flashcard-front {
    background: #1e293b;
    border: 2px solid #38bdf8;
    overflow-y: auto;
    word-break: break-word;
}

.flashcard-back {
    background: #0ea5e9;
    color: white;
    transform: rotateY(180deg);
    overflow-y: auto;
    word-break: break-word;
}
.study-coach{
    background:#0f172a;
    border:2px solid #38bdf8;
    border-radius:16px;
    padding:20px;
    margin:20px 0;
}

.study-coach h2,
.study-coach h3{
    color:#38bdf8;
}
    </style>
</head>
"""

@app.route("/")
def home():
    return f"""
    {HTML_HEADER}
    <body>
        <div class="container">
            <h1>SmartLearn AI </h1>
            <p class="subtitle">
Learn Faster.
Remember Longer.
Study Smarter.</p>

            <div class="search-box">
                <form action="/ask" method="get">
                    <input
                        type="text"
                        name="question"
                        placeholder="What do you want to learn today?"
                        required
                        autofocus
                    maxlength="100">
                    <select name="subject" required>
    <option value="" disabled selected>Select Subject</option>
    <option value="General">General</option>
    <option value="Programming">Programming</option>
    <option value="Mathematics">Mathematics</option>
    <option value="Physics">Physics</option>
    <option value="Chemistry">Chemistry</option>
    <option value="Biology">Biology</option>
</select>

<br><br>

<select name="difficulty" required>
   <option value="" disabled selected>Select Difficulty</option>
    <option value="Beginner">Beginner</option>
    <option value="Intermediate">Intermediate</option>
    <option value="Advanced">Advanced</option>
</select>

<br><br>

<select name="goal" required>
    <option value="" disabled selected>Select Goal</option>
    <option value="Exam Preparation">Exam Preparation</option>
    <option value="Quick Learning">Quick Learning</option>
    <option value="Interview Prep">Interview Prep</option>
    <option value="Revision">Revision</option>
    <option value="Research Mode">
Research Mode
</option>
</select>

<br><br>
                    <button type="submit" id="askBtn">
    Ask AI Partner
</button>
                </form>
                <div id="loading" style="display:none;">
                    <div class="loader"></div>

                    <p class="loading-text">
                        🧠 AI is creating your personalized lesson...
                    </p>

                    <p class="loading-sub">
                        Generating lesson • roadmap • quiz • study coach • flashcards
                    </p>
                </div>
            </div>
        </div>
        <script>
document.querySelector("form").addEventListener("submit", function(){{
    document.getElementById("loading").style.display = "block";
    document.getElementById("askBtn").disabled = true;
    document.getElementById("askBtn").innerText = "Generating...";
}});
</script>
    </body>
    </html>
    """


@app.route("/ask")
def ask():

    question = request.args.get("question")
    subject = request.args.get("subject")
    difficulty = request.args.get("difficulty")
    goal = request.args.get("goal")

    if not question:
        return "<h1>Please enter a topic.</h1>"

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
You are SmartLearn AI Agent.

Subject: {subject}
Difficulty: {difficulty}
Goal: {goal}
Topic: {question}

The Study Coach must be personalized using:

- Subject
- Difficulty Level
- Learning Goal
- Topic

If the difficulty is Beginner:
Use simpler milestones.

If Intermediate:
Use moderate pace.

If Advanced:
Use accelerated learning strategy.

If Goal is Exam Preparation:
Prioritize revision and practice questions.

If Goal is Interview Prep:
Prioritize practical understanding and common interview questions.

If Goal is Revision:
Prioritize memory retention and spaced repetition.

If Goal is Research Mode:
Prioritize deep concepts and further exploration.

Create:

# Short Explanation

# Key Points

# Learning Roadmap

# Quiz Questions

# 30 Minute Study Plan

# Knowledge Gap Analysis

# Study Tips

# Study Coach

Study Coach must include:

## Today's Focus

## Tomorrow's Focus

## This Week's Plan

## Revision Strategy

## Estimated Mastery Time

## Personalized Recommendations

# Flashcards

Generate EXACTLY 5 flashcards.

Format:

Flashcard 1
Question: ...
Answer: ...

Flashcard 2
Question: ...
Answer: ...

Flashcard 3
Question: ...
Answer: ...

Flashcard 4
Question: ...
Answer: ...

Flashcard 5
Question: ...
Answer: ...

# Revision Notes

# Summary
"""
        )

    except Exception as e:

        return f"""
        {HTML_HEADER}
        <body>
            <div class="container">
                <h1>Error</h1>
                <div class="content-card">
                    <p>{str(e)}</p>
                </div>
                <a href="/" class="back-link">Go Back</a>
            </div>
        </body>
        </html>
        """

    response_text = getattr(response, "text", "")

    if not response_text:
        return f"""
    {HTML_HEADER}
    <body>
        <div class="container">
            <h1>SmartLearn AI</h1>

            <div class="content-card">
                <p>
                AI could not generate a response.
                Please try again.
                </p>
            </div>

            <a href="/" class="back-link">
                ← Go Back
            </a>

        </div>
    </body>
    </html>
    """

    flashcards_html = ""

    clean_response = response_text

    flashcards_match = re.search(
        r"#+\s*Flashcards(.*?)(?=#+\s*Revision Notes|#+\s*Summary|$)",
        response_text,
        re.DOTALL | re.IGNORECASE
    )

    if flashcards_match:

        flashcard_section = flashcards_match.group(1)

        matches = re.findall(
            r"Flashcard\s*(\d+)\s*[\r\n]+Question:\s*(.*?)\s*[\r\n]+Answer:\s*(.*?)(?=Flashcard\s*\d+|$)",
            flashcard_section,
            re.DOTALL | re.IGNORECASE
        )

        for num, question, answer in matches:

            flashcards_html += f"""
            <div class="flashcard" onclick="flipCard(this)">
                <div class="flashcard-inner">

                    <div class="flashcard-front">
                        <h3>{question.strip()}</h3>
                    </div>

                    <div class="flashcard-back">
                        <p>{answer.strip()}</p>
                    </div>

                </div>
            </div>
            """

        clean_response = clean_response.replace(
            flashcards_match.group(0),
            ""
        )

    html_response = markdown.markdown(
        clean_response,
        extensions=["extra"]
    )

    return f"""
    {HTML_HEADER}
    <body>

        <div class="container">

            <h1>SmartLearn AI</h1>

            <p class="subtitle">
                Subject: {subject} |
                Level: {difficulty} |
                Goal: {goal}
            </p>

            <div class="content-card" id="studyContent">

                <button onclick="copyContent(this)" class="pdf-btn">
                    📋 Copy Notes
                </button>

                {html_response}

                <h2>Interactive Flashcards</h2>

                {flashcards_html}

            </div>

            <a href="/" class="back-link">
                ← Teach me something else
            </a>

        </div>

<script>

function flipCard(card){{
    card.classList.toggle("flipped");
}}
function copyContent(btn){{

    const content =
        document.getElementById("studyContent").innerText;

    navigator.clipboard.writeText(content);

    btn.innerText = "✅ Copied";

    setTimeout(() => {{
        btn.innerText = "📋 Copy Notes";
    }}, 2000);
}}


</script>

    </body>
    </html>
    """
 


@app.route("/study")
def study():
    return f"""
    {HTML_HEADER}
    <body>
        <div class="container">
            <h1>Study Route Working </h1>
            <p class="subtitle">AI features are now being added...</p>
            
            <a href="/" class="back-link">← Go Back</a>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
    