"""Security modules: attack techniques, integrations, and automation."""

from secagents.modules.bypass_403 import bypass_403 as bypass_403
from secagents.modules.exploit_chain import correlate_chains as correlate_chains
from secagents.modules.external_tools import ExternalTools as ExternalTools
from secagents.modules.autopilot import Autopilot as Autopilot
from secagents.modules.oast_browser import OASTClient as OASTClient, BrowserCluster as BrowserCluster, FeedbackLoop as FeedbackLoop
from secagents.modules.workflow_dsl import WorkflowDSL as WorkflowDSL, load_workflow as load_workflow
from secagents.modules.cve_checks import CHECKS as CHECKS, CheckResult as CheckResult, get_checks_for_url as get_checks_for_url, is_static_asset as is_static_asset
from secagents.modules.cve_scanner import CVEScanner as CVEScanner, ScanConfig as ScanConfig
