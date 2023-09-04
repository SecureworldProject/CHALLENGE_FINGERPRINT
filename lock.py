# module lock

import os
from pathlib import Path
import time
import fnmatch

def searchLock(challenge_name):
    folder=os.environ['SECUREMIRROR_CAPTURES']
    while os.path.isdir(folder)==False:
        print (" challenge : SECUREMIRROR_CAPTURES environment var not valid")
        return False
        time.sleep(60) # check and sleep forever
        
    #si llegamos aqui, el directorio existe
        
    for file in os.listdir(folder):
        if fnmatch.fnmatch(file,'lock_*'):
            print ("file found:", file)
            #hemos encontrado un fichero que cumple
            # si es nuestro challenge, ignoramos
            if file=="lock_"+challenge_name:
                print ("el lock es del mismo challenge. lo ignoramos")
                continue
            creation_date=os.path.getctime(folder+"/"+file)
            now= time.time()
            if (now>creation_date+300): # 5 minutos es viejo
                # es viejo
                print (file, "is old")
                continue
            else:
                return False
    return True
    
def lockIN(challenge_name):
    
    #mientras exista un fichero lock* se queda en bucle
    while True:
        search=searchLock(challenge_name)
        if (search==True):
            break
        else:
            time.sleep(5)
            
    # si llegamos aquies que no hay lock o lo que hay es viejo
    # tambien tenemos garantizado si llegamos aqui que folder existe
    
    folder=os.environ['SECUREMIRROR_CAPTURES']
    #borramos un posible fichero viejo nuestro
    if os.path.exists(folder+"/"+"lock_"+challenge_name):
        os.remove(folder+"/"+"lock_"+challenge_name)
    #creamos el nuevo
    Path(folder+"/"+"lock_"+challenge_name).touch()
    

def lockOUT(challenge_name):
    folder=os.environ['SECUREMIRROR_CAPTURES']
    if os.path.exists(folder+"/"+"lock_"+challenge_name):
        os.remove(folder+"/"+"lock_"+challenge_name)