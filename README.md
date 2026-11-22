# COMPILADOR COMPLETO - DOCUMENTACIÓN TÉCNICA Y GUÍA DE PRUEBAS

**Proyecto:** Compilador Completo  
**Materia:** Compiladores / Teoría de Lenguajes de Programación  
**Entorno de Ejecución:** Python 3.12+, Go 1.20+, GCC (MSYS2)  
**Interfaz Gráfica:** Tkinter (Tema Personalizado Dark Purple / Violeta)

---

## 1. DESCRIPCIÓN GENERAL DEL PROYECTO

Este proyecto consiste en un compilador completo de 6 fases diseñado para procesar un subconjunto estricto y educativo del lenguaje Python, ejecutar un análisis exhaustivo en cada etapa formal de la teoría de compiladores, y finalmente traducir el programa a código compilable y ejecutable en Go (con soporte adicional para C y JavaScript).

El sistema cuenta con una interfaz gráfica interactiva diseñada con la paleta de colores personalizada del autor, que permite inspeccionar visualmente en pestañas independientes el resultado exacto producido por cada una de las fases del compilador, así como ejecutar el código traducido en tiempo real mediante un hilo secundario sin congelar la aplicación.

---

## 2. ARQUITECTURA DEL COMPILADOR UNIFICADO (compilador.py)

Todo el núcleo del compilador se encuentra combinado e integrado en un único archivo principal (compilador.py), organizado en 6 fases formales consecutivas coordinadas por la clase Compilador:

```
                 [Código Fuente en Python]
                             │
                             ▼
 ┌─────────────────────────────────────────────────────────┐
 │               COMPILADOR UNIFICADO                      │
 │                  (compilador.py)                        │
 │                                                         │
 │  [1. Analizador Léxico] ───────► Tokens                 │
 │            │                                            │
 │            ▼                                            │
 │  [2. Analizador Sintáctico] ───► Árbol Jerárquico (AST) │
 │            │                                            │
 │            ▼                                            │
 │  [3. Analizador Semántico] ───► Chequeo de Tipos        │
 │            │                              │             │
 │            │                              ▼             │
 │            ├───────────────────► [4. Tabla de Símbolos] │
 │            ▼                                            │
 │  [5. Código Intermedio] ───────► TAC y Cuádruplos       │
 │            │                                            │
 │            ▼                                            │
 │  [6. Generador Destino] ───────► Código compilable Go   │
 └───────────────────────────┬─────────────────────────────┘
                             │
                             ▼
       [Ejecución en Consola (ejecutor.py) - go run]
```

---

### Fase a: Analizador Léxico (Sección 1 en compilador.py)
* **Propósito:** Lee la secuencia de caracteres del código fuente y los agrupa en unidades léxicas significativas llamadas Tokens.
* **Mecanismo:** Utiliza expresiones regulares ordenadas por precedencia para identificar:
  - PALABRA_RESERVADA: if, else, elif, while, pass, etc.
  - FUNCION_PRINT: Llamada a salida estándar print.
  - BOOLEANO: Literales True, False.
  - IDENTIFICADOR: Variables y nombres ([a-zA-Z_][a-zA-Z0-9_]*).
  - ENTERO y DECIMAL: Literales numéricos enteros (\d+) y flotantes (\d+\.\d+).
  - CADENA: Cadenas delimitadas por comillas dobles o simples.
  - OP_ARITMETICO y OP_POTENCIA: +, -, *, /, //, %, **.
  - OP_ASIGNACION y OP_ASIG_COMPUESTA: =, +=, -=, *=, /=, %=.
  - OP_COMPARACION: ==, !=, <, >, <=, >=.
  - OP_LOGICO: and, or, not.
  - DELIMITADOR: (, ), :, ,.
* **Tratamiento de Errores Léxicos:** Si se detecta un símbolo no admitido en el alfabeto del lenguaje (por ejemplo $, @, ~), el analizador detiene el proceso y emite una excepción ErrorAnalisis('léxico', linea, ...) indicando la línea y columna exactas del fallo.

---

