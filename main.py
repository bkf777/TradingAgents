from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Create a custom config
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openai"  # Use OpenAI
config["backend_url"] = "https://api.nuwaapi.com/v1/chat/completions"  # Use our configured backend
config["deep_think_llm"] = "o3-mini-high"  # Use OpenAI model
config["quick_think_llm"] = "o3-mini-high"  # Use OpenAI model
config["max_debate_rounds"] = 1  # Increase debate rounds
config["online_tools"] = True  # Use online tools

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
_, decision = ta.propagate("NVDA", "2025-06-10")
print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
