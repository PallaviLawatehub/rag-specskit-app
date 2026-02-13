(function(){
  const apiBase = window.API_BASE || 'http://localhost:5001';
  document.getElementById('apiBase').textContent = apiBase;

  const fileInput = document.getElementById('fileInput');
  const uploadBtn = document.getElementById('uploadBtn');
  const uploadResult = document.getElementById('uploadResult');
  const refreshDocs = document.getElementById('refreshDocs');
  const documentsList = document.getElementById('documentsList');
  const queryInput = document.getElementById('queryInput');
  const queryBtn = document.getElementById('queryBtn');
  const queryResult = document.getElementById('queryResult');
  const createCollectionBtn = document.getElementById('createCollection');
  const resetCollectionBtn = document.getElementById('resetCollection');
  const adminResult = document.getElementById('adminResult');
  const collectionNameInput = document.getElementById('collectionName');

  uploadBtn.addEventListener('click', uploadFile);
  refreshDocs.addEventListener('click', fetchDocuments);
  queryBtn.addEventListener('click', doQuery);
  createCollectionBtn.addEventListener('click', createCollection);
  resetCollectionBtn.addEventListener('click', resetCollection);

  async function uploadFile(){
    uploadResult.textContent = '';
    const f = fileInput.files[0];
    if(!f){ uploadResult.textContent = 'Choose a file first'; return; }
    const fd = new FormData();
    fd.append('file', f);
    uploadResult.textContent = 'Uploading...';
    try{
      const res = await fetch(`${apiBase}/api/upload`, { method: 'POST', body: fd });
      const data = await res.json();
      uploadResult.textContent = JSON.stringify(data, null, 2);
      if(res.ok) fetchDocuments();
    }catch(e){ uploadResult.textContent = 'Upload error: '+e.message; }
  }

  async function fetchDocuments(){
    documentsList.textContent = 'Loading...';
    try{
      const res = await fetch(`${apiBase}/api/documents?limit=100`);
      const data = await res.json();
      if(!res.ok){ documentsList.textContent = data.error || JSON.stringify(data); return; }
      if(!data.documents || data.documents.length===0){ documentsList.textContent = 'No documents found'; return; }
      documentsList.innerHTML = '';
      data.documents.forEach(d =>{
        const el = document.createElement('div');
        el.className = 'doc';
        el.innerHTML = `<strong>${escapeHtml(d.metadata?.source || d.id)}</strong> <em>chunk index:</em> ${d.metadata?.chunk_index ?? '-'}<div class='doc-text'>${escapeHtml(d.text)}</div>`;
        documentsList.appendChild(el);
      });
    }catch(e){ documentsList.textContent = 'Error: '+e.message; }
  }

  async function doQuery(){
    queryResult.textContent = '';
    const q = queryInput.value.trim();
    if(!q){ queryResult.textContent='Enter query'; return; }
    queryResult.textContent = 'Querying...';
    try{
      const res = await fetch(`${apiBase}/api/query`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ query: q, top_k: 5 }) });
      const data = await res.json();
      if(!res.ok){ queryResult.textContent = data.error || JSON.stringify(data); return; }
      if(!data.results || data.results.length===0){ queryResult.textContent = 'No results'; return; }
      queryResult.innerHTML = '';
      data.results.forEach(r =>{
        const el = document.createElement('div');
        el.className='result-item';
        el.innerHTML = `<div class='rank'>#${r.rank}</div><div class='score'>score: ${r.similarity_score}</div><div class='text'>${escapeHtml(r.text)}</div><div class='meta'>${escapeHtml(JSON.stringify(r.metadata))}</div>`;
        queryResult.appendChild(el);
      });
    }catch(e){ queryResult.textContent = 'Query error: '+e.message; }
  }

  async function createCollection(){
    adminResult.textContent='Creating collection...';
    const name = collectionNameInput.value.trim();
    try{
      const res = await fetch(`${apiBase}/api/collection`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(name?{name}:{}) });
      const data = await res.json();
      adminResult.textContent = JSON.stringify(data, null, 2);
    }catch(e){ adminResult.textContent = 'Error: '+e.message; }
  }

  async function resetCollection(){
    if(!confirm('Reset collection (delete and recreate)?')) return;
    adminResult.textContent='Resetting...';
    try{
      const res = await fetch(`${apiBase}/api/reset`, { method:'DELETE' });
      const data = await res.json();
      adminResult.textContent = JSON.stringify(data, null, 2);
      fetchDocuments();
    }catch(e){ adminResult.textContent = 'Error: '+e.message; }
  }

  function escapeHtml(s){
    if(!s) return '';
    return String(s).replace(/[&<>"']/g, function(m){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[m]; });
  }

  // initial load
  fetchDocuments();
})();
