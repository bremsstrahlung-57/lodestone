import React, { useEffect, useState } from "react";
import toast from "react-hot-toast";
import ravenLogo from "./assets/raven.svg";
import "./App.css";

const placeholders = [
    "What do you want to find?",
    "Ask your documents something.",
    "What are you looking for?",
    "Query your knowledge base.",
    "What do you need to retrieve?",
    "Search what you've stored.",
    "Ask anything you've ingested.",
    "What did you save here?",
    "Pull something from the archive.",
    "What are you trying to remember?",
    "What did you bury here?",
    "Something you read once...",
    "Pull it back up.",
    "It's in there somewhere.",
    "What were you looking for?",
    "You saved this for a reason.",
    "Ask the archive.",
    "Where did you read that?",
    "Search the stone.",
    "You've seen this before.",
];
const API_URL = "http://localhost:8000/api/";

export default function App() {
    const [health, setHealth] = useState<string>("Checking...");
    const [text, setText] = useState("");
    const [placeholder, setPlaceholder] = useState(
        () => placeholders[Math.floor(Math.random() * placeholders.length)],
    );

    const [showSettings, setShowSettings] = useState(false);
    const [providers, setProviders] = useState<string[]>([]);
    const [selectedProvider, setSelectedProvider] = useState("");
    const [models, setModels] = useState<string[]>([]);
    const [selectedModel, setSelectedModel] = useState("");
    const [apiKeyProvider, setApiKeyProvider] = useState("");
    const [apiKey, setApiKey] = useState("");
    const [useAI, setUseAI] = useState(true);
    const [rewriteQuery, setRewriteQuery] = useState(false);
    const [results, setResults] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [expandedDocs, setExpandedDocs] = useState<Record<number, boolean>>(
        {},
    );
    const [isDragging, setIsDragging] = useState(false);
    const [fullDocContent, setFullDocContent] = useState<string | null>(null);
    const [fullDocTitle, setFullDocTitle] = useState<string>("");
    const [isModalOpen, setIsModalOpen] = useState(false);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    };

    const uploadFile = async (file: File) => {
        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch(API_URL + "ingest", {
                method: "POST",
                body: formData,
            });
            const data = await res.json();
            if (data.status === "success") {
                toast.success(data.message || "File ingested successfully!");
            } else {
                toast.error(
                    "Error: " + (data.detail || "Failed to ingest file"),
                );
            }
            console.log("Upload result:", data);
        } catch (err) {
            console.error("Upload failed:", err);
            toast.error("Upload failed. Check console for details.");
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            console.log("Uploading:", file.name);
            uploadFile(file);
        }
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            const file = e.target.files[0];
            console.log("Uploading:", file.name);
            uploadFile(file);
        }
    };

    const [theme, setTheme] = useState<"light" | "dark">(() => {
        const saved = localStorage.getItem("theme");
        if (saved === "light" || saved === "dark") return saved;
        return window.matchMedia("(prefers-color-scheme: light)").matches
            ? "light"
            : "dark";
    });

    useEffect(() => {
        document.documentElement.setAttribute("data-theme", theme);
        localStorage.setItem("theme", theme);
    }, [theme]);

    // Fetch initial config and providers
    useEffect(() => {
        Promise.all([
            fetch(API_URL + "service_providers").then((res) => res.json()),
            fetch(API_URL + "defaults_config").then((res) => res.json()),
        ])
            .then(([provData, defData]) => {
                let defaultProvider = "";
                if (
                    defData.status === "success" &&
                    defData.data?.active?.provider
                ) {
                    defaultProvider = defData.data.active.provider;
                }

                if (provData.status === "success" && provData.providers) {
                    setProviders(provData.providers);
                    const p = provData.providers.includes(defaultProvider)
                        ? defaultProvider
                        : provData.providers.length > 0
                          ? provData.providers[0]
                          : "";

                    if (p) {
                        setSelectedProvider(p);
                        setApiKeyProvider(p);
                    }
                }
            })
            .catch((err) =>
                console.error("Failed to fetch initial data:", err),
            );
    }, []);

    // Fetch models when provider changes
    useEffect(() => {
        if (!selectedProvider) return;
        fetch(`${API_URL}models?provider=${selectedProvider}`)
            .then((res) => res.json())
            .then((data) => {
                if (data.status === "success" && data.models) {
                    setModels(data.models);
                    fetch(API_URL + "defaults_config")
                        .then((res) => res.json())
                        .then((defData) => {
                            const active = defData?.data?.active;
                            if (
                                active?.provider === selectedProvider &&
                                active?.model &&
                                data.models.includes(active.model)
                            ) {
                                setSelectedModel(active.model);
                            } else if (data.models.length > 0) {
                                setSelectedModel(data.models[0]);
                            }
                        })
                        .catch(() => {
                            if (data.models.length > 0)
                                setSelectedModel(data.models[0]);
                        });
                }
            })
            .catch((err) => {
                console.error("Failed to fetch models:", err);
                setModels([]);
                setSelectedModel("");
            });
    }, [selectedProvider]);

    const handleSaveDefaultModel = async () => {
        if (!selectedProvider || !selectedModel) return;
        try {
            const res = await fetch(API_URL + "add_default_model", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    provider: selectedProvider,
                    model: selectedModel,
                }),
            });
            const data = await res.json();
            if (data.status === "success") {
                toast.success("Default model saved successfully!");
            } else {
                toast.error("Error saving default model");
            }
        } catch (err) {
            console.error("Failed to save default model:", err);
        }
    };

    const fetchFullDocument = async (docId: string, title: string) => {
        try {
            const res = await fetch(`${API_URL}document/${docId}`);
            const data = await res.json();
            if (data.status === "success") {
                setFullDocContent(data.content);
                setFullDocTitle(title || "Untitled Document");
                setIsModalOpen(true);
            } else {
                toast.error("Failed to load document content.");
            }
        } catch (err) {
            console.error("Error fetching full document:", err);
            toast.error("Error fetching full document.");
        }
    };

    const handleAddApiKey = async () => {
        if (!apiKeyProvider || !apiKey) return;
        try {
            const res = await fetch(API_URL + "add_api", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ provider: apiKeyProvider, key: apiKey }),
            });
            const data = await res.json();
            if (data.status === "success") {
                toast.success("API Key added successfully!");
                setApiKey("");
            } else {
                toast.error("Error adding API Key");
            }
        } catch (err) {
            console.error("Failed to add API key:", err);
        }
    };

    const handleSearch = async () => {
        if (!text.trim()) return;
        setIsLoading(true);
        setResults(null);
        setExpandedDocs({});
        const mode = useAI ? "ai" : "retrieval";
        const params = new URLSearchParams({
            query: text,
            mode: mode,
            rewrite_query: String(rewriteQuery),
        });
        if (selectedProvider) {
            params.append("provider", selectedProvider);
        }

        try {
            const res = await fetch(`${API_URL}search?${params.toString()}`);
            const data = await res.json();
            setResults(data);
        } catch (err) {
            console.error("Search failed:", err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        // Fetch health status from the backend
        fetch(API_URL + "health")
            .then((res) => res.json())
            .then((data) => {
                setHealth(
                    data.status === "ok" ? "Online" : JSON.stringify(data),
                );
            })
            .catch((err) => {
                console.error("Health check failed:", err);
                setHealth("Offline");
            });
    }, []);

    return (
        <div>
            {/* theme */}
            <div>
                <button
                    onClick={() =>
                        setTheme(theme === "light" ? "dark" : "light")
                    }
                    className="themeToggleButton"
                >
                    {theme === "light" ? "🌙 Dark Mode" : "☀️ Light Mode"}
                </button>
            </div>

            {/* health check of the backend */}
            <div className="healthCheck">
                <p>{health}</p>
            </div>

            <div className="settings">
                <button
                    onClick={() => setShowSettings(!showSettings)}
                    className="settingsToggle"
                >
                    {showSettings ? "✕ Close" : "⚙️ Settings"}
                </button>
                {showSettings && (
                    <div className="settingsPanel">
                        <div className="settingsGroup">
                            <label>Provider</label>
                            <select
                                value={selectedProvider}
                                onChange={(e) =>
                                    setSelectedProvider(e.target.value)
                                }
                            >
                                {providers.map((p) => (
                                    <option key={p} value={p}>
                                        {p}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="settingsGroup">
                            <label>Model</label>
                            <select
                                value={selectedModel}
                                onChange={(e) =>
                                    setSelectedModel(e.target.value)
                                }
                                disabled={models.length === 0}
                            >
                                {models.map((m) => (
                                    <option key={m} value={m}>
                                        {m}
                                    </option>
                                ))}
                            </select>
                            <button onClick={handleSaveDefaultModel}>
                                Save Default
                            </button>
                        </div>

                        <div className="settingsGroup apiKeyGroup">
                            <label>Add API Key</label>
                            <select
                                value={apiKeyProvider}
                                onChange={(e) =>
                                    setApiKeyProvider(e.target.value)
                                }
                            >
                                {providers.map((p) => (
                                    <option key={p} value={p}>
                                        {p}
                                    </option>
                                ))}
                            </select>
                            <input
                                type="password"
                                placeholder="sk-..."
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                            />
                            <button onClick={handleAddApiKey}>Save Key</button>
                        </div>
                    </div>
                )}
            </div>

            <div className="mainContent">
                {isLoading ? (
                    <div className="loaderText">{placeholder}</div>
                ) : results ? (
                    <div className="resultsContainer">
                        {results.ai_response?.ai_answer && (
                            <div className="aiResponse">
                                <h3>AI Response</h3>
                                <p>{results.ai_response.ai_answer}</p>
                            </div>
                        )}

                        {results.retrieval?.results &&
                            results.retrieval.results.length > 0 && (
                                <div className="sourcesList">
                                    <h3>Sources</h3>
                                    {results.retrieval.results.map(
                                        (doc: any, i: number) => (
                                            <div key={i} className="sourceCard">
                                                <h4>
                                                    {doc.title ||
                                                        "Untitled Document"}
                                                </h4>
                                                <p>
                                                    {doc.text ||
                                                        doc.snippets?.[0]
                                                            ?.text ||
                                                        JSON.stringify(doc)}
                                                </p>
                                                {doc.snippets &&
                                                    doc.snippets.length > 1 && (
                                                        <>
                                                            {expandedDocs[
                                                                i
                                                            ] && (
                                                                <div className="extraChunks">
                                                                    {doc.snippets
                                                                        .slice(
                                                                            1,
                                                                        )
                                                                        .map(
                                                                            (
                                                                                snippet: any,
                                                                                j: number,
                                                                            ) => (
                                                                                <div
                                                                                    key={
                                                                                        j
                                                                                    }
                                                                                    className="chunkItem"
                                                                                >
                                                                                    {snippet.text ||
                                                                                        JSON.stringify(
                                                                                            snippet,
                                                                                        )}
                                                                                </div>
                                                                            ),
                                                                        )}
                                                                </div>
                                                            )}
                                                            <button
                                                                className="expandButton"
                                                                onClick={() =>
                                                                    setExpandedDocs(
                                                                        (
                                                                            prev,
                                                                        ) => ({
                                                                            ...prev,
                                                                            [i]: !prev[
                                                                                i
                                                                            ],
                                                                        }),
                                                                    )
                                                                }
                                                            >
                                                                {expandedDocs[i]
                                                                    ? "▲ Hide other chunks"
                                                                    : "▼ View other chunks"}
                                                            </button>
                                                        </>
                                                    )}
                                                <button
                                                    className="viewFullButton"
                                                    onClick={() =>
                                                        fetchFullDocument(
                                                            doc.doc_id,
                                                            doc.title,
                                                        )
                                                    }
                                                >
                                                    View Full Document
                                                </button>
                                            </div>
                                        ),
                                    )}
                                </div>
                            )}
                    </div>
                ) : (
                    <>
                        <div className="heading">
                            <a>{placeholder}</a>
                        </div>
                        <div className="inputContainer">
                            <input
                                type="text"
                                value={text}
                                id="queryInputText"
                                className="inputField"
                                onChange={(e) => setText(e.target.value)}
                                placeholder="Type here..."
                                onKeyDown={(e) => {
                                    if (e.key === "Enter") {
                                        handleSearch();
                                    }
                                }}
                            />
                            <button
                                onClick={handleSearch}
                                className="sendButton"
                            >
                                <img
                                    src={ravenLogo}
                                    alt="Raven icon"
                                    width="24"
                                    height="24"
                                />
                            </button>
                        </div>
                        <div className="switchesContainer">
                            <label className="switchLabel">
                                <input
                                    type="checkbox"
                                    checked={useAI}
                                    onChange={(e) => setUseAI(e.target.checked)}
                                />
                                Use AI
                            </label>
                            <label className="switchLabel">
                                <input
                                    type="checkbox"
                                    checked={rewriteQuery}
                                    onChange={(e) =>
                                        setRewriteQuery(e.target.checked)
                                    }
                                />
                                Rewrite Query
                            </label>
                        </div>
                        <div
                            className={`dropzoneContainer ${isDragging ? "active" : ""}`}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                            onClick={() =>
                                document.getElementById("fileInput")?.click()
                            }
                        >
                            <input
                                type="file"
                                id="fileInput"
                                onChange={handleFileSelect}
                            />
                            <p>Drop a file here or click to select</p>
                        </div>
                    </>
                )}
            </div>

            {results && !isLoading && (
                <button
                    className="newChatButton"
                    onClick={() => {
                        setResults(null);
                        setText("");
                        setExpandedDocs({});
                    }}
                >
                    + New Chat
                </button>
            )}

            {isModalOpen && (
                <div
                    className="modalOverlay"
                    onClick={() => setIsModalOpen(false)}
                >
                    <div
                        className="modalContent"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="modalHeader">
                            <h3>{fullDocTitle}</h3>
                            <button
                                className="closeModalButton"
                                onClick={() => setIsModalOpen(false)}
                            >
                                ✕ Close
                            </button>
                        </div>
                        <div className="modalBody">{fullDocContent}</div>
                    </div>
                </div>
            )}
        </div>
    );
}
