import os

def list_all_files(directory, output_file='project_structure.txt'):
    """Lista todos los archivos del proyecto"""
    
    # Carpetas a ignorar
    ignore_folders = {
        '__pycache__', 
        '.git', 
        'node_modules', 
        '.venv', 
        'venv',
        '.idea',
        '.vscode',
        'dist',
        'build'
    }
    
    # Extensiones relevantes
    relevant_extensions = {
        '.py', '.html', '.js', '.css', '.json', 
        '.txt', '.md', '.sql', '.env', '.db'
    }
    
    all_files = []
    html_files = []
    js_files = []
    
    print(f"Escaneando: {directory}\n")
    print("=" * 60)
    
    for root, dirs, files in os.walk(directory):
        # Filtrar carpetas a ignorar
        dirs[:] = [d for d in dirs if d not in ignore_folders]
        
        # Obtener ruta relativa
        rel_path = os.path.relpath(root, directory)
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_file_path = os.path.join(rel_path, file)
            
            # Normalizar path
            rel_file_path = rel_file_path.replace('\\', '/')
            if rel_file_path.startswith('./'):
                rel_file_path = rel_file_path[2:]
            
            ext = os.path.splitext(file)[1].lower()
            
            # Guardar archivos relevantes
            if ext in relevant_extensions:
                all_files.append(rel_file_path)
                
                # Detectar archivos HTML
                if ext == '.html':
                    html_files.append(rel_file_path)
                
                # Detectar archivos JS
                if ext == '.js':
                    js_files.append(rel_file_path)
    
    # Imprimir en consola
    print("ARCHIVOS HTML ENCONTRADOS:")
    print("-" * 60)
    if html_files:
        for f in html_files:
            print(f"  {f}")
    else:
        print("  No se encontraron archivos HTML")
    
    print("\n" + "=" * 60)
    print("ARCHIVOS JAVASCRIPT ENCONTRADOS:")
    print("-" * 60)
    if js_files:
        for f in js_files:
            print(f"  {f}")
    else:
        print("  No se encontraron archivos JS")
    
    print("\n" + "=" * 60)
    print("TODOS LOS ARCHIVOS RELEVANTES:")
    print("-" * 60)
    for f in sorted(all_files):
        print(f"  {f}")
    
    # Guardar en archivo
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("ESTRUCTURA DEL PROYECTO\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("ARCHIVOS HTML:\n")
        f.write("-" * 60 + "\n")
        for file in html_files:
            f.write(f"{file}\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("ARCHIVOS JAVASCRIPT:\n")
        f.write("-" * 60 + "\n")
        for file in js_files:
            f.write(f"{file}\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("TODOS LOS ARCHIVOS:\n")
        f.write("-" * 60 + "\n")
        for file in sorted(all_files):
            f.write(f"{file}\n")
    
    print(f"\n{'=' * 60}")
    print(f"Total archivos encontrados: {len(all_files)}")
    print(f"HTML: {len(html_files)}")
    print(f"JS: {len(js_files)}")
    print(f"\nEstructura guardada en: {output_file}")

if __name__ == "__main__":
    project_path = r"C:\Users\javiv\OneDrive\Desktop\Proyectos\bjj-chatbot\bjj-academy-bot"
    list_all_files(project_path)