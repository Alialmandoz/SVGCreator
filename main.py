import customtkinter as ctk
from tkinter import filedialog
import os
# Cambiar la importación para usar la nueva función (o mantener 'optimize_image' si renombraste la función en el otro archivo)
from image_processor import optimize_image_iteratively as optimize_image 

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SVGCreator by Jules & Desarrollador")
        self.geometry("600x480") 

        self.main_image_path = None
        self.background_image_path = None
        self.optimized_main_image_actual_path = None
        self.output_directory = None

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.main_image_frame = ctk.CTkFrame(self)
        self.main_image_frame.pack(pady=10, padx=10, fill="x")
        self.btn_load_main = ctk.CTkButton(self.main_image_frame, text="Cargar Imagen Principal", command=self.load_main_image)
        self.btn_load_main.pack(side="left", padx=5)
        self.lbl_main_image_path = ctk.CTkLabel(self.main_image_frame, text="Ninguna imagen principal cargada", anchor="w")
        self.lbl_main_image_path.pack(side="left", padx=5, expand=True, fill="x")

        self.bg_image_frame = ctk.CTkFrame(self)
        self.bg_image_frame.pack(pady=10, padx=10, fill="x")
        self.btn_load_background = ctk.CTkButton(self.bg_image_frame, text="Cargar Imagen de Fondo", command=self.load_background_image)
        self.btn_load_background.pack(side="left", padx=5)
        self.lbl_bg_image_path = ctk.CTkLabel(self.bg_image_frame, text="Ninguna imagen de fondo cargada", anchor="w")
        self.lbl_bg_image_path.pack(side="left", padx=5, expand=True, fill="x")

        self.output_dir_frame = ctk.CTkFrame(self)
        self.output_dir_frame.pack(pady=10, padx=10, fill="x")
        self.btn_select_output_dir = ctk.CTkButton(self.output_dir_frame, text="Seleccionar Carpeta de Salida", command=self.select_output_directory)
        self.btn_select_output_dir.pack(side="left", padx=5)
        self.lbl_output_dir_path = ctk.CTkLabel(self.output_dir_frame, text="Ninguna carpeta de salida seleccionada", anchor="w")
        self.lbl_output_dir_path.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_generate_svg = ctk.CTkButton(self, text="Generar SVG", command=self.generate_svg_action, state="disabled")
        self.btn_generate_svg.pack(pady=20)

        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.pack(pady=10, padx=10, fill="x", expand=True)
        self.lbl_status = ctk.CTkLabel(self.status_frame, text="Cargue imágenes y seleccione carpeta de salida.", wraplength=550, justify="left")
        self.lbl_status.pack(fill="x")

    def load_main_image(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar Imagen Principal",
            filetypes=(("Archivos PNG", "*.png"), ("Archivos JPG/JPEG", "*.jpg;*.jpeg"), ("Todos los archivos", "*.*"))
        )
        if file_path:
            self.main_image_path = file_path
            self.lbl_main_image_path.configure(text=os.path.basename(file_path))
            self.lbl_status.configure(text=f"Imagen principal: {os.path.basename(file_path)}", text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
            self.check_if_can_generate()
        else:
            self.lbl_status.configure(text="Carga de imagen principal cancelada.", text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        self.optimized_main_image_actual_path = None

    def load_background_image(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar Imagen de Fondo",
            filetypes=(("Archivos PNG", "*.png"), ("Archivos JPG/JPEG", "*.jpg;*.jpeg"), ("Todos los archivos", "*.*"))
        )
        if file_path:
            self.background_image_path = file_path
            self.lbl_bg_image_path.configure(text=os.path.basename(file_path))
            self.lbl_status.configure(text=f"Imagen de fondo: {os.path.basename(file_path)}", text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
            self.check_if_can_generate()
        else:
            self.lbl_status.configure(text="Carga de imagen de fondo cancelada.", text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])

    def select_output_directory(self):
        dir_path = filedialog.askdirectory(title="Seleccionar Carpeta de Salida")
        if dir_path:
            self.output_directory = dir_path
            self.lbl_output_dir_path.configure(text=self.output_directory)
            self.lbl_status.configure(text=f"Carpeta de salida: {self.output_directory}", text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
            self.check_if_can_generate()
        else:
            self.lbl_status.configure(text="Selección de carpeta de salida cancelada.", text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])

    def check_if_can_generate(self):
        if self.main_image_path and self.background_image_path and self.output_directory:
            self.btn_generate_svg.configure(state="normal")
            self.lbl_status.configure(text="Listo para generar SVG.", text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        else:
            self.btn_generate_svg.configure(state="disabled")
            if not self.main_image_path:
                 self.lbl_status.configure(text="Por favor, cargue la imagen principal.", text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
            elif not self.background_image_path:
                 self.lbl_status.configure(text="Por favor, cargue la imagen de fondo.", text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
            elif not self.output_directory:
                 self.lbl_status.configure(text="Por favor, seleccione una carpeta de salida.", text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])
            else:
                 self.lbl_status.configure(text="Cargue imágenes y seleccione carpeta de salida.", text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"])

    def generate_svg_action(self):
        if not self.main_image_path or not self.background_image_path or not self.output_directory:
            self.lbl_status.configure(text="Error: Cargar ambas imágenes y seleccionar carpeta de salida.", text_color="red")
            return

        self.lbl_status.configure(text="Procesando imagen principal (iterativamente)...", text_color="orange")
        self.update_idletasks() 

        optimized_main_image_subdir = os.path.join(self.output_directory, "optimized_main_image")
        
        if not os.path.exists(optimized_main_image_subdir):
            try:
                os.makedirs(optimized_main_image_subdir)
            except OSError as e:
                self.lbl_status.configure(text=f"Error al crear directorio: {optimized_main_image_subdir}. {e}", text_color="red")
                return
            
        # Llamamos a la función de optimización (que ahora es la iterativa)
        self.optimized_main_image_actual_path = optimize_image(
            self.main_image_path,
            output_dir=optimized_main_image_subdir, 
            pngquant_exe_rel_path="tools/pngquant.exe"
        )

        if not self.optimized_main_image_actual_path or not os.path.exists(self.optimized_main_image_actual_path):
            self.lbl_status.configure(text="Error al optimizar la imagen principal o no se generó archivo.", text_color="red")
            return

        final_size_kb = os.path.getsize(self.optimized_main_image_actual_path) / 1024
        self.lbl_status.configure(text=f"Imagen principal procesada: {os.path.basename(self.optimized_main_image_actual_path)} ({final_size_kb:.2f} KB)", text_color="blue")
        self.update_idletasks()

        print(f"Ruta de imagen principal (procesada): {self.optimized_main_image_actual_path}")
        print(f"Ruta de imagen de fondo (sin procesar aún): {self.background_image_path}")
        print(f"Carpeta de salida seleccionada: {self.output_directory}")

        self.lbl_status.configure(text="Vectorización y generación SVG pendientes.", text_color="orange")

if __name__ == "__main__":
    app = App()
    app.mainloop()