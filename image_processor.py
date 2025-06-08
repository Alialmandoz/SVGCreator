import os
import subprocess
import shutil
import tempfile # Para nombres de archivo temporales en iteraciones

# Constante para el tamaño objetivo en bytes (700 KB * 1024 bytes/KB)
TARGET_SIZE_BYTES = 700 * 1024
# Margen aceptable por encima del objetivo (ej. 5%)
ACCEPTABLE_MARGIN_BYTES = TARGET_SIZE_BYTES * 0.05 # 35KB para 700KB -> hasta 735KB

# Parámetros para la optimización iterativa
INITIAL_QUALITY_MIN = 65
INITIAL_QUALITY_MAX = 80
QUALITY_STEP_DOWN = 5  # Cuánto reducir la calidad en cada iteración
MIN_QUALITY_ALLOWED = 40 # Calidad mínima absoluta
MAX_ITERATIONS = 5       # Máximo de intentos de optimización

def optimize_image_iteratively(input_image_path, output_dir="optimized_images", pngquant_exe_rel_path="tools/pngquant.exe"):
    """
    Optimiza una imagen PNG usando pngquant, intentando iterativamente
    alcanzar TARGET_SIZE_BYTES ajustando la calidad.
    """
    try:
        project_root = os.getcwd() # Asume que el script se ejecuta desde la raíz del proyecto
        pngquant_exe_abs_path = os.path.join(project_root, pngquant_exe_rel_path)

        if not os.path.exists(pngquant_exe_abs_path):
            pngquant_exe_abs_path = shutil.which("pngquant")
            if not pngquant_exe_abs_path:
                print(f"Error: pngquant.exe no encontrado en '{os.path.join(project_root, pngquant_exe_rel_path)}' ni en el PATH.")
                return None

        original_file_size_bytes = os.path.getsize(input_image_path)
        filename = os.path.basename(input_image_path)
        name_part, ext_part = os.path.splitext(filename)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        final_output_path = os.path.join(output_dir, f"{name_part}_optimized{ext_part}")

        # Si la imagen original ya está dentro del objetivo + margen, podemos copiarla
        if original_file_size_bytes <= TARGET_SIZE_BYTES + ACCEPTABLE_MARGIN_BYTES:
            print(f"Info: '{filename}' ({original_file_size_bytes / 1024:.2f} KB) ya está dentro o cerca del objetivo ({ (TARGET_SIZE_BYTES + ACCEPTABLE_MARGIN_BYTES) / 1024:.0f} KB).")
            # Considerar una optimización suave aquí si se desea, por ahora copiamos.
            # Ejemplo de optimización suave:
            # command_gentle = [pngquant_exe_abs_path, "--force", "--quality=85-95", "--skip-if-larger",
            #                     "--output", final_output_path, input_image_path]
            # try:
            #     subprocess.run(command_gentle, check=False, capture_output=True, text=True)
            #     if os.path.exists(final_output_path) and os.path.getsize(final_output_path) < original_file_size_bytes:
            #         print(f"Optimización suave aplicada. Nuevo tamaño: {os.path.getsize(final_output_path) / 1024:.2f} KB")
            #         return final_output_path
            # except Exception:
            #     pass # Fallback a copiar si la optimización suave falla

            shutil.copy(input_image_path, final_output_path)
            print(f"Imagen copiada a: '{final_output_path}'")
            return final_output_path

        current_quality_min = INITIAL_QUALITY_MIN
        current_quality_max = INITIAL_QUALITY_MAX
        best_attempt_file_path = None # Ruta al archivo del mejor intento
        best_attempt_file_size = float('inf') # Tamaño del mejor intento

        # Lista para rastrear archivos temporales creados que no sean el 'best_attempt_file_path'
        temp_files_to_clean = []

        for i in range(MAX_ITERATIONS):
            print(f"\nIteración {i+1}/{MAX_ITERATIONS}: Calidad objetivo {current_quality_min}-{current_quality_max}")
            
            # Usar un nombre de archivo temporal para la salida de esta iteración
            temp_fd, current_iteration_output_path = tempfile.mkstemp(suffix="_iter.png", prefix=f"{name_part}_q{current_quality_min}-", dir=output_dir)
            os.close(temp_fd)

            command = [
                pngquant_exe_abs_path,
                "--force",
                f"--quality={current_quality_min}-{current_quality_max}",
                "--skip-if-larger",
                # Considerar "--speed=1" para mejor calidad/compresión, pero más lento
                "--output", current_iteration_output_path,
                input_image_path # Siempre optimizar desde el original para esta estrategia
            ]

            try:
                process = subprocess.run(command, check=False, capture_output=True, text=True, timeout=60) # Timeout de 60s
                
                if process.stdout: print(f"  pngquant stdout: {process.stdout.strip()}")
                if process.stderr: print(f"  pngquant stderr: {process.stderr.strip()}") # stderr puede tener info útil

                if process.returncode == 0 and os.path.exists(current_iteration_output_path) and os.path.getsize(current_iteration_output_path) > 0 :
                    current_iteration_file_size = os.path.getsize(current_iteration_output_path)
                    print(f"  Resultado iteración: {current_iteration_file_size / 1024:.2f} KB")

                    # Si este es el mejor hasta ahora (más pequeño Y mejor que el original si el original era el "mejor")
                    if current_iteration_file_size < best_attempt_file_size:
                        if best_attempt_file_path and best_attempt_file_path != current_iteration_output_path: # Si había un 'mejor' anterior y no es este mismo
                            temp_files_to_clean.append(best_attempt_file_path) # Añadir el antiguo 'mejor' a la limpieza
                        best_attempt_file_path = current_iteration_output_path
                        best_attempt_file_size = current_iteration_file_size
                    elif current_iteration_output_path != best_attempt_file_path: # No fue mejor y no es el 'mejor' actual
                         temp_files_to_clean.append(current_iteration_output_path)


                    if current_iteration_file_size <= TARGET_SIZE_BYTES + ACCEPTABLE_MARGIN_BYTES:
                        print(f"  ¡Objetivo ({ (TARGET_SIZE_BYTES + ACCEPTABLE_MARGIN_BYTES) / 1024:.0f} KB) alcanzado ({current_iteration_file_size / 1024:.2f} KB)!")
                        # Mover el archivo exitoso al nombre final
                        if os.path.exists(final_output_path) and final_output_path != best_attempt_file_path: os.remove(final_output_path)
                        shutil.move(best_attempt_file_path, final_output_path)
                        # Limpiar otros archivos temporales de iteraciones
                        for temp_file in temp_files_to_clean:
                            if os.path.exists(temp_file) and temp_file != final_output_path:
                                try: os.remove(temp_file)
                                except OSError: pass # Ignorar si no se puede borrar por alguna razón
                        return final_output_path
                else:
                    print(f"  pngquant no generó archivo de salida válido (código: {process.returncode}). Puede ser por --skip-if-larger.")
                    if os.path.exists(current_iteration_output_path): # Si creó un archivo (quizás vacío o erróneo), borrarlo
                        os.remove(current_iteration_output_path)
                    # Si es la primera iteración y falla, el "mejor" sigue siendo el original
                    if i == 0 and best_attempt_file_size == float('inf'):
                        best_attempt_file_path = None # Indicar que no hay un intento optimizado válido aún
                        best_attempt_file_size = original_file_size_bytes # El original es el "mejor" hasta ahora
            
            except subprocess.TimeoutExpired:
                print(f"  Timeout durante la ejecución de pngquant en la iteración {i+1}.")
                if os.path.exists(current_iteration_output_path): os.remove(current_iteration_output_path)
            except Exception as e_iter:
                print(f"  Error en la iteración de pngquant: {e_iter}")
                if os.path.exists(current_iteration_output_path): os.remove(current_iteration_output_path)

            current_quality_min -= QUALITY_STEP_DOWN
            current_quality_max -= QUALITY_STEP_DOWN
            if current_quality_min < MIN_QUALITY_ALLOWED:
                print("  Alcanzada calidad mínima permitida.")
                break
        
        # Fin del bucle de iteraciones
        print("\nFin de las iteraciones de optimización.")
        final_decision_path = None
        if best_attempt_file_path and best_attempt_file_size < original_file_size_bytes:
            print(f"Mejor intento optimizado ({best_attempt_file_size / 1024:.2f} KB) es mejor que el original. Usando este.")
            final_decision_path = best_attempt_file_path
        else: # Si no hubo mejora o no hubo 'best_attempt_file_path' válido de optimización
            print("No se encontró una optimización mejor que el original o que cumpliera el objetivo. Copiando original.")
            # Si 'best_attempt_file_path' existe y no es el original, es un temp que no sirvió.
            if best_attempt_file_path and os.path.exists(best_attempt_file_path) and best_attempt_file_path != input_image_path:
                temp_files_to_clean.append(best_attempt_file_path)
            final_decision_path = input_image_path # Usar el original

        # Mover/copiar el archivo decidido al path final
        if final_decision_path == input_image_path:
            if os.path.exists(final_output_path) and not os.path.samefile(input_image_path, final_output_path) : os.remove(final_output_path)
            if not os.path.exists(final_output_path) or not os.path.samefile(input_image_path, final_output_path):
                 shutil.copy(input_image_path, final_output_path)
        elif os.path.exists(final_decision_path): # Es un archivo optimizado temporal
            if os.path.exists(final_output_path) and final_output_path != final_decision_path: os.remove(final_output_path)
            shutil.move(final_decision_path, final_output_path)
        
        # Limpiar archivos temporales restantes
        for temp_file in temp_files_to_clean:
            if os.path.exists(temp_file) and temp_file != final_output_path:
                try: os.remove(temp_file)
                except OSError: pass
        
        if os.path.exists(final_output_path):
            print(f"Archivo final guardado en: {final_output_path} (Tamaño: {os.path.getsize(final_output_path)/1024:.2f} KB)")
            return final_output_path
        else:
            print("Error: No se pudo determinar el archivo final.")
            return None

    except Exception as e:
        print(f"Ocurrió un error inesperado en optimize_image_iteratively: {e}")
        return None

