from app.core.config import settings
from app.core.logging import logger
from typing import Optional, List, Dict, Any

try:
    from neo4j import AsyncGraphDatabase
    HAS_NEO4J = True
except ImportError:
    AsyncGraphDatabase = None
    HAS_NEO4J = False

class Neo4jClient:
    def __init__(self):
        self.driver = None
        self.connected = False

    async def connect(self):
        if not HAS_NEO4J:
            logger.info("Neo4j driver package not installed. Operating in graph-emulated mode.")
            self.connected = False
            return
        try:
            self.driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            await self.driver.verify_connectivity()
            self.connected = True
            logger.info("Successfully connected to Neo4j graph database.")
            await self._init_constraints()
        except Exception as e:
            logger.warning(f"Neo4j connection unavailable ({e}). Falling back to graph emulation mode.")
            self.connected = False

    async def _init_constraints(self):
        if not self.connected or not self.driver:
            return
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.handle IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Device) REQUIRE d.device_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE"
        ]
        async with self.driver.session() as session:
            for query in constraints:
                try:
                    await session.run(query)
                except Exception as err:
                    logger.debug(f"Constraint creation output: {err}")

    async def execute_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.connected or not self.driver:
            logger.debug(f"[Emulated Neo4j] Cypher query ignored: {query}")
            return []
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records

    async def close(self):
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed.")

neo4j_client = Neo4jClient()
