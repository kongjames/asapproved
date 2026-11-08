# Regulatory context — what this tool corresponds to, and what it never claims

These documents describe expectations that this tool's checks resemble. None of them approves,
certifies or validates software. The FDA AI guidance is a **draft**; the CSA guidance is a
**medical-device quality-system** document. Quotations are short and verbatim; read the originals.

| What asapproved does | Where the idea appears in official documents | What asapproved never claims |
|---|---|---|
| Traces every number to the dataset and recipe it came from | ICH E6(R3) 2.12.2: source records "attributable … traceable … (via an audit trail)"; 21 CFR 11.10(e) audit trails; FDA Study Data Technical Conformance Guide: define.xml metadata | "21 CFR Part 11 compliant", "GCP-certified" |
| Re-computes a table independently and compares cell by cell | ICH E6(R3) 9.3: computerised systems "fit for purpose (e.g., through risk-based validation, if appropriate)"; sdTCG: ADaM datasets "support the results in clinical study reports" | "FDA-approved", "FDA-cleared", "meets ICH E6(R3)" |
| Produces a report a reviewer signs and dates | FDA Computer Software Assurance (Feb 2026): "a risk-based approach … least-burdensome"; E6(R3) 4.3.4(d): "Periodic review may be appropriate to ensure that computerised systems remain in a validated state" | "Validated per Part 11", "CSA-compliant" |
| (v0.2) Flags change beyond normal re-run variation | FDA draft guidance on AI for regulatory decision-making (Jan 2025) §IV.B: "Model performance metrics should be monitored on an ongoing basis"; EMA reflection paper (2024): "early detection of drift/degradation"; NIST AI RMF MEASURE 2.4 | "Detects drift per FDA guidance", "FDA validated" |

Sources (fetched 2026-11-07): FDA draft guidance https://www.fda.gov/media/184830/download · sdTCG v6.3 https://www.fda.gov/media/153632/download · 21 CFR Part 11 (eCFR) · FDA CSA guidance https://www.fda.gov/media/188844/download · ICH E6(R3) https://database.ich.org/sites/default/files/ICH_E6%28R3%29_Step4_FinalGuideline_2025_0106.pdf · EMA reflection paper EMA/CHMP/CVMP/83833/2023 · NIST AI 100-1.
