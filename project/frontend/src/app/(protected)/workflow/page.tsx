"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Workflow, WorkflowNode } from "@/lib/workflowSchema";
import { useWorkflows, useSaveWorkflow, useDeleteWorkflow } from "@/hooks/useWorkflows";
import { api } from "@/lib/api";
import WorkflowCanvas from "@/components/canvas/WorkflowCanvas";
import BlockPanel from "@/components/panels/BlockConfigPanel";
import WorkflowSummary from "@/components/panels/WorkflowSummary";
import NodeConfigModal from "@/components/modals/NodeConfigModal";

export function WorkflowPage() {
  const searchParams = useSearchParams();
  const sourceFile = searchParams.get("source_file");

  const { data: savedWorkflows = [], isLoading } = useWorkflows();
  const saveMutation = useSaveWorkflow();
  const deleteMutation = useDeleteWorkflow();
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [editingNode, setEditingNode] = useState<WorkflowNode | null>(null);
  const [generating, setGenerating] = useState(false);
  const [executing, setExecuting] = useState(false);

  const handleDeleteWorkflow = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm("Are you sure you want to delete this workflow?")) {
      try {
        await deleteMutation.mutateAsync(id);
        if (workflow?.id === id) {
          setWorkflow(null);
        }
      } catch (err) {
        console.error("Failed to delete", err);
        alert("Failed to delete workflow");
      }
    }
  };

  // Load AI-generated workflow from sessionStorage (if navigating from AI page)
  useEffect(() => {
    const stored = sessionStorage.getItem("generated_workflow");
    if (stored) {
      try {
        const wf = JSON.parse(stored) as Workflow;
        setWorkflow(wf);
        sessionStorage.removeItem("generated_workflow");
        return; // Don't override with source_file if an AI workflow just generated
      } catch { }
    }

    // Auto-create a source node if navigating directly from a dataset
    if (sourceFile && !workflow) {
      setWorkflow({
        name: `Pipeline for ${sourceFile.split("/").pop()}`,
        nodes: [
          {
            id: "node-1",
            type: "source",
            label: "CSV Dataset",
            config: { source_type: "csv", file_path: sourceFile },
          } as any
        ],
        edges: []
      });
    }
  }, [sourceFile, workflow]);

  const loadWorkflow = (wf: any) => {
    try {
      let parsed = wf;
      if (typeof wf.definition === "string") {
        parsed = JSON.parse(wf.definition);
      } else if (wf.definition) {
        parsed = wf.definition;
      }

      // Ensure nodes and edges arrays exist (failsafe for old bad data)
      setWorkflow({
        ...parsed,
        id: wf.id,
        name: wf.name || "Untitled",
        nodes: Array.isArray(parsed.nodes) ? parsed.nodes : [],
        edges: Array.isArray(parsed.edges) ? parsed.edges : [],
      });
    } catch (e) {
      console.error("Failed to parse workflow definition:", e, wf);
      setWorkflow({ ...wf, nodes: [], edges: [] });
    }
  };

  const saveWorkflow = async () => {
    if (!workflow) return;
    try {
      const res = await saveMutation.mutateAsync({
        name: workflow.name || "Untitled Workflow",
        definition: JSON.parse(JSON.stringify(workflow)),
      });
      if (res && res.id) {
        setWorkflow({ ...workflow, id: res.id });
      }
      alert("Workflow saved ✅");
    } catch (err) {
      console.error("Failed to save workflow", err);
      alert("Failed to save workflow");
    }
  };

  const generateProject = async () => {
    if (!workflow) return;
    setGenerating(true);
    try {
      const res = await api.post(`/workflows/${workflow.id}/generate`);
      alert(`Project generated! ${res.data.message || "Download ready."}`);
    } catch (err) {
      console.error("Generation failed", err);
      alert("Project generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const executeWorkflow = async () => {
    if (!workflow?.id) {
      alert("Save the workflow first before executing.");
      return;
    }
    setExecuting(true);
    try {
      const res = await api.post(`/workflows/${workflow.id}/execute`);
      alert(`Job started! Job ID: ${res.data.job_id || res.data.id}`);
    } catch (err) {
      console.error("Execution failed", err);
      alert("Workflow execution failed");
    } finally {
      setExecuting(false);
    }
  };

  const handleNodeConfig = (node: WorkflowNode) => {
    setEditingNode(node);
  };

  const handleNodeSave = (updatedNode: WorkflowNode) => {
    if (!workflow) return;
    setWorkflow({
      ...workflow,
      nodes: workflow.nodes.map((n) =>
        n.id === updatedNode.id ? updatedNode : n
      ),
    });
    setEditingNode(null);
  };

  return (
    <div className="flex h-[calc(100vh-64px)]">
      {/* LEFT PANEL */}
      <div className="w-64 border-r p-4 bg-white overflow-y-auto">
        <h3 className="font-semibold text-sm text-gray-500 uppercase tracking-wide mb-3">
          Saved Workflows
        </h3>

        {isLoading && (
          <p className="text-sm text-gray-400">Loading...</p>
        )}

        {savedWorkflows.map((wf) => (
          <div
            key={wf.id}
            onClick={() => loadWorkflow(wf)}
            className="cursor-pointer p-2 hover:bg-blue-50 rounded text-sm border mb-1 flex justify-between items-center group"
          >
            <span className="truncate">{wf.name}</span>
            <button
              onClick={(e) => handleDeleteWorkflow(wf.id!, e)}
              className="text-red-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
              title="Delete Workflow"
            >
              ×
            </button>
          </div>
        ))}

        <button
          onClick={() =>
            setWorkflow({ name: "New Workflow", nodes: [], edges: [] })
          }
          className="mt-4 w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
        >
          + New Workflow
        </button>

        {/* Block palette */}
        {workflow && (
          <div className="mt-6">
            <BlockPanel
              onAdd={(node) =>
                setWorkflow({
                  ...workflow,
                  nodes: [...workflow.nodes, node],
                })
              }
            />
          </div>
        )}

        {/* Node list — click to configure */}
        {workflow && workflow.nodes.length > 0 && (
          <div className="mt-6">
            <h3 className="font-bold text-sm text-gray-500 uppercase tracking-wide mb-2">
              Nodes
            </h3>
            {workflow.nodes.map((node) => (
              <button
                key={node.id}
                onClick={() => handleNodeConfig(node)}
                className="w-full text-left p-2 rounded border mb-1 hover:bg-gray-50 text-sm"
              >
                {node.label || node.type}{" "}
                <span className="text-gray-400 text-xs">({node.type})</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* CANVAS */}
      <div className="flex-1 relative bg-gray-50">
        {workflow ? (
          <>
            <WorkflowCanvas workflow={workflow} setWorkflow={setWorkflow} />

            {/* Action buttons */}
            <div className="absolute bottom-4 right-4 flex gap-2">
              <button
                onClick={saveWorkflow}
                disabled={saveMutation.isPending}
                className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition disabled:opacity-50"
              >
                {saveMutation.isPending ? "Saving..." : "💾 Save"}
              </button>
              <button
                onClick={generateProject}
                disabled={generating}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-purple-700 transition disabled:opacity-50"
              >
                {generating ? "Generating..." : "⚡ Generate Project"}
              </button>
              <button
                onClick={executeWorkflow}
                disabled={executing}
                className="bg-orange-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-orange-700 transition disabled:opacity-50"
              >
                {executing ? "Running..." : "🚀 Execute"}
              </button>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <p className="text-4xl mb-2">🏗️</p>
              <p className="text-lg font-medium">Select or create a workflow</p>
              <p className="text-sm">
                Use the left panel to get started
              </p>
            </div>
          </div>
        )}
      </div>

      {/* RIGHT PANEL */}
      <div className="w-72 border-l p-4 bg-white overflow-y-auto">
        {workflow && <WorkflowSummary workflow={workflow} />}
      </div>

      {/* Node Config Modal */}
      {editingNode && (
        <NodeConfigModal
          node={editingNode}
          onSave={handleNodeSave}
          onClose={() => setEditingNode(null)}
        />
      )}
    </div>
  );
}

import { Suspense } from "react";
export default function WorkflowPageWrapper() {
  return (
    <Suspense fallback={<div className="p-8">Loading Workflow Designer...</div>}>
      <WorkflowPage />
    </Suspense>
  );
}
