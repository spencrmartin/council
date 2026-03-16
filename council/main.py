"""
Council backend entry point — FastAPI server.
"""
import atexit
import signal
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import Config, write_port_file, cleanup_port_file
from .database.connection import Database
from .database.repository import AgentRepository, SeatRepository, RegionRepository, IOPortRepository, ConstitutionRepository, DiscussionRepository
from .api.routes import router, init_repos


def create_app(config: Config = None) -> FastAPI:
    if config is None:
        config = Config()

    app = FastAPI(
        title="Council — Agent Governance",
        version="0.1.0",
    )

    # CORS for frontend dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize database
    db = Database(config.db_path)
    db.initialize()

    # Create repositories and wire into routes
    init_repos(
        agents=AgentRepository(db),
        seats=SeatRepository(db),
        regions=RegionRepository(db),
        io_ports=IOPortRepository(db),
        constitution=ConstitutionRepository(db),
        discussions=DiscussionRepository(db),
    )

    app.include_router(router)

    @app.get("/")
    async def root():
        return {"app": "council", "version": "0.1.0"}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


def main():
    config = Config()
    port = config.resolve_port()
    write_port_file(port)
    atexit.register(cleanup_port_file)

    def _signal_handler(sig, frame):
        cleanup_port_file()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    print(f"🏛️  Council backend starting on http://{config.host}:{port}")
    app = create_app(config)
    uvicorn.run(app, host=config.host, port=port)


if __name__ == "__main__":
    main()
