from pathlib import Path
import shutil
import subprocess
import tempfile
import webbrowser


def crear_javascript(codigo, carpeta):
    # JS no va a la consola de Go/C: armamos una pagina para verlo en el navegador
    # Uno guarda el codigo .js y el otro lo muestra en el navegador
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    js = carpeta / 'programa.js'
    html = carpeta / 'programa.html'
    js.write_text(codigo, encoding='utf-8')
    html.write_text('''<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><title>Resultado de JavaScript</title>
<style>body{background:#140b24;color:white;font:18px Consolas;padding:30px}
pre{background:#11091f;border:1px solid #673ab7;padding:20px;white-space:pre-wrap}</style>
</head>
<body><h2>Consola de JavaScript</h2><pre id="resultado"></pre>
<script>
const caja = document.getElementById('resultado');
const original = console.log;
console.log = (...datos) => {
    caja.textContent += datos.join(' ') + '\\n';
    original(...datos);
};
window.addEventListener('error', e => caja.textContent += 'Error: ' + e.message + '\\n');
</script>
<script src="programa.js"></script>
</body></html>''', encoding='utf-8')
    return js, html


def ejecutar(codigo, destino):
    # Este decide si abrimos JS en el navegador o corremos Go/C en consola
    if destino == 'JavaScript':
        carpeta = Path.home() / 'TraductorPythonGo' / 'salida'
        js, html = crear_javascript(codigo, carpeta)
        webbrowser.open(html.resolve().as_uri())
        return f'Archivo generado: {js}\nPágina abierta: {html}\nEl resultado aparece en el navegador.'

    # Si elegiste C toca compilar primero, porque C no corre asi porque si
    if destino == 'C':
        compilador = shutil.which('gcc') or shutil.which('clang')
        if not compilador:
            raise RuntimeError('No encuentro GCC ni Clang. Instala GCC (por ejemplo MSYS2) y comprueba: gcc --version')
        # Carpeta temporal para no llenar tu PC de archivos de prueba
        with tempfile.TemporaryDirectory(prefix='codigo_c_') as carpeta:
            archivo = Path(carpeta) / 'main.c'
            programa = Path(carpeta) / ('programa.exe' if __import__('os').name == 'nt' else 'programa')
            archivo.write_text(codigo, encoding='utf-8')
            comando = [compilador, str(archivo), '-o', str(programa), '-lm']
            try:
                # GCC hace el ejecutable; si hay error lo mandamos a la pantalla
                compilacion = subprocess.run(comando, cwd=carpeta, capture_output=True,
                                             text=True, timeout=30, encoding='utf-8', errors='replace')
                if compilacion.returncode:
                    raise RuntimeError('Error al compilar C:\n' + compilacion.stdout + compilacion.stderr)
                proceso = subprocess.run([str(programa)], cwd=carpeta, capture_output=True,
                                         text=True, timeout=10, encoding='utf-8', errors='replace')
            except subprocess.TimeoutExpired as error:
                raise RuntimeError('La compilación o ejecución de C tardó demasiado y se detuvo.') from error
            resultado = proceso.stdout + proceso.stderr
            if proceso.returncode:
                raise RuntimeError('Error al ejecutar C:\n' + resultado)
            return (resultado or '(El programa no imprimió nada)\n') + '\nProceso terminado correctamente.'

    if destino != 'Go':
        raise ValueError('Elige Go, C o JavaScript.')
    # Si Go no esta instalado, de nada sirve darle a ejecutar jajaj
    if not shutil.which('go'):
        raise RuntimeError('Go no está instalado o no está en el PATH. Prueba: go version')
    with tempfile.TemporaryDirectory(prefix='codigo_go_') as carpeta:
        archivo = Path(carpeta) / 'main.go'
        archivo.write_text(codigo, encoding='utf-8')
        try:
            # Aqui si corre Go de verdad, el Python solo lo usamos para traducir
            proceso = subprocess.run(
                ['go', 'run', 'main.go'], cwd=carpeta,
                capture_output=True, text=True, timeout=30,
                encoding='utf-8', errors='replace'
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError('El programa tardó más de 30 segundos y fue detenido.') from error
        salida = proceso.stdout + proceso.stderr
        if proceso.returncode:
            raise RuntimeError('Error al ejecutar Go:\n' + salida)
        return (salida or '(El programa no imprimió nada)\n') + '\nProceso terminado correctamente.'
