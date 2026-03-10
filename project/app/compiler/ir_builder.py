class Node:
    def __init__(self, node_id: str, node_type: str, config: dict):
        self.id = node_id
        self.type = node_type
        self.config = config

    def __repr__(self):
        return f"Node(id={self.id}, type={self.type})"


class Edge:
    def __init__(self, from_node: str, to_node: str):
        self.from_node = from_node
        self.to_node = to_node

    def __repr__(self):
        return f"Edge(from={self.from_node}, to={self.to_node})"


class Workflow:
    def __init__(self, name: str, nodes: list, edges: list, metadata: dict = None):
        self.name = name
        self.nodes = nodes
        self.edges = edges
        self.metadata = metadata or {}
        # Will be populated by classifier
        self.workflow_type = "unknown" 

    def __repr__(self):
        return f"Workflow(name={self.name}, type={self.workflow_type}, nodes={len(self.nodes)}, edges={len(self.edges)})"


def build_ir(workflow_dict: dict) -> Workflow:
    nodes = []
    edges = []

    for node in workflow_dict.get("nodes", []):
        nodes.append(
            Node(
                node_id=node.get("id"),
                node_type=node.get("type"),
                config=node.get("config", {})
            )
        )

    for edge in workflow_dict.get("edges", []):
        # Handle both ReactFlow and DB schema keys
        from_id = edge.get("source") or edge.get("source_node_id") or edge.get("from")
        to_id = edge.get("target") or edge.get("target_node_id") or edge.get("to")
        if from_id and to_id:
            edges.append(Edge(from_node=from_id, to_node=to_id))

    workflow = Workflow(
        name=workflow_dict.get("name") or workflow_dict.get("workflow_name") or "generated_app",
        nodes=nodes,
        edges=edges,
        metadata=workflow_dict.get("metadata", {})
    )

    return workflow
