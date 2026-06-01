# Advanced Bug Bounty Methodology

## 5-Phase Non-Linear Workflow
1. **Intelligence Gathering**: Beyond recon. Read tech blogs by company devs, check their GitHub for coding patterns.
2. **Deep Surface Mapping**: Build a state machine of the app. Map every transition.
3. **Anomaly Probing**: Look for response time variances, header inconsistencies, and logic gaps.
4. **Targeted Exploitation**: Apply the A->B chain method.
5. **Impact Maximization**: Chain to ATO or RCE.

## Developer Psychology Framework
- **The "Happy Path" Bias**: Developers test what should work. You test what shouldn't.
- **The "Internal" Illusion**: If it's behind a VPN or internal, it's often less secure.
- **The "Refactor" Risk**: New code replacing old code is the most fertile ground for bugs.

## Route Selection: Wide vs. Deep
- **Wide**: Scan 100 subdomains for quick wins (403 bypass, open S3).
- **Deep**: Spend 3 days on ONE complex feature (e.g., the billing system).
