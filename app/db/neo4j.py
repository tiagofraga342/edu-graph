from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))

def create_note_node(note_id, title, embedding):
    with driver.session() as session:
        session.run("""
            CREATE (:Note {id: $id, title: $title, embedding: $embedding})
        """, id=note_id, title=title, embedding=embedding)

def get_all_notes_with_embeddings():
    with driver.session() as session:
        result = session.run("MATCH (n:Note) RETURN n.id AS id, n.embedding AS embedding")
        return [{"id": row["id"], "embedding": row["embedding"]} for row in result]

def create_similarity_edge(id1, id2, score):
    with driver.session() as session:
        session.run("""
            MATCH (a:Note {id: $id1}), (b:Note {id: $id2})
            MERGE (a)-[:SIMILAR_TO {score: $score}]->(b)
        """, id1=id1, id2=id2, score=score)

