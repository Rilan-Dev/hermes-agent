# AI Provider Capability Inventory

Provider identities remain separate until explicit compatibility rules map them.

| Registry | Count | Identifiers |
| --- | --- | --- |
| Provider profiles | 36 | alibaba, alibaba-coding-plan, anthropic, arcee, azure-foundry, bedrock, copilot, copilot-acp, custom, deepinfra, deepseek, fireworks, gemini, gmi, huggingface, kilocode, kimi-coding, kimi-coding-cn, minimax, minimax-cn, minimax-oauth, nous, novita, nvidia, ollama-cloud, openai-codex, opencode-go, opencode-zen, openrouter, qwen-oauth, stepfun, upstage, vertex, xai, xiaomi, zai |
| Profile aliases | 89 | alibaba-cloud → alibaba, alibaba-coding → alibaba-coding-plan, alibaba_coding → alibaba-coding-plan, amazon → bedrock, amazon-bedrock → bedrock, arcee-ai → arcee, arceeai → arcee, aws → bedrock, aws-bedrock → bedrock, azure → azure-foundry, azure-ai → azure-foundry, azure-ai-foundry → azure-foundry, claude → anthropic, claude-code → anthropic, claude-oauth → anthropic, codex → openai-codex, copilot-acp-agent → copilot-acp, dashscope → alibaba, dashscope-coding → alibaba-coding-plan, deep-infra → deepinfra, deepinfra-ai → deepinfra, deepseek-chat → deepseek, fireworks-ai → fireworks, fw → fireworks, gcp-vertex → vertex, github → copilot, github-copilot → copilot, github-copilot-acp → copilot-acp, github-model → copilot, github-models → copilot, glm → zai, gmi-cloud → gmi, gmicloud → gmi, go → opencode-go, google → gemini, google-ai-studio → gemini, google-gemini → gemini, google-vertex → vertex, grok → xai, hf → huggingface, hugging-face → huggingface, huggingface-hub → huggingface, kilo → kilocode, kilo-code → kilocode, kilo-gateway → kilocode, kimi → kimi-coding, kimi-cn → kimi-coding-cn, kimi-for-coding → kimi-coding, llama-cpp → custom, llama.cpp → custom, llamacpp → custom, local → custom, mimo → xiaomi, mini-max → minimax, minimax-china → minimax-cn, minimax-oauth-io → minimax-oauth, minimax_cn → minimax-cn, minimax_oauth → minimax-oauth, moonshot → kimi-coding, moonshot-cn → kimi-coding-cn, nous-portal → nous, nousresearch → nous, novita-ai → novita, novitaai → novita, nvidia-nim → nvidia, ollama → custom, ollama_cloud → ollama-cloud, openai_codex → openai-codex, opencode → opencode-zen, opencode-go-sub → opencode-go, opencode_go → opencode-go, opencode_zen → opencode-zen, or → openrouter, qwen → qwen-oauth, qwen-cli → qwen-oauth, qwen-dashscope → alibaba, qwen-portal → qwen-oauth, solar → upstage, step → stepfun, stepfun-coding-plan → stepfun, vertex-ai → vertex, vllm → custom, x-ai → xai, x.ai → xai, xiaomi-mimo → xiaomi, z-ai → zai, z.ai → zai, zen → opencode-zen, zhipu → zai |
| Auth registry | 44 | alibaba, alibaba-coding-plan, anthropic, arcee, azure-foundry, bedrock, copilot, copilot-acp, deep-infra, deepinfra, deepinfra-ai, deepseek, fireworks, fireworks-ai, fw, gemini, gmi, huggingface, kilocode, kimi-coding, kimi-coding-cn, lmstudio, minimax, minimax-cn, minimax-oauth, nous, novita, novita-ai, novitaai, nvidia, ollama-cloud, openai-api, openai-codex, opencode-go, opencode-zen, qwen-oauth, solar, stepfun, tencent-tokenhub, upstage, xai, xai-oauth, xiaomi, zai |
| Canonical catalog | 41 | alibaba, alibaba-coding-plan, anthropic, arcee, azure-foundry, bedrock, copilot, copilot-acp, custom, deepinfra, deepseek, fireworks, gemini, gmi, huggingface, kilocode, kimi-coding, kimi-coding-cn, lmstudio, minimax, minimax-cn, minimax-oauth, moa, nous, novita, nvidia, ollama-cloud, openai-api, openai-codex, opencode-go, opencode-zen, openrouter, qwen-oauth, stepfun, tencent-tokenhub, upstage, vertex, xai, xai-oauth, xiaomi, zai |
| Model catalog keys | 34 | alibaba, alibaba-coding-plan, anthropic, arcee, azure-foundry, bedrock, copilot, copilot-acp, deepseek, gemini, gmi, huggingface, kilocode, kimi-coding, kimi-coding-cn, minimax, minimax-cn, minimax-oauth, moa, moonshot, nous, novita, nvidia, openai, openai-api, openai-codex, opencode-go, opencode-zen, stepfun, tencent-tokenhub, xai, xai-oauth, xiaomi, zai |
| Transport API modes | 4 | anthropic_messages, bedrock_converse, chat_completions, codex_responses |

