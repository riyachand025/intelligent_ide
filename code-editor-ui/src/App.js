import React, { useState, useEffect } from 'react';
import MonacoEditor from '@monaco-editor/react';
import { io } from 'socket.io-client';
import axios from 'axios';
import './App.css';

const socket = io('http://localhost:5000', {
  transports: ['websocket', 'polling'],
  reconnection: true,
});

function App() {
  const [files, setFiles] = useState([]);
  const [openTabs, setOpenTabs] = useState([]);  // { filename, content, language }
  const [activeTab, setActiveTab] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [errors, setErrors] = useState([]);
  const [compileResult, setCompileResult] = useState('');
  const [task, setTask] = useState('');
  const [newFileName, setNewFileName] = useState('');

  useEffect(() => {
    fetchFiles();
  }, []);

  useEffect(() => {
    if (activeTab) {
      const debounce = setTimeout(() => {
        socket.emit('check_syntax', { code: activeTab.content, language: activeTab.language });
      }, 500);
      return () => clearTimeout(debounce);
    }
  }, [activeTab?.content, activeTab?.language]);

  useEffect(() => {
    socket.on('syntax_result', (data) => {
      setErrors(data.errors || (data.error ? [data.error] : []));
    });
    return () => socket.off('syntax_result');
  }, []);

  const fetchFiles = async () => {
    const res = await axios.get('http://localhost:5000/files');
    setFiles(res.data.files);
  };

  const createFile = async () => {
    if (!newFileName) return;
    const language = newFileName.split('.').pop() || 'txt';
    await axios.post('http://localhost:5000/file', { filename: newFileName, content: '' });
    setNewFileName('');
    fetchFiles();
  };

  const openFile = async (filename) => {
    const res = await axios.get(`http://localhost:5000/file/${filename}`);
    const language = filename.split('.').pop();
    const newTab = { filename, content: res.data.content, language: SUPPORTED_LANGUAGES.includes(language) ? language : 'txt' };
    if (!openTabs.some(tab => tab.filename === filename)) {
      setOpenTabs([...openTabs, newTab]);
    }
    setActiveTab(newTab);
  };

  const saveFile = async () => {
    if (!activeTab) return;
    await axios.put(`http://localhost:5000/file/${activeTab.filename}`, { content: activeTab.content });
    setCompileResult(`Saved ${activeTab.filename}`);
  };

  const deleteFile = async (filename) => {
    await axios.delete(`http://localhost:5000/file/${filename}`);
    setOpenTabs(openTabs.filter(tab => tab.filename !== filename));
    if (activeTab?.filename === filename) setActiveTab(null);
    fetchFiles();
  };

  const closeTab = (filename) => {
    const newTabs = openTabs.filter(tab => tab.filename !== filename);
    setOpenTabs(newTabs);
    if (activeTab?.filename === filename) setActiveTab(newTabs[0] || null);
  };

  const fetchSuggestions = async (editor) => {
    if (!activeTab || !activeTab.content.trim()) return;
    const position = editor.getPosition();
    const cursorPos = editor.getModel().getOffsetAt(position);
    try {
      const res = await axios.post('http://localhost:5000/autocomplete', {
        code: activeTab.content,
        cursor_pos: cursorPos,
        language: activeTab.language,
      });
      setSuggestions(res.data.suggestions || []);
    } catch (err) {
      console.error('Auto-completion failed:', err.response?.data || err.message);
    }
  };

  const handleEditorDidMount = (editor, monaco) => {
    monaco.languages.registerCompletionItemProvider(activeTab?.language || 'python', {
      provideCompletionItems: () => ({
        suggestions: suggestions.map((suggestion, i) => ({
          label: suggestion,
          kind: monaco.languages.CompletionItemKind.Snippet,
          insertText: suggestion,
          range: null,
        })),
      }),
    });
    editor.onDidChangeCursorPosition(() => fetchSuggestions(editor));
  };

  const handleCompile = async () => {
    if (!activeTab) return;
    try {
      const res = await axios.post('http://localhost:5000/compile', {
        code: activeTab.content,
        language: activeTab.language,
      });
      setCompileResult(res.data.output || res.data.error || 'Compilation successful, no output.');
    } catch (err) {
      setCompileResult(err.response?.data?.error || 'Compilation failed.');
    }
  };

  const handleGenerateCode = async () => {
    if (!task || !activeTab) return;
    try {
      const res = await axios.post('http://localhost:5000/generate-code', { task, language: activeTab.language });
      setActiveTab({ ...activeTab, content: res.data.code || '' });
      setCompileResult(res.data.tests || 'No tests generated.');
    } catch (err) {
      setCompileResult(err.response?.data?.error || 'Code generation failed.');
    }
  };

  const SUPPORTED_LANGUAGES = ['python', 'javascript', 'java', 'c', 'cpp', 'rust', 'go', 'typescript', 'ruby', 'php'];

  return (
    <div className="App">
      <div className="sidebar">
        <h2>Files</h2>
        <input
          value={newFileName}
          onChange={(e) => setNewFileName(e.target.value)}
          placeholder="New file (e.g., script.py)"
        />
        <button onClick={createFile}>Create</button>
        <ul>
          {files.map((file) => (
            <li key={file}>
              <span onClick={() => openFile(file)}>{file}</span>
              <button onClick={() => deleteFile(file)}>Delete</button>
            </li>
          ))}
        </ul>
      </div>
      <div className="editor-container">
        <header>
          <div className="tabs">
            {openTabs.map((tab) => (
              <div
                key={tab.filename}
                className={`tab ${activeTab?.filename === tab.filename ? 'active' : ''}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab.filename}
                <span onClick={(e) => { e.stopPropagation(); closeTab(tab.filename); }}>x</span>
              </div>
            ))}
          </div>
          {activeTab && (
            <>
              <select
                value={activeTab.language}
                onChange={(e) => setActiveTab({ ...activeTab, language: e.target.value })}
              >
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <option key={lang} value={lang}>{lang}</option>
                ))}
              </select>
              <button onClick={handleCompile}>Compile</button>
              <input
                type="text"
                value={task}
                onChange={(e) => setTask(e.target.value)}
                placeholder="Enter task (e.g., Sort an array)"
              />
              <button onClick={handleGenerateCode}>Generate Code</button>
              <button onClick={saveFile}>Save</button>
            </>
          )}
        </header>
        {activeTab && (
          <MonacoEditor
            height="70vh"
            language={activeTab.language}
            value={activeTab.content}
            onChange={(value) => setActiveTab({ ...activeTab, content: value })}
            onMount={handleEditorDidMount}
            options={{ minimap: { enabled: true }, fontSize: 16, scrollBeyondLastLine: false }}
          />
        )}
        <div className="errors">
          <h3>Errors/Warnings</h3>
          <ul>
            {errors.map((err, i) => (
              <li key={i} style={{ color: 'red' }}>{err}</li>
            ))}
          </ul>
        </div>
        <div className="compile-result">
          <h3>Compile Output</h3>
          <pre>{compileResult}</pre>
        </div>
      </div>
    </div>
  );
}

export default App;