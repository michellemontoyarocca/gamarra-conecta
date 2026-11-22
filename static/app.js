// Mejoras de interfaz sin dependencias: menú móvil y contador de caracteres.
(function () {
  var toggle = document.querySelector('.nav-toggle');
  var links = document.getElementById('site-nav');
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      var open = links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }
  document.querySelectorAll('textarea[data-counter]').forEach(function (area) {
    var out = document.getElementById(area.getAttribute('data-counter'));
    if (!out) { return; }
    var max = area.getAttribute('maxlength');
    var update = function () { out.textContent = area.value.length + ' de ' + max + ' caracteres'; };
    area.addEventListener('input', update);
    update();
  });
})();
