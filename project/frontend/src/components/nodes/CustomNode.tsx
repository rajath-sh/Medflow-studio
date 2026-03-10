"use client";

import React, { memo } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { NODE_STYLES, NodeType } from "@/lib/workflowSchema";

/**
 * Custom ReactFlow node component.
 * Color-coded by type with an icon, label, and connection handles.
 */
function CustomNode({ data }: NodeProps) {
    const nodeType = (data.nodeType as NodeType) || "source";
    const style = NODE_STYLES[nodeType] || NODE_STYLES.source;
    const label = data.label || style.label;

    return (
        <div
            style={{
                border: `2px solid ${style.color}`,
                backgroundColor: style.bg,
                borderRadius: "8px",
                padding: "10px 16px",
                minWidth: "140px",
                textAlign: "center",
                fontSize: "13px",
                fontWeight: 500,
                boxShadow: "0 1px 4px rgba(0,0,0,0.1)",
            }}
        >
            <Handle type="target" position={Position.Top} style={{ background: style.color }} />

            <div style={{ fontSize: "18px", marginBottom: "4px" }}>{style.icon}</div>
            <div style={{ color: style.color, fontWeight: 600 }}>{label}</div>
            {data.config && Object.keys(data.config).length > 0 && (
                <div style={{ fontSize: "11px", color: "#666", marginTop: "4px" }}>
                    {Object.entries(data.config).slice(0, 2).map(([k, v]) => (
                        <div key={k}>{k}: {String(v).substring(0, 20)}</div>
                    ))}
                </div>
            )}

            <Handle type="source" position={Position.Bottom} style={{ background: style.color }} />
        </div>
    );
}

export default memo(CustomNode);
