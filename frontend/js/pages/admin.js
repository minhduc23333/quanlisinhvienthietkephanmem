const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, ch => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[ch]));
const DAYS = {2: 'Thứ 2', 3: 'Thứ 3', 4: 'Thứ 4', 5: 'Thứ 5', 6: 'Thứ 6', 7: 'Thứ 7'};
const SHIFTS = {sang: 'Sáng', chieu: 'Chiều'};
let users = [], courses = [], view = 'users';
let editingCourseId = null, scheduleCourse = null, editingSlotId = null, completedUser = null;

function errorText(d, status) {
  if (typeof d.detail === 'string') return d.detail;
  if (Array.isArray(d.detail)) return d.detail.map(x => String(x.msg || '').replace(/^Value error, /, '')).join('; ');
  return `Lỗi ${status}`;
}
async function api(url, options) {
  const r = await fetch(url, options);
  const d = await r.json().catch(() => ({}));
  if (!r.ok) {
    if (r.status === 401) location.replace('/');
    throw Error(errorText(d, r.status));
  }
  return d;
}
const send = (url, method, body) => api(url, {method, headers: {'Content-Type': 'application/json'}, body: body === undefined ? undefined : JSON.stringify(body)});
function notify(msg, bad = false, title = '') { if (msg) showToast(msg, bad ? 'error' : 'success', title); }
const fmtDate = iso => { if (!iso) return ''; const d = new Date(iso); return isNaN(d) ? '' : d.toLocaleDateString('vi-VN'); };

async function refresh() {
  try {
    const [people, subjects] = await Promise.all([api('/admin/users'), api('/courses')]);
    users = people; courses = subjects;
    renderUsers(); renderCourses();
  } catch (e) { notify(e.message, true, 'Không tải được dữ liệu'); }
}

/* ------------------------------------------------------------- tài khoản sinh viên */
function renderUsers() {
  const q = $('searchUsers').value.toLowerCase().trim();
  const found = users.filter(u => `${u.name} ${u.username}`.toLowerCase().includes(q));
  $('userRows').innerHTML = found.map(u => `<tr><td class="code">#${u.id}</td><td><strong>${esc(u.name)}</strong></td><td>${esc(u.username)}</td><td>${u.enrollment_count}</td><td><span class="pill ${u.is_locked ? 'closed' : 'open'}">${u.is_locked ? 'Đã khóa' : 'Hoạt động'}</span></td><td><div class="admin-actions"><button class="secondary-button" data-id="${u.id}" data-action="completed">Đã học</button><button class="secondary-button" data-id="${u.id}" data-action="${u.is_locked ? 'unlock' : 'lock'}">${u.is_locked ? 'Mở khóa' : 'Khóa'}</button><button class="danger-button" data-id="${u.id}" data-action="delete">Xóa</button></div></td></tr>`).join('')
    || '<tr><td colspan="6" class="empty">Không tìm thấy sinh viên.</td></tr>';
}

$('userRows').onclick = async e => {
  const b = e.target.closest('[data-action]');
  if (!b) return;
  const id = Number(b.dataset.id), action = b.dataset.action, u = users.find(x => x.id === id);
  if (!u) return;
  if (action === 'completed') return openCompleted(u);
  const label = action === 'delete' ? 'XÓA VĨNH VIỄN' : action === 'lock' ? 'KHÓA' : 'MỞ KHÓA';
  if (!await confirmInPage(`${label} tài khoản ${u.username} (${u.name})?${action === 'delete' ? ' Các học phần đã đăng ký cũng sẽ bị xóa.' : ''}`,
      action === 'delete' ? 'Xóa tài khoản sinh viên' : action === 'lock' ? 'Khóa tài khoản sinh viên' : 'Mở khóa tài khoản sinh viên', action === 'delete')) return;
  try {
    const d = await send(`/admin/users/${id}` + (action === 'delete' ? '' : `/${action}`), action === 'delete' ? 'DELETE' : 'PATCH');
    await refresh();
    notify(d.message, false, action === 'delete' ? 'Xóa tài khoản thành công' : action === 'lock' ? 'Khóa tài khoản thành công' : 'Mở khóa thành công');
  } catch (err) {
    notify(err.message, true, action === 'delete' ? 'Xóa tài khoản thất bại' : action === 'lock' ? 'Khóa tài khoản thất bại' : 'Mở khóa thất bại');
  }
};

