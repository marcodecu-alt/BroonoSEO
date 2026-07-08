from langgraph.graph import StateGraph, END

from .state import PipelineState
from .nodes import research_node, propose_node, draft_node, review_node


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
    # review_node runs once and always hands off to the human, it never loops
    # back to draft_node on its own. A human comment is the only thing that
    # triggers another draft->review pass (see build_resume_graph).
    graph.add_edge("review_node", END)

    return graph.compile()


def build_resume_graph():
    """Entry point at draft_node only, for resuming after a human comment."""
    graph = StateGraph(PipelineState)

    graph.add_node("draft_node", draft_node)
    graph.add_node("review_node", review_node)

    graph.set_entry_point("draft_node")
    graph.add_edge("draft_node", "review_node")
    graph.add_edge("review_node", END)

    return graph.compile()


pipeline_graph = build_graph()
resume_pipeline_graph = build_resume_graph()
