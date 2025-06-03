// Post management functionality
class PostManager {
    constructor() {
        this.setupEventListeners();
        this.initializePopovers();
        this.deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
        this.postToDelete = null;
    }

    initializePopovers() {
        // Initialize popovers for posts
        document.querySelectorAll('[data-bs-toggle="popover"]').forEach(popoverTrigger => {
            new bootstrap.Popover(popoverTrigger, {
                trigger: 'click',
                container: 'body'
            });
        });

        // Close popovers when clicking outside
        document.addEventListener('click', (event) => {
            if (!event.target.closest('[data-bs-toggle="popover"]') && 
                !event.target.closest('.popover')) {
                document.querySelectorAll('[data-bs-toggle="popover"]').forEach(trigger => {
                    const popover = bootstrap.Popover.getInstance(trigger);
                    if (popover) {
                        popover.hide();
                    }
                });
            }
        });
    }

    setupEventListeners() {
        // Handle post actions through event delegation
        document.addEventListener('click', (event) => {
            const actionButton = event.target.closest('.toggle-featured, .delete-post');
            if (!actionButton) return;

            const popoverTrigger = actionButton.closest('.list-group').closest('.popover').previousElementSibling;
            const postId = actionButton.dataset.postId;

            if (actionButton.classList.contains('toggle-featured')) {
                this.handleFeaturedToggle(actionButton);
            } else if (actionButton.classList.contains('delete-post')) {
                this.handleDeleteClick(actionButton);
            }

            // Hide popover after action
            const popover = bootstrap.Popover.getInstance(popoverTrigger);
            if (popover) {
                popover.hide();
            }
        });

        document.getElementById('confirmDelete')?.addEventListener('click', 
            () => this.handleDeleteConfirm());
    }

    handleDeleteClick(button) {
        this.postToDelete = button.dataset.postId;
        this.deleteModal.show();
    }

    async handleDeleteConfirm() {
        if (!this.postToDelete) return;

        try {
            const response = await fetch(`/post/delete/${this.postToDelete}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                }
            });
            const data = await response.json();

            if (data.status === 'success') {
                const postElement = document.getElementById(`post-${this.postToDelete}`);
                postElement?.remove();
                this.deleteModal.hide();
                this.showToast('Post deleted successfully', 'success');
            }
        } catch (error) {
            this.showToast('Failed to delete post', 'error');
        }
    }

    async handleFeaturedToggle(button) {
        const postId = button.dataset.postId;
        try {
            const response = await fetch(`/post/toggle-featured/${postId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                }
            });
            const data = await response.json();

            if (data.status === 'success') {
                const icon = button.querySelector('i');
                if (data.featured) {
                    icon.className = 'bi bi-star me-2';
                    button.querySelector('span').textContent = 'Remove from Featured';
                } else {
                    icon.className = 'bi bi-star-fill me-2';
                    button.querySelector('span').textContent = 'Add to Featured';
                }
                this.showToast(
                    `Post ${data.featured ? 'added to' : 'removed from'} featured`,
                    'success'
                );
            }
        } catch (error) {
            this.showToast('Failed to update featured status', 'error');
        }
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : 'success'} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}

class ProjectManager {
    constructor() {
        this.setupEventListeners();
        this.initializePopovers();
    }

