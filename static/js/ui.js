/* UI helpers: toast, modal, confirm */

function toast(title, message = '', variant = 'primary', timeout = 3500) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const el = document.createElement('div');
    el.className = `toast-item ${variant}`;
    el.innerHTML = `
        <div class="toast-title">${escapeHtml(title)}</div>
        ${message ? `<div class="toast-msg">${escapeHtml(message)}</div>` : ''}
    `;
    container.appendChild(el);
    setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateX(20px)'; }, timeout - 250);
    setTimeout(() => el.remove(), timeout);
}

function showModal({ title = 'Konfirmasi', body = '', footer = '', size = '', onShown }) {
    const container = document.getElementById('modalContainer');
    const id = 'modal-' + Date.now();
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = id;
    modal.tabIndex = -1;
    modal.innerHTML = `
        <div class="modal-dialog ${size ? 'modal-' + size : ''} modal-dialog-centered modal-dialog-scrollable">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${title}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">${body}</div>
                ${footer ? `<div class="modal-footer">${footer}</div>` : ''}
            </div>
        </div>
    `;
    container.appendChild(modal);
    const instance = new bootstrap.Modal(modal);
    modal.addEventListener('hidden.bs.modal', () => modal.remove());
    instance.show();
    if (typeof onShown === 'function') modal.addEventListener('shown.bs.modal', onShown, { once: true });
    return { el: modal, instance };
}

function confirmDialog({ title = 'Konfirmasi', message = 'Apakah Anda yakin?', confirmText = 'Ya, lanjutkan', cancelText = 'Batal', variant = 'danger' }) {
    return new Promise((resolve) => {
        const { el, instance } = showModal({
            title,
            body: `<p class="mb-0">${escapeHtml(message)}</p>`,
            footer: `
                <button type="button" class="btn btn-light" data-bs-dismiss="modal">${cancelText}</button>
                <button type="button" class="btn btn-${variant}" id="confirmBtn">${confirmText}</button>
            `,
        });
        el.querySelector('#confirmBtn').addEventListener('click', () => { instance.hide(); resolve(true); });
        el.addEventListener('hidden.bs.modal', () => resolve(false), { once: true });
    });
}

function initSelect2(selector, opts = {}) {
    if (window.jQuery && jQuery.fn.select2) {
        jQuery(selector).each(function() {
            if (jQuery(this).data('select2')) return;
            jQuery(this).select2(Object.assign({
                width: '100%',
                placeholder: '-- Pilih --',
                allowClear: true,
            }, opts));
        });
    }
}

function destroySelect2(selector) {
    if (window.jQuery && jQuery.fn.select2) {
        jQuery(selector).each(function() {
            if (jQuery(this).data('select2')) jQuery(this).select2('destroy');
        });
    }
}