### Fase b: Analizador Sintáctico (Sección 2 en compilador.py)
* **Propósito:** Verifica que la secuencia de tokens cumpla con la gramática formal del lenguaje y construye la estructura jerárquica (Árbol Sintáctico Abstracto / AST).
* **Gramática EBNF Simplificada:**
  ```ebnf
  Programa       ::= Sentencia*
  Sentencia      ::= Asignacion | AsignacionComp | Condicional | Bucle | LlamadaPrint | 'pass'
  Asignacion     ::= IDENTIFICADOR '=' Expresion
  AsignacionComp ::= IDENTIFICADOR ('+=' | '-=' | '*=' | '/=' | '%=') Expresion
  Condicional    ::= 'if' Expresion ':' Bloque ('else' ':' Bloque)?
  Bucle          ::= 'while' Expresion ':' Bloque
  LlamadaPrint   ::= 'print' '(' (Expresion (',' Expresion)*)? ')'
  Expresion      ::= ExpLogica
  ExpLogica      ::= ExpRelacional (('and' | 'or') ExpRelacional)*
  ExpRelacional  ::= ExpAritmetica (('==' | '!=' | '<' | '<=' | '>' | '>=') ExpAritmetica)*
  ExpAritmetica  ::= Termino (('+' | '-') Termino)*
  Termino        ::= Factor (('*' | '/' | '//' | '%') Factor)*
  Factor         ::= ('+' | '-' | 'not')? Primario ('**' Factor)?
  Primario       ::= ENTERO | DECIMAL | CADENA | BOOLEANO | IDENTIFICADOR | '(' Expresion ')'
  ```
* **Salida Visual:** Genera una representación en árbol ASCII jerárquico que permite observar con total claridad los nodos padre e hijos del programa.

---

### Fase c: Analizador Semántico (Sección 4 en compilador.py)
* **Propósito:** Valida el significado y la coherencia lógica del programa según las reglas de los lenguajes fuertemente tipados.
* **Comprobaciones Realizadas:**
  1. **Uso previo a la definición:** Una variable no puede ser leída si no ha sido asignada previamente.
  2. **Compatibilidad estricta de tipos:**
     - La suma + entre dos cadenas realiza concatenación.
     - No se permite sumar string + int ni string + float64.
     - Operaciones como resta, multiplicación y división exigen operandos numéricos.
  3. **Inmutabilidad de tipos declarados:** Si una variable nace como int, no puede ser reasignada posteriormente a string (regla fundamental para compilar a Go/C).
  4. **Expresiones de control:** Las condiciones de sentencias if y bucles while deben evaluarse forzosamente a tipo booleano (bool).

---

### Fase d: Tabla de Símbolos (Sección 3 en compilador.py)
* **Propósito:** Estructura de datos central que almacena la información contextual de todos los identificadores declarados durante la compilación.
* **Atributos registrados por símbolo:**
  - Nombre: Identificador de la variable.
  - Tipo: Tipo estático inferido (int, float64, string, bool).
  - Ámbito: Alcance del símbolo (por defecto global).
  - Línea Declaración: Número de línea en el código fuente donde se introdujo.
  - Valor Inicial: Valor con el que se inicializó o etiqueta (calculado).
  - Líneas de Uso: Lista ordenada de todas las líneas del código donde la variable es consultada o modificada.

---

### Fase e: Generador de Código Intermedio (Sección 5 en compilador.py)
* **Propósito:** Transforma el árbol sintáctico en una representación lineal independiente de la máquina destino: Código de Tres Direcciones (TAC) y Tabla de Cuádruplos.
* **Convenciones:**
  - Temporales para cálculos atómicos: t0, t1, t2, ...
  - Etiquetas para saltos y control de flujo: L0, L1, L2, ...
  - Instrucciones soportadas:
    - Asignación simple: x = t0
    - Operación binaria: t0 = a + b
    - Salto condicional: if_false t1 goto L0
    - Salto incondicional: goto L1
    - Definición de etiqueta: label L0
    - Pasaje de parámetros y llamada: param x, call print, 1
  - Cuádruplos con formato estándar académico: (Operador, Argumento 1, Argumento 2, Resultado).

---

### Fase f: Generador de Código Destino (Sección 6 en compilador.py)
* **Lenguaje Principal: Go (Golang)**
  - Genera archivos válidos con package main.
  - Gestiona automáticamente las dependencias de importación ("fmt" para print, "math" para math.Pow, math.Floor, math.Mod).
  - Emite declaración rápida := en la primera aparición de la variable y asignación simple = en las subsiguientes.
  - Traduce los bucles while de Python a la instrucción canónica de Go for <condición> { ... }.
  - Asegura el casteo explícito de tipos en divisiones numéricas float64(a) / float64(b) para evitar pérdida de precisión no deseada.
