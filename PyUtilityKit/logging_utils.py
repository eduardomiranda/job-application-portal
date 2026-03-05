# Standard library imports
import logging

# Third party imports
from datetime import datetime
from .file_utils import create_file_and_directory



# def adicionarTimestampComoPrefixo( filename ):

#     # Adiciona um prefixo ao nome do arquivo de logs
#     dateTimeObj = datetime.now()
#     timestampStr = dateTimeObj.strftime("%Y%m%d%H%M") # Ano, mês, dia, hora e minuto

#     novoFilename = timestampStr + '-' + filename

#     return novoFilename



def iniciaLogging(LogFilename, LogLevel, LoggerObjectReference):
 
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(threadName)s -  %(levelname)s - %(message)s')

    create_file_and_directory(LogFilename)

    fileHandler = logging.FileHandler(LogFilename, 'a+', 'utf-8') 
    fileHandler.setFormatter( formatter ) 

    # Empty strings are "falsy" (python 2 or python 3 reference), which means they are considered false in a Boolean context.
    logger = logging.getLogger() if not LoggerObjectReference else logging.getLogger( LoggerObjectReference )
    
    logger.setLevel(LogLevel)
    logger.addHandler(fileHandler)