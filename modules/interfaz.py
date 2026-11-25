import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import calendar
from datetime import datetime, date

from database.conexion import inicializar_base_datos

from modules.trabajadores import (
    registrar_trabajador,
    listar_trabajadores
)

from modules.planillas import (
    crear_tabla_planillas,
    calcular_planilla,
    guardar_planilla,
    listar_planillas,
    obtener_planilla_por_id
)

from reports.boleta_pdf import generar_boleta_pdf
from modules.liquidacion import (
    crear_tabla_liquidaciones,
    listar_trabajadores_liquidacion,
    calcular_liquidacion,
    guardar_liquidacion,
    listar_liquidaciones,
)
from reports.liquidacion_pdf import generar_liquidacion_pdf
from reports.certificados_pdf import generar_certificado_trabajo, generar_constancia_quinta

from modules.asistencia import (
    crear_tabla_asistencia,
    registrar_asistencia,
    actualizar_asistencia,
    listar_asistencias,
    obtener_asistencia_por_id,
    resumen_mensual_asistencia
)


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class SistemaPlanillas:

    def __init__(self, root):
        self.root = root
        self.root.title("SISTEMA DE PLANILLAS - PERÚ")
        self.root.geometry("1200x750")
        self.root.minsize(950, 650)

        # Inicializar y actualizar la estructura de la base de datos
        inicializar_base_datos()
        crear_tabla_planillas()
        crear_tabla_asistencia()
        crear_tabla_liquidaciones()

        self.crear_interfaz()

    # =====================================================
    # INTERFAZ PRINCIPAL
    # =====================================================

    def crear_interfaz(self):

        self.sidebar = ctk.CTkFrame(
            self.root,
            width=230,
            corner_radius=0,
            fg_color="#172554"
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="SISTEMA\nDE PLANILLAS",
            font=("Arial", 24, "bold"),
            text_color="white"
        ).pack(pady=(40, 10))

        ctk.CTkLabel(
            self.sidebar,
            text="GESTIÓN EMPRESARIAL",
            font=("Arial", 11),
            text_color="#BFDBFE"
        ).pack(pady=(0, 40))

        botones = [
            ("⌂  Inicio", self.inicio),
            ("♙  Trabajadores", self.ventana_trabajadores),
            ("▤  Planillas", self.ventana_planillas),
            ("◷  Asistencia", self.ventana_asistencia),
            ("▦  Historial de asistencia", self.ventana_historial_asistencia),
            ("▤  Liquidación de beneficios", self.ventana_liquidaciones),
            ("▧  Certificados", self.ventana_certificados)
        ]

        for nombre, funcion in botones:
            ctk.CTkButton(
                self.sidebar,
                text=nombre,
                height=45,
                corner_radius=8,
                anchor="w",
                fg_color="#1E3A8A",
                hover_color="#2563EB",
                command=funcion
            ).pack(fill="x", padx=16, pady=7)

        self.contenido = ctk.CTkFrame(
            self.root,
            corner_radius=0,
            fg_color="#F3F6FB"
        )
        self.contenido.pack(
            side="right",
            fill="both",
            expand=True
        )

        self.inicio()

    def limpiar_contenido(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()

    # =====================================================
    # INICIO
    # =====================================================

    def inicio(self):

        self.limpiar_contenido()

        ctk.CTkLabel(
            self.contenido,
            text="Panel de administración",
            font=("Arial", 29, "bold"),
            text_color="#172554"
        ).pack(anchor="w", padx=35, pady=(35, 10))

        ctk.CTkLabel(
            self.contenido,
            text="Bienvenido al Sistema de Planillas del Perú",
            font=("Arial", 15),
            text_color="#64748B"
        ).pack(anchor="w", padx=35, pady=5)

        total = len(listar_trabajadores())

        tarjeta = ctk.CTkFrame(
            self.contenido,
            width=270,
            height=145,
            corner_radius=15,
            fg_color="white"
        )
        tarjeta.pack(anchor="w", padx=35, pady=35)
        tarjeta.pack_propagate(False)

        ctk.CTkLabel(
            tarjeta,
            text="TOTAL DE TRABAJADORES",
            font=("Arial", 13, "bold"),
            text_color="#475569"
        ).pack(pady=(25, 8))

        ctk.CTkLabel(
            tarjeta,
            text=str(total),
            font=("Arial", 36, "bold"),
            text_color="#1D4ED8"
        ).pack()

    # =====================================================
    # TRABAJADORES
    # =====================================================

    def ventana_trabajadores(self):

        self.limpiar_contenido()

        ctk.CTkLabel(
            self.contenido,
            text="Administración de trabajadores",
            font=("Arial", 26, "bold"),
            text_color="#172554"
        ).pack(anchor="w", padx=25, pady=25)

        ctk.CTkButton(
            self.contenido,
            text="+ REGISTRAR TRABAJADOR",
            command=self.formulario_trabajador,
            height=42,
            fg_color="#1D4ED8",
            hover_color="#1E40AF"
        ).pack(anchor="w", padx=25, pady=5)

        marco = ctk.CTkFrame(self.contenido)
        marco.pack(fill="both", expand=True, padx=25, pady=20)

        columnas = (
            "dni", "nombres", "apellidos",
            "cargo", "sueldo", "estado"
        )

        self.tabla = ttk.Treeview(
            marco,
            columns=columnas,
            show="headings"
        )

        titulos = {
            "dni": "DNI",
            "nombres": "NOMBRES",
            "apellidos": "APELLIDOS",
            "cargo": "CARGO",
            "sueldo": "SUELDO BÁSICO",
            "estado": "ESTADO"
        }

        for columna, titulo in titulos.items():
            self.tabla.heading(columna, text=titulo)
            self.tabla.column(
                columna,
                width=130,
                anchor="center"
            )

        scroll = ttk.Scrollbar(
            marco,
            orient="vertical",
            command=self.tabla.yview
        )

        self.tabla.configure(yscrollcommand=scroll.set)

        self.tabla.pack(
            side="left",
            fill="both",
            expand=True
        )

        scroll.pack(side="right", fill="y")

        self.actualizar_tabla()

    def actualizar_tabla(self):

        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        for trabajador in listar_trabajadores():

            self.tabla.insert(
                "",
                "end",
                values=(
                    trabajador[1],
                    trabajador[2],
                    trabajador[3],
                    trabajador[5],
                    f"S/ {float(trabajador[6]):,.2f}",
                    trabajador[7]
                )
            )

    # =====================================================
    # FORMULARIO COMPLETO DE TRABAJADORES
    # =====================================================

    def formulario_trabajador(self):

        ventana = ctk.CTkToplevel(self.root)
        ventana.title("Registro de trabajador")
        ventana.geometry("720x820")
        ventana.minsize(600, 650)
        ventana.grab_set()

        ctk.CTkLabel(
            ventana,
            text="REGISTRO DE TRABAJADOR",
            font=("Arial", 23, "bold"),
            text_color="#172554"
        ).pack(pady=(18, 5))

        ctk.CTkLabel(
            ventana,
            text="Completa la información personal y laboral",
            font=("Arial", 12),
            text_color="#64748B"
        ).pack(pady=(0, 12))

        contenedor = ctk.CTkScrollableFrame(
            ventana,
            corner_radius=10
        )
        contenedor.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        entradas = {}
        combos = {}

        def titulo_seccion(texto):

            ctk.CTkLabel(
                contenedor,
                text=texto,
                font=("Arial", 16, "bold"),
                text_color="#1D4ED8"
            ).pack(anchor="w", padx=15, pady=(18, 8))

        def campo(texto, clave, placeholder=""):

            ctk.CTkLabel(
                contenedor,
                text=texto,
                font=("Arial", 12, "bold")
            ).pack(anchor="w", padx=18, pady=(7, 2))

            entrada = ctk.CTkEntry(
                contenedor,
                height=36,
                placeholder_text=placeholder
            )
            entrada.pack(fill="x", padx=18, pady=(0, 4))

            entradas[clave] = entrada

        def selector(texto, clave, opciones, valor_inicial=""):

            ctk.CTkLabel(
                contenedor,
                text=texto,
                font=("Arial", 12, "bold")
            ).pack(anchor="w", padx=18, pady=(7, 2))

            combo = ctk.CTkComboBox(
                contenedor,
                values=opciones,
                height=36,
                state="readonly"
            )
            combo.pack(fill="x", padx=18, pady=(0, 4))

            if valor_inicial:
                combo.set(valor_inicial)

            combos[clave] = combo

        def abrir_calendario(entrada):
            """Abre un calendario emergente; la fecha también puede escribirse manualmente."""
            hoy = date.today()
            try:
                fecha_actual = datetime.strptime(
                    entrada.get().strip(), "%Y-%m-%d"
                ).date()
            except ValueError:
                fecha_actual = hoy

            estado = {"anio": fecha_actual.year, "mes": fecha_actual.month}
            calendario_ventana = ctk.CTkToplevel(ventana)
            calendario_ventana.title("Seleccionar fecha")
            calendario_ventana.geometry("320x350")
            calendario_ventana.resizable(False, False)
            calendario_ventana.transient(ventana)
            calendario_ventana.grab_set()

            encabezado = ctk.CTkFrame(calendario_ventana, fg_color="transparent")
            encabezado.pack(fill="x", padx=12, pady=(12, 6))

            etiqueta_mes = ctk.CTkLabel(
                encabezado, text="", font=("Arial", 15, "bold")
            )
            etiqueta_mes.pack(side="left", expand=True)

            dias_frame = ctk.CTkFrame(
                calendario_ventana, fg_color="transparent"
            )
            dias_frame.pack(fill="both", expand=True, padx=10, pady=5)

            def seleccionar(dia):
                seleccion = date(estado["anio"], estado["mes"], dia)
                entrada.delete(0, "end")
                entrada.insert(0, seleccion.strftime("%Y-%m-%d"))
                calendario_ventana.destroy()

            def dibujar_mes():
                for widget in dias_frame.winfo_children():
                    widget.destroy()

                nombres_meses = [
                    "ENERO", "FEBRERO", "MARZO", "ABRIL",
                    "MAYO", "JUNIO", "JULIO", "AGOSTO",
                    "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
                ]
                etiqueta_mes.configure(
                    text=f"{nombres_meses[estado['mes'] - 1]} {estado['anio']}"
                )

                for columna, nombre_dia in enumerate(
                    ["LU", "MA", "MI", "JU", "VI", "SA", "DO"]
                ):
                    ctk.CTkLabel(
                        dias_frame, text=nombre_dia,
                        font=("Arial", 11, "bold")
                    ).grid(row=0, column=columna, padx=2, pady=5)

                semanas = calendar.monthcalendar(
                    estado["anio"], estado["mes"]
                )
                for fila, semana in enumerate(semanas, start=1):
                    for columna, numero in enumerate(semana):
                        if numero:
                            ctk.CTkButton(
                                dias_frame,
                                text=str(numero),
                                width=34,
                                height=32,
                                command=lambda d=numero: seleccionar(d)
                            ).grid(
                                row=fila, column=columna,
                                padx=2, pady=2
                            )

            def cambiar_mes(desplazamiento):
                mes = estado["mes"] + desplazamiento
                anio = estado["anio"]
                if mes < 1:
                    mes = 12
                    anio -= 1
                elif mes > 12:
                    mes = 1
                    anio += 1
                estado["mes"] = mes
                estado["anio"] = anio
                dibujar_mes()

            ctk.CTkButton(
                encabezado, text="‹", width=35,
                command=lambda: cambiar_mes(-1)
            ).pack(side="left")
            # El botón siguiente se coloca después del título para mantener
            # la navegación del calendario en una sola fila.
            ctk.CTkButton(
                encabezado, text="›", width=35,
                command=lambda: cambiar_mes(1)
            ).pack(side="right")

            dibujar_mes()

        def campo_fecha(texto, clave, placeholder="AAAA-MM-DD"):
            ctk.CTkLabel(
                contenedor,
                text=texto,
                font=("Arial", 12, "bold")
            ).pack(anchor="w", padx=18, pady=(7, 2))

            fila_fecha = ctk.CTkFrame(
                contenedor, fg_color="transparent"
            )
            fila_fecha.pack(fill="x", padx=18, pady=(0, 4))

            entrada = ctk.CTkEntry(
                fila_fecha,
                height=36,
                placeholder_text=placeholder
            )
            entrada.pack(side="left", fill="x", expand=True)

            ctk.CTkButton(
                fila_fecha,
                text="▦",
                width=45,
                height=36,
                command=lambda e=entrada: abrir_calendario(e),
                fg_color="#1D4ED8",
                hover_color="#1E40AF"
            ).pack(side="left", padx=(6, 0))

            entradas[clave] = entrada

        # -------------------------------------------------
        # DATOS PERSONALES
        # -------------------------------------------------

        titulo_seccion("1. DATOS PERSONALES")

        campo("DNI (8 dígitos)", "dni")
        campo("Nombres completos", "nombres")
        campo("Apellidos completos", "apellidos")

        campo_fecha(
            "Fecha de nacimiento (AAAA-MM-DD)",
            "fecha_nacimiento",
            "Ejemplo: 2001-04-04"
        )

        selector(
            "Género (obligatorio)",
            "genero",
            ["FEMENINO", "MASCULINO"]
        )

        selector(
            "Nacionalidad",
            "nacionalidad",
            ["PERUANA", "EXTRANJERA"],
            "PERUANA"
        )

        campo(
            "Domicilio",
            "domicilio",
            "Dirección actual del trabajador"
        )

        selector(
            "Condición domiciliaria",
            "condicion",
            ["Domiciliado", "No domiciliado"],
            "Domiciliado"
        )

        # -------------------------------------------------
        # DATOS LABORALES
        # -------------------------------------------------

        titulo_seccion("2. DATOS LABORALES")

        campo_fecha(
            "Fecha de ingreso laboral (AAAA-MM-DD)",
            "fecha_ingreso_laboral",
            "Ejemplo: 2025-08-01"
        )

        campo_fecha(
            "Fecha de contrato (AAAA-MM-DD)",
            "fecha_contrato",
            "Dejar vacío si no corresponde"
        )

        selector(
            "Cargo o puesto de trabajo",
            "cargo",
            [
                "ADMINISTRADOR",
                "ASISTENTE ADMINISTRATIVO",
                "CONTADOR",
                "AUXILIAR CONTABLE",
                "VENDEDOR",
                "OPERARIO"
            ]
        )

        campo(
            "Sueldo básico mensual (S/)",
            "sueldo",
            "Ejemplo: 2500.00"
        )

        areas = [
            "Administración",
            "Contabilidad",
            "Recursos Humanos",
            "Ventas",
            "Producción",
            "Logística",
            "Operaciones",
            "Otro"
        ]

        subareas_por_area = {
            "Administración": [
                "Administración general", "Asistencia administrativa",
                "Tesorería", "Facturación y cobranzas"
            ],
            "Contabilidad": [
                "Contabilidad general", "Tributación",
                "Costos", "Planillas", "Auditoría"
            ],
            "Recursos Humanos": [
                "Selección y contratación", "Capacitación",
                "Bienestar laboral", "Administración de personal"
            ],
            "Ventas": [
                "Ventas presenciales", "Ventas corporativas",
                "Atención al cliente", "Postventa"
            ],
            "Producción": [
                "Producción", "Control de calidad",
                "Mantenimiento", "Empaque"
            ],
            "Logística": [
                "Compras", "Almacén",
                "Distribución", "Control de inventarios"
            ],
            "Operaciones": [
                "Operaciones generales", "Supervisión",
                "Servicios", "Soporte operativo"
            ],
            "Otro": ["Otra subárea"]
        }

        selector(
            "Área",
            "area",
            areas,
            "Administración"
        )

        selector(
            "Subárea",
            "sub_area",
            subareas_por_area["Administración"],
            "Administración general"
        )

        def actualizar_subareas(nueva_area):
            opciones_subarea = subareas_por_area.get(
                nueva_area, ["Otra subárea"]
            )
            combos["sub_area"].configure(values=opciones_subarea)
            combos["sub_area"].set(opciones_subarea[0])

        combos["area"].configure(command=actualizar_subareas)

        campo("Centro de costo", "centro_costo")

        selector(
            "Tipo de trabajador",
            "tipo_trabajador",
            ["Empleado", "Obrero"],
            "Empleado"
        )

        # -------------------------------------------------
        # DATOS CONTRACTUALES
        # -------------------------------------------------

        titulo_seccion("3. INFORMACIÓN CONTRACTUAL")

        selector(
            "Tipo de contrato",
            "tipo_contrato",
            ["Contrato temporal por inicio o incremento de actividad"],
            "Contrato temporal por inicio o incremento de actividad"
        )

        # -------------------------------------------------
        # INFORMACIÓN DE SALUD Y PENSIONES
        # -------------------------------------------------

        titulo_seccion("4. SEGURIDAD SOCIAL")

        selector(
            "Régimen de salud",
            "regimen_salud",
            ["EsSalud", "EPS", "SIS", "Otro"],
            "EsSalud"
        )

        campo(
            "CUSPP",
            "cuspp",
            "Código de afiliación AFP, si corresponde"
        )

        # -------------------------------------------------
        # GUARDAR TRABAJADOR
        # -------------------------------------------------

        def guardar():

            try:
                # Los campos de texto y los desplegables se leen por separado.
                datos = {
                    clave: entrada.get().strip()
                    for clave, entrada in entradas.items()
                }

                valores_combo = {
                    clave: combo.get().strip()
                    for clave, combo in combos.items()
                }

                dni = datos["dni"]
                nombres = datos["nombres"]
                apellidos = datos["apellidos"]
                fecha_nacimiento = datos["fecha_nacimiento"]
                fecha_ingreso = datos["fecha_ingreso_laboral"]
                fecha_contrato = datos["fecha_contrato"]
                cargo = valores_combo["cargo"]

                # Validaciones personales y laborales.
                if not dni.isdigit() or len(dni) != 8:
                    raise ValueError(
                        "El DNI debe contener exactamente 8 dígitos."
                    )

                if not nombres or not apellidos:
                    raise ValueError(
                        "Debes completar los nombres y apellidos."
                    )

                if not fecha_nacimiento or not fecha_ingreso:
                    raise ValueError(
                        "Completa la fecha de nacimiento y la fecha de ingreso laboral."
                    )

                if not cargo:
                    raise ValueError(
                        "Debes seleccionar el cargo del trabajador."
                    )

                if valores_combo["genero"] not in ("FEMENINO", "MASCULINO"):
                    raise ValueError(
                        "Debes seleccionar FEMENINO o MASCULINO."
                    )

                if valores_combo["nacionalidad"] not in ("PERUANA", "EXTRANJERA"):
                    raise ValueError(
                        "Selecciona PERUANA o EXTRANJERA como nacionalidad."
                    )

                if not valores_combo["tipo_contrato"]:
                    raise ValueError("Debes seleccionar el tipo de contrato.")

                # Validar el formato y la existencia real de las fechas.
                try:
                    datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
                    datetime.strptime(fecha_ingreso, "%Y-%m-%d")
                    if fecha_contrato:
                        datetime.strptime(fecha_contrato, "%Y-%m-%d")
                except ValueError:
                    raise ValueError(
                        "Verifica las fechas. Usa el formato AAAA-MM-DD "
                        "y selecciona días válidos en el calendario."
                    )

                try:
                    sueldo = float(datos["sueldo"])
                except (ValueError, TypeError):
                    raise ValueError(
                        "Ingresa un sueldo básico válido. Ejemplo: 2500.00"
                    )

                if sueldo <= 0:
                    raise ValueError(
                        "El sueldo básico debe ser mayor que cero."
                    )

                # Registrar conservando la firma posicional existente del módulo.
                correcto, mensaje = registrar_trabajador(
                    dni,
                    nombres,
                    apellidos,
                    fecha_nacimiento,
                    cargo,
                    sueldo,
                    fecha_nacimiento=fecha_nacimiento,
                    fecha_ingreso_laboral=fecha_ingreso,
                    fecha_contrato=fecha_contrato or None,
                    genero=valores_combo["genero"],
                    nacionalidad=valores_combo["nacionalidad"],
                    domicilio=datos["domicilio"],
                    condicion=valores_combo["condicion"],
                    area=valores_combo["area"],
                    sub_area=valores_combo["sub_area"],
                    tipo_contrato=valores_combo["tipo_contrato"],
                    centro_costo=datos["centro_costo"],
                    tipo_trabajador=valores_combo["tipo_trabajador"],
                    regimen_salud=valores_combo["regimen_salud"],
                    cuspp=datos["cuspp"]
                )

                if correcto:
                    messagebox.showinfo(
                        "Registro exitoso",
                        mensaje
                    )
                    ventana.destroy()
                    self.actualizar_tabla()
                else:
                    messagebox.showerror(
                        "No se pudo registrar",
                        mensaje
                    )

            except ValueError as error:
                messagebox.showerror(
                    "Validación",
                    str(error)
                )

            except Exception as error:
                messagebox.showerror(
                    "Error",
                    f"Ocurrió un problema al registrar:\n{error}"
                )

        ctk.CTkButton(
            ventana,
            text="GUARDAR TRABAJADOR",
            command=guardar,
            height=46,
            font=("Arial", 14, "bold"),
            fg_color="#167A52",
            hover_color="#105C3D"
        ).pack(fill="x", padx=25, pady=18)

    # =====================================================
    # PLANILLAS
    # =====================================================

    def ventana_planillas(self):

        self.limpiar_contenido()

        ctk.CTkLabel(
            self.contenido,
            text="Administración de planillas",
            font=("Arial", 26, "bold"),
            text_color="#172554"
        ).pack(anchor="w", padx=25, pady=(25, 10))

        ctk.CTkButton(
            self.contenido,
            text="+ GENERAR NUEVA PLANILLA",
            height=42,
            command=self.formulario_planilla
        ).pack(anchor="w", padx=25, pady=8)

        ctk.CTkButton(
            self.contenido,
            text="GENERAR BOLETA DE PAGO PDF",
            height=42,
            fg_color="#167A52",
            hover_color="#105C3D",
            command=self.generar_boleta
        ).pack(anchor="w", padx=25, pady=5)

        ctk.CTkLabel(
            self.contenido,
            text="HISTORIAL DE PLANILLAS",
            font=("Arial", 15, "bold"),
            text_color="#172554"
        ).pack(anchor="w", padx=25, pady=(15, 5))

        marco = ctk.CTkFrame(self.contenido)
        marco.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=15
        )

        columnas = (
            "dni", "nombres", "apellidos",
            "anio", "mes", "ingresos",
            "pension", "essalud", "neto"
        )

        self.tabla_planillas = ttk.Treeview(
            marco,
            columns=columnas,
            show="headings"
        )

        titulos = {
            "dni": "DNI",
            "nombres": "NOMBRES",
            "apellidos": "APELLIDOS",
            "anio": "AÑO",
            "mes": "MES",
            "ingresos": "INGRESOS",
            "pension": "PENSIÓN",
            "essalud": "ESSALUD",
            "neto": "NETO A PAGAR"
        }

        for columna, titulo in titulos.items():

            self.tabla_planillas.heading(
                columna,
                text=titulo
            )

            self.tabla_planillas.column(
                columna,
                width=110,
                anchor="center"
            )

        scroll = ttk.Scrollbar(
            marco,
            orient="vertical",
            command=self.tabla_planillas.yview
        )

        self.tabla_planillas.configure(
            yscrollcommand=scroll.set
        )

        self.tabla_planillas.pack(
            side="left",
            fill="both",
            expand=True
        )

        scroll.pack(side="right", fill="y")

        self.actualizar_tabla_planillas()

    def actualizar_tabla_planillas(self):

        for fila in self.tabla_planillas.get_children():
            self.tabla_planillas.delete(fila)

        registros = listar_planillas()

        for p in registros:

            self.tabla_planillas.insert(
                "",
                "end",
                iid=str(p[0]),
                values=(
                    p[1],
                    p[2],
                    p[3],
                    p[4],
                    p[5],
                    f"S/ {p[6]:,.2f}",
                    f"S/ {p[7]:,.2f}",
                    f"S/ {p[8]:,.2f}",
                    f"S/ {p[9]:,.2f}"
                )
            )

    # =====================================================
    # GENERAR BOLETA PDF
    # =====================================================

    def generar_boleta(self):

        seleccion = self.tabla_planillas.selection()

        if not seleccion:

            messagebox.showwarning(
                "Seleccionar planilla",
                "Primero selecciona una planilla del historial."
            )
            return

        try:

            planilla_id = int(seleccion[0])

            datos = obtener_planilla_por_id(planilla_id)

            if datos is None:

                messagebox.showerror(
                    "Error",
                    "No se encontraron los datos de esa planilla."
                )
                return

            nombre = (
                f"Boleta_{datos['dni']}_"
                f"{datos['anio']}_{datos['mes']:02d}.pdf"
            )

            ruta = filedialog.asksaveasfilename(
                title="Guardar boleta de pago",
                defaultextension=".pdf",
                initialfile=nombre,
                filetypes=[("Documento PDF", "*.pdf")]
            )

            if not ruta:
                return

            generar_boleta_pdf(datos, ruta)

            messagebox.showinfo(
                "Boleta generada",
                "La boleta de pago se generó correctamente.\n\n"
                f"Archivo:\n{ruta}"
            )

        except Exception as error:

            messagebox.showerror(
                "Error al generar boleta",
                f"No se pudo generar el PDF:\n{error}"
            )

    # =====================================================
    # FORMULARIO DE GENERACIÓN DE PLANILLA
    # =====================================================

    def formulario_planilla(self):

        trabajadores = [
            t for t in listar_trabajadores()
            if len(t) > 7 and t[7] == "ACTIVO"
        ]

        if not trabajadores:
            messagebox.showwarning(
                "Aviso",
                "No existen trabajadores activos registrados."
            )
            return

        ventana = ctk.CTkToplevel(self.root)
        ventana.title("Generar planilla")
        ventana.geometry("680x850")
        ventana.minsize(600, 650)
        ventana.grab_set()

        ctk.CTkLabel(
            ventana,
            text="GENERAR PLANILLA MENSUAL",
            font=("Arial", 22, "bold"),
            text_color="#172554"
        ).pack(pady=(16, 8))

        contenedor = ctk.CTkScrollableFrame(
            ventana,
            corner_radius=12,
            fg_color="#F3F4F6"
        )
        contenedor.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        ancho = 570

        def etiqueta(texto):
            ctk.CTkLabel(
                contenedor,
                text=texto,
                font=("Arial", 12, "bold"),
                text_color="#1F2937"
            ).pack(anchor="w", padx=18, pady=(10, 2))

        def combo(valores, valor_inicial=None):
            control = ctk.CTkComboBox(
                contenedor,
                values=valores,
                width=ancho,
                state="readonly"
            )
            control.pack(padx=18, pady=(2, 4), anchor="w")
            if valor_inicial is not None:
                control.set(valor_inicial)
            return control

        def entrada(valor="", placeholder=None):
            control = ctk.CTkEntry(
                contenedor,
                width=ancho,
                placeholder_text=placeholder or ""
            )
            control.pack(padx=18, pady=(2, 4), anchor="w")
            if valor != "":
                control.insert(0, str(valor))
            return control

        opciones = {
            f"{t[0]} - {t[1]} - {t[2]} {t[3]}": t
            for t in trabajadores
        }

        etiqueta("TRABAJADOR")
        trabajador_combo = combo(list(opciones.keys()), list(opciones.keys())[0])

        etiqueta("AÑO")
        anio_entry = entrada(str(datetime.now().year))

        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        mes_a_numero = {nombre: indice for indice, nombre in enumerate(meses, 1)}

        etiqueta("MES")
        mes_combo = combo(meses, meses[datetime.now().month - 1])

        # ---------------- RESUMEN DE ASISTENCIA ----------------
        # Solo consulta y muestra información; no modifica remuneraciones
        # ni aplica descuentos automáticos por faltas.

        ctk.CTkLabel(
            contenedor,
            text="CONTROL DE ASISTENCIA DEL MES",
            font=("Arial", 14, "bold"),
            text_color="#1D4ED8"
        ).pack(anchor="w", padx=18, pady=(18, 3))

        asistencia_info = ctk.CTkLabel(
            contenedor,
            text=(
                "Selecciona el trabajador y el periodo, y pulsa "
                "'CONSULTAR ASISTENCIA DEL MES'."
            ),
            text_color="#475569",
            justify="left",
            wraplength=ancho
        )
        asistencia_info.pack(anchor="w", padx=18, pady=(3, 5))

        def consultar_asistencia_planilla():
            try:
                trabajador_seleccionado = opciones.get(trabajador_combo.get())
                if trabajador_seleccionado is None:
                    raise ValueError("Selecciona un trabajador válido.")

                anio_consulta = int(anio_entry.get().strip())
                mes_consulta = mes_a_numero[mes_combo.get()]
                if anio_consulta < 2000 or anio_consulta > 2100:
                    raise ValueError("Ingresa un año válido.")

                resumen = resumen_mensual_asistencia(
                    anio_consulta,
                    mes_consulta,
                    int(trabajador_seleccionado[0])
                )

                if not resumen:
                    asistencia_info.configure(
                        text="No se encontraron datos de asistencia para este trabajador."
                    )
                    return

                registro = resumen[0]
                dias_registrados = int(registro[4] or 0)
                presentes = int(registro[5] or 0)
                faltas = int(registro[6] or 0)
                permisos = int(registro[7] or 0)
                descansos = int(registro[8] or 0)

                asistencia_info.configure(
                    text=(
                        f"RESUMEN: {mes_combo.get().upper()} {anio_consulta}\n"
                        f"Días registrados: {dias_registrados}\n"
                        f"Presentes: {presentes} | Faltas: {faltas}\n"
                        f"Permisos: {permisos} | Descansos: {descansos}\n\n"
                        "Las faltas se muestran para revisión. "
                        "No se descontarán automáticamente de la remuneración."
                    )
                )

            except (ValueError, TypeError, KeyError) as error:
                messagebox.showerror(
                    "Consulta de asistencia",
                    str(error),
                    parent=ventana
                )
            except Exception as error:
                messagebox.showerror(
                    "Consulta de asistencia",
                    f"No se pudo consultar la asistencia:\n{error}",
                    parent=ventana
                )

        ctk.CTkButton(
            contenedor,
            text="CONSULTAR ASISTENCIA DEL MES",
            command=consultar_asistencia_planilla,
            height=38,
            fg_color="#0F766E",
            hover_color="#115E59"
        ).pack(anchor="w", padx=18, pady=(3, 8))


        # ---------------- PENSIÓN ----------------
        ctk.CTkLabel(
            contenedor,
            text="SISTEMA DE PENSIONES",
            font=("Arial", 14, "bold"),
            text_color="#1D4ED8"
        ).pack(anchor="w", padx=18, pady=(18, 3))

        etiqueta("Sistema")
        pension_combo = combo(["ONP", "AFP"], "ONP")

        pension_info = ctk.CTkLabel(
            contenedor,
            text="ONP: descuento automático del 13%.",
            text_color="#475569",
            justify="left"
        )
        pension_info.pack(anchor="w", padx=18, pady=(0, 5))

        afp_frame = ctk.CTkFrame(contenedor, fg_color="#E5E7EB", corner_radius=8)
        afp_combo = ctk.CTkComboBox(
            afp_frame,
            values=["Habitat", "Integra", "Prima", "Profuturo"],
            width=250,
            state="readonly"
        )
        afp_combo.set("Habitat")

        comision_combo = ctk.CTkComboBox(
            afp_frame,
            values=["FLUJO", "SALDO"],
            width=250,
            state="readonly"
        )
        comision_combo.set("FLUJO")

        ctk.CTkLabel(afp_frame, text="Administradora AFP").pack(
            anchor="w", padx=12, pady=(10, 2)
        )
        afp_combo.pack(anchor="w", padx=12, pady=(0, 8))
        ctk.CTkLabel(afp_frame, text="Tipo de comisión").pack(
            anchor="w", padx=12, pady=(2, 2)
        )
        comision_combo.pack(anchor="w", padx=12, pady=(0, 10))

        def actualizar_pension(_valor=None):
            if pension_combo.get() == "AFP":
                pension_info.configure(
                    text="AFP: selecciona administradora y tipo de comisión. "
                         "El sistema calculará los componentes parametrizados."
                )
                if not afp_frame.winfo_manager():
                    afp_frame.pack(fill="x", padx=18, pady=6)
            else:
                pension_info.configure(
                    text="ONP: descuento automático del 13%."
                )
                if afp_frame.winfo_manager():
                    afp_frame.pack_forget()

        pension_combo.configure(command=actualizar_pension)

        # ---------------- ASIGNACIÓN FAMILIAR ----------------
        ctk.CTkLabel(
            contenedor,
            text="ASIGNACIÓN FAMILIAR",
            font=("Arial", 14, "bold"),
            text_color="#1D4ED8"
        ).pack(anchor="w", padx=18, pady=(18, 3))

        etiqueta("¿Al trabajador le corresponde asignación familiar?")
        asignacion_combo = combo(["NO", "SI"], "NO")
        asignacion_info = ctk.CTkLabel(
            contenedor,
            text="Si corresponde, el importe se calculará automáticamente según la RMV parametrizada.",
            text_color="#475569",
            justify="left",
            wraplength=ancho
        )
        asignacion_info.pack(anchor="w", padx=18, pady=(0, 5))

        # ---------------- HORAS EXTRAS ----------------
        ctk.CTkLabel(
            contenedor,
            text="HORAS EXTRAS",
            font=("Arial", 14, "bold"),
            text_color="#1D4ED8"
        ).pack(anchor="w", padx=18, pady=(18, 3))

        etiqueta("¿El trabajador realizó horas extras?")
        extras_combo = combo(["NO", "SI"], "NO")

        extras_frame = ctk.CTkFrame(contenedor, fg_color="#E5E7EB", corner_radius=8)

        ctk.CTkLabel(
            extras_frame,
            text="Registra las horas acumuladas y en cuántos días se realizaron.",
            text_color="#334155",
            wraplength=520,
            justify="left"
        ).pack(anchor="w", padx=12, pady=(10, 5))

        ctk.CTkLabel(
            extras_frame,
            text="Horas extras diurnas (cantidad total)"
        ).pack(anchor="w", padx=12, pady=(5, 2))
        horas_diurnas_entry = ctk.CTkEntry(extras_frame, width=250)
        horas_diurnas_entry.insert(0, "0")
        horas_diurnas_entry.pack(anchor="w", padx=12, pady=(0, 7))

        ctk.CTkLabel(
            extras_frame,
            text="Días en que realizó horas extras diurnas"
        ).pack(anchor="w", padx=12, pady=(2, 2))
        dias_diurnos_entry = ctk.CTkEntry(extras_frame, width=250)
        dias_diurnos_entry.insert(0, "1")
        dias_diurnos_entry.pack(anchor="w", padx=12, pady=(0, 8))

        ctk.CTkLabel(
            extras_frame,
            text="Horas extras nocturnas (cantidad total)"
        ).pack(anchor="w", padx=12, pady=(2, 2))
        horas_nocturnas_entry = ctk.CTkEntry(extras_frame, width=250)
        horas_nocturnas_entry.insert(0, "0")
        horas_nocturnas_entry.pack(anchor="w", padx=12, pady=(0, 7))

        ctk.CTkLabel(
            extras_frame,
            text="Días en que realizó horas extras nocturnas"
        ).pack(anchor="w", padx=12, pady=(2, 2))
        dias_nocturnos_entry = ctk.CTkEntry(extras_frame, width=250)
        dias_nocturnos_entry.insert(0, "1")
        dias_nocturnos_entry.pack(anchor="w", padx=12, pady=(0, 10))

        def actualizar_extras(_valor=None):
            if extras_combo.get() == "SI":
                if not extras_frame.winfo_manager():
                    extras_frame.pack(fill="x", padx=18, pady=6)
            else:
                if extras_frame.winfo_manager():
                    extras_frame.pack_forget()

        extras_combo.configure(command=actualizar_extras)

        # ---------------- OTROS INGRESOS ----------------
        ctk.CTkLabel(
            contenedor,
            text="OTROS INGRESOS",
            font=("Arial", 14, "bold"),
            text_color="#1D4ED8"
        ).pack(anchor="w", padx=18, pady=(18, 3))

        etiqueta("Otros ingresos (S/)")
        otros_entry = entrada("0")

        # ---------------- RESULTADO ----------------
        resultado_label = ctk.CTkLabel(
            contenedor,
            text="Calcula una vista previa para revisar los importes antes de guardar.",
            text_color="#334155",
            justify="left",
            wraplength=ancho
        )
        resultado_label.pack(anchor="w", padx=18, pady=(16, 8))

        def obtener_datos_calculo():
            trabajador = opciones.get(trabajador_combo.get())
            if trabajador is None:
                raise ValueError("Selecciona un trabajador válido.")

            trabajador_id = int(trabajador[0])
            anio = int(anio_entry.get().strip())
            mes = mes_a_numero[mes_combo.get()]

            if anio < 2000 or anio > 2100:
                raise ValueError("Ingresa un año válido.")

            tipo = pension_combo.get()
            afp_nombre = afp_combo.get().upper() if tipo == "AFP" else None
            afp_comision = comision_combo.get() if tipo == "AFP" else None

            tiene_asignacion = asignacion_combo.get() == "SI"

            horas_diurnas = 0.0
            horas_nocturnas = 0.0
            dias_diurnos = 1
            dias_nocturnos = 1

            if extras_combo.get() == "SI":
                horas_diurnas = float(horas_diurnas_entry.get() or 0)
                horas_nocturnas = float(horas_nocturnas_entry.get() or 0)
                dias_diurnos = int(dias_diurnos_entry.get() or 0)
                dias_nocturnos = int(dias_nocturnos_entry.get() or 0)

                if horas_diurnas < 0 or horas_nocturnas < 0:
                    raise ValueError("Las horas extras no pueden ser negativas.")
                if horas_diurnas > 0 and dias_diurnos < 1:
                    raise ValueError("Indica los días de horas extras diurnas.")
                if horas_nocturnas > 0 and dias_nocturnos < 1:
                    raise ValueError("Indica los días de horas extras nocturnas.")

            otros = float(otros_entry.get() or 0)
            if otros < 0:
                raise ValueError("Otros ingresos no puede ser negativo.")

            return {
                "trabajador_id": trabajador_id,
                "anio": anio,
                "mes": mes,
                "tipo": tipo,
                "tiene_asignacion": tiene_asignacion,
                "horas_diurnas": horas_diurnas,
                "horas_nocturnas": horas_nocturnas,
                "dias_diurnos": dias_diurnos,
                "dias_nocturnos": dias_nocturnos,
                "otros": otros,
                "afp_nombre": afp_nombre,
                "afp_comision": afp_comision,
            }

        def calcular_datos():
            datos_ui = obtener_datos_calculo()
            return calcular_planilla(
                datos_ui["trabajador_id"],
                datos_ui["anio"],
                datos_ui["mes"],
                datos_ui["tipo"],
                otros_ingresos=datos_ui["otros"],
                tiene_asignacion_familiar=datos_ui["tiene_asignacion"],
                horas_extras_diurnas=datos_ui["horas_diurnas"],
                horas_extras_nocturnas=datos_ui["horas_nocturnas"],
                dias_extras_diurnas=datos_ui["dias_diurnos"],
                dias_extras_nocturnas=datos_ui["dias_nocturnos"],
                afp_nombre=datos_ui["afp_nombre"],
                afp_tipo_comision=datos_ui["afp_comision"] or "FLUJO"
            )

        def previsualizar():
            try:
                datos = calcular_datos()
                resultado_label.configure(
                    text=(
                        f"RESUMEN DE CÁLCULO\n"
                        f"Sueldo básico: S/ {datos['sueldo_basico']:,.2f}\n"
                        f"Asignación familiar: S/ {datos['asignacion_familiar']:,.2f}\n"
                        f"Horas extras: S/ {datos['horas_extras']:,.2f}\n"
                        f"Otros ingresos: S/ {datos['otros_ingresos']:,.2f}\n"
                        f"TOTAL INGRESOS: S/ {datos['total_ingresos']:,.2f}\n"
                        f"Descuento {datos['tipo_pension']}: S/ {datos['descuento_pension']:,.2f}\n"
                        f"EsSalud (aporte empleador): S/ {datos['essalud']:,.2f}\n"
                        f"NETO A PAGAR: S/ {datos['neto_pagar']:,.2f}"
                    )
                )
            except Exception as error:
                messagebox.showerror("No se pudo calcular", str(error))

        def generar():
            try:
                datos = calcular_datos()

                correcto, mensaje = guardar_planilla(datos)

                if correcto:
                    messagebox.showinfo(
                        "Planilla generada",
                        f"Trabajador: {datos['nombres']} {datos['apellidos']}\n\n"
                        f"Total ingresos: S/ {datos['total_ingresos']:,.2f}\n"
                        f"Descuento pensión: S/ {datos['descuento_pension']:,.2f}\n"
                        f"EsSalud (aporte del empleador): S/ {datos['essalud']:,.2f}\n"
                        f"NETO A PAGAR: S/ {datos['neto_pagar']:,.2f}\n\n"
                        f"{mensaje}"
                    )
                    ventana.destroy()
                    self.actualizar_tabla_planillas()
                else:
                    messagebox.showerror("No se pudo guardar", mensaje)

            except ValueError as error:
                messagebox.showerror("Validación", str(error))
            except Exception as error:
                messagebox.showerror(
                    "Error",
                    f"Ocurrió un problema al generar la planilla:\n{error}"
                )

        botones = ctk.CTkFrame(contenedor, fg_color="transparent")
        botones.pack(fill="x", padx=18, pady=18)

        ctk.CTkButton(
            botones,
            text="CALCULAR VISTA PREVIA",
            command=previsualizar,
            height=42,
            fg_color="#1D4ED8",
            hover_color="#1E40AF"
        ).pack(fill="x", pady=(0, 8))

        ctk.CTkButton(
            botones,
            text="CALCULAR Y GUARDAR PLANILLA",
            command=generar,
            height=46,
            fg_color="#167A52",
            hover_color="#105C3D"
        ).pack(fill="x")

    # =====================================================
    # LIQUIDACIÓN DE BENEFICIOS SOCIALES
    # Módulo adicional: no modifica planillas ni trabajadores.
    # =====================================================

    def ventana_liquidaciones(self):
        self.limpiar_contenido()
        ctk.CTkLabel(
            self.contenido, text="Liquidación de beneficios sociales",
            font=("Arial", 26, "bold"), text_color="#172554"
        ).pack(anchor="w", padx=25, pady=(22, 5))
        ctk.CTkLabel(
            self.contenido,
            text="Calcula, guarda y genera el PDF de la liquidación al cese del trabajador.",
            font=("Arial", 13), text_color="#64748B"
        ).pack(anchor="w", padx=25, pady=(0, 12))
        ctk.CTkButton(
            self.contenido, text="+ NUEVA LIQUIDACIÓN", height=42,
            command=self.formulario_liquidacion, fg_color="#1D4ED8"
        ).pack(anchor="w", padx=25, pady=6)
        marco = ctk.CTkFrame(self.contenido, fg_color="white")
        marco.pack(fill="both", expand=True, padx=25, pady=12)
        columnas = ("id", "dni", "trabajador", "cese", "bruto", "descuentos", "neto")
        tabla = ttk.Treeview(marco, columns=columnas, show="headings")
        titulos = {"id":"ID", "dni":"DNI", "trabajador":"TRABAJADOR", "cese":"FECHA CESE",
                   "bruto":"TOTAL BRUTO", "descuentos":"DESCUENTOS", "neto":"NETO A PAGAR"}
        anchos = {"id":50, "dni":90, "trabajador":240, "cese":110, "bruto":125, "descuentos":120, "neto":130}
        for col in columnas:
            tabla.heading(col, text=titulos[col])
            tabla.column(col, width=anchos[col], anchor="center")
        tabla.pack(fill="both", expand=True, padx=8, pady=8)
        def cargar():
            for item in tabla.get_children(): tabla.delete(item)
            for f in listar_liquidaciones():
                tabla.insert("", "end", values=(f[0], f[1], f"{f[2]} {f[3]}", f[4],
                    f"S/ {float(f[5]):,.2f}", f"S/ {float(f[6]):,.2f}", f"S/ {float(f[7]):,.2f}"))
        ctk.CTkButton(self.contenido, text="ACTUALIZAR HISTORIAL", command=cargar,
                      fg_color="#64748B").pack(anchor="e", padx=25, pady=(0, 12))
        cargar()

    def formulario_liquidacion(self):
        trabajadores = listar_trabajadores_liquidacion()
        if not trabajadores:
            messagebox.showwarning("Liquidación", "Primero registra un trabajador.")
            return
        ventana = ctk.CTkToplevel(self.root)
        ventana.title("Nueva liquidación de beneficios sociales")
        ventana.geometry("760x850")
        ventana.minsize(650, 700)
        ventana.grab_set()
        ctk.CTkLabel(ventana, text="CÁLCULO DE LIQUIDACIÓN", font=("Arial", 22, "bold"),
                     text_color="#172554").pack(pady=(14, 5))
        ctk.CTkLabel(ventana, text="Completa los datos de cese y revisa los saldos pagados anteriormente.",
                     text_color="#64748B").pack(pady=(0, 8))
        form = ctk.CTkScrollableFrame(ventana, fg_color="#F3F6FB")
        form.pack(fill="both", expand=True, padx=14, pady=8)
        campos = {}
        def etiqueta(texto):
            ctk.CTkLabel(form, text=texto, font=("Arial", 12, "bold"), text_color="#1F2937").pack(anchor="w", padx=14, pady=(8, 2))
        def entry(clave, valor="0", placeholder=""):
            w = ctk.CTkEntry(form, height=34, placeholder_text=placeholder)
            w.pack(fill="x", padx=14, pady=(0, 3))
            if valor is not None: w.insert(0, str(valor))
            campos[clave] = w
            return w
        def combo(clave, opciones, valor):
            w = ctk.CTkComboBox(form, values=opciones, state="readonly", height=34)
            w.pack(fill="x", padx=14, pady=(0, 3)); w.set(valor); campos[clave] = w
            return w
        nombres = {f"{t['dni']} | {t['nombres']} {t['apellidos']}": t for t in trabajadores}
        etiqueta("TRABAJADOR")
        trabajador_combo = combo("trabajador", list(nombres), list(nombres)[0])
        seleccionado = nombres[trabajador_combo.get()]
        etiqueta("FECHA DE INGRESO LABORAL (AAAA-MM-DD)")
        ingreso_entry = entry("fecha_ingreso", seleccionado.get("fecha_ingreso_laboral") or seleccionado.get("fecha_ingreso") or "")
        etiqueta("FECHA DE CESE (AAAA-MM-DD)")
        entry("fecha_cese", date.today().isoformat())
        etiqueta("RÉGIMEN LABORAL APLICABLE")
        combo("regimen_laboral", ["GENERAL", "PEQUEÑA EMPRESA", "MICROEMPRESA"], "GENERAL")
        etiqueta("RÉGIMEN DE SALUD")
        combo("regimen_salud", ["ESSALUD", "EPS"], "ESSALUD")
        etiqueta("SUELDO BÁSICO MENSUAL (S/)")
        sueldo_entry = entry("sueldo", f"{float(seleccionado.get('sueldo_basico') or 0):.2f}")
        etiqueta("ASIGNACIÓN FAMILIAR MENSUAL (S/), SI CORRESPONDE")
        entry("asignacion_familiar", "0")
        etiqueta("OTROS CONCEPTOS REMUNERATIVOS COMPUTABLES (S/)")
        entry("otros_computables", "0")
        etiqueta("ÚLTIMA GRATIFICACIÓN PAGADA (S/) – PARA BASE CTS")
        entry("ultima_gratificacion", "0")
        etiqueta("INICIO DEL PERIODO CTS (AAAA-MM-DD) – ÚLTIMO DEPÓSITO / INICIO DEL SEMESTRE")
        default_cts = f"{date.today().year}-11-01" if date.today().month >= 11 else f"{date.today().year}-05-01"
        entry("inicio_periodo_cts", default_cts)
        etiqueta("INICIO DEL RÉCORD VACACIONAL ACTUAL (AAAA-MM-DD)")
        entry("inicio_periodo_vacaciones", seleccionado.get("fecha_ingreso_laboral") or seleccionado.get("fecha_ingreso") or "")
        etiqueta("DÍAS DE VACACIONES YA GOZADOS EN EL RÉCORD ACTUAL")
        entry("vacaciones_tomadas", "0")
        etiqueta("DÍAS DE VACACIONES PENDIENTES DE PERIODOS ANTERIORES")
        entry("vacaciones_pendientes", "0")
        etiqueta("DÍAS CON INDEMNIZACIÓN VACACIONAL YA DETERMINADA (SI CORRESPONDE)")
        entry("dias_vacaciones_indemnizables", "0")
        etiqueta("REMUNERACIÓN PENDIENTE DE PAGO (S/)")
        entry("sueldo_pendiente", "0")
        etiqueta("OTROS PAGOS PENDIENTES (S/)")
        entry("otros_pendientes", "0")
        etiqueta("OTROS DESCUENTOS AUTORIZADOS Y SUSTENTADOS (S/)")
        entry("descuentos", "0")
        etiqueta("OBSERVACIONES")
        obs = ctk.CTkTextbox(form, height=70)
        obs.pack(fill="x", padx=14, pady=(0, 8))
        campos["observaciones"] = obs
        resumen = ctk.CTkTextbox(form, height=190, font=("Consolas", 12))
        resumen.pack(fill="x", padx=14, pady=10)
        resultado_actual = {"datos": None}

        def cambiar_trabajador(valor):
            t = nombres.get(valor)
            if t:
                ingreso_entry.delete(0, "end"); ingreso_entry.insert(0, t.get("fecha_ingreso_laboral") or t.get("fecha_ingreso") or "")
                sueldo_entry.delete(0, "end"); sueldo_entry.insert(0, f"{float(t.get('sueldo_basico') or 0):.2f}")
        trabajador_combo.configure(command=cambiar_trabajador)

        def obtener_datos():
            t = nombres.get(trabajador_combo.get())
            if not t: raise ValueError("Selecciona un trabajador válido.")
            d = {k: w.get() for k, w in campos.items() if k != "observaciones"}
            d["observaciones"] = obs.get("1.0", "end").strip()
            d.update({"trabajador_id": t["id"], "dni": t["dni"],
                      "trabajador": f"{t['nombres']} {t['apellidos']}", "cargo": t.get("cargo") or ""})
            return d

        def calcular():
            try:
                datos = calcular_liquidacion(obtener_datos())
                resultado_actual["datos"] = datos
                lineas = [f"TRABAJADOR: {datos['trabajador']}", f"RÉGIMEN: {datos['regimen_laboral']}",
                          f"PERIODO: {datos['fecha_ingreso']} AL {datos['fecha_cese']}", "", "DETALLE DE LIQUIDACIÓN"]
                lineas += [f"{k:<48} S/ {v:>10,.2f}" for k, v in datos["conceptos"].items()]
                lineas += ["", f"TOTAL BRUTO:                 S/ {datos['total_bruto']:,.2f}",
                           f"DESCUENTOS:                  S/ {datos['total_descuentos']:,.2f}",
                           f"NETO A PAGAR:                S/ {datos['neto']:,.2f}", "",
                           "Revisa régimen, CTS depositada, gratificaciones y vacaciones ya pagadas."]
                resumen.delete("1.0", "end"); resumen.insert("1.0", "\n".join(lineas))
                return datos
            except Exception as e:
                messagebox.showerror("No se pudo calcular", str(e), parent=ventana)
                return None

        def guardar_pdf():
            datos = resultado_actual.get("datos") or calcular()
            if not datos: return
            try:
                liquidacion_id = guardar_liquidacion(datos)
                ruta = filedialog.asksaveasfilename(parent=ventana, title="Guardar liquidación PDF",
                    defaultextension=".pdf", initialfile=f"Liquidacion_{datos['dni']}_{datos['fecha_cese']}.pdf",
                    filetypes=[("Documento PDF", "*.pdf")])
                if ruta:
                    generar_liquidacion_pdf(datos, ruta)
                    messagebox.showinfo("Liquidación guardada", f"Registro N.° {liquidacion_id}\nPDF generado en:\n{ruta}", parent=ventana)
                else:
                    messagebox.showinfo("Liquidación guardada", f"Registro N.° {liquidacion_id} guardado en el historial. No se generó PDF.", parent=ventana)
                ventana.destroy()
                self.ventana_liquidaciones()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la liquidación:\n{e}", parent=ventana)

        botones = ctk.CTkFrame(form, fg_color="transparent")
        botones.pack(fill="x", padx=14, pady=12)
        ctk.CTkButton(botones, text="CALCULAR VISTA PREVIA", command=calcular,
                      height=42, fg_color="#1D4ED8").pack(fill="x", pady=(0, 7))
        ctk.CTkButton(botones, text="GUARDAR LIQUIDACIÓN Y GENERAR PDF", command=guardar_pdf,
                      height=45, fg_color="#167A52", hover_color="#105C3D").pack(fill="x")

    # =====================================================
    # CERTIFICADOS LABORALES Y TRIBUTARIOS
    # =====================================================

    def ventana_certificados(self):
        self.limpiar_contenido()
        ctk.CTkLabel(self.contenido, text="Certificados y constancias",
                     font=("Arial", 26, "bold"), text_color="#172554").pack(
                         anchor="w", padx=25, pady=(25, 8))
        ctk.CTkLabel(self.contenido,
                     text="Genera certificados de trabajo y reportes de rentas y retenciones de quinta categoría.",
                     font=("Arial", 13), text_color="#64748B").pack(anchor="w", padx=25, pady=(0, 18))
        marco = ctk.CTkFrame(self.contenido, fg_color="white", corner_radius=12)
        marco.pack(fill="x", padx=25, pady=8)
        ctk.CTkLabel(marco, text="DOCUMENTOS DISPONIBLES", font=("Arial", 15, "bold"),
                     text_color="#172554").pack(anchor="w", padx=20, pady=(18, 8))
        ctk.CTkButton(marco, text="GENERAR CERTIFICADO DE TRABAJO", height=45,
                      command=self.formulario_certificado_trabajo).pack(fill="x", padx=20, pady=8)
        ctk.CTkButton(marco, text="GENERAR CONSTANCIA DE RENTAS Y RETENCIONES - 5TA CATEGORÍA",
                      height=45, fg_color="#0F766E", hover_color="#115E59",
                      command=self.formulario_constancia_quinta).pack(fill="x", padx=20, pady=(0, 18))
        ctk.CTkLabel(self.contenido,
                     text=("Importante: el certificado de trabajo utiliza los datos registrados del trabajador. "
                           "La constancia de quinta categoría requiere ingresar los totales anuales verificados, "
                           "porque el sistema todavía no almacena un historial específico de retenciones."),
                     text_color="#92400E", wraplength=900, justify="left").pack(anchor="w", padx=28, pady=12)

    def _trabajadores_para_certificado(self):
        trabajadores = listar_trabajadores()
        opciones = {}
        for t in trabajadores:
            opciones[f"{t[0]} - {t[1]} {t[2]} {t[3]} (DNI: {t[1]})"] = t
        return opciones

    def _datos_trabajador_certificado(self, t):
        # Estructura de trabajadores: id, DNI, nombres, apellidos, fecha_ingreso,
        # cargo, sueldo, estado y columnas adicionales migradas en la BD.
        return {
            "id": t[0], "dni": t[1], "nombres": t[2], "apellidos": t[3],
            "fecha_ingreso": t[4] if len(t) > 4 else None,
            "cargo": t[5] if len(t) > 5 else None,
            "estado": t[7] if len(t) > 7 else None,
            "fecha_nacimiento": t[8] if len(t) > 8 else None,
            "fecha_ingreso_laboral": t[9] if len(t) > 9 else None,
            "area": t[15] if len(t) > 15 else None,
        }

    def formulario_certificado_trabajo(self):
        opciones = self._trabajadores_para_certificado()
        if not opciones:
            messagebox.showwarning("Certificado", "Primero registra un trabajador.")
            return
        v = ctk.CTkToplevel(self.root); v.title("Certificado de trabajo"); v.geometry("620x650"); v.grab_set()
        form = ctk.CTkScrollableFrame(v); form.pack(fill="both", expand=True, padx=15, pady=15)
        ctk.CTkLabel(form, text="CERTIFICADO DE TRABAJO", font=("Arial", 20, "bold")).pack(pady=12)
        def campo(label, default=""):
            ctk.CTkLabel(form, text=label, font=("Arial", 12, "bold")).pack(anchor="w", padx=12, pady=(8, 2))
            e=ctk.CTkEntry(form, width=540); e.pack(padx=12, pady=2); e.insert(0, default); return e
        ctk.CTkLabel(form, text="TRABAJADOR", font=("Arial", 12, "bold")).pack(anchor="w", padx=12)
        combo=ctk.CTkComboBox(form, values=list(opciones), width=540, state="readonly"); combo.pack(padx=12, pady=4); combo.set(list(opciones)[0])
        empresa=campo("Razón social de la empresa")
        ruc=campo("RUC de la empresa")
        representante=campo("Nombre del representante legal")
        cargo_rep=campo("Cargo del representante", "Representante legal")
        cese=campo("Fecha de cese (dejar vacío si continúa laborando)")
        fecha=campo("Fecha de emisión", datetime.now().strftime("%d/%m/%Y"))
        def generar():
            try:
                t=opciones[combo.get()]; datos=self._datos_trabajador_certificado(t); datos['fecha_cese']=cese.get().strip()
                if not empresa.get().strip() or not ruc.get().strip() or not representante.get().strip():
                    raise ValueError("Completa razón social, RUC y representante legal.")
                ruta=filedialog.asksaveasfilename(parent=v, title="Guardar certificado", defaultextension=".pdf",
                    initialfile=f"Certificado_Trabajo_{datos['dni']}.pdf", filetypes=[("PDF", "*.pdf")])
                if not ruta: return
                generar_certificado_trabajo(datos, empresa.get().strip(), ruc.get().strip(), representante.get().strip(),
                                            cargo_rep.get().strip(), fecha.get().strip(), ruta)
                messagebox.showinfo("Certificado generado", f"PDF guardado en:\n{ruta}", parent=v); v.destroy()
            except Exception as e: messagebox.showerror("Certificado", str(e), parent=v)
        ctk.CTkButton(form, text="GENERAR PDF", height=44, command=generar).pack(fill="x", padx=12, pady=20)

    def formulario_constancia_quinta(self):
        opciones=self._trabajadores_para_certificado()
        if not opciones:
            messagebox.showwarning("Quinta categoría", "Primero registra un trabajador."); return
        v=ctk.CTkToplevel(self.root); v.title("Constancia de quinta categoría"); v.geometry("620x700"); v.grab_set()
        form=ctk.CTkScrollableFrame(v); form.pack(fill="both", expand=True, padx=15, pady=15)
        ctk.CTkLabel(form, text="RENTAS Y RETENCIONES - QUINTA CATEGORÍA", font=("Arial", 18, "bold")).pack(pady=12)
        def campo(label, default=""):
            ctk.CTkLabel(form, text=label, font=("Arial", 12, "bold")).pack(anchor="w", padx=12, pady=(8,2))
            e=ctk.CTkEntry(form, width=540); e.pack(padx=12,pady=2); e.insert(0,default); return e
        ctk.CTkLabel(form, text="TRABAJADOR", font=("Arial", 12, "bold")).pack(anchor="w", padx=12)
        combo=ctk.CTkComboBox(form, values=list(opciones), width=540, state="readonly"); combo.pack(padx=12,pady=4); combo.set(list(opciones)[0])
        empresa=campo("Razón social de la empresa"); ruc=campo("RUC de la empresa")
        anio=campo("Ejercicio anual", str(datetime.now().year-1))
        renta=campo("Total anual de rentas brutas de quinta categoría (S/)", "0.00")
        retencion=campo("Total anual de retenciones de quinta categoría (S/)", "0.00")
        fecha=campo("Fecha de emisión", datetime.now().strftime("%d/%m/%Y"))
        ctk.CTkLabel(form, text="Los importes deben contrastarse con planillas, boletas y declaraciones tributarias.",
                     text_color="#92400E", wraplength=530, justify="left").pack(anchor="w", padx=12, pady=10)
        def generar():
            try:
                datos=self._datos_trabajador_certificado(opciones[combo.get()])
                if not empresa.get().strip() or not ruc.get().strip(): raise ValueError("Completa razón social y RUC.")
                ejercicio=int(anio.get()); rb=float(renta.get().replace(",", "")); rt=float(retencion.get().replace(",", ""))
                if ejercicio<2000 or ejercicio>2100 or rb<0 or rt<0: raise ValueError("Verifica el ejercicio y los importes.")
                ruta=filedialog.asksaveasfilename(parent=v, title="Guardar constancia", defaultextension=".pdf",
                    initialfile=f"Constancia_Quinta_{datos['dni']}_{ejercicio}.pdf", filetypes=[("PDF", "*.pdf")])
                if not ruta: return
                generar_constancia_quinta(datos, empresa.get().strip(), ruc.get().strip(), ejercicio, rb, rt,
                                          fecha.get().strip(), ruta)
                messagebox.showinfo("Constancia generada", f"PDF guardado en:\n{ruta}", parent=v); v.destroy()
            except Exception as e: messagebox.showerror("Quinta categoría", str(e), parent=v)
        ctk.CTkButton(form, text="GENERAR PDF", height=44, fg_color="#0F766E", command=generar).pack(fill="x", padx=12, pady=20)

    # =====================================================
    # HISTORIAL DE ASISTENCIA GUARDADO EN PLANILLAS
    # =====================================================

    def ventana_historial_asistencia(self):
        """Consulta la fotografía de asistencia que quedó guardada en cada planilla."""
        self.limpiar_contenido()

        ctk.CTkLabel(
            self.contenido,
            text="Historial de asistencia en planillas",
            font=("Arial", 26, "bold"),
            text_color="#172554"
        ).pack(anchor="w", padx=25, pady=(22, 5))

        ctk.CTkLabel(
            self.contenido,
            text=(
                "Consulta los días registrados, presentes, faltas, permisos y descansos "
                "de cada periodo. Si una planilla no guardó el resumen, se recuperan "
                "los registros existentes de asistencia. No modifica cálculos ni aplica "
                "descuentos automáticos."
            ),
            font=("Arial", 13),
            text_color="#64748B",
            justify="left",
            wraplength=950
        ).pack(anchor="w", padx=25, pady=(0, 14))

        filtros = ctk.CTkFrame(self.contenido, fg_color="white", corner_radius=10)
        filtros.pack(fill="x", padx=25, pady=8)

        ctk.CTkLabel(filtros, text="AÑO").grid(
            row=0, column=0, padx=(12, 5), pady=(10, 2), sticky="w"
        )
        anio_filtro = ctk.CTkEntry(filtros, width=95, placeholder_text="Todos")
        anio_filtro.grid(row=1, column=0, padx=(12, 8), pady=(0, 10))

        ctk.CTkLabel(filtros, text="MES").grid(
            row=0, column=1, padx=5, pady=(10, 2), sticky="w"
        )
        nombres_meses = [
            "Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo",
            "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
            "Noviembre", "Diciembre"
        ]
        mes_filtro = ctk.CTkComboBox(
            filtros, values=nombres_meses, width=145, state="readonly"
        )
        mes_filtro.grid(row=1, column=1, padx=8, pady=(0, 10))
        mes_filtro.set("Todos")

        ctk.CTkLabel(filtros, text="BUSCAR DNI O TRABAJADOR").grid(
            row=0, column=2, padx=5, pady=(10, 2), sticky="w"
        )
        buscar_filtro = ctk.CTkEntry(
            filtros, width=240, placeholder_text="Escribe DNI o nombre"
        )
        buscar_filtro.grid(row=1, column=2, padx=8, pady=(0, 10))

        marco = ctk.CTkFrame(self.contenido, fg_color="white", corner_radius=10)
        marco.pack(fill="both", expand=True, padx=25, pady=(8, 10))

        columnas = (
            "dni", "trabajador", "anio", "mes", "registrados",
            "presentes", "faltas", "permisos", "descansos"
        )
        tabla = ttk.Treeview(
            marco, columns=columnas, show="headings", height=15
        )
        titulos = {
            "dni": "DNI",
            "trabajador": "TRABAJADOR",
            "anio": "AÑO",
            "mes": "MES",
            "registrados": "DÍAS REGISTRADOS",
            "presentes": "PRESENTES",
            "faltas": "FALTAS",
            "permisos": "PERMISOS",
            "descansos": "DESCANSOS"
        }
        anchos = {
            "dni": 85, "trabajador": 210, "anio": 65, "mes": 90,
            "registrados": 115, "presentes": 90, "faltas": 80,
            "permisos": 90, "descansos": 95
        }
        for columna in columnas:
            tabla.heading(columna, text=titulos[columna])
            tabla.column(columna, width=anchos[columna], anchor="center")

        scroll_y = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
        scroll_x = ttk.Scrollbar(marco, orient="horizontal", command=tabla.xview)
        tabla.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        tabla.pack(side="top", fill="both", expand=True, padx=(8, 0), pady=8)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

        resumen_label = ctk.CTkLabel(
            self.contenido,
            text="",
            font=("Arial", 12, "bold"),
            text_color="#334155"
        )
        resumen_label.pack(anchor="w", padx=28, pady=(0, 8))

        registros_historial = []

        def cargar_registros():
            registros_historial.clear()
            try:
                for fila in listar_planillas():
                    planilla_id = fila[0]
                    datos = obtener_planilla_por_id(planilla_id)
                    if not datos:
                        continue

                    datos = dict(datos)
                    trabajador_id = datos.get("trabajador_id")
                    anio = int(datos.get("anio", fila[4] if len(fila) > 4 else 0) or 0)
                    mes = int(datos.get("mes", fila[5] if len(fila) > 5 else 0) or 0)

                    resumen_guardado = {
                        "registrados": int(datos.get("asistencia_dias_registrados", 0) or 0),
                        "presentes": int(datos.get("asistencia_presentes", 0) or 0),
                        "faltas": int(datos.get("asistencia_faltas", 0) or 0),
                        "permisos": int(datos.get("asistencia_permisos", 0) or 0),
                        "descansos": int(datos.get("asistencia_descansos", 0) or 0)
                    }

                    # Compatibilidad con planillas generadas antes de registrar
                    # asistencia o antes de incorporar la fotografía mensual:
                    # si el resumen guardado está vacío, consulta la tabla real
                    # de asistencia para ese trabajador y periodo.
                    if sum(resumen_guardado.values()) == 0 and trabajador_id and anio and 1 <= mes <= 12:
                        resumen_actual = resumen_mensual_asistencia(
                            anio, mes, trabajador_id=trabajador_id
                        )
                        if resumen_actual:
                            resumen_guardado = {
                                "registrados": int(resumen_actual[0][4] or 0),
                                "presentes": int(resumen_actual[0][5] or 0),
                                "faltas": int(resumen_actual[0][6] or 0),
                                "permisos": int(resumen_actual[0][7] or 0),
                                "descansos": int(resumen_actual[0][8] or 0)
                            }

                    registros_historial.append({
                        "dni": str(datos.get("dni", fila[1] if len(fila) > 1 else "")),
                        "nombres": str(datos.get("nombres", fila[2] if len(fila) > 2 else "")),
                        "apellidos": str(datos.get("apellidos", fila[3] if len(fila) > 3 else "")),
                        "anio": anio,
                        "mes": mes,
                        **resumen_guardado
                    })
            except Exception as error:
                messagebox.showerror(
                    "Historial de asistencia",
                    f"No se pudieron consultar las planillas guardadas:\n{error}"
                )

        def aplicar_filtros():
            for item in tabla.get_children():
                tabla.delete(item)

            texto = buscar_filtro.get().strip().lower()
            anio_texto = anio_filtro.get().strip()
            mes_texto = mes_filtro.get()
            mes_numero = nombres_meses.index(mes_texto) if mes_texto in nombres_meses else 0

            if anio_texto:
                if not anio_texto.isdigit() or len(anio_texto) != 4:
                    messagebox.showwarning(
                        "Filtro de año", "Ingresa un año de cuatro dígitos o deja el campo vacío."
                    )
                    return

            mostrados = 0
            total_presentes = total_faltas = total_permisos = total_descansos = 0

            for registro in registros_historial:
                if anio_texto and registro["anio"] != int(anio_texto):
                    continue
                if mes_numero and registro["mes"] != mes_numero:
                    continue

                nombre_completo = f'{registro["nombres"]} {registro["apellidos"]}'.strip()
                if texto and texto not in registro["dni"].lower() and texto not in nombre_completo.lower():
                    continue

                meses_espanol = [
                    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
                ]
                mes_nombre = (
                    meses_espanol[registro["mes"] - 1]
                    if 1 <= registro["mes"] <= 12 else str(registro["mes"])
                )
                tabla.insert("", "end", values=(
                    registro["dni"],
                    nombre_completo,
                    registro["anio"],
                    mes_nombre,
                    registro["registrados"],
                    registro["presentes"],
                    registro["faltas"],
                    registro["permisos"],
                    registro["descansos"]
                ))
                mostrados += 1
                total_presentes += registro["presentes"]
                total_faltas += registro["faltas"]
                total_permisos += registro["permisos"]
                total_descansos += registro["descansos"]

            resumen_label.configure(
                text=(
                    f"PLANILLAS EN PANTALLA: {mostrados}    |    "
                    f"PRESENTES: {total_presentes}    |    "
                    f"FALTAS: {total_faltas}    |    "
                    f"PERMISOS: {total_permisos}    |    "
                    f"DESCANSOS: {total_descansos}"
                )
            )

        botones_filtro = ctk.CTkFrame(filtros, fg_color="transparent")
        botones_filtro.grid(row=1, column=3, padx=8, pady=(0, 10))
        ctk.CTkButton(
            botones_filtro,
            text="FILTRAR",
            width=95,
            command=aplicar_filtros
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            botones_filtro,
            text="ACTUALIZAR",
            width=105,
            fg_color="#64748B",
            hover_color="#475569",
            command=lambda: (cargar_registros(), aplicar_filtros())
        ).pack(side="left")

        cargar_registros()
        aplicar_filtros()

    # =====================================================
    # ASISTENCIA
    # =====================================================

    def ventana_asistencia(self):
        self.limpiar_contenido()

        encabezado = ctk.CTkFrame(self.contenido, fg_color="transparent")
        encabezado.pack(fill="x", padx=25, pady=(22, 8))

        ctk.CTkLabel(
            encabezado, text="Control de asistencia",
            font=("Arial", 26, "bold"), text_color="#172554"
        ).pack(anchor="w")
        ctk.CTkLabel(
            encabezado,
            text="Registra y consulta las entradas, salidas y estados diarios del personal.",
            font=("Arial", 13), text_color="#64748B"
        ).pack(anchor="w", pady=(4, 0))

        acciones = ctk.CTkFrame(self.contenido, fg_color="transparent")
        acciones.pack(fill="x", padx=25, pady=8)
        ctk.CTkButton(
            acciones, text="+ REGISTRAR ASISTENCIA", height=40,
            command=self.formulario_asistencia
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            acciones, text="RESUMEN MENSUAL", height=40,
            fg_color="#167A52", hover_color="#105C3D",
            command=self.mostrar_resumen_asistencia
        ).pack(side="left")

        filtros = ctk.CTkFrame(self.contenido, fg_color="white", corner_radius=10)
        filtros.pack(fill="x", padx=25, pady=8)
        ctk.CTkLabel(filtros, text="Desde (AAAA-MM-DD)").grid(row=0, column=0, padx=10, pady=(10, 2), sticky="w")
        self.asistencia_desde = ctk.CTkEntry(filtros, placeholder_text="2026-11-01", width=145)
        self.asistencia_desde.grid(row=1, column=0, padx=10, pady=(0, 10))
        ctk.CTkLabel(filtros, text="Hasta (AAAA-MM-DD)").grid(row=0, column=1, padx=10, pady=(10, 2), sticky="w")
        self.asistencia_hasta = ctk.CTkEntry(filtros, placeholder_text="2026-11-30", width=145)
        self.asistencia_hasta.grid(row=1, column=1, padx=10, pady=(0, 10))
        ctk.CTkButton(
            filtros, text="FILTRAR", width=100,
            command=self.actualizar_tabla_asistencia
        ).grid(row=1, column=2, padx=10, pady=(0, 10))
        ctk.CTkButton(
            filtros, text="MOSTRAR TODO", width=120, fg_color="#64748B",
            command=self.limpiar_filtros_asistencia
        ).grid(row=1, column=3, padx=10, pady=(0, 10))

        marco = ctk.CTkFrame(self.contenido, fg_color="white")
        marco.pack(fill="both", expand=True, padx=25, pady=(8, 22))
        columnas = ("id", "dni", "trabajador", "fecha", "entrada", "salida", "estado", "observaciones")
        self.tabla_asistencia = ttk.Treeview(marco, columns=columnas, show="headings", height=13)
        titulos = {
            "id": "ID", "dni": "DNI", "trabajador": "TRABAJADOR",
            "fecha": "FECHA", "entrada": "ENTRADA", "salida": "SALIDA",
            "estado": "ESTADO", "observaciones": "OBSERVACIONES"
        }
        anchos = {"id": 45, "dni": 85, "trabajador": 190, "fecha": 100,
                  "entrada": 80, "salida": 80, "estado": 100, "observaciones": 200}
        for col in columnas:
            self.tabla_asistencia.heading(col, text=titulos[col])
            self.tabla_asistencia.column(col, width=anchos[col], anchor="center")
        scroll_y = ttk.Scrollbar(marco, orient="vertical", command=self.tabla_asistencia.yview)
        scroll_x = ttk.Scrollbar(marco, orient="horizontal", command=self.tabla_asistencia.xview)
        self.tabla_asistencia.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tabla_asistencia.pack(side="top", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

        pie = ctk.CTkFrame(self.contenido, fg_color="transparent")
        pie.pack(fill="x", padx=25, pady=(0, 12))
        ctk.CTkButton(
            pie, text="EDITAR REGISTRO SELECCIONADO", height=38,
            fg_color="#D97706", hover_color="#B45309",
            command=self.editar_asistencia_seleccionada
        ).pack(side="left")
        self.actualizar_tabla_asistencia()

    def limpiar_filtros_asistencia(self):
        self.asistencia_desde.delete(0, "end")
        self.asistencia_hasta.delete(0, "end")
        self.actualizar_tabla_asistencia()

    def actualizar_tabla_asistencia(self):
        if not hasattr(self, "tabla_asistencia"):
            return
        for fila in self.tabla_asistencia.get_children():
            self.tabla_asistencia.delete(fila)
        desde = self.asistencia_desde.get().strip() or None
        hasta = self.asistencia_hasta.get().strip() or None
        try:
            registros = listar_asistencias(fecha_inicio=desde, fecha_fin=hasta)
            for r in registros:
                self.tabla_asistencia.insert("", "end", values=(
                    r[0], r[2], f"{r[3]} {r[4]}", r[5], r[6] or "—",
                    r[7] or "—", r[8], r[9] or ""
                ))
        except ValueError as error:
            messagebox.showerror("Filtro de fechas", str(error))

    def _trabajadores_para_asistencia(self):
        trabajadores = listar_trabajadores()
        opciones = {}
        for t in trabajadores:
            # Estructura existente de listar_trabajadores(): id, DNI, nombres, apellidos...
            if len(t) > 7 and str(t[7]).upper() != "ACTIVO":
                continue
            etiqueta = f"{t[1]} - {t[2]} {t[3]}"
            opciones[etiqueta] = t[0]
        return opciones

    def formulario_asistencia(self, registro=None):
        ventana = ctk.CTkToplevel(self.root)
        ventana.title("Registrar asistencia" if registro is None else "Editar asistencia")
        ventana.geometry("520x650")
        ventana.resizable(False, False)
        ventana.transient(self.root)
        ventana.grab_set()

        contenedor = ctk.CTkScrollableFrame(ventana, fg_color="#F3F6FB")
        contenedor.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(
            contenedor, text="REGISTRO DE ASISTENCIA",
            font=("Arial", 22, "bold"), text_color="#172554"
        ).pack(anchor="w", padx=12, pady=(12, 18))

        opciones = self._trabajadores_para_asistencia()
        if not opciones:
            messagebox.showwarning("Sin trabajadores", "Primero registra un trabajador activo.", parent=ventana)
            ventana.destroy()
            return

        def campo(etiqueta, placeholder="", valor=""):
            ctk.CTkLabel(contenedor, text=etiqueta, font=("Arial", 12, "bold"), text_color="#334155").pack(anchor="w", padx=12, pady=(8, 3))
            entrada = ctk.CTkEntry(contenedor, height=36, placeholder_text=placeholder)
            entrada.pack(fill="x", padx=12)
            if valor not in (None, ""):
                entrada.insert(0, str(valor))
            return entrada

        ctk.CTkLabel(contenedor, text="TRABAJADOR", font=("Arial", 12, "bold"), text_color="#334155").pack(anchor="w", padx=12, pady=(8, 3))
        combo_trabajador = ctk.CTkComboBox(contenedor, values=list(opciones.keys()), height=36, state="readonly")
        combo_trabajador.pack(fill="x", padx=12)
        seleccionado = None
        if registro is not None:
            for etiqueta, trabajador_id in opciones.items():
                if trabajador_id == registro[1]:
                    seleccionado = etiqueta
                    break
        combo_trabajador.set(seleccionado or list(opciones.keys())[0])

        fecha = campo("FECHA (AAAA-MM-DD)", "2026-11-25", registro[5] if registro else datetime.now().strftime("%Y-%m-%d"))
        entrada = campo("HORA DE ENTRADA (HH:MM)", "08:00", registro[6] if registro else "")
        salida = campo("HORA DE SALIDA (HH:MM)", "17:00", registro[7] if registro else "")

        ctk.CTkLabel(contenedor, text="ESTADO", font=("Arial", 12, "bold"), text_color="#334155").pack(anchor="w", padx=12, pady=(8, 3))
        combo_estado = ctk.CTkComboBox(contenedor, values=["PRESENTE", "FALTA", "DESCANSO", "PERMISO"], state="readonly", height=36)
        combo_estado.pack(fill="x", padx=12)
        combo_estado.set(registro[8] if registro else "PRESENTE")
        observaciones = campo("OBSERVACIONES", "Detalle opcional", registro[9] if registro else "")

        def guardar():
            try:
                trabajador_id = opciones[combo_trabajador.get()]
                if registro is None:
                    ok, mensaje = registrar_asistencia(
                        trabajador_id, fecha.get().strip(), entrada.get().strip() or None,
                        salida.get().strip() or None, combo_estado.get(), observaciones.get().strip()
                    )
                else:
                    ok, mensaje = actualizar_asistencia(
                        registro[0], fecha.get().strip(), entrada.get().strip() or None,
                        salida.get().strip() or None, combo_estado.get(), observaciones.get().strip()
                    )
                if ok:
                    messagebox.showinfo("Asistencia", mensaje, parent=ventana)
                    ventana.destroy()
                    self.actualizar_tabla_asistencia()
                else:
                    messagebox.showwarning("No se guardó", mensaje, parent=ventana)
            except ValueError as error:
                messagebox.showerror("Validación", str(error), parent=ventana)
            except Exception as error:
                messagebox.showerror("Error", f"No se pudo guardar la asistencia:\n{error}", parent=ventana)

        ctk.CTkButton(
            contenedor, text="GUARDAR REGISTRO", height=44,
            fg_color="#167A52", hover_color="#105C3D", command=guardar
        ).pack(fill="x", padx=12, pady=22)

    def editar_asistencia_seleccionada(self):
        seleccion = self.tabla_asistencia.selection()
        if not seleccion:
            messagebox.showwarning("Selecciona un registro", "Selecciona una fila de asistencia para editar.")
            return
        valores = self.tabla_asistencia.item(seleccion[0], "values")
        registro = obtener_asistencia_por_id(int(valores[0]))
        if registro:
            self.formulario_asistencia(registro)
        else:
            messagebox.showerror("Registro no encontrado", "No se encontró la asistencia seleccionada.")

    def mostrar_resumen_asistencia(self):
        ventana = ctk.CTkToplevel(self.root)
        ventana.title("Resumen mensual de asistencia")
        ventana.geometry("900x520")
        ventana.transient(self.root)
        ventana.grab_set()

        barra = ctk.CTkFrame(ventana, fg_color="transparent")
        barra.pack(fill="x", padx=18, pady=18)
        ctk.CTkLabel(barra, text="AÑO").pack(side="left", padx=(0, 5))
        anio = ctk.CTkEntry(barra, width=90)
        anio.pack(side="left", padx=(0, 15))
        anio.insert(0, str(datetime.now().year))
        ctk.CTkLabel(barra, text="MES").pack(side="left", padx=(0, 5))
        mes = ctk.CTkComboBox(barra, values=[str(i) for i in range(1, 13)], width=90, state="readonly")
        mes.pack(side="left", padx=(0, 15))
        mes.set(str(datetime.now().month))

        marco = ctk.CTkFrame(ventana)
        marco.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        columnas = ("dni", "trabajador", "registrados", "presentes", "faltas", "permisos", "descansos")
        tabla = ttk.Treeview(marco, columns=columnas, show="headings")
        titulos = {"dni": "DNI", "trabajador": "TRABAJADOR", "registrados": "REGISTRADOS",
                   "presentes": "PRESENTES", "faltas": "FALTAS", "permisos": "PERMISOS", "descansos": "DESCANSOS"}
        for col in columnas:
            tabla.heading(col, text=titulos[col])
            tabla.column(col, width=115 if col != "trabajador" else 220, anchor="center")
        tabla.pack(fill="both", expand=True, padx=8, pady=8)

        def cargar():
            for item in tabla.get_children():
                tabla.delete(item)
            try:
                for r in resumen_mensual_asistencia(int(anio.get()), int(mes.get())):
                    tabla.insert("", "end", values=(r[1], f"{r[2]} {r[3]}", *(int(v or 0) for v in r[4:9])))
            except (ValueError, TypeError) as error:
                messagebox.showerror("Periodo inválido", str(error), parent=ventana)

        ctk.CTkButton(barra, text="CONSULTAR", command=cargar).pack(side="left")
        cargar()

# =========================================================
# EJECUCIÓN DEL SISTEMA
# =========================================================

if __name__ == "__main__":

    root = ctk.CTk()
    app = SistemaPlanillas(root)
    root.mainloop()