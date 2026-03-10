"use client";

import { useState, useEffect, Suspense } from "react";
import { api } from "@/lib/api";
import { Workflow, WorkflowNode, WorkflowEdge, NODE_STYLES, NodeType } from "@/lib/workflowSchema";
import { useRouter, useSearchParams } from "next/navigation";
import { Database } from "lucide-react";

const EXAMPLE_PROMPTS = [
  "Read patient data from CSV, validate records, flag abnormal lab values, and store in database",
  "Load HL7 messages from API, convert units, filter by age > 65, save to database with a daily schedule",
  "Read vitals from database, aggregate by patient, export to CSV file",
  "Create a REST API endpoint that filters patients and returns results",
];

export function AIPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sourceFile = searchParams.get("source_file");

  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [datasetContext, setDatasetContext] = useState<any>(null);
  const [result, setResult] = useState<{
    name: string;
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
    explanation: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch dataset preview if navigating from datasets page
  useEffect(() => {
    if (sourceFile) {
      api.get(`/datasets/preview?path=${encodeURIComponent(sourceFile)}`)
        .then((res) => {
          setDatasetContext(res.data);
          // Auto-prompt suggestion
          if (!prompt) {
            setPrompt(`I have a dataset with these columns: ${res.data.headers?.join(", ")}. Please build an ETL pipeline to clean this data, flag any abnormal values, and load it into PostgreSQL.`);
          }
        })
        .catch((err) => console.error("Failed to load dataset preview", err));
    }
  }, [sourceFile]);

  const handleGenerate = async () => {
    if (!prompt.trim() && !datasetContext) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Append dataset context to prompt invisibly so the AI sees it
      let enrichedPrompt = prompt;
      if (datasetContext) {
        const previewStr = JSON.stringify({
          filename: datasetContext.path,
          headers: datasetContext.headers,
          sample_data: datasetContext.sample_rows
        });
        enrichedPrompt += `\n\nCRITICAL CONTEXT: The user is working with the following dataset schema:\n${previewStr}`;
      }

      const res = await api.post("/ai/generate", { prompt: enrichedPrompt });
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Generation failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const openInWorkflowBuilder = () => {
    if (!result) return;
    sessionStorage.setItem(
      "generated_workflow",
      JSON.stringify({
        name: result.name,
        nodes: result.nodes,
        edges: result.edges,
      })
    );
    router.push("/workflow");
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">AI Workflow Generator</h1>
      <p className="text-gray-500 mb-4">
        Describe what your data pipeline should do, and AI will generate a workflow for you.
      </p>

      {/* Dataset Context Indicator */}
      {datasetContext && (
        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-3">
          <Database className="text-blue-600 mt-0.5" size={20} />
          <div>
            <h3 className="text-sm font-semibold text-blue-800">Dataset Context Active: {datasetContext.path.split("/").pop()}</h3>
            <p className="text-xs text-blue-600 mt-1">
              Columns detected: {datasetContext.headers?.join(", ") || "Unknown"}
            </p>
          </div>
        </div>
      )}

      {/* Prompt input */}
      <div className="mb-4">
        <textarea
          className="w-full border rounded-lg p-4 text-sm min-h-[120px] focus:ring-2 focus:ring-purple-400 focus:border-purple-400 outline-none"
          placeholder={datasetContext ? "Type your instructions or click Auto-Generate below..." : "Describe your workflow in natural language..."}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
      </div>

      {/* Example prompts */}
      {!datasetContext && (
        <div className="mb-4">
          <p className="text-xs text-gray-400 mb-2">Try an example:</p>
          <div className="flex flex-wrap gap-2">
            {EXAMPLE_PROMPTS.map((ex, i) => (
              <button
                key={i}
                onClick={() => setPrompt(ex)}
                className="text-xs bg-purple-50 text-purple-700 px-3 py-1 rounded-full hover:bg-purple-100 transition"
              >
                {ex.substring(0, 50)}...
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Generate button */}
      <div className="flex gap-3">
        <button
          onClick={handleGenerate}
          disabled={loading || (!prompt.trim() && !datasetContext)}
          className="bg-purple-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "⏳ Generating..." : datasetContext ? "✨ Auto-Generate Pipeline" : "✨ Generate Workflow"}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="mt-6 space-y-4">
          {/* Explanation */}
          <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
            <h3 className="font-semibold text-green-800 mb-1">✅ Workflow Generated</h3>
            <p className="text-sm text-green-700">{result.explanation}</p>
          </div>

          {/* Workflow name */}
          <div>
            <p className="text-xs text-gray-400">Workflow Name</p>
            <p className="font-bold text-lg">{result.name}</p>
          </div>

          {/* Node preview */}
          <div>
            <h3 className="font-semibold text-sm text-gray-500 uppercase tracking-wide mb-2">
              Generated Nodes ({result.nodes.length})
            </h3>
            <div className="flex flex-wrap gap-3">
              {result.nodes.map((node, i) => {
                const style = NODE_STYLES[node.type as NodeType] || NODE_STYLES.source;
                return (
                  <div
                    key={i}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg border-2"
                    style={{ borderColor: style.color, backgroundColor: style.bg }}
                  >
                    <span>{style.icon}</span>
                    <div>
                      <p className="text-sm font-medium" style={{ color: style.color }}>
                        {node.label || node.type}
                      </p>
                      {node.config && Object.keys(node.config).length > 0 && (
                        <p className="text-xs text-gray-500">
                          {Object.entries(node.config)
                            .map(([k, v]) => `${k}: ${v}`)
                            .join(", ")}
                        </p>
                      )}
                    </div>
                    {i < result.nodes.length - 1 && (
                      <span className="ml-2 text-gray-400">→</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={openInWorkflowBuilder}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
            >
              🏗️ Open in Workflow Builder
            </button>
            <button
              onClick={() => {
                setResult(null);
                setPrompt("");
              }}
              className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg text-sm hover:bg-gray-200 transition"
            >
              Start Over
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AIPageWrapper() {
  return (
    <Suspense fallback={<div className="p-8">Loading AI Generator...</div>}>
      <AIPage />
    </Suspense>
  );
}
