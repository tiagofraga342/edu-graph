from neo4j import GraphDatabase
import os

NEO4J_URI      = "bolt://neo4j:7687"
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = "password"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def create_note_node(note_id: str):
    with driver.session() as session:
        session.run(
            "MERGE (n:Note {id: $id})",
            id=note_id
        )


def create_relationship(from_id: str, to_id: str, rel_type: str = "RELATED"):
    with driver.session() as session:
        session.run(
            f"MATCH (a:Note {{id: $from_id}}), (b:Note {{id: $to_id}}) MERGE (a)-[r:{rel_type}]->(b)",
            from_id=from_id,
            to_id=to_id
        )


def get_relationships(note_id: str) -> list:
    with driver.session() as session:
        result = session.run(
            "MATCH (n:Note {id: $id})-[r]->(m:Note) RETURN type(r) AS type, m.id AS id",
            id=note_id
        )
        return [{"type": row["type"], "id": row["id"]} for row in result]
