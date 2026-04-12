import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Toaster } from "react-hot-toast";
import "./index.css";
import App from "./App.tsx";

createRoot(document.getElementById("root")!).render(
    <StrictMode>
        <App />
        <Toaster
            position="bottom-right"
            toastOptions={{
                style: {
                    borderRadius: "0",
                    border: "3px dashed var(--border-color)",
                    background: "var(--bg-color)",
                    color: "var(--text-color)",
                    fontFamily: '"Geist Mono", monospace',
                    padding: "12px 16px",
                    boxShadow: "none",
                },
                success: {
                    iconTheme: {
                        primary: "var(--accent-color)",
                        secondary: "var(--bg-color)",
                    },
                    style: {
                        border: "3px dashed var(--accent-color)",
                    },
                },
                error: {
                    style: {
                        border: "3px dashed #ff4b4b",
                    },
                },
            }}
        />
    </StrictMode>,
);