## Tool-specific provider families

| Family | Built-in | Plugin | Combined |
| --- | --- | --- | --- |
| browser | — | browser-use, browserbase, firecrawl | browser-use, browserbase, firecrawl |
| image_gen | — | deepinfra, fal, krea, nous, openai, openai-codex, openrouter, xai | deepinfra, fal, krea, nous, openai, openai-codex, openrouter, xai |
| stt | deepinfra, elevenlabs, groq, local, local_command, mistral, openai, xai | — | deepinfra, elevenlabs, groq, local, local_command, mistral, openai, xai |
| tts | deepinfra, edge, elevenlabs, gemini, kittentts, minimax, mistral, neutts, openai, piper, xai | — | deepinfra, edge, elevenlabs, gemini, kittentts, minimax, mistral, neutts, openai, piper, xai |
| video_gen | — | deepinfra, fal, xai | deepinfra, fal, xai |
| web | — | brave-free, ddgs, exa, firecrawl, parallel, searxng, tavily, xai | brave-free, ddgs, exa, firecrawl, parallel, searxng, tavily, xai |

## Cross-registry membership

| ID | Profile | Auth | Canonical | Models |
| --- | --- | --- | --- | --- |
| alibaba | yes | yes | yes | yes |
| alibaba-coding-plan | yes | yes | yes | yes |
| anthropic | yes | yes | yes | yes |
| arcee | yes | yes | yes | yes |
| azure-foundry | yes | yes | yes | yes |
| bedrock | yes | yes | yes | yes |
| copilot | yes | yes | yes | yes |
| copilot-acp | yes | yes | yes | yes |
| custom | yes |  | yes |  |
| deep-infra |  | yes |  |  |
| deepinfra | yes | yes | yes |  |
| deepinfra-ai |  | yes |  |  |
| deepseek | yes | yes | yes | yes |
| fireworks | yes | yes | yes |  |
| fireworks-ai |  | yes |  |  |
| fw |  | yes |  |  |
| gemini | yes | yes | yes | yes |
| gmi | yes | yes | yes | yes |
| huggingface | yes | yes | yes | yes |
| kilocode | yes | yes | yes | yes |
| kimi-coding | yes | yes | yes | yes |
| kimi-coding-cn | yes | yes | yes | yes |
| lmstudio |  | yes | yes |  |
| minimax | yes | yes | yes | yes |
| minimax-cn | yes | yes | yes | yes |
| minimax-oauth | yes | yes | yes | yes |
| moa |  |  | yes | yes |
| moonshot |  |  |  | yes |
| nous | yes | yes | yes | yes |
| novita | yes | yes | yes | yes |
| novita-ai |  | yes |  |  |
| novitaai |  | yes |  |  |
| nvidia | yes | yes | yes | yes |
| ollama-cloud | yes | yes | yes |  |
| openai |  |  |  | yes |
| openai-api |  | yes | yes | yes |
| openai-codex | yes | yes | yes | yes |
| opencode-go | yes | yes | yes | yes |
| opencode-zen | yes | yes | yes | yes |
| openrouter | yes |  | yes |  |
| qwen-oauth | yes | yes | yes |  |
| solar |  | yes |  |  |
| stepfun | yes | yes | yes | yes |
| tencent-tokenhub |  | yes | yes | yes |
| upstage | yes | yes | yes |  |
| vertex | yes |  | yes |  |
| xai | yes | yes | yes | yes |
| xai-oauth |  | yes | yes | yes |
| xiaomi | yes | yes | yes | yes |
| zai | yes | yes | yes | yes |