/* ------------------------------------------------------------- học phần đã hoàn thành (tiên quyết) */
async function openCompleted(u) {
  completedUser = u;
  $('completedTitle').textContent = `Đã hoàn thành · ${u.name}`;
  await renderCompleted();
  $('completedDialog').showModal();
}
async function renderCompleted() {
  try {
    const done = await api(`/admin/users/${completedUser.id}/completed`);
    $('completedList').innerHTML = done.map(c => `<div class="slot-admin-row"><div><strong>${esc(c.code)}</strong><span>${esc(c.name)}${c.completed_at ? ' · ' + fmtDate(c.completed_at) : ''}</span></div><button class="danger-button" data-undo="${c.course_id}">Bỏ ghi nhận</button></div>`).join('')
      || '<p class="empty">Chưa ghi nhận học phần nào.</p>';
    const doneIds = new Set(done.map(c => c.course_id));
    $('completedCourse').innerHTML = courses.filter(c => !doneIds.has(c.id)).map(c => `<option value="${c.id}">${esc(c.code)} – ${esc(c.name)}</option>`).join('');
    $('completedAdd').disabled = !$('completedCourse').options.length;
  } catch (e) { notify(e.message, true, 'Không tải được học phần đã hoàn thành'); }
}
$('completedAdd').onclick = async () => {
  const courseId = Number($('completedCourse').value);
  if (!courseId) return;
  try {
    const d = await send(`/admin/users/${completedUser.id}/completed`, 'POST', {course_id: courseId});
    await renderCompleted(); await refresh(); notify(d.message, false, 'Ghi nhận hoàn thành thành công');
  } catch (e) { notify(e.message, true, 'Ghi nhận hoàn thành thất bại'); }
};
$('completedList').onclick = async e => {
  const b = e.target.closest('[data-undo]');
  if (!b) return;
  try {
    const d = await send(`/admin/users/${completedUser.id}/completed/${b.dataset.undo}`, 'DELETE');
    await renderCompleted(); notify(d.message, false, 'Bỏ ghi nhận thành công');
  } catch (err) { notify(err.message, true, 'Bỏ ghi nhận thất bại'); }
};

/* ------------------------------------------------------------- học phần */
function renderCourses() {
  const q = $('searchCourses').value.toLowerCase().trim();
  const found = courses.filter(c => `${c.code} ${c.name}`.toLowerCase().includes(q));
  $('courseRows').innerHTML = found.map(c => `<tr><td class="code">${esc(c.code)}</td><td><strong>${esc(c.name)}</strong><small class="sub">${esc(c.lecturer || 'Chưa phân công giảng viên')}</small></td><td>${c.prerequisites.length ? c.prerequisites.map(p => `<span class="prereq" title="${esc(p.name)}">${esc(p.code)}</span>`).join(' ') : '<span class="muted">Không có</span>'}</td><td>${c.current_enrolled} / ${c.max_students}</td><td>${c.waitlist_count ? `<button class="text-button" data-act="waitlist" data-id="${c.id}">${c.waitlist_count} sinh viên</button>` : '<span class="muted">0</span>'}</td><td><span class="pill ${c.is_full ? 'closed' : 'open'}">${c.is_full ? 'Đã đầy' : 'Còn chỗ'}</span></td><td><div class="admin-actions"><button class="secondary-button" data-act="schedule" data-id="${c.id}">Lịch học</button><button class="secondary-button" data-act="edit" data-id="${c.id}">Sửa</button><button class="danger-button" data-act="delete" data-id="${c.id}">Xóa</button></div></td></tr>`).join('')
    || '<tr><td colspan="7" class="empty">Không có học phần phù hợp.</td></tr>';
}

function openCourseForm(course) {
  editingCourseId = course ? course.id : null;
  $('courseDialogTitle').textContent = course ? `Sửa học phần ${course.code}` : 'Thêm học phần';
  $('cfCode').value = course?.code ?? '';
  $('cfName').value = course?.name ?? '';
  $('cfLecturer').value = course?.lecturer ?? '';
  $('cfStart').value = course?.start_date ?? '';
  $('cfEnd').value = course?.end_date ?? '';
  $('cfMax').value = course?.max_students ?? 30;
  const chosen = new Set((course?.prerequisites ?? []).map(p => p.id));
  const others = courses.filter(c => !course || c.id !== course.id);
  $('cfPrereq').innerHTML = others.map(c => `<label><input type="checkbox" value="${c.id}" ${chosen.has(c.id) ? 'checked' : ''}> <strong>${esc(c.code)}</strong> ${esc(c.name)}</label>`).join('') || '<p class="empty">Chưa có học phần khác.</p>';
  $('courseDialog').showModal();
}

