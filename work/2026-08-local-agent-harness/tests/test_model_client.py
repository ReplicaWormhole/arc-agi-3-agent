import os
import sys
import unittest
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS))

from arc_agent.model_client import ChatMessage, ModelEndpointConfig, OpenAICompatibleChatModel


class ModelClientTests(unittest.TestCase):
    def test_payload_is_provider_neutral_openai_compatible_shape(self) -> None:
        client = OpenAICompatibleChatModel(
            ModelEndpointConfig("https://example.test/v1", "model-x")
        )
        self.assertEqual(
            client.request_payload([ChatMessage("user", "propose a hypothesis")]),
            {
                "model": "model-x",
                "messages": [{"role": "user", "content": "propose a hypothesis"}],
                "temperature": 0,
            },
        )

    def test_environment_configuration_requires_an_explicit_endpoint_and_model(self) -> None:
        previous = {
            name: os.environ.pop(name, None) for name in ("ARC_MODEL_BASE_URL", "ARC_MODEL_NAME")
        }
        try:
            with self.assertRaises(RuntimeError):
                ModelEndpointConfig.from_environment()
        finally:
            for name, value in previous.items():
                if value is not None:
                    os.environ[name] = value
