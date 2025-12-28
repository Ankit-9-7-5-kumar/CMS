// toggles mobile nav
document.addEventListener("DOMContentLoaded", function(){
  const toggle = document.getElementById("nav-toggle");
  const links = document.getElementById("nav-links");
function toggleMenu() {
  document.getElementById("navMenu").classList.toggle("open");
}

  if(toggle && links){
    toggle.addEventListener("click", function(){
      links.classList.toggle("open");
    });

    // close when clicking outside
    document.addEventListener("click", function(e){
      if(!links.contains(e.target) && !toggle.contains(e.target)){
        links.classList.remove("open");
      }
    });
  }
  <script src="{{ url_for('static', filename='js/script.js') }}"></script>
});
