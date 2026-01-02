# Anthropic (Claude) environment keys

This repo can use Anthropic via the `anthropic` provider.

Add these keys to your local `.env` / `.env.example`:

- `ANTHROPIC_API_KEY`: API key (required)
- `ANTHROPIC_API_BASE`: Base URL (optional, default `https://api.anthropic.com`)
- `ANTHROPIC_MODEL`: Model name (optional, default `claude-3-5-sonnet-20241022`)
- `ANTHROPIC_VERSION`: Request header value for `anthropic-version` (optional, default `2023-06-01`)
- `ANTHROPIC_BETA`: Optional request header value for `anthropic-beta` (leave unset unless needed)

To use Anthropic as the primary backend:

- `BROCA_LLM_PROVIDER=anthropic`


