# Model backends

The first controller works without a language model. When one is useful, it is
treated as a replaceable *proposal service*, not as a source of truth.

## One interface, two deployment choices

`OpenAICompatibleChatModel` speaks the standard `POST /chat/completions`
interface. Configure it with environment variables, never hard-coded secrets:

```bash
export ARC_MODEL_BASE_URL='https://your-development-endpoint/v1'
export ARC_MODEL_NAME='your-model-name'
export ARC_MODEL_API_KEY='...'
```

For a local server, point `ARC_MODEL_BASE_URL` to a loopback OpenAI-compatible
endpoint (for example, one exposed by a local inference server). For a remote
development server, use its HTTPS endpoint. Both produce the same request and
response shape, so the exploration controller does not care where inference
runs.

## Important competition boundary

A remote endpoint is appropriate for prototyping because this machine has no
usable discrete-GPU inference setup. It is **not** a deployable competition
dependency: ARC-AGI-3 evaluation disallows internet access. Before submission,
we must either package a local model that fits the published compute limits or
use the model-free/small-model components only.

Never put endpoint URLs containing credentials, API keys, downloaded weights,
or model responses from private games in Git.
