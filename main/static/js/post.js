document.addEventListener('DOMContentLoaded', function() {
    // Handle like button clicks
    document.querySelectorAll('.like-btn').forEach(btn => {
        btn.addEventListener('click', handleLike);
    });

    // Handle share button clicks
    document.querySelectorAll('.share-btn').forEach(btn => {
        btn.addEventListener('click', handleShare);
    });

    // Initialize Select2 for user tagging if on create/edit page
    if (document.getElementById('id_tagged_users')) {
        $('#id_tagged_users').select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: 'Tag people in your post...',
            allowClear: true
        });
    }

    // Initialize Location Autocomplete if on create/edit page
    const locationInput = document.getElementById('id_location');
    if (locationInput && typeof google !== 'undefined') {
        const autocomplete = new google.maps.places.Autocomplete(locationInput, {
            types: ['geocode', 'establishment']
        });
    }
});

// Handle like button clicks
async function handleLike(e) {
    e.preventDefault();
    const btn = e.currentTarget;
    const postId = btn.dataset.postId;
    const icon = btn.querySelector('i');
    const likesCount = btn.querySelector('.likes-count');

    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const response = await fetch('/post/like/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
            body: `post_id=${postId}`
        });

        const data = await response.json();
        if (data.status === 'success') {
            likesCount.textContent = data.likes_count;
            icon.className = `bi ${data.is_liked ? 'bi-heart-fill text-danger' : 'bi-heart'}`;
        }
    } catch (error) {
        console.error('Error liking post:', error);
    }
}

// Handle share button clicks
function handleShare(e) {
    e.preventDefault();
    if (navigator.share) {
        navigator.share({
            title: document.title,
            url: window.location.href
        }).catch(console.error);
    } else {
        // Fallback: Copy URL to clipboard
        const dummy = document.createElement('input');
        document.body.appendChild(dummy);
        dummy.value = window.location.href;
        dummy.select();
        document.execCommand('copy');
        document.body.removeChild(dummy);
        
        showToast('Link copied to clipboard!');
    }
}

// Show toast notification
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
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
