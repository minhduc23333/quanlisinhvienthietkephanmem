const $ = id => document.getElementById(id);
let studentId = 0;
const state = {
  courses: [], own: [], schedule: [], waitlist: [], completed: [],
  selected: null, view: 'courses', preview: [], keepPreview: false, action: null,
};

const escapeText = t => String(t ?? '').replace(/[&<>"']/g, ch => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[ch]));
const weekdays = {2: 'Thứ 2', 3: 'Thứ 3', 4: 'Thứ 4', 5: 'Thứ 5', 6: 'Thứ 6', 7: 'Thứ 7'};
const shiftName = s => s === 'sang' ? 'Sáng' : 'Chiều';
const formatDate = date => { const p = String(date).split('-'); return p.length === 3 ? `${p[2]}/${p[1]}/${p[0]}` : date; };
const formatDateTime = iso => { if (!iso) return ''; const d = new Date(iso); return isNaN(d) ? '' : d.toLocaleDateString('vi-VN'); };

async function api(path, opts) {
  const r = await fetch(path, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    if (r.status === 401 || r.status === 403) location.replace('/');
    throw Error(typeof data.detail === 'string' ? data.detail : `Lỗi API (${r.status})`);
  }
  return data;
}
const post = (path, body) => api(path, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
function notify(text, error = false, title = '') { if (text) showToast(text, error ? 'error' : 'success', title); }

const TITLES = {
  courses: ['Đăng ký học phần', 'Tra cứu môn học và chọn lịch phù hợp trước khi đăng ký.'],
  calendar: ['Thời khóa biểu của tôi', 'Lịch học cá nhân của bạn, trình bày theo từng ca trong tuần.'],
  status: ['Hàng chờ & đã học', 'Theo dõi vị trí trong danh sách chờ và các học phần bạn đã hoàn thành.'],
};
function show(view) {
  state.view = view;
  $('courseSection').hidden = view !== 'courses';
  $('calendarSection').hidden = view !== 'calendar';
  $('statusSection').hidden = view !== 'status';
  $('menuCourses').classList.toggle('active', view === 'courses');
  $('menuTimetable').classList.toggle('active', view === 'calendar');
  $('menuStatus').classList.toggle('active', view === 'status');
  [$('pageTitle').textContent, $('pageDescription').textContent] = TITLES[view];
  if (view === 'calendar') renderCalendar();
}

async function refresh() {
  try {
    const previousWait = state.waitlist.map(w => w.course_id);
    const previousOwn = state.own.map(o => o.course_id);
    const [courses, own, schedule, waitlist, completed] = await Promise.all([
      api('/courses'), api(`/enrollments/${studentId}`), api(`/enrollments/${studentId}/schedule`),
      api(`/waitlist/${studentId}`), api(`/students/${studentId}/completed`),
    ]);
    Object.assign(state, {courses, own, schedule, waitlist, completed});
    $('totalCourses').textContent = courses.length;
    $('myCount').textContent = own.length;
    $('openCourses').textContent = courses.filter(c => !c.is_full).length;
    $('waitCount').textContent = waitlist.length;
    renderCourses(); renderCalendar(); renderOwn(); renderStatus();
    // Báo khi một học phần đang chờ vừa được hệ thống xếp vào lớp.
    own.filter(o => previousWait.includes(o.course_id) && !previousOwn.includes(o.course_id))
       .forEach(o => notify(`Bạn đã được xếp vào học phần ${o.name} từ danh sách chờ.`, false, 'Đã có chỗ trong danh sách chờ'));
  } catch (e) { notify(e.message, true, 'Không tải được dữ liệu học phần'); }
}

function prereqBadges(c) {
  if (!c.prerequisites.length) return '<span class="muted">Không có</span>';
  return c.prerequisites.map(p => `<span class="prereq ${p.met ? 'met' : 'unmet'}" title="${escapeText(p.name)}">${escapeText(p.code)} ${p.met ? '✓' : '✗'}</span>`).join(' ');
}

function courseAction(c) {
  const mine = state.own.some(x => x.course_id === c.id);
  if (mine) return {label: 'Đã đăng ký', disabled: true};
  if (c.completed) return {label: 'Đã hoàn thành', disabled: true};
  if (c.waitlist_position) return {label: `Đang chờ #${c.waitlist_position}`};
  if (!c.prerequisites_met) return {label: 'Thiếu tiên quyết'};
  if (c.is_full) return {label: 'Xem & vào hàng chờ'};
  return {label: 'Xem & đăng ký'};
}

function renderCourses() {
  const q = $('search').value.trim().toLowerCase();
  const rows = state.courses.filter(c => (c.name + ' ' + c.code).toLowerCase().includes(q));
  $('courseRows').innerHTML = rows.map(c => {
    const action = courseAction(c);
    const status = c.is_full ? `Đã đầy${c.waitlist_count ? ` · ${c.waitlist_count} chờ` : ''}` : 'Còn chỗ';
    return `<tr><td class="code">${escapeText(c.code)}</td><td><strong>${escapeText(c.name)}</strong></td>`
      + `<td>${prereqBadges(c)}</td>`
      + `<td><button class="text-button" data-preview="${c.id}">Xem chi tiết</button></td>`
      + `<td>${c.current_enrolled}/${c.max_students}</td>`
      + `<td><span class="pill ${c.is_full ? 'closed' : 'open'}">${status}</span></td>`
      + `<td><button class="action-button" data-preview="${c.id}" ${action.disabled ? 'disabled' : ''}>${action.label}</button></td></tr>`;
  }).join('') || '<tr><td colspan="7" class="empty">Không có môn học phù hợp.</td></tr>';
}

// Quyết định nút chính của hộp thoại chi tiết và thông báo đi kèm.
function decideDialog(c, mine, conflicts) {
  const unmet = c.prerequisites.filter(p => !p.met);
  if (mine) return {label: 'Đã đăng ký', disabled: true, note: 'Bạn đã đăng ký học phần này.'};
  if (c.completed) return {label: 'Đã hoàn thành', disabled: true, note: 'Bạn đã hoàn thành học phần này.'};
  if (c.waitlist_position) return {label: 'Rời danh sách chờ', action: 'leave',
    note: `Bạn đang ở vị trí #${c.waitlist_position} trong danh sách chờ. Khi có chỗ trống, hệ thống sẽ tự đăng ký cho bạn.`};
  if (unmet.length) return {label: 'Chưa đủ tiên quyết', disabled: true, warn: true,
    note: 'Cần hoàn thành trước: ' + unmet.map(p => `${p.code} - ${p.name}`).join(', ')};
  if (conflicts.length) return {label: 'Trùng lịch', disabled: true, warn: true,
    note: 'Trùng lịch với môn đã đăng ký: ' + conflicts.map(s => `${weekdays[s.day]} (${shiftName(s.shift)})`).join(', ')};
  if (!state.preview.length) return {label: 'Chưa có lịch', disabled: true, note: 'Học phần chưa có lịch học.'};
  if (c.is_full) return {label: 'Vào danh sách chờ', action: 'waitlist',
    note: `Lớp đã đầy. Có ${c.waitlist_count} sinh viên đang chờ trước bạn; bạn sẽ được xếp vào lớp theo thứ tự khi có chỗ.`};
  return {label: 'Đăng ký học phần', action: 'enroll', note: 'Không trùng lịch và đủ điều kiện đăng ký.'};
}

async function previewCourse(id) {
  try {
    const c = await api(`/courses/${id}/details`);
    state.selected = state.courses.find(x => x.id === id);
    state.preview = c.schedules;
    $('detailName').textContent = c.name;
    $('detailCode').textContent = `${c.code} · Học phần ${c.is_full ? 'đã đầy' : 'đang nhận đăng ký'}`;
    $('detailLecturer').textContent = c.lecturer;
    $('detailDates').textContent = c.start_date && c.end_date ? `${formatDate(c.start_date)} – ${formatDate(c.end_date)}` : 'Đang cập nhật';
    $('detailCapacity').textContent = `${c.current_enrolled}/${c.max_students} sinh viên` + (c.waitlist_count ? ` · ${c.waitlist_count} đang chờ` : '');
    $('detailPrereq').innerHTML = c.prerequisites.length
      ? c.prerequisites.map(p => `<div class="prereq-row ${p.met ? 'met' : 'unmet'}"><strong>${escapeText(p.code)}</strong><span>${escapeText(p.name)}</span><em>${p.met ? '✓ Đã hoàn thành' : '✗ Chưa hoàn thành'}</em></div>`).join('')
      : '<p class="empty">Học phần này không yêu cầu môn tiên quyết.</p>';
    $('detailSlots').innerHTML = c.schedules.length
      ? c.schedules.map(s => `<div class="detail-session"><div><strong>${weekdays[s.day]}</strong><span>${shiftName(s.shift)}</span></div><div><strong>${escapeText(s.start_time)} – ${escapeText(s.end_time)}</strong><span>${escapeText(s.room)}</span></div></div>`).join('')
      : '<p class="empty">Chưa có lịch học được phân công.</p>';
    const mine = state.own.some(x => x.course_id === id);
    const conflicts = state.preview.filter(p => state.schedule.some(s => s.day === p.day && s.shift === p.shift));
    const d = decideDialog(c, mine, conflicts);
    state.action = d.action || null;
    $('detailConflict').textContent = d.note;
    $('detailConflict').classList.toggle('warning', !!d.warn);
    $('confirmEnroll').disabled = !!d.disabled;
    $('confirmEnroll').textContent = d.label;
    $('detailDialog').showModal();
  } catch (e) { notify(e.message, true, 'Không xem được chi tiết học phần'); }
}

async function submitAction() {
  const course = state.selected, action = state.action;
  if (!course || !action) return;
  try {
    if (action === 'enroll') {
      const data = await post('/enrollments', {student_id: studentId, course_id: course.id});
      closeDialog(); await refresh(); notify(data.message, false, 'Đăng ký học phần thành công');
    } else if (action === 'waitlist') {
      const data = await post('/waitlist', {student_id: studentId, course_id: course.id});
      closeDialog(); await refresh(); notify(data.message, false, 'Vào danh sách chờ thành công');
    } else if (action === 'leave') {
      await leaveWaitlist(course.id, true);
    }
  } catch (e) {
    const title = {enroll: 'Đăng ký học phần thất bại', waitlist: 'Vào danh sách chờ thất bại', leave: 'Rời danh sách chờ thất bại'}[action];
    notify(e.message, true, title);
  }
}
function closeDialog() { $('detailDialog').close(); state.preview = []; }

async function leaveWaitlist(courseId, fromDialog = false) {
  if (!await confirmInPage('Bạn sẽ mất vị trí hiện tại trong danh sách chờ của học phần này. Bạn có muốn rời danh sách chờ?', 'Rời danh sách chờ')) return;
  try {
    const data = await api(`/waitlist/${studentId}/${courseId}`, {method: 'DELETE'});
    if (fromDialog) closeDialog();
    await refresh(); notify(data.message, false, 'Rời danh sách chờ thành công');
  } catch (e) { notify(e.message, true, 'Rời danh sách chờ thất bại'); }
}

async function cancel(id) {
  if (!await confirmInPage('Học phần sẽ được xóa khỏi thời khóa biểu của bạn. Bạn có muốn hủy đăng ký môn học này?', 'Hủy đăng ký học phần')) return;
  try {
    const data = await api(`/enrollments/${studentId}/${id}`, {method: 'DELETE'});
    await refresh(); notify(data.message, false, 'Hủy đăng ký thành công');
  } catch (e) { notify(e.message, true, 'Hủy đăng ký thất bại'); }
}

function renderOwn() {
  $('enrolledList').innerHTML = state.own.map(c => `<div class="enrolled-item"><div><strong>${escapeText(c.name)}</strong><small>${escapeText(c.code)}</small></div><button class="secondary-button" data-cancel="${c.course_id}">Hủy đăng ký</button></div>`).join('')
    || '<p class="empty">Bạn chưa đăng ký học phần nào.</p>';
}

function renderStatus() {
  $('waitlistList').innerHTML = state.waitlist.map(w => `<div class="enrolled-item"><div><strong>${escapeText(w.name)}</strong><small>${escapeText(w.code)} · Vị trí #${w.position}${w.joined_at ? ' · vào hàng chờ ' + formatDateTime(w.joined_at) : ''}</small></div><button class="secondary-button" data-leave="${w.course_id}">Rời danh sách chờ</button></div>`).join('')
    || '<p class="empty">Bạn không có trong danh sách chờ nào.</p>';
  $('completedList').innerHTML = state.completed.map(c => `<div class="enrolled-item"><div><strong>${escapeText(c.name)}</strong><small>${escapeText(c.code)}${c.completed_at ? ' · hoàn thành ' + formatDateTime(c.completed_at) : ''}</small></div><span class="pill open">Đã hoàn thành</span></div>`).join('')
    || '<p class="empty">Chưa có học phần nào được ghi nhận hoàn thành.</p>';
}

function renderCalendar() {
  const cells = ['<div class="calendar-head corner">Ca học</div>', ...Object.values(weekdays).map(x => `<div class="calendar-head">${x}</div>`)];
  for (const shift of ['sang', 'chieu']) {
    cells.push(`<div class="calendar-shift">${shiftName(shift)}</div>`);
    for (let d = 2; d <= 7; d++) {
      const existing = state.schedule.filter(s => s.day === d && s.shift === shift);
      const preview = state.preview.filter(s => s.day === d && s.shift === shift);
      let content = existing.map(s => `<div class="lesson"><strong>${escapeText(s.course_name)}</strong><small>${escapeText(s.code)} · ${escapeText(s.start_time || '')}–${escapeText(s.end_time || '')} · ${escapeText(s.room || '')}</small></div>`).join('');
      if (state.selected && preview.length) content += `<div class="lesson preview"><strong>${escapeText(state.selected.name)}</strong><small>${escapeText(preview[0].start_time)}–${escapeText(preview[0].end_time)} · ${escapeText(preview[0].room)}</small></div>`;
      cells.push(`<div class="calendar-cell">${content}</div>`);
    }
  }
  $('calendar').innerHTML = cells.join('');
}

$('search').oninput = renderCourses;
$('courseRows').onclick = e => { const b = e.target.closest('[data-preview]'); if (b) previewCourse(Number(b.dataset.preview)); };
$('enrolledList').onclick = e => { const b = e.target.closest('[data-cancel]'); if (b) cancel(Number(b.dataset.cancel)); };
$('waitlistList').onclick = e => { const b = e.target.closest('[data-leave]'); if (b) leaveWaitlist(Number(b.dataset.leave)); };
const resetPreview = () => { state.preview = []; state.selected = null; };
$('menuCourses').onclick = () => { resetPreview(); show('courses'); };
$('menuTimetable').onclick = () => { resetPreview(); show('calendar'); };
$('menuStatus').onclick = () => { resetPreview(); show('status'); };
$('reload').onclick = refresh;
async function logout() { await fetch('/logout', {method: 'POST'}); location.replace('/'); }
$('logout').onclick = logout; $('logoutTop').onclick = logout;
$('closeDialog').onclick = () => $('detailDialog').close();
$('confirmEnroll').onclick = submitAction;
$('viewCalendar').onclick = () => { state.keepPreview = true; $('detailDialog').close(); show('calendar'); };
$('detailDialog').addEventListener('close', () => {
  if (state.keepPreview) { state.keepPreview = false; return; }
  state.preview = []; state.selected = null;
  if (state.view === 'calendar') renderCalendar();
});
// Quay lại tab trình duyệt: tải lại để thấy kết quả xếp từ danh sách chờ.
document.addEventListener('visibilitychange', () => { if (!document.hidden && studentId) refresh(); });

async function init() {
  try {
    const u = await api('/me');
    if (u.role !== 'student') { location.replace('/admin'); return; }
    studentId = u.id;
    $('studentName').textContent = u.name;
    $('avatar').textContent = (u.name.split(' ').slice(-2).map(x => x[0]).join('') || 'SV').toUpperCase();
    await refresh();
  } catch (e) { location.replace('/'); }
}
init();
