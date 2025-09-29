// Admin Panel JavaScript
class MovieAdminPanel {
    constructor() {
        this.apiBase = 'http://127.0.0.1:8003';
        this.authToken = localStorage.getItem('admin_token');
        this.movies = [];
        this.filteredMovies = [];
        this.selectedMovies = new Set();
        this.pipeline = [];
        this.staging = [];
        this.logs = [];
        this.currentPage = 1;
        this.itemsPerPage = 50;
        this.scrapedMovies = [];
        
        this.init();
    }

    init() {
        // Check authentication
        if (!this.authToken) {
            this.redirectToLogin();
            return;
        }
        
        this.setupEventListeners();
        this.loadDashboard();
        this.log('Admin panel initialized', 'info');
    }

    redirectToLogin() {
        window.location.href = 'admin_login.html';
    }

    getAuthHeaders() {
        return {
            'Authorization': `Bearer ${this.authToken}`,
            'Content-Type': 'application/json'
        };
    }

    logout() {
        localStorage.removeItem('admin_token');
        this.redirectToLogin();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.showPage(page);
            });
        });

        // Movie selection
        document.getElementById('selectAllCheckbox')?.addEventListener('change', (e) => {
            this.toggleSelectAll(e.target.checked);
        });

        // Scraped movie selection
        document.getElementById('selectAllScraped')?.addEventListener('change', (e) => {
            this.toggleSelectAllScraped(e.target.checked);
        });

        // Search and filters
        document.getElementById('movieSearch')?.addEventListener('input', (e) => {
            this.debounce(() => this.filterMovies(), 300);
        });

        // API base configuration
        const apiBaseInput = document.getElementById('apiBaseInput');
        if (apiBaseInput) {
            apiBaseInput.value = this.apiBase;
            apiBaseInput.addEventListener('change', (e) => {
                this.apiBase = e.target.value;
                this.log(`API base changed to: ${this.apiBase}`, 'info');
            });
        }

        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }

        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            this.stopEnrichmentPolling();
        });

        // Close preview modal when clicking outside
        document.addEventListener('click', (e) => {
            const previewModal = document.getElementById('moviePreviewModal');
            if (previewModal && e.target === previewModal) {
                this.closePreview();
            }
        });

        // Close preview modal with ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const previewModal = document.getElementById('moviePreviewModal');
                if (previewModal && previewModal.style.display === 'block') {
                    this.closePreview();
                }
            }
        });
    }

    // Navigation
    showPage(pageName) {
        // Stop enrichment polling if leaving enrichment page
        if (this.currentPage === 'enrichment' && pageName !== 'enrichment') {
            this.stopEnrichmentPolling();
        }

        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-page="${pageName}"]`).classList.add('active');

        // Show page content
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        document.getElementById(pageName).classList.add('active');

        // Update current page
        this.currentPage = pageName;

        // Load page-specific data
        switch(pageName) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'movies':
                this.loadMovies();
                break;
            case 'scraping':
                this.loadScrapingPage();
                break;
            case 'enrichment':
                this.loadEnrichmentPage();
                break;
            case 'merge':
                this.loadMergePage();
                break;
            case 'logs':
                this.loadLogs();
                break;
        }
    }

    // Dashboard
    async loadDashboard() {
        try {
            this.log('Loading dashboard data...', 'info');
            
            // Load movie data
            const response = await fetch(`${this.apiBase}/admin/dashboard`, {
                headers: this.getAuthHeaders()
            });
            if (!response.ok) {
                if (response.status === 401) {
                    this.redirectToLogin();
                    return;
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.updateDashboardStats(data);
            this.log('Dashboard data loaded successfully', 'success');
            
        } catch (error) {
            this.log(`Failed to load dashboard: ${error.message}`, 'error');
            this.showAlert('Failed to load dashboard data. Please check your API connection.', 'error');
        }
    }

    updateDashboardStats(data) {
        // Update stat cards
        document.getElementById('totalMovies').textContent = data.totalMovies || 0;
        document.getElementById('completeProfiles').textContent = data.completeProfiles || 0;
        document.getElementById('withImages').textContent = data.withImages || 0;
        document.getElementById('hiddenMovies').textContent = data.hiddenMovies || 0;

        // Update change indicators
        document.getElementById('totalMoviesChange').textContent = `${data.totalMovies} total movies`;
        document.getElementById('completeProfilesChange').textContent = `${data.completeProfiles} complete`;
        document.getElementById('withImagesChange').textContent = `${data.withImages} with images`;
        document.getElementById('hiddenMoviesChange').textContent = `${data.hiddenMovies} hidden`;
        // Update progress bars
        const profileProgress = (data.completeProfiles / data.totalMovies) * 100;
        const imageProgress = (data.withImages / data.totalMovies) * 100;
        const metadataProgress = (data.metadataComplete / data.totalMovies) * 100;

        document.getElementById('profileProgress').style.width = `${profileProgress}%`;
        document.getElementById('imageProgress').style.width = `${imageProgress}%`;
        document.getElementById('metadataProgress').style.width = `${metadataProgress}%`;

        document.getElementById('profileProgressText').textContent = 
            `${data.completeProfiles}/${data.totalMovies} movies (${profileProgress.toFixed(1)}%)`;
        document.getElementById('imageProgressText').textContent = 
            `${data.withImages}/${data.totalMovies} movies (${imageProgress.toFixed(1)}%)`;
        document.getElementById('metadataProgressText').textContent = 
            `${data.metadataComplete}/${data.totalMovies} movies (${metadataProgress.toFixed(1)}%)`;
    }

    // Movies Management
    async loadMovies() {
        try {
            this.log('Loading movies data...', 'info');
            
            const response = await fetch(`${this.apiBase}/admin/movies`, {
                headers: this.getAuthHeaders()
            });
            if (!response.ok) {
                if (response.status === 401) {
                    this.redirectToLogin();
                    return;
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.movies = data.movies || [];
            this.filteredMovies = [...this.movies];
            this.renderMoviesTable();
            this.log(`Loaded ${this.movies.length} movies`, 'success');
            
        } catch (error) {
            this.log(`Failed to load movies: ${error.message}`, 'error');
            this.showAlert('Failed to load movies data.', 'error');
        }
    }

    renderMoviesTable() {
        const tbody = document.getElementById('moviesTableBody');
        if (!tbody) return;

        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageMovies = this.filteredMovies.slice(startIndex, endIndex);

        if (pageMovies.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 40px; color: #666;">
                        No movies found
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = pageMovies.map(movie => {
            const status = this.getMovieStatus(movie);
            const quality = this.getDataQuality(movie);
            const isSelected = this.selectedMovies.has(movie.title);
            
            // Escape movie title for use in HTML attributes - more comprehensive escaping
            const escapedTitle = movie.title
                .replace(/\\/g, '\\\\')  // Escape backslashes first
                .replace(/'/g, "\\'")    // Escape single quotes
                .replace(/"/g, '\\"')    // Escape double quotes
                .replace(/\n/g, '\\n')   // Escape newlines
                .replace(/\r/g, '\\r')   // Escape carriage returns
                .replace(/\t/g, '\\t');  // Escape tabs

            return `
                <tr>
                    <td>
                        <input type="checkbox" ${isSelected ? 'checked' : ''} 
                               onchange="adminPanel.toggleMovieSelection('${escapedTitle}')">
                    </td>
                    <td>
                        <strong>${movie.title}</strong>
                        ${movie.hidden ? '<span class="status-badge status-hidden">Hidden</span>' : ''}
                    </td>
                    <td>${movie.director || 'Unknown'}</td>
                    <td>${movie.year || 'Unknown'}</td>
                    <td><span class="status-badge status-${status}">${status}</span></td>
                    <td>${quality}</td>
                    <td>
                        <button class="btn btn-secondary" onclick="adminPanel.toggleMovieVisibility('${escapedTitle}')">
                            ${movie.hidden ? 'Show' : 'Hide'}
                        </button>
                        <button class="btn" onclick="adminPanel.enrichMovie('${escapedTitle}')">
                            Enrich
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        this.renderPagination();
    }

    getMovieStatus(movie) {
        if (movie.hidden) return 'hidden';
        if (movie.profile_text && movie.poster_url && movie.director) return 'complete';
        if (movie.profile_text || movie.poster_url || movie.director) return 'partial';
        return 'missing';
    }

    getDataQuality(movie) {
        const issues = [];
        if (!movie.poster_url) issues.push('No poster');
        if (!movie.plot_summary) issues.push('No plot');
        if (!movie.director) issues.push('No director');
        if (!movie.profile_text) issues.push('No profile');
        
        return issues.length === 0 ? 'Complete' : issues.join(', ');
    }

    // Movie Selection
    toggleMovieSelection(title) {
        console.log('toggleMovieSelection called with title:', title);
        console.log('Current selectedMovies before:', this.selectedMovies);
        
        if (this.selectedMovies.has(title)) {
            this.selectedMovies.delete(title);
            console.log('Removed from selection');
        } else {
            this.selectedMovies.add(title);
            console.log('Added to selection');
        }
        
        console.log('Current selectedMovies after:', this.selectedMovies);
        this.updateSelectAllCheckbox();
    }

    toggleSelectAll(checked) {
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageMovies = this.filteredMovies.slice(startIndex, endIndex);

        pageMovies.forEach(movie => {
            if (checked) {
                this.selectedMovies.add(movie.title);
            } else {
                this.selectedMovies.delete(movie.title);
            }
        });

        this.renderMoviesTable();
    }

    updateSelectAllCheckbox() {
        const checkbox = document.getElementById('selectAllCheckbox');
        if (!checkbox) return;

        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageMovies = this.filteredMovies.slice(startIndex, endIndex);
        
        const selectedOnPage = pageMovies.filter(movie => this.selectedMovies.has(movie.title)).length;
        
        checkbox.checked = selectedOnPage === pageMovies.length && pageMovies.length > 0;
        checkbox.indeterminate = selectedOnPage > 0 && selectedOnPage < pageMovies.length;
    }

    // Filtering
    filterMovies() {
        const searchTerm = document.getElementById('movieSearch')?.value.toLowerCase() || '';
        const statusFilter = document.getElementById('statusFilter')?.value || '';
        const qualityFilter = document.getElementById('qualityFilter')?.value || '';

        this.filteredMovies = this.movies.filter(movie => {
            // Search filter
            if (searchTerm) {
                const searchable = `${movie.title} ${movie.director} ${movie.year}`.toLowerCase();
                if (!searchable.includes(searchTerm)) return false;
            }

            // Status filter
            if (statusFilter) {
                const status = this.getMovieStatus(movie);
                if (status !== statusFilter) return false;
            }

            // Quality filter
            if (qualityFilter) {
                switch(qualityFilter) {
                    case 'no-poster':
                        if (movie.poster_url) return false;
                        break;
                    case 'no-plot':
                        if (movie.plot_summary) return false;
                        break;
                    case 'no-director':
                        if (movie.director) return false;
                        break;
                    case 'no-profile':
                        if (movie.profile_text) return false;
                        break;
                }
            }

            return true;
        });

        this.currentPage = 1;
        this.renderMoviesTable();
    }

    clearFilters() {
        document.getElementById('movieSearch').value = '';
        document.getElementById('statusFilter').value = '';
        document.getElementById('qualityFilter').value = '';
        this.filteredMovies = [...this.movies];
        this.currentPage = 1;
        this.renderMoviesTable();
    }

    // Pagination
    renderPagination() {
        const pagination = document.getElementById('moviesPagination');
        if (!pagination) return;

        const totalPages = Math.ceil(this.filteredMovies.length / this.itemsPerPage);
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        let paginationHTML = '';
        
        // Previous button
        paginationHTML += `
            <button ${this.currentPage === 1 ? 'disabled' : ''} 
                    onclick="adminPanel.goToPage(${this.currentPage - 1})">
                Previous
            </button>
        `;

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= this.currentPage - 2 && i <= this.currentPage + 2)) {
                paginationHTML += `
                    <button class="${i === this.currentPage ? 'active' : ''}" 
                            onclick="adminPanel.goToPage(${i})">
                        ${i}
                    </button>
                `;
            } else if (i === this.currentPage - 3 || i === this.currentPage + 3) {
                paginationHTML += '<span>...</span>';
            }
        }

        // Next button
        paginationHTML += `
            <button ${this.currentPage === totalPages ? 'disabled' : ''} 
                    onclick="adminPanel.goToPage(${this.currentPage + 1})">
                Next
            </button>
        `;

        pagination.innerHTML = paginationHTML;
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredMovies.length / this.itemsPerPage);
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.renderMoviesTable();
        }
    }

    // Individual movie operations
    async toggleMovieVisibility(title) {
        try {
            console.log('toggleMovieVisibility called with title:', title);
            
            // Find the movie to check its current hidden status
            const movie = this.movies.find(m => m.title === title);
            if (!movie) {
                console.log('Movie not found:', title);
                this.showAlert('Movie not found.', 'error');
                return;
            }

            const isCurrentlyHidden = movie.hidden;
            const action = isCurrentlyHidden ? 'show' : 'hide';
            
            console.log(`Action: ${action}, Currently hidden: ${isCurrentlyHidden}`);
            this.log(`${action === 'show' ? 'Showing' : 'Hiding'} movie: ${title}`, 'info');
            
            const response = await fetch(`${this.apiBase}/admin/movies/${action}`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({ titles: [title] })
            });

            console.log('API response status:', response.status);
            if (!response.ok) {
                const errorText = await response.text();
                console.log('API error response:', errorText);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('API response:', result);
            
            this.log(`Successfully ${action === 'show' ? 'showed' : 'hid'} movie: ${title}`, 'success');
            this.loadMovies();
            this.loadDashboard();
            
        } catch (error) {
            console.error('toggleMovieVisibility error:', error);
            this.log(`Failed to toggle movie visibility: ${error.message}`, 'error');
            this.showAlert('Failed to toggle movie visibility.', 'error');
        }
    }

    // Bulk Operations
    async hideSelected() {
        console.log('hideSelected called, selectedMovies:', this.selectedMovies);
        
        if (this.selectedMovies.size === 0) {
            console.log('No movies selected');
            this.showAlert('Please select movies to hide.', 'warning');
            return;
        }

        try {
            const titlesToHide = Array.from(this.selectedMovies);
            console.log('Hiding movies:', titlesToHide);
            
            this.log(`Hiding ${this.selectedMovies.size} movies...`, 'info');
            
            const response = await fetch(`${this.apiBase}/admin/movies/hide`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({ titles: titlesToHide })
            });

            console.log('API response status:', response.status);
            if (!response.ok) {
                const errorText = await response.text();
                console.log('API error response:', errorText);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('API response:', result);
            
            this.log(`Successfully hid ${this.selectedMovies.size} movies`, 'success');
            
            // Don't clear selection immediately - let user see what was hidden
            console.log('Movies that were hidden:', Array.from(this.selectedMovies));
            
            // Refresh the data
            await this.loadMovies();
            await this.loadDashboard();
            
            // Clear selection after refresh
            this.selectedMovies.clear();
            console.log('Selection cleared after refresh');
            
        } catch (error) {
            console.error('hideSelected error:', error);
            this.log(`Failed to hide movies: ${error.message}`, 'error');
            this.showAlert('Failed to hide selected movies.', 'error');
        }
    }

    async showSelected() {
        if (this.selectedMovies.size === 0) {
            this.showAlert('Please select movies to show.', 'warning');
            return;
        }

        try {
            this.log(`Showing ${this.selectedMovies.size} movies...`, 'info');
            
            const response = await fetch(`${this.apiBase}/admin/movies/show`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({ titles: Array.from(this.selectedMovies) })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.log(`Successfully showed ${this.selectedMovies.size} movies`, 'success');
            this.selectedMovies.clear();
            this.loadMovies();
            this.loadDashboard();
            
        } catch (error) {
            this.log(`Failed to show movies: ${error.message}`, 'error');
            this.showAlert('Failed to show selected movies.', 'error');
        }
    }

    // Scraping
    async searchDirector() {
        const directorName = document.getElementById('directorName').value.trim();
        if (!directorName) {
            this.showAlert('Please enter a director name.', 'warning');
            return;
        }

        try {
            this.log(`Searching for movies by director: ${directorName}`, 'info');
            
            const response = await fetch(`${this.apiBase}/admin/scrape/director`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({ 
                    director: directorName,
                    includeShorts: document.getElementById('includeShorts').checked,
                    includeTV: document.getElementById('includeTV').checked,
                    includeDocumentaries: document.getElementById('includeDocumentaries').checked
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.displayScrapingResults(data.movies);
            this.log(`Found ${data.movies.length} movies for ${directorName}`, 'success');
            
        } catch (error) {
            this.log(`Failed to search director: ${error.message}`, 'error');
            this.showAlert('Failed to search for director movies.', 'error');
        }
    }

    // Enrichment
    async enrichMovie(title) {
        try {
            this.log(`Enriching movie: ${title}`, 'info');
            
            // Get the movie data
            const movie = this.movies.find(m => m.title === title);
            if (!movie) {
                this.showAlert('Movie not found.', 'error');
                return;
            }

            // Show immediate feedback
            this.showAlert(`Adding ${title} to enrichment pipeline...`, 'info');

            // Add to staging area
            const response = await fetch(`${this.apiBase}/admin/pipeline/add`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify([movie])
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.showAlert(`Starting enrichment for ${title}...`, 'info');

            // Start enrichment pipeline
            const enrichResponse = await fetch(`${this.apiBase}/admin/enrichment/start`, {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (!enrichResponse.ok) {
                throw new Error(`HTTP ${enrichResponse.status}: ${enrichResponse.statusText}`);
            }

            this.log(`Successfully started enrichment for ${title}`, 'success');
            this.showAlert(`Enrichment completed for ${title}`, 'success');
            
            // Refresh data immediately
            this.loadMovies(); // Refresh the movies list
            this.loadPipelineStatus(); // Refresh pipeline status
            
            // Start polling for updates
            this.startEnrichmentPolling();
            
        } catch (error) {
            this.log(`Failed to enrich movie: ${error.message}`, 'error');
            this.showAlert('Failed to enrich movie.', 'error');
        }
    }

    async enrichSelected() {
        if (this.selectedMovies.size === 0) {
            this.showAlert('Please select movies to enrich.', 'warning');
            return;
        }

        try {
            this.log(`Enriching ${this.selectedMovies.size} movies...`, 'info');
            
            // Show immediate feedback
            this.showAlert(`Adding ${this.selectedMovies.size} movies to enrichment pipeline...`, 'info');
            
            // Get selected movie data
            const selectedMovieData = this.movies.filter(m => this.selectedMovies.has(m.title));
            
            // Add to staging area
            const response = await fetch(`${this.apiBase}/admin/pipeline/add`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(selectedMovieData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.showAlert(`Starting enrichment for ${this.selectedMovies.size} movies...`, 'info');

            // Start enrichment pipeline
            const enrichResponse = await fetch(`${this.apiBase}/admin/enrichment/start`, {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (!enrichResponse.ok) {
                throw new Error(`HTTP ${enrichResponse.status}: ${enrichResponse.statusText}`);
            }

            this.log(`Successfully started enrichment for ${this.selectedMovies.size} movies`, 'success');
            this.showAlert(`Enrichment completed for ${this.selectedMovies.size} movies`, 'success');
            this.selectedMovies.clear();
            
            // Refresh data immediately
            this.loadMovies(); // Refresh the movies list
            this.loadPipelineStatus(); // Refresh pipeline status
            
            // Start polling for updates
            this.startEnrichmentPolling();
            
        } catch (error) {
            this.log(`Failed to enrich movies: ${error.message}`, 'error');
            this.showAlert('Failed to enrich selected movies.', 'error');
        }
    }

    // Enrichment Panel
    async loadEnrichmentPage() {
        try {
            await this.loadPipelineStatus();
            await this.loadEnrichmentLogs();
            // Start periodic updates when on enrichment page
            this.startEnrichmentPolling();
        } catch (error) {
            this.log(`Failed to load enrichment page: ${error.message}`, 'error');
        }
    }

    startEnrichmentPolling() {
        // Clear any existing polling
        if (this.enrichmentPollingInterval) {
            clearInterval(this.enrichmentPollingInterval);
        }

        // Start polling every 2 seconds for 30 seconds
        let pollCount = 0;
        const maxPolls = 15; // 30 seconds total

        this.enrichmentPollingInterval = setInterval(async () => {
            try {
                await this.loadPipelineStatus();
                await this.loadEnrichmentLogs();
                pollCount++;
                
                if (pollCount >= maxPolls) {
                    clearInterval(this.enrichmentPollingInterval);
                    this.enrichmentPollingInterval = null;
                }
            } catch (error) {
                console.warn('Enrichment polling error:', error);
            }
        }, 2000);
    }

    stopEnrichmentPolling() {
        if (this.enrichmentPollingInterval) {
            clearInterval(this.enrichmentPollingInterval);
            this.enrichmentPollingInterval = null;
        }
    }

    async loadPipelineStatus() {
        try {
            const response = await fetch(`${this.apiBase}/admin/pipeline`, {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.redirectToLogin();
                    return;
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Update pipeline status display
            const pipelineCountElement = document.getElementById('pipelineCount');
            const currentOperationElement = document.getElementById('currentOperation');
            
            if (pipelineCountElement) {
                const totalCount = (data.pipelineCount || 0) + (data.stagingCount || 0);
                pipelineCountElement.textContent = totalCount;
                
                // Update breakdown information
                const breakdownElement = document.getElementById('pipelineBreakdown');
                if (breakdownElement) {
                    if (data.pipelineCount > 0 && data.stagingCount > 0) {
                        breakdownElement.textContent = `${data.pipelineCount} processing, ${data.stagingCount} in staging`;
                    } else if (data.pipelineCount > 0) {
                        breakdownElement.textContent = `${data.pipelineCount} processing`;
                    } else if (data.stagingCount > 0) {
                        breakdownElement.textContent = `${data.stagingCount} in staging (ready to process)`;
                    } else {
                        breakdownElement.textContent = '';
                    }
                }
            }
            
            if (currentOperationElement) {
                const isProcessing = data.pipelineCount > 0;
                const hasStaging = data.stagingCount > 0;
                
                if (isProcessing) {
                    currentOperationElement.textContent = 'Processing';
                    currentOperationElement.className = 'processing';
                } else if (hasStaging) {
                    currentOperationElement.textContent = 'Ready to Process';
                    currentOperationElement.className = 'idle';
                } else {
                    currentOperationElement.textContent = 'Idle';
                    currentOperationElement.className = 'idle';
                }
            }

            this.log(`Pipeline status loaded: ${data.pipelineCount} in pipeline, ${data.stagingCount} in staging`, 'info');
            
        } catch (error) {
            this.log(`Failed to load pipeline status: ${error.message}`, 'error');
        }
    }

    async loadEnrichmentLogs() {
        try {
            const response = await fetch(`${this.apiBase}/admin/logs`, {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.redirectToLogin();
                    return;
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Ensure we have logs array
            if (!data.logs || !Array.isArray(data.logs)) {
                this.log('No logs data received from server', 'warning');
                return;
            }

            // Debug: log the structure of the first few entries
            this.log(`Received ${data.logs.length} log entries`, 'info');
            if (data.logs.length > 0) {
                this.log(`First log entry structure: ${JSON.stringify(Object.keys(data.logs[0]))}`, 'info');
            }
            
            // Filter for enrichment-related logs with robust error handling
            const enrichmentLogs = data.logs.filter(log => {
                try {
                    if (!log || typeof log !== 'object') return false;
                    
                    const operation = (log.operation || '').toString();
                    const message = (log.message || log.details || '').toString();
                    
                    return operation.includes('enrichment') || 
                           operation.includes('pipeline') ||
                           message.includes('enrichment') ||
                           message.includes('pipeline');
                } catch (filterError) {
                    console.warn('Error filtering log entry:', log, filterError);
                    return false;
                }
            }).slice(-10); // Get last 10 enrichment logs

            // Display enrichment activity
            this.log(`Found ${enrichmentLogs.length} enrichment-related logs`, 'info');
            this.displayEnrichmentActivity(enrichmentLogs);
            
        } catch (error) {
            this.log(`Failed to load enrichment logs: ${error.message}`, 'error');
        }
    }

    displayEnrichmentActivity(logs) {
        // Find or create the enrichment activity container
        let activityContainer = document.getElementById('enrichmentActivity');
        if (!activityContainer) {
            // Create the activity container if it doesn't exist
            const enrichmentPanel = document.getElementById('enrichment');
            const statusPanel = document.querySelector('#enrichment .control-panel:first-of-type');
            
            // Check if we're on the enrichment page and the elements exist
            if (!enrichmentPanel || !statusPanel || !statusPanel.parentNode) {
                console.log('Enrichment page not loaded or DOM structure not ready');
                return;
            }
            
            activityContainer = document.createElement('div');
            activityContainer.className = 'enrichment-activity';
            activityContainer.id = 'enrichmentActivity';
            activityContainer.innerHTML = `
                <h3>Recent Enrichment Activity</h3>
                <div id="enrichmentLogs" style="max-height: 300px; overflow-y: auto;">
                    <div style="text-align: center; color: #666; padding: 20px;">
                        Loading enrichment activity...
                    </div>
                </div>
            `;
            
            // Insert after the pipeline status panel
            statusPanel.parentNode.insertBefore(activityContainer, statusPanel.nextSibling);
        }

        const logsContainer = document.getElementById('enrichmentLogs');
        
        if (logs.length === 0) {
            logsContainer.innerHTML = `
                <div style="text-align: center; color: #666; padding: 20px;">
                    No recent enrichment activity
                </div>
            `;
            return;
        }

        logsContainer.innerHTML = logs.map(log => {
            try {
                const timestamp = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : 'Unknown time';
                const levelClass = log.level === 'error' ? 'error' : 
                                  log.level === 'success' ? 'success' : 'info';
                
                // Handle different message field names
                const message = (log.message || log.details || 'No message').toString();
                
                return `
                    <div class="enrichment-log-entry ${levelClass}">
                        <span style="color: #888; font-size: 10px;">[${timestamp}]</span> 
                        <span style="margin-left: 8px;">${message}</span>
                    </div>
                `;
            } catch (displayError) {
                console.warn('Error displaying log entry:', log, displayError);
                return `
                    <div class="enrichment-log-entry error">
                        <span style="color: #888; font-size: 10px;">[Error]</span> 
                        <span style="margin-left: 8px;">Failed to display log entry</span>
                    </div>
                `;
            }
        }).join('');

        // Auto-scroll to bottom to show latest activity
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }

    async startImageEnrichment() {
        try {
            this.log('Starting image enrichment for movies in staging...', 'info');
            this.showAlert('Starting image enrichment...', 'info');
            
            const response = await fetch(`${this.apiBase}/admin/enrichment/images`, {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.log('Image enrichment started successfully', 'success');
            this.showAlert('Image enrichment started for movies in staging', 'success');
            
            // Start polling for updates
            this.startEnrichmentPolling();
            
        } catch (error) {
            this.log(`Failed to start image enrichment: ${error.message}`, 'error');
            this.showAlert('Failed to start image enrichment.', 'error');
        }
    }

    async startMetadataEnrichment() {
        try {
            this.log('Starting metadata enrichment for movies in staging...', 'info');
            this.showAlert('Starting metadata enrichment...', 'info');
            
            const response = await fetch(`${this.apiBase}/admin/enrichment/metadata`, {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.log('Metadata enrichment started successfully', 'success');
            this.showAlert('Metadata enrichment started for movies in staging', 'success');
            
            // Start polling for updates
            this.startEnrichmentPolling();
            
        } catch (error) {
            this.log(`Failed to start metadata enrichment: ${error.message}`, 'error');
            this.showAlert('Failed to start metadata enrichment.', 'error');
        }
    }

    async startProfileGeneration() {
        try {
            this.log('Starting profile generation for movies in staging...', 'info');
            this.showAlert('Starting profile generation...', 'info');
            
            const response = await fetch(`${this.apiBase}/admin/enrichment/profiles`, {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.log('Profile generation started successfully', 'success');
            this.showAlert('Profile generation started for movies in staging', 'success');
            
            // Start polling for updates
            this.startEnrichmentPolling();
            
        } catch (error) {
            this.log(`Failed to start profile generation: ${error.message}`, 'error');
            this.showAlert('Failed to start profile generation.', 'error');
        }
    }

    async runFullEnrichment() {
        try {
            this.log('Starting full enrichment pipeline...', 'info');
            this.showAlert('Starting full enrichment pipeline for all movies...', 'info');
            
            // First, find movies that need enrichment
            const movies = await fetch(`${this.apiBase}/admin/movies`, {
                headers: this.getAuthHeaders()
            });
            
            if (!movies.ok) {
                throw new Error(`HTTP ${movies.status}: ${movies.statusText}`);
            }
            
            const movieData = await movies.json();
            const moviesNeedingEnrichment = movieData.movies.filter(movie => 
                !movie.profile_text || !movie.poster_url || !movie.director
            );
            
            if (moviesNeedingEnrichment.length === 0) {
                this.showAlert('All movies are already fully enriched!', 'success');
                return;
            }
            
            // Add movies to staging
            const response = await fetch(`${this.apiBase}/admin/pipeline/add`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(moviesNeedingEnrichment)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Start enrichment pipeline
            const enrichResponse = await fetch(`${this.apiBase}/admin/enrichment/start`, {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (!enrichResponse.ok) {
                throw new Error(`HTTP ${enrichResponse.status}: ${enrichResponse.statusText}`);
            }

            this.showAlert(`Full enrichment started for ${moviesNeedingEnrichment.length} movies`, 'success');
            this.log(`Full enrichment started for ${moviesNeedingEnrichment.length} movies`, 'success');
            
            // Start polling for updates
            this.startEnrichmentPolling();
            
        } catch (error) {
            this.log(`Failed to start full enrichment: ${error.message}`, 'error');
            this.showAlert('Failed to start full enrichment.', 'error');
        }
    }

    // Test function to debug enrichment
    async testEnrichment() {
        try {
            this.log('Testing enrichment with sample movie...', 'info');
            
            const testMovie = {
                title: "Test Movie " + Date.now(),
                director: "Test Director",
                year: "2023",
                plot_summary: "A test movie for debugging"
            };

            // Add to staging
            const response = await fetch(`${this.apiBase}/admin/pipeline/add`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify([testMovie])
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.log('Test movie added to staging', 'success');

            // Start enrichment
            const enrichResponse = await fetch(`${this.apiBase}/admin/enrichment/start`, {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (!enrichResponse.ok) {
                throw new Error(`HTTP ${enrichResponse.status}: ${enrichResponse.statusText}`);
            }

            this.log('Enrichment started for test movie', 'success');
            
            // Refresh logs after a delay
            setTimeout(() => {
                this.loadEnrichmentLogs();
            }, 2000);
            
        } catch (error) {
            this.log(`Test enrichment failed: ${error.message}`, 'error');
        }
    }

    // Merge & Publish Panel
    async loadMergePage() {
        try {
            await this.loadStagingStats();
        } catch (error) {
            this.log(`Failed to load merge page: ${error.message}`, 'error');
        }
    }

    async loadStagingStats() {
        try {
            const response = await fetch(`${this.apiBase}/admin/pipeline`, {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.redirectToLogin();
                    return;
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Update staging stats display
            document.getElementById('stagingCount').textContent = data.stagingCount || 0;
            document.getElementById('conflictCount').textContent = '0'; // Placeholder for conflict detection

            this.log(`Staging stats loaded: ${data.stagingCount} movies ready for merge`, 'info');
            
        } catch (error) {
            this.log(`Failed to load staging stats: ${error.message}`, 'error');
        }
    }

    async reviewStaging() {
        this.showAlert('Staging review not yet implemented.', 'warning');
    }

    async checkConflicts() {
        this.showAlert('Conflict checking not yet implemented.', 'warning');
    }

    async mergeToMain() {
        this.showAlert('Merge to main database not yet implemented.', 'warning');
    }

    async createBackup() {
        this.showAlert('Backup creation not yet implemented.', 'warning');
    }

    displayScrapingResults(movies) {
        const resultsDiv = document.getElementById('scrapingResults');
        const tbody = document.getElementById('scrapingResultsBody');
        
        if (!resultsDiv || !tbody) return;

        // Store the scraped movies data for later use
        this.scrapedMovies = movies;

        resultsDiv.classList.remove('hidden');
        
        if (movies.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 40px; color: #666;">
                        No movies found
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = movies.map((movie, index) => `
            <tr>
                <td>
                    <input type="checkbox" class="scraped-movie-checkbox" data-title="${movie.title}" data-index="${index}">
                </td>
                <td><strong>${movie.title}</strong></td>
                <td>${movie.year || 'Unknown'}</td>
                <td>${movie.director || 'Unknown'}</td>
                <td>${movie.tmdb_id || 'N/A'}</td>
                <td><span class="status-badge status-partial">Scraped</span></td>
                <td>
                    <button class="btn btn-secondary" onclick="adminPanel.previewMovie('${movie.title}', '${movie.tmdb_id || ''}')">
                        Preview
                    </button>
                </td>
            </tr>
        `).join('');

        // Add event listeners to the new checkboxes
        tbody.querySelectorAll('.scraped-movie-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateSelectAllScrapedCheckbox();
            });
        });
    }

    async previewMovie(title, tmdbId = '') {
        try {
            this.log(`Previewing movie: ${title}`, 'info');
            
            // Show loading state
            this.showAlert(`Loading preview for ${title}...`, 'info');
            
            // Get detailed movie information
            const response = await fetch(`${this.apiBase}/admin/movies/preview`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({ 
                    title: title,
                    tmdb_id: tmdbId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const movieData = await response.json();
            this.displayMoviePreview(movieData);
            
        } catch (error) {
            this.log(`Failed to preview movie: ${error.message}`, 'error');
            this.showAlert('Failed to load movie preview.', 'error');
        }
    }

    displayMoviePreview(movie) {
        // Create or update preview modal
        let previewModal = document.getElementById('moviePreviewModal');
        if (!previewModal) {
            previewModal = document.createElement('div');
            previewModal.id = 'moviePreviewModal';
            previewModal.className = 'preview-modal';
            previewModal.innerHTML = `
                <div class="preview-modal-content">
                    <div class="preview-modal-header">
                        <h2 id="previewTitle">Movie Preview</h2>
                        <button class="preview-close" onclick="adminPanel.closePreview()">&times;</button>
                    </div>
                    <div class="preview-modal-body" id="previewBody">
                        Loading...
                    </div>
                </div>
            `;
            document.body.appendChild(previewModal);
        }

        // Update modal content
        document.getElementById('previewTitle').textContent = movie.title || 'Unknown Title';
        
        const previewBody = document.getElementById('previewBody');
        previewBody.innerHTML = `
            <div class="preview-grid">
                <div class="preview-poster">
                    ${movie.poster_url ? 
                        `<img src="${movie.poster_url}" alt="${movie.title}" style="max-width: 300px; max-height: 450px; border-radius: 8px;">` :
                        `<div class="no-poster">No poster available</div>`
                    }
                </div>
                <div class="preview-details">
                    <div class="preview-field">
                        <strong>Title:</strong> ${movie.title || 'Unknown'}
                    </div>
                    <div class="preview-field">
                        <strong>Director:</strong> ${movie.director || 'Unknown'}
                    </div>
                    <div class="preview-field">
                        <strong>Year:</strong> ${movie.year || 'Unknown'}
                    </div>
                    <div class="preview-field">
                        <strong>Genre:</strong> ${movie.genre_tags ? movie.genre_tags.join(', ') : 'Unknown'}
                    </div>
                    <div class="preview-field">
                        <strong>Runtime:</strong> ${movie.runtime ? `${movie.runtime} minutes` : 'Unknown'}
                    </div>
                    <div class="preview-field">
                        <strong>Rating:</strong> ${movie.vote_average ? `${movie.vote_average}/10` : 'Unknown'}
                    </div>
                    <div class="preview-field">
                        <strong>TMDB ID:</strong> ${movie.tmdb_id || 'N/A'}
                    </div>
                    <div class="preview-field">
                        <strong>Plot Summary:</strong>
                        <p>${movie.plot_summary || movie.overview || 'No plot summary available'}</p>
                    </div>
                    ${movie.profile_text ? `
                        <div class="preview-field">
                            <strong>Profile:</strong>
                            <p>${movie.profile_text}</p>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;

        // Show modal
        previewModal.style.display = 'block';
    }

    closePreview() {
        const previewModal = document.getElementById('moviePreviewModal');
        if (previewModal) {
            previewModal.style.display = 'none';
        }
    }

    // Scraped movies selection and pipeline management
    async addSelectedToPipeline() {
        try {
            // Get all checked scraped movie checkboxes
            const checkedBoxes = document.querySelectorAll('.scraped-movie-checkbox:checked');
            
            if (checkedBoxes.length === 0) {
                this.showAlert('Please select movies to add to the pipeline.', 'warning');
                return;
            }

            // Check if we have scraped movies data
            if (!this.scrapedMovies || this.scrapedMovies.length === 0) {
                this.showAlert('No scraping results found.', 'error');
                return;
            }

            // Get selected movies using the stored data
            const selectedMovies = [];
            checkedBoxes.forEach(checkbox => {
                const index = parseInt(checkbox.dataset.index);
                if (index >= 0 && index < this.scrapedMovies.length) {
                    const movie = this.scrapedMovies[index];
                    // Create a clean movie object for the pipeline
                    const pipelineMovie = {
                        title: movie.title || '',
                        year: movie.year || '',
                        director: movie.director || '',
                        tmdb_id: movie.tmdb_id || '',
                        overview: movie.overview || '',
                        poster_path: movie.poster_path || '',
                        backdrop_path: movie.backdrop_path || '',
                        genre_ids: movie.genre_ids || [],
                        vote_average: movie.vote_average || 0,
                        vote_count: movie.vote_count || 0,
                        status: 'scraped'
                    };
                    selectedMovies.push(pipelineMovie);
                }
            });

            if (selectedMovies.length === 0) {
                this.showAlert('No valid movies selected.', 'warning');
                return;
            }

            this.log(`Adding ${selectedMovies.length} movies to pipeline...`, 'info');
            this.showAlert(`Adding ${selectedMovies.length} movies to pipeline...`, 'info');

            // Add movies to staging area via API
            const response = await fetch(`${this.apiBase}/admin/pipeline/add`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(selectedMovies)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            this.log(`Successfully added ${selectedMovies.length} movies to pipeline`, 'success');
            this.showAlert(`Successfully added ${selectedMovies.length} movies to pipeline`, 'success');
            
            // Clear the selection
            checkedBoxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            
            // Update select all checkbox
            this.updateSelectAllScrapedCheckbox();
            
            // Automatically start enrichment process
            this.log(`Starting enrichment for ${selectedMovies.length} movies...`, 'info');
            this.showAlert(`Starting enrichment for ${selectedMovies.length} movies...`, 'info');
            
            try {
                const enrichResponse = await fetch(`${this.apiBase}/admin/enrichment/start`, {
                    method: 'POST',
                    headers: this.getAuthHeaders()
                });

                if (!enrichResponse.ok) {
                    throw new Error(`HTTP ${enrichResponse.status}: ${enrichResponse.statusText}`);
                }

                this.log(`Enrichment started successfully`, 'success');
                this.showAlert(`Enrichment started for ${selectedMovies.length} movies`, 'success');
                
                // Start polling for updates
                this.startEnrichmentPolling();
                
            } catch (enrichError) {
                this.log(`Failed to start enrichment: ${enrichError.message}`, 'error');
                this.showAlert('Movies added to staging, but failed to start enrichment. Please start manually from the Enrichment page.', 'warning');
            }
            
            // Refresh pipeline status if on enrichment page
            if (this.currentPage === 'enrichment') {
                this.loadPipelineStatus();
            }
            
        } catch (error) {
            this.log(`Failed to add movies to pipeline: ${error.message}`, 'error');
            this.showAlert('Failed to add movies to pipeline.', 'error');
        }
    }

    updateSelectAllScrapedCheckbox() {
        const selectAllCheckbox = document.getElementById('selectAllScraped');
        const scrapedCheckboxes = document.querySelectorAll('.scraped-movie-checkbox');
        
        if (!selectAllCheckbox || scrapedCheckboxes.length === 0) return;
        
        const checkedCount = document.querySelectorAll('.scraped-movie-checkbox:checked').length;
        
        selectAllCheckbox.checked = checkedCount === scrapedCheckboxes.length && scrapedCheckboxes.length > 0;
        selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < scrapedCheckboxes.length;
    }

    toggleSelectAllScraped(checked) {
        const scrapedCheckboxes = document.querySelectorAll('.scraped-movie-checkbox');
        scrapedCheckboxes.forEach(checkbox => {
            checkbox.checked = checked;
        });
    }

    clearScrapingResults() {
        const resultsDiv = document.getElementById('scrapingResults');
        const tbody = document.getElementById('scrapingResultsBody');
        
        if (resultsDiv) {
            resultsDiv.classList.add('hidden');
        }
        
        if (tbody) {
            tbody.innerHTML = '';
        }
        
        this.log('Cleared scraping results', 'info');
    }

    async reloadApiData() {
        try {
            this.log('Reloading API data...', 'info');
            this.showAlert('Reloading API data...', 'info');
            
            const response = await fetch(`${this.apiBase}/admin/sync/reload-api`, {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.log('API data reloaded successfully', 'success');
                this.showAlert('API data reloaded successfully', 'success');
            } else {
                throw new Error(result.message || 'API reload failed');
            }
            
        } catch (error) {
            this.log(`Failed to reload API data: ${error.message}`, 'error');
            this.showAlert('Failed to reload API data.', 'error');
        }
    }

    async restartStaticServer() {
        try {
            this.log('Restarting static server...', 'info');
            this.showAlert('Restarting static server...', 'info');
            
            const response = await fetch(`${this.apiBase}/admin/sync/restart-server`, {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.log('Static server restarted successfully', 'success');
                this.showAlert('Static server restarted successfully', 'success');
            } else {
                throw new Error(result.message || 'Server restart failed');
            }
            
        } catch (error) {
            this.log(`Failed to restart static server: ${error.message}`, 'error');
            this.showAlert('Failed to restart static server.', 'error');
        }
    }

    async fullSyncData() {
        try {
            this.log('Starting full synchronization...', 'info');
            this.showAlert('Starting full synchronization...', 'info');
            
            const response = await fetch(`${this.apiBase}/admin/sync/full`, {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.log('Full synchronization completed successfully', 'success');
                this.showAlert('Full synchronization completed successfully', 'success');
                
                // Refresh dashboard to show updated data
                this.loadDashboard();
            } else {
                throw new Error(result.message || 'Full synchronization failed');
            }
            
        } catch (error) {
            this.log(`Full synchronization failed: ${error.message}`, 'error');
            this.showAlert('Full synchronization failed.', 'error');
        }
    }

    async addDirectorComplete() {
        try {
            const directorName = document.getElementById('directorNameComplete').value.trim();
            if (!directorName) {
                this.showAlert('Please enter a director name', 'error');
                return;
            }

            this.log(`Starting complete director addition for: ${directorName}`, 'info');
            this.showAlert(`Adding director ${directorName} with auto-sync...`, 'info');
            
            const response = await fetch(`${this.apiBase}/admin/director/add-complete`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({
                    director_name: directorName
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            this.log(`Successfully initiated director addition: ${result.movies_scraped} movies scraped`, 'success');
            this.showAlert(`Director addition started! ${result.movies_scraped} movies scraped and enrichment in progress.`, 'success');
            
            // Clear the input field
            document.getElementById('directorNameComplete').value = '';
            
            // Refresh dashboard to show updated data
            this.loadDashboard();
            
        } catch (error) {
            this.log(`Failed to add director: ${error.message}`, 'error');
            this.showAlert('Failed to add director.', 'error');
        }
    }

    // Utility Functions
    log(message, level = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = { timestamp, message, level };
        this.logs.unshift(logEntry);
        
        // Keep only last 1000 logs
        if (this.logs.length > 1000) {
            this.logs = this.logs.slice(0, 1000);
        }

        // Update log display if on logs page
        if (document.getElementById('logs').classList.contains('active')) {
            this.updateLogDisplay();
        }
    }

    updateLogDisplay() {
        const container = document.getElementById('logContainer');
        if (!container) return;

        const levelFilter = document.getElementById('logLevelFilter')?.value || '';
        const filteredLogs = levelFilter ? 
            this.logs.filter(log => log.level === levelFilter) : 
            this.logs;

        container.innerHTML = filteredLogs.slice(0, 100).map(log => 
            `<div class="log-entry log-${log.level}">[${log.timestamp}] [${log.level.toUpperCase()}] ${log.message}</div>`
        ).join('');
    }

    showAlert(message, type = 'info') {
        // Remove existing alerts
        document.querySelectorAll('.alert').forEach(alert => alert.remove());
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        
        const mainContent = document.querySelector('.main-content');
        mainContent.insertBefore(alert, mainContent.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => alert.remove(), 5000);
    }

    debounce(func, wait) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(func, wait);
    }

    // Health Check
    async runHealthCheck() {
        try {
            this.log('Running health check...', 'info');
            
            const response = await fetch(`${this.apiBase}/health`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.log('Health check passed', 'success');
            this.showAlert('System health check passed!', 'success');
            
        } catch (error) {
            this.log(`Health check failed: ${error.message}`, 'error');
            this.showAlert('Health check failed. Please check your API connection.', 'error');
        }
    }
}

// Global functions for HTML onclick handlers
function showPage(pageName) {
    adminPanel.showPage(pageName);
}

function refreshDashboard() {
    adminPanel.loadDashboard();
}

function filterMovies() {
    adminPanel.filterMovies();
}

function clearFilters() {
    adminPanel.clearFilters();
}

function selectAllVisible() {
    document.getElementById('selectAllCheckbox').checked = true;
    adminPanel.toggleSelectAll(true);
}

function deselectAll() {
    document.getElementById('selectAllCheckbox').checked = false;
    adminPanel.toggleSelectAll(false);
}

function hideSelected() {
    adminPanel.hideSelected();
}

function showSelected() {
    adminPanel.showSelected();
}

function searchDirector() {
    adminPanel.searchDirector();
}

function refreshLogs() {
    adminPanel.updateLogDisplay();
}

function clearLogs() {
    adminPanel.logs = [];
    adminPanel.updateLogDisplay();
}

function exportLogs() {
    const logs = adminPanel.logs.map(log => 
        `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.message}`
    ).join('\n');
    
    const blob = new Blob([logs], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `admin-logs-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
}

function enrichSelected() {
    adminPanel.enrichSelected();
}

function regenerateProfiles() {
    adminPanel.showAlert('Profile regeneration not yet implemented.', 'warning');
}

function startImageEnrichment() {
    adminPanel.startImageEnrichment();
}

function startMetadataEnrichment() {
    adminPanel.startMetadataEnrichment();
}

function startProfileGeneration() {
    adminPanel.startProfileGeneration();
}

function runFullEnrichment() {
    adminPanel.runFullEnrichment();
}

function reviewStaging() {
    adminPanel.reviewStaging();
}

function checkConflicts() {
    adminPanel.checkConflicts();
}

function mergeToMain() {
    adminPanel.mergeToMain();
}

function createBackup() {
    adminPanel.createBackup();
}

function closePreview() {
    adminPanel.closePreview();
}

function addSelectedToPipeline() {
    adminPanel.addSelectedToPipeline();
}

function clearScrapingResults() {
    adminPanel.clearScrapingResults();
}

function reloadApiData() {
    adminPanel.reloadApiData();
}

function restartStaticServer() {
    adminPanel.restartStaticServer();
}

function fullSyncData() {
    adminPanel.fullSyncData();
}

function addDirectorComplete() {
    adminPanel.addDirectorComplete();
}

// Initialize admin panel when page loads
let adminPanel;
// Theme Carousel Management Functions
let AVAILABLE_THEMES = [];
let themeOrder = [];
let themeSettings = {};

// Load themes from actual movie data
async function loadThemesFromData() {
    try {
        console.log('🔄 Loading themes from movie data...');
        const response = await fetch('http://localhost:8004/movie_profiles_merged.json');
        const data = await response.json();
        
        console.log('📊 Raw data type:', typeof data);
        console.log('📊 Data keys:', Object.keys(data));
        
        // Handle different data structures
        let movies = [];
        if (Array.isArray(data)) {
            movies = data;
        } else if (data.movies && Array.isArray(data.movies)) {
            movies = data.movies;
        } else if (data.data && Array.isArray(data.data)) {
            movies = data.data;
        } else if (typeof data === 'object' && !Array.isArray(data)) {
            // Handle object where keys are movie titles
            movies = Object.values(data);
            console.log('📊 Detected object structure with', movies.length, 'movies');
        } else {
            console.warn('⚠️ Unexpected data structure, using fallback themes');
            throw new Error('Unexpected data structure');
        }
        
        console.log('🎬 Movies loaded:', movies.length);
        
        // Extract all unique themes from movies
        const themeMap = new Map();
        
        movies.forEach(movie => {
            // Extract themes from primary_theme and secondary_theme fields
            const themes = [];
            
            if (movie.primary_theme) {
                themes.push(movie.primary_theme);
            }
            if (movie.secondary_theme) {
                themes.push(movie.secondary_theme);
            }
            
            // Also check for themes array if it exists
            if (movie.themes && Array.isArray(movie.themes)) {
                themes.push(...movie.themes);
            }
            
            themes.forEach(theme => {
                if (theme && typeof theme === 'string') {
                    // Convert theme to readable format
                    const readableTheme = theme.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    const themeId = theme.toLowerCase().replace(/_/g, '-');
                    
                    if (themeMap.has(themeId)) {
                        themeMap.get(themeId).count++;
                    } else {
                        themeMap.set(themeId, {
                            id: themeId,
                            name: readableTheme,
                            count: 1
                        });
                    }
                }
            });
        });
        
        // Convert to array and sort by count (most movies first)
        // Only include themes with 10+ movies
        AVAILABLE_THEMES = Array.from(themeMap.values())
            .filter(theme => theme.count >= 10)
            .sort((a, b) => b.count - a.count);
        
        console.log('🎭 Loaded themes from data (10+ movies):', AVAILABLE_THEMES);
        
        // Update theme order to include all themes
        themeOrder = AVAILABLE_THEMES.map(theme => theme.id);
        
        // Set default settings (all enabled for themes with 10+ movies)
        themeSettings = {};
        AVAILABLE_THEMES.forEach(theme => {
            themeSettings[theme.id] = true;
        });
        
        return AVAILABLE_THEMES;
    } catch (error) {
        console.error('❌ Error loading themes from data:', error);
        
        // Fallback to hardcoded themes (only those with 10+ movies)
        AVAILABLE_THEMES = [
            { id: 'found-family', name: 'Found Family', count: 45 },
            { id: 'identity-crisis', name: 'Identity Crisis', count: 38 },
            { id: 'forbidden-love', name: 'Forbidden Love', count: 52 },
            { id: 'underdog-triumph', name: 'Underdog Triumph', count: 41 },
            { id: 'coming-of-age', name: 'Coming Of Age', count: 67 }
        ].filter(theme => theme.count >= 10);
        
        themeOrder = AVAILABLE_THEMES.map(theme => theme.id);
        themeSettings = {};
        AVAILABLE_THEMES.forEach(theme => {
            themeSettings[theme.id] = true;
        });
        
        return AVAILABLE_THEMES;
    }
}

async function loadThemeCarouselSettings() {
    console.log('🎛️ Loading theme carousel settings...');
    
    // First load themes from data
    await loadThemesFromData();
    
    // Then load saved settings from localStorage
    const savedSettings = JSON.parse(localStorage.getItem('themeCarouselSettings') || '{}');
    const savedOrder = JSON.parse(localStorage.getItem('themeOrder') || '[]');
    
    // Merge with loaded themes
    if (Object.keys(savedSettings).length > 0) {
        themeSettings = { ...themeSettings, ...savedSettings };
    }
    
    if (savedOrder.length > 0) {
        // Only use saved order for themes that still exist
        themeOrder = savedOrder.filter(themeId => 
            AVAILABLE_THEMES.some(theme => theme.id === themeId)
        );
        
        // Add any new themes that weren't in the saved order
        AVAILABLE_THEMES.forEach(theme => {
            if (!themeOrder.includes(theme.id)) {
                themeOrder.push(theme.id);
            }
        });
    }
    
    console.log('🎛️ Theme settings:', themeSettings);
    console.log('🎛️ Theme order:', themeOrder);
    console.log('🎛️ Available themes:', AVAILABLE_THEMES);
    
    renderThemeList();
}

function renderThemeList() {
    console.log('🎨 Rendering theme list...');
    const themeList = document.getElementById('themeList');
    if (!themeList) {
        console.error('❌ Theme list element not found!');
        return;
    }
    
    console.log('🎨 Theme order:', themeOrder);
    console.log('🎨 Available themes:', AVAILABLE_THEMES);
    
    themeList.innerHTML = '';
    
    themeOrder.forEach(themeId => {
        const theme = AVAILABLE_THEMES.find(t => t.id === themeId);
        if (!theme) {
            console.warn('⚠️ Theme not found:', themeId);
            return;
        }
        
        console.log('🎨 Rendering theme:', theme.name);
        
        const themeItem = document.createElement('div');
        themeItem.className = 'theme-item';
        themeItem.draggable = true;
        themeItem.dataset.themeId = themeId;
        
        themeItem.innerHTML = `
            <div class="theme-drag-handle">⋮⋮</div>
            <input type="checkbox" class="theme-checkbox" id="${themeId}-enabled" ${themeSettings[themeId] ? 'checked' : ''}>
            <label class="theme-label" for="${themeId}-enabled">${theme.name}</label>
            <div class="theme-movie-count">${theme.count || theme.movieCount || 0} movies</div>
            <div class="theme-actions">
                <button class="theme-remove" onclick="removeTheme('${themeId}')">Remove</button>
            </div>
        `;
        
        // Add drag event listeners
        themeItem.addEventListener('dragstart', handleDragStart);
        themeItem.addEventListener('dragover', handleDragOver);
        themeItem.addEventListener('drop', handleDrop);
        themeItem.addEventListener('dragend', handleDragEnd);
        
        themeList.appendChild(themeItem);
    });
}

function handleDragStart(e) {
    e.target.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', e.target.outerHTML);
}

function handleDragOver(e) {
    e.preventDefault();
    e.target.classList.add('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.target.classList.remove('drag-over');
    
    const draggedThemeId = e.dataTransfer.getData('text/html').match(/data-theme-id="([^"]+)"/)?.[1];
    const targetThemeId = e.target.closest('.theme-item')?.dataset.themeId;
    
    if (draggedThemeId && targetThemeId && draggedThemeId !== targetThemeId) {
        const draggedIndex = themeOrder.indexOf(draggedThemeId);
        const targetIndex = themeOrder.indexOf(targetThemeId);
        
        // Remove dragged item and insert at new position
        themeOrder.splice(draggedIndex, 1);
        themeOrder.splice(targetIndex, 0, draggedThemeId);
        
        renderThemeList();
    }
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
    document.querySelectorAll('.theme-item').forEach(item => {
        item.classList.remove('drag-over');
    });
}

function removeTheme(themeId) {
    if (confirm(`Are you sure you want to remove "${AVAILABLE_THEMES.find(t => t.id === themeId)?.name}"?`)) {
        themeOrder = themeOrder.filter(id => id !== themeId);
        delete themeSettings[themeId];
        renderThemeList();
    }
}

function saveThemeCarouselSettings() {
    // Collect current settings from checkboxes
    const settings = {};
    themeOrder.forEach(themeId => {
        const checkbox = document.getElementById(`${themeId}-enabled`);
        if (checkbox) {
            settings[themeId] = checkbox.checked;
        }
    });
    
    // Save settings and order to localStorage
    localStorage.setItem('themeCarouselSettings', JSON.stringify(settings));
    localStorage.setItem('themeOrder', JSON.stringify(themeOrder));
    
    // Update the main app's carousel configuration
    updateMainAppCarouselConfig(settings, themeOrder);
    
    adminPanel.log('Theme carousel settings saved', 'success');
    showAlert('Theme carousel settings saved successfully!', 'success');
}

function resetThemeCarouselSettings() {
    const defaultSettings = {
        'found-family': true,
        'identity-crisis': true,
        'forbidden-love': true,
        'underdog-triumph': true,
        'coming-of-age': true
    };
    
    const defaultOrder = AVAILABLE_THEMES.map(theme => theme.id);
    
    themeSettings = { ...defaultSettings };
    themeOrder = [...defaultOrder];
    
    renderThemeList();
    
    localStorage.setItem('themeCarouselSettings', JSON.stringify(defaultSettings));
    localStorage.setItem('themeOrder', JSON.stringify(defaultOrder));
    updateMainAppCarouselConfig(defaultSettings, defaultOrder);
    
    adminPanel.log('Theme carousel settings reset to default', 'info');
    showAlert('Theme carousel settings reset to default', 'info');
}

function updateMainAppCarouselConfig(settings, order) {
    // This function would communicate with the main app to update the carousel configuration
    // For now, we'll store the settings and the main app can read them
    console.log('Updated carousel configuration:', settings);
    console.log('Updated carousel order:', order);
}

function previewThemeCarousels() {
    // Open the main app in a new tab to preview the carousels
    window.open('http://localhost:8004', '_blank');
}

function loadThemeStatistics() {
    // This would load theme statistics from the API
    // For now, we'll show placeholder data
    document.getElementById('availableThemesCount').textContent = '5';
    document.getElementById('availableThemesBreakdown').textContent = '5 themes configured';
    
    const moviesPerTheme = document.getElementById('moviesPerTheme');
    moviesPerTheme.innerHTML = `
        <div style="font-size: 0.9rem; color: #6b7280;">
            <div>Found Family: ~45 movies</div>
            <div>Identity Crisis: ~38 movies</div>
            <div>Forbidden Love: ~52 movies</div>
            <div>Underdog Triumph: ~41 movies</div>
            <div>Coming Of Age: ~67 movies</div>
        </div>
    `;
}

function refreshThemeStats() {
    adminPanel.log('Refreshing theme statistics...', 'info');
    loadThemeStatistics();
    showAlert('Theme statistics refreshed', 'success');
}

function addNewTheme() {
    console.log('➕ Adding new theme...');
    const themeName = document.getElementById('newThemeName').value.trim();
    console.log('➕ Theme name:', themeName);
    
    if (!themeName) {
        showAlert('Please enter a theme name', 'error');
        return;
    }
    
    // Check if theme already exists
    const existingTheme = AVAILABLE_THEMES.find(t => t.name.toLowerCase() === themeName.toLowerCase());
    if (existingTheme) {
        showAlert('This theme already exists', 'error');
        return;
    }
    
    // Create new theme ID
    const themeId = themeName.toLowerCase().replace(/\s+/g, '-');
    console.log('➕ Theme ID:', themeId);
    
    // Add to available themes
    AVAILABLE_THEMES.push({
        id: themeId,
        name: themeName,
        count: 0 // Will be calculated later
    });
    
    // Add to theme order and settings
    themeOrder.push(themeId);
    themeSettings[themeId] = true;
    
    // Note: Custom themes start with 0 movies, so they won't show on homepage
    // until they have 10+ movies in the actual data
    
    console.log('➕ Updated AVAILABLE_THEMES:', AVAILABLE_THEMES);
    console.log('➕ Updated themeOrder:', themeOrder);
    console.log('➕ Updated themeSettings:', themeSettings);
    
    // Re-render the list
    renderThemeList();
    
    adminPanel.log(`New theme "${themeName}" added`, 'success');
    showAlert(`New theme "${themeName}" added successfully!`, 'success');
    
    // Clear the form
    document.getElementById('newThemeName').value = '';
}

function refreshThemeList() {
    renderThemeList();
    adminPanel.log('Theme list refreshed', 'info');
    showAlert('Theme list refreshed', 'info');
}

function showAlert(message, type) {
    console.log(`🚨 Alert: ${message} (${type})`);
    
    // Create and show an alert message
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        max-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    if (type === 'success') {
        alertDiv.style.backgroundColor = '#10b981';
    } else if (type === 'error') {
        alertDiv.style.backgroundColor = '#ef4444';
    } else if (type === 'info') {
        alertDiv.style.backgroundColor = '#3b82f6';
    }
    
    // Insert at the top of the body
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}

document.addEventListener('DOMContentLoaded', () => {
    adminPanel = new MovieAdminPanel();
    
    // Load theme carousel settings after admin panel is initialized
    setTimeout(() => {
        console.log('🔄 Loading theme carousel settings...');
        loadThemeCarouselSettings();
    }, 100);
});
