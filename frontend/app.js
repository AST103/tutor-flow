const API = 'https://d1z2fxef4f.execute-api.us-east-1.amazonaws.com/prod';
const AVATAR_CLASSES = ['av0', 'av1', 'av2'];

function formatDate(ts) {
  if (!ts) return 'never';
  try {
    return new Date(ts).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: '2-digit'
    });
  } catch {
    return 'never';
  }
}

function getInitials(name) {
  return name.split(' ').map(w => w[0]).join('');
}

function updateClock() {
  document.getElementById('ts').textContent = new Date().toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
}

updateClock();
setInterval(updateClock, 1000);

async function loadStudents() {
  const cards = document.getElementById('cards');
  cards.innerHTML = '<div class="loading-state">Loading students...</div>';

  try {
    const response = await fetch(API + '/students');
    const students = await response.json();
    students.sort((a, b) => (a.student_name || '').localeCompare((b.student_name || ''), undefined, { sensitivity: 'base' }));

    let html = '';
    let practiceCount = 0;
    let sessionCount = 0;

    const sel = document.getElementById('sel');
    sel.innerHTML = '<option value="">Select student</option>';

    students.forEach((student, i) => {
      if (student.last_practice_date) practiceCount++;
      if (student.last_session_date) sessionCount++;

      const avatarClass = AVATAR_CLASSES[i % AVATAR_CLASSES.length];
      const isActive = !!(student.last_practice_date || student.last_session_date);
      const statusTag = isActive
        ? '<span class="tag active">Active</span>'
        : '<span class="tag pending">Pending</span>';
      const typeTag = student.zoom_link
        ? '<span class="tag virtual">Virtual</span>'
        : '<span class="tag onsite">In-person</span>';

      html += `
        <div class="card">
          <div class="avatar ${avatarClass}">${getInitials(student.student_name)}</div>
          <div class="card-mid">
            <div class="card-name">${student.student_name}</div>
            <div class="card-subject">${student.subject}</div>
            <div class="card-data">
              <div>
                <div class="cd-label">Last practice</div>
                <div class="cd-value">${formatDate(student.last_practice_date)}</div>
              </div>
              <div>
                <div class="cd-label">Last session</div>
                <div class="cd-value">${formatDate(student.last_session_date)}</div>
              </div>
              <div>
                <div class="cd-label">Session day</div>
                <div class="cd-value">${student.session_day}</div>
              </div>
              <div>
                <div class="cd-label">Time</div>
                <div class="cd-value">${student.session_time}</div>
              </div>
            </div>
          </div>
          <div class="card-right">
            ${statusTag}
            ${typeTag}
            <div class="card-sched">${student.session_day}<br>${student.session_time}</div>
          </div>
        </div>
      `;

      sel.innerHTML += `<option value="${student.student_name}">${student.student_name}</option>`;
    });

    cards.innerHTML = html;
    document.getElementById('k-students').textContent = students.length;
    document.getElementById('k-practice').textContent = practiceCount;
    document.getElementById('k-sessions').textContent = sessionCount;

  } catch (err) {
    console.error('Failed to load students:', err);
    cards.innerHTML = '<div class="loading-state" style="color:#dc2626">Failed to load — check API connection</div>';
  }
}

async function logSession() {
  const res = document.getElementById('res');
  const studentName = document.getElementById('sel').value;
  const topicsCovered = document.getElementById('top').value.trim();
  const struggledWith = document.getElementById('str').value.trim();
  const notes = document.getElementById('not').value.trim();

  if (!studentName) {
    res.textContent = 'Please select a student first';
    res.className = 'res err';
    res.style.display = 'block';
    return;
  }

  try {
    const response = await fetch(API + '/log-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_name: studentName,
        topics_covered: topicsCovered || 'general review',
        struggled_with: struggledWith || 'nothing specific',
        notes: notes || 'none'
      })
    });

    const data = await response.json();

    if (response.ok) {
      res.textContent = 'Session saved — Bedrock will use this Sunday';
      res.className = 'res ok';
      res.style.display = 'block';
      document.getElementById('top').value = '';
      document.getElementById('str').value = '';
      document.getElementById('not').value = '';
      document.getElementById('sel').value = '';
      loadStudents();
    } else {
      res.textContent = data.message || 'Something went wrong';
      res.className = 'res err';
      res.style.display = 'block';
    }
  } catch (err) {
    console.error('Failed to log session:', err);
    res.textContent = 'Connection failed — check network';
    res.className = 'res err';
    res.style.display = 'block';
  }
}

loadStudents();