# file_utils.py
import os
import random
import string
from pathlib import Path
import shutil



def delete_file_if_exists(filename):
    """
    Deletes a file if it exists.

    :param filename: The path to the file to be deleted.
    """
    if os.path.exists(filename):
        os.remove(filename)
        print(f"{filename} has been deleted.")
    else:
        print(f"The file {filename} does not exist.")



def rename_file_smartly(old_name, new_name, i=0):
    """
    Renames a file efficiently. If the new name exists, it tries appending an index before the extension.
    Uses a mixture of both provided approaches for a more unified method.

    :param old_name: The current name of the file.
    :param new_name: The desired new name for the file.
    :param i: An index to append to the new name if the new name already exists.
    """
    # Use pathlib for handling paths
    p = Path(old_name)
    
    # Extract the filename and extension
    filename, file_extension = os.path.splitext(new_name)
    
    # Modify the filename to include a space (or not) and an index if needed
    if i > 0:
        # Following a consistent pattern with '_' as separator and "i" as the index marker
        new_filename_formatted = '{filename}_{index}{file_extension}'.format(filename=filename, index='i'*i, file_extension=file_extension)
    else:
        new_filename_formatted = new_name
    
    # Combine with the parent path
    new_filepath = p.parent.joinpath(new_filename_formatted)
    
    # Check if the new filepath exists
    if new_filepath.exists():
        # If exists, call function recursively with incremented index
        rename_file_smartly(old_name, new_name, i+1)
    else:
        # If it does not exist, proceed to rename
        os.rename(old_name, new_filepath)
        print(f"File renamed to {new_filepath}")



# def renomear_arquivo(nome_antigo, novo_nome, i = 0):

#    p = Path(nome_antigo)
   
#    filename, file_extension = os.path.splitext(novo_nome)
#    novo_filename = '{path}/{filename}{espaco}{n}{file_extension}'.format(path = p.parent, filename = filename, espaco = ' ' if i > 0 else '', n = i * 'i', file_extension = file_extension)

#    if os.path.exists(novo_filename):
#       i = i + 1
#       renomear_arquivo(nome_antigo, os.path.basename(novo_filename), i)
#    else:
#       os.rename(nome_antigo, novo_filename)




def generate_random_filename(length=8, extension=".txt"):
    """
    Generates a random filename.

    :param length: Length of the base filename (excluding extension).
    :param extension: File extension.
    :return: Generated filename as a string.
    """
    letters = string.ascii_letters + string.digits
    basename = ''.join(random.choice(letters) for i in range(length))
    return basename + extension



def delete_all_files_in_folder(folder_path):
    """
    Deletes all files inside a specified folder.

    :param folder_path: The path to the folder whose contents should be deleted.
    """
    folder = Path(folder_path)
    
    if not folder.is_dir():
        print(f"The specified path {folder_path} is not a directory.")
        return
    
    for file in folder.iterdir():
        if file.is_file():
            file.unlink()
            print(f"Deleted file: {file}")
        elif file.is_dir():
            shutil.rmtree(file)
            print(f"Deleted directory: {file}")
    
    print(f"All contents in {folder_path} have been deleted.")




def create_directory(directory_path):
    """
    Creates a directory if it does not exist.
    :param file_path: The path to the directory to be created.
    """
    # Convert the directory path to a Path object
    directory_path = Path(directory_path)
    
    # Create the directory if it does not exist
    if not directory_path.exists():
        directory_path.mkdir(parents=True, exist_ok=True)
        print(f"Directory {directory_path} created.")





def create_file_and_directory(file_path):
    """
    Creates a directory and a file if they do not exist.

    :param file_path: The path to the file to be created.
    """
    # Convert the file path to a Path object
    file_path = Path(file_path)

    create_directory(file_path.parent)
    
    # Create the file if it does not exist
    if not file_path.exists():
        file_path.touch()
        print(f"File {file_path} created.")
    else:
        print(f"File {file_path} already exists.")



# Example usage
if __name__ == "__main__":
    # Delete a file if it exists
    # delete_file_if_exists("test.txt")

    # Rename a file
    # rename_file("old_name.txt", "new_name.txt")

    # Generate a random filename
    # print(generate_random_filename(10, ".docx"))

    create_file_and_directory("/home/eduardo/Desktop/new_directory/newfile.txt")