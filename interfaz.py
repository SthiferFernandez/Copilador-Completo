import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from concurrent.futures import ThreadPoolExecutor

import estilos as e
from compilador import compilar_y_analizar_completo, ErrorAnalisis
from ejecutor import ejecutar

# Codigos de ejemplo listos para cargar en la exposicion con los companeros
# Asi no hay que estar tipeando en vivo con la presion de la gente mirando jajaj
EJEMPLOS_PRUEBA = {
    '1. Aritmética y Variables': (
        "# Ejemplo 1: Operaciones básicas y variables\n"
        "base = 10\n"
        "altura = 5\n"
        "area = (base * altura) / 2\n"
        "print(\"El área calculada es:\", area)\n"
    ),
    '2. Condicional If-Else': (
        "# Ejemplo 2: Estructuras condicionales y comparaciones\n"
        "edad = 20\n"
        "tiene_cedula = True\n"
        "if edad >= 18 and tiene_cedula:\n"
        "    print(\"Acceso permitido: Es mayor de edad y tiene documento.\")\n"
        "else:\n"
        "    print(\"Acceso denegado.\")\n"
    ),
    '3. Bucle While y Contador': (
        "# Ejemplo 3: Bucle while con acumulador\n"
        "contador = 1\n"
        "total = 0\n"
        "while contador <= 5:\n"
        "    total += contador\n"
        "    print(\"Sumando paso:\", contador, \"Total acumulado:\", total)\n"
        "    contador += 1\n"
        "print(\"Suma final:\", total)\n"
    ),
    '4. Textos y Booleanos': (
        "# Ejemplo 4: Cadenas de texto y valores lógicos\n"
        "saludo = \"Hola compañeros\"\n"
        "materia = \"Compiladores\"\n"
        "mensaje = saludo + \" - Exposición de \" + materia\n"
        "activo = True\n"
        "print(mensaje)\n"
        "print(\"Estado activo:\", activo)\n"
    ),
    '5. Error Léxico': (
        "# Ejemplo 5: Forzar error léxico\n"
        "# El símbolo '$' o '@' no es válido en el analizador léxico\n"
        "precio = 100\n"
        "total = precio $ 2\n"
        "print(total)\n"
    ),
    '6. Error Semántico': (
        "# Ejemplo 6: Forzar error semántico\n"
        "# No se puede sumar texto con número en lenguajes fuertemente tipados\n"
        "nombre = \"Juan\"\n"
        "edad = 25\n"
        "resultado = nombre + edad\n"
        "print(resultado)\n"
    )
}


