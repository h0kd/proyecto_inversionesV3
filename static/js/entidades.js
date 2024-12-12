function cargarEntidadesCorredor() {
	fetch("/entidades_corredor")
		.then((response) => {
			if (!response.ok) {
				throw new Error("Error al obtener corredoras.");
			}
			return response.json();
		})
		.then((data) => {
			console.log("Corredoras recibidas:", data);

			const corredorSelect = document.getElementById("corredora");
			const selectedValue = corredorSelect.value; // Guardar el valor seleccionado

			corredorSelect.innerHTML =
				'<option value="" disabled selected>Seleccione una corredora</option>';

			data.forEach((corredor) => {
				const option = document.createElement("option");
				option.value = corredor.id;
				option.textContent = corredor.nombre;

				// Si el valor coincide con el seleccionado previamente, márcalo
				if (corredor.id == selectedValue) {
					option.selected = true;
				}

				corredorSelect.appendChild(option);
			});
		})
		.catch((error) => console.error("Error al cargar corredoras:", error));
}

function cargarEntidadesEmpresa() {
	fetch("/entidades_empresa")
		.then((response) => {
			if (!response.ok) {
				throw new Error("Error al obtener empresas.");
			}
			return response.json();
		})
		.then((data) => {
			console.log("Empresas recibidas:", data);

			const empresaSelect = document.getElementById("empresa_emisora");
			const selectedValue = empresaSelect.value; // Guardar el valor seleccionado

			empresaSelect.innerHTML =
				'<option value="" disabled selected>Seleccione una empresa emisora</option>';

			data.forEach((empresa) => {
				const option = document.createElement("option");
				option.value = empresa.id;
				option.textContent = empresa.nombre;

				// Si el valor coincide con el seleccionado previamente, márcalo
				if (empresa.id == selectedValue) {
					option.selected = true;
				}

				empresaSelect.appendChild(option);
			});
		})
		.catch((error) =>
			console.error("Error al cargar empresas emisoras:", error)
		);
}
