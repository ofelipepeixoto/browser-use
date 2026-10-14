"""Synthetic regressions; never import browser_use or make external calls."""

import unittest
from unittest.mock import patch

from contract import OfflineStudy, Proposal
from pydantic import ValidationError


class ContractTests(unittest.TestCase):
	def proposal(self, **changes):
		return Proposal(
			**({'job_id': 'job-1', 'action': 'read_fixture', 'url': 'https://fixture.test/page', 'units': 1} | changes)
		)

	def test_network_never_used(self):
		with patch('socket.socket', side_effect=AssertionError('network forbidden')):
			self.assertEqual(OfflineStudy().execute(self.proposal(), now=0).status, 'completed')

	def test_unknown_and_real_targets_rejected(self):
		for url in ('https://example.com', 'http://127.0.0.1', 'file:///tmp/a', 'https://fixture.test/page?token=x'):
			with self.assertRaises(ValidationError):
				self.proposal(url=url)
		with self.assertRaises(ValidationError):
			self.proposal(action='send_message')
		with self.assertRaises(ValidationError):
			self.proposal(tenant_id='from-llm')

	def test_consequential_approval_and_receipt(self):
		study = OfflineStudy()
		proposal = self.proposal(action='submit_fixture')
		with self.assertRaises(ValueError):
			study.execute(proposal, now=0)
		self.assertEqual(study.remaining, 3)
		token = study.approve(proposal, reviewer='fixture-human', now=0)
		result = study.execute(proposal, now=1, approval=token)
		self.assertEqual(result.reviewer, 'fixture-human')
		self.assertEqual(result.proposal_hash, proposal.digest())
		with self.assertRaises(ValueError):
			study.execute(proposal, now=2, approval=token)

	def test_expired_and_changed_proposal(self):
		study = OfflineStudy()
		p = self.proposal(action='submit_fixture')
		token = study.approve(p, reviewer='fixture-human', now=0)
		with self.assertRaises(ValueError):
			study.execute(p, now=60, approval=token)
		with self.assertRaises(ValueError):
			study.execute(self.proposal(action='submit_fixture', units=2), now=1, approval=token)

	def test_budget_and_steps(self):
		study = OfflineStudy(budget=1, max_steps=1)
		study.execute(self.proposal(), now=0)
		with self.assertRaises(ValueError):
			study.execute(self.proposal(job_id='job-2', units=0), now=0)
		with self.assertRaises(ValueError):
			OfflineStudy(budget=0).execute(self.proposal(), now=0)
		with self.assertRaises(ValidationError):
			self.proposal(units=True)

	def test_uncertain_keeps_reservation_and_no_replay(self):
		study = OfflineStudy()
		p = self.proposal(url='https://fixture.test/fail')
		self.assertEqual(study.execute(p, now=0).status, 'uncertain')
		self.assertEqual(study.remaining, 2)
		with self.assertRaises(ValueError):
			study.execute(p, now=1)

	def test_privacy_configuration(self):
		cfg = OfflineStudy.browser_configuration()
		self.assertFalse(cfg['use_cloud'])
		self.assertEqual(cfg['env']['ANONYMIZED_TELEMETRY'], 'false')
		self.assertEqual(cfg['env']['BROWSER_USE_CLOUD_SYNC'], 'false')
		self.assertEqual(cfg['egress'], 'none: fixture transport only')


if __name__ == '__main__':
	unittest.main()
