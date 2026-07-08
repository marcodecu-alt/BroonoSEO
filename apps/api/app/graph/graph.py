from langgraph.graph import StateGraph, END

from .state import PipelineState
from .nodes import research_node, propose_node, draft_node, review_node, review_router


def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("research_node", research_node)
    graph.add_node("propose_node", propose_node)
    graph.add_node("draft_node", draft_node)
    graph.add_node("review_node", review_node)

    graph.set_entry_point("research_node")
    graph.add_edge("research_node", "propose_node")
    graph.add_edge("propose_node", "draft_node")
    graph.add_edge("draft_node", "review_node")
    graph.add_conditional_edges(
        "review_node",
        review_router,
        {
            "draft_node": "draft_node",
            "awaiting_human_approval": END,
        },
    )

    return graph.compile()


pipeline_graph = build_graph()