$('addCourse').onclick = () => openCourseForm(null);
$('courseForm').onsubmit = async e => {
  e.preventDefault();
  const body = {
    code: $('cfCode').value.trim(), name: $('cfName').value.trim(), lecturer: $('cfLecturer').value.trim() || null,
    start_date: $('cfStart').value || null, end_date: $('cfEnd').value || null, max_students: Number($('cfMax').value),
    prerequisite_ids: [...$('cfPrereq').querySelectorAll('input:checked')].map(i => Number(i.value)),
  };
  if (!body.code || !body.name || !(body.max_students > 0)) return notify('Nhập đủ mã, tên học phần và sĩ số tối đa lớn hơn 0.', true, 'Thiếu thông tin học phần');
  const editing = editingCourseId !== null;
  try {
    const d = await send(editing ? `/admin/courses/${editingCourseId}` : '/admin/courses', editing ? 'PATCH' : 'POST', body);
    $('courseDialog').close(); await refresh();
    notify(`${d.code} - ${d.name}`, false, editing ? 'Cập nhật học phần thành công' : 'Thêm học phần thành công');
  } catch (err) { notify(err.message, true, editing ? 'Cập nhật học phần thất bại' : 'Thêm học phần thất bại'); }
};

$('courseRows').onclick = async e => {
  const b = e.target.closest('[data-act]');
  if (!b) return;
  const c = courses.find(x => x.id === Number(b.dataset.id));
  if (!c) return;
  if (b.dataset.act === 'edit') return openCourseForm(c);
  if (b.dataset.act === 'schedule') return openSchedule(c);
  if (b.dataset.act === 'waitlist') return openWaitlist(c);
  if (!await confirmInPage(`Xóa học phần ${c.code} - ${c.name}? Lịch học của học phần cũng bị xóa. Không thể xóa nếu đã có sinh viên đăng ký hoặc đang là môn tiên quyết của học phần khác.`, 'Xóa học phần', true, 'Xóa học phần')) return;
  try {
    const d = await send(`/admin/courses/${c.id}`, 'DELETE');
    await refresh(); notify(d.message, false, 'Xóa học phần thành công');
  } catch (err) { notify(err.message, true, 'Xóa học phần thất bại'); }
};

async function openWaitlist(c) {
  $('waitlistTitle').textContent = `Hàng chờ · ${c.code}`;
  try {
    const rows = await api(`/admin/courses/${c.id}/waitlist`);
    $('waitlistBody').innerHTML = rows.map(r => `<div class="slot-admin-row"><div><strong>#${r.position} · ${esc(r.name)}</strong><span>${esc(r.email || '')}${r.joined_at ? ' · ' + fmtDate(r.joined_at) : ''}</span></div></div>`).join('')
      || '<p class="empty">Không có sinh viên nào đang chờ.</p>';
    $('waitlistDialog').showModal();
  } catch (e) { notify(e.message, true, 'Không tải được danh sách chờ'); }
}

