A web-based code editor inspired by Visual Studio Code, featuring AI-powered code generation, auto-completion, real-time syntax checking, compilation, file management, and multi-window editing. Built with Flask (backend) and React with Monaco Editor (frontend).

Overview

This project supports multiple programming languages (Python, JavaScript, Java, C, C++, Rust, Go, etc.) and provides a robust development environment with features like tabbed editing and a file explorer.
Prerequisites

    Operating System: Linux (e.g., Kali, Ubuntu) recommended; adaptable to Windows/Mac with adjustments.
    Python 3.12: Backend runtime.
    Node.js: Frontend runtime (v16+ recommended).
    Compilers: Required for compilation (e.g., gcc, g++, rustc, go).
    Git: For cloning the repository (optional).

Generating the Environment
1. Clone the Repository (Optional)

If hosted on GitHub or similar:
bash
git clone https://github.com/yourusername/smart-code-editor.git
cd smart-code-editor

Alternatively, create the directory structure manually:
bash
mkdir ~/ide  
cd ~/ide
2. Backend Environment
Install Python 3.12

    On Kali Linux:
    bash

sudo apt update
sudo apt install python3.12 python3-pip
Verify:
bash

    python3 --version

Set Up Virtual Environment
bash
python3 -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
Install Python Dependencies
bash
pip install flask flask-cors flask-socketio google-generativeai pylint

    Notes:
        flask-socketio requires a compatible version (e.g., 5.3.6) for WebSocket support.
        google-generativeai needs a valid API key (see below).

Install Compilers

For compilation support:
bash
sudo apt update
sudo apt install gcc g++ rustc golang

    Verify:
    bash

    gcc --version
    g++ --version
    rustc --version
    go version

Configure Gemini API Key

    Obtain an API key from Google AI Studio.
    Edit app.py:
        Replace "AIzaSyBoTNRvbX3ZD_AT88C7V_ldIG8FpR6P8uE" with your key:
        python

        genai.configure(api_key="YOUR_API_KEY_HERE")

3. Frontend Environment
Install Node.js

    On Kali Linux:
    bash

curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs
Verify:
bash

    node -v  # Should show v16.x.x or higher
    npm -v

Set Up Frontend Directory
bash
cd ~/ide
npx create-react-app smart-code-editor
cd smart-code-editor
Install Frontend Dependencies
bash
npm install @monaco-editor/react socket.io-client axios

    Ensure socket.io-client version matches flask-socketio (e.g., ~4.x):
    bash

    npm install socket.io-client@4.7.4

Running the Code
1. Start the Backend
bash
cd ~/ide
source myenv/bin/activate  # Activate virtual env if not already active
python3 app.py

    Output: Should show:
    text

    * Running on http://127.0.0.1:5000
    * Running on http://<your-ip>:5000
    Notes: Runs on port 5000; keep this terminal open.

2. Start the Frontend

In a new terminal:
bash
cd ~/ide/smart-code-editor
npm start

    Output: Browser opens http://localhost:3000 automatically.
    Notes: Ensure the backend is running first.

Usage

    Access: Open http://localhost:3000 in a browser.
    File Management: Use the sidebar to create (e.g., script.py), open, save, or delete files.
    Multi-Window Editing: Open files in tabs; switch or close them as needed.
    Features:
        Generate Code: Input a task (e.g., "Sort an array") and click "Generate Code".
        Auto-Completion: Type code; suggestions appear as you move the cursor.
        Syntax Checking: Errors/warnings update in real-time.
        Compile: Click "Compile" to run the active file’s code.

