from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import re
from flask_socketio import SocketIO
import io
import tokenize
import ast
import pylint.lint
from pylint.reporters import CollectingReporter
import subprocess
import tempfile
import os
import glob

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000", 
                    async_mode='threading', logger=True, engineio_logger=True)

genai.configure(api_key="AIzaSyBoTNRvbX3ZD_AT88C7V_ldIG8FpR6P8uE")

# Directory for storing files
FILES_DIR = os.path.join(os.getcwd(), "user_files")
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

SUPPORTED_LANGUAGES = [
    'python', 'javascript', 'java', 'c', 'cpp', 'rust', 'go', 'typescript', 'ruby', 'php'
]

def validate_language(language):
    return language.lower() in SUPPORTED_LANGUAGES

def analyze_python_code(code):
    errors = []
    try:
        io_obj = io.StringIO(code)
        for token in tokenize.generate_tokens(io_obj.readline):
            pass
    except tokenize.TokenError as e:
        errors.append({"line": e.args[1][0], "message": str(e), "type": "error"})
    try:
        tree = ast.parse(code)
        assigned_names = set()
        used_names = set()
        class VariableVisitor(ast.NodeVisitor):
            def visit_Assign(self, node):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assigned_names.add(target.id)
                self.generic_visit(node)
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)
                self.generic_visit(node)
        visitor = VariableVisitor()
        visitor.visit(tree)
        unused_variables = assigned_names - used_names
        for var in unused_variables:
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == var:
                            errors.append({"line": node.lineno, "message": f"Unused variable: '{var}'", "type": "warning"})
                            break
    except SyntaxError as e:
        errors.append({"line": e.lineno, "message": str(e), "type": "error"})
    except Exception as e:
        errors.append({"line": 1, "message": f"AST parsing error: {str(e)}", "type": "error"})
    try:
        reporter = CollectingReporter()
        pylint_opts = [
            "--disable=all",
            "--enable=syntax-error,unreachable,unused-variable,useless-else-on-loop,undefined-variable",
            "--persistent=no",
            "--score=no"
        ]
        with io.StringIO(code) as f:
            linter = pylint.lint.Run(["<code>"], reporter=reporter, args=pylint_opts)
            pylint_messages = reporter.messages
            for msg in pylint_messages:
                errors.append({
                    "line": msg.line,
                    "message": msg.msg,
                    "type": "warning" if msg.category == "convention" else "error",
                    "pylint_id": msg.msg_id
                })
    except ImportError:
        errors.append({"line": 1, "message": "Pylint not installed. Install with: pip install pylint", "type": "warning"})
    except Exception as e:
        errors.append({"line": 1, "message": f"Pylint error: {str(e)}", "type": "error"})
    return errors

