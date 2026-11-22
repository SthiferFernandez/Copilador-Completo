# COMPILADOR DIDÁCTICO UNIFICADO

import ast
import json
import re

# Esta clase guarda los errores con mensajes amigables y sugerencias prácticas
# para no espantar al usuario con las excepciones feas de Python jajaj
class ErrorAnalisis(ValueError):
    def __init__(self, tipo, linea, mensaje, sugerencia=''):
        self.tipo = tipo  # 'léxico', 'sintáctico' o 'semántico'
        self.linea = linea
        self.mensaje = mensaje
        self.sugerencia = sugerencia
        super().__init__(mensaje)

    def mostrar(self):
        texto = f'ERROR {self.tipo.upper()}\n\nLínea {self.linea}: {self.mensaje}'
        if self.sugerencia:
            texto += f'\n\nCómo corregirlo: {self.sugerencia}'
        texto += '\n\nCorrige el error y vuelve a presionar Analizar y traducir.'
        return texto

class Token:
    def __init__(self, tipo, valor, linea, columna):
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
        self.columna = columna

    def __repr__(self):
        return f"Token({self.tipo}, {repr(self.valor)}, L:{self.linea}, C:{self.columna})"


PALABRAS_RESERVADAS = {
    'if': 'PALABRA_RESERVADA',
    'else': 'PALABRA_RESERVADA',
    'elif': 'PALABRA_RESERVADA',
    'while': 'PALABRA_RESERVADA',
    'print': 'FUNCION_PRINT',
    'and': 'OP_LOGICO',
    'or': 'OP_LOGICO',
    'not': 'OP_LOGICO',
    'True': 'BOOLEANO',
    'False': 'BOOLEANO',
    'pass': 'PALABRA_RESERVADA',
}

PATRONES_LEXICOS = [
    ('ESPACIO', r'[ \t]+'),
    ('COMENTARIO', r'#[^\n]*'),
    ('SALTO_LINEA', r'\n'),
    ('DECIMAL', r'\d+\.\d+'),
    ('ENTERO', r'\d+'),
    ('CADENA', r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')'),
    ('OP_POTENCIA', r'\*\*'),
    ('OP_DIVISION_ENTERA', r'//'),
    ('OP_ASIG_COMPUESTA', r'(\+=|-=|\*=|/=|%=)'),
    ('OP_COMPARACION', r'(==|!=|<=|>=|<|>)'),
    ('OP_ASIGNACION', r'='),
    ('OP_ARITMETICO', r'[\+\-\*/%]'),
    ('DELIMITADOR', r'[\(\):,]'),
    ('IDENTIFICADOR', r'[a-zA-Z_][a-zA-Z0-9_]*'),
]


def analizar_lexico(codigo):
    # Recorremos el codigo buscando patrones en orden de prioridad
    tokens = []
    lineas = codigo.split('\n')
    regex_combinada = '|'.join(f'(?P<{nombre}>{patron})' for nombre, patron in PATRONES_LEXICOS)

    for num_linea, linea_texto in enumerate(lineas, start=1):
        posicion = 0
        longitud = len(linea_texto)

        while posicion < longitud:
            match = re.compile(regex_combinada).match(linea_texto, posicion)
            if not match:
                char_invalido = linea_texto[posicion]
                raise ErrorAnalisis(
                    'léxico',
                    num_linea,
                    f"Carácter no reconocido o inválido: '{char_invalido}'.",
                    f"Elimina o corrige el símbolo en la columna {posicion + 1}."
                )

            tipo = match.lastgroup
            lexema = match.group(tipo)
            columna = posicion + 1
            posicion = match.end()

            # Saltamos comentarios y espacios porque solo sirven para humanos
            if tipo in ('ESPACIO', 'COMENTARIO'):
                continue

            if tipo == 'IDENTIFICADOR':
                if lexema in PALABRAS_RESERVADAS:
                    tokens.append(Token(PALABRAS_RESERVADAS[lexema], lexema, num_linea, columna))
                else:
                    tokens.append(Token('IDENTIFICADOR', lexema, num_linea, columna))
            elif tipo == 'CADENA':
                tokens.append(Token('CADENA', lexema[1:-1], num_linea, columna))
            elif tipo == 'ENTERO':
                tokens.append(Token('ENTERO', int(lexema), num_linea, columna))
            elif tipo == 'DECIMAL':
                tokens.append(Token('DECIMAL', float(lexema), num_linea, columna))
            else:
                tokens.append(Token(tipo, lexema, num_linea, columna))

    return tokens


def formatear_reporte_lexico(tokens):
    # Genera la tabla para mostrar en la pestaña de la interfaz
    if not tokens:
        return "No se encontraron tokens."
    lineas = []
    lineas.append("=" * 70)
    lineas.append(" FASE 1: REPORTE DEL ANALIZADOR LÉXICO")
    lineas.append("=" * 70)
    lineas.append(f"{'#':<4} | {'LÍNEA':<6} | {'COL':<4} | {'TIPO DE TOKEN':<22} | {'LEXEMA / VALOR'}")
    lineas.append("-" * 70)
    for i, tok in enumerate(tokens, start=1):
        val_str = repr(tok.valor) if isinstance(tok.valor, str) else str(tok.valor)
        if len(val_str) > 28:
            val_str = val_str[:25] + "..."
        lineas.append(f"{i:<4} | {tok.linea:<6} | {tok.columna:<4} | {tok.tipo:<22} | {val_str}")
    lineas.append("-" * 70)
    lineas.append(f"Total de tokens identificados: {len(tokens)}")
    lineas.append("=" * 70)
    return "\n".join(lineas)


