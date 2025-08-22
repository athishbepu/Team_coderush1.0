document.getElementById("registerForm").addEventListener("submit", function(e) {
  e.preventDefault(); // stop default form reload

  const password = document.getElementById("password").value;
  const confirmPassword = document.getElementById("confirmPassword").value;

  if (password !== confirmPassword) {
    alert("Passwords do not match!");
    return;
  }

  alert("Registration Successful 🚀");

  // Later you can send data to Flask backend like this:
  /*
  fetch("http://localhost:5000/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      fullname: document.getElementById("fullname").value,
      email: document.getElementById("email").value,
      password: password
    })
  })
  .then(res => res.json())
  .then(data => console.log(data));
  */
});
