import { useState } from "react";
import "./App.css";

function App() {
    const [inputValue, setInputValue] = useState("");
    const [dialogOpen, setDialogOpen] = useState(false);
    const [healthStatus, setHealthStatus] = useState<string | null>(null);
    const [healthLoading, setHealthLoading] = useState(false);

    const handleHealthCheck = async () => {
        setHealthLoading(true);
        setHealthStatus(null);
        try {
            const response = await fetch("http://localhost:8000/api/health");
            const data = await response.json();
            setHealthStatus(JSON.stringify(data, null, 2));
        } catch (error) {
            setHealthStatus(
                `Error: ${error instanceof Error ? error.message : "Failed to connect to server"}`,
            );
        } finally {
            setHealthLoading(false);
            setDialogOpen(true);
        }
    };

    return (
        <div className="app-container">
            {/* Health Check Button - Top Right */}
            <button className="health-check-btn" onClick={handleHealthCheck}>
                {healthLoading ? (
                    <span className="spinner" />
                ) : (
                    <svg
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                    </svg>
                )}
                <span>Health</span>
            </button>

            {/* Dialog Overlay */}
            {dialogOpen && (
                <div
                    className="dialog-overlay"
                    onClick={() => setDialogOpen(false)}
                >
                    <div
                        className="dialog"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="dialog-header">
                            <h3>API Health Check</h3>
                            <button
                                className="dialog-close"
                                onClick={() => setDialogOpen(false)}
                            >
                                &times;
                            </button>
                        </div>
                        <div className="dialog-body">
                            <pre>{healthStatus}</pre>
                        </div>
                    </div>
                </div>
            )}

            {/* Main Content - Centered */}
            <div className="main-content">
                <div className="greeting">
                    <h1>What can I help you with?</h1>
                </div>

                {/* Input Area */}
                <div className="input-area">
                    <div className="textbar-container">
                        <textarea
                            className="textbar"
                            placeholder="Ask anything..."
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            rows={1}
                            onInput={(e) => {
                                const target = e.target as HTMLTextAreaElement;
                                target.style.height = "auto";
                                target.style.height =
                                    Math.min(target.scrollHeight, 200) + "px";
                            }}
                        />
                        <button
                            className="send-btn"
                            disabled={!inputValue.trim()}
                        >
                            <svg
                                width="20"
                                height="20"
                                viewBox="0 0 24 24"
                                fill="currentColor"
                            >
                                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                            </svg>
                        </button>
                    </div>

                    {/* File Drop Zone */}
                    <div className="file-drop-zone">
                        <svg
                            width="24"
                            height="24"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            className="upload-icon"
                        >
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                            <polyline points="17 8 12 3 7 8" />
                            <line x1="12" y1="3" x2="12" y2="15" />
                        </svg>
                        <span className="drop-text">
                            Drop files here to upload
                        </span>
                        <span className="drop-subtext">
                            Supports PDF, TXT, DOCX, and more
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default App;