#ANALIZADOR SINTÁCTICO
def explicar_sintaxis(error, codigo):
    mensaje = error.msg
    linea = error.lineno or '?'
    lineas = codigo.splitlines()
    texto_linea = lineas[linea - 1].strip() if isinstance(linea, int) and linea <= len(lineas) else ''

    if "expected ':'" in mensaje:
        return ErrorAnalisis('sintáctico', linea,
                             "Faltan los dos puntos (:) al final de la instrucción.",
                             f"Agrega ':' al final de: {texto_linea}")
    if 'expected an indented block' in mensaje:
        return ErrorAnalisis('sintáctico', linea,
                             'Falta un bloque con sangría debajo de la instrucción.',
                             'Escribe la instrucción dentro del bloque usando 4 espacios.')
    if 'was never closed' in mensaje or 'unexpected EOF' in mensaje:
        return ErrorAnalisis('sintáctico', linea,
                             'Hay un paréntesis, corchete o comillas sin cerrar.',
                             'Comprueba que cada apertura tenga su cierre correspondiente.')
    if 'unexpected indent' in mensaje or 'unindent does not match' in mensaje:
        return ErrorAnalisis('sintáctico', linea,
                             'La sangría (indentación) está desalineada.',
                             'Revisa los espacios al principio de esta línea.')
    if 'invalid syntax' in mensaje:
        return ErrorAnalisis('sintáctico', linea,
                             'La instrucción no cumple con las reglas sintácticas.',
                             f'Revisa cómo está escrita esta línea: {texto_linea}')
    return ErrorAnalisis('sintáctico', linea, mensaje, f'Revisa esta línea: {texto_linea}')


def parsear_codigo(codigo):
    try:
        return ast.parse(codigo)
    except SyntaxError as error:
        raise explicar_sintaxis(error, codigo) from error


def generar_arbol_sintactico_visual(nodo, prefijo='', es_ultimo=True):
    # Genera la estructura en arbol con rayitas ASCII
    lineas = []
    marcador = '└── ' if es_ultimo else '├── '
    nuevo_prefijo = prefijo + ('    ' if es_ultimo else '│   ')

    if isinstance(nodo, ast.Module):
        descripcion = "Programa (Módulo Principal)"
    elif isinstance(nodo, ast.Assign):
        var_nom = nodo.targets[0].id if nodo.targets and isinstance(nodo.targets[0], ast.Name) else 'var'
        descripcion = f"Asignación (Línea {nodo.lineno}) → Variable: '{var_nom}'"
    elif isinstance(nodo, ast.AugAssign):
        var_nom = nodo.target.id if isinstance(nodo.target, ast.Name) else 'var'
        descripcion = f"Asignación Compuesta (Línea {nodo.lineno}) → Variable: '{var_nom}', Op: {type(nodo.op).__name__}"
    elif isinstance(nodo, ast.If):
        descripcion = f"Estructura Condicional IF (Línea {nodo.lineno})"
    elif isinstance(nodo, ast.While):
        descripcion = f"Bucle WHILE (Línea {nodo.lineno})"
    elif isinstance(nodo, ast.Expr) and isinstance(nodo.value, ast.Call):
        func_nom = nodo.value.func.id if isinstance(nodo.value.func, ast.Name) else 'llamada'
        descripcion = f"Llamada a Función '{func_nom}' (Línea {nodo.lineno})"
    elif isinstance(nodo, ast.BinOp):
        simbolos = {ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/',
                    ast.FloorDiv: '//', ast.Mod: '%', ast.Pow: '**'}
        op = simbolos.get(type(nodo.op), type(nodo.op).__name__)
        descripcion = f"Operación Binaria ({op})"
    elif isinstance(nodo, ast.UnaryOp):
        descripcion = f"Operación Unaria ({type(nodo.op).__name__})"
    elif isinstance(nodo, ast.Compare):
        descripcion = "Comparación Relacional"
    elif isinstance(nodo, ast.BoolOp):
        op = "AND" if isinstance(nodo.op, ast.And) else "OR"
        descripcion = f"Operación Lógica ({op})"
    elif isinstance(nodo, ast.Constant):
        descripcion = f"Constante Literal: {repr(nodo.value)} ({type(nodo.value).__name__})"
    elif isinstance(nodo, ast.Name):
        descripcion = f"Identificador: '{nodo.id}'"
    elif isinstance(nodo, ast.Pass):
        descripcion = "Instrucción PASS"
    else:
        descripcion = f"Nodo ({type(nodo).__name__})"

    if not prefijo:
        lineas.append(descripcion)
    else:
        lineas.append(prefijo + marcador + descripcion)

    hijos = []
    if isinstance(nodo, ast.Module):
        hijos = nodo.body
    elif isinstance(nodo, ast.Assign):
        hijos = [nodo.value]
    elif isinstance(nodo, ast.AugAssign):
        hijos = [nodo.value]
    elif isinstance(nodo, ast.If):
        hijos = [nodo.test] + nodo.body + (nodo.orelse if nodo.orelse else [])
    elif isinstance(nodo, ast.While):
        hijos = [nodo.test] + nodo.body
    elif isinstance(nodo, ast.Expr) and isinstance(nodo.value, ast.Call):
        hijos = nodo.value.args
    elif isinstance(nodo, ast.BinOp):
        hijos = [nodo.left, nodo.right]
    elif isinstance(nodo, ast.UnaryOp):
        hijos = [nodo.operand]
    elif isinstance(nodo, ast.Compare):
        hijos = [nodo.left] + nodo.comparators
    elif isinstance(nodo, ast.BoolOp):
        hijos = nodo.values

    for i, hijo in enumerate(hijos):
        ultimo = (i == len(hijos) - 1)
        sub_prefijo = nuevo_prefijo if prefijo else ''
        lineas.append(generar_arbol_sintactico_visual(hijo, sub_prefijo, ultimo))

    return "\n".join(lineas)


