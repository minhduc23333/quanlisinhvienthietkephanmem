const $ = id => document.getElementById(id);
let studentId = 0;
const state = {courses:[], own:[], schedule:[], selected:null, view:'courses', preview:[], keepPreview:false};

const escapeText = t => String(t ?? '').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
async function api(path, opts) { const r=await fetch(path,opts);const data=await r.json().catch(()=>({}));if(!r.ok){if(r.status===401||r.status===403){location.replace('/');}throw Error(typeof data.detail==='string'?data.detail:`Lỗi API (${r.status})`);}return data; }
function notify(text,error=false,title=''){if(text)showToast(text,error?'error':'success',title);}
const weekdays = {2:'Thứ 2',3:'Thứ 3',4:'Thứ 4',5:'Thứ 5',6:'Thứ 6',7:'Thứ 7'};
const shiftName = s => s==='sang'?'Sáng':'Chiều';
function show(view) {state.view=view;$('courseSection').hidden=view!=='courses';$('calendarSection').hidden=view!=='calendar';$('menuCourses').classList.toggle('active',view==='courses');$('menuTimetable').classList.toggle('active',view==='calendar');$('pageTitle').textContent=view==='courses'?'Đăng ký học phần':'Thời khóa biểu của tôi';$('pageDescription').textContent=view==='courses'?'Tra cứu môn học và chọn lịch phù hợp trước khi đăng ký.':'Lịch học cá nhân của bạn, trình bày theo từng ca trong tuần.';if(view==='calendar') renderCalendar();}
async function refresh() {try { const [courses,own,schedule] = await Promise.all([api('/courses'),api(`/enrollments/${studentId}`),api(`/enrollments/${studentId}/schedule`)]);Object.assign(state,{courses,own,schedule});$('totalCourses').textContent=courses.length;$('myCount').textContent=own.length;$('openCourses').textContent=courses.filter(c=>!c.is_full).length;renderCourses();renderCalendar();renderOwn();notify('');}catch(e){notify(e.message,true,'Không tải được dữ liệu học phần')}}
function renderCourses() {const q=$('search').value.trim().toLowerCase();const rows=state.courses.filter(c=>(c.name+' '+c.code).toLowerCase().includes(q));$('courseRows').innerHTML=rows.map(c=>{const mine=state.own.some(x=>x.course_id===c.id);const full=c.is_full;return `<tr><td class="code">${escapeText(c.code)}</td><td><strong>${escapeText(c.name)}</strong></td><td><button class="text-button" data-preview="${c.id}">Xem chi tiết</button></td><td>${c.current_enrolled}/${c.max_students}</td><td><span class="pill ${full?'closed':'open'}">${full?'Đã đầy':'Còn chỗ'}</span></td><td><button class="action-button" data-preview="${c.id}" ${mine||full?'disabled':''}>${mine?'Đã đăng ký':full?'Đã đầy':'Xem & đăng ký'}</button></td></tr>`}).join('') || '<tr><td colspan="6" class="empty">Không có môn học phù hợp.</td></tr>';}
async function previewCourse(id) {
 try {
  const c=await api(`/courses/${id}/details`);
  state.selected=state.courses.find(x=>x.id===id);
  state.preview=c.schedules;
  $('detailName').textContent=c.name;
  $('detailCode').textContent=`${c.code} · Học phần ${c.is_full?'đã đầy':'đang nhận đăng ký'}`;
  $('detailLecturer').textContent=c.lecturer;
  $('detailDates').textContent=c.start_date&&c.end_date?`${formatDate(c.start_date)} – ${formatDate(c.end_date)}`:'Đang cập nhật';
  $('detailCapacity').textContent=`${c.current_enrolled}/${c.max_students} sinh viên`;
  $('detailSlots').innerHTML=c.schedules.length?c.schedules.map(s=>`<div class="detail-session"><div><strong>${weekdays[s.day]}</strong><span>${shiftName(s.shift)}</span></div><div><strong>${escapeText(s.start_time)} – ${escapeText(s.end_time)}</strong><span>${escapeText(s.room)}</span></div></div>`).join(''):'<p class="empty">Chưa có lịch học được phân công.</p>';
  const conflicts=state.preview.filter(p=>state.schedule.some(s=>s.day===p.day&&s.shift===p.shift));
  $('detailConflict').textContent=conflicts.length?'Trùng lịch với môn đã đăng ký: '+conflicts.map(s=>`${weekdays[s.day]} (${shiftName(s.shift)})`).join(', '):'Không trùng lịch với các học phần đã đăng ký.';
  $('detailConflict').classList.toggle('warning',conflicts.length>0);
  const mine=state.own.some(x=>x.course_id===id);
  $('confirmEnroll').disabled=!!(mine||c.is_full||conflicts.length||!state.preview.length);
  $('confirmEnroll').textContent=mine?'Đã đăng ký':c.is_full?'Hết chỗ':conflicts.length?'Trùng lịch':!state.preview.length?'Chưa có lịch':'Đăng ký học phần';
  $('detailDialog').showModal();
 }catch(e){notify(e.message,true,'Không xem được chi tiết học phần')}
}
function formatDate(date){const parts=String(date).split('-');return parts.length===3?`${parts[2]}/${parts[1]}/${parts[0]}`:date;}