# --- Bloque de pruebas ---
if __name__ == '__main__':
    # Reemplaza con una ruta a una imagen PNG grande para probar
    test_image_for_iteration = "ruta/a/tu/imagen_muy_grande_para_iterar.png" # ej. una de 2MB o más
    # test_image_for_iteration = "ruta/a/tu/imagen_ya_pequena.png" # ej. una de 500KB

    print("\n--- Probando optimización iterativa ---")
    if os.path.exists(test_image_for_iteration):
        # Asegúrate que pngquant.exe está en tools/ o en el PATH
        output_test_dir = "test_output/iterative_main_test"
        if os.path.exists(output_test_dir): # Limpiar directorio de prueba anterior
            shutil.rmtree(output_test_dir)

        optimized_path_iter = optimize_image_iteratively(
            test_image_for_iteration,
            output_dir=output_test_dir 
        )
        if optimized_path_iter and os.path.exists(optimized_path_iter):
            print(f"\nResultado final de optimización iterativa: {optimized_path_iter} (Tamaño: {os.path.getsize(optimized_path_iter) / 1024:.2f} KB)")
        else:
            print(f"\nFalló la optimización iterativa o no se generó archivo final en '{output_test_dir}'.")
    else:
        print(f"Archivo de prueba para iteración no encontrado: {test_image_for_iteration}")