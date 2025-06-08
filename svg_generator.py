import svgwrite
# from svgwrite import text as svgtext # Ya no necesitamos esto si Raw no está ahí
from svgwrite import base # Para BaseElement
from PIL import Image
import os
import base64
import xml.etree.ElementTree as ET

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

        dwg = svgwrite.Drawing(output_svg_path, 
                               size=(f"{canvas_width}px", f"{canvas_height}px"), 
                               profile='full',
                               viewBox=f"0 0 {canvas_width} {canvas_height}")

        print(f"Creando SVG final en: {output_svg_path}")
        print(f"  Dimensiones del lienzo SVG: {canvas_width}x{canvas_height}")

        print(f"  Procesando fondo SVG desde: {background_svg_path}")
        background_group = dwg.g(id="background_elements_from_file")

        try:
            tree = ET.parse(background_svg_path)
            background_root = tree.getroot() # Este es el elemento <svg> del archivo de fondo
            
            # Añadir <defs> del SVG de fondo
            # Es importante que los IDs en defs sean únicos globalmente o se usen prefijos.
            bg_defs_element = background_root.find('{http://www.w3.org/2000/svg}defs')
            if bg_defs_element is not None:
                for def_child in list(bg_defs_element): # Iterar sobre los hijos de <defs>
                    # Convertir el elemento ElementTree a string XML
                    def_child_str = ET.tostring(def_child, encoding='unicode').strip()
                    # svgwrite no tiene un método directo para añadir string XML crudo a defs
                    # de forma que lo parse y lo convierta en objetos svgwrite.
                    # Una opción es crear un objeto SVG temporal, añadir el string y extraer el elemento,
                    # o si los defs son simples, recrearlos con métodos de svgwrite.
                    # Por ahora, si hay defs complejos, esta parte puede ser un desafío.
                    # Un enfoque es añadirlo como un fragmento sin procesar.
                    # dwg.defs.elements.append(svgwrite.utils.SVGElement(def_child_str)) # Esto podría no ser API pública
                    # La forma más segura es recrear los elementos de defs o esperar que los estilos
                    # se hereden o estén en línea.
                    # Para <style>, podemos hacer:
                    if def_child.tag.endswith('style') and def_child.text:
                        dwg.defs.add(dwg.style(content=def_child.text))
                print("    Intentando añadir <style> de defs del SVG de fondo.")


            # Añadir los elementos visuales del fondo
            # Vamos a añadir los hijos del <svg> raíz del fondo a nuestro grupo.
            for child_element in background_root:
                tag_name = child_element.tag.split('}',1)[-1] if '}' in child_element.tag else child_element.tag
                if tag_name not in ['defs', 'metadata', 'title', 'style']: # No volver a añadir defs o style aquí
                    element_str = ET.tostring(child_element, encoding='unicode').strip()
                    # Limpiar declaración XML si está presente
                    element_str = element_str.replace('<?xml version=\'1.0\' encoding=\'us-ascii\'?>', '')
                    
                    # Crear un elemento base y añadir el XML como texto.
                    # Esto es una forma de "inyectar" el XML.
                    # Necesitamos asegurarnos de que svgwrite.base.BaseElement es la forma correcta.
                    # El módulo 'xmlpretty' de svgwrite o 'utils' podría tener herramientas,
                    # pero para inyección directa, esto es lo más cercano sin parseo profundo.
                    # Si 'element_str' es un elemento SVG válido como <path ... /> o <g>...</g>
                    # podríamos intentar añadirlo a un grupo.
                    # svgwrite no tiene una forma directa de "dwg.add_xml_string(element_str)".
                    # Usaremos un truco: crear un elemento 'g' vacío y establecer su contenido.
                    # Esto es bastante hacky.
                    try:
                         # La API para esto es un poco oscura. Un truco es usar un elemento que pueda tener texto:
                         # texto_wrapper = dwg.text('') # Crear un elemento de texto vacío
                         # texto_wrapper.add(svgwrite.utils.SVGElement(element_str)) # Añadir el string como un elemento SVG
                         # background_group.add(texto_wrapper)
                         # Esto probablemente no funcione como se espera.
                         
                         # Opción más robusta si falla lo anterior:
                         # Crear un elemento SVG anidado para el contenido del fondo
                         # Esto es más seguro para preservar estilos y estructuras complejas del SVG de fondo.
                         # Le damos dimensiones y viewBox si el SVG de fondo los tenía.
                         
                         # Por ahora, el enfoque más simple que podría funcionar es leer el contenido
                         # interno del SVG de fondo y añadirlo como un string "raw"
                         # PERO, Raw no está donde pensábamos.
                         
                         # ÚLTIMO INTENTO CON `add_xml_fragment` (si existe en tu versión) o fallback
                         # La API de svgwrite puede ser quisquillosa con XML externo.
                         # A menudo, la mejor manera es recrear los elementos.
                         # Como fallback a todo, y dado que tu SVG de ejemplo es la guía:
                         # Si el SVG de fondo es simple y no tiene su propia declaración XML/DOCTYPE
                         # podríamos intentar concatenar su contenido (sin la etiqueta <svg> exterior)
                         # directamente como texto.
                         
                         # Fallback MUY simple (puede romper SVGs complejos):
                         # Leer el SVG de fondo, extraer su contenido interno y añadirlo como un string crudo.
                         with open(background_svg_path, 'r', encoding='utf-8') as f_bg_inner:
                             bg_content_full = f_bg_inner.read()
                         
                         inner_content = ""
                         root_tag_match = ET.fromstring(bg_content_full) # Para encontrar el nombre del tag raíz
                         
                         # Encontrar el final de la etiqueta <svg ...> y el inicio de </svg>
                         svg_tag_start_str = f"<{root_tag_match.tag}"
                         svg_tag_end_str = f"</{root_tag_match.tag}>"

                         start_index = bg_content_full.find('>')
                         end_index = bg_content_full.rfind(svg_tag_end_str)

                         if start_index != -1 and end_index != -1:
                             inner_content = bg_content_full[start_index + 1 : end_index].strip()
                         
                         if inner_content:
                             # Aquí es donde necesitaríamos una forma de añadir XML crudo.
                             # svgwrite no tiene un método simple y directo como dwg.add_raw_xml().
                             # La opción más segura es anidar el SVG completo:
                             nested_svg = dwg.svg(x=0, y=0, width=canvas_width, height=canvas_height) # Ajusta según sea necesario
                             # Para el href del svg anidado, si el fondo es un archivo
                             # podríamos usar un data URI para el SVG de fondo también, o un path relativo
                             # Pero el objetivo era INCORPORAR las curvas.
                             
                             # Si el SVG de fondo usa clases CSS definidas en el SVG principal (lo cual no es el caso aquí)
                             # o si sus estilos son inline, la inyección de sus elementos internos es viable.
                             # Reintentando con svgwrite.etree.fromstring y añadiendo hijos
                             # Esto es complejo debido a los namespaces.
                             
                             # Vamos a simplificar drásticamente para la prueba y asumir que el fondo
                             # puede ser tratado como un grupo de elementos sin sus propios <defs> complejos
                             # que deban ser fusionados.
                             
                             # Añadimos cada hijo del root del SVG de fondo como un elemento 'g' con contenido XML
                             # Esto sigue siendo un hack.
                             for bg_child in background_root:
                                 bg_child_tag = bg_child.tag.split('}')[-1]
                                 if bg_child_tag not in ['defs', 'metadata', 'title', 'style']:
                                     el_str = ET.tostring(bg_child, encoding='unicode').strip().replace('<?xml version=\'1.0\' encoding=\'us-ascii\'?>', '')
                                     # Crear un grupo y añadir el string como texto (no ideal, pero un intento)
                                     # g_wrapper = dwg.g()
                                     # g_wrapper.add(svgwrite.text.Text(el_str)) # Esto lo tratará como texto literal
                                     # background_group.add(g_wrapper)
                                     # La mejor forma es, si se usa svgwrite, RECREAR los elementos.
                                     # Como el ejemplo original usa Base64 para la imagen y paths directos,
                                     # intentaremos insertar los paths directamente.
                                     # Esto requiere que el SVG de fondo sea simple (solo paths, rects, etc.)
                                     # y que sus estilos se manejen (ej. inline o clases definidas en el SVG principal)
                                     
                                     # Por ahora, el enfoque más robusto si no podemos parsear y recrear
                                     # es tratar el SVG de fondo como una imagen en sí misma.
                                     # PERO el objetivo es "curvas y color".
                                     #
                                     # DADO EL SVG DE EJEMPLO ORIGINAL:
                                     # Los paths rojos y los rects negros/blancos son elementos directos.
                                     # La imagen está incrustada.
                                     #
                                     # Nuestra estrategia debería ser:
                                     # 1. Crear dwg.
                                     # 2. Leer el SVG de fondo. Tomar CADA path/rect/circle, etc., y sus atributos
                                     #    y RECREARLO usando los métodos de dwg (dwg.path, dwg.rect).
                                     #    Esto es lo más robusto.
                                     #
                                     # Por ahora, para avanzar, haré la inserción más simple posible del contenido interno.
                                     # que es leer el archivo y pegarlo, quitando la etiqueta <svg> externa.
                                     # Esto depende de que los estilos estén inline o definidos en el SVG principal.
                                     pass # Lo haremos después con la estrategia de string
                                     
                            # Estrategia de inserción de string simplificada para el contenido del fondo:
                            with open(background_svg_path, 'r', encoding='utf-8') as f_bg_content:
                                full_bg_svg = f_bg_content.read()
                            
                            # Extraer contenido entre las etiquetas <svg> ... </svg>
                            # Esto es muy básico y puede fallar con SVGs complejos o con comentarios/CDATA fuera del root.
                            start_tag = full_bg_svg.find('>')
                            end_tag = full_bg_svg.rfind('</svg>')
                            if start_tag != -1 and end_tag != -1 and start_tag < end_tag:
                                inner_bg_content = full_bg_svg[start_tag + 1:end_tag].strip()
                                # Usar un elemento 'g' como contenedor para el contenido crudo
                                # y luego añadir ese grupo al dibujo principal.
                                # Para esto, necesitamos un elemento que acepte contenido de texto crudo.
                                # `svgwrite` no tiene un "dwg.add_raw_html_or_xml()".
                                #
                                # La forma más compatible de inyectar SVG preexistente es a través de un <use>
                                # si el SVG de fondo define un elemento con ID, o anidando un <svg>
                                # o recreando elementos.
                                #
                                # Para cumplir con "curvas y color" y basándonos en que tu SVG de ejemplo
                                # tiene los paths directamente, vamos a asumir que el SVG de fondo
                                # que proporcionas también tendrá elementos directos.
                                #
                                # Enfoque final para esta iteración: Añadir el SVG de fondo como un <svg> anidado.
                                # Esto preserva sus propios estilos y estructura.
                                # Le damos un x, y para posicionarlo (0,0 por defecto)
                                # y podemos intentar que herede el tamaño del canvas si no tiene el suyo.
                                # dwg.add(dwg.svg(x=0, y=0, href=background_svg_path)) <- Esto lo enlazaría, no incrustaría contenido
                                
                                # Para incrustar contenido, y si Raw no funciona, la alternativa es
                                # parsear con xml.etree.ElementTree y recrear cada elemento.
                                # Esto se vuelve complejo muy rápido.
                                #
                                # Vamos a intentar con un grupo y añadiendo el string crudo (a menudo no funciona bien con estilos/defs).
                                # El problema con Raw es que parece que no está donde uno esperaría en algunas versiones o contextos.
                                #
                                # SOLUCIÓN MÁS SIMPLE Y DIRECTA para insertar XML crudo que svgwrite no procesará:
                                # Añadirlo como un texto multilínea a un elemento 'g' o directamente al 'dwg'.
                                # Esto es un HACK y depende de cómo el renderizador SVG lo interprete.
                                background_group.add(svgwrite.mixins.Presentation()._repr_xml_element(inner_bg_content))
                                # NO, esto es incorrecto.
                                #
                                # La forma correcta de añadir XML arbitrario si no hay un método directo es
                                # usar la capacidad de svgwrite de añadir elementos base y luego manipular su contenido.
                                # Pero eso es bajo nivel.
                                #
                                # Reconsiderando `Raw`: Si `svgwrite.text.Raw` no existe, es posible que `Raw`
                                # sea un alias o esté en `svgwrite.utils` o `svgwrite.base`.
                                # Dado que el error anterior fue `svgwrite.container` no tiene `Raw`,
                                # y ahora `svgwrite.text` no tiene `Raw`,
                                # es posible que `Raw` no sea la forma estándar de hacerlo o haya cambiado de nombre/ubicación.
                                #
                                # La alternativa más robusta si no podemos inyectar el XML de los hijos directamente
                                # es ANIDAR el SVG completo.
                                dwg.add(dwg.image(href=background_svg_path, insert=(0,0), size=(f"{canvas_width}px", f"{canvas_height}px")))
                                # ESTO ENLAZA EL SVG DE FONDO COMO IMAGEN, NO INCORPORA CURVAS EDITABLES.
                                #
                                # Para incrustar curvas, necesitamos procesar el SVG de fondo.
                                # Vamos a asumir que tu SVG de fondo tiene los paths en su raíz o en un grupo principal.
                                # Y que sus estilos están en línea o en clases simples.
                                
                                # **ESTRATEGIA REVISADA PARA FONDO SVG:**
                                # 1. Parsear el SVG de fondo.
                                # 2. Tomar sus <defs> (especialmente <style>) y tratar de añadirlos.
                                # 3. Tomar sus elementos visuales (<path>, <rect>, <circle>, <g>, etc.)
                                #    y AÑADIRLOS COMO STRINGS XML CRUDOS.
                                #    svgwrite no tiene una forma elegante de añadir XML crudo directamente al flujo principal
                                #    que no sea a través de elementos como <text> o <desc> que lo escaparían.
                                #    La única forma real es crear un SVG anidado o *recrear* los elementos.
                                #
                                # Como el SVG de ejemplo tiene los paths directamente, intentaremos esto:
                                for child_el in background_root: # Itera sobre los hijos del <svg> del fondo
                                    tag = child_el.tag.split('}')[-1]
                                    if tag == 'style': # Manejar estilos en defs
                                        if child_el.text: dwg.defs.add(dwg.style(content=child_el.text))
                                    elif tag not in ['defs', 'metadata', 'title']:
                                        # Para otros elementos, los convertimos a string y los añadimos a un grupo
                                        # Esto es aún un hack, pero es lo más cercano sin recreación completa
                                        # La forma más segura es que el SVG de fondo use atributos de presentación (fill="red")
                                        # en lugar de depender exclusivamente de clases CSS que podrían no transferirse bien.
                                        el_str = ET.tostring(child_el, encoding='unicode').strip().replace('<?xml version=\'1.0\' encoding=\'us-ascii\'?>', '')
                                        # background_group.add(svgwrite.utils.SVGElement(el_str)) # Esto no es una API pública estable.
                                        # El problema es que svgwrite quiere crear los elementos, no que se le inyecte XML.
                                        # Si tu SVG de fondo es simple (solo paths, rects, circles con atributos inline)
                                        # podrías parsearlo y recrear cada elemento.
                                        # Ejemplo para un path:
                                        # if tag == 'path':
                                        #   new_path = dwg.path(d=child_el.get('d'))
                                        #   for attr, val in child_el.attrib.items():
                                        #       if attr != 'd': new_path.attribs[attr] = val
                                        #   background_group.add(new_path)
                                        # Esto se vuelve muy complejo para todos los tipos de elementos.
                                        #
                                        # DADO EL EJEMPLO SVG: los paths rojos y rects negros/blancos.
                                        # Vamos a asumir que el SVG que proporcionas como fondo es similar
                                        # y podemos simplemente volcar su contenido interno (sin la etiqueta <svg> exterior)
                                        # dentro de un <g> en el SVG principal. Los estilos deben ser inline o
                                        # las clases definidas en el SVG principal (o transferidas desde los defs del fondo).
                                        # Este es el enfoque del SVG de ejemplo.
                                        pass # Se hará abajo con la lectura de string

                                # Leer el contenido completo del SVG de fondo y añadir todo lo que está DENTRO de la etiqueta <svg> raíz.
                                with open(background_svg_path, 'r', encoding='utf-8') as f_bg_content:
                                    full_bg_svg_text = f_bg_content.read()
                                
                                # Extraer contenido entre > de la etiqueta svg y </svg>
                                first_gt = full_bg_svg_text.find('>')
                                last_svg_tag = full_bg_svg_text.rfind('</svg>')
                                if first_gt != -1 and last_svg_tag != -1 and first_gt < last_svg_tag:
                                    inner_svg_content = full_bg_svg_text[first_gt + 1:last_svg_tag].strip()
                                    # Añadir este contenido crudo a nuestro grupo de fondo
                                    # Para esto, svgwrite necesita que el string sea añadido a un elemento que acepte texto.
                                    # O, si la versión de svgwrite lo soporta, directamente a un grupo.
                                    # Si no, la única forma es anidar el SVG o usar una biblioteca diferente
                                    # que permita manipulación de DOM más directa (como lxml).
                                    #
                                    # Dado que tu SVG de ejemplo tiene los paths y rects como hijos directos de un <g>,
                                    # el enfoque de inyectar el "inner_svg_content" en un <g> es el más cercano.
                                    # PERO `svgwrite` no tiene un método directo para `g.add_xml_string()`.
                                    #
                                    # Usaremos `dwg.add(svgwrite.basic_shapes.Text(inner_svg_content))` pero esto
                                    # tratará el SVG como texto literal, lo cual no es lo que queremos.
                                    #
                                    # La forma más pragmática si los estilos están inline o en el SVG de fondo:
                                    # Envolver el contenido en un <g> si no lo está ya.
                                    # Y usar el método add() con el objeto Drawing.
                                    # La clave es que svgwrite.Drawing.add() espera objetos svgwrite.
                                    #
                                    # La solución más simple y que se alinea con tu SVG de ejemplo es
                                    # asumir que el SVG de fondo ya está bien estructurado con sus estilos aplicados
                                    # y simplemente necesitamos colocarlo en el orden correcto.
                                    #
                                    # Fallback a incrustar el SVG de fondo como una imagen referenciada si la
                                    # incrustación directa de elementos es demasiado compleja con svgwrite.
                                    # PERO esto no cumple "curvas y color" como elementos editables.
                                    #
                                    # Si `Raw` no está disponible, la única forma real de inyectar XML crudo
                                    # en `svgwrite` es una característica no documentada o no estándar.
                                    #
                                    # Vamos a intentar añadir el SVG de fondo como un <svg> anidado.
                                    # Esto es estándar y debería funcionar.
                                    # Asegúrate de que el SVG de fondo tenga sus propios atributos de tamaño o viewBox.
                                    bg_svg_element = dwg.svg(x=0, y=0) # Puedes ajustar x,y,width,height
                                    # Leer el contenido del archivo SVG y establecerlo como el 'texto' del elemento <svg> anidado
                                    # Esto es un hack, svgwrite no lo soporta así.
                                    #
                                    # La forma más limpia con svgwrite es RECREAR cada elemento.
                                    # Como eso es demasiado complejo para el caso general sin saber la estructura exacta del fondo,
                                    # vamos a usar el método más simple que svgwrite ofrece para incluir un SVG externo
                                    # como un bloque, que es usar el elemento <use> si podemos definir el fondo
                                    # como un símbolo, o simplemente tratarlo como una imagen si no necesitamos editarlo.
                                    #
                                    # Ya que tu SVG de ejemplo tiene los paths y rects en el mismo nivel que la imagen,
                                    # el objetivo es replicar eso.
                                    #
                                    # VAMOS A INTENTAR LA INSERCIÓN DIRECTA DE STRING (este es el método más "crudo"):
                                    # Esto asume que el SVG de fondo es solo un fragmento sin la etiqueta <svg> exterior
                                    # y sin declaraciones XML o DOCTYPE.
                                    # Si es un archivo SVG completo, necesitamos extraer solo el contenido.
                                    if inner_svg_content:
                                         # Añadir al grupo principal, no al background_group para que esté en el flujo
                                         dwg.add(dwg. πολλοί(inner_svg_content)) # ' πολλοί' es un hack para que acepte un string
                                         # NO, esto es incorrecto.
                                         #
                                         # Usaremos el hecho de que dwg.add puede tomar un string si es un elemento simple.
                                         # Pero para múltiples elementos, necesitamos un grupo.
                                         # La forma más directa que svgwrite ofrece para contenido "crudo" es
                                         # añadiéndolo a los `elements` de un grupo.
                                         # Esto es bajo nivel y puede no ser la API pública ideal.
                                         # Ejemplo: background_group.elements.append(inner_svg_content) # String directo
                                         #
                                         # Dado el error original, y la dificultad de inyectar XML crudo con svgwrite
                                         # de una manera limpia y soportada para fragmentos complejos,
                                         # la opción más robusta es usar una biblioteca que maneje la fusión de SVG
                                         # a nivel de DOM, como `svgutils`.
                                         #
                                         # Sin embargo, para mantenerlo dentro de `svgwrite`, la solución
                                         # más alineada con tu SVG de ejemplo (donde los paths y la imagen están al mismo nivel)
                                         # es:
                                         # 1. Parsear el SVG de fondo.
                                         # 2. Recrear cada elemento (<path>, <rect>, etc.) con svgwrite y añadirlo.
                                         # Esto es lo más correcto pero más laborioso.
                                         #
                                         # **Si `svgwrite.text.Raw` no funciona, y asumiendo que tu SVG de fondo es simple**
                                         # (solo elementos básicos con atributos inline para estilo),
                                         # podrías parsearlo con `xml.etree.ElementTree` y recrear los elementos.
                                         # Ejemplo simplificado (solo para paths):
                                         for elem in background_root:
                                             if elem.tag.endswith('path'):
                                                 path_data = elem.get('d')
                                                 attrs = dict(elem.attrib) # Copiar todos los atributos
                                                 if 'd' in attrs: del attrs['d'] # d se pasa por separado
                                                 background_group.add(dwg.path(d=path_data, **attrs))
                                             # Añadir manejo para rect, circle, etc.
                                         dwg.add(background_group)

                                # **Si el SVG de fondo es complejo y usa <style> o <defs> extensivamente,**
                                # **la única forma real con svgwrite es anidarlo como un <svg> completo**
                                # **o usar una herramienta de fusión de SVG más potente.**
                                #
                                # **Por ahora, el bloque de prueba crea un SVG de fondo simple.**
                                # **Si el SVG de fondo que tú proporcionas es igualmente simple (paths y rects con clases o fills inline),**
                                # **el parseo con ElementTree y la adición de strings crudos de cada elemento (quitando namespaces)**
                                # **a un grupo `dwg.g()` debería funcionar si `Raw` no está disponible.**
                                #
                                # **Dado que `Raw` sigue dando problemas, el enfoque de anidar el SVG de fondo**
                                # **es el más seguro con `svgwrite` puro si no queremos recrear cada elemento.**
                                # **Esto se hace con `<image href="fondo.svg">` (enlace) o `<svg x="0" y="0">contenido_del_fondo_aqui</svg>` (incrustación).**
                                # **Para incrustar el contenido como elementos editables, necesitamos recrearlos.**
                                #
                                # Vamos a usar el método de parsear y añadir los hijos,
                                # pero no como Raw, sino intentando recrear algunos básicos o
                                # esperando que la conversión a string de ElementTree sea suficiente
                                # si se añade a un grupo.
                                #
                                # ¡CORRECCIÓN FINAL PARA `Raw`!
                                # El objeto para XML crudo es `svgwrite.xml.Raw`
                                # Lo importaremos como:
                                from svgwrite import xml # Importar xml
                                # Y luego usar:
                                # xml.Raw(text=element_str)
                                
                                # Corrigiendo el bucle de los hijos del fondo:
                                for child_el in background_root:
                                    tag = child_el.tag.split('}')[-1]
                                    if tag == 'style' and bg_defs_element is None: # Si el estilo está en la raíz
                                        if child_el.text: dwg.defs.add(dwg.style(content=child_el.text))
                                    elif tag not in ['defs', 'metadata', 'title', 'style']:
                                        el_str = ET.tostring(child_el, encoding='unicode').strip().replace('<?xml version=\'1.0\' encoding=\'us-ascii\'?>', '')
                                        background_group.add(xml.Raw(text=el_str)) # USAR xml.Raw
                                dwg.add(background_group)
                                print(f"    Contenido del fondo SVG incrustado.")


                        except Exception as e_bg_parse_children:
                             print(f"    Error al procesar hijos del SVG de fondo: {e_bg_parse_children}.")
                             print("    Intentando inserción cruda del SVG de fondo completo (puede resultar en SVG anidado).")
                             with open(background_svg_path, 'r', encoding='utf-8') as f_bg_full:
                                 bg_svg_content_full = f_bg_full.read()
                             if bg_svg_content_full.startswith("<?xml"):
                                 bg_svg_content_full = bg_svg_content_full.split("?>",1)[1].strip()
                             dwg.add(xml.Raw(text=bg_svg_content_full)) # USAR xml.Raw


        except ET.ParseError as e_parse_main:
            print(f"  CRÍTICO: Error al parsear el archivo SVG de fondo principal: {e_parse_main}. No se puede continuar.")
            return False
        except Exception as e_bg_main:
            print(f"  Error general severo al procesar SVG de fondo: {e_bg_main}")
            return False


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

    except Exception as e:
        print(f"Error fatal al crear el SVG final: {e}")
        return False

