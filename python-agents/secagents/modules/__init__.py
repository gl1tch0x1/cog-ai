"""Security modules: attack techniques, integrations, and automation."""

from secagents.modules.bypass_403 import bypass_403
from secagents.modules.exploit_chain import correlate_chains
from secagents.modules.external_tools import ExternalTools
from secagents.modules.autopilot import Autopilot
from secagents.modules.oast_browser import OASTClient, BrowserCluster, FeedbackLoop
from secagents.modules.workflow_dsl import WorkflowDSL, load_workflow
from secagents.modules.cve_checks import CHECKS, CheckResult, get_checks_for_url, is_static_asset
from secagents.modules.cve_scanner import CVEScanner, ScanConfig
