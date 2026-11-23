// Adds a button that hides or shows the left navigation pane. The choice is remembered in this browser.
(function () {
  var KEY = "bdai-nav-hidden";
  function read() { try { return localStorage.getItem(KEY) === "1"; } catch (e) { return false; } }
  function write(v) { try { localStorage.setItem(KEY, v ? "1" : "0"); } catch (e) { /* private mode: still works for this page */ } }

  function apply(hidden, button) {
    document.body.classList.toggle("bdai-nav-hidden", hidden);
    button.setAttribute("aria-pressed", hidden ? "true" : "false");
    button.title = hidden ? "Show the navigation pane" : "Hide the navigation pane";
    button.setAttribute("aria-label", button.title);
    button.textContent = hidden ? "▶" : "◀";
  }

  function init() {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "bdai-nav-toggle";
    var hidden = read();
    apply(hidden, button);
    button.addEventListener("click", function () {
      hidden = !hidden;
      write(hidden);
      apply(hidden, button);
    });
    document.body.appendChild(button);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
