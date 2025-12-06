"use client";

import { useState } from "react";

const BACKEND_URL = ""; // Use relative path to leverage Next.js proxy (solves CORS)

interface UseRAGApiReturn {
    uploadDocument: (file: File) => Promise<{ success: boolean; message: string }>;
    askQuestion: (query: string) => Promise<{ result: string }>;
    summarizeDocument: (query?: string) => Promise<{ result: string }>;
    runCPAAgent: (query?: string) => Promise<{ result: string }>;
    isLoading: boolean;
    error: string | null;
}

export function useRAGApi(): UseRAGApiReturn {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const uploadDocument = async (file: File): Promise<{ success: boolean; message: string }> => {
        setIsLoading(true);
        setError(null);

        try {
            const formData = new FormData();

            // Check if file is JSON
            if (file.name.endsWith('.json') || file.type === 'application/json') {
                // Read JSON content
                const textContent = await file.text();
                // Create a new Blob with text content
                const blob = new Blob([textContent], { type: 'text/plain' });
                // Create a new File object with .txt extension
                const newFileName = file.name.replace(/\.json$/i, '.txt');
                const newFile = new File([blob], newFileName, { type: 'text/plain' });

                formData.append("file", newFile);
            } else {
                formData.append("file", file);
            }

            const response = await fetch(`${BACKEND_URL}/api/upload`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            const data = await response.json();
            setIsLoading(false);
            return { success: true, message: data.message || "Document uploaded successfully!" };
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Failed to upload document";
            setError(errorMessage);
            setIsLoading(false);
            return { success: false, message: errorMessage };
        }
    };

    const formatResponse = (data: any): string => {
        try {
            if (data === null || data === undefined) return "No data received.";
            if (typeof data === 'string') return data;

            if (typeof data === 'object') {
                // Check for the specific structure mentioned in the error
                // keys: {title, content, key_points, language}
                if (data.title || data.content) {
                    let markdown = "";
                    if (data.title) markdown += `### ${data.title}\n\n`;
                    if (data.content) markdown += `${data.content}\n\n`;

                    if (data.key_points && Array.isArray(data.key_points)) {
                        markdown += `**Key Points:**\n${data.key_points.map((kp: any) => `- ${kp}`).join('\n')}\n\n`;
                    }

                    return markdown.trim();
                }
                // Check if result is nested and we haven't already processed it
                // Prevent infinite recursion if data.result === data
                if (data.result && data.result !== data) return formatResponse(data.result);

                // Fallback: pretty print JSON
                return JSON.stringify(data, null, 2);
            }
            return String(data);
        } catch (e) {
            console.error("Error formatting response:", e);
            return "Error formatting response.";
        }
    };

    const askQuestion = async (query: string): Promise<{ result: string }> => {
        setIsLoading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append("query", query);

            const response = await fetch(`${BACKEND_URL}/api/qa`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Question failed: ${response.statusText}`);
            }

            const data = await response.json();
            setIsLoading(false);
            return { result: formatResponse(data.result || data.answer || data) };
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Failed to get answer";
            setError(errorMessage);
            setIsLoading(false);
            throw new Error(errorMessage);
        }
    };

    const summarizeDocument = async (query: string = "Summarize this document"): Promise<{ result: string }> => {
        setIsLoading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append("query", query);

            const response = await fetch(`${BACKEND_URL}/api/summarize`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Summarization failed: ${response.statusText}`);
            }

            const data = await response.json();
            setIsLoading(false);
            return { result: formatResponse(data.result || data.summary || data) };
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Failed to summarize document";
            setError(errorMessage);
            setIsLoading(false);
            throw new Error(errorMessage);
        }
    };

    const runCPAAgent = async (query: string = "Process this document"): Promise<{ result: string }> => {
        setIsLoading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append("query", query);

            const response = await fetch(`${BACKEND_URL}/api/cpa_agent`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`CPA Agent failed: ${response.statusText}`);
            }

            const data = await response.json();
            setIsLoading(false);
            return { result: formatResponse(data.result || data) };
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Failed to run CPA agent";
            setError(errorMessage);
            setIsLoading(false);
            throw new Error(errorMessage);
        }
    };

    return {
        uploadDocument,
        askQuestion,
        summarizeDocument,
        runCPAAgent,
        isLoading,
        error,
    };
}
