document.addEventListener('DOMContentLoaded', () => {

    // --- MODE SELECTION ---
    const startupChoiceDiv = document.getElementById('startup-choice');
    const onlineModeDiv = document.getElementById('online-mode');
    const ocrModeDiv = document.getElementById('ocr-mode');

    // --- NEW: Navigation Reset Logic ---
    const homeLink = document.getElementById('home-link');

    // Get references to all content areas
    const headlinesContainer = document.getElementById('headlines-container');
    const articleContainer = document.getElementById('article-container');
    const summaryContainer = document.getElementById('summary-container');
    const ocrResultContainer = document.getElementById('ocr-result-container');

    function resetToHome() {
        // Hide all modes and results
        onlineModeDiv.style.display = 'none';
        ocrModeDiv.style.display = 'none';

        // Also reset and hide any content inside the modes
        headlinesContainer.innerHTML = '<p class="loading-message">Please select a news source.</p>';
        articleContainer.innerHTML = '';
        summaryContainer.innerHTML = '';
        ocrResultContainer.innerHTML = '';

        // Show the startup choice
        startupChoiceDiv.style.display = 'block';
    }

    // When the user clicks "Home", reset the UI
    if (homeLink) { // Check if the link exists on this page
        homeLink.addEventListener('click', (e) => {
            // Check if we are on the main page
            if (window.location.pathname === '/') {
                e.preventDefault(); // Stop the page from reloading
                resetToHome();
            }
            // If on /history, let the link work normally
        });
    }
    // --- END of NEW Navigation Logic ---

    // When user clicks "Summarize an Online Article"
    document.getElementById('btn-show-online').addEventListener('click', () => {
        startupChoiceDiv.style.display = 'none';
        onlineModeDiv.style.display = 'block';
    });

    // When user clicks "Summarize from Newspaper Image"
    document.getElementById('btn-show-ocr').addEventListener('click', () => {
        startupChoiceDiv.style.display = 'none';
        ocrModeDiv.style.display = 'block';
    });

    // --- ONLINE MODE CODE ---

    document.querySelectorAll('.publisher-btn').forEach(button => {
        button.addEventListener('click', (event) => {
            const publisher = event.target.dataset.publisher;
            fetchHeadlines(publisher);
        });
    });

    function fetchHeadlines(publisher) {
        let sourceName = "Unknown";
        if (publisher === 'toi') {
            sourceName = "TOI (India)";
        } else if (publisher === 'gnews') {
            sourceName = "World News (from Google)";
        }

        headlinesContainer.innerHTML = `<p class="loading-message">Loading news from ${sourceName}...</p>`;
        articleContainer.innerHTML = '';
        summaryContainer.innerHTML = '';

        fetch(`/api/headlines/${publisher}`)
            .then(response => response.json())
            .then(headlines => {
                headlinesContainer.innerHTML = `<h2>Top Stories from ${sourceName}</h2>`;
                if (!headlines || headlines.length === 0) {
                    headlinesContainer.innerHTML += '<p>Could not fetch headlines. The RSS feed may be down.</p>';
                    return;
                }
                const ul = document.createElement('ul');
                ul.className = 'headline-list';
                headlines.forEach(article => {
                    const li = document.createElement('li');
                    const a = document.createElement('a');
                    a.href = article.url;
                    a.textContent = article.headline;
                    a.addEventListener('click', e => {
                        e.preventDefault();
                        fetchArticle(article.url);
                    });
                    li.appendChild(a);
                    ul.appendChild(li);
                });
                headlinesContainer.appendChild(ul);
            });
    }

    function fetchArticle(url) {
        articleContainer.innerHTML = `<p class="loading-message">Fetching full article (this may take up to a minute)...</p>`;
        summaryContainer.innerHTML = '';
        articleContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });

        fetch('/api/get_article', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url }),
                signal: AbortSignal.timeout(120000)
            })
            .then(response => response.json())
            .then(data => {
                if (!data || !data.article_text || data.article_text.includes("Could not") || data.article_text.includes("blocking") || data.article_text.includes("unrecognized")) {
                    articleContainer.innerHTML = `<p class="loading-message">${data.article_text || 'Error: Could not fetch article content.'}</p>`;
                    return;
                }
                articleContainer.innerHTML = `
                <div class="article-content">
                    <h2>Full Article</h2>
                    <p id="full-article-text">${data.article_text.replace(/\n/g, '<br>')}</p>
                    <button id="summarize-btn">Summarize This Article</button>
                </div>`;
                document.getElementById('summarize-btn').addEventListener('click', () => {
                    const text = document.getElementById('full-article-text').innerText;
                    fetchSummary(text, "Online Article");
                });
            })
            .catch(error => {
                console.error('Fetch article error:', error);
                articleContainer.innerHTML = `<p class="loading-message">Error: The request took too long and timed out.</p>`;
            });
    }

    function fetchSummary(text, source) {
        summaryContainer.innerHTML = '<p class="loading-message">🤖 AI is summarizing (this may take a moment for long articles)...</p>';
        summaryContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });

        fetch('/api/summarize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text, source: source }),
            })
            .then(response => response.json())
            .then(data => {
                summaryContainer.innerHTML = `
                    <div class="summary-content">
                        <h2>AI Summary</h2>
                        <h4 class="category-tag">Category: ${data.category}</h4>
                        <p>${data.summary}</p>
                    </div>`;
                summaryContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
    }

    // --- "HUMAN-IN-THE-LOOP" OCR CODE ---

    const ocrUploadInput = document.getElementById('ocr-upload-input');
    const ocrImageContainer = document.getElementById('ocr-image-container');
    const ocrInstructions = document.getElementById('ocr-instructions');
    const ocrButtonContainer = document.getElementById('ocr-button-container');
    const ocrSubmitGapsBtn = document.getElementById('ocr-submit-gaps');
    const ocrResetGapsBtn = document.getElementById('ocr-reset-gaps');

    let currentImageFile = null;
    let gapCoordinates = []; // Stores the x-coordinates of the user's clicks

    // 1. When user uploads a file
    ocrUploadInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        currentImageFile = file;
        gapCoordinates = []; // Reset gaps
        ocrImageContainer.innerHTML = ''; // Clear old image

        const reader = new FileReader();
        reader.onload = (event) => {
            const img = document.createElement('img');
            img.src = event.target.result;

            // When the image loads, add it to the container
            img.onload = () => {
                ocrImageContainer.appendChild(img);
                ocrInstructions.style.display = 'block';
                ocrButtonContainer.style.display = 'flex';

                // Add the click listener to the image
                img.addEventListener('click', drawGapLine);
            }
        };
        reader.readAsDataURL(file);
    });

    // 2. When user clicks on the image
    function drawGapLine(e) {
        // Get the x-coordinate relative to the image
        const img = e.target;
        const rect = img.getBoundingClientRect();
        const scaleX = img.naturalWidth / rect.width;
        const x_coord = (e.clientX - rect.left) * scaleX;

        // Store the *actual* image coordinate
        gapCoordinates.push(Math.round(x_coord));

        // Draw the visual line (relative to the container)
        const displayX = (e.clientX - rect.left);
        const line = document.createElement('div');
        line.className = 'gap-line';
        line.style.left = `${displayX}px`;
        ocrImageContainer.appendChild(line);
    }

    // 3. When user clicks "Reset"
    ocrResetGapsBtn.addEventListener('click', () => {
        currentImageFile = null;
        gapCoordinates = [];
        ocrImageContainer.innerHTML = '';
        ocrResultContainer.innerHTML = '';
        ocrUploadInput.value = null; // Reset file input
        ocrInstructions.style.display = 'none';
        ocrButtonContainer.style.display = 'none';
    });

    // 4. When user clicks "Summarize"
    ocrSubmitGapsBtn.addEventListener('click', () => {
        if (!currentImageFile) {
            ocrResultContainer.innerHTML = `<p class="loading-message">Please upload an image first.</p>`;
            return;
        }

        // This is a common-sense check: if 0 gaps are marked, process as 1 column
        // We will just send an empty array, and the backend will handle it.

        ocrResultContainer.innerHTML = `<p class="loading-message">Uploading and processing image... (this may take a minute)</p>`;
        ocrResultContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });

        const formData = new FormData();
        formData.append('image', currentImageFile);

        // Sort the gaps and send them as JSON
        gapCoordinates.sort((a, b) => a - b);
        formData.append('gaps', JSON.stringify(gapCoordinates));

        fetch('/api/ocr-summarize-manual', {
                method: 'POST',
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    ocrResultContainer.innerHTML = `<p class="loading-message">${data.error}</p>`;
                    return;
                }

                // Display results
                ocrResultContainer.innerHTML = `
                <div class="article-content">
                    <h2>Extracted Text</h2>
                    <p>${data.extracted_text.replace(/\n/g, '<br>')}</p>
                </div>
                <div class="summary-content">
                    <h2>AI Summary</h2>
                    <h4 class="category-tag">Category: ${data.category}</h4>
                    <p>${data.summary}</p>
                </div>
            `;
                ocrResultContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            })
            .catch(error => {
                console.error('OCR Error:', error);
                ocrResultContainer.innerHTML = `<p class="loading-message">An error occurred during the OCR process.</p>`;
            });
    });
});