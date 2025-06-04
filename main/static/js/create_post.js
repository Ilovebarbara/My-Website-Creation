document.addEventListener('DOMContentLoaded', function() {
    // Initialize Select2 for user tagging
    $('#id_tagged_users').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Tag people in your post...',
        allowClear: true
    });

    // Media preview functionality
    const mediaPreview = document.getElementById('media-preview');
    const mediaFormset = document.getElementById('media-formset');
    const addMediaBtn = document.getElementById('add-media');
    const totalForms = document.querySelector('#id_media-TOTAL_FORMS');

    function updateMediaPreview(input) {
        const files = input.files;
        const previewDiv = document.createElement('div');
        previewDiv.className = 'col-4 position-relative';

        if (files && files[0]) {
            const file = files[0];
            const reader = new FileReader();

            reader.onload = function(e) {
                if (file.type.startsWith('image/')) {
                    previewDiv.innerHTML = `
                        <img src="${e.target.result}" class="img-fluid rounded" alt="Preview">
                        <button type="button" class="btn btn-danger btn-sm position-absolute top-0 end-0 m-1 remove-media">
                            <i class="bi bi-x"></i>
                        </button>
                    `;
                } else if (file.type.startsWith('video/')) {
                    previewDiv.innerHTML = `
                        <video class="img-fluid rounded" controls>
                            <source src="${e.target.result}" type="${file.type}">
                        </video>
                        <button type="button" class="btn btn-danger btn-sm position-absolute top-0 end-0 m-1 remove-media">
                            <i class="bi bi-x"></i>
                        </button>
                    `;
                }
                mediaPreview.appendChild(previewDiv);
            };

            reader.readAsDataURL(file);
        }
    }

    // Handle file input changes
    mediaFormset.addEventListener('change', function(e) {
        if (e.target.type === 'file') {
            updateMediaPreview(e.target);
        }
    });

    // Remove media preview and clear file input
    mediaPreview.addEventListener('click', function(e) {
        if (e.target.closest('.remove-media')) {
            const previewDiv = e.target.closest('.col-4');
            const index = Array.from(mediaPreview.children).indexOf(previewDiv);
            const fileInput = mediaFormset.querySelectorAll('input[type="file"]')[index];
            fileInput.value = '';
            previewDiv.remove();
        }
    });

    // Add new media form
    let formCount = mediaFormset.children.length;
    addMediaBtn.addEventListener('click', function() {
        const newForm = mediaFormset.children[0].cloneNode(true);
        const formRegex = RegExp(`media-(\\d){1}-`,'g');
        
        newForm.innerHTML = newForm.innerHTML.replace(formRegex, `media-${formCount}-`);
        newForm.querySelectorAll('input').forEach(input => input.value = '');
        mediaFormset.appendChild(newForm);
        
        formCount++;
        totalForms.value = formCount;
    });

    // Location autocomplete
    const locationInput = document.getElementById('id_location');
    if (locationInput) {
        const autocomplete = new google.maps.places.Autocomplete(locationInput, {
            types: ['geocode', 'establishment']
        });
    }

    // Form validation
    const form = document.querySelector('form');
    form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        form.classList.add('was-validated');
    });

    // Auto-expanding textarea
    const textarea = document.querySelector('textarea');
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
});
