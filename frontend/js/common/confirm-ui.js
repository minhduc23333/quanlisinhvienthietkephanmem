// Hộp xác nhận trong giao diện, thay cho window.confirm của trình duyệt.
function confirmInPage(message, title = 'Xác nhận thao tác', dangerous = false, confirmLabel = '') {
  const dialog = document.getElementById('confirmDialog');
  const agree = document.getElementById('acceptConfirm');
  const cancel = document.getElementById('cancelConfirm');
  document.getElementById('confirmTitle').textContent = title;
  document.getElementById('confirmMessage').textContent = message;
  agree.textContent = confirmLabel || (dangerous ? 'Xóa tài khoản' : 'Xác nhận');
  agree.classList.toggle('confirm-danger', dangerous);
  return new Promise(resolve => {
    let finished = false;
    const finish = result => {
      if (finished) return;
      finished = true;
      agree.removeEventListener('click', onAgree);
      cancel.removeEventListener('click', onCancel);
      dialog.removeEventListener('cancel', onEscape);
      dialog.removeEventListener('close', onClose);
      if (dialog.open) dialog.close();
      resolve(result);
    };
    const onAgree = () => finish(true);
    const onCancel = () => finish(false);
    const onEscape = event => { event.preventDefault(); finish(false); };
    const onClose = () => finish(false);
    agree.addEventListener('click', onAgree);
    cancel.addEventListener('click', onCancel);
    dialog.addEventListener('cancel', onEscape);
    dialog.addEventListener('close', onClose);
    dialog.showModal();
    cancel.focus();
  });
}
