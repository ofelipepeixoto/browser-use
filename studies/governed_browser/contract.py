"""Offline contract study. No browser, model, HTTP or MCP transport is imported."""

import hashlib
import json
import secrets
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Schema(BaseModel):
	model_config = ConfigDict(extra='forbid', strict=True, frozen=True)


class Proposal(Schema):
	job_id: str = Field(pattern=r'^[a-z0-9-]{1,40}$')
	action: Literal['read_fixture', 'submit_fixture']
	url: str
	units: int = Field(ge=0, le=100)

	@field_validator('url')
	@classmethod
	def fixture_url(cls, value: str) -> str:
		"""Only exact synthetic origins/paths, without credentials or query data."""
		parsed = urlsplit(value)
		if value not in ('https://fixture.test/page', 'https://fixture.test/fail'):
			raise ValueError('fixture URL required')
		if parsed.username or parsed.password or parsed.query or parsed.fragment:
			raise ValueError('URL data forbidden')
		return value

	def digest(self) -> str:
		return hashlib.sha256(json.dumps(self.model_dump(), sort_keys=True).encode()).hexdigest()


class Receipt(Schema):
	job_id: str
	proposal_hash: str
	status: Literal['completed', 'uncertain']
	reserved_units: int
	reviewer: Literal['fixture-human'] | None = None


class OfflineStudy:
	"""Single-process synthetic approval, budget and replay state; not an authenticator.

	No injectable executor exists: even an approved consequential action is a fixture.
	State is in memory, not distributed, durable, thread-safe or production-ready.
	"""

	def __init__(self, budget: int = 3, max_steps: int = 2) -> None:
		if type(budget) is not int or budget < 0 or type(max_steps) is not int or max_steps < 1:
			raise ValueError('invalid limits')
		self.remaining = budget
		self.max_steps = max_steps
		self.receipts: dict[str, Receipt] = {}
		self._grants: dict[str, tuple[str, int]] = {}

	@staticmethod
	def browser_configuration() -> dict:
		"""Configuration proposal only: never instantiate a Browser from this study."""
		return {
			'allowed_domains': ['https://fixture.test'],
			'block_ip_addresses': True,
			'use_cloud': False,
			'env': {'ANONYMIZED_TELEMETRY': 'false', 'BROWSER_USE_CLOUD_SYNC': 'false'},
			'egress': 'none: fixture transport only',
		}

	def approve(self, proposal: Proposal, *, reviewer: str, now: int) -> str:
		"""Simulate a trusted reviewer; the caller identity is NOT authenticated here."""
		if reviewer != 'fixture-human' or type(now) is not int or now < 0:
			raise ValueError('synthetic review required')
		token = secrets.token_hex(16)
		self._grants[token] = (proposal.digest(), now + 60)
		return token

	def execute(self, proposal: Proposal, *, now: int, approval: str | None = None) -> Receipt:
		"""Reserve simulated units once, then record a synthetic result, including uncertainty."""
		if type(now) is not int or now < 0:
			raise ValueError('invalid clock')
		if proposal.job_id in self.receipts:
			raise ValueError('replay')
		if len(self.receipts) >= self.max_steps or proposal.units > self.remaining:
			raise ValueError('limit exceeded')
		reviewer: Literal['fixture-human'] | None = None
		if proposal.action == 'submit_fixture':
			grant = self._grants.get(approval or '')
			if not grant or grant[0] != proposal.digest() or now >= grant[1]:
				raise ValueError('approval required')
			del self._grants[approval]  # type: ignore[index]
			reviewer = 'fixture-human'
		self.remaining -= proposal.units
		# No network dispatch or real action. A failure keeps the reservation.
		receipt = Receipt(
			job_id=proposal.job_id,
			proposal_hash=proposal.digest(),
			status='uncertain' if proposal.url.endswith('/fail') else 'completed',
			reserved_units=proposal.units,
			reviewer=reviewer,
		)
		self.receipts[proposal.job_id] = receipt
		return receipt
