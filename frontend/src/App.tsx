import { useEffect, useState } from "react";
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

export default function App() {
    const [health, setHealth] = useState<string>("Checking...");
    const [text, setText] = useState("");
    const [placeholder, setPlaceholder] = useState(
        () => placeholders[Math.floor(Math.random() * placeholders.length)],
    );
    const [theme, setTheme] = useState<"light" | "dark">(() =>
        window.matchMedia("(prefers-color-scheme: light)").matches
            ? "light"
            : "dark",
    );

    useEffect(() => {
        document.documentElement.setAttribute("data-theme", theme);
    }, [theme]);

    useEffect(() => {
        // Fetch health status from the backend
        fetch("http://localhost:8000/api/health")
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
            <div className="healthCheck">
                <p>{health}</p>
            </div>
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
                />
                <button
                    onClick={() => console.log("Send:", text)}
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
        </div>
    );
}
