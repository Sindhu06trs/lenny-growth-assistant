from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.session_service import SessionService
from app.schemas.artifact import ArtifactResponse

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


# Curated Demonstration Artifacts matching frontend demo catalog
DEMO_ARTIFACTS: dict = {
    "demo-retention-calc": {
        "id": "demo-retention-calc",
        "session_id": "demo-session",
        "message_id": None,
        "type": "html",
        "title": "Customer Retention & Cohort Simulator",
        "content": """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0F172A;
      color: #F8FAFC;
      margin: 0;
      padding: 24px;
      box-sizing: border-box;
    }
    .card {
      background: #1E293B;
      border: 1px solid #334155;
      border-radius: 16px;
      padding: 24px;
      max-width: 540px;
      margin: 0 auto;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    }
    h2 {
      margin-top: 0;
      color: #818CF8;
      font-size: 18px;
    }
    .input-group {
      margin-bottom: 16px;
    }
    label {
      display: block;
      font-size: 12px;
      color: #94A3B8;
      margin-bottom: 6px;
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 0.05em;
    }
    input[type="range"] {
      width: 100%;
      accent-color: #6366F1;
      cursor: pointer;
    }
    .val-display {
      font-size: 14px;
      color: #38BDF8;
      font-weight: bold;
      float: right;
    }
    .results {
      margin-top: 24px;
      background: #0B0F19;
      border: 1px solid #232F4D;
      border-radius: 12px;
      padding: 16px;
    }
    .stat-row {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      font-size: 13px;
    }
    .stat-label { color: #94A3B8; }
    .stat-val { font-weight: 700; color: #10B981; }
    .badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 10px;
      font-weight: bold;
      background: rgba(99, 102, 241, 0.2);
      color: #A5B4FC;
      margin-bottom: 16px;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">DEMO WIDGET</div>
    <h2>⚡ SaaS Retention & ARR Simulator</h2>
    
    <div class="input-group">
      <label>Monthly Signups <span id="signups-val" class="val-display">5,000</span></label>
      <input id="signups" type="range" min="1000" max="20000" step="500" value="5000" oninput="calculate()">
    </div>

    <div class="input-group">
      <label>Monthly Churn Rate <span id="churn-val" class="val-display">3.5%</span></label>
      <input id="churn" type="range" min="0.5" max="100" step="0.5" value="3.5" oninput="calculate()">
    </div>

    <div class="input-group">
      <label>Average Revenue Per User (ARPU) <span id="arpu-val" class="val-display">$65</span></label>
      <input id="arpu" type="range" min="10" max="300" step="5" value="65" oninput="calculate()">
    </div>

    <div class="results">
      <div class="stat-row">
        <span class="stat-label">Steady-State Active Users:</span>
        <span id="active-users" class="stat-val">142,857</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Projected Monthly Recurring Revenue (MRR):</span>
        <span id="mrr" class="stat-val">$9,285,705</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Annual Run Rate (ARR):</span>
        <span id="arr" class="stat-val" style="color: #6366F1;">$111.4M</span>
      </div>
    </div>
  </div>

  <script>
    function calculate() {
      const signups = parseFloat(document.getElementById('signups').value);
      const churn = parseFloat(document.getElementById('churn').value) / 100;
      const arpu = parseFloat(document.getElementById('arpu').value);

      document.getElementById('signups-val').innerText = signups.toLocaleString();
      document.getElementById('churn-val').innerText = (churn * 100).toFixed(1) + '%';
      document.getElementById('arpu-val').innerText = '$' + arpu;

      const activeUsers = Math.round(signups / churn);
      const mrr = Math.round(activeUsers * arpu);
      const arr = (mrr * 12) / 1000000;

      document.getElementById('active-users').innerText = activeUsers.toLocaleString();
      document.getElementById('mrr').innerText = '$' + mrr.toLocaleString();
      document.getElementById('arr').innerText = '$' + arr.toFixed(1) + 'M';
    }
  </script>
</body>
</html>""",
        "version": 1,
        "is_demonstration": True,
        "created_at": "2026-10-12T00:00:00Z",
    },
    "demo-strategy-guide": {
        "id": "demo-strategy-guide",
        "session_id": "demo-session",
        "message_id": None,
        "type": "markdown",
        "title": "Product-Led Growth & Retention Audit Playbook",
        "content": """# Product-Led Growth & Retention Audit Playbook
> *[UI Demonstration Artifact — Staged Strategy Guide Framework]*

## 1. Executive Summary
Before accelerating top-of-funnel acquisition, growth teams must establish cohort retention baseline health.

---

## 2. Core Diagnostic Metrics

| Metric | Target Benchmark (B2B SaaS) | Target Benchmark (Consumer) | Health Action Trigger |
| :--- | :--- | :--- | :--- |
| **D1 Retention** | 40% – 60% | 30% – 45% | Audit first-mile onboarding time-to-value |
| **D30 Retention** | 20% – 35% | 10% – 20% | Evaluate habit loop & notification triggers |
| **Net Revenue Retention (NRR)** | > 115% | N/A | Review expansion pricing tiers |

---

## 3. Four-Step Retention Diagnostic Flow

1. **Segment Cohorts by Acquisition Channel**: Disaggregate organic vs. paid cohorts to isolate user intent.
2. **Identify the Core Setup Moment**: Determine the single action that correlates with 80%+ 6-month retention.
3. **Remove Friction in Activation**: Shorten time from signup to the "Aha!" realization.
4. **Establish Retention Loops**: Connect user outputs to downstream viral or habitual re-engagement triggers.
""",
        "version": 1,
        "is_demonstration": True,
        "created_at": "2026-10-12T00:00:00Z",
    },
    "demo-ship30-essay": {
        "id": "demo-ship30-essay",
        "session_id": "demo-session",
        "message_id": None,
        "type": "essay",
        "title": "Why Top-of-Funnel Fixes Won’t Save a Leaky Bucket",
        "content": """# Why Top-of-Funnel Fixes Won’t Save a Leaky Bucket

Most early-stage founders believe their primary problem is distribution. They buy more ads, launch on Product Hunt, and hire growth agencies.

**Here is the hard truth: Pouring water into a leaky bucket does not fix the holes; it only empties your bank account.**

---

### 1. The Growth Mirage: Acquisition Without Retention
When a product lacks a stable retention curve, every new user acquired is merely a temporary visitor.

- **The Linear Trap**: Funnels require perpetual spending. Stop spending, and growth evaporates.
- **The Compounding Loop**: Retained users compound. Each cohort layers on top of the last, creating sustainable momentum.

---

### 2. The 3 Signals of a Leaky Bucket
How do you know if your retention is fundamentally broken?

1. **Asymptotic Retention Curves Never Flatten**: If your cohort line continues down to zero over 90 days, you do not have Product-Market Fit.
2. **Paid CAC Payback Exceeds 18 Months**: High churn destroys customer lifetime value (LTV).
3. **Users Churn Before Experiencing the Core Value**: If 70% of churn occurs within 48 hours, onboarding friction is killing your product.

---

### 3. The 30-Day Fix: Re-engineer the Activation Moment
Instead of spending another dollar on acquisition, focus on time-to-value (TTV):

- **Kill the Signup Survey**: Remove unnecessary friction before the user reaches the primary workflow.
- **Pre-populate Templates**: Show the user what a finished project looks like instead of confronting them with a blank canvas.
- **Design the Habit Loop**: Give the user a clear reason to return within 72 hours.

---

### Conclusion: Fix Retention First, Accelerate Second
Growth is not a megaphone; growth is a flywheel. When the flywheel retains energy, every push makes it spin faster. Fix the holes in the bucket first.
""",
        "version": 1,
        "is_demonstration": True,
        "created_at": "2026-10-12T00:00:00Z",
    },
}


@router.get(
    "/{artifact_id}",
    response_model=ArtifactResponse,
    summary="Get Artifact by ID",
    description="Retrieves a single persisted Markdown, HTML, or Essay artifact by its unique ID."
)
async def get_artifact(
    artifact_id: str,
    db: AsyncSession = Depends(get_db)
) -> ArtifactResponse:
    """
    Returns an individual artifact.
    """
    artifact = await SessionService.get_artifact(db, artifact_id)
    if not artifact:
        # Check built-in demo artifacts
        if artifact_id in DEMO_ARTIFACTS:
            return ArtifactResponse(**DEMO_ARTIFACTS[artifact_id])
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact '{artifact_id}' not found."
        )
    return ArtifactResponse(**artifact.to_dict())


@router.get(
    "",
    response_model=List[ArtifactResponse],
    summary="List Session Artifacts",
    description="Retrieves all artifacts belonging to a specific conversation session."
)
async def list_artifacts(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> List[ArtifactResponse]:
    """
    Returns artifacts belonging to a given session.
    """
    artifacts = await SessionService.get_session_artifacts(db, session_id)
    return [ArtifactResponse(**a.to_dict()) for a in artifacts]