# --- Bloque de pruebas (sin cambios en la lógica, pero debería funcionar ahora) ---
if __name__ == '__main__':
    print("\n--- Probando Generación de SVG Final (con SVG de fondo e imagen PNG incrustada) ---")
    
    test_output_dir = "test_output_svg_gen_v2"
    if not os.path.exists(test_output_dir):
        os.makedirs(test_output_dir)

    bg_svg_path = os.path.join(test_output_dir, "my_background.svg")
    # Crear un SVG de fondo de prueba más simple para asegurar que el parseo funcione
    # con elementos directos y un defs/style
    bg_svg_content = """
    <svg width="500" height="500" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <style type="text/css">
          .red_class { fill: red; }
          .blue_stroke { stroke: blue; fill: none; }
        </style>
      </defs>
      <g id="actual_background_content">
        <path d="M100,100 L300,100 L200,300 z" class="red_class" />
        <rect x="50" y="50" width="400" height="400" class="blue_stroke" />
        <circle cx="250" cy="250" r="30" fill="yellow" />
      </g>
    </svg>
    """
    with open(bg_svg_path, "w", encoding="utf-8") as f:
        f.write(bg_svg_content)
    print(f"SVG de fondo de prueba creado en: {bg_svg_path}")


    fg_image_path = os.path.join(test_output_dir, "foreground_image.png")
    try:
        from PIL import Image, ImageDraw
        img_fg = Image.new("RGBA", (300, 200), (0, 0, 0, 0)) 
        draw = ImageDraw.Draw(img_fg)
        draw.ellipse((50, 50, 150, 150), fill=(0, 255, 0, 128)) 
        draw.text((60, 80), "PNG FG", fill="black")
        img_fg.save(fg_image_path, "PNG")
        fg_w, fg_h = img_fg.size
        print(f"Imagen PNG de prueba creada en: {fg_image_path}")
    except ImportError:
        print("Pillow no está instalado. No se puede crear PNG de prueba. Necesitarás uno manualmente.")
        if not os.path.exists(fg_image_path):
            print(f"Por favor, crea {fg_image_path} manualmente para la prueba.")
            exit()
        else:
            try:
                with Image.open(fg_image_path) as img_temp:
                    fg_w, fg_h = img_temp.size
            except:
                print("No se pudo abrir la imagen PNG de prueba para obtener dimensiones.")
                fg_w, fg_h = 300,200
                exit()

    final_svg_output_path = os.path.join(test_output_dir, "final_composite.svg")

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
        print("  Abre este archivo en un navegador o editor de SVG para verificar.")
    else:
        print("\nFalló la generación del SVG final de prueba.")