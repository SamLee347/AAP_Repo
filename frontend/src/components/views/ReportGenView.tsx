"use client"

import { useState, useEffect } from "react"

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000"

export function ReportGenView() {
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState("")
    const [pdfFiles, setPdfFiles] = useState<string[]>([])
    const [pdfLoading, setPdfLoading] = useState(true)

    useEffect(() => {
        setPdfLoading(true)
        fetch(`${API_BASE_URL}/list-reports`)
            .then(res => res.json())
            .then(data => setPdfFiles(data || []))
            .catch(() => setPdfFiles([]))
            .finally(() => setPdfLoading(false))
    }, [])

    const handleGenerate = async () => {
        setLoading(true)
        try {
            const response = await fetch(`${API_BASE_URL}/generateReport`, {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            })

            if (response.ok) {
                const data = await response.text()
                setResult(data)
            } else {
                throw new Error("API not available")
            }
        } catch (error) {
            setResult(`Error: ${error}`)
        }
        setLoading(false)
    }

    return (
        <div>
            <h2 className="mb-6 font-size-24 font-weight-600">
                AI Report Generation
            </h2>
            <div>
                <button
                    className="btn btn-primary mb-4"
                    onClick={handleGenerate}
                    disabled={loading}
                >
                    {loading ? "Generating... (This may take a while)" : "Generate Report"}
                </button>
                {result && (
                    <div className="alert alert-info mb-4">
                        {result}
                    </div>
                )}
                <h3 className="mb-3">Available Reports</h3>
                {pdfLoading ? (
                    <div>Loading reports...</div>
                ) : (
                    <div className="card-deck">
                        {pdfFiles.map((filename) => (
                            <div className="card mb-3" key={filename}>
                                <div className="card-body">
                                    <h5 className="card-title">{filename.replace(".pdf", "")}</h5>
                                    <button
                                        className="btn btn-outline-primary"
                                        onClick={() => window.open(
                                            `${API_BASE_URL}/Reports/${filename}`,
                                            "_blank",
                                            "noopener,noreferrer"
                                        )}
                                    >
                                        View PDF
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}