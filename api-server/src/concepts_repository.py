import chromadb
from chromadb.config import Settings
import uuid

class ConceptsRepository:
    def __init__(self):
        client = chromadb.Client(Settings())
        self.concept_collection = client.create_collection(name="chess-concepts")
        self.save_chess_concepts()
        
        
    def save_chess_concepts(self):
        with open('data/ChessConcepts.md') as f:
            content = f.read()
            concepts = content.split("## ")
            
            documents = []
            metadatas = []
            ids = []

            for concept in concepts[1:]:
                self.save_concept(documents, metadatas, ids, concept)

        self.concept_collection.add(
            documents = documents,
            metadatas = metadatas,
            ids = ids
        )

    def save_concept(self, documents, metadatas,
                     ids, concept):
        lines = concept.split('\n')
        title = lines[0]
        content = lines[1]
        tags = lines[2].replace('- **Labels:** ', '')
        metadata = self.build_metadata(tags)
        
        metadatas.append(metadata)
        documents.append(f"{title}\n{content}")
        ids.append(str(uuid.uuid4()))

        

    def build_metadata(self, tags):
        metadata = {
            'Phase': '',
            'Concepts': ''
        }

        for tag in tags.split(', '):
            if tag in ['Opening', 'Middlegame', 'Endgame']:
                metadata['Phase'] += f"{tag}, "
            else:
                metadata['Concepts'] += tag
        
        return metadata

    def search(self, phase, aspect, keywords):
        query_text = ' '.join(keywords + [phase, aspect])
        
        query_result = self.concept_collection.query(
            query_texts=[query_text],
            n_results=5
        )
        
        return query_result["documents"]