    initializePopovers() {
        document.querySelectorAll('[data-bs-toggle="popover"]').forEach(popoverTrigger => {
            new bootstrap.Popover(popoverTrigger, {
                trigger: 'click',
                container: 'body'
            });
        });

        // Close popovers when clicking outside
        document.addEventListener('click', (event) => {
            if (!event.target.closest('[data-bs-toggle="popover"]') && 
                !event.target.closest('.popover')) {
                document.querySelectorAll('[data-bs-toggle="popover"]').forEach(trigger => {
                    const popover = bootstrap.Popover.getInstance(trigger);
                    if (popover) {
                        popover.hide();
                    }
                });
            }
        });
    }    setupEventListeners() {
        // Handle project actions through event delegation
        document.addEventListener('click', (event) => {
            const actionButton = event.target.closest('.toggle-featured, .delete-project');
            if (!actionButton) return;

            const popoverTrigger = actionButton.closest('.card-body').querySelector('[data-bs-toggle="popover"]');
            const projectId = actionButton.dataset.projectId;

            if (actionButton.classList.contains('toggle-featured')) {
                this.handleFeaturedToggle(projectId);
            } else if (actionButton.classList.contains('delete-project')) {
                this.deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
                this.projectToDelete = projectId;
                this.deleteModal.show();
            }

            // Hide popover after action
            const popover = bootstrap.Popover.getInstance(popoverTrigger);
            if (popover) {
                popover.hide();
            }
        });

        // Handle delete confirmation
        document.getElementById('confirmDelete')?.addEventListener('click', () => {
            if (this.projectToDelete) {
                this.handleDelete(this.projectToDelete);
                this.deleteModal.hide();
            }
        });
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    showToast(message, type = 'success') {
        const toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toast);
        document.body.appendChild(toastContainer);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => {
            toastContainer.remove();
        });
    }

    async handleDelete(projectId) {
        if (!confirm('Are you sure you want to delete this project?')) return;

        try {
            const response = await fetch(`/project/delete/${projectId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                }
            });
            const data = await response.json();

            if (data.status === 'success') {
                document.getElementById(`project-${projectId}`)?.remove();
                this.showToast('Project deleted successfully', 'success');
            }
        } catch (error) {
            this.showToast('Failed to delete project', 'error');
            console.error('Error deleting project:', error);
        }
    }
}

class TutorialManager {
    constructor() {
        this.setupEventListeners();
        this.initializePopovers();
        this.deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
        this.tutorialToDelete = null;
    }

    initializePopovers() {
        // Initialize popovers for tutorials
        document.querySelectorAll('[data-bs-toggle="popover"]').forEach(popoverTrigger => {
            new bootstrap.Popover(popoverTrigger, {
                trigger: 'click',
                container: 'body'
            });
        });
    }

    setupEventListeners() {
        // Handle tutorial actions through event delegation
        document.addEventListener('click', (event) => {
            const actionButton = event.target.closest('.delete-tutorial');
            if (!actionButton) return;

            const popoverTrigger = actionButton.closest('.list-group').closest('.popover').previousElementSibling;
            const tutorialId = actionButton.dataset.tutorialId;

            if (actionButton.classList.contains('delete-tutorial')) {
                this.handleDeleteClick(actionButton);
            }

            // Hide popover after action
            const popover = bootstrap.Popover.getInstance(popoverTrigger);
            if (popover) {
                popover.hide();
            }
        });

        document.getElementById('confirmDelete')?.addEventListener('click', 
            () => this.handleDeleteConfirm());
    }

    handleDeleteClick(button) {
        this.tutorialToDelete = button.dataset.tutorialId;
        this.deleteModal.show();
    }

    async handleDeleteConfirm() {
        if (!this.tutorialToDelete) return;

        try {
            const response = await fetch(`/tutorial/delete/${this.tutorialToDelete}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                }
            });
            const data = await response.json();

            if (data.status === 'success') {
                const element = document.getElementById(`tutorial-${this.tutorialToDelete}`);
                if (element) {
                    element.remove();
                    this.showToast('Tutorial deleted successfully');
                } else {
                    this.showToast('Tutorial deleted but UI not updated', 'warning');
                }
                this.deleteModal.hide();
            } else {
                this.showToast(data.message || 'Failed to delete tutorial', 'danger');
            }
        } catch (error) {
            console.error('Error deleting tutorial:', error);
            this.showToast('Failed to delete tutorial', 'danger');
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    showToast(message, type = 'success') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            console.error('Toast container not found');
            return;
        }

        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
}

// Initialize managers
document.addEventListener('DOMContentLoaded', () => {
    new PostManager();
    new ProjectManager();
    new TutorialManager();
});
