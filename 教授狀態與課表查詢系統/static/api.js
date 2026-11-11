/* ===================================================================
   前端共用：狀態定義、節次、工具函式、與 Python 後端 API 溝通
   由 index.html（學生端）與 professor.html（教授端）共同載入
   =================================================================== */

const STATUS = {
  unknown  : { label:'尚未更新',      dot:'#9aa5b1' },
  available: { label:'空閒中・可洽談', dot:'#22c55e' },
  office   : { label:'在辦公室',      dot:'#2563eb' },
  class    : { label:'上課中',        dot:'#6366f1' },
  meeting  : { label:'開會中',        dot:'#f59e0b' },
  out      : { label:'外出中',        dot:'#94a3b8' },
  leave    : { label:'休假／請假',    dot:'#ef4444' },
};

const PERIODS = [
  {id:'1', label:'第1節', time:'08:10–09:00'},
  {id:'2', label:'第2節', time:'09:10–10:00'},
  {id:'3', label:'第3節', time:'10:10–11:00'},
  {id:'4', label:'第4節', time:'11:10–12:00'},
  {id:'5', label:'第5節', time:'13:10–14:00'},
  {id:'6', label:'第6節', time:'14:10–15:00'},
  {id:'7', label:'第7節', time:'15:10–16:00'},
  {id:'8', label:'第8節', time:'16:10–17:00'},
  {id:'9', label:'第9節', time:'17:10–18:00'},
];
const DAYS = [
  {id:'mon',label:'星期一'},
  {id:'tue',label:'星期二'},
  {id:'wed',label:'星期三'},
  {id:'thu',label:'星期四'},
  {id:'fri',label:'星期五'},
];

/* 從後端取得、目前畫面上使用的教授清單 */
let PROFESSORS = [];
function getProf(id){ return PROFESSORS.find(p => p.id === id); }

/* ---------------- 工具函式 ---------------- */
const $ = (s, el=document) => el.querySelector(s);
function esc(s){
  return String(s==null?'':s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function initials(name){ return esc(String(name||'').slice(0,2)); }
function fmtTime(ts){
  if(!ts) return '尚未更新';
  const d = new Date(ts), p = n => String(n).padStart(2,'0');
  return `${d.getFullYear()}/${p(d.getMonth()+1)}/${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}
let toastTimer;
function toast(msg){
  const t = $('#toast'); if(!t){ alert(msg); return; }
  t.textContent = msg; t.classList.add('show');
  clearTimeout(toastTimer); toastTimer = setTimeout(()=>t.classList.remove('show'), 1900);
}
function badgeHTML(statusId){
  const s = STATUS[statusId] || STATUS.unknown;
  return `<span class="badge"><span class="dot" style="background:${s.dot}"></span>${s.label}</span>`;
}
/* 課表表格：editable=true 產生輸入框，false 產生純文字 */
function ttTableHTML(schedule, editable){
  schedule = schedule || {};
  const head = `<tr><th>節次 / 時間</th>${DAYS.map(d=>`<th>${d.label}</th>`).join('')}</tr>`;
  const rows = PERIODS.map(per => {
    const cells = DAYS.map(day => {
      const key = `${day.id}-${per.id}`;
      const val = schedule[key] || '';
      if(editable){
        return `<td><input type="text" data-cell="${key}" value="${esc(val)}" placeholder="－"></td>`;
      }
      return val.trim() ? `<td class="has">${esc(val)}</td>` : `<td style="color:#cbd5e1">－</td>`;
    }).join('');
    return `<tr><td class="per">${per.label}<br>${per.time}</td>${cells}</tr>`;
  }).join('');
  return `<div class="tt-wrap"><table class="tt"><thead>${head}</thead><tbody>${rows}</tbody></table></div>`;
}

/* ---------------- 與 Python 後端 API 溝通 ---------------- */
async function apiPost(url, body){
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}
async function apiGetProfessors(){
  const res = await fetch('/api/professors');
  const data = await res.json();
  PROFESSORS = (data && data.professors) || [];
  return PROFESSORS;
}
function apiLogin(id, password){ return apiPost('/api/login', { id, password }); }
function apiSaveStatus(id, password, status, note){ return apiPost('/api/status', { id, password, status, note }); }
function apiSaveSchedule(id, password, schedule){ return apiPost('/api/schedule', { id, password, schedule }); }
function apiChangePassword(id, password, newPassword){ return apiPost('/api/password', { id, password, newPassword }); }
