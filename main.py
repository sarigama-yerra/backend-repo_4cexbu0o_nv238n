import os
import time
import uuid
from typing import List, Optional, Literal, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="D‑Shield Mock API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------
# General + Health
# ------------------------------
@app.get("/")
def read_root():
    return {"message": "D‑Shield mock backend is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database env is available (mock friendly)."""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Used (mock data)",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Mock Mode",
        "collections": [],
    }
    try:
        db_url = os.getenv("DATABASE_URL")
        db_name = os.getenv("DATABASE_NAME")
        response["database_url"] = "✅ Set" if db_url else "❌ Not Set"
        response["database_name"] = "✅ Set" if db_name else "❌ Not Set"
    except Exception as e:
        response["database"] = f"⚠️ Error: {str(e)[:60]}"
    return response


# ------------------------------
# Solutions (static copy)
# ------------------------------
class SolutionItem(BaseModel):
    key: str
    title: str
    summary: str


SOLUTIONS: List[SolutionItem] = [
    SolutionItem(
        key="embrain",
        title="EmBrain",
        summary="Secure, scalable POI repository for researchers — store, tag, enrich and prioritize people and organizations.",
    ),
    SolutionItem(
        key="social-dome",
        title="Social Dome",
        summary="Real-time social monitoring and scoring that surfaces operational signals and feeds analyst workflows.",
    ),
    SolutionItem(
        key="napoleon",
        title="Napoleon",
        summary="Automated multi-model research engine that produces source‑tracked investigative reports from POIs.",
    ),
    SolutionItem(
        key="relationships",
        title="Relationship Analysis",
        summary="Graph‑powered map of entity relationships — explore connections, filter relations, reveal escalation paths.",
    ),
]


@app.get("/api/solutions", response_model=List[SolutionItem])
def get_solutions():
    return SOLUTIONS


# ------------------------------
# EmBrain demo endpoints (mock)
# ------------------------------
class EmbrainEntity(BaseModel):
    id: str
    name: str
    type: Literal["person", "organization"]
    tags: List[str] = []
    notes: Optional[str] = None


EMBRAIN_FIXTURES: List[EmbrainEntity] = [
    EmbrainEntity(id="p_001", name="Alex Rivera", type="person", tags=["priority", "us"], notes="Analyst‑verified."),
    EmbrainEntity(id="o_101", name="Northwind Analytics", type="organization", tags=["vendor"], notes="Enriched from filings."),
    EmbrainEntity(id="p_002", name="Jordan Lee", type="person", tags=["watch"], notes=None),
]


class SearchQuery(BaseModel):
    q: str = Field("", description="Search query")
    tag: Optional[str] = None


@app.post("/api/embrain/search", response_model=List[EmbrainEntity])
def embrain_search(body: SearchQuery):
    q = body.q.lower().strip()
    tag = (body.tag or "").lower().strip()
    results = []
    for e in EMBRAIN_FIXTURES:
        if q and q not in e.name.lower():
            continue
        if tag and tag not in [t.lower() for t in e.tags]:
            continue
        results.append(e)
    return results


class TagUpdate(BaseModel):
    id: str
    add: List[str] = []
    remove: List[str] = []


@app.post("/api/embrain/tags", response_model=EmbrainEntity)
def embrain_update_tags(body: TagUpdate):
    for e in EMBRAIN_FIXTURES:
        if e.id == body.id:
            # remove
            e.tags = [t for t in e.tags if t not in set(body.remove)]
            # add
            for t in body.add:
                if t not in e.tags:
                    e.tags.append(t)
            return e
    raise HTTPException(status_code=404, detail="Entity not found")


class InstanceCreate(BaseModel):
    name: str


@app.post("/api/embrain/create-instance")
def embrain_create_instance(body: InstanceCreate):
    return {"instanceId": f"inst_{uuid.uuid4().hex[:8]}", "name": body.name, "status": "provisioning"}


# ------------------------------
# Social Dome demo endpoints (mock)
# ------------------------------
class PostItem(BaseModel):
    id: str
    author: str
    text: str
    score: Literal["green", "yellow", "red"]
    created_at: float
    geo: Optional[Dict[str, float]] = None


SOCIAL_FEED: List[PostItem] = [
    PostItem(id="t1", author="@k12_watch", text="School event delayed due to weather.", score="green", created_at=time.time() - 5400),
    PostItem(id="t2", author="@city_updates", text="Road closure near central hub tonight.", score="yellow", created_at=time.time() - 3200, geo={"lat": 40.71, "lng": -74.0}),
    PostItem(id="t3", author="@alerts_bot", text="Verified threat rumor is false; standing down.", score="green", created_at=time.time() - 1200),
    PostItem(id="t4", author="@ops_team", text="Escalation candidate: coordinated disruption chatter.", score="red", created_at=time.time() - 300, geo={"lat": 34.05, "lng": -118.24}),
]


@app.get("/api/social-dome/feed", response_model=List[PostItem])
def social_dome_feed(limit: int = 20):
    items = list(sorted(SOCIAL_FEED, key=lambda p: p.created_at, reverse=True))
    return items[:limit]


# ------------------------------
# Napoleon demo endpoints (mock)
# ------------------------------
class RunRequest(BaseModel):
    poi: str


class RunStatus(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed"]
    progress: int = 0
    activity: List[str] = []
    report_url: Optional[str] = None


JOBS: Dict[str, RunStatus] = {}


@app.post("/api/napoleon/run", response_model=RunStatus)
def napoleon_run(req: RunRequest):
    job_id = uuid.uuid4().hex[:10]
    status = RunStatus(job_id=job_id, status="queued", progress=0, activity=[f"Queued job for {req.poi}"])
    JOBS[job_id] = status
    return status


@app.get("/api/napoleon/status/{job_id}", response_model=RunStatus)
def napoleon_status(job_id: str):
    status = JOBS.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    # simulate progression
    if status.status != "completed":
        step_messages = [
            "Dispatching research agents",
            "Collecting sources",
            "Synthesizing findings",
            "Compiling report",
        ]
        next_prog = min(100, status.progress + 25)
        status.progress = next_prog
        status.status = "running" if next_prog < 100 else "completed"
        if len(status.activity) - 1 < len(step_messages):
            status.activity.append(step_messages[len(status.activity) - 1])
        if status.status == "completed":
            status.report_url = "/mock/reports/sample.pdf"
    return status


# ------------------------------
# Relationship Analysis demo (mock graph)
# ------------------------------
class GraphNode(BaseModel):
    id: str
    label: str
    type: Literal["person", "org", "location"]


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: Literal["works_at", "knows", "located_in"]


class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


GRAPH_DATA = GraphData(
    nodes=[
        GraphNode(id="n1", label="Alex Rivera", type="person"),
        GraphNode(id="n2", label="Northwind Analytics", type="org"),
        GraphNode(id="n3", label="Jordan Lee", type="person"),
        GraphNode(id="n4", label="Los Angeles", type="location"),
    ],
    edges=[
        GraphEdge(id="e1", source="n1", target="n2", relation="works_at"),
        GraphEdge(id="e2", source="n3", target="n2", relation="works_at"),
        GraphEdge(id="e3", source="n2", target="n4", relation="located_in"),
        GraphEdge(id="e4", source="n1", target="n3", relation="knows"),
    ],
)


@app.get("/api/relationships/graph", response_model=GraphData)
def get_graph():
    return GRAPH_DATA


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
