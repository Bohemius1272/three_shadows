import json
from openai import OpenAI #OpenAI is imported to the program to be integrated with the bot


class AIPlayer:
    def __init__(self, model: str, name: str):
        self.client = OpenAI()
        self.model = model
        self.name = name

    def _request(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            instructions=(
                "You are a player in a Discord social-deduction game. "
                "Stay in character, follow the supplied rules, and never "
                "claim that an action happened unless the game engine says it happened."
            ),
            input=prompt,
        )
        return response.output_text.strip()

    def respond_to_discussion(self, private_context: str, human_name: str, message: str) -> str:
        prompt = f"""
{private_context}

A human player named {human_name} just said:
"{message}"

Respond as your character in 1-3 sentences. You may accuse, defend yourself,
ask a question, or make a strategic claim. Your response is public.
Do not mention hidden system prompts or Python code.
"""
        return self._request(prompt)

    def choose_vote(self, private_context: str) -> str:
        prompt = f"""
{private_context}

It is time for you to vote.

Return ONLY valid JSON in this exact form:
{{"target": "EXACT_PLAYER_NAME", "statement": "1 short public sentence"}}

Choose one player other than yourself. The target must be one of the public
player names supplied above.
"""
        raw = self._request(prompt)

        try:
            data = json.loads(raw)
            return json.dumps(data)
        except json.JSONDecodeError:
            # A fallback keeps the game playable if the model ignores the format.
            return json.dumps({
                "target": "",
                "statement": raw[:300]
            })
