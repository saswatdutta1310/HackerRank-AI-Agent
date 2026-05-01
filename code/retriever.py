import os
from pathlib import Path
from rank_bm25 import BM25Okapi
import re
import logging
import config

logger = logging.getLogger(__name__)

class DocumentChunk:
    def __init__(self, domain: str, path: str, content: str):
        self.domain = domain
        self.path = path
        self.content = content
        # Tokenize for BM25
        self.tokens = self._tokenize(content)

    def _tokenize(self, text: str):
        # Basic word tokenization, lowercase, keep alphanumerics
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
        return text.split()

class Retriever:
    def __init__(self):
        self.chunks = []
        self.domain_indices = {}  # domain -> {'bm25': BM25Okapi, 'chunks': list}
        
    def load_corpus(self):
        logger.info("Loading corpus from %s", config.DATA_DIR)
        for domain in config.COMPANIES:
            domain_lower = domain.lower()
            domain_path = config.DATA_DIR / domain_lower
            if not domain_path.exists():
                logger.warning(f"Domain path not found: {domain_path}")
                continue
            
            domain_chunks = []
            for filepath in domain_path.rglob("*.md"):
                content = filepath.read_text(encoding='utf-8', errors='ignore')
                chunks = self._chunk_text(content)
                for chunk_text in chunks:
                    chunk = DocumentChunk(
                        domain=domain,
                        path=str(filepath.relative_to(config.DATA_DIR)),
                        content=chunk_text
                    )
                    if chunk.tokens: # only add if not empty
                        domain_chunks.append(chunk)
                        self.chunks.append(chunk)
            
            if domain_chunks:
                bm25 = BM25Okapi([c.tokens for c in domain_chunks])
                self.domain_indices[domain] = {
                    'bm25': bm25,
                    'chunks': domain_chunks
                }
            logger.info("Loaded %d chunks for domain %s", len(domain_chunks), domain)
            
    def _chunk_text(self, text: str) -> list[str]:
        # Simple splitting by paragraph, then grouping
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        chunks = []
        current_chunk = []
        current_len = 0
        
        for p in paragraphs:
            # Approx word count
            p_len = len(p.split())
            if current_len + p_len > config.CHUNK_SIZE and current_chunk:
                chunks.append(" ".join(current_chunk))
                # Keep some overlap
                overlap = current_chunk[-max(1, len(current_chunk)//4):]
                current_chunk = overlap + [p]
                current_len = sum(len(x.split()) for x in current_chunk)
            else:
                current_chunk.append(p)
                current_len += p_len
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    def retrieve(self, query: str, domain: str, top_k: int = config.TOP_K) -> list[DocumentChunk]:
        if domain not in self.domain_indices:
            logger.warning(f"No index found for domain: {domain}")
            return []
            
        index_data = self.domain_indices[domain]
        bm25 = index_data['bm25']
        domain_chunks = index_data['chunks']
        
        # Tokenize query
        tokenized_query = re.sub(r'[^a-zA-Z0-9\s]', ' ', query.lower()).split()
        if not tokenized_query:
            return []
            
        doc_scores = bm25.get_scores(tokenized_query)
        scored_chunks = []
        for score, chunk in zip(doc_scores, index_data['chunks']):
            # Filename boost: if query keywords match the filename, boost the score
            filename = Path(chunk.path).stem.lower()
            boost = 1.0
            for word in tokenized_query:
                if len(word) > 3 and word in filename:
                    boost += 0.5
            scored_chunks.append((score * boost, chunk))
        
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        # Filter by threshold and take top k
        results = [chunk for score, chunk in scored_chunks if score >= config.BM25_THRESHOLD][:top_k]
        return results
