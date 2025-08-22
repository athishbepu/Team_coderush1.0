document.getElementById("loginForm").addEventListener("submit", function(e) {
  e.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();

  if(username && password){
    alert("Login successful ✅ (connect this with Flask later)");
    // Example fetch to backend:
    /*
    fetch("http://127.0.0.1:5000/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    })
    .then(res => res.json())
    .then(data => console.log(data))
    */
  } else {
    alert("Please fill all fields ❌");
  }
});