def formatear_reporte_sintactico(arbol):
    lineas = []
    lineas.append("=" * 70)
    lineas.append(" FASE 2: REPORTE DEL ANALIZADOR SINTÁCTICO")
    lineas.append("=" * 70)
    lineas.append("Estructura jerárquica del programa validada correctamente:")
    lineas.append("-" * 70)
    lineas.append(generar_arbol_sintactico_visual(arbol))
    lineas.append("=" * 70)
    return "\n".join(lineas)


# TABLA DE SÍMBOLOS
class Simbolo:
    def __init__(self, nombre, tipo, valor_inicial, linea_declaracion, ambito='global'):
        self.nombre = nombre
        self.tipo = tipo  # 'int', 'float64', 'string', 'bool'
        self.valor_inicial = valor_inicial
        self.linea_declaracion = linea_declaracion
        self.lineas_uso = [linea_declaracion]
        self.ambito = ambito

    def registrar_uso(self, linea):
        if linea not in self.lineas_uso:
            self.lineas_uso.append(linea)


class TablaSimbolos:
    def __init__(self):
        self.simbolos = {}

    def insertar(self, nombre, tipo, valor_inicial, linea, ambito='global'):
        if nombre not in self.simbolos:
            self.simbolos[nombre] = Simbolo(nombre, tipo, valor_inicial, linea, ambito)
            return self.simbolos[nombre]
        else:
            self.simbolos[nombre].registrar_uso(linea)
            return self.simbolos[nombre]

    def buscar(self, nombre):
        return self.simbolos.get(nombre)

    def existe(self, nombre):
        return nombre in self.simbolos

    def obtener_tipo(self, nombre):
        sim = self.buscar(nombre)
        return sim.tipo if sim else None

    def registrar_uso(self, nombre, linea):
        if nombre in self.simbolos:
            self.simbolos[nombre].registrar_uso(linea)

    def obtener_variables_tipo_dict(self):
        return {k: v.tipo for k, v in self.simbolos.items()}

    def generar_reporte(self):
        if not self.simbolos:
            return "No se declararon variables (la tabla de símbolos está vacía)."
        lineas = []
        lineas.append("=" * 82)
        lineas.append(" FASE 3: TABLA DE SÍMBOLOS GENERADA POR EL COMPILADOR")
        lineas.append("=" * 82)
        lineas.append(f"{'IDENTIFICADOR':<16} | {'TIPO':<10} | {'ÁMBITO':<8} | {'LÍNEA DECL.':<12} | {'VALOR INICIAL':<16} | {'USOS EN LÍNEAS'}")
        lineas.append("-" * 82)
        for nombre, sim in self.simbolos.items():
            usos_str = ", ".join(str(l) for l in sim.lineas_uso)
            val_str = repr(sim.valor_inicial) if isinstance(sim.valor_inicial, str) else str(sim.valor_inicial)
            if len(val_str) > 14:
                val_str = val_str[:12] + ".."
            lineas.append(f"{nombre:<16} | {sim.tipo:<10} | {sim.ambito:<8} | {sim.linea_declaracion:<12} | {val_str:<16} | {usos_str}")
        lineas.append("-" * 82)
        lineas.append(f"Total de símbolos registrados: {len(self.simbolos)}")
        lineas.append("=" * 82)
        return "\n".join(lineas)


