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
  let consumosPorFecha = {}; // Almacenar consumos por fecha

  const ymd = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
  const cap = s => s.charAt(0).toUpperCase() + s.slice(1);

  // Obtener el ID del proyecto desde la variable global o la URL
  function getProjectId() {
    if (window.PROJECT_ID) return window.PROJECT_ID;
    const pathParts = window.location.pathname.split('/');
    const projectIndex = pathParts.indexOf('projects') + 1;
    return pathParts[projectIndex];
  }

  // Cargar consumos del mes actual desde el servidor
  async function cargarConsumos() {
    const projectId = getProjectId();
    if (!projectId) return;

    try {
      // Hacer fetch al endpoint para obtener consumos del mes
      const response = await fetch(`/projects/${projectId}/consumo/api/mes/?mes=${shown.getMonth() + 1}&anio=${shown.getFullYear()}`);

      if (response.ok) {
        const data = await response.json();
        consumosPorFecha = data.consumos_por_fecha || {};
      } else {
        console.warn('No se pudieron cargar los consumos del mes');
        consumosPorFecha = {};
      }
    } catch (error) {
      console.error('Error cargando consumos:', error);
      consumosPorFecha = {};
    }
  }

  // Mostrar modal con opciones del día
  function showDayOptionsModal(date, dateStr, consumos) {
    const projectId = getProjectId();
    const modal = new bootstrap.Modal(document.getElementById('dayOptionsModal'));

    // Formatear fecha para mostrar
    const dateFormatted = new Date(date).toLocaleDateString('es-ES', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });

    document.getElementById('modal-selected-date').textContent = dateFormatted;

    // Actualizar resumen del día
    const statusBadge = document.getElementById('day-status-badge');
    const countDiv = document.getElementById('day-consumos-count');

    if (consumos && consumos.length > 0) {
      statusBadge.className = 'badge bg-success';
      statusBadge.innerHTML = '<i class="fas fa-check-circle me-1"></i>Con registros';
      countDiv.innerHTML = `<i class="fas fa-list-ul me-1"></i>${consumos.length} consumo(s) registrado(s) este día`;

      // Deshabilitar botón "Ver consumos" si no hay consumos
      document.getElementById('btn-ver-consumos').classList.remove('disabled');
    } else {
      statusBadge.className = 'badge bg-secondary';
      statusBadge.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>Sin registros';
      countDiv.innerHTML = '<i class="fas fa-info-circle me-1"></i>No hay consumos registrados para este día';

      // Deshabilitar botón "Ver consumos" si no hay consumos
      document.getElementById('btn-ver-consumos').classList.add('disabled');
    }

    // Configurar enlaces de los botones
    document.getElementById('btn-agregar-consumo').href = `/projects/${projectId}/consumo/registrar/?fecha=${dateStr}`;
    document.getElementById('btn-ver-consumos').href = `/projects/${projectId}/consumo/listar/?fecha_desde=${dateStr}&fecha_hasta=${dateStr}`;

    // Cargar vista previa de consumos
    cargarVistaPrevia(dateStr, consumos);

    modal.show();
  }

  // Cargar vista previa de consumos
  async function cargarVistaPrevia(dateStr, consumos) {
    const previewContent = document.getElementById('consumos-preview-content');

    if (!consumos || consumos.length === 0) {
      previewContent.innerHTML = `
        <div class="text-center text-muted py-3">
          <i class="fas fa-inbox fa-2x mb-2"></i>
          <p class="mb-0">No hay consumos registrados</p>
        </div>
      `;
      return;
    }

    // Mostrar lista de consumos
    let html = '<div class="list-group list-group-flush">';
    consumos.forEach(consumo => {
      html += `
        <div class="list-group-item px-0 py-2">
          <div class="d-flex justify-content-between align-items-start">
            <div class="small">
              <strong class="text-primary">${consumo.material}</strong><br>
              <span class="badge bg-info text-dark">${consumo.cantidad} ${consumo.unidad}</span>
              <span class="text-muted ms-2">${consumo.actividad}</span>
            </div>
            <small class="text-muted">${consumo.responsable || 'N/A'}</small>
          </div>
        </div>
      `;
    });
    html += '</div>';

    previewContent.innerHTML = html;
  }

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
      const dateStr = ymd(date);

      const cell = document.createElement("div");
      cell.className = "day";

      // Contenedor para el número del día
      const dayNumber = document.createElement("span");
      dayNumber.className = "day-number";
      dayNumber.textContent = date.getDate();
      cell.appendChild(dayNumber);

      if (date.getMonth() !== shown.getMonth()) cell.classList.add("muted");
      if (dateStr === ymd(today)) cell.classList.add("today");
      if (selected && dateStr === ymd(selected)) cell.classList.add("selected");

      // Marcar días con consumos registrados (VERDE)
      const consumosEnFecha = consumosPorFecha[dateStr];
      if (consumosEnFecha && consumosEnFecha.length > 0) {
        cell.classList.add("has-registro");

        // Badge con número de consumos
        const badge = document.createElement("span");
        badge.className = "consumo-badge bg-success";
        badge.textContent = consumosEnFecha.length;
        cell.appendChild(badge);

        // Tooltip con información detallada
        const tooltipText = consumosEnFecha.map(c =>
          `• ${c.material}: ${c.cantidad} ${c.unidad} (${c.actividad})`
        ).join('\n');
        cell.title = `✅ ${consumosEnFecha.length} consumo(s) registrado(s):\n${tooltipText}`;
      }
      // Marcar días pasados sin consumos (GRIS) - solo si es antes de hoy
      else if (date < today) {
        cell.classList.add("sin-registro");
        cell.title = "⚠️ No hay consumos registrados este día";
      }
      // Días futuros o día actual sin consumos
      else {
        cell.title = "📝 Clic para ver opciones";
      }

      // Al hacer clic: mostrar modal con opciones
      cell.addEventListener("click", () => {
        selected = new Date(date);
        hiddenInput.value = dateStr;
        showDayOptionsModal(date, dateStr, consumosEnFecha);
      });

      grid.appendChild(cell);
    }
  }

  prevBtn.addEventListener("click", async () => {
    shown.setMonth(shown.getMonth() - 1);
    await cargarConsumos();
    render();
  });

  nextBtn.addEventListener("click", async () => {
    shown.setMonth(shown.getMonth() + 1);
    await cargarConsumos();
    render();
  });

  // Inicializar
  cargarConsumos().then(() => render());
})();