@app.route('/generate-code', methods=['POST'])
def generate_code():
    task = request.json.get('task', '').strip()
    language = request.json.get('language', 'python').strip().lower()
    if not task:
        return jsonify({"error": "No task provided"}), 400
    if not validate_language(language):
        return jsonify({"error": f"Unsupported language: {language}"}), 400
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(f"""
        Task: {task}
        Language: {language.capitalize()}
        Generate only the code and corresponding unit tests. Do not include explanations.
        """)
        raw_output = response.text.strip()
        code_blocks = re.findall(r'```(.*?)```', raw_output, re.DOTALL)
        if not code_blocks:
            return jsonify({"error": "No valid code found"}), 500
        code_and_tests = code_blocks[0].strip().split("Unit Tests:")
        code = code_and_tests[0].strip()
        tests = code_and_tests[1].strip() if len(code_and_tests) > 1 else ""
        return jsonify({"code": code, "tests": tests}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/debug-code', methods=['POST'])
def debug_code():
    code = request.json.get('code', '').strip()
    language = request.json.get('language', 'python').strip().lower()
    if not code:
        return jsonify({"error": "No code provided"}), 400
    if not validate_language(language):
        return jsonify({"error": f"Unsupported language: {language}"}), 400
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(f"""
        Code: {code}
        Language: {language.capitalize()}
        Identify potential bugs and suggest fixes. Provide only actionable suggestions.
        """)
        return jsonify({"suggestions": response.text.strip()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/autocomplete', methods=['POST'])
def autocomplete():
    code = request.json.get('code', '').strip()
    cursor_pos = request.json.get('cursor_pos', 0)
    language = request.json.get('language', 'python').strip().lower()
    if not code:
        return jsonify({"error": "No code provided"}), 400
    if not validate_language(language):
        return jsonify({"error": f"Unsupported language: {language}"}), 400
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(f"""
        Code: {code}
        Language: {language.capitalize()}
        Cursor Position: {cursor_pos}
        Suggest auto-completion snippets based on the current context. Return only the snippet suggestions as a list.
        """)
        suggestions = response.text.strip().split('\n')
        return jsonify({"suggestions": [s.strip() for s in suggestions if s.strip()]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/compile', methods=['POST'])
def compile_code():
    code = request.json.get('code', '').strip()
    language = request.json.get('language', 'python').strip().lower()
    if not code:
        return jsonify({"error": "No code provided"}), 400
    if not validate_language(language):
        return jsonify({"error": f"Unsupported language: {language}"}), 400
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{language}') as temp_file:
            temp_file.write(code.encode('utf-8'))
            temp_file_path = temp_file.name
        if language == 'python':
            result = subprocess.run(['python3', temp_file_path], capture_output=True, text=True, timeout=5)
            output = result.stdout if result.returncode == 0 else result.stderr
        elif language == 'c':
            output_file = temp_file_path.replace('.c', '')
            result = subprocess.run(['gcc', temp_file_path, '-o', output_file], capture_output=True, text=True, timeout=5)
            output = result.stderr if result.returncode != 0 else subprocess.run([output_file], capture_output=True, text=True).stdout
        elif language == 'cpp':
            output_file = temp_file_path.replace('.cpp', '')
            result = subprocess.run(['g++', temp_file_path, '-o', output_file], capture_output=True, text=True, timeout=5)
            output = result.stderr if result.returncode != 0 else subprocess.run([output_file], capture_output=True, text=True).stdout
        elif language == 'rust':
            output_file = temp_file_path.replace('.rust', '')
            result = subprocess.run(['rustc', temp_file_path, '-o', output_file], capture_output=True, text=True, timeout=5)
            output = result.stderr if result.returncode != 0 else subprocess.run([output_file], capture_output=True, text=True).stdout
        elif language == 'go':
            result = subprocess.run(['go', 'run', temp_file_path], capture_output=True, text=True, timeout=5)
            output = result.stdout if result.returncode == 0 else result.stderr
        else:
            output = f"Compilation not supported for {language} yet."
        os.remove(temp_file_path)
        if language in ['c', 'cpp', 'rust'] and os.path.exists(output_file):
            os.remove(output_file)
        return jsonify({"output": output.strip()}), 200
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Compilation timed out"}), 500
    except FileNotFoundError as e:
        return jsonify({"error": f"Compiler not found: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# File Management Endpoints
@app.route('/files', methods=['GET'])
def list_files():
    files = glob.glob(os.path.join(FILES_DIR, "*"))
    return jsonify({"files": [os.path.basename(f) for f in files]}), 200

@app.route('/file', methods=['POST'])
def create_file():
    filename = request.json.get('filename', '').strip()
    content = request.json.get('content', '')
    if not filename:
        return jsonify({"error": "No filename provided"}), 400
    file_path = os.path.join(FILES_DIR, filename)
    with open(file_path, 'w') as f:
        f.write(content)
    return jsonify({"message": f"File {filename} created"}), 200

@app.route('/file/<filename>', methods=['GET'])
def read_file(filename):
    file_path = os.path.join(FILES_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    with open(file_path, 'r') as f:
        content = f.read()
    return jsonify({"content": content}), 200

@app.route('/file/<filename>', methods=['PUT'])
def save_file(filename):
    content = request.json.get('content', '')
    file_path = os.path.join(FILES_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    with open(file_path, 'w') as f:
        f.write(content)
    return jsonify({"message": f"File {filename} saved"}), 200

@app.route('/file/<filename>', methods=['DELETE'])
def delete_file(filename):
    file_path = os.path.join(FILES_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    os.remove(file_path)
    return jsonify({"message": f"File {filename} deleted"}), 200

@socketio.on('check_syntax')
def handle_syntax_check(data):
    code = data.get('code', '').strip()
    language = data.get('language', 'python').strip().lower()
    if not code:
        socketio.emit('syntax_result', {"error": "No code provided"})
        return
    if not validate_language(language):
        socketio.emit('syntax_result', {"error": f"Unsupported language: {language}"})
        return
    if language == 'python':
        errors = analyze_python_code(code)
        formatted_errors = [f"Line {e['line']}: {e['message']}" for e in errors]
        socketio.emit('syntax_result', {"errors": formatted_errors})
    else:
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(f"""
            Code: {code}
            Language: {language.capitalize()}
            Perform real-time syntax checking and static analysis. Return a list of errors or warnings (e.g., line number, message).
            Return an empty list if no issues are found.
            """)
            errors = response.text.strip().split('\n') if response.text.strip() else []
            socketio.emit('syntax_result', {"errors": [e.strip() for e in errors if e.strip()]})
        except Exception as e:
            socketio.emit('syntax_result', {"error": str(e)})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)