# ANALIZADOR SEMÁNTICO 
class AnalizadorSemantico:
    def __init__(self):
        self.tabla = TablaSimbolos()

    def error(self, linea, mensaje, sugerencia=''):
        raise ErrorAnalisis('semántico', linea, mensaje, sugerencia)

    def evaluar_tipo_expresion(self, nodo):
        linea = getattr(nodo, 'lineno', '?')

        if isinstance(nodo, ast.Constant):
            valor = nodo.value
            if isinstance(valor, bool):
                return 'bool', valor
            if isinstance(valor, str):
                return 'string', valor
            if isinstance(valor, int):
                return 'int', valor
            if isinstance(valor, float):
                return 'float64', valor
            self.error(linea, f"El tipo '{type(valor).__name__}' no está permitido.")

        if isinstance(nodo, ast.Name):
            nombre = nodo.id
            if not self.tabla.existe(nombre):
                self.error(
                    linea,
                    f"La variable '{nombre}' se está utilizando antes de ser asignada.",
                    f"Declara primero '{nombre} = ...' antes de usarla en la línea {linea}."
                )
            self.tabla.registrar_uso(nombre, linea)
            return self.tabla.obtener_tipo(nombre), None

        if isinstance(nodo, ast.UnaryOp):
            tipo_op, _ = self.evaluar_tipo_expresion(nodo.operand)
            if isinstance(nodo.op, ast.Not):
                if tipo_op != 'bool':
                    self.error(linea, "El operador 'not' solo se puede aplicar a valores booleanos.",
                               "Verifica que la condición sea verdadera o falsa.")
                return 'bool', None
            if isinstance(nodo.op, (ast.USub, ast.UAdd)):
                if tipo_op not in ('int', 'float64'):
                    self.error(linea, "Los operadores de signo (+, -) solo se aplican a números.")
                return tipo_op, None
            self.error(linea, "Operación unaria no permitida.")

        if isinstance(nodo, ast.BinOp):
            tipo_izq, val_izq = self.evaluar_tipo_expresion(nodo.left)
            tipo_der, val_der = self.evaluar_tipo_expresion(nodo.right)

            # Suma de cadenas = concatenacion
            if isinstance(nodo.op, ast.Add):
                if tipo_izq == 'string' and tipo_der == 'string':
                    val_res = (val_izq + val_der) if (val_izq is not None and val_der is not None) else None
                    return 'string', val_res
                if tipo_izq == 'string' or tipo_der == 'string':
                    self.error(
                        linea,
                        f"Incompatibilidad de tipos: no puedes sumar un '{tipo_izq}' con un '{tipo_der}'.",
                        "Para unir textos, ambas partes deben ser de tipo string."
                    )

            if tipo_izq not in ('int', 'float64') or tipo_der not in ('int', 'float64'):
                self.error(
                    linea,
                    f"Operación matemática inválida entre '{tipo_izq}' y '{tipo_der}'.",
                    "Ambos operandos deben ser números (enteros o decimales)."
                )

            if isinstance(nodo.op, (ast.Div, ast.Pow)):
                return 'float64', None

            if tipo_izq == 'float64' or tipo_der == 'float64':
                return 'float64', None

            return 'int', None

        if isinstance(nodo, ast.Compare):
            tipo_izq, _ = self.evaluar_tipo_expresion(nodo.left)
            for comp in nodo.comparators:
                tipo_der, _ = self.evaluar_tipo_expresion(comp)
                if (tipo_izq == 'string' and tipo_der != 'string') or (tipo_der == 'string' and tipo_izq != 'string'):
                    self.error(linea, f"No puedes comparar tipos incompatibles ('{tipo_izq}' con '{tipo_der}').")
                tipo_izq = tipo_der
            return 'bool', None

        if isinstance(nodo, ast.BoolOp):
            for valor in nodo.values:
                tipo, _ = self.evaluar_tipo_expresion(valor)
                if tipo != 'bool':
                    self.error(linea, "Los operadores 'and' y 'or' requieren expresiones booleanas.")
            return 'bool', None

        self.error(linea, f"Expresión no soportada semánticamente: {type(nodo).__name__}.")

    def analizar_instrucciones(self, instrucciones):
        for inst in instrucciones:
            linea = getattr(inst, 'lineno', '?')

            if isinstance(inst, ast.Assign):
                if len(inst.targets) != 1 or not isinstance(inst.targets[0], ast.Name):
                    self.error(linea, "Solo se permite asignar una variable a la vez (ej: x = 10).")
                nombre = inst.targets[0].id
                tipo, valor_inicial = self.evaluar_tipo_expresion(inst.value)

                if self.tabla.existe(nombre):
                    tipo_existente = self.tabla.obtener_tipo(nombre)
                    if tipo_existente != tipo:
                        self.error(
                            linea,
                            f"Cambio de tipo no permitido: '{nombre}' es de tipo '{tipo_existente}' y no puede pasar a '{tipo}'.",
                            "En lenguajes compilados estrictos como Go o C, una variable conserva su tipo declarado."
                        )
                    self.tabla.registrar_uso(nombre, linea)
                else:
                    self.tabla.insertar(nombre, tipo, valor_inicial if valor_inicial is not None else "(calculado)", linea)

            elif isinstance(inst, ast.AugAssign):
                if not isinstance(inst.target, ast.Name):
                    self.error(linea, "La asignación compuesta requiere una variable a la izquierda.")
                nombre = inst.target.id
                if not self.tabla.existe(nombre):
                    self.error(linea, f"La variable '{nombre}' no está declarada.")
                tipo_var = self.tabla.obtener_tipo(nombre)
                tipo_val, _ = self.evaluar_tipo_expresion(inst.value)
                if tipo_var != tipo_val:
                    self.error(linea, f"No se puede operar '{tipo_var}' con '{tipo_val}' en asignación compuesta.")
                self.tabla.registrar_uso(nombre, linea)

            elif isinstance(inst, ast.Expr) and isinstance(inst.value, ast.Call):
                llamada = inst.value
                if not isinstance(llamada.func, ast.Name) or llamada.func.id != 'print':
                    self.error(linea, "Por los momentos la única función estándar soportada es print().")
                for arg in llamada.args:
                    self.evaluar_tipo_expresion(arg)

            elif isinstance(inst, (ast.If, ast.While)):
                tipo_cond, _ = self.evaluar_tipo_expresion(inst.test)
                if tipo_cond != 'bool':
                    self.error(linea, f"La condición debe ser booleana, no '{tipo_cond}'.")
                self.analizar_instrucciones(inst.body)
                if isinstance(inst, ast.If) and inst.orelse:
                    self.analizar_instrucciones(inst.orelse)
                elif isinstance(inst, ast.While) and inst.orelse:
                    self.error(linea, "El bloque 'else' en bucles while no está admitido.")

            elif isinstance(inst, ast.Pass):
                pass
            else:
                self.error(linea, f"Instrucción no soportada: {type(inst).__name__}.")

    def analizar(self, arbol):
        self.analizar_instrucciones(arbol.body)
        return self.tabla


