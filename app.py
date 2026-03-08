import streamlit as st
import requests

# Point this to your FastAPI server
API_URL = "http://localhost:8000"

# Set up the page layout
st.set_page_config(page_title="Semantic Search", page_icon="🔍", layout="wide")

st.title("🔍 Semantic Search Engine")
st.markdown("Powered by Vector Embeddings, Fuzzy Clustering, and Semantic Caching.")

# ==========================================
# SIDEBAR: System Status & Cache Stats
# ==========================================
with st.sidebar:
    st.header("⚙️ System Status")
    try:
        # Check backend health
        health = requests.get(f"{API_URL}/health").json()
        st.success("🟢 API is Online")
        st.metric("Documents in DB", health["vector_db_docs"])
    except requests.exceptions.ConnectionError:
        st.error("🔴 API is Offline")
        st.caption("Please ensure uvicorn is running on port 8000.")
        st.stop()
        
    st.markdown("---")
    st.header("🧠 Cache Stats")
    
    # Fetch and display cache stats
    stats = requests.get(f"{API_URL}/cache/stats").json()
    col1, col2 = st.columns(2)
    col1.metric("Cache Entries", stats["total_entries"])
    col2.metric("Hit Rate", f"{stats['hit_rate']*100:.1f}%")
    
    # Button to clear the cache
    if st.button("🗑️ Clear Cache"):
        requests.delete(f"{API_URL}/cache")
        st.success("Cache cleared!")
        st.rerun()

# ==========================================
# MAIN UI: Search Interface
# ==========================================
query = st.text_input("Enter your search query:", placeholder="e.g., space shuttle mission to mars")

# Trigger search on button click or Enter key
if st.button("Search", type="primary") or query:
    if query:
        with st.spinner("Searching the vector database..."):
            # Send the request to your FastAPI backend
            response = requests.post(f"{API_URL}/query", json={"query": query})
            
            if response.status_code == 200:
                data = response.json()
                
                # 1. Display Search Metrics
                st.markdown("### Search Metrics")
                cols = st.columns(4)
                cols[0].metric("Processing Time", f"{data['processing_time_ms']:.2f} ms")
                cols[1].metric("Dominant Cluster", data['dominant_cluster'])
                cols[2].metric("Cache Hit?", "✅ Yes" if data['cache_hit'] else "❌ No")
                
                if data['cache_hit']:
                    cols[3].metric("Similarity Match", f"{data['similarity_score']:.3f}")
                
                st.markdown("---")
                
                # 2. Display the Retrieved Documents
                st.subheader(f"📄 Top Results")
                
                docs = data['result'].get('documents', [])
                meta = data['result'].get('metadatas', [])
                dists = data['result'].get('distances', [])
                
                if not docs:
                    st.info("No documents found for this query.")
                else:
                    for i, doc in enumerate(docs):
                        # Use an expander so the screen doesn't get cluttered with massive text blocks
                        distance_str = f"Distance: {dists[i]:.4f}" if dists else ""
                        with st.expander(f"Result {i+1} | {distance_str}", expanded=(i==0)):
                            if meta and i < len(meta):
                                category = meta[i].get('category', 'Unknown')
                                st.caption(f"**Original Category:** `{category}`")
                            st.write(doc)
            else:
                st.error(f"API Error: {response.text}")