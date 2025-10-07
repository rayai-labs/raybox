"""
Raybox API Server - Ray Serve + FastAPI
"""

import uuid
from datetime import datetime

import ray
from fastapi import FastAPI, HTTPException
from ray import serve

from .sandbox import (
    CodeExecutionRequest,
    ExecutionResult,
    SandboxActor,
    SandboxCreateRequest,
    SandboxInfo,
)

# FastAPI app
app = FastAPI(
    title="Raybox API", description="Secure code execution sandboxes via HTTP", version="0.1.0"
)


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
@serve.ingress(app)
class RayboxAPI:
    """Raybox HTTP API served by Ray Serve."""

    def __init__(self):
        # Track active sandboxes: {sandbox_id: actor_handle}
        self.sandboxes: dict[str, ray.ObjectRef] = {}

    @app.get("/health")
    async def health_check(self):
        """Health check endpoint."""
        return {"status": "healthy", "service": "raybox-api", "version": "0.1.0"}

    @app.post("/sandboxes", response_model=SandboxInfo)
    async def create_sandbox(self, request: SandboxCreateRequest):
        """Create a new sandbox."""
        sandbox_id = str(uuid.uuid4())

        config = {
            "memory_limit_mb": request.memory_limit_mb,
            "cpu_limit": request.cpu_limit,
            "timeout": request.timeout,
        }

        # Create Ray actor for this sandbox
        sandbox_actor = SandboxActor.remote(sandbox_id, config)  # type: ignore[attr-defined]

        # Store the actor handle
        self.sandboxes[sandbox_id] = sandbox_actor

        return SandboxInfo(
            sandbox_id=sandbox_id, status="running", created_at=datetime.utcnow().isoformat()
        )

    @app.post("/sandboxes/{sandbox_id}/execute", response_model=ExecutionResult)
    async def execute_code(self, sandbox_id: str, request: CodeExecutionRequest):
        """Execute code in a sandbox."""
        if sandbox_id not in self.sandboxes:
            raise HTTPException(status_code=404, detail="Sandbox not found")

        sandbox_actor = self.sandboxes[sandbox_id]

        # Execute code via Ray actor
        result = await sandbox_actor.execute.remote(request.code)  # type: ignore[attr-defined]

        return ExecutionResult(**result)

    @app.post("/sandboxes/{sandbox_id}/packages")
    async def install_packages(self, sandbox_id: str, packages: list[str]):
        """Install Python packages in a sandbox."""
        if sandbox_id not in self.sandboxes:
            raise HTTPException(status_code=404, detail="Sandbox not found")

        sandbox_actor = self.sandboxes[sandbox_id]

        # Install packages via Ray actor
        result = await sandbox_actor.install_packages.remote(packages)  # type: ignore[attr-defined]

        return result

    @app.get("/sandboxes/{sandbox_id}", response_model=SandboxInfo)
    async def get_sandbox(self, sandbox_id: str):
        """Get sandbox information."""
        if sandbox_id not in self.sandboxes:
            raise HTTPException(status_code=404, detail="Sandbox not found")

        sandbox_actor = self.sandboxes[sandbox_id]
        info = await sandbox_actor.get_info.remote()  # type: ignore[attr-defined]

        return SandboxInfo(**info)

    @app.delete("/sandboxes/{sandbox_id}")
    async def delete_sandbox(self, sandbox_id: str):
        """Terminate and delete a sandbox."""
        if sandbox_id not in self.sandboxes:
            raise HTTPException(status_code=404, detail="Sandbox not found")

        sandbox_actor = self.sandboxes[sandbox_id]

        # Terminate the sandbox
        await sandbox_actor.terminate.remote()  # type: ignore[attr-defined]

        # Remove from tracking
        del self.sandboxes[sandbox_id]

        return {"status": "deleted", "sandbox_id": sandbox_id}


# Deployment configuration
raybox_api = RayboxAPI.bind()  # type: ignore[attr-defined]
