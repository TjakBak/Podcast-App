// Search functionality
let searchTimeout;

const searchInput = document.getElementById('searchInput');
const resultsDiv = document.getElementById('results');
const loadingDiv = document.getElementById('loading');
const sortRadios = document.querySelectorAll('input[name="sort"]');
const limitSelect = document.getElementById('limitSelect');

// Debounced search function
function performSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        const query = searchInput.value.trim();
        const sort = document.querySelector('input[name="sort"]:checked').value;
        const limit = limitSelect.value;

        // Show loading
        loadingDiv.style.display = 'block';
        resultsDiv.innerHTML = '';

        // Build query string
        const params = new URLSearchParams();
        if (query) params.append('q', query);
        params.append('sort', sort);
        params.append('limit', limit);

        // Fetch results
        fetch(`/search?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                loadingDiv.style.display = 'none';
                displayResults(data.results, data.count);
            })
            .catch(error => {
                loadingDiv.style.display = 'none';
                resultsDiv.innerHTML = '<p class="info-text" style="color: red;">Error loading results. Please try again.</p>';
                console.error('Error:', error);
            });
    }, 300); // Wait 300ms after user stops typing
}

function displayResults(episodes, count) {
    if (episodes.length === 0) {
        resultsDiv.innerHTML = '<p class="info-text">No episodes found. Try a different search term.</p>';
        return;
    }

    let html = `<div class="results-count">Found ${count} episode${count !== 1 ? 's' : ''}</div>`;

    episodes.forEach(episode => {
        const title = escapeHtml(episode.title || 'Untitled');
        const description = escapeHtml(episode.description || '');
        const shortDesc = description.length > 300 ? description.substring(0, 300) + '...' : description;
        const date = episode.formatted_date || episode.short_date || 'Unknown date';
        const audioUrl = episode.audio_url || '';

        html += `
            <div class="episode-card">
                <h3>${title}</h3>
                <div class="episode-date">${date}</div>
                ${shortDesc ? `<div class="episode-description">${shortDesc}</div>` : ''}
                ${audioUrl ? `
                    <div class="episode-audio">
                        <audio controls preload="none">
                            <source src="${escapeHtml(audioUrl)}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                        <a href="${escapeHtml(audioUrl)}" target="_blank" class="audio-link">Open Audio Link</a>
                    </div>
                ` : ''}
            </div>
        `;
    });

    resultsDiv.innerHTML = html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Event listeners
searchInput.addEventListener('input', performSearch);
sortRadios.forEach(radio => radio.addEventListener('change', performSearch));
limitSelect.addEventListener('change', performSearch);

// Allow Enter key to search
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        performSearch();
    }
});

// Initial search on page load (show all episodes)
window.addEventListener('load', () => {
    // Only search if there are episodes in the database
    const totalEpisodes = parseInt(document.querySelector('.stat-value')?.textContent || '0');
    if (totalEpisodes > 0) {
        performSearch();
    }
});