#GENERADOR DE CÓDIGO INTERMEDIO (TAC - THREE-ADDRESS CODE)
class GeneradorTAC:
    def __init__(self):
        self.contador_temporales = 0
        self.contador_etiquetas = 0
        self.instrucciones_tac = []
        self.cuadruplos = []

    def nuevo_temporal(self):
        t = f"t{self.contador_temporales}"
        self.contador_temporales += 1
        return t

    def nueva_etiqueta(self):
        l = f"L{self.contador_etiquetas}"
        self.contador_etiquetas += 1
        return l

    def agregar_tac(self, texto):
        self.instrucciones_tac.append(texto)

    def agregar_cuadruplo(self, op, arg1='-', arg2='-', res='-'):
        self.cuadruplos.append((op, str(arg1), str(arg2), str(res)))

    def procesar_expresion(self, nodo):
        if isinstance(nodo, ast.Constant):
            return repr(nodo.value) if isinstance(nodo.value, str) else str(nodo.value)
        if isinstance(nodo, ast.Name):
            return nodo.id

        if isinstance(nodo, ast.UnaryOp):
            operando = self.procesar_expresion(nodo.operand)
            temp = self.nuevo_temporal()
            simbolo_op = '-' if isinstance(nodo.op, ast.USub) else ('+' if isinstance(nodo.op, ast.UAdd) else 'not')
            self.agregar_tac(f"{temp} = {simbolo_op} {operando}")
            self.agregar_cuadruplo(simbolo_op, operando, '-', temp)
            return temp

        if isinstance(nodo, ast.BinOp):
            izq = self.procesar_expresion(nodo.left)
            der = self.procesar_expresion(nodo.right)
            simbolos = {ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/',
                        ast.FloorDiv: '//', ast.Mod: '%', ast.Pow: '**'}
            op = simbolos.get(type(nodo.op), '+')
            temp = self.nuevo_temporal()
            self.agregar_tac(f"{temp} = {izq} {op} {der}")
            self.agregar_cuadruplo(op, izq, der, temp)
            return temp

        if isinstance(nodo, ast.Compare):
            simbolos = {ast.Eq: '==', ast.NotEq: '!=', ast.Gt: '>',
                        ast.GtE: '>=', ast.Lt: '<', ast.LtE: '<='}
            izq = self.procesar_expresion(nodo.left)
            resultados = []
            for op_nodo, comp in zip(nodo.ops, nodo.comparators):
                der = self.procesar_expresion(comp)
                op_str = simbolos.get(type(op_nodo), '==')
                temp = self.nuevo_temporal()
                self.agregar_tac(f"{temp} = {izq} {op_str} {der}")
                self.agregar_cuadruplo(op_str, izq, der, temp)
                resultados.append(temp)
                izq = der
            return resultados[0] if len(resultados) == 1 else resultados[-1]

        if isinstance(nodo, ast.BoolOp):
            simbolo = 'and' if isinstance(nodo.op, ast.And) else 'or'
            valores = [self.procesar_expresion(p) for p in nodo.values]
            temp_actual = valores[0]
            for v in valores[1:]:
                temp_nuevo = self.nuevo_temporal()
                self.agregar_tac(f"{temp_nuevo} = {temp_actual} {simbolo} {v}")
                self.agregar_cuadruplo(simbolo.upper(), temp_actual, v, temp_nuevo)
                temp_actual = temp_nuevo
            return temp_actual

        return "(expresion)"

    def procesar_bloque(self, instrucciones):
        for inst in instrucciones:
            if isinstance(inst, ast.Assign):
                var_nombre = inst.targets[0].id
                val = self.procesar_expresion(inst.value)
                self.agregar_tac(f"{var_nombre} = {val}")
                self.agregar_cuadruplo('=', val, '-', var_nombre)

            elif isinstance(inst, ast.AugAssign):
                var_nombre = inst.target.id
                val = self.procesar_expresion(inst.value)
                ops = {ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/', ast.Mod: '%'}
                op_str = ops.get(type(inst.op), '+')
                temp = self.nuevo_temporal()
                self.agregar_tac(f"{temp} = {var_nombre} {op_str} {val}")
                self.agregar_cuadruplo(op_str, var_nombre, val, temp)
                self.agregar_tac(f"{var_nombre} = {temp}")
                self.agregar_cuadruplo('=', temp, '-', var_nombre)

            elif isinstance(inst, ast.Expr) and isinstance(inst.value, ast.Call):
                llamada = inst.value
                func_nom = llamada.func.id if isinstance(llamada.func, ast.Name) else 'print'
                args_temporales = [self.procesar_expresion(arg) for arg in llamada.args]
                for arg in args_temporales:
                    self.agregar_tac(f"param {arg}")
                    self.agregar_cuadruplo('PARAM', arg, '-', '-')
                self.agregar_tac(f"call {func_nom}, {len(args_temporales)}")
                self.agregar_cuadruplo('CALL', func_nom, len(args_temporales), '-')

            elif isinstance(inst, ast.If):
                cond = self.procesar_expresion(inst.test)
                lbl_else = self.nueva_etiqueta()
                lbl_fin = self.nueva_etiqueta()

                self.agregar_tac(f"if_false {cond} goto {lbl_else}")
                self.agregar_cuadruplo('IF_FALSE', cond, '-', lbl_else)

                self.procesar_bloque(inst.body)

                if inst.orelse:
                    self.agregar_tac(f"goto {lbl_fin}")
                    self.agregar_cuadruplo('GOTO', '-', '-', lbl_fin)
                    self.agregar_tac(f"label {lbl_else}")
                    self.agregar_cuadruplo('LABEL', '-', '-', lbl_else)
                    self.procesar_bloque(inst.orelse)
                    self.agregar_tac(f"label {lbl_fin}")
                    self.agregar_cuadruplo('LABEL', '-', '-', lbl_fin)
                else:
                    self.agregar_tac(f"label {lbl_else}")
                    self.agregar_cuadruplo('LABEL', '-', '-', lbl_else)

            elif isinstance(inst, ast.While):
                lbl_inicio = self.nueva_etiqueta()
                lbl_fin = self.nueva_etiqueta()

                self.agregar_tac(f"label {lbl_inicio}")
                self.agregar_cuadruplo('LABEL', '-', '-', lbl_inicio)

                cond = self.procesar_expresion(inst.test)
                self.agregar_tac(f"if_false {cond} goto {lbl_fin}")
                self.agregar_cuadruplo('IF_FALSE', cond, '-', lbl_fin)

                self.procesar_bloque(inst.body)
                self.agregar_tac(f"goto {lbl_inicio}")
                self.agregar_cuadruplo('GOTO', '-', '-', lbl_inicio)

                self.agregar_tac(f"label {lbl_fin}")
                self.agregar_cuadruplo('LABEL', '-', '-', lbl_fin)

            elif isinstance(inst, ast.Pass):
                self.agregar_tac("nop")
                self.agregar_cuadruplo('NOP', '-', '-', '-')


def generar_codigo_intermedio(arbol):
    generador = GeneradorTAC()
    generador.procesar_bloque(arbol.body)
    return generador


def formatear_reporte_intermedio(generador):
    lineas = []
    lineas.append("=" * 72)
    lineas.append(" FASE 4: CÓDIGO INTERMEDIO")
    lineas.append("=" * 72)
    lineas.append("Instrucciones TAC generadas (descomposición en pasos atómicos):")
    lineas.append("-" * 72)
    if not generador.instrucciones_tac:
        lineas.append("(No se generaron instrucciones intermedias)")
    else:
        for i, inst in enumerate(generador.instrucciones_tac, start=1):
            lineas.append(f"{i:03d} |  {inst}")

    lineas.append("\n" + "=" * 72)
    lineas.append(" TABLA DE CUÁDRUPLOS")
    lineas.append("=" * 72)
    lineas.append(f"{'#':<4} | {'OPERADOR':<12} | {'ARG 1':<14} | {'ARG 2':<14} | {'RESULTADO'}")
    lineas.append("-" * 72)
    for i, c in enumerate(generador.cuadruplos):
        lineas.append(f"{i:<4} | {c[0]:<12} | {c[1]:<14} | {c[2]:<14} | {c[3]}")
    lineas.append("=" * 72)
    return "\n".join(lineas)


#GENERADOR DE CÓDIGO DESTINO
class GeneradorCodigoDestino:
    def __init__(self, destino='Go', tabla_simbolos=None):
        self.destino = destino
        self.tabla_simbolos = tabla_simbolos
        self.tipos = {}
        self.declaradas = set()
        self.usa_math = False

    def error(self, nodo, mensaje):
        raise ErrorAnalisis('semántico', getattr(nodo, 'lineno', '?'), mensaje)

    def expresion(self, nodo):
        if isinstance(nodo, ast.Constant):
            valor = nodo.value
            if isinstance(valor, bool):
                return ('true' if valor else 'false'), 'bool'
            if isinstance(valor, str):
                return json.dumps(valor, ensure_ascii=False), 'string'
            if isinstance(valor, (int, float)):
                return repr(valor), 'float64' if isinstance(valor, float) else 'int'
            self.error(nodo, 'Ese valor no está permitido.')

        if isinstance(nodo, ast.Name):
            if nodo.id not in self.tipos:
                self.error(nodo, f"La variable '{nodo.id}' no existe o no ha sido inicializada.")
            return nodo.id, self.tipos[nodo.id]

        if isinstance(nodo, ast.UnaryOp):
            valor, tipo = self.expresion(nodo.operand)
            if isinstance(nodo.op, ast.Not):
                if tipo != 'bool':
                    self.error(nodo, 'not necesita una condición booleana.')
                return ('!' + valor), 'bool'
            if isinstance(nodo.op, (ast.USub, ast.UAdd)) and tipo in ('int', 'float64'):
                return ('-' if isinstance(nodo.op, ast.USub) else '+') + valor, tipo
            self.error(nodo, 'Operación unaria no permitida.')

        if isinstance(nodo, ast.BinOp):
            izq, ti = self.expresion(nodo.left)
            der, td = self.expresion(nodo.right)
            simbolos = {ast.Add: '+', ast.Sub: '-', ast.Mult: '*',
                        ast.Div: '/', ast.FloorDiv: '//', ast.Mod: '%', ast.Pow: '**'}
            op = simbolos.get(type(nodo.op))
            if op is None:
                self.error(nodo, 'No se reconoce ese operador.')
            if op == '+' and ti == td == 'string':
                if self.destino == 'C':
                    self.error(nodo, 'La concatenación de textos todavía no está implementada en C.')
                return f'({izq} + {der})', 'string'
            if ti not in ('int', 'float64') or td not in ('int', 'float64'):
                self.error(nodo, 'Las operaciones matemáticas necesitan números.')
            tipo = 'float64' if 'float64' in (ti, td) or op in ('/', '**') else 'int'

            if self.destino == 'Go':
                if op == '**':
                    self.usa_math = True
                    return f'math.Pow(float64({izq}), float64({der}))', 'float64'
                if op == '//':
                    if ti == td == 'int':
                        return f'({izq} / {der})', 'int'
                    self.usa_math = True
                    return f'math.Floor(float64({izq}) / float64({der}))', 'float64'
                if op == '/' or tipo == 'float64':
                    if ti == 'int':
                        izq = f'float64({izq})'
                    if td == 'int':
                        der = f'float64({der})'
                if op == '%' and tipo == 'float64':
                    self.usa_math = True
                    return f'math.Mod({izq}, {der})', 'float64'
                return f'({izq} {op} {der})', tipo

            if self.destino == 'C':
                if op == '**':
                    self.usa_math = True
                    return f'pow((double)({izq}), (double)({der}))', 'float64'
                if op == '//':
                    self.usa_math = True
                    valor = f'floor((double)({izq}) / (double)({der}))'
                    return (f'(int){valor}', 'int') if ti == td == 'int' else (valor, 'float64')
                if op == '/':
                    return f'((double)({izq}) / (double)({der}))', 'float64'
                if op == '%' and tipo == 'float64':
                    self.usa_math = True
                    return f'fmod((double)({izq}), (double)({der}))', 'float64'
                return f'({izq} {op} {der})', tipo

            if op == '//':
                return f'Math.floor({izq} / {der})', tipo
            if op == '**':
                return f'Math.pow({izq}, {der})', tipo
            return f'({izq} {op} {der})', tipo

        if isinstance(nodo, ast.Compare):
            operadores = {ast.Eq: '==', ast.NotEq: '!=', ast.Gt: '>',
                          ast.GtE: '>=', ast.Lt: '<', ast.LtE: '<='}
            anterior, _ = self.expresion(nodo.left)
            partes = []
            for op, valor in zip(nodo.ops, nodo.comparators):
                siguiente, _ = self.expresion(valor)
                simbolo = operadores.get(type(op))
                if not simbolo:
                    self.error(nodo, 'Comparación no permitida.')
                partes.append(f'({anterior} {simbolo} {siguiente})')
                anterior = siguiente
            return ' && '.join(partes), 'bool'

        if isinstance(nodo, ast.BoolOp):
            simbolo = ' && ' if isinstance(nodo.op, ast.And) else ' || '
            valores = []
            for parte in nodo.values:
                resultado, tipo = self.expresion(parte)
                if tipo != 'bool':
                    self.error(parte, 'and y or necesitan condiciones.')
                valores.append(resultado)
            return '(' + simbolo.join(valores) + ')', 'bool'

        self.error(nodo, 'Esta expresión todavía no está soportada.')

    def bloque(self, instrucciones, nivel=1):
        lineas = []
        esp = '    ' * nivel
        for instruccion in instrucciones:
            if isinstance(instruccion, ast.Assign):
                if len(instruccion.targets) != 1 or not isinstance(instruccion.targets[0], ast.Name):
                    self.error(instruccion, 'Solo se permite asignar una variable a la vez.')
                nombre = instruccion.targets[0].id
                valor, tipo = self.expresion(instruccion.value)
                nueva = nombre not in self.declaradas
                if nueva:
                    self.declaradas.add(nombre)
                    self.tipos[nombre] = tipo
                elif self.tipos[nombre] != tipo:
                    self.error(instruccion, f"No puedes cambiar el tipo de '{nombre}' de {self.tipos[nombre]} a {tipo}.")

                if self.destino == 'Go':
                    linea = f'{nombre} := {valor}' if nueva else f'{nombre} = {valor}'
                elif self.destino == 'C':
                    tipos_c = {'int': 'int', 'float64': 'double', 'bool': 'bool', 'string': 'char *'}
                    linea = f'{tipos_c[tipo]}{nombre if tipo == "string" else " " + nombre} = {valor};' if nueva else f'{nombre} = {valor};'
                else:
                    linea = f'let {nombre} = {valor};' if nueva else f'{nombre} = {valor};'
                lineas.append(esp + linea)

            elif isinstance(instruccion, ast.AugAssign):
                if not isinstance(instruccion.target, ast.Name):
                    self.error(instruccion, 'La asignación no es válida.')
                nombre = instruccion.target.id
                if nombre not in self.tipos:
                    self.error(instruccion, f"La variable '{nombre}' no existe.")
                valor, tipo = self.expresion(instruccion.value)
                if tipo != self.tipos[nombre]:
                    self.error(instruccion, 'Los tipos de esa operación no coinciden.')
                ops = {ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/', ast.Mod: '%'}
                op = ops.get(type(instruccion.op))
                if not op:
                    self.error(instruccion, 'Operador no permitido.')
                lineas.append(esp + f'{nombre} {op}= {valor}' + (';' if self.destino in ('JavaScript', 'C') else ''))

            elif isinstance(instruccion, ast.Expr) and isinstance(instruccion.value, ast.Call):
                llamada = instruccion.value
                if not isinstance(llamada.func, ast.Name) or llamada.func.id != 'print' or llamada.keywords:
                    self.error(instruccion, 'Por ahora solo puedes llamar a print().')
                args = [self.expresion(x)[0] for x in llamada.args]
                if self.destino == 'Go':
                    lineas.append(esp + f'fmt.Println({", ".join(args)})')
                elif self.destino == 'C':
                    tipos = [self.expresion(x)[1] for x in llamada.args]
                    formatos = {'int': '%d', 'float64': '%g', 'string': '%s', 'bool': '%s'}
                    formato = ' '.join(formatos[t] for t in tipos) + r'\n'
                    valores = [f'({a} ? "True" : "False")' if t == 'bool' else a for a, t in zip(args, tipos)]
                    parametros = ', ' + ', '.join(valores) if valores else ''
                    lineas.append(esp + f'printf("{formato}"{parametros});')
                else:
                    lineas.append(esp + f'console.log({", ".join(args)});')

            elif isinstance(instruccion, (ast.If, ast.While)):
                condicion, tipo = self.expresion(instruccion.test)
                if tipo != 'bool':
                    self.error(instruccion, 'La condición debe ser verdadera o falsa.')
                es_if = isinstance(instruccion, ast.If)
                if self.destino == 'Go':
                    prefijo = 'if ' if es_if else 'for '
                    lineas.append(esp + f'{prefijo}{condicion} {{')
                else:
                    prefijo = 'if' if es_if else 'while'
                    lineas.append(esp + f'{prefijo} ({condicion}) {{')
                lineas += self.bloque(instruccion.body, nivel + 1)
                lineas.append(esp + '}')
                if es_if and instruccion.orelse:
                    lineas[-1] = esp + '} else {'
                    lineas += self.bloque(instruccion.orelse, nivel + 1)
                    lineas.append(esp + '}')
                elif not es_if and instruccion.orelse:
                    self.error(instruccion, 'while con else todavía no se admite.')

            elif isinstance(instruccion, ast.Pass):
                lineas.append(esp + '// pass')
            else:
                self.error(instruccion, 'Esa instrucción todavía no se puede traducir.')
        return lineas


# EL COMPILADOR UNIFICADO (CLASE PRINCIPAL)
class Compilador:
    def __init__(self, destino='Go'):
        if destino not in ('Go', 'C', 'JavaScript'):
            raise ValueError('Elige Go, C o JavaScript.')
        self.destino = destino

    def compilar(self, codigo):
        # 1. Fase Léxica: convertimos el código en tokens
        tokens = analizar_lexico(codigo)
        reporte_lexico = formatear_reporte_lexico(tokens)

        # 2. Fase Sintáctica: verificamos la gramática y armamos el árbol AST
        arbol = parsear_codigo(codigo)
        reporte_sintactico = formatear_reporte_sintactico(arbol)

        # 3. Fase Semántica y 4. Tabla de Símbolos: chequeamos tipos y alcance
        analizador_sem = AnalizadorSemantico()
        tabla_simbolos = analizador_sem.analizar(arbol)
        reporte_tabla = tabla_simbolos.generar_reporte()

        # 5. Fase de Código Intermedio: TAC y cuádruplos
        generador_tac = generar_codigo_intermedio(arbol)
        reporte_intermedio = formatear_reporte_intermedio(generador_tac)

        # 6. Fase de Generación de Código Final
        generador_codigo = GeneradorCodigoDestino(self.destino, tabla_simbolos)
        lineas = generador_codigo.bloque(arbol.body)

        if self.destino == 'JavaScript':
            codigo_final = '\n'.join(lineas)
        elif self.destino == 'C':
            cabecera = ['#include <stdio.h>', '#include <stdbool.h>']
            if generador_codigo.usa_math:
                cabecera.append('#include <math.h>')
            codigo_final = '\n'.join(cabecera + ['', 'int main(void) {'] + lineas +
                                     ['    return 0;', '}', ''])
        else:  # Go
            imports = ['"fmt"'] if any('fmt.' in linea for linea in lineas) else []
            if generador_codigo.usa_math:
                imports.append('"math"')
            cabecera = ['package main', '']
            if len(imports) == 1:
                cabecera += [f'import {imports[0]}', '']
            elif imports:
                cabecera += ['import ('] + ['    ' + x for x in imports] + [')', '']
            codigo_final = '\n'.join(cabecera + ['func main() {'] + lineas + ['}', ''])

        return {
            'codigo_traducido': codigo_final,
            'variables': dict(generador_codigo.tipos),
            'tabla_simbolos': tabla_simbolos,
            'reporte_tabla': reporte_tabla,
            'tokens': tokens,
            'reporte_lexico': reporte_lexico,
            'arbol': arbol,
            'reporte_sintactico': reporte_sintactico,
            'generador_tac': generador_tac,
            'reporte_intermedio': reporte_intermedio
        }


# Funciones de conveniencia para la interfaz y scripts externos
def compilar_y_analizar_completo(codigo, destino='Go'):
    compilador = Compilador(destino)
    return compilador.compilar(codigo)


def analizar_y_traducir(codigo, destino='Go', devolver_variables=False, devolver_todo=False):
    datos = compilar_y_analizar_completo(codigo, destino)
    if devolver_todo:
        return datos
    if devolver_variables:
        return datos['codigo_traducido'], datos['variables']
    return datos['codigo_traducido']