* **Lenguajes Secundarios Soportados:**
  - **C:** Genera código estructurado con int main(void), #include <stdio.h>, #include <stdbool.h>, mapeando tipos a int, double, char* y llamadas printf.
  - **JavaScript:** Genera script modular compatible con navegadores y Node.js.

---

## 3. GUÍA DE CASOS DE PRUEBA (PLAN DE PRUEBAS PARA LA EXPOSICIÓN)

A continuación se detallan 6 casos de prueba diseñados específicamente para demostrar el funcionamiento de cada fase durante la presentación.

---

### Caso de Prueba 1: Operaciones Aritméticas y Variables
**Objetivo:** Demostrar el análisis léxico de números y operadores, la inferencia de tipos flotantes en divisiones, la generación de TAC y la salida compilada en Go.

* **Código Python de Entrada:**
```python
base = 10
altura = 5
area = (base * altura) / 2
print("El área calculada es:", area)
```

* **Tabla de Símbolos Generada:**
```
IDENTIFICADOR    | TIPO       | ÁMBITO   | LÍNEA DECL.  | VALOR INICIAL    | USOS EN LÍNEAS
----------------------------------------------------------------------------------
base             | int        | global   | 1            | 10               | 1, 3
altura           | int        | global   | 2            | 5                | 2, 3
area             | float64    | global   | 3            | '(calculado)'    | 3, 4
```

* **Código Intermedio (TAC):**
```
001 |  base = 10
002 |  altura = 5
003 |  t0 = base * altura
004 |  t1 = t0 / 2
005 |  area = t1
006 |  param "El área calculada es:"
007 |  param area
008 |  call print, 2
```

* **Código Traducido a Go:**
```go
package main

import "fmt"

func main() {
    base := 10
    altura := 5
    area := (float64((base * altura)) / float64(2))
    fmt.Println("El área calculada es:", area)
}
```

* **Resultado de Ejecución en Consola:**
```
El área calculada es: 25

Proceso terminado correctamente.
```

---

### Caso de Prueba 2: Estructuras Condicionales (If-Else) y Operadores Lógicos
**Objetivo:** Demostrar cómo se evalúan las condiciones booleanas, la generación de saltos if_false y goto en TAC, y su traducción a Go.

* **Código Python de Entrada:**
```python
edad = 20
tiene_cedula = True
if edad >= 18 and tiene_cedula:
    print("Acceso permitido: Es mayor de edad y tiene documento.")
else:
    print("Acceso denegado.")
```

* **Código Intermedio (TAC):**
```
001 |  edad = 20
002 |  tiene_cedula = True
003 |  t0 = edad >= 18
004 |  t1 = t0 and tiene_cedula
005 |  if_false t1 goto L0
006 |  param "Acceso permitido: Es mayor de edad y tiene documento."
007 |  call print, 1
008 |  goto L1
009 |  label L0
010 |  param "Acceso denegado."
011 |  call print, 1
012 |  label L1
```

* **Código Traducido a Go:**
```go
package main

import "fmt"

func main() {
    edad := 20
    tiene_cedula := true
    if ((edad >= 18) && tiene_cedula) {
        fmt.Println("Acceso permitido: Es mayor de edad y tiene documento.")
    } else {
        fmt.Println("Acceso denegado.")
    }
}
```

* **Resultado de Ejecución en Consola:**
```
Acceso permitido: Es mayor de edad y tiene documento.

Proceso terminado correctamente.
```

---

### Caso de Prueba 3: Bucles While y Acumuladores
**Objetivo:** Demostrar la traducción de bucles a la estructura de salto cíclico en TAC y su equivalencia con for en Go.

* **Código Python de Entrada:**
```python
contador = 1
total = 0
while contador <= 5:
    total += contador
    print("Sumando paso:", contador, "Total acumulado:", total)
    contador += 1
print("Suma final:", total)
```

* **Código Intermedio (TAC):**
```
001 |  contador = 1
002 |  total = 0
003 |  label L0
004 |  t0 = contador <= 5
005 |  if_false t0 goto L1
006 |  t1 = total + contador
007 |  total = t1
008 |  param "Sumando paso:"
009 |  param contador
010 |  param "Total acumulado:"
011 |  param total
012 |  call print, 4
013 |  t2 = contador + 1
014 |  contador = t2
015 |  goto L0
016 |  label L1
017 |  param "Suma final:"
018 |  param total
019 |  call print, 2
```

