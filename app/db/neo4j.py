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


def find_shortest_path(start_note_id: str, end_note_id: str, max_depth: int = 6) -> dict:
    """
    Find the shortest path between two notes using Cypher's shortestPath algorithm
    Returns path information including nodes and relationships
    """
    print(f"🔧 Neo4j: find_shortest_path called with start={start_note_id}, end={end_note_id}, max_depth={max_depth}")

    try:
        with driver.session() as session:
            # First check if both nodes exist
            check_query = """
            MATCH (start:Note {id: $start_id})
            MATCH (end:Note {id: $end_id})
            RETURN start.id as start_exists, end.id as end_exists
            """

            print(f"🔧 Neo4j: Checking if nodes exist...")
            result = session.run(check_query, start_id=start_note_id, end_id=end_note_id)
            record = result.single()

            if not record:
                print(f"❌ Neo4j: One or both nodes not found in Neo4j")
                return {"path": None, "error": "One or both notes not found in graph database"}

            print(f"✅ Neo4j: Both nodes exist in Neo4j")

            # Find shortest path (undirected)
            path_query = f"""
            MATCH (start:Note {{id: $start_id}}), (end:Note {{id: $end_id}})
            MATCH path = shortestPath((start)-[*1..{max_depth}]-(end))
            RETURN path,
                   length(path) as path_length,
                   [node in nodes(path) | node.id] as node_ids,
                   [rel in relationships(path) | type(rel)] as relationship_types
            """

            print(f"🔧 Neo4j: Executing path query...")
            result = session.run(path_query, start_id=start_note_id, end_id=end_note_id)
            record = result.single()

            if not record or record["path"] is None:
                print(f"❌ Neo4j: No path found between nodes")
                return {
                    "path": None,
                    "error": f"No path found between notes within {max_depth} steps"
                }

            path_result = {
                "node_ids": record["node_ids"],
                "relationship_types": record["relationship_types"],
                "length": record["path_length"]
            }

            print(f"✅ Neo4j: Path found: {path_result}")

            return {
                "path": path_result,
                "error": None
            }

    except Exception as e:
        print(f"❌ Neo4j: Exception in find_shortest_path: {e}")
        import traceback
        traceback.print_exc()
        return {"path": None, "error": f"Database error: {str(e)}"}


def find_all_paths(start_note_id: str, end_note_id: str, max_depth: int = 4, max_paths: int = 5) -> dict:
    """
    Find multiple paths between two notes
    Returns up to max_paths different paths
    """
    with driver.session() as session:
        # Find all paths up to max_depth
        paths_query = f"""
        MATCH (start:Note {{id: $start_id}}), (end:Note {{id: $end_id}})
        MATCH path = (start)-[*1..{max_depth}]-(end)
        WHERE start <> end
        RETURN path,
               length(path) as path_length,
               [node in nodes(path) | node.id] as node_ids,
               [rel in relationships(path) | type(rel)] as relationship_types
        ORDER BY length(path), path
        LIMIT {max_paths}
        """

        result = session.run(paths_query, start_id=start_note_id, end_id=end_note_id)

        paths = []
        for record in result:
            paths.append({
                "node_ids": record["node_ids"],
                "relationship_types": record["relationship_types"],
                "length": record["path_length"]
            })

        return {
            "paths": paths,
            "count": len(paths),
            "error": None if paths else f"No paths found between notes within {max_depth} steps"
        }


def get_node_neighbors(note_id: str, depth: int = 1) -> dict:
    """
    Get all neighboring nodes within specified depth
    Useful for exploring the local graph structure
    """
    with driver.session() as session:
        neighbors_query = f"""
        MATCH (start:Note {{id: $note_id}})
        MATCH path = (start)-[*1..{depth}]-(neighbor:Note)
        WHERE start <> neighbor
        RETURN DISTINCT neighbor.id as neighbor_id,
               length(path) as distance,
               [node in nodes(path) | node.id] as path_nodes
        ORDER BY distance, neighbor_id
        """

        result = session.run(neighbors_query, note_id=note_id)

        neighbors = []
        for record in result:
            neighbors.append({
                "id": record["neighbor_id"],
                "distance": record["distance"],
                "path": record["path_nodes"]
            })

        return {
            "neighbors": neighbors,
            "count": len(neighbors)
        }
