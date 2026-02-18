document.addEventListener("DOMContentLoaded", function() {

    const form = document.querySelector("form");
    const loader = document.getElementById("aiLoader");
    // Note: Upload uses server-rendered POST (no AJAX) so results are returned
    // by the server and displayed when the page reloads. We don't intercept submit.

    // Sidebar navigation
    const sidebarItems = document.querySelectorAll('.sidebar nav ul li');
    const dynamicSection = document.getElementById('dynamicSection');
    const sections = {
        'Dashboard': null,
        'Upload Scan': document.getElementById('upload-section'),
        'AI Analysis': dynamicSection,
        'Grad-CAM': dynamicSection,
        'Clinical Report': dynamicSection
    };

    function fetchLatestPrediction() {
        // Returns a Promise that resolves to the api_result JSON for the latest prediction or null
        return fetch('/api/history/').then(r => r.json()).then(h => {
            if(h.status === 'success' && h.count > 0) {
                const latest = h.predictions[0];
                const id = latest.id;
                return fetch(`/api/result/${id}/`).then(r2 => r2.json()).then(res => {
                    if(res.status === 'success') return res;
                    return null;
                }).catch(() => null);
            }
            return null;
        }).catch(() => null);
    }

    function renderUploadOnly(res) {
        const container = document.getElementById('uploadOnlyContent');
        if(!res) {
            container.innerHTML = '<p>No scans available.</p>';
            return;
        }
        container.innerHTML = `
            <h4>${res.stage_name} (${res.stage})</h4>
            <p>Confidence: ${res.confidence}%</p>
            <img src="${res.heatmap_url}" style="max-width:100%;height:auto;" />
            <p>Recorded: ${res.created_at || ''}</p>
        `;
    }

    function renderAnalysis(res) {
        const out = dynamicSection;
        if(!res) { out.innerHTML = '<p>No analysis available.</p>'; return; }
        out.innerHTML = `
            <section class="card">
              <h3>AI Analysis</h3>
              <p><strong>Stage:</strong> ${res.stage_name} (${res.stage})</p>
              <p><strong>Confidence:</strong> ${res.confidence}%</p>
              <p><strong>Model:</strong> ResNet50 (fine-tuned)</p>
              <h4>Heatmap</h4>
              <img src="${res.heatmap_url}" style="max-width:100%;height:auto;" />
            </section>
        `;
    }

    function renderGradcam(res) {
        const out = dynamicSection;
        if(!res) { out.innerHTML = '<p>No Grad-CAM available.</p>'; return; }
        out.innerHTML = `
            <section class="card">
              <h3>Grad-CAM</h3>
              <img src="${res.heatmap_url}" style="max-width:100%;height:auto;" />
            </section>
        `;
    }

    function renderReport(res) {
        const out = dynamicSection;
        if(!res) { out.innerHTML = '<p>No report available.</p>'; return; }
        const stage = res.stage_name;
        const confidence = res.confidence;
        const summary = `Clinical Summary: The AI classified the retinal image as '${stage}' with a confidence of ${confidence}%. Recommend ophthalmology consult for confirmation and consider further imaging or specialist referral as needed.`;
        out.innerHTML = `
            <section class="card">
              <h3>Clinical Report</h3>
              <p>${summary}</p>
              <img src="${res.heatmap_url}" style="max-width:100%;height:auto;" />
            </section>
        `;
    }

    sidebarItems.forEach(item => {
        item.addEventListener('click', () => {
            const text = item.innerText.trim();
            // Toggle active class
            sidebarItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            // Hide all sections
            Object.values(sections).forEach(s => { if(s) s.classList.add('hidden'); });

            // Show selected
            const section = sections[text];
            if(section) section.classList.remove('hidden');

            // Special handling: Dashboard vs Upload Scan
            const uploadFormWrapper = document.getElementById('uploadFormWrapper');
            const uploadResultOnly = document.getElementById('uploadResultOnly');
            if(text === 'Dashboard') {
                if(uploadFormWrapper) uploadFormWrapper.classList.remove('hidden');
                if(uploadResultOnly) uploadResultOnly.classList.add('hidden');
                return;
            }

            if(text === 'Upload Scan') {
                // Show result-only view (hide upload form)
                if(uploadFormWrapper) uploadFormWrapper.classList.add('hidden');
                if(uploadResultOnly) uploadResultOnly.classList.remove('hidden');
                fetchLatestPrediction().then(res => renderUploadOnly(res));
                return;
            }

            // For analysis, gradcam, report: fetch latest then render accordingly
            if(text === 'AI Analysis') {
                fetchLatestPrediction().then(res => renderAnalysis(res));
            } else if(text === 'Grad-CAM') {
                fetchLatestPrediction().then(res => renderGradcam(res));
            } else if(text === 'Clinical Report') {
                fetchLatestPrediction().then(res => renderReport(res));
            }
        });
    });

    // Removed legacy per-ID handlers; UI now fetches latest prediction when sidebar items are clicked.

});