/* ------------------------------------------------------------- lịch học */
async function openSchedule(c) {
  scheduleCourse = c;
  $('scheduleDialogTitle').textContent = `${c.code} · ${c.name}`;
  resetSlotForm();
  await renderSlots();
  $('scheduleDialog').showModal();
}
async function renderSlots() {
  try {
    const slots = await api(`/schedules/${scheduleCourse.id}`);
    $('slotList').innerHTML = slots.map(s => `<div class="slot-admin-row"><div><strong>${DAYS[s.day]} · ${SHIFTS[s.shift]}</strong><span>${esc(s.start_time || '—')} – ${esc(s.end_time || '—')} · ${esc(s.room || 'Chưa có phòng')}</span></div><div class="admin-actions"><button class="secondary-button" data-slot-edit="${s.id}">Sửa</button><button class="danger-button" data-slot-del="${s.id}">Xóa</button></div></div>`).join('')
      || '<p class="empty">Học phần chưa có lịch học. Thêm buổi học bên dưới.</p>';
    $('slotList').dataset.slots = JSON.stringify(slots);
  } catch (e) { notify(e.message, true, 'Không tải được lịch học'); }
}
function resetSlotForm() {
  editingSlotId = null;
  $('sfDay').value = '2'; $('sfShift').value = 'sang'; $('sfStart').value = ''; $('sfEnd').value = ''; $('sfRoom').value = '';
  $('slotFormTitle').textContent = 'Thêm buổi học';
  $('slotSubmit').textContent = 'Thêm lịch';
  $('slotCancelEdit').hidden = true;
}
$('slotCancelEdit').onclick = resetSlotForm;
$('slotList').onclick = async e => {
  const slots = JSON.parse($('slotList').dataset.slots || '[]');
  const edit = e.target.closest('[data-slot-edit]'), del = e.target.closest('[data-slot-del]');
  if (edit) {
    const s = slots.find(x => x.id === Number(edit.dataset.slotEdit));
    if (!s) return;
    editingSlotId = s.id;
    $('sfDay').value = String(s.day); $('sfShift').value = s.shift; $('sfStart').value = s.start_time || ''; $('sfEnd').value = s.end_time || ''; $('sfRoom').value = s.room || '';
    $('slotFormTitle').textContent = 'Sửa buổi học'; $('slotSubmit').textContent = 'Lưu thay đổi'; $('slotCancelEdit').hidden = false;
  } else if (del) {
    if (!await confirmInPage('Xóa buổi học này? Sinh viên đã đăng ký sẽ không còn thấy buổi học này trong thời khóa biểu.', 'Xóa buổi học', true, 'Xóa buổi học')) return;
    try {
      const d = await send(`/schedules/${del.dataset.slotDel}`, 'DELETE');
      resetSlotForm(); await renderSlots(); notify(d.message, false, 'Xóa buổi học thành công');
    } catch (err) { notify(err.message, true, 'Xóa buổi học thất bại'); }
  }
};
$('slotForm').onsubmit = async e => {
  e.preventDefault();
  const body = {day: Number($('sfDay').value), shift: $('sfShift').value, start_time: $('sfStart').value || null, end_time: $('sfEnd').value || null, room: $('sfRoom').value.trim() || null};
  const editing = editingSlotId !== null;
  try {
    if (editing) await send(`/schedules/${editingSlotId}`, 'PATCH', body);
    else await send('/schedules', 'POST', {course_id: scheduleCourse.id, ...body});
    resetSlotForm(); await renderSlots();
    notify(`${DAYS[body.day]} · ${SHIFTS[body.shift]}`, false, editing ? 'Cập nhật buổi học thành công' : 'Thêm buổi học thành công');
  } catch (err) { notify(err.message, true, editing ? 'Cập nhật buổi học thất bại' : 'Thêm buổi học thất bại'); }
};

/* ------------------------------------------------------------- điều hướng chung */
document.querySelectorAll('[data-close]').forEach(b => b.onclick = () => $(b.dataset.close).close());
['scheduleDialog', 'completedDialog'].forEach(id => $(id).addEventListener('close', refresh));
function show(next) {
  view = next;
  $('usersPanel').hidden = next !== 'users'; $('coursesPanel').hidden = next !== 'courses';
  $('usersTab').classList.toggle('active', next === 'users'); $('coursesTab').classList.toggle('active', next === 'courses');
  $('pageTitle').textContent = next === 'users' ? 'Quản lý tài khoản' : 'Quản lý học phần';
  $('pageSubtitle').textContent = next === 'users' ? 'Theo dõi tình trạng tài khoản sinh viên và quyền truy cập hệ thống.' : 'Quản lý học phần, lịch học, sĩ số tối đa, môn tiên quyết và hàng chờ.';
}
$('usersTab').onclick = () => show('users'); $('coursesTab').onclick = () => show('courses');
$('searchUsers').oninput = renderUsers; $('searchCourses').oninput = renderCourses; $('reload').onclick = refresh;
async function logout() { await fetch('/logout', {method: 'POST'}); location.replace('/'); }
$('logoutTop').onclick = logout;
(async () => {
  try {
    const u = await api('/me');
    if (u.role !== 'admin') { location.replace('/dashboard'); return; }
    $('adminName').textContent = u.name;
    await refresh();
  } catch (e) { location.replace('/'); }
})();
