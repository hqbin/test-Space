import hashlib
from collections import deque
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class TVState:
    activity: str
    focused_id: str
    focused_desc: str
    focused_text: str
    focusable_ids: frozenset[str]
    screenshot_hash: str

    def fingerprint(self) -> str:
        sorted_ids = sorted(self.focusable_ids)
        raw = f"{self.activity}|{self.focused_id}|{','.join(sorted_ids)}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def to_json(self) -> dict[str, Any]:
        return {
            "activity": self.activity,
            "focused_id": self.focused_id,
            "focused_desc": self.focused_desc,
            "focused_text": self.focused_text,
            "focusable_ids": list(self.focusable_ids),
            "screenshot_hash": self.screenshot_hash,
            "fingerprint": self.fingerprint(),
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "TVState":
        return cls(
            activity=data["activity"],
            focused_id=data["focused_id"],
            focused_desc=data["focused_desc"],
            focused_text=data["focused_text"],
            focusable_ids=frozenset(data.get("focusable_ids", [])),
            screenshot_hash=data["screenshot_hash"],
        )


class StateGraph:
    def __init__(
        self,
        nodes: Optional[dict[str, TVState]] = None,
        edges: Optional[dict[tuple[str, str], str]] = None,
    ) -> None:
        self.nodes: dict[str, TVState] = nodes if nodes is not None else {}
        self.edges: dict[tuple[str, str], str] = edges if edges is not None else {}

    def add_state(self, state: TVState) -> bool:
        fp = state.fingerprint()
        if fp not in self.nodes:
            self.nodes[fp] = state
            return True
        return False

    def add_transition(self, from_fp: str, to_fp: str, key: str) -> None:
        self.edges[(from_fp, to_fp)] = key

    def find_path(self, from_fp: str, to_fp: str) -> list[str]:
        if from_fp == to_fp:
            return []

        queue: deque[tuple[str, list[str]]] = deque()
        queue.append((from_fp, []))
        visited: set[str] = {from_fp}

        while queue:
            current_fp, path = queue.popleft()
            for (src, dst), key in self.edges.items():
                if src == current_fp and dst not in visited:
                    new_path = path + [key]
                    if dst == to_fp:
                        return new_path
                    visited.add(dst)
                    queue.append((dst, new_path))
        return []

    def find_all_paths(self, from_fp: str, to_fp: str, max_depth: int = 20) -> list[list[str]]:
        results: list[list[str]] = []
        queue: deque[tuple[str, list[str], set[str]]] = deque()
        queue.append((from_fp, [], {from_fp}))

        while queue:
            current_fp, path, visited = queue.popleft()
            if len(path) > max_depth:
                continue
            for (src, dst), key in self.edges.items():
                if src == current_fp and dst not in visited:
                    new_path = path + [key]
                    if dst == to_fp:
                        results.append(new_path)
                    else:
                        new_visited = visited | {dst}
                        queue.append((dst, new_path, new_visited))
        return results

    def to_json(self) -> dict[str, Any]:
        edges_list: list[dict[str, str]] = []
        for (src, dst), key in self.edges.items():
            edges_list.append({"from": src, "to": dst, "key": key})
        nodes_dict: dict[str, dict[str, Any]] = {}
        for fp, state in self.nodes.items():
            nodes_dict[fp] = state.to_json()
        return {
            "nodes": nodes_dict,
            "edges": edges_list,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "StateGraph":
        nodes: dict[str, TVState] = {}
        for fp, node_data in data.get("nodes", {}).items():
            nodes[fp] = TVState.from_json(node_data)
        edges: dict[tuple[str, str], str] = {}
        for edge_data in data.get("edges", []):
            src = edge_data["from"]
            dst = edge_data["to"]
            key = edge_data["key"]
            edges[(src, dst)] = key
        return cls(nodes=nodes, edges=edges)
