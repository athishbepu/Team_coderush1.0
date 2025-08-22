// Select the form
const loginForm = document.getElementById("loginForm");

// Handle submit
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();

  // Remove old error messages
  document.querySelectorAll(".error-msg").forEach(el => el.remove());

  let hasError = false;

  // Validation for empty fields
  if (!username) {
    showError("username", "Username / Phone is required");
    hasError = true;
  }

  if (!password) {
    showError("password", "Password is required");
    hasError = true;
  }

  if (hasError) return;

  // 🔗 Example placeholder for Flask API call
  try {
    const response = await fetch("http://127.0.0.1:5000/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    if (data.success) {
      alert("✅ Login successful! Redirecting...");
      // Example redirect
      window.location.href = "/dashboard";
    } else {
      showError("password", "Invalid username or password");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("⚠️ Server error. Please try again later.");
  }
});

// Helper function to show error messages under inputs
function showError(inputId, message) {
  const input = document.getElementById(inputId);
  const error = document.createElement("p");
  error.className = "error-msg";
  error.style.color = "#ff6b6b";
  error.style.fontSize = "12px";
  error.style.marginTop = "5px";
  error.textContent = message;
  input.insertAdjacentElement("afterend", error);
}
