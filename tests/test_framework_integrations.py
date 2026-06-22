import asyncio
from pathlib import Path

from google.adk.agents import LlmAgent
from langchain_core.tools import StructuredTool

from src.adk.agents import root_agent as adk_root_agent
from src.integrations.langchain_tools import LANGCHAIN_TOOLS
from src.rag.langchain_rag import get_rag_chain
from src.services.mcp_backend.client import call_tool_async


def test_google_adk_root_is_real_multi_agent_tree():
    assert isinstance(adk_root_agent, LlmAgent)
    assert {agent.name for agent in adk_root_agent.sub_agents} == {
        "ecombot_support_agent",
        "ecombot_sales_agent",
    }


def test_langchain_structured_tools_are_registered():
    assert all(isinstance(tool, StructuredTool) for tool in LANGCHAIN_TOOLS)
    assert {tool.name for tool in LANGCHAIN_TOOLS} >= {
        "get_order_status",
        "lookup_product",
        "search_ecombot_knowledge",
    }


def test_langchain_chroma_retrieves_grounded_product():
    results = get_rag_chain().search("Samsung Galaxy M35 battery", 3)
    assert any(item["source"] == "PHONE-M35" for item in results)


def test_fastmcp_client_executes_real_tool():
    result = asyncio.run(call_tool_async("mcp_get_order_status", {"order_id": "ORD-001"}))
    assert result["ok"] is True
    assert result["status"] == "Shipped"


def test_promptfoo_suite_has_minimum_10_cases():
    config = Path("evals/promptfooconfig.yaml").read_text(encoding="utf-8")
    assert config.count("- vars:") >= 10
    assert "providers:" in config
    assert "http" in config