async function enroll() {const course=state.selected;if(!course)return;try {const data=await api('/enrollments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({student_id:studentId,course_id:course.id})});$('detailDialog').close();state.preview=[];await refresh();notify(data.message,false,'Đăng ký học phần thành công'); }catch(e){notify(e.message,true,'Đăng ký học phần thất bại')}}
async function cancel(id){if(!await confirmInPage('Học phần sẽ được xóa khỏi thời khóa biểu của bạn. Bạn có muốn hủy đăng ký môn học này?', 'Hủy đăng ký học phần'))return;try{const data=await api(`/enrollments/${studentId}/${id}`,{method:'DELETE'});await refresh();notify(data.message,false,'Hủy đăng ký thành công');}catch(e){notify(e.message,true,'Hủy đăng ký thất bại')}}
function renderOwn(){ $('enrolledList').innerHTML=state.own.map(c=>`<div class="enrolled-item"><div><strong>${escapeText(c.name)}</strong><small>${escapeText(c.code)}</small></div><button class="secondary-button" data-cancel="${c.course_id}">Hủy đăng ký</button></div>`).join('')||'<p class="empty">Bạn chưa đăng ký học phần nào.</p>'; }
function renderCalendar(){const shifts=['sang','chieu'];const cells=['<div class="calendar-head corner">Ca học</div>',...Object.values(weekdays).map(x=>`<div class="calendar-head">${x}</div>`)];for(const shift of shifts){cells.push(`<div class="calendar-shift">${shiftName(shift)}</div>`);for(let d=2;d<=7;d++){const existing=state.schedule.filter(s=>s.day===d&&s.shift===shift);const preview=state.preview.filter(s=>s.day===d&&s.shift===shift);let content=existing.map(s=>`<div class="lesson"><strong>${escapeText(s.course_name)}</strong><small>${escapeText(s.code)} · ${escapeText(s.start_time||'')}–${escapeText(s.end_time||'')} · ${escapeText(s.room||'')}</small></div>`).join('');if(state.selected&&preview.length)content+=`<div class="lesson preview"><strong>${escapeText(state.selected.name)}</strong><small>${escapeText(preview[0].start_time)}–${escapeText(preview[0].end_time)} · ${escapeText(preview[0].room)}</small></div>`;cells.push(`<div class="calendar-cell">${content}</div>`);}}$('calendar').innerHTML=cells.join('');}
$('search').oninput=renderCourses;
$('courseRows').onclick=e=>{const b=e.target.closest('[data-preview]');if(b)previewCourse(Number(b.dataset.preview));};
$('enrolledList').onclick=e=>{const b=e.target.closest('[data-cancel]');if(b)cancel(Number(b.dataset.cancel));};
$('menuCourses').onclick=()=>{state.preview=[];state.selected=null;show('courses');};
$('menuTimetable').onclick=()=>{state.preview=[];state.selected=null;show('calendar');};
$('reload').onclick=refresh;
async function logout(){await fetch('/logout',{method:'POST'});location.replace('/');}
$('logout').onclick=logout;$('logoutTop').onclick=logout;
$('closeDialog').onclick=()=>$('detailDialog').close();
$('confirmEnroll').onclick=enroll;
$('viewCalendar').onclick=()=>{state.keepPreview=true;$('detailDialog').close();show('calendar');};
$('detailDialog').addEventListener('close',()=>{if(state.keepPreview){state.keepPreview=false;return;}state.preview=[];state.selected=null;if(state.view==='calendar')renderCalendar();});
async function init(){try{const u=await api('/me');if(u.role!=='student'){location.replace('/admin');return;}studentId=u.id;$('studentName').textContent=u.name;$('avatar').textContent=(u.name.split(' ').slice(-2).map(x=>x[0]).join('')||'SV').toUpperCase();await refresh();}catch(e){location.replace('/');}}
init();

