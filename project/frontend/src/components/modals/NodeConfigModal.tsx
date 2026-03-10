"use client";

import { useState, useEffect } from "react";
import { WorkflowNode, NodeType, NODE_STYLES } from "@/lib/workflowSchema";

type Props = {
    node: WorkflowNode;
    onSave: (node: WorkflowNode) => void;
    onClose: () => void;
};

// ── Config fields per node type ──────────────────────────
const CONFIG_FIELDS: Record<NodeType, { key: string; label: string; type: string; placeholder: string }[]> = {
    source: [
        { key: "source_type", label: "Source Type", type: "select", placeholder: "csv|database|api" },
        { key: "path", label: "File Path / URL", type: "text", placeholder: "/data/patients.csv" },
        { key: "format", label: "Format", type: "select", placeholder: "csv|json|parquet" },
    ],
    transform: [
        { key: "operation", label: "Operation", type: "select", placeholder: "filter|map|validate|aggregate|join|hl7_parse|unit_convert|lab_flag" },
        { key: "expression", label: "Expression", type: "text", placeholder: "age > 18" },
        { key: "field", label: "Target Field", type: "text", placeholder: "blood_pressure" },
    ],
    destination: [
        { key: "destination_type", label: "Destination", type: "select", placeholder: "database|file|api" },
        { key: "table", label: "Table / Path", type: "text", placeholder: "patients" },
        { key: "mode", label: "Write Mode", type: "select", placeholder: "append|overwrite|upsert" },
    ],
    api_endpoint: [
        { key: "method", label: "HTTP Method", type: "select", placeholder: "GET|POST|PUT|DELETE" },
        { key: "route", label: "Route", type: "text", placeholder: "/api/patients" },
        { key: "auth", label: "Auth Required", type: "select", placeholder: "true|false" },
    ],
    trigger: [
        { key: "trigger_type", label: "Trigger Type", type: "select", placeholder: "cron|webhook|manual" },
        { key: "schedule", label: "Schedule (cron)", type: "text", placeholder: "0 */6 * * *" },
    ],
};

export default function NodeConfigModal({ node, onSave, onClose }: Props) {
    const style = NODE_STYLES[node.type];
    const fields = CONFIG_FIELDS[node.type] || [];
    const [config, setConfig] = useState<Record<string, string>>(
        (node.config as Record<string, string>) || {}
    );
    const [label, setLabel] = useState(node.label || style.label);

    const handleSave = () => {
        onSave({ ...node, label, config });
    };

    return (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
            <div
                className="bg-white rounded-xl shadow-2xl p-6 w-[420px] max-h-[80vh] overflow-y-auto"
                style={{ borderTop: `4px solid ${style.color}` }}
            >
                {/* Header */}
                <div className="flex items-center gap-2 mb-4">
                    <span className="text-2xl">{style.icon}</span>
                    <h2 className="text-lg font-bold" style={{ color: style.color }}>
                        Configure {style.label}
                    </h2>
                </div>

                {/* Label field */}
                <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Label
                    </label>
                    <input
                        type="text"
                        className="w-full border rounded-lg p-2 text-sm"
                        value={label}
                        onChange={(e) => setLabel(e.target.value)}
                    />
                </div>

                {/* Config fields */}
                {fields.map((field) => (
                    <div key={field.key} className="mb-3">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            {field.label}
                        </label>
                        {field.type === "select" ? (
                            <select
                                className="w-full border rounded-lg p-2 text-sm"
                                value={config[field.key] || ""}
                                onChange={(e) =>
                                    setConfig({ ...config, [field.key]: e.target.value })
                                }
                            >
                                <option value="">Select...</option>
                                {field.placeholder.split("|").map((opt) => (
                                    <option key={opt} value={opt}>
                                        {opt}
                                    </option>
                                ))}
                            </select>
                        ) : (
                            <input
                                type="text"
                                className="w-full border rounded-lg p-2 text-sm"
                                placeholder={field.placeholder}
                                value={config[field.key] || ""}
                                onChange={(e) =>
                                    setConfig({ ...config, [field.key]: e.target.value })
                                }
                            />
                        )}
                    </div>
                ))}

                {/* Actions */}
                <div className="flex justify-end gap-2 mt-6">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm rounded-lg border hover:bg-gray-50"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        className="px-4 py-2 text-sm rounded-lg text-white font-medium"
                        style={{ backgroundColor: style.color }}
                    >
                        Save
                    </button>
                </div>
            </div>
        </div>
    );
}
