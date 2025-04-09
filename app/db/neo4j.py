from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))

def create_note_node(note_id, title, embedding):
    with driver.session() as session:
        session.run("""
            CREATE (:Note {id: $id, title: $title, embedding: $embedding})
        """, id=note_id, title=title, embedding=embedding)

