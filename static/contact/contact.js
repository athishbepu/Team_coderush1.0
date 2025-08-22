document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('btnReturn').onclick = function() {
    window.location.href = '/chat';
  };
  document.getElementById('btnSanjeevani').onclick = function() {
    window.open('https://esanjeevani.mohfw.gov.in/', '_blank');
  };
  document.getElementById('btnBHAH').onclick = function() {
    window.open('https://abha.abdm.gov.in/', '_blank');
  };
});
