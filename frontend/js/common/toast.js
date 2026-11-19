// Thông báo theo tên hành động: tiêu đề cụ thể, xanh thành công, đỏ thất bại.
// Gọi showToast(message, 'success' | 'error', title).
(() => {
  let timer;
  function showToast(message, type = 'success', title = '') {
    const el = document.getElementById('appToast');
    if (!el || !message) return;
    clearTimeout(timer);
    const isError = type === 'error';
    el.className = 'app-toast ' + (isError ? 'toast-error' : 'toast-success');
    el.querySelector('.toast-symbol').textContent = isError ? '!' : '✓';
    el.querySelector('.toast-heading').textContent = title || (isError ? 'Yêu cầu không thành công' : 'Yêu cầu đã được thực hiện');
    el.querySelector('.toast-message').textContent = String(message);
    el.hidden = false;
    el.querySelector('.toast-close').onclick = hideToast;
    timer = setTimeout(hideToast, 4500);
  }
  function hideToast() {
    clearTimeout(timer);
    const el = document.getElementById('appToast');
    if (el) el.hidden = true;
  }
  window.showToast = showToast;
  window.hideToast = hideToast;
})();
