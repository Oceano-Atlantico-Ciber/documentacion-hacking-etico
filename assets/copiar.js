// Botón «Copiar» en cada bloque de órdenes (<div class="cmd">). Su aspecto está en estilo.css.
document.querySelectorAll('.cmd').forEach(function (box) {
  var btn = document.createElement('button');
  btn.type = 'button';
  btn.textContent = 'Copiar';
  btn.addEventListener('click', function () {
    var code = box.querySelector('code');
    var done = function () { btn.textContent = 'Copiado'; setTimeout(function () { btn.textContent = 'Copiar'; }, 1500); };
    var fallback = function () {
      var r = document.createRange(); r.selectNodeContents(code);
      var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
      btn.textContent = 'Pulsa Ctrl/Cmd+C';
    };
    try { navigator.clipboard.writeText(code.textContent).then(done, fallback); } catch (e) { fallback(); }
  });
  box.appendChild(btn);
});
