const registerForm = document.getElementById("registerForm");

registerForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const name = document.getElementById("name").value.trim();
  const email = document.getElementById("email").value.trim();
  const phone = document.getElementById("phone").value.trim();
  const password = document.getElementById("password").value.trim();
  const age = document.getElementById("age").value.trim();
  const gender = document.getElementById("gender").value;
  const location = document.getElementById("location").value.trim();

  // Basic validation
  if (!name || !email || !phone || !password || !age || !gender || !location) {
    alert("⚠️ Please fill all fields");
    return;
  }

  try {
    const response = await fetch("http://127.0.0.1:5000/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, phone, password, age, gender, location })
    });

    const data = await response.json();

    if (data.success) {
      alert("✅ Registration successful! Redirecting to login...");
      window.location.href = "login.html";
    } else {
      alert("❌ Registration failed: " + data.message);
    }
  } catch (err) {
    console.error("Error:", err);
    alert("⚠️ Server error. Try again later.");
  }
});
