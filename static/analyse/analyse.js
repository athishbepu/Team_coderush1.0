document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('analyseForm');
  const graphs = document.getElementById('analyticsGraphs');

  if (!form) return;

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    const res = await fetch('/analyse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    const result = await res.json();
    renderAnalytics(result);
  });

  function renderAnalytics(data) {
    graphs.innerHTML = `
      <div class="mb-3"><strong>Health Details:</strong></div>
      <ul class="mb-3">
        <li><strong>Age:</strong> ${data.age}</li>
        <li><strong>Weight:</strong> ${data.weight} kg</li>
        <li><strong>Height:</strong> ${data.height} cm</li>
  <li><strong>Blood Pressure:</strong> ${data.bp_systolic}/${data.bp_diastolic} mmHg</li>
  <li><strong>Heart Rate:</strong> ${data.heart_rate} bpm</li>
  <li><strong>Blood Sugar:</strong> ${data.blood_sugar} mg/dL</li>
  <li><strong>Cholesterol:</strong> ${data.cholesterol} mg/dL</li>
  <li><strong>Activity Level:</strong> ${data.activity_level || 'N/A'}</li>
  <li><strong>Diet Type:</strong> ${data.diet_type || 'N/A'}</li>
  <li><strong>Symptoms:</strong> ${data.symptoms || 'N/A'}</li>
  <li><strong>Habits:</strong> ${data.habits || 'N/A'}</li>
      </ul>
      <div class="mb-3"><strong>Analysis:</strong></div>
      <ul>
        <li><strong>BMI:</strong> ${data.bmi} (${data.bmi_status})</li>
        <li><strong>Risk Score:</strong> ${data.risk_score}</li>
  <li><strong>Hypertension:</strong> ${data.hypertension}</li>
  <li><strong>Diabetes:</strong> ${data.diabetes}</li>
  <li><strong>Cholesterol Status:</strong> ${data.cholesterol_status}</li>
      </ul>
    `;
  }
});