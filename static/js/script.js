document.addEventListener("DOMContentLoaded", function() {

    const form = document.querySelector("form");
    const loader = document.getElementById("aiLoader");
    // Upload form handling
    const uploadForm = document.getElementById('uploadForm');
    const uploadResult = document.getElementById('uploadResult');

    if(uploadForm) {
        uploadForm.addEventListener('submit', function(ev) {
            ev.preventDefault();
            loader.classList.remove('hidden');
            uploadResult.classList.add('hidden');

            const fileInput = document.getElementById('uploadImage');
            const data = new FormData();
            if(fileInput.files.length === 0) return alert('Please select an image');
            data.append('image', fileInput.files[0]);
            // CSRF token
            const csrf = document.querySelector('input[name=csrfmiddlewaretoken]').value;

            fetch('/api/predict/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrf
                },
                body: data
            }).then(r => r.json())
            .then(res => {
                loader.classList.add('hidden');
                if(res.status === 'success') {
                    uploadResult.classList.remove('hidden');
                    uploadResult.innerHTML = `
                        <h3>Prediction: ${res.stage_name} (${res.stage})</h3>
                        <p>Confidence: ${res.confidence}%</p>
                        <img src="${res.heatmap_url}" alt="Grad-CAM" style="max-width:100%;height:auto;"/>
                        <p>Prediction ID: ${res.prediction_id}</p>
                    `;
                } else {
                    uploadResult.classList.remove('hidden');
                    uploadResult.innerText = 'Error: ' + (res.message || 'Prediction failed');
                }
            }).catch(err => {
                loader.classList.add('hidden');
                uploadResult.classList.remove('hidden');
                uploadResult.innerText = 'Error: ' + err;
            });
        });
    }

    // Sidebar navigation
    const sidebarItems = document.querySelectorAll('.sidebar nav ul li');
    const sections = {
        'Dashboard': null,
        'Upload Scan': document.getElementById('upload-section'),
        'AI Analysis': document.getElementById('analysis-section'),
        'Grad-CAM': document.getElementById('gradcam-section'),
        'Clinical Report': document.getElementById('report-section')
    };

    sidebarItems.forEach(item => {
        item.addEventListener('click', () => {
            const text = item.innerText.trim();
            // Toggle active class
            sidebarItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            // Hide all sections
            Object.values(sections).forEach(s => { if(s) s.classList.add('hidden'); });

            // Show selected
            if(sections[text]) sections[text].classList.remove('hidden');
        });
    });

    // Analysis fetch
    const btnFetchAnalysis = document.getElementById('btnFetchAnalysis');
    if(btnFetchAnalysis) {
        btnFetchAnalysis.addEventListener('click', () => {
            const id = document.getElementById('analysisPredictionId').value.trim();
            const out = document.getElementById('analysisResult');
            if(!id) return alert('Enter prediction ID');
            out.innerText = 'Loading...';
            fetch(`/api/result/${id}/`).then(r => r.json()).then(res => {
                if(res.status === 'success') {
                    out.innerHTML = `
                        <h3>${res.stage_name} (${res.stage})</h3>
                        <p>Confidence: ${res.confidence}%</p>
                        <img src="${res.heatmap_url}" style="max-width:100%;height:auto;" />
                        <p>Recorded: ${res.created_at}</p>
                    `;
                } else {
                    out.innerText = 'Error: ' + (res.message || 'Could not fetch');
                }
            }).catch(e => out.innerText = 'Error: ' + e);
        });
    }

    // Grad-CAM fetch
    const btnFetchGradcam = document.getElementById('btnFetchGradcam');
    if(btnFetchGradcam) {
        btnFetchGradcam.addEventListener('click', () => {
            const id = document.getElementById('gradcamPredictionId').value.trim();
            const out = document.getElementById('gradcamResult');
            if(!id) return alert('Enter prediction ID');
            out.innerText = 'Loading...';
            fetch(`/api/result/${id}/`).then(r => r.json()).then(res => {
                if(res.status === 'success') {
                    out.innerHTML = `
                        <h3>Grad-CAM for ${res.stage_name}</h3>
                        <img src="${res.heatmap_url}" style="max-width:100%;height:auto;" />
                    `;
                } else {
                    out.innerText = 'Error: ' + (res.message || 'Could not fetch');
                }
            }).catch(e => out.innerText = 'Error: ' + e);
        });
    }

    // Clinical report generation (simple client-side summary)
    const btnFetchReport = document.getElementById('btnFetchReport');
    if(btnFetchReport) {
        btnFetchReport.addEventListener('click', () => {
            const id = document.getElementById('reportPredictionId').value.trim();
            const out = document.getElementById('reportResult');
            if(!id) return alert('Enter prediction ID');
            out.innerText = 'Generating report...';
            fetch(`/api/result/${id}/`).then(r => r.json()).then(res => {
                if(res.status === 'success') {
                    const stage = res.stage_name;
                    const confidence = res.confidence;
                    const summary = `Clinical Summary: The AI classified the retinal image as '${stage}' with a confidence of ${confidence}%. Recommend ophthalmology consult for confirmation and possible fluorescein angiography if indicated.`;
                    out.innerHTML = `<h3>Clinical Report</h3><p>${summary}</p><img src="${res.heatmap_url}" style="max-width:100%;height:auto;" />`;
                } else {
                    out.innerText = 'Error: ' + (res.message || 'Could not fetch');
                }
            }).catch(e => out.innerText = 'Error: ' + e);
        });
    }

});

