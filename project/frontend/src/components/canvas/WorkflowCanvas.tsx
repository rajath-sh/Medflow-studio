"use client";

import React, { useEffect, useMemo, useCallback } from "react";
import ReactFlow, {
  addEdge,
  Background,
  Controls,
  MiniMap,
  Connection,
  Edge,
  Node,
  useNodesState,
  useEdgesState,
} from "reactflow";
import "reactflow/dist/style.css";

import { Workflow, NODE_STYLES, NodeType } from "@/lib/workflowSchema";
import CustomNode from "@/components/nodes/CustomNode";

type Props = {
  workflow: Workflow;
  setWorkflow: (wf: Workflow) => void;
};

// Register custom node types — must be stable reference (outside component or useMemo)
const nodeTypes = { custom: CustomNode };

export default function WorkflowCanvas({ workflow, setWorkflow }: Props) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Sync workflow prop → ReactFlow state
  useEffect(() => {
    const newNodes: Node[] = workflow.nodes.map((n, i) => ({
      id: n.id,
      type: "custom",
      position: { x: 80 + (i % 3) * 220, y: 60 + Math.floor(i / 3) * 160 },
      data: {
        label: n.label || n.type,
        nodeType: n.type,
        config: n.config || {},
      },
    }));

    const newEdges: Edge[] = workflow.edges.map((e) => ({
      id: `${e.from}-${e.to}`,
      source: e.from,
      target: e.to,
      animated: true,
      style: { stroke: "#6b7280" },
    }));

    setNodes(newNodes);
    setEdges(newEdges);
  }, [workflow, setNodes, setEdges]);

  const onConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) return;

      const edge: Edge = {
        id: `${connection.source}-${connection.target}`,
        source: connection.source,
        target: connection.target,
        animated: true,
        style: { stroke: "#6b7280" },
      };

      setEdges((eds) => addEdge(edge, eds));

      setWorkflow({
        ...workflow,
        edges: [
          ...workflow.edges,
          { from: connection.source, to: connection.target },
        ],
      });
    },
    [workflow, setWorkflow, setEdges]
  );

  // MiniMap node color based on type
  const nodeColor = useCallback((node: Node) => {
    const nt = node.data?.nodeType as NodeType;
    return NODE_STYLES[nt]?.color || "#6b7280";
  }, []);

  return (
    <div style={{ width: "100%", height: "80vh" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        snapToGrid
        snapGrid={[20, 20]}
      >
        <MiniMap nodeColor={nodeColor} />
        <Controls />
        <Background gap={20} />
      </ReactFlow>
    </div>
  );
}
