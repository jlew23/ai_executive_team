# LLM Provider Settings
LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'openai')  # 'openai', 'local', or 'anthropic'
LLM_MODEL = os.environ.get('LLM_MODEL', 'gpt-3.5-turbo')  # model name depends on provider
LOCAL_MODEL_PATH = os.environ.get('LOCAL_MODEL_PATH', 'C:/Users/Luda/.lmstudio/models/Llama-3-WhiteRabbitNeo-8B-v2.0.Q4_K_M/Llama-3-WhiteRabbitNeo-8B-v2.0.Q4_K_M.gguf')