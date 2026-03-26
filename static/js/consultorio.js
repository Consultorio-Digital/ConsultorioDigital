document.addEventListener('DOMContentLoaded', function() {
    const regionSelect = document.getElementById('region');
    const comunaSelect = document.getElementById('comuna');
    const consultorioSelect = document.getElementById('consultorio');

    regionSelect.addEventListener('change', function() {
        const regionId = parseInt(this.value);
        if (regionId) {
            fetch(`consultorio/obtener_comunas/${regionId}/`)
                .then(response => response.json())
                .then(data => {
                    comunaSelect.innerHTML = '<option value="">Seleccione una comuna</option>';
                    data.forEach(comuna => {
                        comunaSelect.innerHTML += `<option value="${comuna.c_com}">${comuna.nom_com}</option>`;
                    });
                    comunaSelect.disabled = false;
                });
        } else {
            comunaSelect.innerHTML = '<option value="">Seleccione una comuna</option>';
            comunaSelect.disabled = true;
            consultorioSelect.innerHTML = '<option value="">Seleccione un consultorio</option>';
            consultorioSelect.disabled = true;
        }
    });

    comunaSelect.addEventListener('change', function() {
        const comunaId = this.value;
        if (comunaId) {
            fetch(`consultorio/obtener_consultorios/${comunaId}/`)
                .then(response => response.json())
                .then(data => {
                    consultorioSelect.innerHTML = '<option value="">Seleccione un consultorio</option>';
                    data.forEach(consultorio => {
                        consultorioSelect.innerHTML += `<option value="${consultorio.objectid}">${consultorio.nombre}</option>`;
                    });
                    consultorioSelect.disabled = false;
                });
        } else {
            consultorioSelect.innerHTML = '<option value="">Seleccione un consultorio</option>';
            consultorioSelect.disabled = true;
        }
    });
});
