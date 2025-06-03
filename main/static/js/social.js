// Function to get CSRF token
function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue;
}

// Handle likes
document.querySelectorAll('.like-btn').forEach(button => {
    button.addEventListener('click', function() {
        const postId = this.dataset.postId;
        const icon = this.querySelector('i');
        const countSpan = this.querySelector('.likes-count');

        fetch('/post/like/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCSRFToken(),
            },
            body: `post_id=${postId}`
        })
        .then(response => response.json())
        .then(data => {
            icon.className = data.is_liked ? 'bi bi-heart-fill text-danger' : 'bi bi-heart';
            countSpan.textContent = data.likes_count;
        });
    });
});

// Handle follows
document.querySelectorAll('.follow-btn').forEach(button => {
    button.addEventListener('click', function() {
        const userId = this.dataset.userId;
        const action = this.dataset.action;

        fetch('/follow/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCSRFToken(),
            },
            body: `user_id=${userId}`
        })
        .then(response => response.json())
        .then(data => {
            this.textContent = data.is_following ? 'Unfollow' : 'Follow';
            this.dataset.action = data.is_following ? 'unfollow' : 'follow';
        });
    });
});

// Handle shares
document.querySelectorAll('.share-btn').forEach(button => {
    button.addEventListener('click', function() {
        const postId = this.dataset.postId;

        fetch('/post/share/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCSRFToken(),
            },
            body: `post_id=${postId}`
        })
        .then(response => response.json())
        .then(data => {
            this.querySelector('span').textContent = data.shares_count;
        });
    });
});

// Handle comment submissions
document.querySelectorAll('.comment-form').forEach(form => {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const postId = this.dataset.postId;
        const input = this.querySelector('input[name="content"]');
        const commentsList = document.querySelector(`#comments-${postId} .comments-list`);

        fetch(`/post/${postId}/comment/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCSRFToken(),
            },
            body: `content=${encodeURIComponent(input.value)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const commentHtml = `
                    <div class="mb-2">
                        <div class="d-flex align-items-center">
                            <div class="user-avatar me-2" style="width: 30px; height: 30px; font-size: 0.8rem;">
                                ${data.author[0].toUpperCase()}
                            </div>
                            <div>
                                <strong>${data.author}</strong>
                                <small class="text-muted">just now</small>
                            </div>
                        </div>
                        <p class="mb-1 ms-5">${data.content}</p>
                    </div>
                `;
                commentsList.insertAdjacentHTML('beforeend', commentHtml);
                input.value = '';
            }
        });
    });
});
