// NovelForge - App JS

// Auto-close flash messages
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.alert').forEach(function(el) {
        setTimeout(function() { el.style.opacity = '0'; setTimeout(function() { el.remove(); }, 300); }, 4000);
    });
});

// Confirm dialogs
function confirmDelete(msg) {
    return confirm(msg || '确定要删除吗？此操作不可撤销。');
}

// Tab switching
function switchTab(tabs, tabId) {
    tabs.forEach(function(t) { t.classList.remove('active'); });
    document.querySelectorAll('.tab-content').forEach(function(c) { c.style.display = 'none'; });
    var activeTab = document.querySelector('.tab[data-tab="' + tabId + '"]');
    if (activeTab) activeTab.classList.add('active');
    var activeContent = document.getElementById('tab-' + tabId);
    if (activeContent) activeContent.style.display = 'block';
}

// Poll job status
function pollJobStatus(jobId, checkInterval, callback) {
    var interval = setInterval(function() {
        fetch('/jobs/' + jobId + '/status')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.status === 'success' || data.status === 'failed' || data.status === 'cancelled') {
                    clearInterval(interval);
                    if (callback) callback(data);
                }
            })
            .catch(function() { clearInterval(interval); });
    }, checkInterval || 2000);
}