def iniciar_interfaz():
    # Aqui montamos la ventana completa, sin esto no hay pantalla ni botones
    ventana = tk.Tk()
    ventana.title('Compilador Completo')
    ventana.geometry('1280x780')
    ventana.minsize(920, 580)
    ventana.configure(bg=e.FONDO)

    # Esto evita que la ventana se congele mientras Go o C hacen su chamba
    tareas = ThreadPoolExecutor(max_workers=1)
    ultimo = {'python': '', 'destino': '', 'codigo': ''}
    trabajando = False

    # Guardamos el resultado de cada una de las 5 fases para cambiarlas con pestañas
    vistas_compilador = {
        'traducido': 'Presiona "Analizar y traducir" para generar el código.',
        'simbolos': 'Sin analizar aún.',
        'intermedio': 'Sin analizar aún.',
        'lexico': 'Sin analizar aún.',
        'sintactico': 'Sin analizar aún.'
    }
    pestana_activa = {'clave': 'traducido'}

    # Borra lo que habia en un cuadrito y pone el texto nuevo
    def mostrar(caja, texto):
        caja.config(state='normal')
        caja.delete('1.0', tk.END)
        caja.insert('1.0', texto)
        caja.config(state='disabled')

    # La barrita de abajo avisa si todo bien o si explotamos
    def estado(mensaje, bien=True):
        barra_estado.config(text=mensaje, fg=e.VERDE if bien else e.ROJO)

    # Aqui sale el estado del analisis, verde bien y rojo mal
    def actualizar_analisis(texto, bien=True):
        analisis.config(text=texto, fg=e.VERDE if bien else e.ROJO)

    # Este es el informe que sale cuando no hay errores
    def informe_correcto(variables, codigo, destino):
        nombres = {'int': 'int', 'float64': 'float', 'string': 'str', 'bool': 'bool'}
        texto = ('========================================================================\n'
                 ' ANÁLISIS COMPLETADO EXITOSAMENTE\n'
                 '========================================================================\n'
                 'El código es sintáctica y semánticamente correcto.\n'
                 'No se encontraron errores léxicos, sintácticos ni semánticos.\n\n'
                 'VARIABLES REGISTRADAS:\n')
        if variables:
            for nombre, tipo in variables.items():
                texto += f'  • {nombre:<12} : {nombres.get(tipo, tipo)}\n'
        else:
            texto += '  (No se encontraron variables)\n'
        texto += f'\nCÓDIGO GENERADO EN {destino.upper()}:\n'
        texto += '------------------------------------------------------------------------\n'
        texto += codigo
        return texto

    # Cambia la vista del panel superior derecho segun la pestaña que toquen
    def cambiar_pestana(clave):
        pestana_activa['clave'] = clave
        for k, btn in botones_pestanas.items():
            if k == clave:
                btn.config(bg=e.MORADO, fg=e.BLANCO)
            else:
                btn.config(bg=e.MORADO_SECUNDARIO, fg=e.TEXTO_SECUNDARIO)
        mostrar(traducido, vistas_compilador.get(clave, ''))

    # Este boton corre las 6 fases del compilador
    def analizar():
        original = entrada.get('1.0', 'end-1c')
        destino = seleccion.get()
        if not original.strip():
            actualizar_analisis('Escribe un código Python o carga un ejemplo para comenzar.', False)
            for k in vistas_compilador:
                vistas_compilador[k] = ''
            mostrar(traducido, '')
            mostrar(consola, '')
            ultimo.update(python='', destino='', codigo='')
            estado('Falta el código Python.', False)
            return False

        try:
            # Mandamos a correr todo el pipeline del compilador
            datos = compilar_y_analizar_completo(original, destino)
            codigo = datos['codigo_traducido']
            variables = datos['variables']

            # Guardamos cada fase en su respectiva pestaña
            vistas_compilador['traducido'] = informe_correcto(variables, codigo, destino)
            vistas_compilador['simbolos'] = datos['reporte_tabla']
            vistas_compilador['intermedio'] = datos['reporte_intermedio']
            vistas_compilador['lexico'] = datos['reporte_lexico']
            vistas_compilador['sintactico'] = datos['reporte_sintactico']

        except ErrorAnalisis as error:
            # Si metieron la pata, mostramos donde y por que, no solo "error"
            msg_err = error.mostrar()
            for k in vistas_compilador:
                vistas_compilador[k] = msg_err
            mostrar(traducido, msg_err)
            mostrar(consola, '')
            actualizar_analisis(f'Error {error.tipo} en la línea {error.linea}.', False)
            ultimo.update(python='', destino='', codigo='')
            estado('Corrige el error antes de ejecutar.', False)
            return False
        except Exception as error:
            msg_gen = f'ERROR DE ANÁLISIS\n\n{error}'
            for k in vistas_compilador:
                vistas_compilador[k] = msg_gen
            mostrar(traducido, msg_gen)
            mostrar(consola, '')
            actualizar_analisis('No se pudo analizar el código.', False)
            ultimo.update(python='', destino='', codigo='')
            estado('Revisa el error indicado.', False)
            return False

        ultimo.update(python=original, destino=destino, codigo=codigo)
        cambiar_pestana(pestana_activa['clave'])
        mostrar(consola, '')
        actualizar_analisis(f'Análisis exitoso (6 fases completadas). Traducción a {destino} lista.')
        estado('Código analizado, tabla y TAC generados. Presiona Ejecutar.')
        return True

    # Aqui ejecutamos la traduccion, no el Python original, ojo con eso
    def ejecutar_traduccion():
        nonlocal trabajando
        if trabajando:
            return

        original = entrada.get('1.0', 'end-1c')
        if (original != ultimo['python'] or seleccion.get() != ultimo['destino']
                or not ultimo['codigo']):
            if not analizar():
                return

        codigo = ultimo['codigo']
        destino = ultimo['destino']
        trabajando = True
        b_analizar.config(state='disabled')
        b_ejecutar.config(state='disabled')
        mostrar(consola, f'Compilando y ejecutando {destino}...' if destino != 'JavaScript'
                else 'Generando archivos JavaScript...')
        estado('Ejecutando...')
        tarea = tareas.submit(ejecutar, codigo, destino)

        def revisar():
            nonlocal trabajando
            if not ventana.winfo_exists():
                return
            if not tarea.done():
                ventana.after(100, revisar)
                return
            try:
                salida = tarea.result()
                mostrar(consola, salida)
                estado('Ejecución terminada correctamente.')
            except Exception as error:
                mostrar(consola, 'ERROR DE EJECUCIÓN\n' + str(error))
                estado('No se pudo ejecutar el código.', False)
            trabajando = False
            b_analizar.config(state='normal')
            b_ejecutar.config(state='normal')

        ventana.after(100, revisar)

    # Carga el ejemplo seleccionado en el cuadro de texto para la exposicion
    def cargar_ejemplo_seleccionado(event=None):
        seleccionado = combo_ejemplos.get()
        if seleccionado in EJEMPLOS_PRUEBA:
            entrada.delete('1.0', tk.END)
            entrada.insert('1.0', EJEMPLOS_PRUEBA[seleccionado])
            estado(f'Ejemplo cargado: "{seleccionado}". Presiona "Analizar y traducir".')
            # Limpiamos salidas viejas
            for k in vistas_compilador:
                vistas_compilador[k] = ''
            mostrar(traducido, '')
            mostrar(consola, '')
            actualizar_analisis('Ejemplo listo para analizar.', True)

    # Deja todo en blanco para empezar otro codigo de cero
    def limpiar():
        if trabajando:
            return
        entrada.delete('1.0', tk.END)
        for k in vistas_compilador:
            vistas_compilador[k] = ''
        mostrar(traducido, '')
        mostrar(consola, '')
        combo_ejemplos.set('Cargar ejemplo de prueba...')
        ultimo.update(python='', destino='', codigo='')
        analisis.config(text='Sin analizar.', fg=e.TEXTO_SECUNDARIO)
        estado('Listo. Escribe tu código Python o carga un ejemplo.')

    # ================= CONSTRUCCIÓN VISUAL DE LA INTERFAZ =================

    cabecera = tk.Frame(ventana, bg=e.HEADER)
    cabecera.pack(fill='x')
    tk.Label(cabecera, text='COMPILADOR COMPLETO',
             font=e.FUENTE_TITULO, fg=e.BLANCO, bg=e.HEADER).pack(pady=(12, 4))
    tk.Label(cabecera, text='Léxico  •  Sintáctico  •  Semántico  •  Tabla de Símbolos  •  Código Intermedio  •  Traducción a Go / C / JS',
             font=('Arial', 10), fg=e.TEXTO_SECUNDARIO, bg=e.HEADER).pack(pady=(0, 10))

    barra = tk.Frame(ventana, bg=e.FONDO)
    barra.pack(fill='x', padx=16, pady=(10, 8))

    tk.Label(barra, text='Traducir a:', fg=e.BLANCO, bg=e.FONDO,
             font=e.FUENTE_NORMAL).pack(side='left', padx=(0, 6))
    seleccion = ttk.Combobox(barra, values=['Go', 'C', 'JavaScript'],
                             state='readonly', width=12, font=e.FUENTE_NORMAL)
    seleccion.set('Go')
    seleccion.pack(side='left', padx=(0, 15))

    # Botones principales de accion
    def crear_boton(texto, accion, principal=False):
        return tk.Button(barra, text=texto, command=accion,
                         bg=e.MORADO if principal else e.MORADO_SECUNDARIO,
                         fg=e.BLANCO, activebackground=e.MORADO_HOVER,
                         activeforeground=e.BLANCO, font=e.FUENTE_NORMAL,
                         relief='flat', cursor='hand2', padx=15, pady=7)

    b_analizar = crear_boton('Analizar y traducir', analizar, True)
    b_analizar.pack(side='left', padx=(0, 5))
    b_ejecutar = crear_boton('Ejecutar', ejecutar_traduccion, True)
    b_ejecutar.pack(side='left', padx=5)
    crear_boton('Limpiar', limpiar).pack(side='left', padx=5)

    # Selector de ejemplos para la exposicion
    tk.Label(barra, text='Ejemplos de prueba:', fg=e.TEXTO_SECUNDARIO, bg=e.FONDO,
             font=e.FUENTE_NORMAL).pack(side='left', padx=(25, 6))
    combo_ejemplos = ttk.Combobox(
        barra,
        values=list(EJEMPLOS_PRUEBA.keys()),
        state='readonly',
        width=30,
        font=e.FUENTE_NORMAL
    )
    combo_ejemplos.set('Cargar ejemplo de prueba...')
    combo_ejemplos.bind('<<ComboboxSelected>>', cargar_ejemplo_seleccionado)
    combo_ejemplos.pack(side='left')

    # Paneles divididos: Izquierda para entrada y Derecha para salidas
    zona = tk.PanedWindow(ventana, orient=tk.HORIZONTAL, sashwidth=7,
                          bg=e.FONDO, borderwidth=0, showhandle=False)
    zona.pack(fill='both', expand=True, padx=16, pady=(0, 10))

    izquierda = tk.Frame(zona, bg=e.PANEL, highlightthickness=1,
                         highlightbackground=e.BORDE)
    derecha = tk.PanedWindow(zona, orient=tk.VERTICAL, sashwidth=7,
                             bg=e.FONDO, borderwidth=0, showhandle=False)
    zona.add(izquierda, minsize=320, stretch='always')
    zona.add(derecha, minsize=400, stretch='always')

    superior = tk.Frame(derecha, bg=e.PANEL, highlightthickness=1,
                        highlightbackground=e.BORDE)
    inferior = tk.Frame(derecha, bg=e.PANEL, highlightthickness=1,
                        highlightbackground=e.BORDE)
    derecha.add(superior, minsize=220, stretch='always')
    derecha.add(inferior, minsize=140, stretch='always')

    def titulo_panel(panel, texto):
        tk.Label(panel, text=texto, bg=e.PANEL, fg=e.BLANCO,
                 font=e.FUENTE_SUBTITULO, anchor='w').pack(fill='x', padx=12, pady=(10, 6))

    def caja_codigo(panel, solo_lectura=False, color=None):
        caja = ScrolledText(panel, bg=e.CAJA, fg=color or e.BLANCO,
                            insertbackground=e.BLANCO, selectbackground=e.MORADO,
                            font=e.FUENTE_CODIGO, relief='flat', padx=12, pady=10,
                            wrap='none', undo=not solo_lectura)
        caja.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        if solo_lectura:
            caja.config(state='disabled')
        return caja

    # Panel Izquierdo: Codigo fuente
    titulo_panel(izquierda, 'Código Fuente')
    entrada = caja_codigo(izquierda)

    # Panel Superior Derecho: Barra de pestañas para las 5 fases del compilador
    barra_pestanas = tk.Frame(superior, bg=e.PANEL)
    barra_pestanas.pack(fill='x', padx=10, pady=(8, 4))

    botones_pestanas = {}

    def crear_pestana(clave, texto):
        btn = tk.Button(
            barra_pestanas,
            text=texto,
            command=lambda: cambiar_pestana(clave),
            bg=e.MORADO if clave == 'traducido' else e.MORADO_SECUNDARIO,
            fg=e.BLANCO if clave == 'traducido' else e.TEXTO_SECUNDARIO,
            activebackground=e.MORADO_HOVER,
            activeforeground=e.BLANCO,
            font=('Arial', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            padx=10,
            pady=5
        )
        btn.pack(side='left', padx=(0, 4))
        botones_pestanas[clave] = btn

    crear_pestana('traducido', 'Traducción')
    crear_pestana('simbolos', 'Tabla de Símbolos')
    crear_pestana('intermedio', 'Código Intermedio')
    crear_pestana('lexico', 'Léxico')
    crear_pestana('sintactico', 'Sintáctico')

    analisis = tk.Label(superior, text='Sin analizar.', bg=e.PANEL,
                        fg=e.TEXTO_SECUNDARIO, font=e.FUENTE_NORMAL,
                        anchor='w', justify='left')
    analisis.pack(fill='x', padx=12, pady=(2, 6))
    traducido = caja_codigo(superior, solo_lectura=True)

    # Panel Inferior Derecho: Consola de ejecucion real
    titulo_panel(inferior, 'Consola de Ejecución')
    consola = caja_codigo(inferior, solo_lectura=True, color=e.VERDE)

    barra_estado = tk.Label(ventana, text='Listo. Escribe tu código Python o selecciona un ejemplo de prueba.',
                            bg=e.HEADER, fg=e.TEXTO_SECUNDARIO,
                            anchor='w', padx=12, pady=7, font=e.FUENTE_NORMAL)
    barra_estado.pack(fill='x', side='bottom')

    # Cerramos sin dejar el programa esperando tareas como loco
    def cerrar():
        tareas.shutdown(wait=False, cancel_futures=True)
        ventana.destroy()

    ventana.protocol('WM_DELETE_WINDOW', cerrar)
    ventana.mainloop()
