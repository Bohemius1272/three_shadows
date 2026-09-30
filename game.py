from dataclasses import dataclass, field
from typing import Dict, List, Optional
import random


@dataclass
class Player:
    key: str
    name: str
    is_ai: bool = False
    role: Optional[str] = None

# dataclass stuff
@dataclass
class GameState:
    players: Dict[str, Player] = field(default_factory=dict)
    started: bool = False
    round_number: int = 0
    votes: Dict[str, str] = field(default_factory=dict)
    discussion: List[str] = field(default_factory=list)
    eliminated: Optional[str] = None

    def reset(self):
        self.players.clear()
        self.started = False
        self.round_number = 0
        self.votes.clear()
        self.discussion.clear()
        self.eliminated = None

    def add_human(self, key: str, name: str) -> bool:
        if self.started or len(self.players) >= 2:
            return False
        if key in self.players:
            return False
        self.players[key] = Player(key=key, name=name)
        return True

    def add_ai(self, key: str, name: str):
        self.players[key] = Player(key=key, name=name, is_ai=True)
# The amount of players that are required to start the game
    def start(self, ai_key: str, ai_name: str):
        if len(self.players) != 2:
            raise ValueError("Exactly two human players are required.")
        self.add_ai(ai_key, ai_name)

        roles = ["Shadow", "Investigator", "Investigator"]
        random.shuffle(roles)

        for player, role in zip(self.players.values(), roles):
            player.role = role

        self.started = True
        self.round_number = 1
        self.votes.clear()

    def public_players(self) -> List[str]:
        return [p.name for p in self.players.values()]

    def player_by_name(self, name: str) -> Optional[Player]:
        lowered = name.lower()
        for p in self.players.values():
            if p.name.lower() == lowered:
                return p
        return None

    def add_discussion(self, speaker: str, message: str):
        self.discussion.append(f"{speaker}: {message}")
        # Keep the context bounded.
        self.discussion = self.discussion[-30:]

    def cast_vote(self, voter_key: str, target_key: str):
        if not self.started:
            raise ValueError("The game has not started.")
        if voter_key not in self.players:
            raise ValueError("You are not a player.")
        if target_key not in self.players:
            raise ValueError("That player does not exist.")
        if voter_key == target_key:
            raise ValueError("You cannot vote for yourself.")
        self.votes[voter_key] = target_key

    def all_voted(self) -> bool:
        return len(self.votes) == len(self.players)

    def tally(self) -> Dict[str, int]:
        result = {key: 0 for key in self.players}
        for target in self.votes.values():
            result[target] += 1
        return result

    def resolve_vote(self):
        if not self.all_voted():
            return None

        tally = self.tally()
        highest = max(tally.values())
        leaders = [key for key, count in tally.items() if count == highest]

        if len(leaders) > 1:
            self.round_number += 1
            self.votes.clear()
            return {"type": "tie", "tally": tally}

        eliminated_key = leaders[0]
        self.eliminated = eliminated_key
        eliminated = self.players[eliminated_key]

        winner = "Investigators" if eliminated.role == "Shadow" else "Shadow"
        return {
            "type": "win",
            "tally": tally,
            "eliminated": eliminated_key,
            "winner": winner,
            "role": eliminated.role,
        }

    def ai_player(self) -> Player:
        return next(p for p in self.players.values() if p.is_ai)
# Lines 124-135 display the status and rules of the game
    def ai_private_context(self) -> str:
        ai = self.ai_player()
        return f"""
You are playing Three Shadows as {ai.name}.
Your secret role is: {ai.role}. 

Rules:              
- There are three players.
- One player is the Shadow.
- Investigators win if the Shadow is eliminated.
- The Shadow wins if an Investigator is eliminated.
- You must protect your own win condition.
- Never reveal your secret role unless you intentionally choose to bluff about it.
- You cannot invent players or change the rules.
- The Python game engine determines the actual winner.

Public players:
{", ".join(self.public_players())} 

Recent public discussion:
{chr(10).join(self.discussion[-20:]) or "(No discussion yet)"}

Current round:
{self.round_number}
""".strip()
