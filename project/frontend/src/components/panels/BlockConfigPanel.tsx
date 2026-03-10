"use client";

import { WorkflowNode, NodeType, NODE_STYLES } from "@/lib/workflowSchema";

type Props = {
  onAdd: (node: WorkflowNode) => void;
};

const NODE_TYPES: NodeType[] = [
  "source",
  "transform",
  "destination",
  "api_endpoint",
  "trigger",
];

export default function BlockConfigPanel({ onAdd }: Props) {
  return (
    <div className="space-y-3">
      <h3 className="font-bold text-sm text-gray-500 uppercase tracking-wide">
        Add Blocks
      </h3>

      {NODE_TYPES.map((nodeType) => {
        const style = NODE_STYLES[nodeType];
        return (
          <button
            key={nodeType}
            className="w-full text-left p-2 rounded-lg border-2 hover:shadow-md transition-shadow flex items-center gap-2"
            style={{
              borderColor: style.color,
              backgroundColor: style.bg,
            }}
            onClick={() =>
              onAdd({
                id: crypto.randomUUID(),
                type: nodeType,
                label: style.label,
                config: {},
              })
            }
          >
            <span className="text-lg">{style.icon}</span>
            <span className="font-medium text-sm" style={{ color: style.color }}>
              {style.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}
