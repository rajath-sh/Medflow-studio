"use client";

import { Workflow, NODE_STYLES, NodeType } from "@/lib/workflowSchema";

type Props = {
  workflow: Workflow;
};

export default function WorkflowSummary({ workflow }: Props) {
  const nodeCount = workflow.nodes.length;
  const edgeCount = workflow.edges.length;

  // Count by type safely
  const typeCounts: Partial<Record<string, number>> = {};
  workflow.nodes?.forEach((n) => {
    if (!n) return;
    const t = n.type || "unknown";
    typeCounts[t] = (typeCounts[t] || 0) + 1;
  });

  return (
    <div className="space-y-4">
      <h3 className="font-bold text-sm text-gray-500 uppercase tracking-wide">
        Workflow Summary
      </h3>

      {/* Name */}
      <div>
        <p className="text-xs text-gray-400">Name</p>
        <p className="font-semibold">{workflow.name}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-blue-50 p-2 rounded text-center">
          <p className="text-xl font-bold text-blue-600">{nodeCount}</p>
          <p className="text-xs text-gray-500">Nodes</p>
        </div>
        <div className="bg-gray-100 p-2 rounded text-center">
          <p className="text-xl font-bold text-gray-600">{edgeCount}</p>
          <p className="text-xs text-gray-500">Edges</p>
        </div>
      </div>

      {/* Node breakdown */}
      {Object.entries(typeCounts).map(([type, count]) => {
        const style = NODE_STYLES[type as NodeType] || {
          color: "#6b7280",
          bg: "#f3f4f6",
          icon: "❓",
          label: type,
        };
        return (
          <div
            key={type}
            className="flex items-center gap-2 p-2 rounded"
            style={{ backgroundColor: style.bg }}
          >
            <span>{style.icon}</span>
            <span className="text-sm font-medium" style={{ color: style.color }}>
              {style.label}
            </span>
            <span className="ml-auto text-sm font-bold" style={{ color: style.color }}>
              {count}
            </span>
          </div>
        );
      })}

      {/* JSON preview */}
      <details className="mt-2">
        <summary className="text-xs text-gray-400 cursor-pointer">
          View raw JSON
        </summary>
        <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto mt-1 max-h-60">
          {JSON.stringify(workflow, null, 2)}
        </pre>
      </details>
    </div>
  );
}
