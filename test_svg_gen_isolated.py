import svgwrite
import xml.etree.ElementTree as ET
import os
import base64
from PIL import Image, ImageDraw # For the test block
# Removed: from svgwrite import utils
# No "from svgwrite import xml" here, will try direct svgwrite.xml.Raw

# This is the simplified create_final_svg function
def create_final_svg(
    output_svg_path,
    background_svg_path,
    foreground_png_path,
    fg_width,
    fg_height,
    svg_width=None,
    svg_height=None
):
    try:
        canvas_width = svg_width if svg_width is not None else fg_width
        canvas_height = svg_height if svg_height is not None else fg_height

        dwg = svgwrite.Drawing(
            output_svg_path,
            size=(f"{canvas_width}px", f"{canvas_height}px"),
            profile='full',
            viewBox=f"0 0 {canvas_width} {canvas_height}"
        )
        print(f"Creando SVG final en: {output_svg_path}")
        print(f"  Dimensiones del lienzo SVG: {canvas_width}x{canvas_height}")

        # --- Procesamiento del Fondo SVG ---
        print(f"  Procesando fondo SVG desde: {background_svg_path}")
        background_group = dwg.g(id="background_group_from_file")
        try:
            tree = ET.parse(background_svg_path)
            background_root = tree.getroot()

            bg_defs = background_root.find('{http://www.w3.org/2000/svg}defs')
            if bg_defs is not None:
                for style_element in bg_defs.findall('{http://www.w3.org/2000/svg}style'):
                    if style_element.text:
                        dwg.defs.add(dwg.style(content=style_element.text))
                        print("    <style> del fondo SVG añadido a <defs>.")

            for child_element in background_root:
                tag_name = child_element.tag.split('}', 1)[-1] if '}' in child_element.tag else child_element.tag
                if tag_name not in ['defs', 'metadata', 'title']:
                    if tag_name == 'style' and child_element.text:
                         dwg.defs.add(dwg.style(content=child_element.text))
                         print("    <style> raíz del fondo SVG añadido a <defs>.")
                    elif tag_name != 'style': # Process other non-style, non-defs elements
                        try:
                            element_str = ET.tostring(child_element, encoding='unicode').strip()
                            element_str = element_str.replace('<?xml version=\'1.0\' encoding=\'us-ascii\'? M>', '')
                            element_str = element_str.replace('<?xml version="1.0" ?>', '')
                            element_str = element_str.replace('<?xml version=\'1.0\' encoding=\'us-ascii\'?>', '')

                            # Attempt to use svgwrite.xml.Raw directly
                            background_group.add(svgwrite.xml.Raw(text=element_str))
                        except Exception as e_add_element:
                            print(f"    Error al añadir elemento del fondo con svgwrite.xml.Raw: {child_element.tag}, {e_add_element}")
            dwg.add(background_group)
            print(f"    Contenido del fondo SVG incrustado en el grupo.")

        except ET.ParseError as e_parse:
            print(f"  ERROR: No se pudo parsear el SVG de fondo: {e_parse}")
            print(f"  Como fallback, intentando añadir el SVG de fondo como una imagen enlazada.")
            try:
                dwg.add(dwg.image(href=background_svg_path, insert=(0,0), size=(f"{canvas_width}px", f"{canvas_height}px")))
                print(f"    SVG de fondo enlazado como imagen (fallback).")
            except Exception as e_fallback_img:
                print(f"    ERROR: Fallback de enlazar SVG de fondo como imagen también falló: {e_fallback_img}")
                return False
        except Exception as e_bg_general:
            print(f"  Error general procesando el SVG de fondo: {e_bg_general}")
            # Continue to add foreground

        # --- Imagen de primer plano ---
        print(f"  Añadiendo imagen PNG de primer plano: {foreground_png_path}")
        try:
            with open(foreground_png_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            mime_type = "image/png"
            if foreground_png_path.lower().endswith((".jpg", ".jpeg")):
                mime_type = "image/jpeg"
            href_data_uri = f"data:{mime_type};base64,{encoded_string}"
            dwg.add(dwg.image(
                href=href_data_uri,
                insert=(0, 0),
                size=(f"{fg_width}px", f"{fg_height}px")
            ))
            print(f"    Imagen de primer plano incrustada como Base64.")
        except FileNotFoundError:
            print(f"    Error: Archivo de imagen de primer plano no encontrado: {foreground_png_path}")
            return False
        except Exception as e_fg:
            print(f"    Error al procesar o añadir imagen de primer plano: {e_fg}")
            return False

        dwg.save(pretty=True)
        print(f"SVG final guardado exitosamente en {output_svg_path}")
        return True

    except Exception as e_main:
        print(f"Error fatal al crear el SVG final: {e_main}")
        return False

# --- Bloque de pruebas (identical to the one intended for svg_generator.py) ---
if __name__ == '__main__':
    print("\n--- Probando Generación de SVG Final (desde test_svg_gen_isolated.py) ---")

    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    if not current_script_dir:
        current_script_dir = os.getcwd()
    test_output_dir = os.path.join(current_script_dir, "test_output_svg_gen_v2")

    if not os.path.exists(test_output_dir):
        os.makedirs(test_output_dir)
        print(f"Directorio de prueba creado: {test_output_dir}")

    bg_svg_path = os.path.join(test_output_dir, "my_background.svg")
    bg_svg_content = r"""<?xml version="1.0" encoding="UTF-8"?>
    <svg width="500px" height="500px" viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <style type="text/css">
          .red_class { fill: red; }
          .blue_stroke { stroke: blue; stroke-width: 2px; fill: none; }
        </style>
      </defs>
      <g id="actual_background_content">
        <path d="M100,100 L300,100 L200,300 z" class="red_class" />
        <rect x="50" y="50" width="400" height="400" class="blue_stroke" />
        <circle cx="250" cy="250" r="30" fill="yellow" />
        <text x="10" y="20" font-family="Verdana" font-size="15">Fondo SVG</text>
      </g>
    </svg>
    """
    with open(bg_svg_path, "w", encoding="utf-8") as f:
        f.write(bg_svg_content)
    print(f"SVG de fondo de prueba creado/actualizado en: {bg_svg_path}")

    fg_image_path = os.path.join(test_output_dir, "foreground_image.png")
    fg_w, fg_h = 300, 200
    try:
        img_fg = Image.new("RGBA", (fg_w, fg_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img_fg)
        draw.ellipse((50, 50, 150, 150), fill=(0, 255, 0, 180))
        draw.text((10, 10), "PNG FG Test", fill="black")
        img_fg.save(fg_image_path, "PNG")
        print(f"Imagen PNG de prueba creada/actualizada en: {fg_image_path}")
    except ImportError:
        print("ADVERTENCIA: Pillow (PIL) no está instalado.")
        if not os.path.exists(fg_image_path):
            print(f"ERROR: Crea {fg_image_path} o instala Pillow.")
        else:
            print(f"Usando PNG de prueba existente: {fg_image_path}")
            try:
                with Image.open(fg_image_path) as img_temp:
                    fg_w, fg_h = img_temp.size
            except Exception as e_open_img:
                print(f"No se pudo abrir PNG existente: {e_open_img}")
    except Exception as e_pil:
        print(f"Error al crear imagen de prueba con Pillow: {e_pil}")

    final_svg_output_path = os.path.join(test_output_dir, "final_composite.svg")
    print(f"Intentando generar SVG final con: bg='{bg_svg_path}', fg='{fg_image_path}'")
    success = create_final_svg(
        output_svg_path=final_svg_output_path,
        background_svg_path=bg_svg_path,
        foreground_png_path=fg_image_path,
        fg_width=fg_w,
        fg_height=fg_h,
        svg_width=500,
        svg_height=500
    )

    if success and os.path.exists(final_svg_output_path):
        print(f"\nSVG final de prueba generado exitosamente en: {final_svg_output_path}")
        with open(final_svg_output_path, "r", encoding="utf-8") as f_out:
            print("\nPrimeras líneas del SVG generado:")
            for _ in range(15): # Print first 15 lines to see more context
                line = f_out.readline().strip()
                if line: print(f"  {line}")
                else: break
    else:
        print("\nFalló la generación del SVG final de prueba.")
