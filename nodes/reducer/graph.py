"""
Reducer subgraph: merge_content -> decide_images -> generate_and_place_images
"""
from langgraph.graph import END, START, StateGraph

from nodes.reducer.decide_images import decide_images
from nodes.reducer.generate_images import generate_and_place_images
from nodes.reducer.merge_content import merge_content
from state import State


def build_reducer_subgraph():
    reducer_graph = StateGraph(State)
    reducer_graph.add_node("merge_content", merge_content)
    reducer_graph.add_node("decide_images", decide_images)
    reducer_graph.add_node("generate_and_place_images", generate_and_place_images)

    reducer_graph.add_edge(START, "merge_content")
    reducer_graph.add_edge("merge_content", "decide_images")
    reducer_graph.add_edge("decide_images", "generate_and_place_images")
    reducer_graph.add_edge("generate_and_place_images", END)

    return reducer_graph.compile()
