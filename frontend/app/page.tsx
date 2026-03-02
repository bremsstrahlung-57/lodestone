"use client";

import { useState } from "react";

export default function Home() {
    const [query, setQuery] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;
        // TODO: handle search submission
        console.log("Search:", query);
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-screen px-4">
            <div className="w-full max-w-2xl flex flex-col items-center gap-8">
                {/* Greeting */}
                <div className="flex flex-col items-center gap-2">
                    <h1 className="text-4xl font-semibold tracking-tight text-foreground">
                        What do you want to recall?
                    </h1>
                    <p className="text-base text-foreground/50">
                        Search your personal knowledge base
                    </p>
                </div>

                {/* Search bar */}
                <form onSubmit={handleSubmit} className="w-full">
                    <div className="relative w-full rounded-2xl border border-foreground/15 bg-foreground/[0.03] shadow-sm transition-all duration-200 focus-within:border-foreground/30 focus-within:shadow-md">
                        <textarea
                            value={query}
                            onChange={(e) => {
                                setQuery(e.target.value);
                                // Auto-resize
                                e.target.style.height = "auto";
                                e.target.style.height =
                                    Math.min(e.target.scrollHeight, 200) + "px";
                            }}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSubmit(e);
                                }
                            }}
                            placeholder="Ask anything..."
                            rows={1}
                            className="w-full resize-none bg-transparent px-5 pt-4 pb-14 text-base text-foreground placeholder:text-foreground/35 focus:outline-none"
                        />

                        {/* Bottom toolbar */}
                        <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between px-3 pb-3">
                            {/* Left side - attachment button */}
                            <button
                                type="button"
                                className="flex items-center justify-center h-9 w-9 rounded-lg text-foreground/40 hover:text-foreground/70 hover:bg-foreground/5 transition-colors"
                                aria-label="Attach file"
                            >
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    width="18"
                                    height="18"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                >
                                    <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
                                </svg>
                            </button>

                            {/* Right side - submit button */}
                            <button
                                type="submit"
                                disabled={!query.trim()}
                                className="flex items-center justify-center h-9 w-9 rounded-lg bg-foreground text-background transition-opacity disabled:opacity-25 hover:opacity-80"
                                aria-label="Submit"
                            >
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    width="18"
                                    height="18"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                >
                                    <line x1="12" y1="19" x2="12" y2="5" />
                                    <polyline points="5 12 12 5 19 12" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    );
}
