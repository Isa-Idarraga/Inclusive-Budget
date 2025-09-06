(function () {
  const cal = document.getElementById("calendar");
  if (!cal) return;

  const titleEl = cal.querySelector("[data-cal-title]");
  const grid = cal.querySelector(".cal-grid");
  const prevBtn = cal.querySelector("[data-cal-prev]");
  const nextBtn = cal.querySelector("[data-cal-next]");
  const hiddenInput = document.getElementById("selected_date");

  const DOW = ["LUN","MAR","MIÉ","JUE","VIE","SÁB","DOM"];
  const monthNames = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"];

  let today = new Date(); today.setHours(0,0,0,0);
  let shown = new Date(today); shown.setDate(1);
  let selected = null;

  const ymd = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
  const cap = s => s.charAt(0).toUpperCase() + s.slice(1);

  function render() {
    titleEl.textContent = `${cap(monthNames[shown.getMonth()])} ${shown.getFullYear()}`;
    grid.innerHTML = "";

    // cabecera días
    for (const d of DOW) {
      const e = document.createElement("div");
      e.className = "dow"; e.textContent = d; grid.appendChild(e);
    }

    // arranque en lunes
    const firstDayIndex = (shown.getDay() + 6) % 7; // 0=Mon
    const start = new Date(shown); start.setDate(1 - firstDayIndex);

    for (let i = 0; i < 42; i++) {
      const date = new Date(start); date.setDate(start.getDate() + i);

      const cell = document.createElement("div");
      cell.className = "day";
      cell.textContent = date.getDate();

      if (date.getMonth() !== shown.getMonth()) cell.classList.add("muted");
      if (ymd(date) === ymd(today)) cell.classList.add("today");
      if (selected && ymd(date) === ymd(selected)) cell.classList.add("selected");

      cell.addEventListener("click", () => {
        selected = new Date(date);
        hiddenInput.value = ymd(selected);
        render();
        // aquí podrías disparar un fetch a tu backend
      });

      grid.appendChild(cell);
    }
  }

  prevBtn.addEventListener("click", () => { shown.setMonth(shown.getMonth() - 1); render(); });
  nextBtn.addEventListener("click", () => { shown.setMonth(shown.getMonth() + 1); render(); });

  render();
})();