* **Código Traducido a Go:**
```go
package main

import "fmt"

func main() {
    contador := 1
    total := 0
    for (contador <= 5) {
        total += contador
        fmt.Println("Sumando paso:", contador, "Total acumulado:", total)
        contador += 1
    }
    fmt.Println("Suma final:", total)
}
```

* **Resultado de Ejecución en Consola:**
```
Sumando paso: 1 Total acumulado: 1
Sumando paso: 2 Total acumulado: 3
Sumando paso: 3 Total acumulado: 6
Sumando paso: 4 Total acumulado: 10
Sumando paso: 5 Total acumulado: 15
Suma final: 15

Proceso terminado correctamente.
```

---

### Caso de Prueba 4: Cadenas de Texto y Concatenación
**Objetivo:** Verificar la concatenación de cadenas y el soporte de tipos textuales y booleanos.

* **Código Python de Entrada:**
```python
saludo = "Hola compañeros"
materia = "Compiladores"
mensaje = saludo + " - Exposición de " + materia
activo = True
print(mensaje)
print("Estado activo:", activo)
```

* **Código Traducido a Go:**
```go
package main

import "fmt"

func main() {
    saludo := "Hola compañeros"
    materia := "Compiladores"
    mensaje := ((saludo + " - Exposición de ") + materia)
    activo := true
    fmt.Println(mensaje)
    fmt.Println("Estado activo:", activo)
}
```

* **Resultado de Ejecución en Consola:**
```
Hola compañeros - Exposición de Compiladores
Estado activo: true

Proceso terminado correctamente.
```

---

### Caso de Prueba 5: Detección de Error Léxico
**Objetivo:** Demostrar la robustez del analizador léxico al rechazar caracteres ilegales en el código.

* **Código Python de Entrada:**
```python
precio = 100
total = precio $ 2
print(total)
```

* **Diagnóstico Generado por el Compilador:**
```
ERROR LÉXICO

Línea 2: Carácter no reconocido o inválido: '$'.

Cómo corregirlo: Elimina o corrige el símbolo en la columna 16.

Corrige el error y vuelve a presionar Analizar y traducir.
```

---

### Caso de Prueba 6: Detección de Error Semántico
**Objetivo:** Demostrar que el analizador semántico previene operaciones inválidas antes de emitir código final.

* **Código Python de Entrada:**
```python
nombre = "Juan"
edad = 25
resultado = nombre + edad
print(resultado)
```

* **Diagnóstico Generado por el Compilador:**
```
ERROR SEMÁNTICO

Línea 3: Incompatibilidad de tipos: no puedes sumar un 'string' con un 'int'.

Cómo corregirlo: Para unir textos, ambas partes deben ser de tipo string.

Corrige el error y vuelve a presionar Analizar y traducir.
```

---

## 4. MANUAL DE USO DE LA INTERFAZ GRÁFICA

1. **Ejecución de la Aplicación:**
   Abra la terminal en el directorio del proyecto y ejecute:
   ```powershell
   python main.py
   ```
2. **Carga Rápida de Pruebas:**
   En la barra superior, haga clic en el desplegable **"Ejemplos de prueba"** y seleccione cualquiera de los 6 casos preparados para cargarlo inmediatamente sin necesidad de escribir.
3. **Selección del Lenguaje de Salida:**
   Elija **Go** (predeterminado), **C** o **JavaScript** en el selector "Traducir a:".
4. **Análisis y Compilación:**
   Haga clic en el botón morado **"Analizar y traducir"**. El compilador procesará las 6 fases de manera instantánea.
5. **Inspección de Fases:**
   Use las pestañas superiores derechas para alternar entre:
   - `Traducción`: Código fuente final generado y resumen de variables.
   - `Tabla de Símbolos`: Tabla estructurada con identificadores, tipos, ámbitos y líneas de uso.
   - `Código Intermedio`: Código de tres direcciones y matriz de cuádruplos.
   - `Léxico`: Desglose completo de cada token reconocido con su línea y columna.
   - `Sintáctico`: Representación gráfica en árbol de la sintaxis abstracta.
6. **Ejecución:**
   Haga clic en **"Ejecutar"**. El compilador invocará `go run` en segundo plano y mostrará la salida en color verde brillante en la consola inferior.
